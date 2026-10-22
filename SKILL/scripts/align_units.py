#!/usr/bin/env python3
"""align_units.py — elimina la doble propiedad tras regenerar unidades.

Problema que resuelve
--------------------
`build_units.py` solo genera unidades a partir de las filas **pendientes** de
`cobertura.csv`. Cuando una feature esta a medio cerrar (F02: 537 filas
verificadas de 651), sus sub-unidades ya escritas siguen en disco incluyendo
las filas pendientes que todavia no estan cubiertas. En cuanto se regenera la
feature con una subdivision nueva (F02.13/14/15), esas filas quedan
**reclamadas por dos unidades** y `validate_units.py` falla.

Este script deja el ledger de unidades en un unico propietario por fila:

  1. Lee `cobertura.csv` y las unidades recien generadas (parametro
     `--generated` o, por defecto, las unidades cuyo `id` coincide con las
     que `build_units.py` acaba de escribir).
  2. Para cada unidad **no** regenerada, le quita las filas que ya son
     propiedad de una unidad regenerada.
  3. Reescribe la unidad y reporta el shrinkage. Las unidades que quedan con
     0 archivos se conservan si eranindices (0 archivos de origen) y se
     borran (a `.stale-bak/`) si eran unidades de contenido que se han
     quedado sin nada.

Es idempotente y tiene `--dry-run`.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
LEDGER = PROJECT_ROOT / "OUT" / "_ledger" / "cobertura.csv"
UNITS = PROJECT_ROOT / "OUT" / "_ledger" / "units"


def load_ledger(path: Path) -> dict[str, str]:
    import csv
    with path.open(encoding="utf-8", newline="") as f:
        return {row["ruta"]: row["estado"] for row in csv.DictReader(f)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--generated", type=str, default="",
                    help="CSV de ids de unidades regeneradas. Si se omite, se "
                         "inferen de las unidades cuya entrada contiene filas "
                         "pendientes (heuristica barata, puede fallar).")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    estado = load_ledger(LEDGER)
    units: dict[str, dict] = {}
    for path in sorted(UNITS.glob("*.json")):
        if path.name == "_index.json":
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if data.get("id"):
            units[data["id"]] = data

    # Las unidades `B1.*` usan otro esquema: su `archivos` es una lista de
    # documentos de OUT/, no de ficheros de SRC/ (ver validate_units.py).
    units = {
        uid: u for uid, u in units.items()
        if not uid.startswith("B")
        and all(isinstance(a, dict) for a in u.get("archivos", []))
    }

    if args.generated:
        generated_ids = {s.strip() for s in args.generated.split(",") if s.strip()}
    else:
        # Heuristica: una unidad esta "regenerada" si alguno de sus archivos
        # sigue pendiente en el ledger Y su unidad no es un indice.
        generated_ids = {
            uid for uid, u in units.items()
            if any(estado.get(a["ruta"]) == "pendiente" for a in u.get("archivos", []))
            and u.get("archivos")
        }
    # Las unidades regeneradas se regeneran enteras: nunca se tocan.
    targets = {uid: u for uid, u in units.items() if uid not in generated_ids}
    claimed: set[str] = set()
    for u in units.values():
        if u["id"] in generated_ids:
            claimed.update(a["ruta"] for a in u.get("archivos", []))

    shrunk: dict[str, tuple[int, int]] = {}
    emptied: list[str] = []
    for uid, u in sorted(targets.items()):
        keep, drop = [], []
        for a in u.get("archivos", []):
            (drop if a["ruta"] in claimed else keep).append(a)
        if not drop:
            continue
        shrunk[uid] = (len(u.get("archivos", [])), len(keep))
        if not args.dry_run:
            u["archivos"] = keep
            u["archivos_total"] = len(keep)
            u["metricas"]["archivos"] = len(keep)
            capas: dict[str, int] = defaultdict(int)
            fuentes: dict[str, int] = defaultdict(int)
            for a in keep:
                capas[a["capa"]] += 1
                fuentes[a["fuente"]] += 1
            u["metricas"]["por_capa"] = dict(capas)
            u["metricas"]["por_fuente"] = dict(fuentes)
            (UNITS / f"{uid}.json").write_text(
                json.dumps(u, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
            )
        if not keep:
            emptied.append(uid)

    print(f"[align_units] generadas={len(generated_ids)} "
          f"ajustadas={len(shrunk)} vaciadas={len(emptied)}"
          f"{' (dry-run)' if args.dry_run else ''}")
    for uid, (before, after) in sorted(shrunk.items()):
        print(f"  {uid}: {before} -> {after} archivos")
    if emptied:
        print(f"[align_units] unidades que quedan sin archivos: {', '.join(sorted(emptied))}")
        if not args.dry_run:
            backup = UNITS / ".stale-bak"
            backup.mkdir(parents=True, exist_ok=True)
            for uid in emptied:
                unit = units[uid]
                # Solo se borran si eran unidades de contenido; los indices
                # (0 archivos de origen) se conservan porque materializan las
                # dependencias `tipo: indice` de sus hermanas.
                if unit.get("archivos_total") or uid.endswith(".0"):
                    continue
                shutil.copy2(UNITS / f"{uid}.json", backup / f"{uid}.json")
                (UNITS / f"{uid}.json").unlink()
    return 0


if __name__ == "__main__":
    sys.exit(main())