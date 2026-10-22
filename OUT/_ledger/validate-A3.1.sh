#!/usr/bin/env bash
# validate-A3.1.sh — orquestador de la prueba del ROADMAP A3.1.
# Invoca SKILL/scripts/validate_mermaid.sh sobre los fixtures y verifica
# el comportamiento exacto exigido por la fase:
#   1) script ejecutable
#   2) --help imprime uso y sale 0
#   3) mmdc localizable
#   4) positive.md: exit 0
#   5) broken.md: exit 1 con "archivo:bloque_nº" en stderr
#   6) mixed.md: exit 1 y stderr contiene exactamente el nº del bloque roto
#   7) --quiet en positive.md: stdout resumen compacto
#   8) número de líneas "ERROR archivo:N:" en stderr = nº de bloques fallidos
#   9) modo directorio: 3 archivos, 4 OK / 2 FAIL

set -u
set -o pipefail

ROOT="/Users/martin/Desktop/projects/Skills/notemartin-appflowy-review"
SCRIPT="$ROOT/SKILL/scripts/validate_mermaid.sh"
FIXDIR="$ROOT/OUT/_ledger/pruebas/A3.1/fixtures"
LOG="$ROOT/OUT/_ledger/pruebas/A3.1/validate.log"

mkdir -p "$(dirname "$LOG")"
: > "$LOG"

