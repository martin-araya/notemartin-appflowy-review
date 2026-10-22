#!/usr/bin/env python3
"""split_F0202.py — Divide OUT/_ledger/units/F02.0.2.json (113 archivos collab-database Rust) en
3 sub-unidades + 1 indice F02.0.2.0.

Adaptado del pattern split_F0103.py. Ver plan
~/.local/share/kilo/plans/1792429084675-b3-f02-0-1-2-3-4-5-plan.md
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve()
SKILL_ROOT = SCRIPT_PATH.parent.parent.parent
UNITS_DEFAULT = SKILL_ROOT / "OUT" / "_ledger" / "units"

DIVISION_RULES = [
    (
        "F02.0.2.1",
        "collab-database: fields + blocks + meta + workspace_database (model + relations)",
        "0.2.1-collab-database-fields-blocks-meta-workspace-relation.md",
        [
            "src/fields",
            "src/blocks",
            "src/meta",
            "src/workspace_database",
        ],
    ),
    (
        "F02.0.2.2",
        "collab-database: template + views + rows + misc (template.rs, manager lifecycle, view logic)",
        "0.2.2-collab-database-template-views-rows-misc.md",
        [
            "src/template",
            "src/views",
            "src/rows",
            "src/database.rs",
            "src/database_state.rs",
            "src/entity.rs",
            "src/error.rs",
            "src/macros.rs",
            "src/util.rs",
            "src/lib.rs",
        ],
    ),
    (
        "F02.0.2.3",
        "collab-database: tests + Cargo.toml",
        "0.2.3-collab-database-tests.md",
        [
            "tests/database_test",
            "tests/user_test",
            "tests/template_test",
            "tests/history_database",
            "tests/helper",
            "tests/asset",
            "tests/main.rs",
            "Cargo.toml",
        ],
    ),
]

INDEX_UNIT = {
    "schema_version": 1,
    "id": "F02.0.2.0",
    "feature_id": "F02",
    "sub_index": 0,
    "titulo": "Indice F02.0.2 (collab-database Rust: manager.rs, model, template, view logic)",
    "fuentes": ["collab"],
    "archivos": [],
    "archivos_total": 0,
    "catalogos": ["blocs.json", "deps.json", "events.json", "misc.json", "notifications.json", "protobuf.json"],
    "catalogos_razon": {
        "events.json": "Eventos FFI / dispatch del feature F02",
        "blocs.json": "BLoCs / Cubits presentes en los archivos de esta unidad",
        "protobuf.json": "Entidades protobuf input/output de los eventos",
        "notifications.json": "Notificaciones Rust->Dart emitidas o escuchadas",
        "deps.json": "Dependencias del workspace rust y pubspec",
        "misc.json": "Rutas, atajos, flags, error codes, i18n",
    },
    "dependencias": [
        {"id": "F02.0.2.1", "relacion": "sub-unidad"},
        {"id": "F02.0.2.2", "relacion": "sub-unidad"},
        {"id": "F02.0.2.3", "relacion": "sub-unidad"},
    ],
    "plantilla": "feature",
    "documento": "OUT/09-features/F02-bases-de-datos/0.2.0-indice-collab-database-rust-manager-model-template-view.md",
    "metricas": {
        "archivos": 0,
        "por_capa": {},
        "por_fuente": {},
        "es_indice": True,
        "sub_unidades": ["F02.0.2.1", "F02.0.2.2", "F02.0.2.3"],
    },
    "prioridad": 1,
    "concurrencia": "meta",
}


def _classify(ruta: str) -> str | None:
    for unit_id, _titulo, _doc, patterns in DIVISION_RULES:
        for p in patterns:
            if p in ruta:
                return unit_id
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--unit", type=Path, default=UNITS_DEFAULT / "F02.0.2.json")
    ap.add_argument("--out-dir", type=Path, default=UNITS_DEFAULT)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    if not args.unit.exists():
        print(f"ERROR: {args.unit} no existe.", file=sys.stderr)
        return 1

    with args.unit.open() as f:
        unit = json.load(f)
    archivos = unit["archivos"]
    n_total = len(archivos)

    buckets: dict = {uid: [] for uid, *_ in DIVISION_RULES}
    orphans = []
    for ar in archivos:
        sub = _classify(ar["ruta"])
        if sub is None:
            orphans.append(ar)
        else:
            buckets[sub].append(ar)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    written = []

    for unit_id, titulo, doc_out, _patterns in DIVISION_RULES:
        items = buckets[unit_id]
        capas = Counter(a["capa"] for a in items)
        fuentes = Counter(a["fuente"] for a in items)
        new_unit = {
            "schema_version": 1,
            "id": unit_id,
            "feature_id": "F02",
            "sub_index": int(unit_id.rsplit(".", 1)[-1]),
            "titulo": titulo,
            "fuentes": unit.get("fuentes", ["collab"]),
            "archivos": items,
            "archivos_total": len(items),
            "catalogos": unit.get("catalogos", []),
            "catalogos_razon": unit.get("catalogos_razon", {}),
            "dependencias": [{"id": "F02.0.2.0", "relacion": "indice"}],
            "plantilla": "feature",
            "documento": f"OUT/09-features/F02-bases-de-datos/{doc_out}",
            "metricas": {
                "archivos": len(items),
                "por_capa": dict(capas),
                "por_fuente": dict(fuentes),
            },
            "prioridad": 3,
            "concurrencia": "paralela",
            "generado_en": now,
        }
        out_path = args.out_dir / f"{unit_id}.json"
        with out_path.open("w") as f:
            json.dump(new_unit, f, indent=2, ensure_ascii=False)
        written.append(out_path)
        if not args.quiet:
            print(f"OK {unit_id}: {len(items)} archivos")

    index_path = args.out_dir / "F02.0.2.0.json"
    with index_path.open("w") as f:
        json.dump(INDEX_UNIT, f, indent=2, ensure_ascii=False)
    written.append(index_path)
    if not args.quiet:
        print("OK F02.0.2.0: indice (0 archivos, 3 sub-unidades)")

    if orphans:
        print(f"\nWARN: {len(orphans)} archivos orphan:", file=sys.stderr)
        for o in orphans[:20]:
            print(f"  - {o['ruta']}", file=sys.stderr)

    total = sum(len(v) for v in buckets.values())
    if not args.quiet:
        print()
        print(f"Resumen: {n_total} -> {total} + {len(orphans)} orphan")

    if total + len(orphans) != n_total:
        print(f"ERROR ARITMETICA: {total}+{len(orphans)} != {n_total}", file=sys.stderr)
        return 2

    args.unit.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
