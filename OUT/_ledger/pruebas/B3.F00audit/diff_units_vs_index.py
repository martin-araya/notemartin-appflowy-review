#!/usr/bin/env python3
"""diff_units_vs_index.py — ids presentes en disco y ausentes de _index.json."""
from __future__ import annotations
import json
from pathlib import Path

UNITS = Path(__file__).resolve().parents[4] / "OUT" / "_ledger" / "units"

disk = {}
for p in sorted(UNITS.glob("[!_]*.json")):
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"{p.name}: JSON INVALIDO -> {e}")
        continue
    disk[d.get("id", f"?{p.name}")] = p.name

index = {u["id"] for u in json.loads((UNITS / "_index.json").read_text(encoding="utf-8"))["units"]}

print("en disco y NO en el indice:", sorted(set(disk) - index))
print("en el indice y NO en disco:", sorted(index - set(disk)))
print("total disco:", len(disk), "total indice:", len(index))