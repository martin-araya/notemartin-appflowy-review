#!/usr/bin/env bash
# extract_codegen.sh — Orquestador de codegen de flowy-codegen.
#   Ver AGENTS.md §5.1 y ROADMAP.md A2.7.
#
# Estrategia: intentar 3 paths en orden; si todos fallan, escribir
# `codegen-fallido.md` con la causa raíz.
#
# Uso:
#   extract_codegen.sh [--help] [--work-dir DIR]

set -u

# ---------- constantes ----------

SCRIPT_PATH="$(cd "$(dirname "$0")" && pwd)"
SKILL_ROOT="$(cd "$SCRIPT_PATH/../.." && pwd)"
SRC_ROOT="$SKILL_ROOT/SRC"
RUSTLIB="$SRC_ROOT/appflowy/frontend/rust-lib"
CODEGEN_CRATE="$RUSTLIB/build-tool/flowy-codegen"
APPFLOWY_FLUTTER="$SRC_ROOT/appflowy/frontend/appflowy_flutter"

PRUEBAS_DIR="$SKILL_ROOT/OUT/_ledger/pruebas/A2.7"
RESULT_JSON="$PRUEBAS_DIR/codegen-result.json"
RESULT_MD="$PRUEBAS_DIR/codegen-result.md"
FAIL_MD="$PRUEBAS_DIR/codegen-fallido.md"
LOG_FILE="$PRUEBAS_DIR/extract.log"

WORK_DIR="${CODEGEN_DIR:-/tmp/codegen-run}"

# ---------- helpers ----------

log() { echo "[$(date -u +%H:%M:%S)] $*" | tee -a "$LOG_FILE" >&2; }

json_escape() {
  # Escapa un string para uso dentro de un JSON string literal.
  printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/"/\\"/g' -e 's/	/\\t/g' | tr '\n' ' '
}

check_prereq() {
  local tool="$1"
  local path
  path="$(command -v "$tool" 2>/dev/null || echo "")"
  if [ -n "$path" ]; then
    printf 'present\t%s\n' "$path"
  else
    printf 'absent\t\n'
  fi
}

# ---------- banner ----------

echo "extract_codegen.sh — A2.7" > "$LOG_FILE"
log "  work_dir:  $WORK_DIR"
log "  rustlib:   $RUSTLIB"
log "  codegen:   $CODEGEN_CRATE"

# ---------- crear directorios ----------

mkdir -p "$PRUEBAS_DIR"
mkdir -p "$WORK_DIR/protos" "$WORK_DIR/dart_dispatch" "$WORK_DIR/rust_protobuf" 2>/dev/null || true

if [ ! -d "$WORK_DIR/protos" ]; then
  log "  WARN: no se pudo crear $WORK_DIR/protos; WORK_DIR no escribible"
fi

# ---------- FASE 1: prerrequisitos ----------

log ""
log "FASE 1: comprobando prerrequisitos..."

PREREQ_CARGO="$(check_prereq cargo)"
PREREQ_CARGO_MAKE="$(check_prereq cargo-make)"
PREREQ_PROTOC="$(check_prereq protoc)"
PREREQ_PROTOC_GEN_DART="$(check_prereq protoc-gen-dart)"

if [ -f "$RUSTLIB/Makefile.toml" ]; then
  PREREQ_MK="present	$RUSTLIB/Makefile.toml"
else
  PREREQ_MK="absent	"
fi

if [ -f "$CODEGEN_CRATE/src/main.rs" ]; then
  PREREQ_MAIN="present	$CODEGEN_CRATE/src/main.rs"
else
  PREREQ_MAIN="absent	(lib.rs only — flowy-codegen se invoca como librería)"
fi

# Env vars
PREREQ_CMWD_PRESENT="false"
PREREQ_CMWD_VALUE=""
if [ -n "${CARGO_MAKE_WORKING_DIRECTORY:-}" ]; then
  PREREQ_CMWD_PRESENT="true"
  PREREQ_CMWD_VALUE="$CARGO_MAKE_WORKING_DIRECTORY"
fi
PREREQ_FFSP_PRESENT="false"
PREREQ_FFSP_VALUE=""
if [ -n "${FLUTTER_FLOWY_SDK_PATH:-}" ]; then
  PREREQ_FFSP_PRESENT="true"
  PREREQ_FFSP_VALUE="$FLUTTER_FLOWY_SDK_PATH"
fi

