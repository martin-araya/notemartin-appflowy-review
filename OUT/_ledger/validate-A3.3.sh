#!/usr/bin/env bash
# validate-A3.3.sh — orquestador de la prueba del ROADMAP A3.3.
# Invoca SKILL/scripts/validate_template.py sobre los fixtures y
# verifica el comportamiento exigido por la fase.

set -u
set -o pipefail

ROOT="/Users/martin/Desktop/projects/Skills/notemartin-appflowy-review"
SCRIPT="$ROOT/SKILL/scripts/validate_template.py"
FIXDIR="$ROOT/OUT/_ledger/pruebas/A3.3/fixtures"
LOG="$ROOT/OUT/_ledger/pruebas/A3.3/validate.log"

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

# Wrapper: --no-color para que el output sea parseable por grep.
run_vt() {
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
HELP_OUT=$(run_vt --help 2>&1)
HELP_RC=$?
if [[ $HELP_RC -eq 0 ]] && printf '%s' "$HELP_OUT" | grep -q "validate_template.py"; then
  check "--help imprime uso y sale 0" 0
else
  check "--help imprime uso y sale 0" 1 "rc=$HELP_RC"
fi

# --- check 3: valid_feature.md exit 0 con 0 errores ---
VF_OUT=$(run_vt "$FIXDIR/valid_feature.md" 2>&1)
VF_RC=$?
VF_ERR_COUNT=$(printf '%s' "$VF_OUT" | grep -c "^ERROR" || true)
if [[ $VF_RC -eq 0 ]] && [[ "$VF_ERR_COUNT" -eq 0 ]]; then
  check "valid_feature.md exit 0 con 0 errores" 0
else
  check "valid_feature.md exit 0 con 0 errores" 1 "rc=$VF_RC; errores=$VF_ERR_COUNT"
fi

# --- check 4: valid_export.md exit 0 con 0 errores ---
VE_OUT=$(run_vt "$FIXDIR/valid_export.md" 2>&1)
VE_RC=$?
VE_ERR_COUNT=$(printf '%s' "$VE_OUT" | grep -c "^ERROR" || true)
if [[ $VE_RC -eq 0 ]] && [[ "$VE_ERR_COUNT" -eq 0 ]]; then
  check "valid_export.md exit 0 con 0 errores" 0
else
  check "valid_export.md exit 0 con 0 errores" 1 "rc=$VE_RC; errores=$VE_ERR_COUNT"
fi

# --- check 5: missing_section_13.md exit 1 con E_MISSING_SECTION: [13] ---
MS_OUT=$(run_vt "$FIXDIR/missing_section_13.md" 2>&1)
MS_RC=$?
MS_HAS_CODE=$(printf '%s' "$MS_OUT" | grep -c "E_MISSING_SECTION" || true)
MS_HAS_13=$(printf '%s' "$MS_OUT" | grep -cE "faltan secciones: \[13\]" || true)
if [[ $MS_RC -eq 1 ]] && [[ "$MS_HAS_CODE" -ge 1 ]] && [[ "$MS_HAS_13" -ge 1 ]]; then
  check "missing_section_13.md exit 1 con E_MISSING_SECTION: [13]" 0
else
  check "missing_section_13.md exit 1 con E_MISSING_SECTION: [13]" 1 "rc=$MS_RC; code=$MS_HAS_CODE; has_13=$MS_HAS_13"
fi

# --- check 6: missing_frontmatter.md exit 1 con E_NO_FRONTMATTER ---
MF_OUT=$(run_vt "$FIXDIR/missing_frontmatter.md" 2>&1)
MF_RC=$?
MF_HAS_CODE=$(printf '%s' "$MF_OUT" | grep -c "E_NO_FRONTMATTER" || true)
if [[ $MF_RC -eq 1 ]] && [[ "$MF_HAS_CODE" -ge 1 ]]; then
  check "missing_frontmatter.md exit 1 con E_NO_FRONTMATTER" 0
else
  check "missing_frontmatter.md exit 1 con E_NO_FRONTMATTER" 1 "rc=$MF_RC; code=$MF_HAS_CODE"
fi

# --- check 7: bad_estado.md exit 1 con E_BAD_ESTADO ---
BE_OUT=$(run_vt "$FIXDIR/bad_estado.md" 2>&1)
BE_RC=$?
BE_HAS_CODE=$(printf '%s' "$BE_OUT" | grep -c "E_BAD_ESTADO" || true)
if [[ $BE_RC -eq 1 ]] && [[ "$BE_HAS_CODE" -ge 1 ]]; then
  check "bad_estado.md exit 1 con E_BAD_ESTADO" 0
else
  check "bad_estado.md exit 1 con E_BAD_ESTADO" 1 "rc=$BE_RC; code=$BE_HAS_CODE"
fi

# --- check 8: out_of_order.md exit 1 con E_OUT_OF_ORDER ---
OO_OUT=$(run_vt "$FIXDIR/out_of_order.md" 2>&1)
OO_RC=$?
OO_HAS_CODE=$(printf '%s' "$OO_OUT" | grep -c "E_OUT_OF_ORDER" || true)
if [[ $OO_RC -eq 1 ]] && [[ "$OO_HAS_CODE" -ge 1 ]]; then
  check "out_of_order.md exit 1 con E_OUT_OF_ORDER" 0
else
  check "out_of_order.md exit 1 con E_OUT_OF_ORDER" 1 "rc=$OO_RC; code=$OO_HAS_CODE"
fi

# --- check 9: --json produce JSON parseable ---
JSON_OUT=$(run_vt --json "$FIXDIR/valid_feature.md" 2>/dev/null)
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

# --- check 10: modo directorio: 6 archivos, 2 OK / 4 errores ---
DIR_OUT=$(run_vt --quiet "$FIXDIR" 2>&1)
DIR_RC=$?
DIR_SUMMARY=$(printf '%s' "$DIR_OUT" | grep -oE "files=[0-9]+ ok=[0-9]+ errors=[0-9]+" | head -1)
DIR_FILES=$(printf '%s' "$DIR_SUMMARY" | grep -oE "files=[0-9]+" | cut -d= -f2)
DIR_OK=$(printf '%s' "$DIR_SUMMARY" | grep -oE "ok=[0-9]+" | cut -d= -f2)
DIR_ERR=$(printf '%s' "$DIR_SUMMARY" | grep -oE "errors=[0-9]+" | cut -d= -f2)
if [[ $DIR_RC -eq 1 ]] \
   && [[ "${DIR_FILES:-0}" == "6" ]] \
   && [[ "${DIR_OK:-0}" == "2" ]] \
   && [[ "${DIR_ERR:-0}" == "4" ]]; then
  check "modo directorio: 6 archivos, 2 OK / 4 errores" 0
else
  check "modo directorio: 6 archivos, 2 OK / 4 errores" 1 "rc=$DIR_RC; files=$DIR_FILES; ok=$DIR_OK; errors=$DIR_ERR"
fi

# --- summary ---
log "---"
log "resultado: $PASS/$checks checks OK ($FAIL fallidos)"
if [[ $FAIL -eq 0 ]]; then
  log "OK: A3.3 (validate_template.py funciona: valida frontmatter 5 campos + secciones en orden, 10+ códigos de error)"
  exit 0
else
  log "FAIL: A3.3 (revisar logs)"
  exit 1
fi
