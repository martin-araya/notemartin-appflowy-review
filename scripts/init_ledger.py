#!/usr/bin/env python3
# init_ledger.py — Inicializa OUT/_ledger/cobertura.csv desde
#   OUT/_ledger/inventario.json con todas las filas en estado sin_asignar.
# Ver AGENTS.md §9 y ROADMAP.md A1.3.
#
# Uso:
#   init_ledger.py [--inventario PATH] [--out PATH] [--help]
#
# Esquema del CSV (7 columnas, en este orden):
#   fuente, ruta, capa, feature_ids, documento, estado, verificado_por
# Estado inicial: sin_asignar; feature_ids/documento/verificado_por vacíos.

import argparse
import csv
import json
import sys
from pathlib import Path

# ---------- constantes (D3, D6) ----------

SCRIPT_PATH = Path(__file__).resolve()
SKILL_ROOT = SCRIPT_PATH.parent.parent.parent  # SKILL/scripts/init_ledger.py → skill_root
INVENTARIO_DEFAULT = SKILL_ROOT / "OUT" / "_ledger" / "inventario.json"
COBERTURA_DEFAULT = SKILL_ROOT / "OUT" / "_ledger" / "cobertura.csv"

HEADER = (
    "fuente",
    "ruta",
    "capa",
    "feature_ids",
    "documento",
    "estado",
    "verificado_por",
)
ESTADO_INICIAL = "sin_asignar"
COLS_VACIAS_INICIALES = ("feature_ids", "documento", "verificado_por")


# ---------- helpers ----------

def load_inventario(path: Path) -> list[dict]:
    if not path.is_file():
        print(f"ERROR: no existe {path}", file=sys.stderr)
        sys.exit(2)
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: {path} no es JSON válido: {e}", file=sys.stderr)
        sys.exit(2)
    if d.get("schema_version") != 1:
        print(f"ERROR: schema_version esperado 1, hay {d.get('schema_version')}", file=sys.stderr)
        sys.exit(2)
    if "files" not in d or not isinstance(d["files"], list):
        print(f"ERROR: {path} no tiene clave 'files' como lista", file=sys.stderr)
        sys.exit(2)
    return d["files"]


def write_cobertura(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    # newline="" según recomendación de la stdlib para csv en Windows/POSIX.
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, dialect="excel", quoting=csv.QUOTE_MINIMAL)
        w.writerow(HEADER)
        for r in rows:
            w.writerow((
                r["fuente"],
                r["ruta_rel"],     # mapeo: inventario usa 'ruta_rel', CSV usa 'ruta' (D4)
                r["capa"],
                "",                # feature_ids
                "",                # documento
                ESTADO_INICIAL,    # sin_asignar
                "",                # verificado_por
            ))


# ---------- CLI ----------

def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="Inicializa _ledger/cobertura.csv desde inventario.json con todas las filas en sin_asignar.",
    )
    p.add_argument("--inventario", type=Path, default=INVENTARIO_DEFAULT,
                   help=f"Path al inventario (default: {INVENTARIO_DEFAULT})")
    p.add_argument("--out", type=Path, default=COBERTURA_DEFAULT,
                   help=f"Path al CSV de salida (default: {COBERTURA_DEFAULT})")
    return p.parse_args(argv)


# ---------- main ----------

def main(argv=None):
    args = parse_args(argv)
    inv_path: Path = args.inventario
    out_path: Path = args.out

    files = load_inventario(inv_path)
    # Orden estable por (fuente, ruta_rel) — el inventario ya viene así,
    # pero por si acaso. Mapeamos a la columna 'ruta' del CSV (D4).
    files.sort(key=lambda e: (e["fuente"], e["ruta_rel"]))
    write_cobertura(files, out_path)

    # Resumen a stderr
    by_fuente = {}
    by_capa = {}
    for f in files:
        by_fuente[f["fuente"]] = by_fuente.get(f["fuente"], 0) + 1
        by_capa[f["capa"]] = by_capa.get(f["capa"], 0) + 1
    print(f"  rows:  {len(files)}", file=sys.stderr)
    for fu in ("appflowy", "collab", "editor"):
        print(f"    {fu:10} {by_fuente.get(fu, 0)} rows", file=sys.stderr)
    print(f"  by_capa: {dict(sorted(by_capa.items()))}", file=sys.stderr)
    print(f"  escrito: {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
