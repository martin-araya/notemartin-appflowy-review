#!/usr/bin/env bash
# run_subagent_author.sh — Wrapper que invoca un LLM externo para
# producir un AutorOutput a partir de una unidad de trabajo de la
# skill `notemartin-appflowy-review`.
#
# A partir de A5.2, el modo `autor` de `run_subagent.py` (mock
# generador de placeholders) se ha movido a `run_subagent_placeholder.py`.
# Este wrapper es la vía **real** para producir documentos de Parte B.
#
# Uso:
#   run_subagent_author.sh --unit UNIT_PATH --out OUT_JSON
#                          [--src-root SRC] [--out-root PROJECT_ROOT]
#                          [--catalogos-dir DIR] [--inventario PATH]
#                          [--feature-id Fxx] [--max-secciones N]
#
# Variables de entorno:
#   KILO_AUTHOR_CMD  Comando a invocar. Default: "kilo --rol autor --input -"
#                    El comando debe leer el AutorInput JSON de stdin y
#                    escribir el AutorOutput JSON en stdout. Si tu
#                    herramienta no es Kilo, sobreescribe la variable,
#                    p. ej.:
#                      export KILO_AUTHOR_CMD="claude --prompt -"
#                      export KILO_AUTHOR_CMD="python3 my_author.py"
#
# Esquema del AutorInput inyectado: ver
# `SKILL/references/subagent-contract.md` §2.

set -u
set -o pipefail

SCRIPT_NAME=$(basename "$0")
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
SKILL_ROOT=$(cd "$SCRIPT_DIR/../.." && pwd)
PROJECT_ROOT=$(cd "$SCRIPT_DIR/../../.." && pwd)

# --- defaults ---
UNIT_PATH=""
OUT_PATH=""
SRC_ROOT="$PROJECT_ROOT/SRC"
OUT_ROOT="$PROJECT_ROOT"
CATALOGOS_DIR="$PROJECT_ROOT/OUT/_ledger/extract"
INVENTARIO_PATH="$PROJECT_ROOT/OUT/_ledger/inventario.json"
FEATURE_ID=""
MAX_SECCIONES=19
KILO_AUTHOR_CMD="${KILO_AUTHOR_CMD:-kilo --rol autor --input -}"

