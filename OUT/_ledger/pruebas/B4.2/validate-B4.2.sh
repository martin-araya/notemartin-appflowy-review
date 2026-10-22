#!/usr/bin/env bash
# validate-B4.2.sh — Prueba de la Fase B4.2 (B4.2 — unidad B4.2).
# Verifica el documento B4.2 y su cobertura.

set -u
set -o pipefail
fail() { echo "FAIL: $1" >&2; exit 1; }

ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
DOC="$ROOT/OUT/10-motor-export-import/02-html-export.md"
LEDGER="$ROOT/OUT/_ledger/cobertura.csv"
VT="$ROOT/SKILL/scripts/validate_template.py"
VE="$ROOT/SKILL/scripts/validate_evidence.py"
VM="$ROOT/SKILL/scripts/validate_mermaid.sh"
EXPECTED=18

[ -f "$DOC" ]     || fail "no existe $DOC"
[ -f "$LEDGER" ]  || fail "no existe $LEDGER"

python3 "$VT" -t export "$DOC" --quiet >/dev/null 2>&1 \
  || fail "template: B4.2 no cumple la plantilla export"

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

verificados=$(python3 - "$DOC" "$EXPECTED" "$ROOT" <<'PYX'
import sys
from pathlib import Path
doc, expected, root = Path(sys.argv[1]), int(sys.argv[2]), Path(sys.argv[3])
front = doc.read_text().split("---")[1]
rutas = [l.strip()[2:].strip() for l in front.splitlines()
         if l.strip().startswith("- ") and "/" in l]
assert len(rutas) == expected, f"frontmatter declara {len(rutas)} rutas, esperado {expected}"
src = {"appflowy": root / "SRC/appflowy", "collab": root / "SRC/collab",
       "editor": root / "SRC/editor"}
faltan = []
for r in rutas:
    fuente = r.split("/")[0]
    p = src.get(fuente)
    if p is None or not (p / r.split("/", 1)[1]).exists():
        faltan.append(r)
assert not faltan, f"rutas inexistentes en SRC: {faltan[:3]}"
print(len(rutas))
PYX
) || fail "cobertura: el frontmatter no cuadra con EXPECTED o cita rutas inexistentes"

# Revisor con veredicto favorable
REV="$ROOT/OUT/_ledger/pruebas/B4.2/revisor_output.json"
[ -f "$REV" ] || fail "falta revisor_output.json"
veredicto=$(python3 -c "
import json
d=json.load(open('$REV'))
print(d.get('veredicto',''))
")
[ "$veredicto" = "aprobado" ] || fail "revisor: veredicto=$veredicto (esperado aprobado)"

echo "OK: B4.2 (template=1/1, evidence=${refs_ok}/${refs}, mermaid=${ok_count} OK, cobertura=$verificados/$EXPECTED, revisor=aprobado)"
exit 0
