#!/usr/bin/env python3
"""restore_unit_files.py — reinyecta en una unidad las filas asignadas de su
feature que ya estan `verificado` y que `build_units.py` no vuelve a emitir.

Caso que动机: F08 se cerro a medias (piloto A5.1 verifico 21 de 32 archivos).
`build_units.py` solo lee filas pendientes, asi que al regenerar F08 su
unidad perdi those 21 y el invariante de `validate_units.py` (suma == filas
asignadas) se rompio en 21.

Uso:
  python3 restore_unit_files.py --unit F08
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LEDGER = PROJECT_ROOT / "OUT" / "_ledger" / "cobertura.csv"
UNITS = PROJECT_ROOT / "OUT" / "_ledger" / "units"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--unit", required=True, help="id de la unidad destino")
    args = ap.parse_args()

    path = UNITS / f"{args.unit}.json"
    unit = json.loads(path.read_text(encoding="utf-8"))
    feature_id = unit["feature_id"]
    have = {a["ruta"] for a in unit["archivos"]}

    added = []
    with LEDGER.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            if row["feature_ids"] != feature_id or row["ruta"] in have:
                continue
            # **Solo filas ya verificadas.** Reinyectar tambien las pendientes
            # seria un error: en una feature con varias unidades (F00 tiene
            # 20) cada unidad "recuperaria" las filas de sus hermanas.
            if row["estado"] != "verificado":
                continue
            added.append({
                "fuente": row["fuente"],
                "ruta": row["ruta"],
                "capa": row["capa"],
                "estado": row["estado"],
            })

    if not added:
        print(f"[restore_unit_files] {args.unit}: nada que reinyectar")
        return 0

    unit["archivos"].extend(added)
    unit["archivos"].sort(key=lambda a: a["ruta"])
    unit["archivos_total"] = len(unit["archivos"])
    metricas = unit.setdefault("metricas", {})
    metricas["archivos"] = len(unit["archivos"])
    capas: dict[str, int] = {}
    fuentes: dict[str, int] = {}
    for a in unit["archivos"]:
        capas[a["capa"]] = capas.get(a["capa"], 0) + 1
        fuentes[a["fuente"]] = fuentes.get(a["fuente"], 0) + 1
    metricas["por_capa"] = capas
    metricas["por_fuente"] = fuentes
    path.write_text(json.dumps(unit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[restore_unit_files] {args.unit}: +{len(added)} archivos -> "
          f"{unit['archivos_total']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())