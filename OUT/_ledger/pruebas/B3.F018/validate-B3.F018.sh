#!/usr/bin/env bash
# validate-B3.F018.sh — Prueba de la Fase B3.F01.8 (Infraestructura del editor).
# Verifica el documento de feature F01.8 y la cobertura de los
# 19 archivos físicos (ledger declara 20) en OUT/_ledger/units/F01.8.json.

set -u
set -o pipefail
fail() { echo "FAIL: $1" >&2; exit 1; }

ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
DOC="$ROOT/OUT/09-features/F01-documentos-y-editor/8-infraestructura-del-editor-transaction-handler-block-transaction-handler-migrati.md"
LEDGER="$ROOT/OUT/_ledger/cobertura.csv"
VT="$ROOT/SKILL/scripts/validate_template.py"
VE="$ROOT/SKILL/scripts/validate_evidence.py"
VM="$ROOT/SKILL/scripts/validate_mermaid.sh"

[ -f "$DOC" ]    || fail "no existe $DOC"
[ -f "$LEDGER" ] || fail "no existe $LEDGER"
[ -f "$VT" ]     || fail "no existe validate_template.py"
[ -f "$VE" ]     || fail "no existe validate_evidence.py"
[ -f "$VM" ]     || fail "no existe validate_mermaid.sh"

if ! python3 "$VT" -t feature "$DOC" --quiet >/dev/null 2>&1; then
  fail "template: F01.8 no cumple la plantilla feature"
fi

ev_output=$(python3 "$VE" "$DOC" --quiet 2>&1)
refs=$(echo "$ev_output" | grep -oE 'refs=[0-9]+' | tail -1 | grep -oE '[0-9]+')
refs_ok=$(echo "$ev_output" | grep -oE 'ok=[0-9]+' | tail -1 | grep -oE '[0-9]+')
if [ "${refs_ok:-0}" != "${refs:-0}" ]; then
  fail "evidence: ${refs_ok:-0}/${refs:-0} OK"
fi

m_output=$(bash "$VM" "$DOC" --quiet 2>&1)
ok_count=$(echo "$m_output" | grep -oE 'OK=[0-9]+' | tail -1 | grep -oE '[0-9]+')
fail_count=$(echo "$m_output" | grep -oE 'FAIL=[0-9]+' | tail -1 | grep -oE '[0-9]+')
if [ "${fail_count:-0}" != "0" ] && [ -n "${fail_count}" ]; then
  fail "mermaid: ${ok_count:-0} OK / ${fail_count} FAIL"
fi

# Cobertura: 20 archivos en editor_plugins/{block_transaction_handler|transaction_handler|migration|parsers}/
verificados=$(awk -F, 'BEGIN{n=0} $4=="F01" && ($2 ~ /editor_plugins\/block_transaction_handler\// || $2 ~ /editor_plugins\/transaction_handler\// || $2 ~ /editor_plugins\/migration\// || $2 ~ /editor_plugins\/parsers\//) && $6=="verificado" {n++} END{print n}' "$LEDGER")
if [ "$verificados" = "20" ]; then
  :
else
  fail "cobertura: esperaba 20 archivos F01.8 verificados, hay $verificados"
fi

echo "OK: B3.F01.8 (template=1/1, evidence=${refs_ok:-0}/${refs:-0}, mermaid=${ok_count:-0} OK, cobertura=20/20)"
exit 0