usage() {
  cat <<USAGE
$SCRIPT_NAME — wrapper de producción para el subagente autor.

Uso:
  $SCRIPT_NAME --unit UNIT_PATH --out OUT_JSON [opciones]

Opciones:
  --unit PATH          Ruta al JSON de la unidad (obligatorio).
  --out PATH           Ruta del JSON AutorOutput a escribir (obligatorio).
  --src-root PATH      Raíz de los clones (default: $PROJECT_ROOT/SRC).
  --out-root PATH      Raíz del proyecto (default: $PROJECT_ROOT).
  --catalogos-dir DIR  Carpeta con extract/*.json (default: .../OUT/_ledger/extract).
  --inventario PATH    Ruta al inventario (default: .../OUT/_ledger/inventario.json).
  --feature-id Fxx     Override del feature_id (default: leído de la unidad).
  --max-secciones N    19 para feature, 11 para export (default: 19).
  -h, --help           Muestra esta ayuda.

Variables de entorno:
  KILO_AUTHOR_CMD  Comando externo que lee AutorInput JSON de stdin y
                   escribe AutorOutput JSON en stdout.
                   Default: "kilo --rol autor --input -"
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --unit) UNIT_PATH="$2"; shift 2 ;;
    --out) OUT_PATH="$2"; shift 2 ;;
    --src-root) SRC_ROOT="$2"; shift 2 ;;
    --out-root) OUT_ROOT="$2"; shift 2 ;;
    --catalogos-dir) CATALOGOS_DIR="$2"; shift 2 ;;
    --inventario) INVENTARIO_PATH="$2"; shift 2 ;;
    --feature-id) FEATURE_ID="$2"; shift 2 ;;
    --max-secciones) MAX_SECCIONES="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "[$SCRIPT_NAME] argumento desconocido: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ -z "$UNIT_PATH" || -z "$OUT_PATH" ]]; then
  echo "[$SCRIPT_NAME] ERROR: --unit y --out son obligatorios." >&2
  usage
  exit 2
fi
if [[ ! -f "$UNIT_PATH" ]]; then
  echo "[$SCRIPT_NAME] ERROR: no existe $UNIT_PATH" >&2
  exit 2
fi

# --- construir AutorInput con python (jq no siempre está) ---
AUTOR_INPUT=$(python3 - "$UNIT_PATH" "$SRC_ROOT" "$OUT_ROOT" "$CATALOGOS_DIR" "$INVENTARIO_PATH" "$FEATURE_ID" "$MAX_SECCIONES" <<'PY'
import json
import sys
unit_path, src_root, out_root, catalogos_dir, inventario_path, feature_id, max_secciones = sys.argv[1:]
with open(unit_path, encoding="utf-8") as f:
    unit = json.load(f)
autor_input = {
    "schema_version": 1,
    "unit_id": unit.get("id", "F?"),
    "unit_path": unit_path,
    "src_root": src_root,
    "inventario_path": inventario_path,
    "catalogos_dir": catalogos_dir,
    "plantilla": "feature" if int(max_secciones) >= 19 else "export",
    "plantilla_path": f"{out_root}/SKILL/references/feature-template.md" if int(max_secciones) >= 19 else f"{out_root}/SKILL/references/export-template.md",
    "out_root": out_root,
    "max_secciones": int(max_secciones),
    "allowed_refs": [
        f"{out_root}/SKILL/references",
        f"{out_root}/OUT/_ledger/extract",
        f"{out_root}/OUT/_ledger/cobertura.csv",
    ],
    "feature_id": feature_id or unit.get("feature_id", ""),
}
print(json.dumps(autor_input, ensure_ascii=False))
PY
)

# --- invocar el LLM externo ---
if ! command -v ${KILO_AUTHOR_CMD%% *} >/dev/null 2>&1; then
  echo "[$SCRIPT_NAME] ERROR: comando externo no encontrado: $KILO_AUTHOR_CMD" >&2
  echo "[$SCRIPT_NAME] Sugerencia: export KILO_AUTHOR_CMD='claude --prompt -' o similar." >&2
  exit 2
fi

echo "[$SCRIPT_NAME] invocando: $KILO_AUTHOR_CMD" >&2
AUTOR_OUTPUT=$(printf '%s' "$AUTOR_INPUT" | $KILO_AUTHOR_CMD 2>/dev/null)
cmd_exit=$?
if [[ $cmd_exit -ne 0 ]]; then
  echo "[$SCRIPT_NAME] ERROR: comando externo salió con código $cmd_exit." >&2
  exit $cmd_exit
fi
if [[ -z "$AUTOR_OUTPUT" ]]; then
  echo "[$SCRIPT_NAME] ERROR: comando externo no produjo salida (¿no leyó stdin?)." >&2
  exit 2
fi

# --- validar que el output es JSON y tiene schema_version=1 ---
if ! echo "$AUTOR_OUTPUT" | python3 -c "import json,sys; d=json.load(sys.stdin); assert d.get('schema_version')==1, 'schema_version != 1'" 2>/dev/null; then
  echo "[$SCRIPT_NAME] ERROR: la salida no es un AutorOutput válido (JSON con schema_version=1)." >&2
  echo "[$SCRIPT_NAME] Primeras líneas: $(echo "$AUTOR_OUTPUT" | head -c 200)" >&2
  exit 2
fi

# --- escribir ---
mkdir -p "$(dirname "$OUT_PATH")"
printf '%s' "$AUTOR_OUTPUT" > "$OUT_PATH"
echo "[$SCRIPT_NAME] OK: AutorOutput escrito en $OUT_PATH" >&2
