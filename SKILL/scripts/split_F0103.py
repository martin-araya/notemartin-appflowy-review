#!/usr/bin/env python3
"""split_F0103.py — Divide OUT/_ledger/units/F01.0.3.json en 5 sub-unidades
(0.3.1 editor core, 0.3.2 toolbars, 0.3.3 encoders, 0.3.4 shortcuts,
0.3.5 l10n+utils+misc) siguiendo el plan B3.F01.0 §2.2.

Fase B3.F01.0 de la skill notemartin-appflowy-review.
Ver plan en /Users/martin/.local/share/kilo/plans/1792429084675-b3-f010-indice-documentos-editor.md

Uso:
  split_F0103.py [--unit PATH] [--out-dir PATH] [--quiet]

Salida:
  - OUT/_ledger/units/F01.0.3.1.json ... F01.0.3.5.json (5 nuevos)
  - OUT/_ledger/units/F01.0.3.json (eliminado o vacio)
  - OUT/_ledger/units/F01.0.json (nuevo, indice de orquestacion)
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_PATH = Path(__file__).resolve()
SKILL_ROOT = SCRIPT_PATH.parent.parent.parent
UNITS_DEFAULT = SKILL_ROOT / "OUT" / "_ledger" / "units"

# ---------------------------------------------------------------------------
# Reglas de division (orden = precedencia; primera coincidencia gana).
# Inspirado en assign_ledger.py: orden por longitud de patron descendente.
# ---------------------------------------------------------------------------
DIVISION_RULES: list[tuple[str, str, str, list[str]]] = [
    # (id, titulo, ruta_salida, patrones)
    (
        "F01.0.3.1",
        "Editor core: estado, bloques, infraestructura",
        "OUT/09-features/F01-documentos-y-editor/0.3.1-editor-core-estado-bloques-infraestructura.md",
        [
            # core data structures (Node, Delta, Transaction, Selection)
            "editor/lib/src/core/",
            # block_component base + standard registry (block_component.dart, standard_block_components.dart, base_component/, rich_text/)
            "editor/lib/src/editor/block_component/block_component.dart",
            "editor/lib/src/editor/block_component/standard_block_components.dart",
            "editor/lib/src/editor/block_component/base_component_keys.dart",
            "editor/lib/src/editor/block_component/base_component/",
            "editor/lib/src/editor/block_component/rich_text/",
            # individual block implementations (catalogados aqui; F01.1..F01.9 los referencian)
            "editor/lib/src/editor/block_component/bulleted_list_block_component/",
            "editor/lib/src/editor/block_component/divider_block_component/",
            "editor/lib/src/editor/block_component/heading_block_component/",
            "editor/lib/src/editor/block_component/image_block_component/",
            "editor/lib/src/editor/block_component/numbered_list_block_component/",
            "editor/lib/src/editor/block_component/paragraph_block_component/",
            "editor/lib/src/editor/block_component/quote_block_component/",
            "editor/lib/src/editor/block_component/todo_list_block_component/",
            "editor/lib/src/editor/block_component/table_block_component/",
            # comandos del editor (text_commands, selection_commands, transform)
            "editor/lib/src/editor/command/",
            # editor entry points
            "editor/lib/src/editor/editor.dart",
            "editor/lib/src/editor/editor_component/editor_component.dart",
            "editor/lib/src/editor/editor_component/entry/",
            # state
            "editor/lib/src/editor_state.dart",
            # editor component services & style
            "editor/lib/src/editor/editor_component/service/scroll/",
            "editor/lib/src/editor/editor_component/service/ime/",
            "editor/lib/src/editor/editor_component/service/renderer/",
            "editor/lib/src/editor/editor_component/service/keyboard_service",
            "editor/lib/src/editor/editor_component/service/scroll_service",
            "editor/lib/src/editor/editor_component/service/selection_service",
            "editor/lib/src/editor/editor_component/style/",
            "editor/lib/src/editor/editor_component/service/",
            # infra base
            "editor/lib/src/extensions/",
            "editor/lib/src/flutter/",
            "editor/lib/src/infra/",
            "editor/lib/src/history/",
            "editor/lib/src/render/",
        ],
    ),
    (
        "F01.0.3.2",
        "Editor toolbars (desktop floating + mobile v1/v2/v3), find/replace, selection menu",
        "OUT/09-features/F01-documentos-y-editor/0.3.2-editor-toolbars-find-replace-selection-menu.md",
        [
            "editor/lib/src/editor/toolbar/",
            "editor/lib/src/editor/find_replace_menu/",
            "editor/lib/src/editor/selection_menu/",
        ],
    ),
    (
        "F01.0.3.3",
        "Editor encoders/decoders: Markdown, HTML, JSON (quill delta), PDF, word count",
        "OUT/09-features/F01-documentos-y-editor/0.3.3-editor-encoders-decoders-markdown-html-json-pdf.md",
        [
            "editor/lib/src/plugins/markdown/",
            "editor/lib/src/plugins/html/",
            "editor/lib/src/plugins/pdf/",
            "editor/lib/src/plugins/quill_delta/",
            "editor/lib/src/plugins/word_count/",
            "editor/lib/src/plugins/plugins.dart",
        ],
    ),
    (
        "F01.0.3.4",
        "Editor shortcuts (character + command), IME, default text operations, internal handlers",
        "OUT/09-features/F01-documentos-y-editor/0.3.4-editor-shortcuts-ime-context-menu-servicios.md",
        [
            "editor/lib/src/service/shortcut_event/",
            "editor/lib/src/service/shortcuts/",
            "editor/lib/src/service/default_text_operations/",
            "editor/lib/src/service/internal_key_event_handlers/",
            "editor/lib/src/service/context_menu/",
            "editor/lib/src/service/selection/",
        ],
    ),
    (
        "F01.0.3.5",
        "Editor L10n + util + plugins/blocks + misc",
        "OUT/09-features/F01-documentos-y-editor/0.3.5-editor-l10n-utils-bloques-misc.md",
        [
            "editor/lib/src/l10n/",
            "editor/lib/src/editor/l10n/",
            "editor/lib/src/editor/util/",
            "editor/lib/src/editor/util/file_picker/",
            "editor/lib/src/editor/style/",
            "editor/lib/src/plugins/blocks/",
        ],
    ),
]

INDEX_UNIT: dict[str, Any] = {
    "schema_version": 1,
    "id": "F01.0",
    "feature_id": "F01",
    "sub_index": 0,
    "titulo": "Indice de documentos y editor (orquestacion cross-cutting)",
    "fuentes": ["appflowy", "collab", "editor"],
    "archivos": [],
    "archivos_total": 0,
    "catalogos": [
        "blocs.json",
        "deps.json",
        "events.json",
        "misc.json",
        "notifications.json",
        "protobuf.json",
    ],
    "catalogos_razon": {
        "events.json": "Eventos FFI / dispatch del feature completo (21 eventos flowy-document)",
        "blocs.json": "Todos los BLoCs Dart del feature (DocumentBloc, DocumentSyncBloc, ...)",
        "protobuf.json": "Entidades protobuf DocumentDataPB, ApplyActionPB, ... input/output de los eventos",
        "notifications.json": "Notificaciones DocumentNotification emitidas por Rust+escuchadas por Dart",
        "deps.json": "Dependencias del workspace rust y pubspec (flowy-document + appflowy_editor)",
        "misc.json": "Rutas go_router, atajos, flags, error codes, i18n, startup tasks del editor",
    },
    "dependencias": [
        {"id": "F01.0.1", "relacion": "sub-unidad"},
        {"id": "F01.0.2", "relacion": "sub-unidad"},
        {"id": "F01.0.3.1", "relacion": "sub-unidad"},
        {"id": "F01.0.3.2", "relacion": "sub-unidad"},
        {"id": "F01.0.3.3", "relacion": "sub-unidad"},
        {"id": "F01.0.3.4", "relacion": "sub-unidad"},
        {"id": "F01.0.3.5", "relacion": "sub-unidad"},
    ],
    "plantilla": "feature",
    "documento": "OUT/09-features/F01-documentos-y-editor/0.0-indice-documentos-y-editor.md",
    "metricas": {
        "archivos": 0,
        "por_capa": {},
        "por_fuente": {},
        "es_indice": True,
    },
    "prioridad": 1,
    "concurrencia": "serial",
}


def _classify(ruta: str) -> str | None:
    """Devuelve el id de sub-unidad segun las reglas (primera coincidencia
    en orden; si no hay match, devuelve None -> archivo no asignable)."""
    # path like editor/lib/src/...; las reglas apuntan a subpaths
    for unit_id, _titulo, _ruta_out, patterns in DIVISION_RULES:
        for p in patterns:
            if p in ruta:
                return unit_id
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--units",
        type=Path,
        nargs="+",
        default=[UNITS_DEFAULT / "F01.0.3.json"],
        help="Unidades origen (concatena archivos; util para re-classify)",
    )
    ap.add_argument("--out-dir", type=Path, default=UNITS_DEFAULT)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    archivos: list[dict[str, Any]] = []
    catalogos: list[str] = []
    catalogos_razon: dict[str, str] = {}
    for unit_path in args.units:
        if not unit_path.exists():
            print(
                f"WARN: unidad no encontrada, se omite: {unit_path}", file=sys.stderr
            )
            continue
        with unit_path.open() as f:
            u = json.load(f)
        archivos.extend(u["archivos"])
        for c in u.get("catalogos", []):
            if c not in catalogos:
                catalogos.append(c)
        catalogos_razon.update(u.get("catalogos_razon", {}))
    if not archivos:
        print(f"ERROR: ningun archivo recogido de {args.units}", file=sys.stderr)
        return 1
    n_total = len(archivos)

    # Distribuir
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    orphans: list[dict[str, Any]] = []
    for ar in archivos:
        sub = _classify(ar["ruta"])
        if sub is None:
            orphans.append(ar)
        else:
            buckets[sub].append(ar)

    # Crear sub-unidades
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    written: list[Path] = []
    for unit_id, titulo, doc_out, _patterns in DIVISION_RULES:
        items = buckets.get(unit_id, [])
        capas = Counter(a["capa"] for a in items)
        fuentes = Counter(a["fuente"] for a in items)
        new_unit = {
            "schema_version": 1,
            "id": unit_id,
            "feature_id": "F01",
            "sub_index": 0,
            "titulo": titulo,
            "fuentes": ["editor"],
            "archivos": items,
            "archivos_total": len(items),
            "catalogos": list(catalogos),
            "catalogos_razon": dict(catalogos_razon),
            "dependencias": [
                {"id": "F01.0", "relacion": "indice"},
                {"id": "F01.0.2", "relacion": "precedente (modelo de datos collab)"},
                {"id": "F01.0.1", "relacion": "precedente (DocumentBloc + servicios Dart)"},
            ],
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

    # Crear F01.0 (indice)
    index_path = args.out_dir / "F01.0.json"
    with index_path.open("w") as f:
        json.dump(INDEX_UNIT, f, indent=2, ensure_ascii=False)
    written.append(index_path)
    if not args.quiet:
        print(f"OK F01.0: indice (0 archivos, 8 dependencias)")

    # Manejo de archivos no asignados
    if orphans:
        print(
            f"WARN: {len(orphans)} archivos no asignados en F01.0.3 -> se conservan en F01.0.3.json",
            file=sys.stderr,
        )
        # Moverlos a una unidad "tierra de nadie" para no perder evidencia
        if orphans:
            orphans_unit = {
                "schema_version": 1,
                "id": "F01.0.3.6",
                "feature_id": "F01",
                "sub_index": 0,
                "titulo": "Editor: archivos miscelaneos (subdocs faltan)",
                "fuentes": ["editor"],
                "archivos": orphans,
                "archivos_total": len(orphans),
                "catalogos": list(catalogos),
                "catalogos_razon": dict(catalogos_razon),
                "dependencias": [],
                "plantilla": "feature",
                "documento": "OUT/09-features/F01-documentos-y-editor/0.3.6-editor-miscelaneos.md",
                "metricas": {
                    "archivos": len(orphans),
                    "por_capa": dict(Counter(a["capa"] for a in orphans)),
                    "por_fuente": dict(Counter(a["fuente"] for a in orphans)),
                },
                "prioridad": 5,
                "concurrencia": "paralela",
                "generado_en": now,
            }
            out_path = args.out_dir / "F01.0.3.6.json"
            with out_path.open("w") as f:
                json.dump(orphans_unit, f, indent=2, ensure_ascii=False)
            written.append(out_path)
            # crear doc vacio
            doc_path = SKILL_ROOT / orphans_unit["documento"]
            doc_path.parent.mkdir(parents=True, exist_ok=True)
            if not doc_path.exists():
                doc_path.write_text(
                    "---\n"
                    f"id: F01.0.3.6\n"
                    f"titulo: {orphans_unit['titulo']}\n"
                    f"fuente: editor\n"
                    f"archivos_cubiertos: []\n"
                    f"estado: pendiente\n"
                    "---\n"
                )
                written.append(doc_path)

    # Eliminar F01.0.3.json (si existia como input). Si el usuario paso
    # varias unidades (caso re-classify), las conservamos: solo borramos la
    # primera si es F01.0.3.json y hay sub-unidades generadas.
    if args.units and len(args.units) == 1 and args.units[0].name == "F01.0.3.json":
        args.units[0].unlink(missing_ok=True)
        if not args.quiet:
            print(f"OK eliminado {args.units[0]}")

    # Resumen final
    total_buckets = sum(len(v) for v in buckets.values())
    total_orphans = len(orphans)
    if not args.quiet:
        print()
        print(
            f"Resumen: {n_total} archivos en F01.0.3 -> {total_buckets} redistribuidos + {total_orphans} en F01.0.3.6"
        )
        if total_buckets + total_orphans != n_total:
            print(
                f"ERROR ARITMETICA: {total_buckets}+{total_orphans} != {n_total}",
                file=sys.stderr,
            )
            return 2
        for uid in sorted(buckets.keys()):
            print(f"  {uid}: {len(buckets[uid])}")
        if orphans:
            print(f"  F01.0.3.6: {len(orphans)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
