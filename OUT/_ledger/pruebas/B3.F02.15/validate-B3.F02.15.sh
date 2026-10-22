#!/usr/bin/env bash
# validate-B3.F02.15.sh — Prueba de la Fase B3.F02.15 (F02 — unidad F02.15).
# Verifica el documento de feature F02.15 y la cobertura de los 51 archivos de la unidad.

set -u
set -o pipefail
fail() { echo "FAIL: $1" >&2; exit 1; }

ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
DOC="$ROOT/OUT/09-features/F02-bases-de-datos/15-cierre-f02-bateria-de-tests-de-flowy-database2-tests-database.md"
LEDGER="$ROOT/OUT/_ledger/cobertura.csv"
VT="$ROOT/SKILL/scripts/validate_template.py"
VE="$ROOT/SKILL/scripts/validate_evidence.py"
VM="$ROOT/SKILL/scripts/validate_mermaid.sh"
EXPECTED=51

[ -f "$DOC" ]     || fail "no existe $DOC"
[ -f "$LEDGER" ]  || fail "no existe $LEDGER"

python3 "$VT" -t feature "$DOC" --quiet >/dev/null 2>&1 \
  || fail "template: F02.15 no cumple la plantilla feature"

ev_output=$(python3 "$VE" "$DOC" --quiet 2>&1)
refs=$(echo "$ev_output" | grep -oE 'refs=[0-9]+' | tail -1 | grep -oE '[0-9]+')
refs_ok=$(echo "$ev_output" | grep -oE 'ok=[0-9]+' | tail -1 | grep -oE '[0-9]+')
if [ "${refs_ok:-0}" != "${refs:-0}" ]; then
  fail "evidence: ${refs_ok:-0}/${refs:-0} OK"
fi
[ "${refs:-0}" -ge 1 ] || fail "evidence: el documento no cita ninguna ruta:línea"

m_output=$(bash "$VM" "$DOC" --quiet 2>&1)
ok_count=$(echo "$m_output" | grep -oE 'OK=[0-9]+' | tail -1 | grep -oE '[0-9]+')
fail_count=$(echo "$m_output" | grep -oE 'FAIL=[0-9]+' | tail -1 | grep -oE '[0-9]+')
[ "${fail_count:-1}" = "0" ] || fail "mermaid: ${ok_count:-0} OK / ${fail_count:-?} FAIL"
[ "${ok_count:-0}" -ge 4 ] || fail "mermaid: se esperaban >= 4 bloques, hay ${ok_count:-0}"

# Cobertura: filas de F02.15 verificadas por record_unit_state.py (prefijo, incluye " @ ts")
verificados=$(awk -F, 'BEGIN{n=0} {gsub(/\r/,""); if(index($7,"autor_F02.15")==1) n++} END{print n}' "$LEDGER")
[ "$verificados" = "$EXPECTED" ] \
  || fail "cobertura: esperaba $EXPECTED archivos F02.15 verificados, hay $verificados"

# Revisor con veredicto favorable
REV="$ROOT/OUT/_ledger/pruebas/B3.F02.15/revisor_output.json"
[ -f "$REV" ] || fail "falta revisor_output.json"
veredicto=$(python3 -c "
import json
d=json.load(open('$REV'))
print(d.get('veredicto',''))
")
[ "$veredicto" = "aprobado" ] || fail "revisor: veredicto=$veredicto (esperado aprobado)"

echo "OK: B3.F02.15 (template=1/1, evidence=${refs_ok}/${refs}, mermaid=${ok_count} OK, cobertura=$verificados/$EXPECTED, revisor=aprobado)"
exit 0