log() { printf '[%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" | tee -a "$LOG"; }

# --- pre-check 3: mmdc ---
if ! command -v mmdc >/dev/null 2>&1; then
  log "SKIP: A3.1 (mmdc no encontrado. Instalar: npm i -g @mermaid-js/mermaid-cli)"
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
HELP_OUT=$(bash "$SCRIPT" --help 2>&1)
HELP_RC=$?
if [[ $HELP_RC -eq 0 ]] && printf '%s' "$HELP_OUT" | grep -q "Uso: validate_mermaid.sh"; then
  check "--help imprime uso y sale 0" 0
else
  check "--help imprime uso y sale 0" 1 "rc=$HELP_RC, sin 'Uso:'"
fi

# --- check 4: positive.md exit 0 ---
POS_OUT=$(bash "$SCRIPT" "$FIXDIR/positive.md" 2>&1)
POS_RC=$?
if [[ $POS_RC -eq 0 ]]; then
  check "positive.md exit 0" 0
else
  check "positive.md exit 0" 1 "rc=$POS_RC; output: $POS_OUT"
fi

# --- check 5: broken.md exit 1 + archivo:bloque_nº en stderr ---
BRK_OUT=$(bash "$SCRIPT" "$FIXDIR/broken.md" 2>&1)
BRK_RC=$?
BRK_STDERR_LINE=$(printf '%s' "$BRK_OUT" | grep -E "ERROR.*broken\.md:[0-9]+:" | head -1)
if [[ $BRK_RC -eq 1 ]] && [[ -n "$BRK_STDERR_LINE" ]]; then
  check "broken.md exit 1 con archivo:bloque_nº en stderr" 0
else
  check "broken.md exit 1 con archivo:bloque_nº en stderr" 1 "rc=$BRK_RC; stderr-line='$BRK_STDERR_LINE'"
fi

# --- check 6: mixed.md exit 1 + exactamente bloque 4 ---
MIX_OUT=$(bash "$SCRIPT" "$FIXDIR/mixed.md" 2>&1)
MIX_RC=$?
MIX_STDERR_LINES=$(printf '%s' "$MIX_OUT" | grep -cE "ERROR.*mixed\.md:[0-9]+:" || true)
MIX_HAS_BLOCK_4=$(printf '%s' "$MIX_OUT" | grep -cE "ERROR.*mixed\.md:4:" || true)
MIX_HAS_OTHER=$(printf '%s' "$MIX_OUT" | grep -cE "ERROR.*mixed\.md:[123]:" || true)
if [[ $MIX_RC -eq 1 ]] && [[ "$MIX_HAS_BLOCK_4" -ge 1 ]] && [[ "$MIX_HAS_OTHER" -eq 0 ]]; then
  check "mixed.md exit 1 identificando bloque 4 (no 1/2/3)" 0
else
  check "mixed.md exit 1 identificando bloque 4 (no 1/2/3)" 1 "rc=$MIX_RC; total_errores=$MIX_STDERR_LINES; con_bloque_4=$MIX_HAS_BLOCK_4; con_otros=$MIX_HAS_OTHER"
fi

# --- check 7: --quiet en positive.md (stdout compacto) ---
QPOS_OUT=$(bash "$SCRIPT" --quiet "$FIXDIR/positive.md" 2>/dev/null)
QPOS_RC=$?
QPOS_LINES=$(printf '%s\n' "$QPOS_OUT" | wc -l | tr -d ' ')
if [[ $QPOS_RC -eq 0 ]] && [[ "$QPOS_LINES" -le 4 ]] && printf '%s' "$QPOS_OUT" | grep -q "OK="; then
  check "--quiet en positive.md: exit 0, stdout ≤ 4 líneas con OK=" 0
else
  check "--quiet en positive.md: exit 0, stdout ≤ 4 líneas con OK=" 1 "rc=$QPOS_RC; lines=$QPOS_LINES; out=$QPOS_OUT"
fi

# --- check 8: número de líneas ERROR = número de bloques fallidos ---
# En mixed.md debe haber exactamente 1 línea ERROR.
if [[ "$MIX_STDERR_LINES" -eq 1 ]]; then
  check "nº de líneas ERROR = nº de bloques fallidos (mixed.md: 1)" 0
else
  check "nº de líneas ERROR = nº de bloques fallidos (mixed.md: 1)" 1 "esperado=1, got=$MIX_STDERR_LINES"
fi

# --- check 9: modo directorio ---
DIR_OUT=$(bash "$SCRIPT" "$FIXDIR" 2>&1)
DIR_RC=$?
DIR_HAS_BROKEN=$(printf '%s' "$DIR_OUT" | grep -cE "ERROR.*broken\.md:[0-9]+:" || true)
DIR_HAS_MIXED=$(printf '%s' "$DIR_OUT" | grep -cE "ERROR.*mixed\.md:[0-9]+:" || true)
DIR_HAS_POSITIVE=$(printf '%s' "$DIR_OUT" | grep -cE "positive\.md: [0-9]+ bloques.*OK" || true)
DIR_HAS_3_FILES=$(printf '%s' "$DIR_OUT" | grep -cE "\.md: [0-9]+ bloques" || true)
DIR_OK=$(printf '%s' "$DIR_OUT" | grep -oE "ok=[0-9]+" | head -1 | cut -d= -f2)
DIR_FAIL=$(printf '%s' "$DIR_OUT" | grep -oE "fail=[0-9]+" | head -1 | cut -d= -f2)
if [[ $DIR_RC -eq 1 ]] && [[ "$DIR_HAS_3_FILES" -eq 3 ]] \
   && [[ "$DIR_OK" == "4" ]] && [[ "$DIR_FAIL" == "2" ]] \
   && [[ "$DIR_HAS_BROKEN" -ge 1 ]] && [[ "$DIR_HAS_MIXED" -ge 1 ]] \
   && [[ "$DIR_HAS_POSITIVE" -ge 1 ]]; then
  check "modo directorio: 3 archivos, ok=4 fail=2" 0
else
  check "modo directorio: 3 archivos, ok=4 fail=2" 1 "rc=$DIR_RC; archivos=$DIR_HAS_3_FILES; ok=$DIR_OK; fail=$DIR_FAIL; broken=$DIR_HAS_BROKEN; mixed=$DIR_HAS_MIXED; positive=$DIR_HAS_POSITIVE"
fi

# --- summary ---
log "---"
log "resultado: $PASS/$checks checks OK ($FAIL fallidos)"
if [[ $FAIL -eq 0 ]]; then
  log "OK: A3.1 (validate_mermaid.sh funciona: extrae bloques mermaid, renderiza con mmdc, reporta archivo:bloque_nº en fallos)"
  exit 0
else
  log "FAIL: A3.1 (revisar logs)"
  exit 1
fi
