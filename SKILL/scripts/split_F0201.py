#!/usr/bin/env python3
"""split_F0201.py — Divide OUT/_ledger/units/F02.0.1.json (283 archivos) en
3 sub-unidades + 1 indice F02.0.0.0.

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
        "F02.0.1.1",
        "Database widgets (cell, row, field, setting, card, group) + Rust entities (cell_entities, row_entities, field_entities, type_option_entities)",
        "0.1.1-database-widgets-cell-row-field-setting-card-group.md",
        [
            "plugins/database/widgets/cell",
            "plugins/database/widgets/cell_editor",
            "plugins/database/widgets/row",
            "plugins/database/widgets/field",
            "plugins/database/widgets/setting",
            "plugins/database/widgets/card",
            "plugins/database/widgets/group",
            "plugins/database/widgets/share_button",
            "plugins/database/widgets/media_file_type_ext",
            "plugins/database/widgets/database_view_widget",
            "plugins/database/widgets/database_layout_ext",
            "rust-lib/flowy-database2/src/entities/cell_entities",
            "rust-lib/flowy-database2/src/entities/row_entities",
            "rust-lib/flowy-database2/src/entities/field_entities",
            "rust-lib/flowy-database2/src/entities/type_option_entities",
            "rust-lib/flowy-database2/src/entities/filter_entities",  # also goes here for consistency
            "rust-lib/flowy-database2/src/entities/sort_entities",  # if present
        ],
    ),
    (
        "F02.0.1.2",
        "Database application + domain + misc (DatabaseController, DatabaseView, layouts, settings) + Rust infrastructure (manager, lib, event_map, event_handler, notification, services, utils, database_entities, group_entities, file_entities, view_entities, field_settings_entities, board_entities, calendar_entities, calculation)",
        "0.1.2-database-application-domain-misc.md",
        [
            "plugins/database/application/",
            "plugins/database/domain",
            "plugins/database/database_editor",
            "plugins/database/mod.rs",
            "rust-lib/flowy-database2/src/manager",
            "rust-lib/flowy-database2/src/lib.rs",
            "rust-lib/flowy-database2/src/event_handler",
            "rust-lib/flowy-database2/src/event_map",
            "rust-lib/flowy-database2/src/notification",
            "rust-lib/flowy-database2/src/template.rs",
            "rust-lib/flowy-database2/src/utils",
            "rust-lib/flowy-database2/src/services",
            "rust-lib/flowy-database2/src/entities/database_entities",
            "rust-lib/flowy-database2/src/entities/group_entities",
            "rust-lib/flowy-database2/src/entities/file_entities",
            "rust-lib/flowy-database2/src/entities/view_entities",
            "rust-lib/flowy-database2/src/entities/field_settings_entities",
            "rust-lib/flowy-database2/src/entities/board_entities",
            "rust-lib/flowy-database2/src/entities/calendar_entities",
            "rust-lib/flowy-database2/src/entities/calculation",
        ],
    ),
    (
        "F02.0.1.3",
        "Database tests (filter, group, sort, field, cell, calculations, pre_fill, share, mock_data)",
        "0.1.3-database-tests.md",
        [
            "plugins/database/filter_test",
            "plugins/database/group_test",
            "plugins/database/sort_test",
            "plugins/database/pre_fill_cell_test",
            "plugins/database/mock_data",
            "plugins/database/field_test",
            "plugins/database/layout_test",
            "plugins/database/field_settings_test",
            "plugins/database/cell_test",
            "plugins/database/calculations_test",
            "plugins/database/block_test",
            "plugins/database/share_test",
            "plugins/database/widgets/card/container",  # 1 file
        ],
    ),
]

INDEX_UNIT = {
    "schema_version": 1,
    "id": "F02.0.1.0",
    "feature_id": "F02",
    "sub_index": 0,
    "titulo": "Indice F02.0.1 (appflowy side: DatabaseController + services + widgets)",
    "fuentes": ["appflowy"],
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
        {"id": "F02.0.1.1", "relacion": "sub-unidad"},
        {"id": "F02.0.1.2", "relacion": "sub-unidad"},
        {"id": "F02.0.1.3", "relacion": "sub-unidad"},
    ],
    "plantilla": "feature",
    "documento": "OUT/09-features/F02-bases-de-datos/0.1.0-indice-appflowy-side-database-controller-services-widgets.md",
    "metricas": {
        "archivos": 0,
        "por_capa": {},
        "por_fuente": {},
        "es_indice": True,
        "sub_unidades": ["F02.0.1.1", "F02.0.1.2", "F02.0.1.3"],
    },
    "prioridad": 1,
    "concurrencia": "meta",
}


def _classify(ruta: str) -> str | None:
    for unit_id, _titulo, _doc, patterns in DIVISION_RULES:
        for p in patterns:
            if ruta.startswith(p) or p in ruta:
                return unit_id
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--unit", type=Path, default=UNITS_DEFAULT / "F02.0.1.json")
    ap.add_argument("--out-dir", type=Path, default=UNITS_DEFAULT)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    if not args.unit.exists():
        print(f"ERROR: {args.unit} no existe. Pasa --unit explicito o reconstruye F02.0.1.json.", file=sys.stderr)
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
            "fuentes": unit.get("fuentes", ["appflowy"]),
            "archivos": items,
            "archivos_total": len(items),
            "catalogos": unit.get("catalogos", []),
            "catalogos_razon": unit.get("catalogos_razon", {}),
            "dependencias": [{"id": "F02.0.1.0", "relacion": "indice"}],
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

    index_path = args.out_dir / "F02.0.1.0.json"
    with index_path.open("w") as f:
        json.dump(INDEX_UNIT, f, indent=2, ensure_ascii=False)
    written.append(index_path)
    if not args.quiet:
        print("OK F02.0.1.0: indice (0 archivos, 3 sub-unidades)")

    if orphans:
        print(f"\nWARN: {len(orphans)} archivos orphan (sin categoria):", file=sys.stderr)
        for o in orphans[:20]:
            print(f"  - {o['ruta']}", file=sys.stderr)
        if len(orphans) > 20:
            print(f"  ... and {len(orphans) - 20} more", file=sys.stderr)

    total = sum(len(v) for v in buckets.values())
    if not args.quiet:
        print()
        print(f"Resumen: {n_total} archivos -> {total} redistribuidos + {len(orphans)} orphan")

    if total + len(orphans) != n_total:
        print(f"ERROR ARITMETICA: {total}+{len(orphans)} != {n_total}", file=sys.stderr)
        return 2

    args.unit.unlink(missing_ok=True)
    if not args.quiet:
        print(f"OK eliminado {args.unit}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
