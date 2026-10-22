#!/usr/bin/env python3
"""coverage_report.py — estado de cobertura por feature y por unidad.

Una sola lectura del ledger; sirve para el cierre de fase (ROADMAP, STATE) y
para saber exactamente qué queda pendiente.

Uso:
  python3 coverage_report.py [--pendiente] [--csv OUT.csv]
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LEDGER = PROJECT_ROOT / "OUT" / "_ledger" / "cobertura.csv"
UNITS = PROJECT_ROOT / "OUT" / "_ledger" / "units"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--pendiente", action="store_true",
                    help="solo features y unidades con filas pendientes")
    ap.add_argument("--csv", type=Path)
    args = ap.parse_args()

    rows = list(csv.DictReader(LEDGER.open(encoding="utf-8", newline="")))
    feat: dict[str, Counter] = defaultdict(Counter)
    # Estado real por ruta. El `estado` guardado dentro de cada unidad es una
    # foto del momento en que se genero el JSON: `record_unit_state.py`
    # actualiza cobertura.csv, no las unidades. El ledger manda.
    por_ruta: dict[str, str] = {}
    for r in rows:
        feat[r["feature_ids"]][r["estado"]] += 1
        por_ruta[r["ruta"]] = r["estado"]

    units = []
    for p in sorted(UNITS.glob("[!_]*.json")):
        if p.name == "_index.json":
            continue
        try:
            u = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if not u.get("id") or u["id"].startswith("B"):
            continue
        pend = sum(1 for a in u.get("archivos", [])
                   if por_ruta.get(a["ruta"], a.get("estado")) == "pendiente")
        units.append((u["id"], u["archivos_total"], pend, u["documento"]))

    print("| Feature | Asignados | Verificados | Pendientes | % | Estado |")
    print("|---|---:|---:|---:|---:|---|")
    total_v = total_p = 0
    for f in sorted(feat, key=lambda x: (len(x), x)):
        c = feat[f]
        v, p = c["verificado"], c["pendiente"]
        total_v += v
        total_p += p
        pct = 100 * v / max(v + p, 1)
        estado = "completa" if not p else f"faltan {p}"
        print(f"| {f} | {v + p} | {v} | {p} | {pct:.1f}% | {estado} |")
    print(f"| **TOTAL** | **{len(rows)}** | **{total_v}** | **{total_p}** | "
          f"**{100 * total_v / len(rows):.1f}%** | |")

    pend_units = [u for u in units if u[2]]
    if pend_units:
        print(f"\n### {len(pend_units)} unidades con filas pendientes")
        print("| Unidad | Archivos | Pendientes | Documento |")
        print("|---|---:|---:|---|")
        for uid, tot, p, doc in pend_units:
            print(f"| `{uid}` | {tot} | {p} | `{doc}` |")

    if args.csv:
        with args.csv.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["feature", "asignados", "verificados", "pendientes"])
            for f_ in sorted(feat, key=lambda x: (len(x), x)):
                c = feat[f_]
                w.writerow([f_, c["verificado"] + c["pendiente"], c["verificado"], c["pendiente"]])
        print(f"\nescrito {args.csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())