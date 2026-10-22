#!/usr/bin/env python3
"""build_units.py — Genera OUT/_ledger/units/<id>.json a partir de
OUT/_ledger/cobertura.csv (post-A4.1). Cada unidad lista los archivos
a documentar, los catalogos extractores que aplican, sus dependencias
y la ruta del documento de salida. Las features grandes (> max_files,
default 120) se dividen en sub-unidades siguiendo ROADMAP.md B3.

Fase A4.2 de la skill notemartin-appflowy-review.
Ver AGENTS.md §8 y ROADMAP.md linea 99.

Uso:
  build_units.py [--ledger PATH] [--extract-dir PATH]
                 [--out-dir PATH] [--index-out PATH]
                 [--max-files N] [--include LIST] [--no-split]
                 [--quiet] [--no-color] [--json]
                 [--help]

Crea ademas OUT/_ledger/units/_index.json con la lista resumida.
"""
from __future__ import annotations

import argparse
import csv
import fnmatch
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

# ---------- rutas y constantes --------------------------------------------

SCRIPT_PATH = Path(__file__).resolve()
SKILL_ROOT = SCRIPT_PATH.parent.parent.parent
LEDGER_DEFAULT = SKILL_ROOT / "OUT" / "_ledger" / "cobertura.csv"
EXTRACT_DEFAULT = SKILL_ROOT / "OUT" / "_ledger" / "extract"
UNITS_DEFAULT = SKILL_ROOT / "OUT" / "_ledger" / "units"
INDEX_DEFAULT = UNITS_DEFAULT / "_index.json"
MAX_FILES_DEFAULT = 120

HEADER_LEDGER = (
    "fuente",
    "ruta",
    "capa",
    "feature_ids",
    "documento",
    "estado",
    "verificado_por",
)

CATALOG_NAMES = (
    "events.json",
    "protobuf.json",
    "notifications.json",
    "blocs.json",
    "deps.json",
    "misc.json",
)

