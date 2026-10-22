#!/usr/bin/env bash
# validate-A3.4.sh — orquestador de la prueba del ROADMAP A3.4.
# Invoca SKILL/scripts/validate_coverage.py sobre los fixtures y
# verifica el comportamiento exigido por la fase.

set -u
set -o pipefail

ROOT="/Users/martin/Desktop/projects/Skills/notemartin-appflowy-review"
SCRIPT="$ROOT/SKILL/scripts/validate_coverage.py"
FIXDIR="$ROOT/OUT/_ledger/pruebas/A3.4/fixtures"
LEDGER_REAL="$ROOT/OUT/_ledger/cobertura.csv"
LOG="$ROOT/OUT/_ledger/pruebas/A3.4/validate.log"

mkdir -p "$(dirname "$LOG")"
: > "$LOG"

log() { printf '[%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" | tee -a "$LOG"; }

PASS=0
FAIL=0
checks=0
check() {
  local name="$1" result="$2" detail="${3:-}"
  checks=$(( checks + 1 ))
  if [[ "$result" == "0" ]]; then
    PASS=$(( PASS + 1 ))
    log "  OK  check $checks: $name"
  else
    FAIL=$(( FAIL + 1 ))
    log "  FAIL check $checks: $name — $detail"
  fi
}

# Wrapper: --no-color para parsear con grep sin ANSI.
run_vc() {
  python3 "$SCRIPT" --no-color "$@"
}

# --- check 1: script ejecutable ---
if [[ -x "$SCRIPT" ]]; then
  check "script ejecutable" 0
else
  check "script ejecutable" 1 "no se encuentra o no es ejecutable: $SCRIPT"
  log "abortando: script no disponible"
  exit 1
fi

# --- check 2: --help ---
HELP_OUT=$(run_vc --help 2>&1)
HELP_RC=$?
if [[ $HELP_RC -eq 0 ]] && printf '%s' "$HELP_OUT" | grep -q "validate_coverage.py"; then
  check "--help imprime uso y sale 0" 0
else
  check "--help imprime uso y sale 0" 1 "rc=$HELP_RC"
fi

# --- check 3: toy_50pct.csv → exit 1, 50.00%, 2 sin_asignar ---
P50_OUT=$(run_vc --ledger "$FIXDIR/toy_50pct.csv" 2>&1)
P50_RC=$?
P50_PCT=$(printf '%s' "$P50_OUT" | grep -oE "[0-9]+\.[0-9]+%" | head -1)
P50_SA=$(printf '%s' "$P50_OUT" | awk '/sin_asignar \(2\)/{f=1; next} f && /^[[:space:]]+- /{c++} f && /pendiente/{exit} END{print c+0}')
if [[ $P50_RC -eq 1 ]] && [[ "$P50_PCT" == "50.00%" ]] && [[ "$P50_SA" -ge 2 ]]; then
  check "toy_50pct.csv: exit 1, global=50.00%, lista 2 sin_asignar" 0
else
  check "toy_50pct.csv: exit 1, global=50.00%, lista 2 sin_asignar" 1 "rc=$P50_RC; pct=$P50_PCT; sa=$P50_SA"
fi

# --- check 4: toy_100pct.csv → exit 0, 100.00%, sin faltantes ---
P100_OUT=$(run_vc --ledger "$FIXDIR/toy_100pct.csv" 2>&1)
P100_RC=$?
P100_PCT=$(printf '%s' "$P100_OUT" | grep -oE "[0-9]+\.[0-9]+%" | head -1)
P100_NO_FALT=$(printf '%s' "$P100_OUT" | grep -c "Sin faltantes" || true)
if [[ $P100_RC -eq 0 ]] && [[ "$P100_PCT" == "100.00%" ]] && [[ "$P100_NO_FALT" -ge 1 ]]; then
  check "toy_100pct.csv: exit 0, global=100.00%, sin faltantes" 0
else
  check "toy_100pct.csv: exit 0, global=100.00%, sin faltantes" 1 "rc=$P100_RC; pct=$P100_PCT; no_falt=$P100_NO_FALT"
fi

# --- check 5: toy_0pct.csv → exit 1, 0.00%, 10 sin_asignar listados ---
P0_OUT=$(run_vc --ledger "$FIXDIR/toy_0pct.csv" 2>&1)
P0_RC=$?
P0_PCT=$(printf '%s' "$P0_OUT" | grep -oE "[0-9]+\.[0-9]+%" | head -1)
P0_SA=$(printf '%s' "$P0_OUT" | awk '/sin_asignar \(10\)/{f=1; next} f && /^[[:space:]]+- /{c++} f && /Cobertura/{exit} END{print c+0}')
if [[ $P0_RC -eq 1 ]] && [[ "$P0_PCT" == "0.00%" ]] && [[ "$P0_SA" -ge 10 ]]; then
  check "toy_0pct.csv: exit 1, global=0.00%, lista 10 sin_asignar" 0
else
  check "toy_0pct.csv: exit 1, global=0.00%, lista 10 sin_asignar" 1 "rc=$P0_RC; pct=$P0_PCT; sa=$P0_SA"
fi

# --- check 6: toy_multi_capa.csv → 3 capas y global=50.00% ---
PMC_OUT=$(run_vc --ledger "$FIXDIR/toy_multi_capa.csv" 2>&1)
PMC_RC=$?
PMC_GLOBAL=$(printf '%s' "$PMC_OUT" | grep -E "GLOBAL.*50\.00%" | head -1)
PMC_HAS_RH=$(printf '%s' "$PMC_OUT" | grep -c "rust-handler" || true)
PMC_HAS_SVC=$(printf '%s' "$PMC_OUT" | grep -c "^service " || true)
PMC_HAS_UI=$(printf '%s' "$PMC_OUT" | grep -c "^ui " || true)
if [[ $PMC_RC -eq 1 ]] \
   && [[ -n "$PMC_GLOBAL" ]] \
   && [[ "$PMC_HAS_RH" -ge 1 ]] \
   && [[ "$PMC_HAS_SVC" -ge 1 ]] \
   && [[ "$PMC_HAS_UI" -ge 1 ]]; then
  check "toy_multi_capa.csv: 3 capas (ui/service/rust-handler), global=50.00%" 0
else
  check "toy_multi_capa.csv: 3 capas (ui/service/rust-handler), global=50.00%" 1 "rc=$PMC_RC; global='$PMC_GLOBAL'; ui=$PMC_HAS_UI; svc=$PMC_HAS_SVC; rh=$PMC_HAS_RH"
fi

# --- check 7: --json produce JSON parseable con global.pct == 50.0 ---
# Nota: el script puede salir 1 (umbral no cumplido) pero el JSON es
# válido; sólo validamos la parseabilidad + contenido.
JSON_OUT=$(run_vc --json --ledger "$FIXDIR/toy_50pct.csv" 2>/dev/null || true)
if printf '%s' "$JSON_OUT" | python3 -m json.tool >/dev/null 2>&1; then
  JSON_PCT=$(printf '%s' "$JSON_OUT" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d["global"]["pct"])' 2>/dev/null)
  if [[ "$JSON_PCT" == "50.0" ]]; then
    check "--json produce JSON parseable con global.pct == 50.0" 0
  else
    check "--json produce JSON parseable con global.pct == 50.0" 1 "pct=$JSON_PCT"
  fi
else
  check "--json produce JSON parseable con global.pct == 50.0" 1 "json inválido"
fi

# --- check 8: modo real sobre cobertura.csv actual ---
REAL_OUT=$(run_vc --quiet --limit 5 --ledger "$LEDGER_REAL" 2>&1)
REAL_RC=$?
REAL_PCT=$(printf '%s' "$REAL_OUT" | grep -oE "[0-9]+\.[0-9]+%" | head -1)
if [[ $REAL_RC -eq 1 ]] && [[ "$REAL_PCT" == "0.00%" ]]; then
  check "modo real cobertura.csv: exit 1, global=0.00% (4.603 sin_asignar)" 0
else
  check "modo real cobertura.csv: exit 1, global=0.00% (4.603 sin_asignar)" 1 "rc=$REAL_RC; pct=$REAL_PCT"
fi

# --- check 9: --threshold 50 sobre toy_50pct → exit 0 ---
T50_OUT=$(run_vc --quiet --threshold 50 --ledger "$FIXDIR/toy_50pct.csv" 2>&1)
T50_RC=$?
if [[ $T50_RC -eq 0 ]]; then
  check "--threshold 50 sobre toy_50pct (50% >= 50) → exit 0" 0
else
  check "--threshold 50 sobre toy_50pct (50% >= 50) → exit 0" 1 "rc=$T50_RC"
fi

# --- check 10: --threshold 51 sobre toy_50pct → exit 1 ---
T51_OUT=$(run_vc --quiet --threshold 51 --ledger "$FIXDIR/toy_50pct.csv" 2>&1)
T51_RC=$?
if [[ $T51_RC -eq 1 ]]; then
  check "--threshold 51 sobre toy_50pct (50% < 51) → exit 1" 0
else
  check "--threshold 51 sobre toy_50pct (50% < 51) → exit 1" 1 "rc=$T51_RC"
fi

# --- summary ---
log "---"
log "resultado: $PASS/$checks checks OK ($FAIL fallidos)"
if [[ $FAIL -eq 0 ]]; then
  log "OK: A3.4 (validate_coverage.py funciona: lee CSV, calcula % global y por capa, lista faltantes, soporta threshold y JSON)"
  exit 0
else
  log "FAIL: A3.4 (revisar logs)"
  exit 1
fi
