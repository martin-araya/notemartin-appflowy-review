#!/usr/bin/env python3
"""count_matcher.py — cuenta y desglosa las filas del ledger que casan con
los prefijos dados, para dimensionar un corte antes de declararlo.

Uso:
  python3 count_matcher.py prefijo1 [prefijo2 ...]
  python3 count_matcher.py --split-2   # muestra el segundo nivel
"""
from __future__ import annotations

import csv
import sys
from collections import Counter
from pathlib import Path

LEDGER = Path(__file__).resolve().parents[4] / "OUT" / "_ledger" / "cobertura.csv"


def main() -> int:
    argv = sys.argv[1:]
    level = 6
    if argv and argv[0] == "--split-4":
        level = 5
        argv = argv[1:]
    elif argv and argv[0] == "--split-5":
        level = 6
        argv = argv[1:]
    rows = [r for r in csv.DictReader(LEDGER.open(encoding="utf-8")) if r["feature_ids"] == "F00"]
    if not argv:
        counts = Counter()
        for r in rows:
            counts[r["ruta"].split("/", 4)[4] if len(r["ruta"].split("/")) > 4 else "(root)"] += 1
        for k, v in counts.most_common(40):
            print(f"{v:5}  {k}")
        return 0
    matched = [r for r in rows if any(r["ruta"].startswith(p) for p in argv)]
    print(f"{len(matched)} filas casan con {argv}")
    counts: Counter[str] = Counter()
    for r in matched:
        parts = r["ruta"].split("/")
        counts["/".join(parts[:level])] += 1
    for k, v in counts.most_common(40):
        print(f"{v:5}  {k}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())