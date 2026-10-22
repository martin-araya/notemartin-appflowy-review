#!/usr/bin/env python3
"""make_b5_units.py — crea las 14 unidades del Bloque B5 (secuencias globales
extremo a extremo) con la lista real de archivos cuya traza sustenta cada
secuencia.

Las unidades B5 usan el mismo esquema transversal que las del Bloque B4:
`archivos` es la lista de ficheros que el documento RE-PRESENTA (no una
partición del ledger) y no tocan `cobertura.csv`, porque esos ficheros ya
pertenecen a features F* y están verificados al 100 % desde el cierre de B3.

Las 14 unidades:
  - B5.0  índice del bloque (0 archivos; cross-cutting)
  - B5.1  arranque en frío (15 startup tasks + flutter entry + init_sdk)
  - B5.2  login local y cloud (UserBloc + flowy-user/auth)
  - B5.3  cambio de workspace (FolderManager + workspace blocs)
  - B5.4  crear/abrir/editar/cerrar documento (DocumentBloc + DocumentManager)
  - B5.5  edición concurrente y merge (yrs + EncodedCollab)
  - B5.6  database con filtro+orden+grupo (DatabaseEditor + Filter/Sort/Group)
  - B5.7  subir imagen (StorageManager + ChunkedByteUploader)
  - B5.8  búsqueda (SearchManager + TantivyState)
  - B5.9  chat con streaming (AIManager + Chat)
  - B5.10 export Markdown (DocumentExporter + MarkdownDocumentEncoder)
  - B5.11 import CSV/ZIP (folder::share::import + DatabaseView::import_csv)
  - B5.12 publish (publish_util.rs)
  - B5.13 pérdida y recuperación de red (NetworkStatus + connect_state)

Uso:
  python3 make_b5_units.py              # crea/actualiza las 14
  python3 make_b5_units.py --list       # solo lista el plan
  python3 make_b5_units.py --only B5.4  # solo una unidad
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
UNITS = PROJECT_ROOT / "OUT" / "_ledger" / "units"
OUT_DOCS = PROJECT_ROOT / "OUT" / "15-secuencias-globales"

A = "appflowy/frontend/appflowy_flutter/lib/"
R = "appflowy/frontend/rust-lib/"
E = "editor/lib/src/"
C = "collab/"
TEST = "appflowy/frontend/appflowy_flutter/test/"

# --- Bloques reutilizables ---------------------------------------------------
STARTUP = [
    f"{A}startup/startup.dart",
    f"{A}startup/entry_point.dart",
    f"{A}startup/launch_configuration.dart",
    f"{A}startup/deps_resolver.dart",
    f"{A}startup/tasks/platform_error_catcher.dart",
    f"{A}startup/tasks/memory_leak_detector.dart",
    f"{A}startup/tasks/debug_task.dart",
    f"{A}startup/tasks/feature_flag_task.dart",
    f"{A}startup/tasks/localization.dart",
    f"{A}startup/tasks/windows.dart",
    f"{A}startup/tasks/rust_sdk.dart",
    f"{A}startup/tasks/load_plugin.dart",
    f"{A}startup/tasks/file_storage_task.dart",
    f"{A}startup/tasks/device_info_task.dart",
    f"{A}startup/tasks/auto_update_task.dart",
    f"{A}startup/tasks/hot_key.dart",
    f"{A}startup/tasks/appflowy_cloud_task.dart",
    f"{A}startup/tasks/app_widget.dart",
    f"{A}startup/tasks/platform_service.dart",
    f"{A}startup/tasks/recent_service_task.dart",
    f"{A}main.dart",
]

FFI_BRIDGE = [
    f"{R}dart-ffi/src/lib.rs",
    f"{A}packages/appflowy_backend/lib/rust_stream.dart",
    f"{R}lib-dispatch/src/dispatcher.rs",
    f"{R}lib-dispatch/src/module.rs",
    f"{R}flowy-core/src/lib.rs",
]

USER_AUTH = [
    f"{A}user/application/sign_in_bloc.dart",
    f"{A}user/application/sign_up_bloc.dart",
    f"{A}user/application/auth/auth_service.dart",
    f"{A}user/application/user_auth_listener.dart",
    f"{R}flowy-user/src/user_manager/manager.rs",
    f"{R}flowy-user/src/event_handler.rs",
    f"{R}flowy-user/src/event_map.rs",
    f"{R}flowy-user/src/notification.rs",
]

WORKSPACE_OPS = [
    f"{A}workspace/application/workspace/workspace_bloc.dart",
    f"{A}workspace/application/workspace/workspace_event.dart",
    f"{A}workspace/application/user/user_workspace_bloc.dart",
    f"{A}workspace/application/app/app_bloc.dart",
    f"{R}flowy-folder/src/manager.rs",
    f"{R}flowy-folder/src/event_handler.rs",
    f"{R}flowy-folder/src/event_map.rs",
    f"{R}flowy-folder/src/notification.rs",
]

DOC_LIFECYCLE = [
    f"{A}plugins/document/application/document_bloc.dart",
    f"{A}plugins/document/application/document_service.dart",
    f"{A}plugins/document/application/document_collab_adapter.dart",
    f"{A}plugins/document/application/doc_sync_state_listener.dart",
    f"{R}flowy-document/src/manager.rs",
    f"{R}flowy-document/src/event_handler.rs",
    f"{R}flowy-document/src/event_map.rs",
    f"{R}flowy-document/src/notification.rs",
    f"{R}flowy-document/src/document.rs",
]

CRDT_ENGINE = [
    f"{R}collab-integrate/src/collab_builder.rs",
    f"{R}collab-integrate/src/plugin_provider.rs",
    f"{C}collab/src/lib.rs",
    f"{C}collab-entity/src/lib.rs",
    f"{C}collab-document/src/document.rs",
    f"{C}collab-folder/src/folder.rs",
    f"{C}collab-database/src/database.rs",
]

DB_OPERATIONS = [
    f"{A}plugins/database/application/database_controller.dart",
    f"{A}plugins/database/application/grid/grid_bloc.dart",
    f"{A}plugins/database/application/filter/filter_editor_bloc.dart",
    f"{R}flowy-database2/src/manager.rs",
    f"{R}flowy-database2/src/services/database/database_editor.rs",
    f"{R}flowy-database2/src/services/filter/controller.rs",
    f"{R}flowy-database2/src/services/sort/controller.rs",
    f"{R}flowy-database2/src/services/group/controller.rs",
    f"{R}flowy-database2/src/services/database_view/view_filter.rs",
    f"{R}flowy-database2/src/services/database_view/view_sort.rs",
    f"{R}flowy-database2/src/services/database_view/view_group.rs",
    f"{R}flowy-database2/src/event_handler.rs",
    f"{R}flowy-database2/src/event_map.rs",
]

STORAGE_PIPELINE = [
    f"{A}plugins/document/presentation/editor_plugins/image/image_upload.dart",
    f"{A}plugins/document/presentation/editor_plugins/image/image_util.dart",
    f"{R}flowy-storage/src/manager.rs",
    f"{R}flowy-storage/src/uploader.rs",
    f"{R}flowy-storage/src/file_cache.rs",
    f"{R}flowy-storage/src/event_handler.rs",
    f"{R}flowy-storage/src/event_map.rs",
    f"{R}flowy-storage-pub/src/chunked_byte.rs",
    f"{R}flowy-storage-pub/src/storage.rs",
    f"{R}flowy-storage-pub/src/cloud.rs",
]

SEARCH_ENGINE = [
    f"{A}workspace/application/command_palette/command_palette_bloc.dart",
    f"{A}workspace/application/command_palette/search_menu_bloc.dart",
    f"{A}workspace/application/command_palette/command_palette_service.dart",
    f"{R}flowy-search/src/manager.rs",
    f"{R}flowy-search/src/tantivy_state.rs",
    f"{R}flowy-search/src/handler.rs",
    f"{R}flowy-search/src/event_handler.rs",
    f"{R}flowy-search/src/event_map.rs",
]

AI_CHAT = [
    f"{A}plugins/ai_chat/application/chat_bloc.dart",
    f"{A}plugins/ai_chat/application/chat_edit_document_bloc.dart",
    f"{A}plugins/ai_chat/application/chat_message.dart",
    f"{A}plugins/ai_chat/application/chat_input_bloc.dart",
    f"{R}flowy-ai/src/ai_manager.rs",
    f"{R}flowy-ai/src/chat.rs",
    f"{R}flowy-ai/src/completion.rs",
    f"{R}flowy-ai/src/event_handler.rs",
    f"{R}flowy-ai/src/event_map.rs",
]

EXPORT_MD = [
    f"{A}workspace/application/export/document_exporter.dart",
    f"{A}plugins/shared/share/export_tab.dart",
    f"{A}shared/markdown_to_document.dart",
    f"{E}plugins/markdown/document_markdown.dart",
    f"{E}plugins/markdown/document_markdown_parsers.dart",
]

IMPORT_CSV = [
    f"{A}workspace/presentation/home/menu/sidebar/import/import_panel.dart",
    f"{A}workspace/application/settings/share/import_service.dart",
    f"{R}flowy-database2/src/services/share/csv/import.rs",
    f"{R}flowy-database2/src/services/share/csv/mod.rs",
    f"{R}flowy-folder/src/share/import.rs",
    f"{C}collab-importer/src/lib.rs",
    f"{C}collab-importer/src/zip_tool/mod.rs",
    f"{C}collab-importer/src/notion/mod.rs",
]

PUBLISH_PIPE = [
    f"{A}plugins/shared/share/publish_tab.dart",
    f"{A}plugins/shared/share/publish_name_generator.dart",
    f"{A}workspace/presentation/settings/pages/sites/domain/domain_settings_dialog.dart",
    f"{R}flowy-folder/src/publish_util.rs",
    f"{R}flowy-folder/src/event_handler.rs",
    f"{R}flowy-folder/src/event_map.rs",
]

NETWORK_RECOVERY = [
    f"{A}core/network_monitor.dart",
    f"{A}plugins/document/application/document_sync_bloc.dart",
    f"{A}plugins/document/application/doc_sync_state_listener.dart",
    f"{R}flowy-core/src/server_layer.rs",
    f"{R}flowy-server/src/af_cloud/mod.rs",
    f"{C}collab-plugins/src/cloud_storage/sync_state.rs",
    f"{C}collab-plugins/src/cloud_storage/connect_state.rs",
]

# --- Plan --------------------------------------------------------------------
PLAN: list[tuple[str, str, str, list[str]]] = [
    ("B5.0", "00-indice-secuencias-globales", "Secuencias globales extremo a extremo",
     []),
    ("B5.1", "01-arranque-en-frio", "Arranque en frío",
     STARTUP + FFI_BRIDGE),
    ("B5.2", "02-login-local-y-cloud", "Login local y cloud",
     USER_AUTH + FFI_BRIDGE),
    ("B5.3", "03-cambio-de-workspace", "Cambio de workspace",
     WORKSPACE_OPS + FFI_BRIDGE),
    ("B5.4", "04-crear-abrir-editar-cerrar-documento", "Crear/abrir/editar/cerrar documento",
     DOC_LIFECYCLE + CRDT_ENGINE + FFI_BRIDGE),
    ("B5.5", "05-edicion-concurrente-y-merge", "Edición concurrente y merge",
     CRDT_ENGINE + DOC_LIFECYCLE),
    ("B5.6", "06-database-filtro-orden-grupo", "Abrir database y aplicar filtro+orden+grupo",
     DB_OPERATIONS),
    ("B5.7", "07-subir-imagen", "Subir imagen",
     STORAGE_PIPELINE),
    ("B5.8", "08-busqueda", "Búsqueda",
     SEARCH_ENGINE),
    ("B5.9", "09-chat-con-streaming", "Chat con streaming",
     AI_CHAT + FFI_BRIDGE),
    ("B5.10", "10-export-markdown", "Export (Markdown)",
     EXPORT_MD),
    ("B5.11", "11-import-csv-zip", "Import (CSV/ZIP/Notion)",
     IMPORT_CSV),
    ("B5.12", "12-publish", "Publicación web",
     PUBLISH_PIPE + FFI_BRIDGE),
    ("B5.13", "13-perdida-y-recuperacion-de-red", "Pérdida y recuperación de red",
     NETWORK_RECOVERY),
]


def build(unit_id: str, doc_name: str, titulo: str, archivos: list[str]) -> dict:
    fuentes = sorted({a.split("/")[0] for a in archivos})
    return {
        "id": unit_id,
        "titulo": titulo,
        "feature_id": unit_id,
        "documento": f"OUT/15-secuencias-globales/{doc_name}.md",
        "plantilla": "feature",
        "archivos": archivos,
        "archivos_total": len(archivos),
        "fuentes": fuentes,
        "evidence_min_pct": 95,
        "gate_100": False,
        "transversal": True,
        "secuencia": True,
        "nota": (
            "Secuencia global extremo a extremo: transversal, no ancla "
            "archivos a cobertura.csv. Sus archivos ya pertenecen a "
            "features F* y están verificados al 100 % desde el cierre de "
            "B3; B5 los re-presenta como recorrido con sequenceDiagram."
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
    print(f"B5: {written} unidades escritas en {UNITS}")
    print(f"B5: directorio de salida creado en {OUT_DOCS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
