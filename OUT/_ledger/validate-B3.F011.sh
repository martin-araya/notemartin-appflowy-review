#!/usr/bin/env bash
# validate-B3.F011.sh — Prueba de la Fase B3.F01.1.
# Verifica el documento de feature F01.1 (Bloques de texto) y la cobertura
# de los 19 archivos asignados en OUT/_ledger/units/F01.1.json.
#
# Checks: 4 (template + evidence + mermaid + cobertura).
# Salida: 0 si OK, 1 si algun check falla.

set -u
set -o pipefail
fail() { echo "FAIL: $1" >&2; exit 1; }

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DOC="$ROOT/OUT/09-features/F01-documentos-y-editor/1-bloques-de-texto-heading-bulleted-numbered-list-todo-list-quote-toggle-callout-h.md"
LEDGER="$ROOT/OUT/_ledger/cobertura.csv"
VT="$ROOT/SKILL/scripts/validate_template.py"
VE="$ROOT/SKILL/scripts/validate_evidence.py"
VM="$ROOT/SKILL/scripts/validate_mermaid.sh"

[ -f "$DOC" ]    || fail "no existe $DOC"
[ -f "$LEDGER" ] || fail "no existe $LEDGER"
[ -f "$VT" ]     || fail "no existe validate_template.py"
[ -f "$VE" ]     || fail "no existe validate_evidence.py"
[ -f "$VM" ]     || fail "no existe validate_mermaid.sh"

# Check 1: template (19 secciones)
if ! python3 "$VT" -t feature "$DOC" --quiet >/dev/null 2>&1; then
  echo "  ❌ template: $DOC"
  fail "template: F01.1 no cumple la plantilla feature"
fi

# Check 2: evidence
ev_output=$(python3 "$VE" "$DOC" --quiet 2>&1)
refs=$(echo "$ev_output" | grep -oE 'refs=[0-9]+' | tail -1 | grep -oE '[0-9]+')
refs_ok=$(echo "$ev_output" | grep -oE 'ok=[0-9]+' | tail -1 | grep -oE '[0-9]+')
if [ "${refs_ok:-0}" != "${refs:-0}" ]; then
  fail "evidence: ${refs_ok:-0}/${refs:-0} OK"
fi

# Check 3: mermaid
m_output=$(bash "$VM" "$DOC" --quiet 2>&1)
ok_count=$(echo "$m_output" | grep -oE 'OK=[0-9]+' | tail -1 | grep -oE '[0-9]+')
fail_count=$(echo "$m_output" | grep -oE 'FAIL=[0-9]+' | tail -1 | grep -oE '[0-9]+')
if [ "${fail_count:-0}" != "0" ] && [ -n "${fail_count}" ]; then
  echo "  ❌ mermaid: ${ok_count:-0} OK / ${fail_count} FAIL"
  fail "mermaid: bloques Mermaid invalidos"
fi

# Check 4: cobertura (19 archivos F01.1 verificados)
verificados=$(awk -F, 'BEGIN{n=0} $4=="F01" && $2 ~ /editor_plugins\/(bulleted_list|callout|delta|heading|header|numbered_list|quote|todo_list|toggle)\// && $6=="verificado" {n++} END{print n}' "$LEDGER")
if [ "$verificados" = "19" ]; then
  :
else
  fail "cobertura: esperaba 19 archivos F01.1 verificados, hay $verificados"
fi

echo "OK: B3.F01.1 (template=1/1, evidence=${refs_ok:-0}/${refs:-0}, mermaid=${ok_count:-0} OK, cobertura=19/19)"
exit 0
