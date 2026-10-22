#!/usr/bin/env python3
"""validate_units.py — Verifica el esquema y la coherencia de
OUT/_ledger/units/<id>.json emitidos por build_units.py (A4.2).

Comprobaciones:
  1. Cada <id>.json existe y parsea como JSON.
  2. Cabecera con los campos obligatorios del esquema v1.
  3. archivos_total == len(archivos).
  4. Sin (fuente, ruta) duplicados entre unidades (sin solapamiento).
  5. La suma de archivos_total de todas las unidades = total de filas
     con feature_ids != "" en el cobertura.csv de referencia.
  6. (Opcional) Cada ruta existe en el inventario.

Uso:
  validate_units.py [--units-dir PATH] [--ledger PATH]
                    [--inventario PATH] [--index PATH]
                    [--quiet] [--no-color] [--json]
                    [--help]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = SKILL_DIR.parent
UNITS_DEFAULT = PROJECT_ROOT / "OUT" / "_ledger" / "units"
LEDGER_DEFAULT = PROJECT_ROOT / "OUT" / "_ledger" / "cobertura.csv"
INVENTARIO_DEFAULT = PROJECT_ROOT / "OUT" / "_ledger" / "inventario.json"
INDEX_DEFAULT = UNITS_DEFAULT / "_index.json"

REQUIRED_FIELDS = (
    "schema_version",
    "id",
    "feature_id",
    "sub_index",
    "titulo",
    "fuentes",
    "archivos",
    "archivos_total",
    "catalogos",
    "dependencias",
    "plantilla",
    "documento",
    "metricas",
    "prioridad",
    "concurrencia",
    "generado_en",
)

RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BOLD = "\033[1m"
RESET = "\033[0m"


def load_unit(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def check_schema(unit: dict, errors: list[str]) -> None:
    for f in REQUIRED_FIELDS:
        if f not in unit:
            errors.append(f"[{unit.get('id', '?')}] falta campo obligatorio: {f}")
    if unit.get("schema_version") != 1:
        errors.append(f"[{unit.get('id', '?')}] schema_version != 1")
    if unit.get("plantilla") not in ("feature", "export"):
        errors.append(f"[{unit.get('id', '?')}] plantilla no reconocida: {unit.get('plantilla')}")


def check_totals(unit: dict, errors: list[str]) -> None:
    if unit.get("archivos_total") != len(unit.get("archivos", [])):
        errors.append(
            f"[{unit.get('id')}] archivos_total={unit.get('archivos_total')} "
            f"!= len(archivos)={len(unit.get('archivos', []))}"
        )


def check_inventario(unit: dict, inv_index: set, warnings: list[str]) -> None:
    for f in unit.get("archivos", []):
        key = (f.get("fuente", ""), f.get("ruta", ""))
        if key not in inv_index:
            warnings.append(
                f"[{unit.get('id')}] archivo no esta en inventario: {key[0]}:{key[1]}"
            )


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--units-dir", type=Path, default=UNITS_DEFAULT)
    p.add_argument("--ledger", type=Path, default=LEDGER_DEFAULT)
    p.add_argument("--inventario", type=Path, default=INVENTARIO_DEFAULT)
    p.add_argument("--index", type=Path, default=INDEX_DEFAULT)
    p.add_argument("--quiet", action="store_true")
    p.add_argument("--no-color", action="store_true")
    p.add_argument("--json", action="store_true", dest="as_json")
    p.add_argument("--estados", default="all",
                   choices=["all", "pendiente"],
                   help="Que filas de cobertura.csv contar contra las unidades. "
                        "'all' (default) = toda fila asignada, que es el "
                        "invariante real del ledger. 'pendiente' = solo las no "
                        "verificadas, para validar un build_units temporal "
                        "generado antes de cerrar sub-fases.")
    args = p.parse_args(argv)

    use_color = (not args.no_color) and sys.stdout.isatty()

    unit_paths = sorted(args.units_dir.glob("[!_]*.json"))
    if not unit_paths:
        print(f"ERROR: no hay unidades en {args.units_dir}", file=sys.stderr)
        return 2

    inv_index: set = set()
    if args.inventario.is_file():
        try:
            inv = json.loads(args.inventario.read_text(encoding="utf-8"))
            for f in inv.get("files", []):
                inv_index.add((f["fuente"], f["ruta_rel"]))
        except json.JSONDecodeError as e:
            print(f"WARN: inventario no es JSON valido: {e}", file=sys.stderr)

    errors: list[str] = []
    warnings: list[str] = []
    by_feature: Counter = Counter()
    seen: dict[tuple[str, str], str] = {}  # (fuente, ruta) -> unit_id
    total_files_in_units = 0
    units: list[dict] = []
    for path in unit_paths:
        try:
            unit = load_unit(path)
        except json.JSONDecodeError as e:
            errors.append(f"{path.name}: JSON invalido: {e}")
            continue
        # Las unidades B1.x usan otro esquema: `archivos` es una lista de
        # documentos de OUT (no de ficheros de SRC) y `feature_id` no aplica.
        # validate-A4.2.sh Check 3 ya las excluye; aquí se excluyen igual.
        if str(unit.get("id", "")).startswith("B"):
            continue
        check_schema(unit, errors)
        check_totals(unit, errors)
        if inv_index:
            check_inventario(unit, inv_index, warnings)
        for f in unit.get("archivos", []):
            key = (f.get("fuente", ""), f.get("ruta", ""))
            if key in seen:
                errors.append(
                    f"archivo {key[0]}:{key[1]} aparece en {seen[key]} y en {unit.get('id')}"
                )
            seen[key] = unit.get("id")
        by_feature[unit.get("feature_id", "?")] += 1
        total_files_in_units += unit.get("archivos_total", 0)
        units.append(unit)

    # Invariante del ledger: cada fila asignada (feature_ids no vacio) debe estar
    # en exactamente una unidad, este o verificado. Anteriormente se comparaba solo
    # contra las filas `pendiente`, lo que breakaba en cuanto una sub-unidad se
    # cerraba (sus archivos seguian en su unit.json pero pasaban a `verificado`).
    ledger_total = 0
    ledger_pendientes = 0
    if args.ledger.is_file():
        with args.ledger.open(encoding="utf-8", newline="") as f:
            r = csv.DictReader(f)
            for row in r:
                if not row.get("feature_ids", "").strip():
                    continue
                if args.estados == "pendiente" and row.get("estado") != "pendiente":
                    continue
                ledger_total += 1
                if row.get("estado") == "pendiente":
                    ledger_pendientes += 1
    if total_files_in_units != ledger_total:
        errors.append(
            f"suma archivos_total en unidades ({total_files_in_units}) "
            f"!= filas asignadas[{args.estados}] en cobertura.csv ({ledger_total}; "
            f"{ledger_pendientes} pendientes, {ledger_total - ledger_pendientes} verificadas)"
        )

    if args.as_json:
        print(json.dumps({
            "ok": not errors,
            "n_units": len(units),
            "by_feature": dict(by_feature),
            "total_archivos": total_files_in_units,
            "ledger_total": ledger_total,
            "ledger_pendientes": ledger_pendientes,
            "errors": errors,
            "warnings": warnings[:20],
        }, indent=2, ensure_ascii=False))
        return 0 if not errors else 1

    if not args.quiet:
        head = f"{BOLD}[validate_units]{RESET}" if use_color else "[validate_units]"
        print(f"{head} units_dir={args.units_dir}", file=sys.stderr)
        print(f"{head} unidades={len(units)} archivos={total_files_in_units} "
              f"asignados_csv={ledger_total}", file=sys.stderr)
        for fid in sorted(by_feature):
            print(f"  {fid} {by_feature[fid]} unidades", file=sys.stderr)
        if errors:
            print(f"{head} {RED}ERRORS={len(errors)}{RESET}" if use_color else f"[validate_units] ERRORS={len(errors)}", file=sys.stderr)
            for e in errors[:20]:
                print(f"  ERR: {e}", file=sys.stderr)
        if warnings and not args.quiet:
            print(f"{head} warnings={len(warnings)}", file=sys.stderr)
            for w in warnings[:10]:
                print(f"  WARN: {w}", file=sys.stderr)
        if not errors:
            ok = f"{GREEN}OK{RESET}" if use_color else "OK"
            print(f"{head} {ok}", file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