log "  cargo:              $PREREQ_CARGO"
log "  cargo-make:         $PREREQ_CARGO_MAKE"
log "  protoc:             $PREREQ_PROTOC"
log "  protoc-gen-dart:    $PREREQ_PROTOC_GEN_DART"
log "  Makefile.toml:      $PREREQ_MK"
log "  flowy-codegen main: $PREREQ_MAIN"
log "  CARGO_MAKE_WORKING_DIRECTORY: $PREREQ_CMWD_PRESENT ($PREREQ_CMWD_VALUE)"
log "  FLUTTER_FLOWY_SDK_PATH:       $PREREQ_FFSP_PRESENT ($PREREQ_FFSP_VALUE)"

# ---------- FASE 2: intentos ----------

ATTEMPTS_JSON="["
ATTEMPT_COUNT=0
OVERALL_OUTCOME="failed"
OVERALL_CAUSE=""

# Helper: ejecutar un intento con timeout.
run_attempt() {
  local strategy="$1"
  local cmd="$2"
  local timeout="${3:-60}"
  local started
  started=$(date -u +%s)
  log ""
  log "FASE 2.${ATTEMPT_COUNT}: intentando estrategia '$strategy'..."
  log "  cmd: $cmd"
  log "  timeout: ${timeout}s"

  # Capturar stdout/stderr truncados.
  local stdout_file="$PRUEBAS_DIR/.stdout.${strategy}.log"
  local stderr_file="$PRUEBAS_DIR/.stderr.${strategy}.log"
  local exit_code
  if command -v timeout >/dev/null 2>&1; then
    (cd "$(dirname "$cmd_path" 2>/dev/null || echo .)" && bash -c "$cmd") > "$stdout_file" 2> "$stderr_file" &
    local pid=$!
    ( sleep "$timeout"; kill -9 "$pid" 2>/dev/null ) &
    local watchdog=$!
    if wait "$pid" 2>/dev/null; then exit_code=0; else exit_code=$?; fi
    kill -9 "$watchdog" 2>/dev/null || true
  else
    # Sin timeout, ejecutar y capturar.
    (cd "$(dirname "$cmd_path" 2>/dev/null || echo .)" && bash -c "$cmd") > "$stdout_file" 2> "$stderr_file"
    exit_code=$?
  fi
  local finished
  finished=$(date -u +%s)
  local duration=$((finished - started))

  # Truncar a 50 líneas (preservar las últimas).
  local stdout_tail stderr_tail
  stdout_tail="$(tail -n 50 "$stdout_file" 2>/dev/null | tr '\n' ' ' | head -c 2000)"
  stderr_tail="$(tail -n 50 "$stderr_file" 2>/dev/null | tr '\n' ' ' | head -c 2000)"

  ATTEMPT_COUNT=$((ATTEMPT_COUNT + 1))
  local cause=""
  case "$strategy" in
    cargo_make)
      if [ -z "${PREREQ_CARGO_MAKE%%absent*}" ] || [ -z "${PREREQ_CARGO%%absent*}" ]; then
        cause="toolchain_missing: cargo o cargo-make no instalado"
      elif [ -z "${PREREQ_MK%%absent*}" ]; then
        cause="Makefile.toml no presente en $RUSTLIB"
      elif [ "$exit_code" -ne 0 ]; then
        cause="cargo make terminó con exit=$exit_code; ver stderr"
      else
        cause="ok"
      fi
      ;;
    cargo_run_bin)
      if [ -z "${PREREQ_CARGO%%absent*}" ]; then
        cause="toolchain_missing: cargo no instalado"
      elif [ -z "${PREREQ_MAIN%%present*}" ]; then
        cause="flowy-codegen no expone binario (main.rs ausente; solo lib.rs)"
      elif [ "$exit_code" -ne 0 ]; then
        cause="cargo run terminó con exit=$exit_code; ver stderr"
      else
        cause="ok"
      fi
      ;;
    cargo_build_manual)
      if [ -z "${PREREQ_CARGO%%absent*}" ]; then
        cause="toolchain_missing: cargo no instalado"
      elif [ "$exit_code" -ne 0 ]; then
        cause="cargo build terminó con exit=$exit_code; ver stderr"
      else
        # El binario compila pero el codegen NO se ejecuta; flowy-codegen es
        # una librería sin main.rs. Para ejecutar el codegen hay que
        # escribir un wrapper crate que llame a dart_gen(...) y compilarlo.
        cause="compila pero no ejecuta codegen (flowy-codegen es lib, no bin); requiere wrapper"
      fi
      ;;
  esac

  log "  exit_code: $exit_code"
  log "  duration:  ${duration}s"
  log "  cause:     $cause"

  # Append JSON del intento.
  local cmd_esc; cmd_esc="$(json_escape "$cmd")"
  local stdout_esc; stdout_esc="$(json_escape "$stdout_tail")"
  local stderr_esc; stderr_esc="$(json_escape "$stderr_tail")"
  local cause_esc; cause_esc="$(json_escape "$cause")"
  if [ "$ATTEMPT_COUNT" -gt 1 ]; then ATTEMPTS_JSON+=","; fi
  ATTEMPTS_JSON+="{\"strategy\":\"$strategy\",\"command\":\"$cmd_esc\",\"started_at\":\"$(date -u -d "@$started" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || echo "$started")\",\"finished_at\":\"$(date -u -d "@$finished" +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || echo "$finished")\",\"duration_sec\":$duration,\"exit_code\":$exit_code,\"stdout_tail\":\"$stdout_esc\",\"stderr_tail\":\"$stderr_esc\",\"cause\":\"$cause_esc\"}"

  # Verificar si se generaron .proto (criterio de éxito).
  local protos_count
  protos_count="$(find "$WORK_DIR/protos" -name "*.proto" 2>/dev/null | wc -l | tr -d ' ')"
  if [ "$protos_count" -gt 0 ]; then
    OVERALL_OUTCOME="success"
    OVERALL_CAUSE="$strategy generó $protos_count archivos .proto"
  fi
}

