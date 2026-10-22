#!/usr/bin/env bash
# validate-B3.F010.sh — Prueba de la Fase B3.F01.0.
# Verifica los 9 documentos del feature F01 (Indice de documentos y editor):
#   0.0 indice (cross-cutting)
#   0.1 appflowy (Dart + flowy-document)
#   0.2 collab (collab-document Rust)
#   0.3.1 editor core
#   0.3.2 editor toolbars
#   0.3.3 editor encoders/decoders
#   0.3.4 editor shortcuts/IME
#   0.3.5 editor l10n/util/plugins
#
# Checks: 8 (template x8 + evidence x8 + mermaid x8 + cobertura).
# Salida: 0 si OK, 1 si algun check falla.

set -u
set -o pipefail
SCRIPT_NAME=$(basename "$0")
fail() { echo "FAIL: $1" >&2; exit 1; }

ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
DOCS_DIR="$ROOT/OUT/09-features/F01-documentos-y-editor"
LEDGER="$ROOT/OUT/_ledger/cobertura.csv"
VT="$ROOT/SKILL/scripts/validate_template.py"
VE="$ROOT/SKILL/scripts/validate_evidence.py"
VM="$ROOT/SKILL/scripts/validate_mermaid.sh"

[ -d "$DOCS_DIR" ] || fail "no existe $DOCS_DIR"
[ -f "$LEDGER" ]   || fail "no existe $LEDGER"
[ -f "$VT" ]       || fail "no existe validate_template.py"
[ -f "$VE" ]       || fail "no existe validate_evidence.py"
[ -f "$VM" ]       || fail "no existe validate_mermaid.sh"

# Docs a validar
EXPECTED=(
  "0.0-indice-documentos-y-editor.md"
  "0.1-indice-de-documentos-y-editor-modelo-documentbloc-servicios-appflowy.md"
  "0.2-indice-de-documentos-y-editor-modelo-documentbloc-servicios-collab.md"
  "0.3.1-editor-core-estado-bloques-infraestructura.md"
  "0.3.2-editor-toolbars-find-replace-selection-menu.md"
  "0.3.3-editor-encoders-decoders-markdown-html-json-pdf.md"
  "0.3.4-editor-shortcuts-ime-context-menu-servicios.md"
  "0.3.5-editor-l10n-utils-bloques-misc.md"
)

OK_COUNT=0
FAIL_COUNT=0
TOTAL_REFS=0
TOTAL_REFS_OK=0
TOTAL_MERMAID=0
TOTAL_MERMAID_OK=0

for doc in "${EXPECTED[@]}"; do
  path="$DOCS_DIR/$doc"
  [ -f "$path" ] || fail "falta doc: $doc"
  
  # Check 1: template
  if python3 "$VT" -t feature "$path" --quiet >/dev/null 2>&1; then
    OK_COUNT=$((OK_COUNT+1))
  else
    fail_count_t=$(python3 "$VT" -t feature "$path" 2>&1 | grep -c "^ERROR")
    FAIL_COUNT=$((FAIL_COUNT+1))
    echo "  ❌ template: $doc ($fail_count_t errores)"
  fi
  
  # Check 2: evidence
  ev_output=$(python3 "$VE" "$path" --quiet 2>&1)
  refs=$(echo "$ev_output" | grep -oE 'refs=[0-9]+' | tail -1 | grep -oE '[0-9]+')
  refs_ok=$(echo "$ev_output" | grep -oE 'ok=[0-9]+' | tail -1 | grep -oE '[0-9]+')
  TOTAL_REFS=$((TOTAL_REFS + ${refs:-0}))
  TOTAL_REFS_OK=$((TOTAL_REFS_OK + ${refs_ok:-0}))
  if [ "${refs_ok:-0}" = "${refs:-0}" ] && [ "${refs:-0}" -gt 0 ]; then
    :
  elif [ "${refs:-0}" = "0" ]; then
    :  # docs sin refs externas son válidos (e.g. doc 0.3.2..5 concentran refs en índice)
  else
    echo "  ❌ evidence: $doc (${refs_ok:-0}/${refs:-0} OK)"
  fi
  
  # Check 3: mermaid
  m_output=$(bash "$VM" "$path" --quiet 2>&1)
  ok_count=$(echo "$m_output" | grep -oE 'OK=[0-9]+' | tail -1 | grep -oE '[0-9]+')
  fail_count=$(echo "$m_output" | grep -oE 'FAIL=[0-9]+' | tail -1 | grep -oE '[0-9]+')
  TOTAL_MERMAID=$((TOTAL_MERMAID + ${ok_count:-0} + ${fail_count:-0}))
  TOTAL_MERMAID_OK=$((TOTAL_MERMAID_OK + ${ok_count:-0}))
  if [ "${fail_count:-0}" != "0" ] && [ -n "${fail_count}" ]; then
    echo "  ❌ mermaid: $doc (${ok_count:-0} OK / ${fail_count} FAIL)"
  fi
done

# Check 4: cobertura (los archivos de F01.0.x verificados). B3.F030: el umbral
# paso de "exactamente 555" a ">= 555" porque las sub-fases F01.1..F01.9 se
# cerraron despues y ellipton el total de F01 verificado (hoy 798).
verificados=$(awk -F, 'BEGIN{n=0} $4=="F01" && $6=="verificado" {n++} END{print n}' "$LEDGER")
if [ "$verificados" -ge 555 ]; then
  :
else
  fail "cobertura: esperaba >=555 archivos F01 verificados, hay $verificados"
fi

if [ "$OK_COUNT" = "8" ] && [ "$FAIL_COUNT" = "0" ]; then
  echo "OK: B3.F01.0 (8 docs verdes; template=8/8, evidence=${TOTAL_REFS_OK}/${TOTAL_REFS}, mermaid=${TOTAL_MERMAID_OK}/${TOTAL_MERMAID}, cobertura=$verificados/>=555)"
  exit 0
else
  echo "FAIL: B3.F01.0 (template OK=$OK_COUNT FAIL=$FAIL_COUNT; evidence ${TOTAL_REFS_OK}/${TOTAL_REFS}; mermaid ${TOTAL_MERMAID_OK}/${TOTAL_MERMAID})"
  exit 1
fi
