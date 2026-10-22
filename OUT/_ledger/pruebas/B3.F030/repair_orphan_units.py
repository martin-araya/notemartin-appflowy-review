#!/usr/bin/env python3
"""repair_orphan_units.py — Reparacion one-off del ledger de unidades (B3.F03..F07).

Contexto: `build_units.py` regenera `F02.0.1.json` / `F02.0.2.json` (padres) cada vez
que se ejecuta, y esos padres se solapan con las sub-unidades creadas a mano por
`split_F0201.py` / `split_F0202.py` / `split_F0209.py`. Al purgar los padres quedaron:

  (a) 425 rutas con doble propietario -> reducidas a 0 al borrar F02.0.1/F02.0.2.
  (b) 51 rutas Dart de `application/{cell,field,row,calculations}` en dos unidades
      (F02.0.1.2 y F02.{1,2,3,7,8,12}) -> el ROADMAP las atribuye a F02.0.1.2.
  (c) 114 filas asignadas a F02 sin ninguna unidad (raiz de flowy-database2,
      `src/entities/**` y `tests/**`) tras la purga.
  (d) 3 unidades indice sin `generado_en` (campo obligatorio de `check_schema`).

Este script deja el ledger en un estado consistente y verificable. Es idempotente.

Uso:  python3 OUT/_ledger/pruebas/B3.F030/repair_orphan_units.py [--dry-run]
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
UNITS_DIR = PROJECT_ROOT / "OUT" / "_ledger" / "units"
LEDGER = PROJECT_ROOT / "OUT" / "_ledger" / "cobertura.csv"

# (c) Reparto de las 114 filas huerfanas, segun la atribucion del ROADMAP.
ORPHAN_ROUTES = (
    "appflowy/frontend/rust-lib/flowy-database2/src/entities/",
    "appflowy/frontend/rust-lib/flowy-database2/tests/",
)

# (b) Las sub-unidades F02.x ceden a F02.0.1.2 las rutas Dart ya documentadas alli.
YIELDING_UNITS = ("F02.1", "F02.2", "F02.3", "F02.7", "F02.8", "F02.12")


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def dump(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def all_files() -> dict[str, dict]:
    out = {}
    for p in sorted(UNITS_DIR.glob("[!_]*.json")):
        d = load(p)
        if str(d.get("id", "")).startswith("B"):
            continue
        out[d["id"]] = d
    return out


def refresh(u: dict) -> None:
    """Recalcula archivos_total y metricas tras editar `archivos`."""
    u["archivos_total"] = len(u["archivos"])
    u["metricas"] = {
        "archivos": len(u["archivos"]),
        "por_capa": dict(Counter(a.get("capa", "?") for a in u["archivos"])),
        "por_fuente": dict(Counter(a.get("fuente", "?") for a in u["archivos"])),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    units = all_files()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    with LEDGER.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    capa = {(r["fuente"], r["ruta"]): r["capa"] for r in rows}

    owner: dict[tuple[str, str], set[str]] = {}
    for uid, u in units.items():
        for a in u["archivos"]:
            owner.setdefault((a["fuente"], a["ruta"]), set()).add(uid)

    # ---- (b) F02.{1,2,3,7,8,12} ceden las rutas ya propiedad de F02.0.1.2 ----
    idx = units["F02.0.1.2"]
    idx_files = {(a["fuente"], a["ruta"]) for a in idx["archivos"]}
    yielded = 0
    for uid in YIELDING_UNITS:
        u = units[uid]
        keep = [a for a in u["archivos"] if (a["fuente"], a["ruta"]) not in idx_files]
        yielded += len(u["archivos"]) - len(keep)
        u["archivos"] = keep
        refresh(u)

    # ---- (c) Reanclar las filas asignadas que no tienen unidad ----
    orphans = [
        r for r in rows
        if r["feature_ids"].strip()
        and (r["fuente"], r["ruta"]) not in owner
    ]
    routed: Counter = Counter()
    for r in orphans:
        ruta = r["ruta"]
        fid = r["feature_ids"].split(",")[0].strip()
        if fid == "F02" and ruta.startswith(ORPHAN_ROUTES[0]):
            target = "F02.0.1.1"          # ROADMAP: "+ 5 directorios Rust PB entities"
        elif fid == "F02" and ruta.startswith(ORPHAN_ROUTES[1]):
            target = "F02.0.1.3"          # ROADMAP: sub-unidad de tests de database
        elif fid == "F02":
            target = "F02.0.1.2"          # raiz del crate + services/utils
        else:
            # F08 (piloto A5.1): sus 21 archivos quedaron `verificado`, asi que
            # build_units.py dejo de emitirlos. Se recuperan para que la unidad
            # siga declarando su alcance real.
            target = fid
        u = units[target]
        u["archivos"].append(
            {"fuente": r["fuente"], "ruta": ruta, "capa": r["capa"], "estado": r["estado"]}
        )
        routed[target] += 1
        owner.setdefault((r["fuente"], ruta), set()).add(target)
    for uid in routed:
        refresh(units[uid])

    # ---- (d) `generado_en` obligatorio ----
    fixed_stamp = 0
    for u in units.values():
        if not u.get("generado_en"):
            u["generado_en"] = now
            fixed_stamp += 1

    # ---- verificacion ----
    owner = {}
    for uid, u in units.items():
        for a in u["archivos"]:
            owner.setdefault((a["fuente"], a["ruta"]), set()).add(uid)
    dups = {k: v for k, v in owner.items() if len(v) > 1}
    assigned = {(r["fuente"], r["ruta"]) for r in rows if r["feature_ids"].strip()}
    unowned = assigned - set(owner)

    print(f"cedidos por F02.x -> F02.0.1.2 : {yielded}")
    print(f"huerfanos reanclados            : {len(orphans)} {dict(routed)}")
    print(f"generado_en añadidos            : {fixed_stamp}")
    print(f"rutas con doble propietario     : {len(dups)}")
    print(f"asignadas sin unidad            : {len(unowned)}")
    print(f"unidades                       : {len(units)}")
    print(f"suma archivos_total             : {sum(u['archivos_total'] for u in units.values())}")

    if dups or unowned:
        for k, v in list(dups.items())[:5]:
            print(f"  DUP {k[1]} -> {sorted(v)}")
        for k in list(unowned)[:5]:
            print(f"  UNOWNED {k[1]}")
        return 1

    if args.dry_run:
        print("dry-run: no se ha escrito nada")
        return 0

    for uid, u in units.items():
        dump(UNITS_DIR / f"{uid}.json", u)
    print("OK: unidades reescritas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())