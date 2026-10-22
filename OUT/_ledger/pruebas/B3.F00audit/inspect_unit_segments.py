#!/usr/bin/env python3
"""inspect_unit_segments.py — volca la distribucion por primer segmento de
ruta de una unidad, para decidir cortes de split sin adivinar."""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

UNITS = Path(__file__).resolve().parents[4] / "OUT" / "_ledger" / "units"


def main() -> int:
    for unit_id in sys.argv[1:]:
        unit = json.loads((UNITS / f"{unit_id}.json").read_text(encoding="utf-8"))
        files = [a["ruta"] for a in unit["archivos"]]
        common = files[0]
        for f in files[1:]:
            while not f.startswith(common) and common:
                common = common[:-1]
        counts: Counter[str] = Counter()
        for f in files:
            rest = f[len(common):].lstrip("/")
            counts[rest.split("/", 1)[0] if rest else "(root)"] += 1
        print(f"\n== {unit_id}  total={len(files)}  common={common}")
        for seg, n in counts.most_common():
            print(f"   {n:5}  {seg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())