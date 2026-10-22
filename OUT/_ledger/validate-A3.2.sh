#!/usr/bin/env bash
# validate-A3.2.sh — orquestador de la prueba del ROADMAP A3.2.
# Invoca SKILL/scripts/validate_evidence.py sobre los fixtures y
# verifica el comportamiento exigido por la fase.

set -u
set -o pipefail

ROOT="/Users/martin/Desktop/projects/Skills/notemartin-appflowy-review"
SCRIPT="$ROOT/SKILL/scripts/validate_evidence.py"
FIXDIR="$ROOT/OUT/_ledger/pruebas/A3.2/fixtures"
INVENTARIO="$ROOT/OUT/_ledger/inventario.json"
LOG="$ROOT/OUT/_ledger/pruebas/A3.2/validate.log"

# Wrapper: invoca validate_evidence.py con --no-color para que el output
# sea parseable por grep sin sorpresas por códigos ANSI.
run_ve() {
  python3 "$SCRIPT" --no-color "$@"
}

mkdir -p "$(dirname "$LOG")"
: > "$LOG"

log() { printf '[%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" | tee -a "$LOG"; }

# --- pre-check: inventario ---
if [[ ! -f "$INVENTARIO" ]]; then
  log "SKIP: A3.2 (inventario.json no encontrado. Ejecutar A1.2 primero.)"
  log "exit=77"
  exit 77
fi

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

# --- check 1: script ejecutable ---
if [[ -x "$SCRIPT" ]]; then
  check "script ejecutable" 0
else
  check "script ejecutable" 1 "no se encuentra o no es ejecutable: $SCRIPT"
  log "abortando: script no disponible"
  exit 1
fi

# --- check 2: --help ---
HELP_OUT=$(run_ve --help 2>&1)
HELP_RC=$?
if [[ $HELP_RC -eq 0 ]] && printf '%s' "$HELP_OUT" | grep -q "validate_evidence.py"; then
  check "--help imprime uso y sale 0" 0
else
  check "--help imprime uso y sale 0" 1 "rc=$HELP_RC"
fi

# --- check 3: inventario presente ---
if [[ -f "$INVENTARIO" ]]; then
  check "inventario.json presente" 0
else
  check "inventario.json presente" 1 "falta $INVENTARIO"
  exit 1
fi

# --- check 4: valid.md exit 0 y 0 errores ---
POS_OUT=$(run_ve "$FIXDIR/valid.md" 2>&1)
POS_RC=$?
POS_ERR_COUNT=$(printf '%s' "$POS_OUT" | grep -c "^ERROR" || true)
if [[ $POS_RC -eq 0 ]] && [[ "$POS_ERR_COUNT" -eq 0 ]]; then
  check "valid.md exit 0 con 0 errores" 0
else
  check "valid.md exit 0 con 0 errores" 1 "rc=$POS_RC; errores=$POS_ERR_COUNT"
fi

# --- check 5: fake_path.md exit 1 + E_PATH_NOT_IN_INVENTORY + ref :1: ---
FP_OUT=$(run_ve "$FIXDIR/fake_path.md" 2>&1)
FP_RC=$?
FP_HAS_CODE=$(printf '%s' "$FP_OUT" | grep -c "E_PATH_NOT_IN_INVENTORY" || true)
FP_HAS_REF=$(printf '%s' "$FP_OUT" | grep -cE "ERROR .*fake_path\.md:1:" || true)
if [[ $FP_RC -eq 1 ]] && [[ "$FP_HAS_CODE" -ge 1 ]] && [[ "$FP_HAS_REF" -ge 1 ]]; then
  check "fake_path.md exit 1 con E_PATH_NOT_IN_INVENTORY en ref :1:" 0
else
  check "fake_path.md exit 1 con E_PATH_NOT_IN_INVENTORY en ref :1:" 1 "rc=$FP_RC; code=$FP_HAS_CODE; ref=$FP_HAS_REF"
fi

# --- check 6: out_of_range.md exit 1 + E_LINE_OUT_OF_RANGE ---
OOR_OUT=$(run_ve "$FIXDIR/out_of_range.md" 2>&1)
OOR_RC=$?
OOR_HAS_CODE=$(printf '%s' "$OOR_OUT" | grep -c "E_LINE_OUT_OF_RANGE" || true)
OOR_HAS_REF=$(printf '%s' "$OOR_OUT" | grep -cE "ERROR .*out_of_range\.md:1:" || true)
if [[ $OOR_RC -eq 1 ]] && [[ "$OOR_HAS_CODE" -ge 1 ]] && [[ "$OOR_HAS_REF" -ge 1 ]]; then
  check "out_of_range.md exit 1 con E_LINE_OUT_OF_RANGE en ref :1:" 0
else
  check "out_of_range.md exit 1 con E_LINE_OUT_OF_RANGE en ref :1:" 1 "rc=$OOR_RC; code=$OOR_HAS_CODE; ref=$OOR_HAS_REF"
fi

# --- check 7: mixed.md exit 1 + EXACTAMENTE 3 errores en refs 2, 3, 4 ---
MIX_OUT=$(run_ve "$FIXDIR/mixed.md" 2>&1)
MIX_RC=$?
MIX_ERROR_LINES=$(printf '%s' "$MIX_OUT" | grep -cE "^ERROR .*mixed\.md:[0-9]+:" || true)
MIX_HAS_R2=$(printf '%s' "$MIX_OUT" | grep -cE "ERROR .*mixed\.md:2:" || true)
MIX_HAS_R3=$(printf '%s' "$MIX_OUT" | grep -cE "ERROR .*mixed\.md:3:" || true)
MIX_HAS_R4=$(printf '%s' "$MIX_OUT" | grep -cE "ERROR .*mixed\.md:4:" || true)
MIX_HAS_R1=$(printf '%s' "$MIX_OUT" | grep -cE "ERROR .*mixed\.md:1:" || true)
MIX_HAS_R5=$(printf '%s' "$MIX_OUT" | grep -cE "ERROR .*mixed\.md:5:" || true)
if [[ $MIX_RC -eq 1 ]] \
   && [[ "$MIX_ERROR_LINES" -eq 3 ]] \
   && [[ "$MIX_HAS_R2" -ge 1 && "$MIX_HAS_R3" -ge 1 && "$MIX_HAS_R4" -ge 1 ]] \
   && [[ "$MIX_HAS_R1" -eq 0 && "$MIX_HAS_R5" -eq 0 ]]; then
  check "mixed.md exit 1, 3 errores en refs :2: :3: :4: (no :1: ni :5:)" 0
else
  check "mixed.md exit 1, 3 errores en refs :2: :3: :4: (no :1: ni :5:)" 1 "rc=$MIX_RC; total=$MIX_ERROR_LINES; r1=$MIX_HAS_R1; r2=$MIX_HAS_R2; r3=$MIX_HAS_R3; r4=$MIX_HAS_R4; r5=$MIX_HAS_R5"
fi

# --- check 8: --json produce JSON parseable ---
JSON_OUT=$(run_ve --json "$FIXDIR/valid.md" 2>/dev/null)
JSON_RC=$?
if [[ $JSON_RC -eq 0 ]] && printf '%s' "$JSON_OUT" | python3 -m json.tool >/dev/null 2>&1; then
  JSON_OK=$(printf '%s' "$JSON_OUT" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d["summary"]["errors"])' 2>/dev/null)
  if [[ "$JSON_OK" == "0" ]]; then
    check "--json produce JSON parseable con errors==0" 0
  else
    check "--json produce JSON parseable con errors==0" 1 "errors=$JSON_OK"
  fi
else
  check "--json produce JSON parseable con errors==0" 1 "rc=$JSON_RC; json inválido"
fi

# --- check 9: modo directorio: 4 archivos, 10 refs, 5 OK / 5 FAIL ---
DIR_OUT=$(run_ve --quiet "$FIXDIR" 2>&1)
DIR_RC=$?
DIR_HAS_4=$(printf '%s' "$DIR_OUT" | grep -cE "ERROR .*\.md:[0-9]+:" || true)
DIR_SUMMARY=$(printf '%s' "$DIR_OUT" | grep -oE "refs=[0-9]+ ok=[0-9]+ errors=[0-9]+" | head -1)
DIR_TOTAL=$(printf '%s' "$DIR_SUMMARY" | grep -oE "refs=[0-9]+" | cut -d= -f2)
DIR_OK=$(printf '%s' "$DIR_SUMMARY" | grep -oE "ok=[0-9]+" | cut -d= -f2)
DIR_FAIL=$(printf '%s' "$DIR_SUMMARY" | grep -oE "errors=[0-9]+" | cut -d= -f2)
if [[ $DIR_RC -eq 1 ]] \
   && [[ "${DIR_TOTAL:-0}" == "10" ]] \
   && [[ "${DIR_OK:-0}" == "5" ]] \
   && [[ "${DIR_FAIL:-0}" == "5" ]] \
   && [[ "$DIR_HAS_4" -ge 4 ]]; then
  check "modo directorio: 4 archivos, 10 refs (5 OK / 5 FAIL)" 0
else
  check "modo directorio: 4 archivos, 10 refs (5 OK / 5 FAIL)" 1 "rc=$DIR_RC; total=$DIR_TOTAL; ok=$DIR_OK; fail=$DIR_FAIL; distinct=$DIR_HAS_4"
fi

# --- summary ---
log "---"
log "resultado: $PASS/$checks checks OK ($FAIL fallidos)"
if [[ $FAIL -eq 0 ]]; then
  log "OK: A3.2 (validate_evidence.py funciona: extrae refs, valida fuente/ruta/línea/rango, reporta con código)"
  exit 0
else
  log "FAIL: A3.2 (revisar logs)"
  exit 1
fi
