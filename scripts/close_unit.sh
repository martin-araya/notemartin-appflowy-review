#!/usr/bin/env bash
# close_unit.sh — cierra una unidad de B3: valida, genera la suite de 5
# checks, lanza el revisor y, si aprueba, marca la cobertura en el ledger.
#
# Uso:
#   close_unit.sh --unit F02.13 [--feature F02] [--gate-100] [--expected 12]
#                  [--min-mermaid 4] [--no-mark]
#
# `--expected` por defecto = `archivos_total` de la unidad.
# `--no-mark` deja la unidad validada pero sin tocar `cobertura.csv` (util para
#   documentos en borrador o de scope-correction con 0 archivos).

set -u
set -o pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
UNIT=""
FEATURE=""
GATE=""
MARK="1"
EXPECTED=""
MIN_MERMAID=4

while [[ $# -gt 0 ]]; do
  case "$1" in
    --unit) UNIT="$2"; shift 2 ;;
    --feature) FEATURE="$2"; shift 2 ;;
    --expected) EXPECTED="$2"; shift 2 ;;
    --min-mermaid) MIN_MERMAID="$2"; shift 2 ;;
    --gate-100) GATE="--gate-100"; shift ;;
    --no-mark) MARK="0"; shift ;;
    -h|--help) sed -n '2,12p' "$0"; exit 0 ;;
    *) echo "argumento desconocido: $1" >&2; exit 2 ;;
  esac
done

[[ -z "$UNIT" ]] && { echo "ERROR: --unit obligatorio" >&2; exit 2; }
UNIT_PATH="$ROOT/OUT/_ledger/units/$UNIT.json"
[[ -f "$UNIT_PATH" ]] || { echo "ERROR: no existe $UNIT_PATH" >&2; exit 2; }

DOC=$(python3 -c "import json;print(json.load(open('$UNIT_PATH'))['documento'])")
FEATURE=${FEATURE:-$(python3 -c "import json;print(json.load(open('$UNIT_PATH')).get('feature_id',''))")}
# Plantilla: las unidades B4.x usan `export-template.md` (11 secciones); las
# B3.* y F* usan la plantilla de feature (19 secciones).
case "$UNIT" in
  B4.*) TEMPLATE="export"; PHASE="$UNIT" ;;
  B1.*) TEMPLATE="structure"; PHASE="$UNIT" ;;
  *)    TEMPLATE="feature"; PHASE="B3.$UNIT" ;;
esac
[[ -z "$EXPECTED" ]] && EXPECTED=$(python3 -c "import json;print(json.load(open('$UNIT_PATH')).get('archivos_total',0))")
DOC_ABS="$ROOT/$DOC"
PRUEBAS="$ROOT/OUT/_ledger/pruebas/$PHASE"

[[ -f "$DOC_ABS" ]] || { echo "ERROR: no existe el documento $DOC_ABS" >&2; exit 2; }
mkdir -p "$PRUEBAS"

echo "== $PHASE ($UNIT) · $EXPECTED archivos · $DOC"
python3 "$ROOT/SKILL/scripts/validate_template.py" -t "$TEMPLATE" "$DOC_ABS" --quiet || {
  echo "FAIL: template ($TEMPLATE)"; exit 1; }

python3 "$ROOT/SKILL/scripts/run_subagent.py" --rol revisor \
  --unit "$UNIT_PATH" --out-root "$ROOT" --out "$PRUEBAS/revisor_output.json" \
  --feature-id "$FEATURE" $GATE --quiet

VEREDICTO=$(python3 -c "
import json;d=json.load(open('$PRUEBAS/revisor_output.json'));print(d.get('veredicto',''))")
CORRECCIONES=$(python3 -c "
import json;d=json.load(open('$PRUEBAS/revisor_output.json'));print(len(d.get('correcciones',[])))")
echo "   revisor: veredicto=$VEREDICTO correcciones=$CORRECCIONES"

if [[ "$VEREDICTO" != "aprobado" ]]; then
  echo "FAIL: el revisor no aprueba; no se marca la cobertura" >&2
  exit 1
fi

python3 "$ROOT/SKILL/scripts/make_phase_suite.py" --phase "$PHASE" --unit "$UNIT" \
  --feature "$FEATURE" --doc "$DOC" --expected "$EXPECTED" \
  --template "$TEMPLATE" $([[ "$UNIT" == B* ]] && echo --transversal) \
  --min-mermaid "$MIN_MERMAID" >/dev/null

# El ledger se actualiza ANTES de lanzar la suite: el check de cobertura
# cuenta las filas con `verificado_por = autor_<UNIT>`.
# Las unidades B* no tocan `cobertura.csv`: sus archivos ya pertenecen a alguna
# feature F* y están verificados (el bloque B4 re-trazа transversalmente).
if [[ "$MARK" == "1" && "$UNIT" != B* ]]; then
  python3 "$ROOT/SKILL/scripts/record_unit_state.py" --unit "$UNIT" --accion verificar \
    --verificado-por "autor_$UNIT" --units-dir "$ROOT/OUT/_ledger/units"
  echo "   ledger: $EXPECTED filas de $UNIT marcadas verificado"
fi

bash "$PRUEBAS/validate-$PHASE.sh" | tee "$PRUEBAS/validate-$PHASE.log"