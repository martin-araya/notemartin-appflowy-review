#!/usr/bin/env python3
"""make_b4_units.py — crea las 14 unidades del Bloque B4 (motor de
exportación, importación y publicación) con su lista real de archivos.

Las unidades B4 usan el esquema transversal de `B1.x`: `archivos` es la lista
de ficheros que el documento RECONSTRUYE (no una partición del ledger) y no
tocan `cobertura.csv`, porque esos ficheros ya pertenecen a alguna feature F* y
están verificados (el ledger está al 100 % desde el cierre de B3).

Uso:
  python3 make_b4_units.py              # crea/actualiza las 14
  python3 make_b4_units.py --list       # solo lista el plan
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
UNITS = PROJECT_ROOT / "OUT" / "_ledger" / "units"
OUT_DOCS = PROJECT_ROOT / "OUT" / "10-motor-export-import"

A = "appflowy/frontend/appflowy_flutter/lib/"
R = "appflowy/frontend/rust-lib/"
E = "editor/lib/src/"
C = "collab/"

# --- Bloques de archivos reutilizables -------------------------------------
DOC_EXPORT_UI = [
    f"{A}workspace/application/export/document_exporter.dart",
    f"{A}plugins/shared/share/export_tab.dart",
    f"{A}plugins/shared/share/_shared.dart",
]
IMPORT_UI = [
    f"{A}workspace/presentation/home/menu/sidebar/import/import_panel.dart",
    f"{A}workspace/presentation/home/menu/sidebar/import/import_type.dart",
    f"{A}workspace/application/settings/share/import_service.dart",
    f"{A}workspace/presentation/home/menu/sidebar/workspace/_sidebar_import_notion.dart",
    f"{A}util/file_extension.dart",
]
MARKDOWN_ENGINE = [
    f"{A}shared/markdown_to_document.dart",
    f"{E}plugins/markdown/document_markdown.dart",
]
HTML_ENGINE = [
    f"{E}plugins/html/html_document.dart",
    f"{E}plugins/html/html_document_encoder.dart",
    f"{E}plugins/html/html_document_decoder.dart",
    f"{E}plugins/html/encoder/delta_html_encoder.dart",
    f"{E}plugins/html/encoder/parser/html_node_parser.dart",
    f"{E}plugins/html/encoder/parser/html_parser.dart",
    f"{E}plugins/html/encoder/parser/text_node_parser.dart",
    f"{E}plugins/html/encoder/parser/heading_node_parser.dart",
    f"{E}plugins/html/encoder/parser/bulleted_list_node_parser.dart",
    f"{E}plugins/html/encoder/parser/numbered_list_node_parser.dart",
    f"{E}plugins/html/encoder/parser/todo_list_node_parser.dart",
    f"{E}plugins/html/encoder/parser/quote_node_parser.dart",
    f"{E}plugins/html/encoder/parser/divider_node_parser.dart",
    f"{E}plugins/html/encoder/parser/image_node_parser.dart",
    f"{E}plugins/html/encoder/parser/table_node_parser.dart",
]
CSV_ENGINE = [
    f"{A}plugins/database/application/share_bloc.dart",
    f"{R}flowy-database2/src/services/share/csv/mod.rs",
    f"{R}flowy-database2/src/services/share/csv/export.rs",
    f"{R}flowy-database2/src/services/share/csv/import.rs",
    f"{R}flowy-database2/src/event_handler.rs",
    f"{R}flowy-database2/src/event_map.rs",
]
FOLDER_SHARE = [
    f"{R}flowy-folder/src/share/mod.rs",
    f"{R}flowy-folder/src/share/import.rs",
    f"{R}flowy-folder/src/publish_util.rs",
    f"{R}flowy-folder/src/event_handler.rs",
    f"{R}flowy-folder/src/event_map.rs",
]
IMPORTER = [
    f"{C}collab-importer/src/lib.rs",
    f"{C}collab-importer/src/error.rs",
    f"{C}collab-importer/src/imported_collab.rs",
    f"{C}collab-importer/src/space_view.rs",
    f"{C}collab-importer/src/util.rs",
    f"{C}collab-importer/src/notion/mod.rs",
    f"{C}collab-importer/src/notion/importer.rs",
    f"{C}collab-importer/src/notion/file.rs",
    f"{C}collab-importer/src/notion/page.rs",
    f"{C}collab-importer/src/notion/walk_dir.rs",
    f"{C}collab-importer/src/zip_tool/mod.rs",
    f"{C}collab-importer/src/zip_tool/async_zip.rs",
    f"{C}collab-importer/src/zip_tool/sync_zip.rs",
    f"{C}collab-importer/src/zip_tool/util.rs",
]
RUST_DOC_PARSER = [
    f"{R}flowy-document/src/parse.rs",
    f"{R}flowy-document/src/parser/mod.rs",
    f"{R}flowy-document/src/parser/document_data_parser.rs",
    f"{R}flowy-document/src/parser/parser_entities.rs",
    f"{R}flowy-document/src/parser/constant.rs",
    f"{R}flowy-document/src/parser/utils.rs",
]
MIGRATION = [
    f"{A}plugins/document/presentation/editor_plugins/migration/editor_migration.dart",
    f"{A}plugins/document/application/document_data_pb_extension.dart",
]
PUBLISH_UI = [
    f"{A}plugins/shared/share/publish_tab.dart",
    f"{A}plugins/shared/share/publish_name_generator.dart",
    f"{A}plugins/shared/share/publish_color_extension.dart",
    f"{A}workspace/presentation/settings/pages/sites/domain/domain_settings_dialog.dart",
    f"{A}features/share_tab/data/repositories/local_share_with_user_repository_impl.dart",
    f"{R}flowy-server/src/af_cloud/impls/folder.rs",
]
OTHER_FORMATS = [
    f"{E}plugins/pdf/html_to_pdf_encoder.dart",
    f"{E}plugins/pdf/extension/color_ext.dart",
    f"{E}plugins/quill_delta/quill_delta_encoder.dart",
    f"{E}plugins/word_count/word_counter_service.dart",
    f"{E}plugins/plugins.dart",
]

PLAN: list[tuple[str, str, str, list[str]]] = [
    ("B4.0", "00-indice-motor-export-import", "Motor de exportación, importación y publicación",
     []),
    ("B4.1", "01-markdown-export", "Export Markdown",
     MARKDOWN_ENGINE + DOC_EXPORT_UI),
    ("B4.2", "02-html-export", "Export HTML",
     HTML_ENGINE + DOC_EXPORT_UI),
    ("B4.3", "03-texto-plano-export", "Export texto plano",
     MARKDOWN_ENGINE + [f"{A}workspace/application/export/document_exporter.dart",
                       f"{R}flowy-document/src/event_map.rs",
                       f"{R}flowy-document/src/event_handler.rs"]),
    ("B4.4", "04-json-documento-export", "Export JSON del documento",
     MARKDOWN_ENGINE + [
         f"{A}plugins/document/application/document_data_pb_extension.dart",
         f"{R}flowy-document/src/parser/document_data_parser.rs",
     ]),
    ("B4.5", "05-csv-database-export", "Export CSV de base de datos",
     CSV_ENGINE),
    ("B4.6", "06-raw-database-export", "Export raw database data",
     CSV_ENGINE),
    ("B4.7", "07-otros-formatos-export", "Otros formatos: PDF, quill delta y recuento de palabras",
     OTHER_FORMATS),
    ("B4.8", "08-import-markdown-texto", "Import Markdown y texto",
     IMPORT_UI + MARKDOWN_ENGINE + FOLDER_SHARE),
    ("B4.9", "09-import-csv", "Import CSV",
     IMPORT_UI + CSV_ENGINE + FOLDER_SHARE),
    ("B4.10", "10-import-historial-afdb", "Import de historial v0.x y de base de datos AF",
     IMPORT_UI + FOLDER_SHARE + MIGRATION),
    ("B4.11", "11-import-zip-notion", "Import ZIP y Notion",
     IMPORT_UI + FOLDER_SHARE + IMPORTER),
    ("B4.12", "12-publicacion-web", "Publicación web",
     PUBLISH_UI + FOLDER_SHARE),
    ("B4.13", "13-matriz-round-trip", "Matriz de round-trip y fidelidad",
     []),
]


def build(unit_id: str, doc_name: str, titulo: str, archivos: list[str]) -> dict:
    fuentes = sorted({a.split("/")[0] for a in archivos})
    return {
        "id": unit_id,
        "titulo": titulo,
        "feature_id": unit_id,
        "documento": f"OUT/10-motor-export-import/{doc_name}.md",
        "plantilla": "export",
        "archivos": archivos,
        "archivos_total": len(archivos),
        "fuentes": fuentes,
        "evidence_min_pct": 30,
        # El motor de export/import es 🔒 en el ROADMAP: el revisor eleva a 100 %.
        "gate_100": True,
        "nota": (
            "Unidad transversal: sus archivos ya pertenecen a features F* y "
            "están verificados en cobertura.csv. El bloque B4 no modifica el "
            "ledger; documenta el motor re-trazando esos mismos ficheros."
        ),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true", help="solo muestra el plan")
    ap.add_argument("--only", default=None, help="solo la unidad indicada")
    args = ap.parse_args(argv)

    if args.list:
        for uid, doc, tit, arch in PLAN:
            print(f"{uid:7} {len(arch):3} arch  {doc}")
        return 0

    OUT_DOCS.mkdir(parents=True, exist_ok=True)
    UNITS.mkdir(parents=True, exist_ok=True)
    written = 0
    for uid, doc, tit, arch in PLAN:
        if args.only and uid != args.only:
            continue
        unit = build(uid, doc, tit, arch)
        (UNITS / f"{uid}.json").write_text(
            json.dumps(unit, ensure_ascii=False, indent=2) + "\n"
        )
        written += 1
    print(f"[make_b4_units] {written} unidades escritas en {UNITS}")
    total = sum(len(a) for _, _, _, a in PLAN)
    print(f"[make_b4_units] archivos referenciados: {total} "
          f"(transversales: comparten ficheros entre unidades)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())