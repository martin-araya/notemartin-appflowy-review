#!/usr/bin/env python3
"""split_F0209.py — Divide OUT/_ledger/units/F02.9.json (61 archivos) en
3 sub-unidades (F02.9.0 indice + grid layout + core BLoCs, F02.9.1 filter + calculations widgets, F02.9.2 sort + header + row + footer + toolbar).

Adaptado del patron split_F0106.py. Ver plan
~/.local/share/kilo/plans/1792453115498-f02-6-to-12-completion.md
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
        "F02.9.0",
        "Indice Grid (layout principal, scroll, page, 4 BLoCs raiz)",
        "OUT/09-features/F02-bases-de-datos/9.0-grid-indice-plugins-database-grid.md",
        [
            "appflowy/frontend/appflowy_flutter/lib/plugins/database/grid/grid.dart",
            "appflowy/frontend/appflowy_flutter/lib/plugins/database/grid/presentation/grid_page.dart",
            "appflowy/frontend/appflowy_flutter/lib/plugins/database/grid/presentation/grid_scroll.dart",
            "appflowy/frontend/appflowy_flutter/lib/plugins/database/grid/presentation/layout/layout.dart",
            "appflowy/frontend/appflowy_flutter/lib/plugins/database/grid/presentation/layout/sizes.dart",
            "appflowy/frontend/appflowy_flutter/lib/plugins/database/grid/presentation/mobile_grid_page.dart",
            "appflowy/frontend/appflowy_flutter/lib/plugins/database/grid/presentation/widgets/mobile_fab.dart",
            "appflowy/frontend/appflowy_flutter/lib/plugins/database/grid/presentation/widgets/shortcuts.dart",
            "appflowy/frontend/appflowy_flutter/lib/plugins/database/grid/application/grid_bloc.dart",
            "appflowy/frontend/appflowy_flutter/lib/plugins/database/grid/application/grid_accessory_bloc.dart",
            "appflowy/frontend/appflowy_flutter/lib/plugins/database/grid/application/grid_header_bloc.dart",
            "appflowy/frontend/appflowy_flutter/lib/plugins/database/grid/application/row/row_bloc.dart",
        ],
    ),
    (
        "F02.9.1",
        "Grid filters y calculations widgets (filter_editor_bloc, simple_text_filter_bloc, choicechips, calculations widgets, common)",
        "OUT/09-features/F02-bases-de-datos/9.1-grid-filtros-y-filter-choicechips.md",
        [
            "appflowy/frontend/appflowy_flutter/lib/plugins/database/grid/application/filter/filter_editor_bloc.dart",
            "appflowy/frontend/appflowy_flutter/lib/plugins/database/grid/application/filter/select_option_loader.dart",
            "appflowy/frontend/appflowy_flutter/lib/plugins/database/grid/application/simple_text_filter_bloc.dart",
            "appflowy/frontend/appflowy_flutter/lib/plugins/database/grid/application/calculations/calculations_bloc.dart",
            "appflowy/frontend/appflowy_flutter/lib/plugins/database/grid/application/calculations/field_type_calc_ext.dart",
            "appflowy/frontend/appflowy_flutter/lib/plugins/database/grid/presentation/widgets/filter/",
            "appflowy/frontend/appflowy_flutter/lib/plugins/database/grid/presentation/widgets/calculations/",
            "appflowy/frontend/appflowy_flutter/lib/plugins/database/grid/presentation/widgets/common/",
        ],
    ),
    (
        "F02.9.2",
        "Grid sort, header, row detail/mobile, footer, toolbar",
        "OUT/09-features/F02-bases-de-datos/9.2-grid-sort-header-row-footer-toolbar-shortcuts.md",
        [
            "appflowy/frontend/appflowy_flutter/lib/plugins/database/grid/application/sort/sort_editor_bloc.dart",
            "appflowy/frontend/appflowy_flutter/lib/plugins/database/grid/application/row/mobile_row_detail_bloc.dart",
            "appflowy/frontend/appflowy_flutter/lib/plugins/database/grid/application/row/row_detail_bloc.dart",
            "appflowy/frontend/appflowy_flutter/lib/plugins/database/grid/application/row/row_document_bloc.dart",
            "appflowy/frontend/appflowy_flutter/lib/plugins/database/grid/presentation/widgets/sort/",
            "appflowy/frontend/appflowy_flutter/lib/plugins/database/grid/presentation/widgets/header/",
            "appflowy/frontend/appflowy_flutter/lib/plugins/database/grid/presentation/widgets/row/",
            "appflowy/frontend/appflowy_flutter/lib/plugins/database/grid/presentation/widgets/footer/",
            "appflowy/frontend/appflowy_flutter/lib/plugins/database/grid/presentation/widgets/toolbar/",
        ],
    ),
]


def _classify(ruta: str) -> str | None:
    for unit_id, _titulo, _doc, patterns in DIVISION_RULES:
        for p in patterns:
            if p.endswith("/") and ruta.startswith(p):
                return unit_id
            if ruta.startswith(p) or ruta == p:
                return unit_id
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--unit", type=Path, default=UNITS_DEFAULT / "F02.9.json")
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
            "fuentes": unit.get("fuentes", ["appflowy"]),
            "archivos": items,
            "archivos_total": len(items),
            "catalogos": unit.get("catalogos", []),
            "catalogos_razon": unit.get("catalogos_razon", {}),
            "dependencias": [{"id": "F02.0", "relacion": "indice"}],
            "plantilla": "feature",
            "documento": doc_out,
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

    if orphans:
        print(f"\nWARN: {len(orphans)} archivos orphan (sin categoria):", file=sys.stderr)
        for o in orphans[:10]:
            print(f"  - {o['ruta']}", file=sys.stderr)
        if len(orphans) > 10:
            print(f"  ... and {len(orphans) - 10} more", file=sys.stderr)

    total = sum(len(b) for b in buckets.values())
    if not args.quiet:
        print(f"\nResumen: {n_total} archivos -> {total} redistribuidos + {len(orphans)} orphan")

    if total + len(orphans) != n_total:
        print(f"ERROR ARITMETICA: {total}+{len(orphans)} != {n_total}", file=sys.stderr)
        return 2

    args.unit.unlink(missing_ok=True)
    if not args.quiet:
        print(f"OK eliminado {args.unit}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