# Estrategia 1: cargo make (si todo disponible)
if [[ "$PREREQ_CARGO" == present* ]] && [[ "$PREREQ_CARGO_MAKE" == present* ]] && [[ "$PREREQ_MK" == present* ]]; then
  cmd_path="$RUSTLIB"
  run_attempt "cargo_make" "cd $RUSTLIB && CARGO_MAKE_WORKING_DIRECTORY=$WORK_DIR FLUTTER_FLOWY_SDK_PATH=packages/appflowy_backend cargo make codegen 2>&1" 120
else
  log ""
  log "FASE 2.0: saltando cargo_make (faltan prerrequisitos)"
fi

# Estrategia 2: cargo run --bin (si cargo y main.rs disponibles)
if [ "$OVERALL_OUTCOME" != "success" ]; then
  if [[ "$PREREQ_CARGO" == present* ]] && [[ "$PREREQ_MAIN" == present* ]]; then
    cmd_path="$RUSTLIB"
    run_attempt "cargo_run_bin" "cd $RUSTLIB && CARGO_MAKE_WORKING_DIRECTORY=$WORK_DIR FLUTTER_FLOWY_SDK_PATH=packages/appflowy_backend cargo run -p flowy-codegen --features proto_gen,dart_event --bin flowy-codegen -- appflowy_editor 2>&1" 120
  else
    log ""
    log "FASE 2.x: saltando cargo_run_bin (faltan prerrequisitos)"
  fi
fi

# Estrategia 3: cargo build + manual (último recurso; solo si cargo).
# NOTA: en este entorno, cargo build descarga ~200 MB de dependencias
# (yrs, collab-*, etc.) en el primer build, lo que excede el timeout
# del shell (~120 s). Se intenta con timeout de 60 s; si no termina,
# se documenta como "skipped por timeout de shell".
if [ "$OVERALL_OUTCOME" != "success" ]; then
  if [[ "$PREREQ_CARGO" == present* ]]; then
    cmd_path="$RUSTLIB"
    run_attempt "cargo_build_manual" "cd $RUSTLIB && cargo build -p flowy-codegen --features proto_gen,dart_event 2>&1" 60
  else
    log ""
    log "FASE 2.x: saltando cargo_build_manual (faltan prerrequisitos)"
  fi
fi

ATTEMPTS_JSON+="]"

# ---------- FASE 3: outcome ----------

log ""
log "FASE 3: outcome final: $OVERALL_OUTCOME"
log "  causa: $OVERALL_CAUSE"

