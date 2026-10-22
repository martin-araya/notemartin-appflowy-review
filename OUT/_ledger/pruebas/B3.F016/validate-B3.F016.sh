#!/usr/bin/env bash
# validate-B3.F016.sh — Prueba de la Fase B3.F01.6 (Interacción).
# Verifica las 7 sub-unidades (F01.6.0..F01.6.6) y la cobertura de los
# 115 archivos asignados en OUT/_ledger/units/F01.6.{1..6}.json.

set -u
set -o pipefail
fail() { echo "FAIL: $1" >&2; exit 1; }

ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
DOCS_DIR="$ROOT/OUT/09-features/F01-documentos-y-editor"
LEDGER="$ROOT/OUT/_ledger/cobertura.csv"
VT="$ROOT/SKILL/scripts/validate_template.py"
VE="$ROOT/SKILL/scripts/validate_evidence.py"
VM="$ROOT/SKILL/scripts/validate_mermaid.sh"

# 7 sub-unidades (incluyendo F01.6.0 indice).
DOCS=(
  "6.0-indice-interaccion.md"
  "6.1-slash-menu-elementos.md"
  "6.2-block-menu-actions-context-menu.md"
  "6.3-drag-to-reorder.md"
  "6.4-toolbars-desktop-mobile-items-link.md"
  "6.5-copy-y-paste.md"
  "6.6-shortcuts-find-replace-keyboard.md"
)

[ -d "$DOCS_DIR" ] || fail "no existe $DOCS_DIR"
[ -f "$LEDGER" ]   || fail "no existe $LEDGER"
[ -f "$VT" ]       || fail "no existe validate_template.py"
[ -f "$VE" ]       || fail "no existe validate_evidence.py"
[ -f "$VM" ]       || fail "no existe validate_mermaid.sh"

TPL_OK=0; EVD_OK=0; MRD_OK=0

for doc in "${DOCS[@]}"; do
  path="$DOCS_DIR/$doc"
  [ -f "$path" ] || fail "falta doc: $doc"

  # Check 1: template
  if python3 "$VT" -t feature "$path" --quiet >/dev/null 2>&1; then
    TPL_OK=$((TPL_OK+1))
  else
    fail "template: $doc no cumple la plantilla feature"
  fi

  # Check 2: evidence
  ev_output=$(python3 "$VE" "$path" --quiet 2>&1)
  refs=$(echo "$ev_output" | grep -oE 'refs=[0-9]+' | tail -1 | grep -oE '[0-9]+')
  refs_ok=$(echo "$ev_output" | grep -oE 'ok=[0-9]+' | tail -1 | grep -oE '[0-9]+')
  if [ "${refs_ok:-0}" = "${refs:-0}" ]; then
    EVD_OK=$((EVD_OK+1))
  else
    echo "  evidence: $doc ${refs_ok:-0}/${refs:-0}" >&2
    fail "evidence: $doc ${refs_ok:-0}/${refs:-0} OK"
  fi

  # Check 3: mermaid
  m_output=$(bash "$VM" "$path" --quiet 2>&1)
  ok_count=$(echo "$m_output" | grep -oE 'OK=[0-9]+' | tail -1 | grep -oE '[0-9]+')
  fail_count=$(echo "$m_output" | grep -oE 'FAIL=[0-9]+' | tail -1 | grep -oE '[0-9]+')
  if [ "${fail_count:-0}" != "0" ] && [ -n "${fail_count}" ]; then
    fail "mermaid: $doc ${ok_count:-0} OK / ${fail_count} FAIL"
  fi
  # Success mergeo: count OK in this doc
  MRD_OK=$((MRD_OK+${ok_count:-0}))
done

# Check 4: cobertura (115 archivos F01.6 verificados en cobertura.csv)
verificados=$(awk -F, 'BEGIN{n=0} $4=="F01" && ($2 ~ /editor_plugins\/slash_menu\// || $2 ~ /editor_plugins\/block_menu\// || $2 ~ /editor_plugins\/context_menu\// || $2 ~ /editor_plugins\/actions\// || $2 ~ /editor_plugins\/desktop_toolbar\// || $2 ~ /editor_plugins\/mobile_toolbar_v3\// || $2 ~ /editor_plugins\/mobile_floating_toolbar\// || $2 ~ /editor_plugins\/toolbar_item\// || $2 ~ /editor_plugins\/shortcuts\// || $2 ~ /editor_plugins\/find_and_replace\// || $2 ~ /editor_plugins\/keyboard_interceptor\// || $2 ~ /editor_plugins\/copy_and_paste\// || $2 ~ /editor_plugins\/undo_redo_toolbar_item\.dart$/ || $2 ~ /editor_plugins\/exit_edit_mode_command\// || $2 ~ /editor_plugins\/align_toolbar_item\//) && $6=="verificado" {n++} END{print n}' "$LEDGER")
if [ "$verificados" = "115" ]; then
  :
else
  fail "cobertura: esperaba 115 archivos F01.6 verificados, hay $verificados"
fi

echo "OK: B3.F01.6 (template=$TPL_OK/7, evidence=$EVD_OK/7, mermaid=$MRD_OK bloques, cobertura=115/115, 7 sub-unidades)"
exit 0
