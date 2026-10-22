#!/usr/bin/env bash
# validate-B3.F02.0.2.3.sh — Prueba de la Fase B3.F02.0.2.3 (collab-database tests (F02.0.2.3)).
# Verifica el documento de feature F02.0.2.3 y la cobertura (counting archivos in unit JSON that
# are at estado=verificado in cobertura.csv, regardless of attribution author — overlapping
# archivos in F02.6..F02.12 may carry a downstream autor_* attribution).

set -u
set -o pipefail
fail() { echo "FAIL: $1" >&2; exit 1; }

ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
DOC="$ROOT/OUT/09-features/F02-bases-de-datos/0.2.3-collab-database-tests.md"
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
  fail "template: F02.0.2.3 no cumple la plantilla feature"
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

# Cobertura: archivos listed in units/F02.0.2.3.json that are at estado=verificado in cobertura.csv
# (any autor_* attribution is acceptable — F02.0.X indices overlap with downstream F02.6..F02.12)
verificados=$(python3 -c "
import csv, json
from pathlib import Path
rutas = {a['ruta'] for a in json.load(open('/Users/martin/Desktop/projects/Skills/notemartin-appflowy-review/OUT/_ledger/units/F02.0.2.3.json'))['archivos']}
n = 0
with open('/Users/martin/Desktop/projects/Skills/notemartin-appflowy-review/OUT/_ledger/cobertura.csv') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['ruta'] in rutas and row['estado'] == 'verificado':
            n += 1
print(n)")
if [ "$verificados" = "39" ]; then
  :
else
  fail "cobertura: esperaba 39 archivos F02.0.2.3 verificados, hay $verificados"
fi

echo "OK: B3.F02.0.2.3 (template=1/1, evidence=${refs_ok:-0}/${refs:-0}, mermaid=${ok_count:-0} OK, cobertura=39/39)"
exit 0
