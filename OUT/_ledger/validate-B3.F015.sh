#!/usr/bin/env bash
# validate-B3.F015.sh — Prueba de la Fase B3.F01.5.
# Verifica el documento de feature F01.5 (Bases embebidas en documentos)
# y la cobertura de los 3 archivos asignados en OUT/_ledger/units/F01.5.json.

set -u
set -o pipefail
fail() { echo "FAIL: $1" >&2; exit 1; }

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DOC="$ROOT/OUT/09-features/F01-documentos-y-editor/5-bases-de-datos-embebidas-en-documentos.md"
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
  fail "template: F01.5 no cumple la plantilla feature"
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

verificados=$(awk -F, 'BEGIN{n=0} $4=="F01" && $2 ~ /editor_plugins\/database\// && $6=="verificado" {n++} END{print n}' "$LEDGER")
if [ "$verificados" = "3" ]; then
  :
else
  fail "cobertura: esperaba 3 archivos F01.5 verificados, hay $verificados"
fi

echo "OK: B3.F01.5 (template=1/1, evidence=${refs_ok:-0}/${refs:-0}, mermaid=${ok_count:-0} OK, cobertura=3/3)"
exit 0
