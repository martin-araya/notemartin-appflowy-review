#!/usr/bin/env bash
# validate-B3.F18.sh — Prueba de la Fase B3.F18 (F18 — unidad F18).
# Verifica el documento de feature F18 y la cobertura de los 113 archivos de la unidad.

set -u
set -o pipefail
fail() { echo "FAIL: $1" >&2; exit 1; }

ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
DOC="$ROOT/OUT/09-features/F18-motor-colab-crdt-plugins-importer-entity-derive/F18-motor-colab-crdt-plugins-importer-entity-derive.md"
LEDGER="$ROOT/OUT/_ledger/cobertura.csv"
VT="$ROOT/SKILL/scripts/validate_template.py"
VE="$ROOT/SKILL/scripts/validate_evidence.py"
VM="$ROOT/SKILL/scripts/validate_mermaid.sh"
EXPECTED=113

[ -f "$DOC" ]     || fail "no existe $DOC"
[ -f "$LEDGER" ]  || fail "no existe $LEDGER"

python3 "$VT" -t feature "$DOC" --quiet >/dev/null 2>&1 \
  || fail "template: F18 no cumple la plantilla feature"

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
[ "${ok_count:-0}" -ge 6 ] || fail "mermaid: se esperaban >= 6 bloques, hay ${ok_count:-0}"

# Cobertura: filas de F18 verificadas por record_unit_state.py (prefijo, incluye " @ ts")
verificados=$(awk -F, 'BEGIN{n=0} {gsub(/\r/,""); if(index($7,"autor_F18")==1) n++} END{print n}' "$LEDGER")
[ "$verificados" = "$EXPECTED" ] \
  || fail "cobertura: esperaba $EXPECTED archivos F18 verificados, hay $verificados"

# Revisor con veredicto favorable
REV="$ROOT/OUT/_ledger/pruebas/B3.F18/revisor_output.json"
[ -f "$REV" ] || fail "falta revisor_output.json"
veredicto=$(python3 -c "
import json
d=json.load(open('$REV'))
print(d.get('veredicto',''))
")
[ "$veredicto" = "aprobado" ] || fail "revisor: veredicto=$veredicto (esperado aprobado)"

echo "OK: B3.F18 (template=1/1, evidence=${refs_ok}/${refs}, mermaid=${ok_count} OK, cobertura=$verificados/$EXPECTED, revisor=aprobado)"
exit 0