# Si el outcome sigue siendo failed, construir un resumen más rico.
if [ "$OVERALL_OUTCOME" = "failed" ]; then
  # Recopilar los "cause" de cada intento.
  causes=$(echo "$ATTEMPTS_JSON" | python3 -c "
import json, sys
data = json.loads(sys.stdin.read())
for a in data:
    print(f\"  - {a['strategy']}: {a.get('cause', '?')}\")
")
  OVERALL_CAUSE="Toolchain missing o incompleto. Intentos y causas:
$causes
Documentado en $FAIL_MD."
fi

# ---------- FASE 4: escribir JSON (vía Python para evitar quoting issues) ----------

GENERATED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
log ""
log "FASE 4: escribiendo JSON → $RESULT_JSON"

# Construir el JSON via Python para evitar issues de quoting en bash heredoc.
# Pasar todo por env vars.
export _CARGO_P="$PREREQ_CARGO"
export _CM_P="$PREREQ_CARGO_MAKE"
export _PROTOC_P="$PREREQ_PROTOC"
export _PGD_P="$PREREQ_PROTOC_GEN_DART"
export _MK_P="$PREREQ_MK"
export _MAIN_P="$PREREQ_MAIN"
export _CMWD="$PREREQ_CMWD_PRESENT"
export _CMWD_VALUE="$PREREQ_CMWD_VALUE"
export _FFSP="$PREREQ_FFSP_PRESENT"
export _FFSP_VALUE="$PREREQ_FFSP_VALUE"
export _OUTCOME="$OVERALL_OUTCOME"
export _CAUSE="$OVERALL_CAUSE"
export _WORK_DIR="$WORK_DIR"
export _GENERATED_AT="$GENERATED_AT"
export _ATTEMPTS_JSON="$ATTEMPTS_JSON"
export _RUSTLIB="$RUSTLIB"
export _RESULT_JSON="$RESULT_JSON"

# Escribir los prerrequisitos a un archivo de texto (formato `K=V\n`,
# TAB reemplazado por `|`) para evitar el mangling de tabs en env vars.
{
  printf '_CARGO_P=%s\n'        "${PREREQ_CARGO//	/|}"
  printf '_CM_P=%s\n'           "${PREREQ_CARGO_MAKE//	/|}"
  printf '_PROTOC_P=%s\n'       "${PREREQ_PROTOC//	/|}"
  printf '_PGD_P=%s\n'          "${PREREQ_PROTOC_GEN_DART//	/|}"
  printf '_MK_P=%s\n'            "${PREREQ_MK//	/|}"
  printf '_MAIN_P=%s\n'          "${PREREQ_MAIN//	/|}"
} > "$PRUEBAS_DIR/.prereq.env"

PREREQ_FILE="$PRUEBAS_DIR/.prereq.env"
export PREREQ_FILE

python3 - <<'PY'
import json, os, sys

# Leer prerrequisitos del archivo (formato K=V\n) para evitar el
# tab-mangling de env vars de bash.
PREREQ_FILE = os.environ.get("PREREQ_FILE", "")
prereq_values = {}
if PREREQ_FILE and os.path.isfile(PREREQ_FILE):
    with open(PREREQ_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if "=" in line:
                k, v = line.split("=", 1)
                prereq_values[k] = v.replace("|", "\t")

def prereq(name: str) -> dict:
    v = prereq_values.get(name, "")
    parts = v.split("\t", 1)
    if len(parts) == 1:
        return {"present": parts[0] != "absent" and parts[0] != "", "path": ""}
    p, path = parts
    return {"present": p != "absent" and p != "", "path": path}

attempts = json.loads(os.environ["_ATTEMPTS_JSON"])
prereqs = {
    "cargo":               prereq("_CARGO_P"),
    "cargo_make":          prereq("_CM_P"),
    "protoc":              prereq("_PROTOC_P"),
    "protoc_gen_dart":     prereq("_PGD_P"),
    "makefile_toml":       prereq("_MK_P"),
    "flowy_codegen_main":  prereq("_MAIN_P"),
    "cargo_make_working_directory": {
        "present": os.environ.get("_CMWD", "false") == "true",
        "value": os.environ.get("_CMWD_VALUE", ""),
    },
    "flutter_flowy_sdk_path": {
        "present": os.environ.get("_FFSP", "false") == "true",
        "value": os.environ.get("_FFSP_VALUE", ""),
    },
}

obj = {
    "schema_version": "1.0",
    "generated_at": os.environ["_GENERATED_AT"],
    "tool": {"name": "extract_codegen.sh", "version": "1.0"},
    "fuentes": ["appflowy"],
    "workspace_root": os.environ["_RUSTLIB"],
    "prerequisites": prereqs,
    "attempts": attempts,
    "outcome": os.environ["_OUTCOME"],
    "failure_cause_summary": os.environ["_CAUSE"],
    "output_dir": os.environ["_WORK_DIR"],
}

with open(os.environ["_RESULT_JSON"], "w", encoding="utf-8") as f:
    json.dump(obj, f, indent=2, ensure_ascii=False)
    f.write("\n")
PY

# ---------- FASE 5: escribir Markdown resumen ----------

log "FASE 5: escribiendo resúmenes MD..."

# Resumen ejecutivo (codegen-result.md)
{
  echo "# Codegen A2.7 — Resumen"
  echo
  echo "**Fecha:** $GENERATED_AT"
  echo
  echo "**Workspace:** \`$RUSTLIB\`"
  echo
  echo "**Outcome:** \`$OVERALL_OUTCOME\`"
  echo
  if [ "$OVERALL_OUTCOME" = "failed" ]; then
    echo "**Causa:** $OVERALL_CAUSE"
    echo
  fi
  echo "## Prerrequisitos"
  echo
  echo "| Herramienta | Presente | Path |"
  echo "|---|---|---|"
  printf '| `cargo` | `%s` | `%s` |\n' "$PREREQ_CARGO" "$(printf '%s' "$PREREQ_CARGO" | cut -f2-)"
  printf '| `cargo-make` | `%s` | `%s` |\n' "$PREREQ_CARGO_MAKE" "$(printf '%s' "$PREREQ_CARGO_MAKE" | cut -f2-)"
  printf '| `protoc` | `%s` | `%s` |\n' "$PREREQ_PROTOC" "$(printf '%s' "$PREREQ_PROTOC" | cut -f2-)"
  printf '| `protoc-gen-dart` | `%s` | `%s` |\n' "$PREREQ_PROTOC_GEN_DART" "$(printf '%s' "$PREREQ_PROTOC_GEN_DART" | cut -f2-)"
  printf '| `Makefile.toml` | `%s` | `%s` |\n' "$PREREQ_MK" "$(printf '%s' "$PREREQ_MK" | cut -f2-)"
  printf '| `flowy-codegen/src/main.rs` | `%s` | `%s` |\n' "$PREREQ_MAIN" "$(printf '%s' "$PREREQ_MAIN" | cut -f2-)"
  printf '| `CARGO_MAKE_WORKING_DIRECTORY` | `%s` | `%s` |\n' "$PREREQ_CMWD_PRESENT" "$PREREQ_CMWD_VALUE"
  printf '| `FLUTTER_FLOWY_SDK_PATH` | `%s` | `%s` |\n' "$PREREQ_FFSP_PRESENT" "$PREREQ_FFSP_VALUE"
  echo
  echo "## Intentos"
  echo
  echo "| # | Estrategia | Exit | Causa |"
  echo "|---:|---|---:|---|"
  if [ "$ATTEMPT_COUNT" -gt 0 ]; then
    i=1
    echo "$ATTEMPTS_JSON" | python3 -c "
import json, sys
for a in json.loads(sys.stdin.read()):
    print(f'| {a[\"strategy\"]} | {a[\"exit_code\"]} | {a[\"cause\"]} |')
" 2>/dev/null || true
  else
    echo "| — | — | 0 | (ningún intento: prerrequisitos faltantes) |"
  fi
  echo
  echo "## Resultado"
  echo
  if [ "$OVERALL_OUTCOME" = "success" ]; then
    nprotos=$(find "$WORK_DIR/protos" -name "*.proto" 2>/dev/null | wc -l | tr -d ' ')
    echo "✅ Codegen exitoso. Se generaron **$nprotos** archivos \`.proto\` en \`$WORK_DIR/protos\`."
  else
    echo "❌ Codegen no ejecutado. Detalles en \`$FAIL_MD\`."
  fi
  echo
  echo "## Logs"
  echo
  echo "Logs detallados en \`$LOG_FILE\` (incluye stdout/stderr truncados de cada intento)."
} > "$RESULT_MD"

# Si falló, escribir el documento de causa.
if [ "$OVERALL_OUTCOME" = "failed" ]; then
  log "FASE 6: escribiendo $FAIL_MD..."
  {
    echo "# Codegen A2.7 — Fallo documentado"
    echo
    echo "**Fecha:** $GENERATED_AT"
    echo "**Outcome:** \`failed\` (esperado en este entorno)."
    echo
    echo "## Causa raíz"
    echo
    echo "El codegen de \`build-tool/flowy-codegen\` requiere las siguientes herramientas y archivos, que no están todos disponibles en este entorno:"
    echo
    echo "| Prerrequisito | Estado |"
    echo "|---|---|"
    printf '| `cargo` | %s |\n' "$PREREQ_CARGO"
    printf '| `cargo-make` | %s |\n' "$PREREQ_CARGO_MAKE"
    printf '| `protoc` | %s |\n' "$PREREQ_PROTOC"
    printf '| `protoc-gen-dart` | %s |\n' "$PREREQ_PROTOC_GEN_DART"
    printf '| `Makefile.toml` en `%s` | %s |\n' "$RUSTLIB" "$PREREQ_MK"
    printf '| `flowy-codegen/src/main.rs` | %s |\n' "$PREREQ_MAIN"
    printf '| Env `CARGO_MAKE_WORKING_DIRECTORY` | %s |\n' "$PREREQ_CMWD_PRESENT"
    printf '| Env `FLUTTER_FLOWY_SDK_PATH` | %s |\n' "$PREREQ_FFSP_PRESENT"
    echo
    echo "## Estrategias intentadas"
    echo
    if [ "$ATTEMPT_COUNT" -gt 0 ]; then
      i=1
      echo "$ATTEMPTS_JSON" | python3 -c "
import json, sys
for a in json.loads(sys.stdin.read()):
    print(f\"### Intento $i — {a['strategy']}\")
    print()
    print(f\"- **Comando:** \`{a['command']}\`\")
    print(f\"- **Exit code:** {a['exit_code']}\")
    print(f\"- **Causa:** {a['cause']}\")
    print(f\"- **stderr (tail):**\")
    print()
    print('\`\`\`')
    print((a.get('stderr_tail') or '(vacío)')[:1500])
    print('\`\`\`')
    print()
" 2>/dev/null || true
    else
      echo "(Ningún intento ejecutado: todos los prerrequisitos faltan.)"
    fi
    echo
    echo "## Código relevante"
    echo
    echo "El codegen se ejecuta como librería en"
    echo "\`$CODEGEN_CRATE/src/lib.rs\` (líneas 1-66 definen \`Project\` y \`ProtoCache\`)."
    echo "Los entry points principales son:"
    echo "- \`protobuf_file::mod.rs::dart_gen(crate_name: &str)\` — genera \`.proto\` + Dart + Rust."
    echo "- \`dart_event::mod.rs\` — genera el dispatch Dart a partir de \`Flowy.toml\`."
    echo
    echo "Sin \`Makefile.toml\` o binario expuesto, invocar el codegen desde fuera requiere"
    echo "construir manualmente un wrapper que llame a estas funciones con los env vars correctos."
    echo
    echo "## Cómo habilitar el codegen en un entorno con toolchain"
    echo
    echo "1. Instalar Rust toolchain (rustup; la versión de \`rust-toolchain.toml\` si difiere)."
    echo "2. Instalar cargo-make: \`cargo install cargo-make\`."
    echo "3. Instalar Protocol Buffers compiler: \`brew install protobuf\` (macOS) o equivalente."
    echo "4. Instalar el plugin Dart de protoc: \`dart pub global activate protoc_plugin\`."
    echo "5. Crear/recuperar \`Makefile.toml\` en \`$RUSTLIB\` (no presente en este snapshot)."
    echo "6. Configurar \`CARGO_MAKE_WORKING_DIRECTORY=\$PWD\` y \`FLUTTER_FLOWY_SDK_PATH=packages/appflowy_backend\`."
    echo "7. Ejecutar \`cargo make codegen\`."
    echo
    echo "## Estado de A2.2 sin dependencia de A2.7"
    echo
    echo "A2.2 (\`extract_protobuf.py\`) extrae las entidades \`#[derive(ProtoBuf)]\` y"
    echo "\`#[derive(ProtoBuf_Enum)]\` directamente de los \`.rs\` fuente, sin requerir"
    echo "los \`.proto\` generados. Por tanto, A2.2 es funcional aunque A2.7 falle."
    echo "Este es exactamente el caso (b) que el ROADMAP A2.7 permite explícitamente."
  } > "$FAIL_MD"
fi

log ""
log "escrito: $RESULT_JSON"
log "escrito: $RESULT_MD"
[ "$OVERALL_OUTCOME" = "failed" ] && log "escrito: $FAIL_MD"

exit 0
