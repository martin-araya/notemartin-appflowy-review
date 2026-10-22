#!/usr/bin/env python3
"""record_unit_state.py — Marca el estado de unidades en
OUT/_ledger/cobertura.csv. Soporta tres acciones:

  --verificar UNIT_ID          → estado=verificado, verificado_por=<TEXT>
  --marcar_in_flight UNIT_ID   → anade marca 'in_flight: <ts>' en verificado_por
  --desmarcar_in_flight UNIT_ID → elimina la marca 'in_flight:' de verificado_por

Una unidad se identifica por su `id` (`Fxx` o `Fxx.y`). El script
afecta a todas las filas del cobertura.csv cuyo `feature_ids`
contenga ese id (multi-feature: marca global, no por feature).

Fase A4.4 de la skill notemartin-appflowy-review.
Ver AGENTS.md §8 y ROADMAP.md linea 103.

Uso:
  record_unit_state.py --unit UNIT_ID --accion {verificar|marcar_in_flight|desmarcar_in_flight}
                       [--verificado-por TEXT]
                       [--nota TEXT]
                       [--ledger PATH]
                       [--quiet] [--no-color] [--json]
                       [--help]
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve()
SKILL_ROOT = SCRIPT_PATH.parent.parent.parent
LEDGER_DEFAULT = SKILL_ROOT / "OUT" / "_ledger" / "cobertura.csv"

HEADER_LEDGER = (
    "fuente",
    "ruta",
    "capa",
    "feature_ids",
    "documento",
    "estado",
    "verificado_por",
)

IN_FLIGHT_PREFIX = "in_flight:"
IN_FLIGHT_RE = re.compile(r"\s*in_flight:\s*\S+(?:\s+\S+)*")

RED = "\033[31m"
GREEN = "\033[32m"
BOLD = "\033[1m"
RESET = "\033[0m"


def load_ledger(path: Path) -> tuple[list[dict], list[str]]:
    if not path.is_file():
        print(f"ERROR: no existe {path}", file=sys.stderr)
        sys.exit(2)
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames
        if header is None or tuple(header) != HEADER_LEDGER:
            print(
                f"ERROR: cabecera de {path} no coincide.\n"
                f"  esperado: {list(HEADER_LEDGER)}\n"
                f"  encontrado: {header}",
                file=sys.stderr,
            )
            sys.exit(2)
        rows = list(reader)
    return rows, list(reader.fieldnames or [])


def write_ledger(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        for r in rows:
            w.writerow(r)


UNITS_DEFAULT = SKILL_ROOT / "OUT" / "_ledger" / "units"


def unit_file_index(unit_id: str, units_dir: Path) -> set[tuple[str, str]] | None:
    """Devuelve {(fuente, ruta)} de la unidad, o None si no existe el unit.json.

    B3.F030: `cobertura.csv::feature_ids` solo guarda el id de FEATURE (`F03`),
    no el de la sub-unidad (`F03.2`), asi que un matcher por `feature_ids`
    afectaba 0 filas al cerrar sub-fases. Para los ids con punto se resuelve
    ahora el conjunto real de ficheros desde `OUT/_ledger/units/<id>.json`.
    """
    if "." not in unit_id:
        return None
    path = units_dir / f"{unit_id}.json"
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return {(a["fuente"], a["ruta"]) for a in data.get("archivos", []) if isinstance(a, dict)}


def unit_in_row(unit_id: str, row: dict, files: set[tuple[str, str]] | None = None) -> bool:
    fids = [f for f in row.get("feature_ids", "").split(";") if f]
    if unit_id in fids:
        return True
    if files is None:
        return False
    return (row.get("fuente", ""), row.get("ruta", "")) in files


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def action_verificar(rows: list[dict], unit_id: str, verificado_por: str, nota: str,
                     files: set | None = None) -> int:
    n = 0
    for r in rows:
        if unit_in_row(unit_id, r, files):
            r["estado"] = "verificado"
            extra = ""
            if nota:
                extra = f" | {nota}"
            stamp = f"{verificado_por}{extra} @ {_now()}" if verificado_por else _now()
            r["verificado_por"] = stamp
            n += 1
    return n


def action_marcar_in_flight(rows: list[dict], unit_id: str, files: set | None = None) -> int:
    n = 0
    for r in rows:
        if not unit_in_row(unit_id, r, files):
            continue
        existing = r.get("verificado_por", "")
        if IN_FLIGHT_PREFIX in existing:
            # Reemplazar la marca in_flight actual.
            existing = IN_FLIGHT_RE.sub("", existing).strip()
        marca = f"{IN_FLIGHT_PREFIX}{_now()}"
        r["verificado_por"] = (existing + " " + marca).strip() if existing else marca
        n += 1
    return n


def action_desmarcar_in_flight(rows: list[dict], unit_id: str, files: set | None = None) -> int:
    n = 0
    for r in rows:
        if not unit_in_row(unit_id, r, files):
            continue
        existing = r.get("verificado_por", "")
        if IN_FLIGHT_PREFIX in existing:
            r["verificado_por"] = IN_FLIGHT_RE.sub("", existing).strip()
            n += 1
    return n


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Marca el estado de unidades en OUT/_ledger/cobertura.csv "
            "(verificar / in_flight) para A4.4."
        )
    )
    p.add_argument("--unit", required=True, help="ID de la unidad (Fxx o Fxx.y).")
    p.add_argument("--accion", choices=["verificar", "marcar_in_flight", "desmarcar_in_flight"], required=True)
    p.add_argument("--verificado-por", type=str, default="",
                   help="Texto para la columna verificado_por (solo --verificar).")
    p.add_argument("--nota", type=str, default="",
                   help="Nota libre (solo --verificar).")
    p.add_argument("--ledger", type=Path, default=LEDGER_DEFAULT)
    p.add_argument("--units-dir", type=Path, default=UNITS_DEFAULT,
                   help="Carpeta de unit.json; permite resolver sub-unidades (F03.2).")
    p.add_argument("--quiet", action="store_true")
    p.add_argument("--no-color", action="store_true")
    p.add_argument("--json", action="store_true", dest="as_json")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    rows, fieldnames = load_ledger(args.ledger)
    files = unit_file_index(args.unit, args.units_dir)

    if args.accion == "verificar":
        n = action_verificar(rows, args.unit, args.verificado_por, args.nota, files)
    elif args.accion == "marcar_in_flight":
        n = action_marcar_in_flight(rows, args.unit, files)
    else:
        n = action_desmarcar_in_flight(rows, args.unit, files)

    if n > 0:
        write_ledger(args.ledger, rows, fieldnames)

    if args.as_json:
        print(json.dumps({
            "unit": args.unit,
            "accion": args.accion,
            "filas_afectadas": n,
            "resolucion": "unit.json" if files else "feature_ids",
        }, indent=2, ensure_ascii=False))
    elif not args.quiet:
        head = f"{BOLD}[record_unit_state]{RESET}" if not args.no_color else "[record_unit_state]"
        head = head.replace(RESET, "")
        color = GREEN if n > 0 else ""
        end = RESET if color and not args.no_color else ""
        print(f"{head} unit={args.unit} accion={args.accion} "
              f"filas_afectadas={color}{n}{end}",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
