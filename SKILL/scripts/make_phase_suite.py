#!/usr/bin/env python3
"""make_phase_suite.py — Genera `validate-<PHASE>.sh` para una unidad de B3.

Plantilla de 5 checks: template, evidence (ok/total y >0), mermaid (FAIL=0 y
minimo de bloques), cobertura (prefijo de `verificado_por`) y veredicto del
revisor. El marcador de cobertura se compara por prefijo porque
`record_unit_state.py` anade " @ <timestamp>" al valor de `verificado_por`.

Uso:
  python3 make_phase_suite.py --phase B3.F07 --unit F07 --feature F07 \
      --doc OUT/09-features/F07-almacenamiento-de-archivos/F07-almacenamiento-de-archivos.md \
      --expected 58 --min-mermaid 4
"""
from __future__ import annotations

import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TESTS_ROOT = PROJECT_ROOT / "OUT" / "_ledger" / "pruebas"

# Cobertura: filas de {unit} verificadas por record_unit_state.py (prefijo, incluye " @ ts")
# Las unidades transversales B* no tocan cobertura.csv: sus archivos ya
# pertenecen a una feature F* y están verificados. Para ellas el quinto check
# comprueba que el frontmatter declara exactamente N rutas y que todas existen.
COV_LEDGER = """verificados=$(awk -F, 'BEGIN{n=0} {gsub(/\\r/,""); if(index($7,"autor_{unit}")==1) n++}} END{print n}' "$LEDGER")
[ "$verificados" = "$EXPECTED" ] \\
  || fail "cobertura: esperaba $EXPECTED archivos {unit} verificados, hay $verificados\""""

COV_FRONTMATTER = """verificados=$(python3 - "$DOC" "$EXPECTED" "$ROOT" <<'PYX'
import re, sys
from pathlib import Path
doc, expected, root = Path(sys.argv[1]), int(sys.argv[2]), Path(sys.argv[3])
front = doc.read_text().split("---")[1]
src = {"appflowy": root / "SRC/appflowy", "collab": root / "SRC/collab",
       "editor": root / "SRC/editor"}
rutas = []
for line in front.splitlines():
    s = line.strip()
    if not s.startswith("- ") or "/" not in s and ":" not in s:
        continue
    s = s[2:].strip()
    # Acepta 'appflowy/.../foo.dart' y 'collab:collab-database/src/database.rs'
    if s.startswith("collab:") or s.startswith("collab-database/"):
        if s.startswith("collab:"):
            s = s[len("collab:"):]
        if not s.startswith("collab/"):
            s = "collab/" + s
    elif s.startswith("editor:"):
        s = s[len("editor:"):]
        if not s.startswith("editor/"):
            s = "editor/" + s
    rutas.append(s)
assert len(rutas) == expected, f"frontmatter declara {len(rutas)} rutas, esperado {expected}"
faltan = []
for r in rutas:
    fuente = r.split("/")[0]
    p = src.get(fuente)
    if p is None or not (p / r.split("/", 1)[1]).exists():
        faltan.append(r)
assert not faltan, f"rutas inexistentes en SRC: {faltan[:3]}"
print(len(rutas))
PYX
) || fail "cobertura: el frontmatter no cuadra con EXPECTED o cita rutas inexistentes\""""

TEMPLATE = """#!/usr/bin/env bash
# validate-{phase}.sh — Prueba de la Fase {phase} ({title}).
# Verifica el documento {unit} y su cobertura.

set -u
set -o pipefail
fail() {{ echo "FAIL: $1" >&2; exit 1; }}

ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
DOC="$ROOT/{doc}"
LEDGER="$ROOT/OUT/_ledger/cobertura.csv"
VT="$ROOT/SKILL/scripts/validate_template.py"
VE="$ROOT/SKILL/scripts/validate_evidence.py"
VM="$ROOT/SKILL/scripts/validate_mermaid.sh"
EXPECTED={expected}

[ -f "$DOC" ]     || fail "no existe $DOC"
[ -f "$LEDGER" ]  || fail "no existe $LEDGER"

python3 "$VT" -t {template} "$DOC" --quiet >/dev/null 2>&1 \\
  || fail "template: {unit} no cumple la plantilla {template}"

ev_output=$(python3 "$VE" "$DOC" --quiet 2>&1)
refs=$(echo "$ev_output" | grep -oE 'refs=[0-9]+' | tail -1 | grep -oE '[0-9]+')
refs_ok=$(echo "$ev_output" | grep -oE 'ok=[0-9]+' | tail -1 | grep -oE '[0-9]+')
if [ "${{refs_ok:-0}}" != "${{refs:-0}}" ]; then
  fail "evidence: ${{refs_ok:-0}}/${{refs:-0}} OK"
fi
[ "${{refs:-0}}" -ge 1 ] || fail "evidence: el documento no cita ninguna ruta:línea"

m_output=$(bash "$VM" "$DOC" --quiet 2>&1)
ok_count=$(echo "$m_output" | grep -oE 'OK=[0-9]+' | tail -1 | grep -oE '[0-9]+')
fail_count=$(echo "$m_output" | grep -oE 'FAIL=[0-9]+' | tail -1 | grep -oE '[0-9]+')
[ "${{fail_count:-1}}" = "0" ] || fail "mermaid: ${{ok_count:-0}} OK / ${{fail_count:-?}} FAIL"
[ "${{ok_count:-0}}" -ge {min_mermaid} ] || fail "mermaid: se esperaban >= {min_mermaid} bloques, hay ${{ok_count:-0}}"

{coverage_check}

# Revisor con veredicto favorable
REV="$ROOT/OUT/_ledger/pruebas/{phase}/revisor_output.json"
[ -f "$REV" ] || fail "falta revisor_output.json"
veredicto=$(python3 -c "
import json
d=json.load(open('$REV'))
print(d.get('veredicto',''))
")
[ "$veredicto" = "aprobado" ] || fail "revisor: veredicto=$veredicto (esperado aprobado)"

echo "OK: {phase} (template=1/1, evidence=${{refs_ok}}/${{refs}}, mermaid=${{ok_count}} OK, cobertura=$verificados/$EXPECTED, revisor=aprobado)"
exit 0
"""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--phase", required=True)
    ap.add_argument("--unit", required=True)
    ap.add_argument("--feature", required=True)
    ap.add_argument("--doc", required=True)
    ap.add_argument("--expected", type=int, required=True)
    ap.add_argument("--min-mermaid", type=int, default=4)
    ap.add_argument("--title", default="")
    ap.add_argument("--template", default="feature",
                    help="feature | export | structure (auto por --transversal)")
    ap.add_argument("--transversal", action="store_true",
                    help="unidad B*: no toca cobertura.csv; el check de "
                         "cobertura valida el frontmatter contra SRC")
    args = ap.parse_args()

    if args.transversal and args.template == "feature":
        args.template = "export"
    cov = COV_FRONTMATTER if args.transversal else COV_LEDGER

    out_dir = TESTS_ROOT / args.phase
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"validate-{args.phase}.sh"
    path.write_text(
        TEMPLATE.format(
            phase=args.phase,
            unit=args.unit,
            feature=args.feature,
            doc=args.doc,
            expected=args.expected,
            min_mermaid=args.min_mermaid,
            template=args.template,
            coverage_check=cov,
            title=args.title or f"{args.feature} — unidad {args.unit}",
        ),
        encoding="utf-8",
    )
    path.chmod(0o755)
    print(f"OK {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())