# ANSI
_RED = "\033[31m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_RESET = "\033[0m"


# ---------- sub-divisiones pre-declaradas --------------------------------
#
# Cada entrada: feature_id -> lista de (sub_id, titulo, matcher_callable)
# matcher_callable(ruta) -> bool indica si la ruta cae en esta sub-unidad.
# El orden importa: la primera coincidencia gana. La ultima entrada se
# trata como "resto" (cualquier archivo que no haya matcheado).
#
# Convencion de matchers: si la ruta empieza por la cadena canónica
# expandida con la fuente (la misma forma que usa assign_ledger.py).

def _exact(prefix: str):
    def m(ruta: str) -> bool:
        return ruta.startswith(prefix)
    return m


def _any(*prefixes: str):
    def m(ruta: str) -> bool:
        return any(ruta.startswith(p) for p in prefixes)
    return m


def _all(*prefixes: str):
    """True si TODOS los prefijos aparecen en la ruta (orden cualquiera)."""
    def m(ruta: str) -> bool:
        return all(p in ruta for p in prefixes)
    return m


def _by_capa(capas: tuple[str, ...]):
    """Filtro por capa — aplicado tras leer el inventario o por la
    columna 'capa' del cobertura.csv."""
    def m(ruta: str, capa: str = "") -> bool:
        return capa in capas
    return m


# F00 — Infraestructura compartida (1.529 archivos).
# Particion por afinidad estructural (capas y crates).
F00_SUBS: list[tuple[str, str, Any]] = [
    ("F00.0", "Indice: infraestructura compartida (FFI, dispatch, errores, build, paquetes, nativo, tests)", _exact("__F00_INDEX_SENTINEL__")),
    ("F00.1", "FFI y dispatcher (dart-ffi, lib-dispatch, lib-infra)", _any(
        "appflowy/frontend/rust-lib/dart-ffi/",
        "appflowy/frontend/rust-lib/lib-dispatch/",
        "appflowy/frontend/rust-lib/lib-infra/",
    )),
    ("F00.2", "Errores, SQLite, migraciones", _any(
        "appflowy/frontend/rust-lib/flowy-error/",
        "appflowy/frontend/rust-lib/flowy-sqlite/",
    )),
    ("F00.3", "Build, codegen, integration tests Rust", _any(
        "appflowy/frontend/rust-lib/build-tool/",
        "appflowy/frontend/rust-lib/event-integration-test/",
    )),
    ("F00.4", "collab-integrate y crates -pub (contratos)", _any(
        "appflowy/frontend/rust-lib/collab-integrate/",
        "appflowy/frontend/rust-lib/flowy-document-pub/",
        "appflowy/frontend/rust-lib/flowy-folder-pub/",
        "appflowy/frontend/rust-lib/flowy-user-pub/",
        "appflowy/frontend/rust-lib/flowy-database-pub/",
        "appflowy/frontend/rust-lib/flowy-ai-pub/",
        "appflowy/frontend/rust-lib/flowy-search-pub/",
        "appflowy/frontend/rust-lib/flowy-storage-pub/",
        "appflowy/frontend/rust-lib/flowy-server-pub/",
    )),
    ("F00.5.1", "Paquetes Dart internos: appflowy_backend/lib (FFI, rust_stream, dispatch generado)", _exact(
        "appflowy/frontend/appflowy_flutter/packages/appflowy_backend/lib/"
    )),
    ("F00.5.1.2", "Paquetes Dart internos: appflowy_backend (example, nativo, test, config)", _any(
        "appflowy/frontend/appflowy_flutter/packages/appflowy_backend/example/",
        "appflowy/frontend/appflowy_flutter/packages/appflowy_backend/android/",
        "appflowy/frontend/appflowy_flutter/packages/appflowy_backend/ios/",
        "appflowy/frontend/appflowy_flutter/packages/appflowy_backend/linux/",
        "appflowy/frontend/appflowy_flutter/packages/appflowy_backend/macos/",
        "appflowy/frontend/appflowy_flutter/packages/appflowy_backend/windows/",
        "appflowy/frontend/appflowy_flutter/packages/appflowy_backend/web/",
        "appflowy/frontend/appflowy_flutter/packages/appflowy_backend/test/",
        "appflowy/frontend/appflowy_flutter/packages/appflowy_backend/.gitignore",
        "appflowy/frontend/appflowy_flutter/packages/appflowy_backend/.metadata",
        "appflowy/frontend/appflowy_flutter/packages/appflowy_backend/CHANGELOG.md",
        "appflowy/frontend/appflowy_flutter/packages/appflowy_backend/LICENSE",
        "appflowy/frontend/appflowy_flutter/packages/appflowy_backend/README.md",
        "appflowy/frontend/appflowy_flutter/packages/appflowy_backend/analysis_options.yaml",
        "appflowy/frontend/appflowy_flutter/packages/appflowy_backend/pubspec.yaml",
    )),
    ("F00.5.2", "Paquetes Dart internos: appflowy_popover", _exact(
        "appflowy/frontend/appflowy_flutter/packages/appflowy_popover/"
    )),
    ("F00.5.3", "Paquetes Dart internos: appflowy_result", _exact(
        "appflowy/frontend/appflowy_flutter/packages/appflowy_result/"
    )),
    ("F00.5.4", "Paquetes Dart internos: appflowy_ui", _exact(
        "appflowy/frontend/appflowy_flutter/packages/appflowy_ui/"
    )),
    ("F00.5.5", "Paquetes Dart internos: flowy_infra", _exact(
        "appflowy/frontend/appflowy_flutter/packages/flowy_infra/"
    )),
    ("F00.5.6", "Paquetes Dart internos: flowy_infra_ui/lib (widgets y estilos)", _exact(
        "appflowy/frontend/appflowy_flutter/packages/flowy_infra_ui/lib/"
    )),
    ("F00.5.6.2", "Paquetes Dart internos: flowy_infra_ui (nativo, web, platform interface, config)", _any(
        "appflowy/frontend/appflowy_flutter/packages/flowy_infra_ui/android/",
        "appflowy/frontend/appflowy_flutter/packages/flowy_infra_ui/ios/",
        "appflowy/frontend/appflowy_flutter/packages/flowy_infra_ui/linux/",
        "appflowy/frontend/appflowy_flutter/packages/flowy_infra_ui/macos/",
        "appflowy/frontend/appflowy_flutter/packages/flowy_infra_ui/windows/",
        "appflowy/frontend/appflowy_flutter/packages/flowy_infra_ui/web/",
        "appflowy/frontend/appflowy_flutter/packages/flowy_infra_ui/flowy_infra_ui_web/",
        "appflowy/frontend/appflowy_flutter/packages/flowy_infra_ui/flowy_infra_ui_platform_interface/",
        "appflowy/frontend/appflowy_flutter/packages/flowy_infra_ui/test/",
        "appflowy/frontend/appflowy_flutter/packages/flowy_infra_ui/.gitignore",
        "appflowy/frontend/appflowy_flutter/packages/flowy_infra_ui/.metadata",
        "appflowy/frontend/appflowy_flutter/packages/flowy_infra_ui/CHANGELOG.md",
        "appflowy/frontend/appflowy_flutter/packages/flowy_infra_ui/LICENSE",
        "appflowy/frontend/appflowy_flutter/packages/flowy_infra_ui/README.md",
        "appflowy/frontend/appflowy_flutter/packages/flowy_infra_ui/analysis_options.yaml",
        "appflowy/frontend/appflowy_flutter/packages/flowy_infra_ui/pubspec.yaml",
    )),
    ("F00.5.7", "Paquetes Dart internos: flowy_svg", _exact(
        "appflowy/frontend/appflowy_flutter/packages/flowy_svg/"
    )),
    ("F00.5.6.3", "Paquetes Dart internos: flowy_infra_ui/example (97 ficheros de ejemplo)", _exact(
        "appflowy/frontend/appflowy_flutter/packages/flowy_infra_ui/example/"
    )),
    ("F00.6", "Carcasas nativas (android, ios, linux, macos, windows, web)", _any(
        "appflowy/frontend/appflowy_flutter/android/",
        "appflowy/frontend/appflowy_flutter/ios/",
        "appflowy/frontend/appflowy_flutter/linux/",
        "appflowy/frontend/appflowy_flutter/macos/",
        "appflowy/frontend/appflowy_flutter/windows/",
        "appflowy/frontend/appflowy_flutter/web/",
    )),
("F00.7.0", "App glue: raiz del repo, CI, docs y ficheros de licencia", _any(
        "appflowy/.github/",
        "appflowy/install.sh",
        "appflowy/codemagic.yaml",
        "appflowy/commitlint.config.js",
        "appflowy/README.md",
        "appflowy/ROADMAP.md",
        "appflowy/CHANGELOG.md",
        "appflowy/doc/",
        "appflowy/.gitignore",
        "appflowy/.gitattributes",
        "appflowy/.dockerignore",
        "appflowy/.githooks/",
        "appflowy/LICENSE",
        "appflowy/CODE_OF_CONDUCT.md",
    )),
    ("F00.7.1", "App glue: scripts de build, packaging y resources/translations (36 bundles i18n)", _any(
        "appflowy/frontend/scripts/",
        "appflowy/frontend/resources/",
    )),
    ("F00.7.2", "App glue: raiz de frontend/ y de appflowy_flutter (config, assets, plantillas)", _any(
        "appflowy/frontend/Makefile.toml",
        "appflowy/frontend/rust-toolchain.toml",
        "appflowy/frontend/appflowy_flutter/assets/",
        "appflowy/frontend/appflowy_flutter/.gitignore",
        "appflowy/frontend/appflowy_flutter/.metadata",
        "appflowy/frontend/appflowy_flutter/Makefile",
        "appflowy/frontend/appflowy_flutter/README.md",
        "appflowy/frontend/appflowy_flutter/analysis_options.yaml",
        "appflowy/frontend/appflowy_flutter/pubspec.yaml",
        "appflowy/frontend/appflowy_flutter/build.yaml",
        "appflowy/frontend/appflowy_flutter/cargokit_options.yaml",
        "appflowy/frontend/appflowy_flutter/distribute_options.yaml",
        "appflowy/frontend/appflowy_flutter/devtools_options.yaml",
        "appflowy/frontend/appflowy_flutter/dart_dependency_validator.yaml",
        "appflowy/frontend/appflowy_flutter/dev.env",
        "appflowy/frontend/appflowy_flutter/dsa_pub.pem",
    )),
    ("F00.7.3", "App glue: integration_test runners y suites moviles/compartidas", _any(
        "appflowy/frontend/appflowy_flutter/integration_test/desktop_runner_",
        "appflowy/frontend/appflowy_flutter/integration_test/mobile",
        "appflowy/frontend/appflowy_flutter/integration_test/shared",
        "appflowy/frontend/appflowy_flutter/integration_test/runner.dart",
    )),
    ("F00.7.4", "App glue: integration_test/desktop/{document,cloud}", _any(
        "appflowy/frontend/appflowy_flutter/integration_test/desktop/document",
        "appflowy/frontend/appflowy_flutter/integration_test/desktop/cloud",
    )),
    ("F00.7.5", "App glue: integration_test/desktop resto (grid, board, sidebar, database, settings...)", _exact(
        "appflowy/frontend/appflowy_flutter/integration_test/desktop/"
    )),
    ("F00.7.6", "App glue: test/** (bloc_test, unit_test, widget_test)", _exact(
        "appflowy/frontend/appflowy_flutter/test/"
    )),
    ("F00.7.7", "App glue: lib/{core,startup,util,shared,workspace,features} y plugins transversales", _any(
        "appflowy/frontend/appflowy_flutter/lib/main.dart",
        "appflowy/frontend/appflowy_flutter/lib/startup/",
        "appflowy/frontend/appflowy_flutter/lib/core/",
        "appflowy/frontend/appflowy_flutter/lib/util/",
        "appflowy/frontend/appflowy_flutter/lib/env/",
        "appflowy/frontend/appflowy_flutter/lib/date/",
        "appflowy/frontend/appflowy_flutter/lib/flutter/",
        "appflowy/frontend/appflowy_flutter/lib/features/util/",
        "appflowy/frontend/appflowy_flutter/lib/features/workspace/",
        "appflowy/frontend/appflowy_flutter/lib/workspace/",
        "appflowy/frontend/appflowy_flutter/lib/shared/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/database_document/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/emoji/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/inline_actions/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/blank/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/base/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/shared/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/util.dart",
    )),
    # Ultimo bucket: "resto" de rust-lib/ y raiz de collab/.
    ("F00.7.8", "App glue: restos de rust-lib/ y raiz de collab/", _any(
        "appflowy/frontend/rust-lib/",
        "collab/",
    )),
]

# F01 — Documentos y editor (710). Sub-features segun ROADMAP B3.F01.
F01_SUBS: list[tuple[str, str, Any]] = [
    ("F01.0", "Indice de documentos y editor (modelo, DocumentBloc, servicios)", _any(
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/application/document_bloc.dart",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/application/document_service.dart",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/application/document_collab_adapter.dart",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/application/editor_transaction_adapter.dart",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/application/document_sync_bloc.dart",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/application/document_collaborators_bloc.dart",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/application/doc_sync_state_listener.dart",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/application/document_awareness_metadata.dart",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/application/document_diff.dart",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/application/document_rules.dart",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/application/document_validator.dart",
        "appflowy/frontend/appflowy_flutter/lib/shared/markdown_to_document.dart",
    )),
    ("F01.1", "Bloques de texto: heading, bulleted/numbered list, todo_list, quote, toggle, callout, header, delta", _any(
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/heading/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/bulleted_list/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/numbered_list/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/todo_list/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/quote/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/toggle/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/callout/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/header/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/delta/",
    )),
    ("F01.2", "Bloques ricos: code_block, math_equation, inline_math_equation, simple_table, table, columns, outline, page_block, sub_page", _any(
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/code_block/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/math_equation/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/inline_math_equation/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/simple_table/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/table/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/columns/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/outline/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/page_block/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/sub_page/",
    )),
    ("F01.3", "Media y archivos: image, video, file, cover, link_preview, link_embed", _any(
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/image/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/video/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/file/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/cover/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/link_preview/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/link_embed/",
    )),
    ("F01.4", "Menciones, inline actions, emoji", _any(
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/mention/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/inline_actions/",  # noqa: E501
        "appflowy/frontend/appflowy_flutter/lib/plugins/emoji/",
    )),
    ("F01.5", "Bases de datos embebidas en documentos", _any(
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/database/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/database_document/",
    )),
    ("F01.6", "Interaccion: slash_menu, block_menu, context_menu, actions, toolbars, shortcuts, find_and_replace, copy_and_paste", _any(
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/slash_menu/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/block_menu/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/context_menu/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/actions/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/desktop_toolbar/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/mobile_toolbar_v3/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/mobile_floating_toolbar/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/toolbar_item/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/align_toolbar_item/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/shortcuts/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/keyboard_interceptor/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/find_and_replace/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/copy_and_paste/",
    )),
    ("F01.7", "Estilo: font, background_color, page_style, i18n del editor", _any(
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/font/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/background_color/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/page_style/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/i18n/",
    )),
    ("F01.8", "Infraestructura del editor: transaction_handler, block_transaction_handler, migration, parsers, error, base, extensions, shared_context", _any(
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/transaction_handler/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/block_transaction_handler/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/migration/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/parsers/",
    )),
    ("F01.9", "IA en el editor", _exact(
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/ai/"
    )),
]

# F02 — Bases de datos (651). Sub-features segun ROADMAP B3.F02.
F02_SUBS: list[tuple[str, str, Any]] = [
    ("F02.0", "Indice: DatabaseController, manager, modelo collab-database, layouts, template", _any(
        "appflowy/frontend/appflowy_flutter/lib/plugins/database/application/database_controller.dart",
        "appflowy/frontend/appflowy_flutter/lib/plugins/database/application/database_view_cache.dart",
        "appflowy/frontend/appflowy_flutter/lib/plugins/database/application/defines.dart",
        # `manager.rs` y `template.rs` los reclama F02.13 (raiz de
        # flowy-database2). Si se dejaran aqui, el indice se apropiaba de dos
        # ficheros de contenido y F02 se quedaba en 99,7 %.
    )),
    ("F02.1", "Campos y tipos (services/field, application/field)", _any(
        "appflowy/frontend/appflowy_flutter/lib/plugins/database/application/field/",
        "appflowy/frontend/rust-lib/flowy-database2/src/services/field/",
    )),
    ("F02.2", "Celdas (services/cell, application/cell)", _any(
        "appflowy/frontend/appflowy_flutter/lib/plugins/database/application/cell/",
        "appflowy/frontend/rust-lib/flowy-database2/src/services/cell/",
    )),
    ("F02.3", "Filas y row detail (application/row), relaciones", _any(
        "appflowy/frontend/appflowy_flutter/lib/plugins/database/application/row/",
        "appflowy/frontend/rust-lib/flowy-database2/src/services/row/",
        "appflowy/frontend/rust-lib/flowy-database2/src/services/database/",
    )),
    ("F02.4", "Filtros (services/filter)", _exact(
        "appflowy/frontend/rust-lib/flowy-database2/src/services/filter/"
    )),
    ("F02.5", "Orden (services/sort)", _exact(
        "appflowy/frontend/rust-lib/flowy-database2/src/services/sort/"
    )),
    ("F02.6", "Agrupacion (services/group)", _exact(
        "appflowy/frontend/rust-lib/flowy-database2/src/services/group/"
    )),
    ("F02.7", "Calculos (services/calculations, application/calculations)", _any(
        "appflowy/frontend/appflowy_flutter/lib/plugins/database/application/calculations/",
        "appflowy/frontend/rust-lib/flowy-database2/src/services/calculations/",
    )),
    ("F02.8", "Field settings, settings de vista, database_view", _any(
        "appflowy/frontend/appflowy_flutter/lib/plugins/database/application/setting/",
        "appflowy/frontend/rust-lib/flowy-database2/src/services/field_settings/",
        "appflowy/frontend/rust-lib/flowy-database2/src/services/database_view/",
        "appflowy/frontend/rust-lib/flowy-database2/src/services/share/",
    )),
    ("F02.13", "Cierre F02: raiz de flowy-database2 (event_map, event_handler, manager, notification, lib) + services/mod + utils", _any(
        "appflowy/frontend/rust-lib/flowy-database2/Cargo.toml",
        "appflowy/frontend/rust-lib/flowy-database2/Flowy.toml",
        "appflowy/frontend/rust-lib/flowy-database2/build.rs",
        "appflowy/frontend/rust-lib/flowy-database2/src/lib.rs",
        "appflowy/frontend/rust-lib/flowy-database2/src/event_map.rs",
        "appflowy/frontend/rust-lib/flowy-database2/src/event_handler.rs",
        "appflowy/frontend/rust-lib/flowy-database2/src/manager.rs",
        "appflowy/frontend/rust-lib/flowy-database2/src/notification.rs",
        "appflowy/frontend/rust-lib/flowy-database2/src/template.rs",
        "appflowy/frontend/rust-lib/flowy-database2/src/services/mod.rs",
        "appflowy/frontend/rust-lib/flowy-database2/src/services/setting/",
        "appflowy/frontend/rust-lib/flowy-database2/src/utils/",
    )),
    ("F02.14", "Cierre F02: entidades protobuf y changesets de flowy-database2/src/entities", _exact(
        "appflowy/frontend/rust-lib/flowy-database2/src/entities/"
    )),
    ("F02.15", "Cierre F02: bateria de tests de flowy-database2/tests/database", _exact(
        "appflowy/frontend/rust-lib/flowy-database2/tests/"
    )),
    ("F02.9", "Grid (plugins/database/grid)", _exact(
        "appflowy/frontend/appflowy_flutter/lib/plugins/database/grid/"
    )),
    ("F02.10", "Board (plugins/database/board)", _exact(
        "appflowy/frontend/appflowy_flutter/lib/plugins/database/board/"
    )),
    ("F02.11", "Calendar (plugins/database/calendar)", _exact(
        "appflowy/frontend/appflowy_flutter/lib/plugins/database/calendar/"
    )),
    ("F02.12", "Tab bar de vistas, sync de database, snapshots", _any(
        "appflowy/frontend/appflowy_flutter/lib/plugins/database/tab_bar/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/database/application/sync/",
        "appflowy/frontend/rust-lib/flowy-database2/src/services/snapshot/",
        "appflowy/frontend/rust-lib/flowy-database2/src/services/sync/",
    )),
]

# F19 — Editor tests/ejemplos (354).
F19_SUBS: list[tuple[str, str, Any]] = [
    ("F19.0", "Indice: tests, ejemplos, l10n y configuracion del editor", _exact("__F19_INDEX_SENTINEL__")),
    ("F19.1", "Tests del editor: test/new", _exact("editor/test/new/")),
    ("F19.2", "Tests del editor: test/{plugins,editor,core,service,extensions,infra,render,legacy,customer,mobile}", _any(
        "editor/test/plugins/",
        "editor/test/editor/",
        "editor/test/core/",
        "editor/test/service/",
        "editor/test/extensions/",
        "editor/test/infra/",
        "editor/test/render/",
        "editor/test/legacy/",
        "editor/test/customer/",
        "editor/test/mobile/",
    )),
    ("F19.3", "Ejemplos del editor (example/*)", _exact("editor/example/")),
    ("F19.4", "Editor: lib/l10n + lib/ raiz", _any(
        "editor/lib/l10n/",
        "editor/lib/",
    )),
    ("F19.5", "Editor: configuracion (pubspec.*, .github, CHANGELOG, LICENSE, documentation) + raiz de test/", _any(
        "editor/pubspec.yaml",
        "editor/pubspec.lock",
        "editor/analysis_options.yaml",
        "editor/README.md",
        "editor/.github/",
        "editor/CHANGELOG.md",
        "editor/LICENSE",
        "editor/documentation/",
        "editor/codecov.yml",
        "editor/.gitignore",
        # Andamiaje compartido de la bateria de tests del editor.
        "editor/test/editor_state_test.dart",
        "editor/test/test_helper.dart",
        "editor/test/l10n",
    )),
]

# F16 — Mobile (184). Corte por capa de `lib/mobile/` y por area funcional de
# `presentation/`: la sub-unidad F16.1.2 original son 178 archivos (4x el
# umbral de AGENTS.md §8) y se divide en tres.
_MOB = "appflowy/frontend/appflowy_flutter/lib/mobile/presentation/"

F16_SUBS: list[tuple[str, str, Any]] = [
    ("F16.0", "Indice: Mobile (shell de la app, editor movil y capas de presentacion)", _exact("__F16_INDEX_SENTINEL__")),
    ("F16.1.1", "Mobile: lib/mobile/application (router y blocs base)", _exact(
        "appflowy/frontend/appflowy_flutter/lib/mobile/application/"
    )),
    ("F16.1.2.1", "Mobile presentation: shell, ajustes, home, favoritos y widgets", _any(
        _MOB + "setting/",
        _MOB + "home/",
        _MOB + "favorite/",
        _MOB + "page_item/",
        _MOB + "bottom_sheet/",
        _MOB + "widgets/",
        _MOB + "presentation.dart",
        _MOB + "root_placeholder_page.dart",
        _MOB + "mobile_bottom_navigation_bar.dart",
    )),
    ("F16.1.2.2", "Mobile presentation: documento, editor, selection menu e inline actions", _any(
        _MOB + "document/",
        _MOB + "editor/",
        _MOB + "selection_menu/",
        _MOB + "inline_actions/",
    )),
    ("F16.1.2.3", "Mobile presentation: database, chat, busqueda, notificaciones y base", _any(
        _MOB + "database/",
        _MOB + "chat/",
        _MOB + "search/",
        _MOB + "notifications/",
        _MOB + "base/",
    )),
    ("F16.2", "Mobile: editor_plugins/mobile_*", _any(
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/mobile_toolbar_v3/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/mobile_floating_toolbar/",
    )),
]

# F09 — IA (166).
F09_SUBS: list[tuple[str, str, Any]] = [
    ("F09.0", "Indice: IA (chat, completion, IA local, MCP, embeddings, middleware)", _exact("__F09_INDEX_SENTINEL__")),
    ("F09.1", "IA: flowy-ai (Rust)", _exact(
        "appflowy/frontend/rust-lib/flowy-ai/"
    )),
    ("F09.2", "IA: flowy-sqlite-vec (vectores)", _exact(
        "appflowy/frontend/rust-lib/flowy-sqlite-vec/"
    )),
    ("F09.3", "IA: appflowy_flutter/lib/ai + plugins/ai_chat (Dart)", _any(
        "appflowy/frontend/appflowy_flutter/lib/ai/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/ai_chat/",
    )),
    ("F09.4", "IA: editor_plugins/ai", _exact(
        "appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/ai/"
    )),
]

# F03 — Folder, workspaces, vistas (116). Corte por lenguaje/fuente.
# F03.0 es el indice (0 archivos): el sentinel no casa con ninguna ruta y todo
# lo demas ya casa con F03.1..F03.3, asi que `resto` queda vacio.
F03_SUBS: list[tuple[str, str, Any]] = [
    ("F03.0", "Indice: Folder, workspaces, espacios, vistas, view_management", _exact("__F03_INDEX_SENTINEL__")),
    ("F03.1", "Vistas, workspaces y sidebar (Dart: workspace/application + presentation)", _any(
        "appflowy/frontend/appflowy_flutter/lib/workspace/application/",
        "appflowy/frontend/appflowy_flutter/lib/workspace/presentation/",
    )),
    ("F03.2", "flowy-folder (Rust): FolderEvent, handlers, FolderManager, entidades View/Workspace/Trash", _any(
        "appflowy/frontend/rust-lib/flowy-folder/",
    )),
    ("F03.3", "collab-folder: Folder, View, Workspace, jerarquia, secciones, relaciones", _any(
        "collab/collab-folder/",
    )),
]

# F05 — Usuario/auth (126).
F05_SUBS: list[tuple[str, str, Any]] = [
    ("F05.0", "Indice: usuario, auth (local/cloud/third-party), sesion, miembros, roles, migraciones", _exact("__F05_INDEX_SENTINEL__")),
    ("F05.1", "Usuario: appflowy_flutter/lib/user (Dart)", _any(
        "appflowy/frontend/appflowy_flutter/lib/user/",
        # B0.2 asigno a F05 el bloque `workspace/application/user/` y dos
        # ficheros sueltos de estado de usuario; sin ellos caerian como "resto"
        # en F05.0 y el indice dejaria de ser un indice de 0 archivos.
        "appflowy/frontend/appflowy_flutter/lib/workspace/application/user/",
        "appflowy/frontend/appflowy_flutter/lib/workspace/application/appearance_defaults.dart",
        "appflowy/frontend/appflowy_flutter/lib/workspace/application/subscription_success_listenable/",
    )),
    ("F05.2", "Usuario: flowy-user + collab-user (Rust + Collab)", _any(
        "appflowy/frontend/rust-lib/flowy-user/",
        "collab/collab-user/",
    )),
]

# F12 — Compartir / publicar / shared section (72). Corte por dominio.
F12_SUBS: list[tuple[str, str, Any]] = [
    ("F12.1", "Compartir: share_tab, niveles de acceso y plugins/shared/share", _any(
        "appflowy/frontend/appflowy_flutter/lib/features/share_tab/",
        "appflowy/frontend/appflowy_flutter/lib/features/page_access_level/",
        "appflowy/frontend/appflowy_flutter/lib/plugins/shared/share/",
    )),
    ("F12.2", "Shared section, sitios publicados y publish_util/import en Rust", _any(
        "appflowy/frontend/appflowy_flutter/lib/features/shared_section/",
        "appflowy/frontend/appflowy_flutter/lib/workspace/presentation/settings/pages/sites/",
        "appflowy/frontend/rust-lib/flowy-folder/src/publish_util.rs",
        "appflowy/frontend/rust-lib/flowy-folder/src/share/",
    )),
]

# F13 — Ajustes / apariencia / temas / fuentes (127). Corte por area.
_ST = "appflowy/frontend/appflowy_flutter/lib/workspace/"
F13_SUBS: list[tuple[str, str, Any]] = [
    ("F13.1", "Ajustes: logica de aplicacion + cuenta, billing, plan, nube y workspace", _any(
        _ST + "application/settings/",
        _ST + "presentation/settings/pages/about/",
        _ST + "presentation/settings/pages/account/",
        _ST + "presentation/settings/pages/settings_account_view.dart",
        _ST + "presentation/settings/pages/settings_billing_view.dart",
        _ST + "presentation/settings/pages/settings_plan_view.dart",
        _ST + "presentation/settings/pages/settings_plan_comparison_dialog.dart",
        _ST + "presentation/settings/pages/settings_workspace_view.dart",
        _ST + "presentation/settings/pages/fix_data_widget.dart",
    )),
    ("F13.2", "Apariencia, IA, miembros, feature flags y theme_upload", _any(
        _ST + "presentation/settings/pages/setting_ai_view/",
        _ST + "presentation/settings/pages/settings_manage_data_view.dart",
        _ST + "presentation/settings/pages/settings_shortcuts_view.dart",
        _ST + "presentation/settings/widgets/members/",
        _ST + "presentation/settings/widgets/theme_upload/",
        _ST + "presentation/settings/widgets/feature_flags/",
        _ST + "presentation/settings/widgets/files/",
        _ST + "presentation/settings/widgets/setting_appflowy_cloud.dart",
        _ST + "presentation/settings/widgets/setting_cloud.dart",
        _ST + "presentation/settings/widgets/setting_local_cloud.dart",
        _ST + "presentation/settings/widgets/setting_third_party_login.dart",
        _ST + "presentation/settings/widgets/settings_notifications_view.dart",
    )),
    ("F13.3", "Widgets compartidos de Ajustes, emoji picker y data layer de settings", _any(
        _ST + "presentation/settings/shared/",
        _ST + "presentation/settings/widgets/emoji_picker/",
        _ST + "presentation/settings/widgets/utils/",
        _ST + "presentation/settings/widgets/_restart_app_button.dart",
        _ST + "presentation/settings/widgets/cancel_plan_survey_dialog.dart",
        _ST + "presentation/settings/widgets/settings_menu.dart",
        _ST + "presentation/settings/widgets/settings_menu_element.dart",
        _ST + "presentation/settings/widgets/web_url_hint_widget.dart",
        _ST + "presentation/settings/settings_dialog.dart",
        "appflowy/frontend/appflowy_flutter/lib/features/settings/",
    )),
]

# F15 — Notificaciones in-app / recordatorios / flowy-date (53).
F15_SUBS: list[tuple[str, str, Any]] = [
    ("F15.1", "Notificaciones y recordatorios (Dart): listeners, panel, date picker", _any(
        "appflowy/frontend/appflowy_flutter/lib/core/notification/",
        "appflowy/frontend/appflowy_flutter/lib/workspace/application/notification/",
        "appflowy/frontend/appflowy_flutter/lib/workspace/presentation/notifications/",
        "appflowy/frontend/appflowy_flutter/lib/workspace/presentation/widgets/date_picker/",
    )),
    ("F15.2", "flowy-date, reminder.rs y flowy-notification (Rust)", _any(
        "appflowy/frontend/rust-lib/flowy-date/",
        "appflowy/frontend/rust-lib/flowy-document/src/reminder.rs",
        "appflowy/frontend/rust-lib/flowy-notification/",
    )),
]

# Features con sub-divisiones declaradas.
SUBDIVISIONS: dict[str, list[tuple[str, str, Any]]] = {
    "F00": F00_SUBS,
    "F01": F01_SUBS,
    "F02": F02_SUBS,
    "F03": F03_SUBS,
    "F05": F05_SUBS,
    "F09": F09_SUBS,
    "F12": F12_SUBS,
    "F13": F13_SUBS,
    "F15": F15_SUBS,
    "F16": F16_SUBS,
    "F19": F19_SUBS,
}

# Sub-unidades que se emiten siempre, tengan o no archivos.
# F16.2 cubre `editor_plugins/{mobile_toolbar_v3,mobile_floating_toolbar}`, que
# el triage de B0.2 asigno a F01.6.4 (ya verificado): el ROADMAP lo promete
# como parte de "B3.F16 — Mobile", asi que se materializa la unidad para poder
# dejar constancia por escrito de la correccion de scope.
ALWAYS_EMIT: set[str] = {"F16.2"}

# Titulos canonicos para features no divididas.
# La clave es el **slug** del directorio (`09-features/<id>-<slug>/`), asi que
# se limita a 80 caracteres para que coincida con `_slug()`. F00 y F21 estaban
# mal: F00 generaba un directorio de 80 caracteres que `_doc_path` recortaba de
# otra forma, y F21 no tinha entrada (quedaba como `F21-f21/`).
FEATURE_TITLES: dict[str, str] = {
    "F00": "Infraestructura compartida (FFI, dispatch, errores, build, nativo)",
    "F01": "Documentos y editor",
    "F02": "Bases de datos",
    "F03": "Folder, workspaces, vistas",
    "F04": "Sidebar, favoritos, recientes, papelera, tabs, command palette",
    "F05": "Usuario, auth, sesion",
    "F06": "Sync y servidores",
    "F07": "Almacenamiento de archivos",
    "F08": "Busqueda e indexacion",
    "F09": "IA",
    "F10": "Importacion (UI)",
    "F11": "Exportacion (UI)",
    "F12": "Compartir, publicar, niveles de acceso",
    "F13": "Ajustes, apariencia, temas, fuentes",
    "F14": "Internacionalizacion",
    "F15": "Notificaciones in-app y recordatorios",
    "F16": "Mobile",
    "F17": "Plataforma (ventanas, deeplinks, auto-update, hotkeys, feature flags, errores, logging)",
    "F18": "Motor Colab (CRDT, plugins, importer, entity, derive)",
    "F19": "Editor (tests, ejemplos, l10n, configuracion)",
    "F20": "Colab (raiz: configuracion, CI, docs, manifests)",
    # F21 lo creo el triage de B0.2 pero se quedo con `titulo: "F21"` (id
    # repetido) y con la ruta `F21-f21/F21-f21.md`. Sin esta entrada,
    # `_doc_path` cae en el feature_id y produce esa carpeta.
    "F21": "Icon/Emoji picker",
}

# Dependencias internas: feature -> set(feature_id_dependiente).
FEATURE_DEPS: dict[str, set[str]] = {
    "F08": {"F03"},   # busqueda usa vistas
    "F07": {"F01"},   # almacenamiento relacionado con documentos
}


# ---------- IO -------------------------------------------------------------


def load_ledger(path: Path) -> list[dict]:
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
        return list(reader)


def load_extracts(extract_dir: Path) -> dict[str, Any]:
    """Devuelve {nombre_archivo: contenido} de los catalogos disponibles.

    No se valida el esquema interno: el script solo necesita saber que
    existen y entrega la lista al subagente autor.
    """
    out: dict[str, Any] = {}
    if not extract_dir.is_dir():
        return out
    for p in sorted(extract_dir.iterdir()):
        if p.suffix == ".json" and p.is_file():
            try:
                out[p.name] = json.loads(p.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                print(f"WARN: {p.name} no es JSON valido: {e}", file=sys.stderr)
    return out


# ---------- distribucion y division ---------------------------------------


@dataclass
class FileRow:
    fuente: str
    ruta: str
    capa: str
    estado: str
    verificado_por: str = ""
    documento: str = ""


def distribute(rows: list[dict]) -> dict[str, list[FileRow]]:
    """Agrupa filas por feature_id (una fila -> una feature)."""
    out: dict[str, list[FileRow]] = defaultdict(list)
    for r in rows:
        fids = [f for f in r.get("feature_ids", "").split(";") if f]
        if not fids:
            continue
        # No tocamos verificados; ya se filtraron al asignar.
        if r.get("estado") == "verificado":
            continue
        primary = sorted(fids)[0]
        out[primary].append(FileRow(
            fuente=r["fuente"],
            ruta=r["ruta"],
            capa=r.get("capa", ""),
            estado=r.get("estado", "pendiente"),
            verificado_por=r.get("verificado_por", ""),
            documento=r.get("documento", ""),
        ))
    return out


def _classify(
    feature_id: str,
    files: list[FileRow],
    no_split: bool,
    max_files: int,
) -> tuple[list[tuple[str, str, list[FileRow]]], list[str]]:
    """Devuelve (lista_de_unidades, warnings).

    Cada elemento: (sub_id, titulo, files).

    Estrategia: si la feature tiene subdivision declarada, se usa en
    UNA sola pasada; lo que no case cae como "resto" en la primera
    sub-unidad (que es el indice). Las sub-unidades resultantes NO se
    vuelven a subdividir; si una queda > max_files, se emite warning
    y se conserva. Esto evita explosion combinatoria de IDs.
    """
    if feature_id not in SUBDIVISIONS or no_split:
        return (
            [(feature_id, FEATURE_TITLES.get(feature_id, feature_id), files)],
            [],
        )

    buckets: list[tuple[str, str, list[FileRow]]] = []
    used_ids: set[int] = set()
    for sub_id, titulo, matcher in SUBDIVISIONS[feature_id]:
        bucket: list[FileRow] = []
        for f in files:
            if id(f) in used_ids:
                continue
            if matcher(f.ruta):
                bucket.append(f)
                used_ids.add(id(f))
        # Solo emitir sub-unidades con archivos (o si es la primera /
        # indice, conservarla con "resto").
        buckets.append((sub_id, titulo, bucket))

    # Lo que no haya matcheado cae como "resto" en la primera sub-unidad
    # (que es el indice de la feature, por convencion de la tabla).
    resto = [f for f in files if id(f) not in used_ids]
    if resto and buckets:
        first_id, first_tit, first_files = buckets[0]
        buckets[0] = (first_id, first_tit, first_files + resto)
    elif resto:
        buckets.append((feature_id, FEATURE_TITLES.get(feature_id, feature_id), resto))

    # Eliminar sub-unidades vacias que no sean la primera (indice).
    # Si la primera queda vacia y no hay resto, igualmente se conserva
    # solo si representa el indice "modelo" de la feature.
    non_empty: list[tuple[str, str, list[FileRow]]] = []
    for i, (sub_id, titulo, fs) in enumerate(buckets):
        if fs or i == 0 and not non_empty:
            non_empty.append((sub_id, titulo, fs))
        elif fs:
            non_empty.append((sub_id, titulo, fs))
    # Si todo esta vacio, dejar al menos la primera con su titulo.
    if not any(fs for _, _, fs in non_empty) and buckets:
        sub_id, titulo, _ = buckets[0]
        non_empty = [(sub_id, titulo, [])]
    buckets = non_empty

    warnings: list[str] = []
    # Sub-unidades que deben emitirse aunque no tengan archivos. Se usan para
    # los cortes que hoy estan "vacios" pero que el ROADMAP exige documentar
    # como correccion de scope (F16.2 = editor_plugins/mobile_*, ya cubierto
    # por F01.6.4; F01.3 y F01.9HISTO全身).
    declarados = {sid for sid, _t, _m in SUBDIVISIONS.get(feature_id, [])}
    emitidos = {sid for sid, _t, _f in buckets}
    for sid in sorted(ALWAYS_EMIT & declarados - emitidos):
        titulo = next(t for s, t, _m in SUBDIVISIONS[feature_id] if s == sid)
        buckets.append((sid, titulo, []))
        warnings.append(f"{sid}: unidad de scope-correction emitida con 0 archivos")

    # Si una sub-unidad ya excede max_files tras el matching automatico,
    # partir por primer nivel de subdirectorio UNA sola vez (sin recursion).
    # Esto cubre tanto los "catch-all" (F00.5, F00.7) como las unidades
    # especificas grandes (F16.1, F19.2) y los indices con "resto".
    final: list[tuple[str, str, list[FileRow]]] = []
    for sub_id, titulo, fs in buckets:
        if len(fs) <= max_files:
            final.append((sub_id, titulo, fs))
            continue
        for sub2_id, sub2_tit, sub2_fs in _split_one_level(sub_id, titulo, fs, max_files):
            final.append((sub2_id, sub2_tit, sub2_fs))
    return final, warnings


def _split_recursive(
    base_id: str,
    base_titulo: str,
    files: list[FileRow],
    max_files: int,
    depth: int = 0,
) -> list[tuple[str, str, list[FileRow]]]:
    """Reparte `files` por el primer nivel de subdirectorio y vuelve a
    intentarlo sobre los grupos que sigan excediendo `max_files`.

    **No se usa en el pipeline por defecto** (`_classify` llama a
    `_split_one_level`): la recursion se probó y fragmentaba en exceso los
    paquetes Dart, cuyos `example/`, `android/` e `ios/` son casi todos
    ficheros de andamiaje y producian ~15 sub-unidades de 3-10 archivos para
    `appflowy_backend`. Las divisiones que si hacen falta estan declaradas
    explicitamente en SUBDIVISIONS (F00.5.1/.1.2, F00.5.6/.6.2, F16.1.2.x).
    Se conserva la funcion por si se quiere un `--max-depth` en el futuro."""
    if len(files) <= max_files or not files:
        return [(base_id, base_titulo, files)]

    parts = _split_one_level(base_id, base_titulo, files, max_files)
    if len(parts) <= 1 or depth >= 3:
        # No se pudo partir (todos los ficheros comparten el mismo padre).
        return parts

    out: list[tuple[str, str, list[FileRow]]] = []
    for sub_id, sub_tit, sub_files in parts:
        out.extend(_split_recursive(sub_id, sub_tit, sub_files, max_files, depth + 1))
    return out


def _split_one_level(
    base_id: str,
    base_titulo: str,
    files: list[FileRow],
    max_files: int,
) -> list[tuple[str, str, list[FileRow]]]:
    """Parte `files` por el primer nivel de subdirectorio en UNA sola
    pasada. No recursivo. Cada grupo se conserva tal cual aunque supere
    max_files (eso se reporta como warning)."""
    if len(files) <= max_files or not files:
        return [(base_id, base_titulo, files)]

    common = files[0].ruta
    for f in files[1:]:
        while not f.ruta.startswith(common) and common:
            common = common[:-1]

    def _next_seg(ruta: str) -> str:
        rest = ruta[len(common):].lstrip("/")
        return rest.split("/", 1)[0] if rest else "(root)"

    groups: dict[str, list[FileRow]] = defaultdict(list)
    for f in files:
        groups[_next_seg(f.ruta)].append(f)

    out: list[tuple[str, str, list[FileRow]]] = []
    for idx, seg in enumerate(sorted(groups), start=1):
        sub_id = f"{base_id}.{idx}"
        sub_tit = f"{base_titulo} — {seg}"
        out.append((sub_id, sub_tit, groups[seg]))
    return out


# ---------- generacion de unidades ----------------------------------------


def _doc_path(unit_id: str, titulo: str) -> str:
    """Mapea unit_id a la ruta del documento Markdown esperado.

    Convencion:
      Fxx         -> 09-features/Fxx-<slug>/<id>-<slug>.md
      Fxx.y       -> 09-features/Fxx-<slug>/<xx.y>-<slug>.md
      Fxx.y.z     -> 09-features/Fxx-<slug>/<xx.y.z>-<slug>.md
    """
    parts = unit_id.split(".")
    feature_id = parts[0]
    sub = ".".join(parts[1:]) if len(parts) > 1 else ""
    feature_slug = _slug(FEATURE_TITLES.get(feature_id, feature_id))
    if sub:
        return f"OUT/09-features/{feature_id}-{feature_slug}/{sub}-{_slug(titulo)}.md"
    return f"OUT/09-features/{feature_id}-{feature_slug}/{feature_id}-{feature_slug}.md"


_SLUG_RE = re.compile(r"[^a-z0-9]+")


def _slug(s: str) -> str:
    s = s.lower()
    s = _SLUG_RE.sub("-", s).strip("-")
    return s[:80]


def _prioridad(unit_id: str, feature_id: str, sub_count: int) -> int:
    if unit_id.endswith(".0") or "." not in unit_id and not FEATURE_DEPS.get(feature_id):
        return 1
    return 2


def _make_unit(
    unit_id: str,
    feature_id: str,
    titulo: str,
    files: list[FileRow],
    catalogs_present: list[str],
) -> dict:
    archivos = [
        {
            "fuente": f.fuente,
            "ruta": f.ruta,
            "capa": f.capa,
            "estado": f.estado,
        }
        for f in sorted(files, key=lambda x: (x.fuente, x.ruta))
    ]
    fuentes = sorted({f.fuente for f in files})
    capas: Counter = Counter(f.capa for f in files)
    sub_count = len(SUBDIVISIONS.get(feature_id, []))
    return {
        "schema_version": 1,
        "id": unit_id,
        "feature_id": feature_id,
        "sub_index": int(unit_id.split(".")[1]) if "." in unit_id else None,
        "titulo": titulo,
        "fuentes": fuentes,
        "archivos": archivos,
        "archivos_total": len(archivos),
        "catalogos": list(catalogs_present),
        "catalogos_razon": {
            "events.json": "Eventos FFI / dispatch de esta feature",
            "blocs.json": "BLoCs / Cubits presentes en los archivos de esta unidad",
            "protobuf.json": "Entidades protobuf input/output de los eventos",
            "notifications.json": "Notificaciones Rust→Dart emitidas o escuchadas",
            "deps.json": "Dependencias del workspace rust y pubspec",
            "misc.json": "Rutas, atajos, flags, error codes, i18n",
        },
        "dependencias": _unit_dependencies(unit_id, feature_id),
        "plantilla": "feature",
        "documento": _doc_path(unit_id, titulo),
        "metricas": {
            "archivos": len(archivos),
            "por_capa": dict(capas),
            "por_fuente": dict(Counter(f.fuente for f in files)),
        },
        "prioridad": _prioridad(unit_id, feature_id, sub_count),
        "concurrencia": "serial" if unit_id.endswith(".0") else "paralela",
        "generado_en": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def _unit_dependencies(unit_id: str, feature_id: str) -> list[dict]:
    deps: list[dict] = []
    # Indice de feature: cada sub-unidad depende del .0.
    if "." in unit_id:
        sub = unit_id.split(".")
        if sub[1] != "0":
            index_id = f"{feature_id}.0"
            deps.append({
                "id": index_id,
                "tipo": "indice",
                "nota": f"Documento indice {index_id} debe existir antes de esta sub-unidad.",
            })
    # Dependencias cross-feature.
    for d in sorted(FEATURE_DEPS.get(feature_id, set())):
        deps.append({
            "id": d,
            "tipo": "feature",
            "nota": f"Documento de {d} debe estar disponible (referencia).",
        })
    return deps


# ---------- escritura ------------------------------------------------------


def write_unit(out_dir: Path, unit: dict) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{unit['id']}.json"
    path.write_text(
        json.dumps(unit, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return path


def load_units_from_disk(out_dir: Path) -> list[dict]:
    """Lee TODOS los `*.json` de unidad del directorio (excepto `_index.json`).

    `build_units.py` solo regenera las features que procesa, pero las unidades
    ya cerradas (F01, F03..F07) siguen en disco y son necesarias para el
    invariante de `validate_units.py` (suma == filas asignadas). Por eso el
    indice se reconstruye desde el directorio completo y no solo desde las
    units recien generadas (si no, se perderian del indice)."""
    units: list[dict] = []
    for path in sorted(out_dir.glob("*.json")):
        if path.name == "_index.json":
            continue
        try:
            units.append(json.loads(path.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            continue
    return [u for u in units if u.get("id") and "archivos_total" in u]


def prune_stale_units(
    out_dir: Path,
    features: set[str],
    keep_ids: set[str],
    protected_paths: set[str] | None = None,
) -> tuple[list[str], list[str]]:
    """Borra las unidades de las features procesadas cuyo id ya no se genera.

    Sin esto, al cambiar `SUBDIVISIONS` quedan ficheros huerfanos (p. ej. los
    antiguos `F00.7.1`..`F00.7.14` tras pasar a un corte declarativo) que
    `validate_units.py` cuenta como doble propiedad.

    **Proteccion**: una unidad no se borra si contiene alguna ruta que en
    `cobertura.csv` ya no este en `pendiente` (p. ej. F02, que esta a medio
    cerrar: sus sub-unidades declaradas cubren filas ya verificadas y
    `build_units.py` no las regenera porque solo lee filas pendientes).
    Esas unidades se devuelven en `kept` para que el orquestador las revise."""
    protected_paths = protected_paths or set()
    stale: list[str] = []
    kept: list[str] = []
    for path in sorted(out_dir.glob("*.json")):
        if path.name == "_index.json":
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if data.get("feature_id") not in features:
            continue
        if data.get("id") in keep_ids:
            continue
        # Las unidades indice (0 archivos) son deliberadas: las crean los
        # sentinels `__F0X_INDEX_SENTINEL__` y materializan las dependencias
        # `tipo: indice` que declaran sus hermanas. Nunca se purgan.
        if not data.get("archivos"):
            kept.append(path.name)
            continue
        rutas = {a.get("ruta") for a in data.get("archivos", [])}
        if rutas & protected_paths:
            kept.append(path.name)
            continue
        stale.append(path.name)
    if stale:
        backup = out_dir / ".stale-bak"
        backup.mkdir(parents=True, exist_ok=True)
        for name in stale:
            (backup / name).write_bytes((out_dir / name).read_bytes())
            (out_dir / name).unlink()
    return stale, kept


def write_index(out_dir: Path, units: list[dict], features_vacias: list[str]) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    index = {
        "schema_version": 1,
        "generado_en": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_unidades": len(units),
        "archivos_total_global": sum(u["archivos_total"] for u in units),
        "units": [
            {
                "id": u["id"],
                "feature_id": u["feature_id"],
                "titulo": u["titulo"],
                "archivos_total": u["archivos_total"],
                "prioridad": u["prioridad"],
                "concurrencia": u["concurrencia"],
                "dependencias": [d["id"] for d in u["dependencias"]],
                "documento": u["documento"],
            }
            for u in sorted(units, key=lambda x: (x["prioridad"], x["id"]))
        ],
        "features_vacias": features_vacias,
    }
    path = out_dir / "_index.json"
    path.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


# ---------- CLI -----------------------------------------------------------


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Genera OUT/_ledger/units/<id>.json a partir de cobertura.csv "
            "con sub-unidades para features grandes."
        )
    )
    p.add_argument("--ledger", type=Path, default=LEDGER_DEFAULT)
    p.add_argument("--extract-dir", type=Path, default=EXTRACT_DEFAULT, dest="extract_dir")
    p.add_argument("--out-dir", type=Path, default=UNITS_DEFAULT, dest="out_dir")
    p.add_argument("--index-out", type=Path, default=INDEX_DEFAULT, dest="index_out")
    p.add_argument("--max-files", type=int, default=MAX_FILES_DEFAULT, dest="max_files")
    p.add_argument("--include", type=str, default="",
                   help="Solo procesar features en la lista separada por comas (p.ej. F01,F02).")
    p.add_argument("--no-split", action="store_true", dest="no_split")
    p.add_argument("--index-only", action="store_true", dest="index_only",
                   help="No regenera unidades: solo reconstruye _index.json "
                        "leyendo el directorio completo.")
    p.add_argument("--prune", action="store_true",
                   help="Borra (a .stale-bak/) las unidades de las features "
                        "procesadas cuyo id ya no se genera, p. ej. tras "
                        "cambiar SUBDIVISIONS. Sin este flag quedan huerfanas "
                        "y validate_units.py las cuenta como doble propiedad.")
    p.add_argument("--quiet", action="store_true")
    p.add_argument("--no-color", action="store_true")
    p.add_argument("--json", action="store_true", dest="as_json")
    return p.parse_args(argv)


def _color(s: str, code: str, use_color: bool) -> str:
    return f"{code}{s}{_RESET}" if use_color else s


def _print_summary(
    units: list[dict],
    features_vacias: list[str],
    use_color: bool,
    out_dir: Path,
) -> None:
    head = _color("[build_units]", _BOLD, use_color)
    total = sum(u["archivos_total"] for u in units)
    print(f"{head} unidades={len(units)} archivos_total={total} "
          f"features_vacias={features_vacias}",
          file=sys.stderr)
    by_feature: dict[str, int] = defaultdict(int)
    for u in units:
        by_feature[u["feature_id"]] += u["archivos_total"]
    for fid in sorted(by_feature):
        n_units = sum(1 for u in units if u["feature_id"] == fid)
        print(f"  {fid:5} {n_units:2} unidades  {by_feature[fid]:5} archivos", file=sys.stderr)
    print(f"{head} out_dir={out_dir}", file=sys.stderr)


def main(argv=None) -> int:
    args = parse_args(argv)
    use_color = (not args.no_color) and sys.stderr.isatty()

    rows = load_ledger(args.ledger)
    extracts = load_extracts(args.extract_dir)
    catalogs_present = sorted(extracts.keys()) or list(CATALOG_NAMES)
    if not extracts and not args.quiet:
        print(f"WARN: no se encontraron catalogos en {args.extract_dir}; "
              f"usando lista nominal {list(CATALOG_NAMES)}",
              file=sys.stderr)

    by_feature = distribute(rows)

    if args.include:
        wanted = {f.strip() for f in args.include.split(",") if f.strip()}
        by_feature = {k: v for k, v in by_feature.items() if k in wanted}

    if args.index_only:
        # Solo reconstruye `_index.json` desde el directorio de unidades
        # (util tras `restore_unit_files.py` o `align_units.py`, que editan
        # las unidades sin pasar por el generador).
        only = load_units_from_disk(args.out_dir)
        write_index(args.out_dir, only, sorted(
            fid for fid in FEATURE_TITLES
            if fid not in {u["feature_id"] for u in only}
        ))
        print(f"[build_units] index_only: {len(only)} unidades")
        return 0

    units: list[dict] = []
    all_warnings: list[str] = []
    for feature_id in sorted(by_feature):
        files = by_feature[feature_id]
        sub_units, warnings = _classify(
            feature_id, files, args.no_split, args.max_files
        )
        all_warnings.extend(warnings)
        for sub_id, titulo, sub_files in sub_units:
            unit = _make_unit(sub_id, feature_id, titulo, sub_files, catalogs_present)
            units.append(unit)
            write_unit(args.out_dir, unit)

    if args.prune:
        protected = {r["ruta"] for r in rows if r["estado"] != "pendiente"}
        stale, kept = prune_stale_units(
            args.out_dir, set(by_feature), {u["id"] for u in units}, protected
        )
        if stale and not args.quiet:
            print(f"[build_units] purgadas {len(stale)} unidades obsoletas: "
                  f"{', '.join(stale)}", file=sys.stderr)
        if kept and not args.quiet:
            print(f"[build_units] conservadas {len(kept)} unidades que cubren "
                  f"filas ya verificadas: {', '.join(kept)}", file=sys.stderr)

    # El indice se reconstruye desde el disco completo: las features ya
    # cerradas no se regeneran aqui pero siguen necesitando estar listadas.
    all_units = load_units_from_disk(args.out_dir)
    features_vacias = sorted(
        fid for fid in FEATURE_TITLES if fid not in by_feature
    )
    write_index(args.out_dir, all_units, features_vacias)

    if all_warnings and not args.quiet:
        for w in all_warnings:
            print(f"WARN: {w}", file=sys.stderr)

    if args.as_json:
        print(json.dumps({
            "total_unidades": len(all_units),
            "archivos_total": sum(u["archivos_total"] for u in all_units),
            "features_vacias": features_vacias,
            "by_feature": {
                fid: sum(u["archivos_total"] for u in all_units if u["feature_id"] == fid)
                for fid in sorted({u["feature_id"] for u in all_units})
            },
        }, indent=2, ensure_ascii=False))
    elif not args.quiet:
        _print_summary(all_units, features_vacias, use_color, args.out_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
