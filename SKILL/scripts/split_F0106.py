#!/usr/bin/env python3
"""split_F0106.py v2 — Divide F01.6 en 6 sub-unidades + 1 indice (limpia)."""
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
        "F01.6.1",
        "Slash menu",
        "OUT/09-features/F01-documentos-y-editor/6.1-slash-menu-elementos.md",
        ["editor_plugins/slash_menu/"],
    ),
    (
        "F01.6.2",
        "Block menu, block actions y context menu",
        "OUT/09-features/F01-documentos-y-editor/6.2-block-menu-actions-context-menu.md",
        [
            "editor_plugins/block_menu/",
            "editor_plugins/context_menu/",
            "editor_plugins/actions/block_action_add_button.dart",
            "editor_plugins/actions/block_action_button.dart",
            "editor_plugins/actions/block_action_list.dart",
            "editor_plugins/actions/block_action_option_button.dart",
            "editor_plugins/actions/block_action_option_cubit.dart",
            "editor_plugins/actions/mobile_block_action_buttons.dart",
            "editor_plugins/actions/option/",
        ],
    ),
    (
        "F01.6.3",
        "Drag to reorder",
        "OUT/09-features/F01-documentos-y-editor/6.3-drag-to-reorder.md",
        [
            "editor_plugins/actions/drag_to_reorder/",
            "editor_plugins/actions/menu_extension.dart",
            "editor_plugins/options_toolbar_item.dart",
        ],
    ),
    (
        "F01.6.4",
        "Toolbars desktop, mobile, items y link",
        "OUT/09-features/F01-documentos-y-editor/6.4-toolbars-desktop-mobile-items-link.md",
        [
            "editor_plugins/desktop_toolbar/",
            "editor_plugins/mobile_toolbar_v3/",
            "editor_plugins/mobile_floating_toolbar/",
            "editor_plugins/toolbar_item/",
            "editor_plugins/undo_redo_toolbar_item.dart",
            "editor_plugins/align_toolbar_item/",
        ],
    ),
    (
        "F01.6.5",
        "Copy y paste",
        "OUT/09-features/F01-documentos-y-editor/6.5-copy-y-paste.md",
        ["editor_plugins/copy_and_paste/"],
    ),
    (
        "F01.6.6",
        "Shortcuts, find_and_replace y keyboard",
        "OUT/09-features/F01-documentos-y-editor/6.6-shortcuts-find-replace-keyboard.md",
        [
            "editor_plugins/shortcuts/",
            "editor_plugins/find_and_replace/",
            "editor_plugins/keyboard_interceptor/",
            "editor_plugins/exit_edit_mode_command.dart",
            "editor_plugins/undo_redo/",
        ],
    ),
]

INDEX_UNIT = {
    "schema_version": 1,
    "id": "F01.6.0",
    "feature_id": "F01",
    "sub_index": 0,
    "titulo": "Indice Interaccion (cross-cutting)",
    "fuentes": ["appflowy"],
    "archivos": [],
    "archivos_total": 0,
    "catalogos": [
        "blocs.json", "deps.json", "events.json",
        "misc.json", "notifications.json", "protobuf.json",
    ],
    "catalogos_razon": {
        "events.json": "Eventos FFI / dispatch del feature completo",
        "blocs.json": "BLoCs / Cubits presentes en los archivos de esta unidad",
        "protobuf.json": "Entidades protobuf input/output",
        "notifications.json": "Notificaciones Rust->Dart",
        "deps.json": "Dependencias del workspace",
        "misc.json": "Rutas, atajos, flags, i18n keys",
    },
    "dependencias": [
        {"id": sub, "relacion": "sub-unidad"}
        for sub in ["F01.6.1", "F01.6.2", "F01.6.3", "F01.6.4", "F01.6.5", "F01.6.6"]
    ],
    "plantilla": "feature",
    "documento": "OUT/09-features/F01-documentos-y-editor/6.0-indice-interaccion.md",
    "metricas": {
        "archivos": 0,
        "por_capa": {},
        "por_fuente": {},
        "es_indice": True,
        "sub_unidades": ["F01.6.1", "F01.6.2", "F01.6.3", "F01.6.4", "F01.6.5", "F01.6.6"],
    },
    "prioridad": 1,
    "concurrencia": "meta",
}


def _classify(ruta: str) -> str | None:
    parts = ruta.split("/")
    if "editor_plugins" in parts:
        idx = parts.index("editor_plugins")
        rel = "/".join(parts[idx:])
    else:
        return None
    for unit_id, _titulo, _doc, patterns in DIVISION_RULES:
        for p in patterns:
            if rel.startswith(p):
                return unit_id
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--unit", type=Path, default=UNITS_DEFAULT / "F01.6.json")
    ap.add_argument("--out-dir", type=Path, default=UNITS_DEFAULT)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    if not args.unit.exists():
        print(f"ERROR: {args.unit} no existe. Pasa --unit explícito o reconstruye F01.6.json desde cobertura.")
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
            "feature_id": "F01",
            "sub_index": int(unit_id.rsplit(".", 1)[-1]),
            "titulo": titulo,
            "fuentes": unit.get("fuentes", ["appflowy"]),
            "archivos": items,
            "archivos_total": len(items),
            "catalogos": unit.get("catalogos", []),
            "catalogos_razon": unit.get("catalogos_razon", {}),
            "dependencias": [{"id": "F01.6.0", "relacion": "indice"}],
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

    index_path = args.out_dir / "F01.6.0.json"
    with index_path.open("w") as f:
        json.dump(INDEX_UNIT, f, indent=2, ensure_ascii=False)
    written.append(index_path)
    if not args.quiet:
        print("OK F01.6.0: indice (0 archivos, 6 sub-unidades)")

    if orphans:
        print(f"\nWARN: {len(orphans)} archivos orphan (sin categoria):", file=sys.stderr)
        for o in orphans:
            print(f"  - {o['ruta']}", file=sys.stderr)

    # Eliminar el unit origen F01.6.json (lo regenerara build_units).
    args.unit.unlink(missing_ok=True)
    if not args.quiet:
        print(f"OK eliminado {args.unit}")

    if not args.quiet:
        print("\nResumen por sub-unidad:")
        for uid in sorted(buckets.keys()):
            print(f"  {uid}: {len(buckets[uid])}")
        print(f"  total: {sum(len(b) for b in buckets.values())}/{n_total}")
        print(f"  orphan: {len(orphans)}")

    total = sum(len(b) for b in buckets.values())
    if total + len(orphans) != n_total:
        print(f"ERROR ARITMETICA: {total}+{len(orphans)} != {n_total}", file=sys.stderr)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
