#!/usr/bin/env bash
# validate-B3.F02.3.sh — Prueba de la Fase B3.F02.3 (Filas y row detail (application/row), relaciones).
# Verifica el documento de feature F02.3 y la cobertura de los archivos asignados a autor_F02.3.

set -u
set -o pipefail
fail() { echo "FAIL: $1" >&2; exit 1; }

ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
DOC="$ROOT/OUT/09-features/F02-bases-de-datos/3-filas-y-row-detail-application-row-relaciones.md"
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
  fail "template: F02.3 no cumple la plantilla feature"
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

# Cobertura: archivos de F02.3 con verificado_por=autor_F02.3
verificados=$(awk -F, 'BEGIN{n=0} {gsub(/\r/,""); if($7=="autor_F02.3") n++} END{print n}' "$LEDGER")
if [ "$verificados" = "5" ]; then
  :
else
  fail "cobertura: esperaba 5 archivos F02.3 verificados, hay $verificados"
fi

echo "OK: B3.F02.3 (template=1/1, evidence=${refs_ok:-0}/${refs:-0}, mermaid=${ok_count:-0} OK, cobertura=5/5)"
exit 0