#!/usr/bin/env python3
"""assign_ledger.py — Asigna archivos del inventario a features F01..F17
aplicando las reglas de ruta de PROMPT.md §4 (líneas 143–159) sobre
OUT/_ledger/inventario.json. Reescribe OUT/_ledger/cobertura.csv
poblando `feature_ids` y moviendo el estado de sin_asignar → pendiente
para los matchings. Lo no casado se vuelca a
OUT/_ledger/sin_asignar.md para triage manual en B0.2.

Fase A4.1 de la skill notemartin-appflowy-review.
Ver AGENTS.md §6 (evidencia) y ROADMAP.md línea 97.

Uso:
  assign_ledger.py [--inventario PATH] [--ledger PATH]
                   [--sin-asignar PATH] [--sin-asignar-json PATH]
                   [--dry-run] [--min-coverage N] [--strict]
                   [--quiet] [--no-color] [--json]
                   [--help]

Códigos de salida:
  0  éxito (cubre --min-coverage si se pasó)
  1  cobertura por debajo del umbral (solo si --min-coverage)
  2  error de E/S o de esquema
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

# ---------- rutas y constantes --------------------------------------------

SCRIPT_PATH = Path(__file__).resolve()
SKILL_ROOT = SCRIPT_PATH.parent.parent.parent
INVENTARIO_DEFAULT = SKILL_ROOT / "OUT" / "_ledger" / "inventario.json"
COBERTURA_DEFAULT = SKILL_ROOT / "OUT" / "_ledger" / "cobertura.csv"
SIN_ASIGNAR_MD_DEFAULT = SKILL_ROOT / "OUT" / "_ledger" / "sin_asignar.md"
SIN_ASIGNAR_JSON_DEFAULT = SKILL_ROOT / "OUT" / "_ledger" / "sin_asignar.json"

HEADER_LEDGER = (
    "fuente",
    "ruta",
    "capa",
    "feature_ids",
    "documento",
    "estado",
    "verificado_por",
)
ESTADOS_VALIDOS = {"verificado", "pendiente", "sin_asignar"}
ESTADO_ASIGNADO = "pendiente"
ESTADO_NO_ASIGNADO = "sin_asignar"

# Tabla de features (PROMPT.md §4 líneas 143–159).
# Formato: (id, titulo, [(fuente_raw, patron_raw), ...]).
# fuente_raw puede llevar prefijo "appflowy:", "editor:", "collab:" o
# ninguno (en cuyo caso se asume "appflowy" porque las rutas rust-lib
# viven dentro del repo AppFlowy). La función compile_patterns() lo
# normaliza.
FEATURES: list[tuple[str, str, list[tuple[str, str]]]] = [
    ("F00", "Infraestructura compartida (FFI, dispatch, errores, build, paquetes, nativo, tests)", [
        # Rust workspace — crates estructurales no asignados a feature concreta.
        ("appflowy:", "frontend/rust-lib/dart-ffi/"),
        ("appflowy:", "frontend/rust-lib/lib-dispatch/"),
        ("appflowy:", "frontend/rust-lib/lib-infra/"),
        ("appflowy:", "frontend/rust-lib/flowy-error/"),
        ("appflowy:", "frontend/rust-lib/flowy-sqlite/"),
        ("appflowy:", "frontend/rust-lib/build-tool/"),
        ("appflowy:", "frontend/rust-lib/event-integration-test/"),
        ("appflowy:", "frontend/rust-lib/collab-integrate/"),
        ("appflowy:", "frontend/rust-lib/flowy-document-pub/"),
        ("appflowy:", "frontend/rust-lib/flowy-folder-pub/"),
        ("appflowy:", "frontend/rust-lib/flowy-user-pub/"),
        ("appflowy:", "frontend/rust-lib/flowy-database-pub/"),
        ("appflowy:", "frontend/rust-lib/flowy-ai-pub/"),
        ("appflowy:", "frontend/rust-lib/flowy-search-pub/"),
        ("appflowy:", "frontend/rust-lib/flowy-storage-pub/"),
        ("appflowy:", "frontend/rust-lib/flowy-server-pub/"),
        # flowy-core: SDK, lifecycle, module, config, server_layer, deps_resolve/*.
        ("appflowy:", "frontend/rust-lib/flowy-core/src/lib.rs"),
        ("appflowy:", "frontend/rust-lib/flowy-core/src/app_life_cycle.rs"),
        ("appflowy:", "frontend/rust-lib/flowy-core/src/module.rs"),
        ("appflowy:", "frontend/rust-lib/flowy-core/src/config.rs"),
        ("appflowy:", "frontend/rust-lib/flowy-core/src/server_layer.rs"),
        ("appflowy:", "frontend/rust-lib/flowy-core/src/folder_view_observer.rs"),
        ("appflowy:", "frontend/rust-lib/flowy-core/src/deps_resolve/"),
        ("appflowy:", "frontend/rust-lib/flowy-core/src/cloud_service_impl.rs"),
        ("appflowy:", "frontend/rust-lib/flowy-core/Cargo.toml"),
        ("appflowy:", "frontend/rust-lib/flowy-core/assets/"),
        ("appflowy:", "frontend/rust-lib/flowy-core/.gitignore"),
        ("appflowy:", "frontend/rust-lib/covtest.rs"),
        # Notificaciones cross-crate (de flowy-document, enviada al cliente).
        ("appflowy:", "frontend/rust-lib/flowy-document/src/notification.rs"),
        # Toolchain y configs raíz del workspace rust.
        ("appflowy:", "frontend/rust-lib/Cargo.toml"),
        ("appflowy:", "frontend/rust-lib/rust-toolchain.toml"),
        ("appflowy:", "frontend/rust-lib/rustfmt.toml"),
        ("appflowy:", "frontend/rust-lib/.gitignore"),
        ("appflowy:", "frontend/rust-lib/.cargo/"),
        ("appflowy:", "frontend/Makefile.toml"),
        ("appflowy:", "frontend/scripts/"),
        ("appflowy:", "frontend/resources/"),
        ("appflowy:", "frontend/rust-toolchain.toml"),
        # Paquetes Dart internos (no asignables a feature).
        ("appflowy:", "frontend/appflowy_flutter/packages/"),
        # Estructura de app (no feature concreta).
        ("appflowy:", "frontend/appflowy_flutter/lib/main.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/startup/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/core/config"),
        ("appflowy:", "frontend/appflowy_flutter/lib/core/helpers"),
        ("appflowy:", "frontend/appflowy_flutter/lib/util/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/env/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/date"),
        ("appflowy:", "frontend/appflowy_flutter/lib/flutter"),
        ("appflowy:", "frontend/appflowy_flutter/lib/features/util/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/features/workspace/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/plugins/database_document/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/plugins/emoji/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/plugins/inline_actions/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/plugins/blank/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/plugins/base/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/plugins/shared/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/plugins/util.dart"),
        ("appflowy:", "frontend/appflowy_flutter/dsa_pub.pem"),
        # Tests de la app.
        ("appflowy:", "frontend/appflowy_flutter/test/"),
        ("appflowy:", "frontend/appflowy_flutter/integration_test/"),
        # Carcasas nativas.
        ("appflowy:", "frontend/appflowy_flutter/android/"),
        ("appflowy:", "frontend/appflowy_flutter/ios/"),
        ("appflowy:", "frontend/appflowy_flutter/linux/"),
        ("appflowy:", "frontend/appflowy_flutter/macos/"),
        ("appflowy:", "frontend/appflowy_flutter/windows/"),
        ("appflowy:", "frontend/appflowy_flutter/web/"),
        # Configuración raíz del repo y archivos sueltos.
        ("appflowy:", "frontend/appflowy_flutter/.gitignore"),
        ("appflowy:", "frontend/appflowy_flutter/.metadata"),
        ("appflowy:", "frontend/appflowy_flutter/Makefile"),
        ("appflowy:", "frontend/appflowy_flutter/README.md"),
        ("appflowy:", "frontend/appflowy_flutter/analysis_options.yaml"),
        ("appflowy:", "frontend/appflowy_flutter/pubspec.yaml"),
        ("appflowy:", "frontend/appflowy_flutter/build.yaml"),
        ("appflowy:", "frontend/appflowy_flutter/cargokit_options.yaml"),
        ("appflowy:", "frontend/appflowy_flutter/distribute_options.yaml"),
        ("appflowy:", "frontend/appflowy_flutter/devtools_options.yaml"),
        ("appflowy:", "frontend/appflowy_flutter/dart_dependency_validator.yaml"),
        ("appflowy:", "frontend/appflowy_flutter/dev.env"),
        ("appflowy:", "frontend/appflowy_flutter/assets/"),
        ("appflowy:", ".github/"),
        ("appflowy:", "install.sh"),
        ("appflowy:", "codemagic.yaml"),
        ("appflowy:", "commitlint.config.js"),
        ("appflowy:", "README.md"),
        ("appflowy:", "ROADMAP.md"),
        ("appflowy:", "CHANGELOG.md"),
        ("appflowy:", "doc/"),
        ("appflowy:", ".gitignore"),
        ("appflowy:", ".gitattributes"),
        ("appflowy:", ".dockerignore"),
        ("appflowy:", ".githooks/"),
        ("appflowy:", "LICENSE"),
        ("appflowy:", "CODE_OF_CONDUCT.md"),
    ]),
    ("F18", "Motor Colab (CRDT, plugins, importer, entity, derive)", [
        ("collab:", "collab/"),
        ("collab:", "collab-plugins/"),
        ("collab:", "collab-importer/"),
        ("collab:", "collab-entity/"),
        ("collab:", "collab-derive/"),
    ]),
    ("F19", "Editor (tests, ejemplos, l10n, configuracion)", [
        ("editor:", "test/"),
        ("editor:", "example/"),
        ("editor:", "lib/l10n/"),
        ("editor:", "lib/"),
        ("editor:", "pubspec.yaml"),
        ("editor:", "pubspec.lock"),
        ("editor:", "analysis_options.yaml"),
        ("editor:", "README.md"),
        ("editor:", ".github/"),
        ("editor:", "CHANGELOG.md"),
        ("editor:", "LICENSE"),
        ("editor:", "documentation/"),
        ("editor:", "codecov.yml"),
        ("editor:", ".gitignore"),
    ]),
    ("F20", "Colab (raíz: configuración, CI, docs, manifests)", [
        ("collab:", ".github/"),
        ("collab:", "Cargo.toml"),
        ("collab:", "Makefile.toml"),
        ("collab:", "rust-toolchain.toml"),
        ("collab:", "rustfmt.toml"),
        ("collab:", "LICENSE"),
        ("collab:", "README.md"),
        ("collab:", ".gitignore"),
        ("collab:", "docs/"),
    ]),
    ("F21", "Icon/Emoji picker (Dart UI)", [
        # Modulo autocontenido en shared/. Tocado por toolbar de F01,
        # page-icons de F03, settings de F13 y assets de F17.
        ("appflowy:", "frontend/appflowy_flutter/lib/shared/icon_emoji_picker/"),
    ]),
    ("F01", "Documentos y editor", [
        ("appflowy:", "frontend/appflowy_flutter/lib/plugins/document/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/shared/markdown_to_document.dart"),
        ("editor:", "lib/src/"),
        ("collab:", "collab-document/"),
        # Crate Rust flowy-document (parser, manager, event_map, deps, fixtures, tests).
        ("appflowy:", "frontend/rust-lib/flowy-document/src/"),
        ("appflowy:", "frontend/rust-lib/flowy-document/tests/"),
        ("appflowy:", "frontend/rust-lib/flowy-document/Cargo.toml"),
        ("appflowy:", "frontend/rust-lib/flowy-document/Flowy.toml"),
        ("appflowy:", "frontend/rust-lib/flowy-document/build.rs"),
    ]),
    ("F02", "Bases de datos", [
        ("appflowy:", "frontend/appflowy_flutter/lib/plugins/database/"),
        ("appflowy:", "frontend/rust-lib/flowy-database2/"),
        ("collab:", "collab-database/"),
    ]),
    ("F03", "Folder, workspaces, vistas", [
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/application/home/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/application/view/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/application/view_info/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/application/view_title/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/application/workspace/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/application/menu/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/application/sidebar/"),
        ("appflowy:", "frontend/rust-lib/flowy-folder/"),
        ("collab:", "collab-folder/"),
        # Triage B0.2: chrome estructural de sidebar, vista y move-to.
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/home/menu/sidebar/space/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/home/menu/sidebar/workspace/sidebar_workspace.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/home/menu/sidebar/workspace/_sidebar_workspace_actions.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/home/menu/sidebar/folder/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/home/menu/sidebar/move_to/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/home/menu/view/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/widgets/more_view_actions/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/widgets/rename_view_popover.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/widgets/favorite_button.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/widgets/view_title_bar.dart"),
    ]),
    ("F04", "Sidebar, favoritos, recientes, papelera, tabs, command palette", [
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/application/favorite/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/application/recent/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/application/tabs/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/application/command_palette/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/application/action_navigation/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/application/edit_panel/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/plugins/trash/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/features/view_management/"),
        # Triage B0.2 (recidual): workspace_notifier dentro de sidebar + menu shared state.
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/home/menu/sidebar/workspace/workspace_notifier.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/home/menu/menu_shared_state.dart"),
        # Triage B0.2: chrome de sidebar, home/ layout shell, tabs.
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/home/menu/sidebar/favorites/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/home/menu/sidebar/sidebar.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/home/menu/sidebar/footer/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/home/menu/sidebar/header/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/home/menu/sidebar/shared/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/home/menu/sidebar/workspace/_sidebar_workspace_icon.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/home/menu/sidebar/workspace/_sidebar_workspace_menu.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/home/menu/sidebar/slider_menu_hover_trigger.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/widgets/sidebar_resizer.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/home/desktop_home_screen.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/home/tabs/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/home/af_focus_manager.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/home/home_layout.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/home/home_stack.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/home/home_sizes.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/home/navigation.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/home/hotkeys.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/home/toast.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/home/errors/"),
        # Triage B0.2: edit panel UI y draggable item de sidebar.
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/widgets/edit_panel/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/widgets/draggable_item/"),
    ]),
    ("F05", "Usuario, auth, sesion", [
        ("appflowy:", "frontend/appflowy_flutter/lib/user/"),
        ("appflowy:", "frontend/rust-lib/flowy-user/"),
        ("collab:", "collab-user/"),
        # Triage B0.2: subscription success + user BLoCs + appearance defaults.
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/application/subscription_success_listenable/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/application/user/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/application/appearance_defaults.dart"),
    ]),
    ("F06", "Sync y servidores", [
        ("appflowy:", "frontend/rust-lib/flowy-server/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/core/network_monitor.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/plugins/document/application/doc_sync_state_listener.dart"),
    ]),
    ("F07", "Almacenamiento de archivos", [
        ("appflowy:", "frontend/rust-lib/flowy-storage/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/file/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/image/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/video/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/cover/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/link_preview/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/link_embed/"),
        # Triage B0.2: visor de imagen interactivo (workspace level, capa de presentacion).
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/widgets/image_viewer/"),
    ]),
    ("F08", "Busqueda e indexacion", [
        ("appflowy:", "frontend/rust-lib/flowy-search/"),
        ("appflowy:", "frontend/rust-lib/flowy-core/src/indexing_data_runner.rs"),
        ("appflowy:", "frontend/rust-lib/flowy-core/src/full_indexed_data_provider.rs"),
        ("appflowy:", "frontend/rust-lib/flowy-core/src/indexed_data_consumer.rs"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/application/command_palette/"),
        # Triage B0.2: capa de presentacion de command palette (search UI).
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/command_palette/"),
    ]),
    ("F09", "IA", [
        ("appflowy:", "frontend/rust-lib/flowy-ai/"),
        ("appflowy:", "frontend/rust-lib/flowy-sqlite-vec/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/ai/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/plugins/ai_chat/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/ai/"),
    ]),
    ("F10", "Importacion (UI)", [
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/home/import/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/plugins/database/application/import*"),
        # Triage B0.2: import UI dentro de sidebar y Notion en sidebar de workspace.
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/home/menu/sidebar/import/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/home/menu/sidebar/workspace/_sidebar_import_notion.dart"),
    ]),
    ("F11", "Exportacion (UI)", [
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/application/export/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/plugins/shared/share/export_tab.dart"),
    ]),
    ("F12", "Compartir, publicar, niveles de acceso", [
        ("appflowy:", "frontend/appflowy_flutter/lib/plugins/shared/share/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/features/page_access_level/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/features/share_tab/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/features/shared_section/"),
        ("appflowy:", "frontend/rust-lib/flowy-folder/src/share/import.rs"),
        ("appflowy:", "frontend/rust-lib/flowy-folder/src/publish_util.rs"),
        # Triage B0.2: sitios publicados y dominios (capa presentation de settings).
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/settings/pages/sites/"),
    ]),
    ("F13", "Ajustes, apariencia, temas, fuentes", [
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/application/settings/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/settings/widgets/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/features/settings/"),
        # Triage B0.2: pages y shared de settings (excepto sites/, que va a F12).
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/settings/pages/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/settings/shared/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/settings/settings_dialog.dart"),
    ]),
    ("F14", "Internacionalizacion", [
        ("appflowy:", "project.inlang*"),
        ("appflowy:", "frontend/appflowy_flutter/lib/shared/easy_localiation_service.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/startup/tasks/localization.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/i18n/"),
    ]),
    ("F15", "Notificaciones in-app y recordatorios", [
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/application/notification/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/notifications/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/core/notification/"),
        ("appflowy:", "frontend/rust-lib/flowy-notification/"),
        ("appflowy:", "frontend/rust-lib/flowy-document/src/reminder.rs"),
        ("appflowy:", "frontend/rust-lib/flowy-date/"),
        # Triage B0.2: date picker (recordatorios) y reminder selector.
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/widgets/date_picker/"),
    ]),
    ("F16", "Mobile", [
        ("appflowy:", "frontend/appflowy_flutter/lib/mobile/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/mobile_*/"),
    ]),
    ("F17", "Plataforma (ventanas, deeplinks, auto-update, hotkeys, feature flags, errores, logging)", [
        ("appflowy:", "frontend/appflowy_flutter/lib/startup/tasks/windows.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/startup/tasks/deeplink/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/startup/tasks/auto_update_task.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/startup/tasks/hot_key.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/startup/tasks/platform_error_catcher.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/startup/tasks/memory_leak_detector.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/startup/tasks/feature_flag_task.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/shared/feature_flags.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/core/frameless_window.dart"),
        ("appflowy:", "frontend/rust-lib/lib-log/"),
        ("appflowy:", "frontend/rust-lib/flowy-core/src/log_filter.rs"),
        # Triage B0.2: shared/ utilidades transversales y widgets UI reusables.
        # Excluir icon_emoji_picker/ (F21) y text_field/ (F17 sigue siendo correcto).
        ("appflowy:", "frontend/appflowy_flutter/lib/shared/text_field/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/shared/version_checker/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/shared/conditional_listenable_builder.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/shared/popup_menu/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/shared/permission/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/shared/patterns/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/shared/custom_image_cache_manager.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/shared/appflowy_cache_manager.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/shared/appflowy_network_image.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/shared/appflowy_network_svg.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/shared/google_fonts_extension.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/shared/error_code/error_code_map.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/shared/feedback_gesture_detector.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/shared/settings/show_settings.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/shared/error_page/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/shared/flowy_error_page.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/shared/flowy_gradient_colors.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/shared/af_image.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/shared/af_role_pb_extension.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/shared/af_user_profile_extension.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/shared/loading.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/shared/colors.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/shared/time_format.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/shared/list_extension.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/shared/clipboard_state.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/shared/window_title_bar.dart"),
        # Widgets UI reusables que no encajan en F03/F04/F07/F15.
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/widgets/dialog_v2.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/widgets/dialogs.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/widgets/pop_up_action.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/widgets/tab_bar_item.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/widgets/toggle/"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/widgets/user_avatar.dart"),
        ("appflowy:", "frontend/appflowy_flutter/lib/workspace/presentation/widgets/float_bubble/"),
    ]),
]

# ANSI
_RED = "\033[31m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_RESET = "\033[0m"


# ---------- modelo --------------------------------------------------------


@dataclass
class CompiledPattern:
    """Un patrón (fuente, prefijo_canónico, longitud) listo para matchear.

    `fuente` se compara con inventario['fuente']; `prefix` se compara
    con inventario['ruta_rel'] mediante startswith. `length` es la clave
    de precedencia (más largo gana). `feature_id` y `feature_title`
    conservan el origen.
    """
    feature_id: str
    feature_title: str
    fuente: str
    prefix: str
    length: int
    raw: str


@dataclass
class Stats:
    total: int = 0
    assigned: int = 0
    unassigned: int = 0
    verified_preserved: int = 0
    by_feature: Counter = field(default_factory=Counter)
    by_capa: Counter = field(default_factory=Counter)
    by_fuente: Counter = field(default_factory=Counter)
    unassigned_by_capa: Counter = field(default_factory=Counter)
    unassigned_by_fuente: Counter = field(default_factory=Counter)


# ---------- compilación de patrones ---------------------------------------


def _split_prefix(fuente_raw: str, patron: str) -> tuple[str, str]:
    """Devuelve (fuente, patron_sin_prefijo) manejando 'appflowy:'/'editor:'/'collab:'.

    Los patrones sin prefijo se consideran 'appflowy' (rust-lib vive
    dentro del repo AppFlowy).
    """
    for pre in ("appflowy:", "editor:", "collab:"):
        if fuente_raw == pre:
            return pre[:-1], patron
    return "appflowy", patron


_BRACE_RE = re.compile(r"\{([^{}]*)\}")


def _expand_braces(patron: str) -> list[str]:
    """Expande un único nivel de {a,b,c} en una lista de patrones.

    Si el patrón no tiene llaves, devuelve [patron]. Solo se soporta
    un nivel (los patrones de la tabla no anidan).
    """
    m = _BRACE_RE.search(patron)
    if not m:
        return [patron]
    inside = m.group(1)
    alts = [a.strip() for a in inside.split(",") if a.strip()]
    if not alts:
        return [patron]
    before, after = patron[: m.start()], patron[m.end():]
    return [before + alt + after for alt in alts]


def _glob_to_regex(pat: str) -> str:
    """Convierte un glob (con '*' como wildcard) a regex anchored.

    '*' → '.*'; el resto se escapa. '^' y '$' se añaden al final.
    """
    out = []
    for ch in pat:
        if ch == "*":
            out.append(".*")
        else:
            out.append(re.escape(ch))
    return "^" + "".join(out) + "$"


@dataclass
class CompiledPattern:
    """Un patrón (fuente, regex_canónica, longitud) listo para matchear.

    `fuente` se compara con inventario['fuente']; `regex` se compara
    contra inventario['ruta_rel']. `length` es la clave de
    precedencia (más largo gana). `feature_id` y `feature_title`
    conservan el origen.

    Para reglas de precedencia usamos la longitud de la cadena
    canónica completa (incluye el segmento inicial de la fuente) sin
    contar los wildcards expandidos, de forma que 'mobile_*/' (más
    corto literalmente) quede subordinado a prefijos más específicos
    del mismo nivel.
    """
    feature_id: str
    feature_title: str
    fuente: str
    regex: re.Pattern
    prefix: str  # texto literal que se usa en startswith; '' si el patrón tiene '*' interno
    length: int
    raw: str


def compile_patterns(features: list[tuple[str, str, list[tuple[str, str]]]]) -> list[CompiledPattern]:
    """Compila la tabla FEATURES en lista plana de CompiledPattern.

    Cada `{a,b,c}` se expande; los patrones se ordenan por longitud
    descendente y luego por orden de declaración (F01 antes que F11
    en caso de empate) — la regla 1 de precedencia.

    Soporta `*` como wildcard en cualquier posición (p.ej.
    'mobile_*/'). Si un patrón no contiene '*', se usa startswith
    para velocidad; si lo contiene, se usa regex.
    """
    out: list[CompiledPattern] = []
    for fid, ftitle, patterns in features:
        for fuente_raw, patron in patterns:
            fuente, patron_norm = _split_prefix(fuente_raw, patron)
            for sub in _expand_braces(patron_norm):
                full = fuente + "/" + sub
                if "*" in sub:
                    # Patrón con wildcard → regex anchored.
                    regex = re.compile(_glob_to_regex(full))
                    # Para longitud de precedencia usamos la longitud
                    # del prefijo literal antes del primer '*'.
                    first_star = sub.index("*")
                    literal_prefix = fuente + "/" + sub[:first_star]
                    length = len(literal_prefix)
                else:
                    # Sin wildcard: startswith sobre la ruta completa.
                    regex = re.compile(re.escape(full))
                    literal_prefix = full
                    length = len(full)
                out.append(CompiledPattern(
                    feature_id=fid,
                    feature_title=ftitle,
                    fuente=fuente,
                    regex=regex,
                    prefix=literal_prefix,
                    length=length,
                    raw=f"{fuente_raw}{patron}",
                ))
    # Precedencia: longitud DESC, luego orden de aparición estable.
    out_with_idx = list(enumerate(out))
    out_with_idx.sort(key=lambda t: (-t[1].length, t[0]))
    return [c for _, c in out_with_idx]


def match_file(
    fuente: str,
    ruta_rel: str,
    compiled: list[CompiledPattern],
) -> CompiledPattern | None:
    """Devuelve el CompiledPattern ganador para (fuente, ruta_rel) o None.

    `ruta_rel` debe incluir ya el segmento inicial de la fuente
    (p.ej. 'appflowy/frontend/...'), como lo emite inventory.py.
    """
    best: CompiledPattern | None = None
    best_rank: tuple[int, int] = (-1, -1)  # (length_neg, idx_neg)
    for idx, p in enumerate(compiled):
        if p.fuente != fuente:
            continue
        # Optimización: si el patrón tiene prefijo literal y la ruta
        # no lo comparte, salta el regex.
        if p.prefix and not ruta_rel.startswith(p.prefix):
            continue
        if p.regex.match(ruta_rel):
            # rank = (-length, idx) para preferir el más largo y, en
            # empate, el declarado antes.
            rank = (-p.length, idx)
            if rank < best_rank:
                best = p
                best_rank = rank
    return best


# ---------- IO -------------------------------------------------------------


def load_inventario(path: Path) -> list[dict]:
    if not path.is_file():
        print(f"ERROR: no existe {path}", file=sys.stderr)
        sys.exit(2)
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"ERROR: {path} no es JSON valido: {e}", file=sys.stderr)
        sys.exit(2)
    if d.get("schema_version") != 1:
        print(f"ERROR: schema_version esperado 1, hay {d.get('schema_version')}", file=sys.stderr)
        sys.exit(2)
    if "files" not in d or not isinstance(d["files"], list):
        print(f"ERROR: {path} no tiene clave 'files' como lista", file=sys.stderr)
        sys.exit(2)
    return d["files"]


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
        rows = list(reader)
    return rows


def write_ledger(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, dialect="excel", quoting=csv.QUOTE_MINIMAL)
        w.writerow(HEADER_LEDGER)
        for r in rows:
            w.writerow(tuple(r[c] for c in HEADER_LEDGER))


# ---------- asignación ----------------------------------------------------


def _parse_feature_ids(s: str) -> set[str]:
    s = (s or "").strip()
    if not s:
        return set()
    return {p.strip() for p in s.split(";") if p.strip()}


def _format_feature_ids(ids: set[str]) -> str:
    return ";".join(sorted(ids))


def assign(
    ledger_rows: list[dict],
    inventario_files: list[dict],
    compiled: list[CompiledPattern],
    *,
    strict: bool = False,
) -> tuple[list[dict], Stats, list[str]]:
    """Aplica el matching a las filas del ledger.

    - Construye índice inventario por (fuente, ruta_rel).
    - Para cada fila del ledger, busca su match; añade la feature
      ganadora a feature_ids y transiciona el estado.
    - 'verificado' no se toca nunca.
    - Devuelve (filas_nuevas, stats, warnings).
    """
    inv_index: dict[tuple[str, str], dict] = {}
    for f in inventario_files:
        inv_index[(f["fuente"], f["ruta_rel"])] = f

    stats = Stats()
    warnings: list[str] = []
    out_rows: list[dict] = []
    for r in ledger_rows:
        stats.total += 1
        fuente = r["fuente"]
        ruta = r["ruta"]
        capa = r.get("capa", "")
        estado = r.get("estado", ESTADO_NO_ASIGNADO)
        feature_ids = _parse_feature_ids(r.get("feature_ids", ""))
        doc = r.get("documento", "")
        verif = r.get("verificado_por", "")

        stats.by_fuente[fuente] += 1
        stats.by_capa[capa] += 1

        inv = inv_index.get((fuente, ruta))
        if inv is None:
            warnings.append(f"fila del ledger sin entrada en inventario: {fuente}:{ruta}")

        winner = match_file(fuente, ruta, compiled)

        if estado == "verificado":
            stats.verified_preserved += 1
            # No tocar fila, pero registrarla en out_rows idéntica.
            out_rows.append({
                "fuente": fuente, "ruta": ruta, "capa": capa,
                "feature_ids": _format_feature_ids(feature_ids) or _format_feature_ids({winner.feature_id}) if winner else "",
                "documento": doc, "estado": estado, "verificado_por": verif,
            })
            continue

        if winner is not None:
            feature_ids.add(winner.feature_id)
            new_estado = ESTADO_ASIGNADO
            stats.assigned += 1
            stats.by_feature[winner.feature_id] += 1
        else:
            new_estado = ESTADO_NO_ASIGNADO
            stats.unassigned += 1
            stats.unassigned_by_capa[capa] += 1
            stats.unassigned_by_fuente[fuente] += 1

        if strict and estado == "pendiente" and winner is None:
            warnings.append(
                f"fila previamente 'pendiente' sin matcher: {fuente}:{ruta}"
            )

        out_rows.append({
            "fuente": fuente, "ruta": ruta, "capa": capa,
            "feature_ids": _format_feature_ids(feature_ids),
            "documento": doc, "estado": new_estado, "verificado_por": verif,
        })

    return out_rows, stats, warnings


# ---------- salidas auxiliares --------------------------------------------


def write_sin_asignar(
    md_path: Path,
    json_path: Path,
    rows: list[dict],
    stats: Stats,
    use_color: bool,
) -> None:
    md_path.parent.mkdir(parents=True, exist_ok=True)
    cov = (stats.assigned / stats.total * 100) if stats.total else 0.0

    lines: list[str] = []
    lines.append("# Archivos sin asignar — triage B0.2")
    lines.append("")
    lines.append(f"Generado por `assign_ledger.py` (A4.1). Total inventario: **{stats.total}**.")
    lines.append("")
    lines.append(f"- Asignados: **{stats.assigned}** ({cov:.2f} %)")
    lines.append(f"- Sin asignar: **{stats.unassigned}** ({100 - cov:.2f} %)")
    lines.append(f"- Verificados preservados: **{stats.verified_preserved}**")
    lines.append("")

    lines.append("## Por fuente")
    lines.append("")
    lines.append("| Fuente | Sin asignar | % sobre su fuente |")
    lines.append("|---|---:|---:|")
    for fu in sorted(stats.by_fuente):
        n = stats.unassigned_by_fuente.get(fu, 0)
        tot = stats.by_fuente[fu]
        pct = (n / tot * 100) if tot else 0.0
        lines.append(f"| {fu} | {n} | {pct:.2f} % |")
    lines.append("")

    lines.append("## Por capa")
    lines.append("")
    lines.append("| Capa | Sin asignar |")
    lines.append("|---|---:|")
    for c in sorted(stats.unassigned_by_capa, key=lambda k: -stats.unassigned_by_capa[k]):
        lines.append(f"| {c} | {stats.unassigned_by_capa[c]} |")
    lines.append("")

    unassigned_rows = [r for r in rows if r["estado"] == ESTADO_NO_ASIGNADO]
    unassigned_rows.sort(key=lambda r: (-len(r["ruta"]), r["fuente"], r["ruta"]))
    top = unassigned_rows[:50]
    lines.append(f"## Top {len(top)} rutas no asignadas (las mas profundas primero)")
    lines.append("")
    lines.append("| Ruta | Capa | Fuente |")
    lines.append("|---|---|---|")
    for r in top:
        lines.append(f"| `{r['ruta']}` | {r['capa']} | {r['fuente']} |")
    lines.append("")

    lines.append("## Listado completo por capa")
    lines.append("")
    by_capa_rows: dict[str, list[dict]] = defaultdict(list)
    for r in unassigned_rows:
        by_capa_rows[r["capa"]].append(r)
    for capa in sorted(by_capa_rows):
        lines.append(f"### {capa} ({len(by_capa_rows[capa])})")
        lines.append("")
        for r in by_capa_rows[capa][:200]:
            lines.append(f"- `{r['fuente']}` · `{r['ruta']}`")
        if len(by_capa_rows[capa]) > 200:
            lines.append(f"- … y {len(by_capa_rows[capa]) - 200} más")
        lines.append("")

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    json_path.write_text(
        json.dumps(
            [r for r in rows if r["estado"] == ESTADO_NO_ASIGNADO],
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


# ---------- CLI -----------------------------------------------------------


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Asigna archivos del inventario a features F01..F17 aplicando "
            "PROMPT.md seccion 4 y reescribe OUT/_ledger/cobertura.csv."
        )
    )
    p.add_argument("--inventario", type=Path, default=INVENTARIO_DEFAULT)
    p.add_argument("--ledger", type=Path, default=COBERTURA_DEFAULT)
    p.add_argument("--sin-asignar", type=Path, default=SIN_ASIGNAR_MD_DEFAULT,
                   dest="sin_asignar_md")
    p.add_argument("--sin-asignar-json", type=Path, default=SIN_ASIGNAR_JSON_DEFAULT,
                   dest="sin_asignar_json")
    p.add_argument("--dry-run", action="store_true",
                   help="No escribe cobertura.csv (solo calcula y reporta).")
    p.add_argument("--min-coverage", type=float, default=None,
                   help="Exit 1 si la cobertura (%%) esta por debajo del umbral.")
    p.add_argument("--strict", action="store_true",
                   help="Avisa de filas 'pendiente' previas que pierden su matcher.")
    p.add_argument("--quiet", action="store_true")
    p.add_argument("--no-color", action="store_true")
    p.add_argument("--json", action="store_true", dest="as_json",
                   help="Resumen final en JSON a stdout.")
    return p.parse_args(argv)


def _color(s: str, code: str, use_color: bool) -> str:
    return f"{code}{s}{_RESET}" if use_color else s


def _print_summary(stats: Stats, use_color: bool, out_ledger: Path) -> None:
    cov = (stats.assigned / stats.total * 100) if stats.total else 0.0
    head = _color("[assign_ledger]", _BOLD, use_color)
    print(f"{head} total={stats.total} assigned={stats.assigned} "
          f"unassigned={stats.unassigned} verified_preserved={stats.verified_preserved}",
          file=sys.stderr)
    color = _GREEN if cov >= 90 else (_YELLOW if cov >= 75 else _RED)
    print(f"{head} coverage={_color(f'{cov:.2f}%', color, use_color)}",
          file=sys.stderr)
    print(f"{head} by_feature:", file=sys.stderr)
    for fid, n in sorted(stats.by_feature.items()):
        print(f"  {fid} {n}", file=sys.stderr)
    print(f"{head} by_capa:", file=sys.stderr)
    for c, n in sorted(stats.by_capa.items()):
        u = stats.unassigned_by_capa.get(c, 0)
        print(f"  {c:14} total={n:5}  unassigned={u:5}", file=sys.stderr)
    print(f"{head} by_fuente:", file=sys.stderr)
    for f, n in sorted(stats.by_fuente.items()):
        u = stats.unassigned_by_fuente.get(f, 0)
        print(f"  {f:10} total={n:5}  unassigned={u:5}", file=sys.stderr)
    print(f"{head} ledger={out_ledger}", file=sys.stderr)


def main(argv=None) -> int:
    args = parse_args(argv)
    use_color = (not args.no_color) and sys.stderr.isatty()

    inv_files = load_inventario(args.inventario)
    ledger_rows = load_ledger(args.ledger)
    compiled = compile_patterns(FEATURES)

    if not args.quiet:
        print(f"[assign_ledger] patrones compilados: {len(compiled)} "
              f"({len({p.feature_id for p in compiled})} features)",
              file=sys.stderr)

    new_rows, stats, warnings = assign(
        ledger_rows, inv_files, compiled, strict=args.strict
    )

    if warnings and not args.quiet:
        for w in warnings[:20]:
            print(f"WARN: {w}", file=sys.stderr)
        if len(warnings) > 20:
            print(f"WARN: … y {len(warnings) - 20} mas", file=sys.stderr)

    if not args.dry_run:
        write_ledger(args.ledger, new_rows)
        write_sin_asignar(args.sin_asignar_md, args.sin_asignar_json,
                          new_rows, stats, use_color)

    if args.as_json:
        cov = (stats.assigned / stats.total * 100) if stats.total else 0.0
        print(json.dumps({
            "total": stats.total,
            "assigned": stats.assigned,
            "unassigned": stats.unassigned,
            "verified_preserved": stats.verified_preserved,
            "coverage_pct": round(cov, 4),
            "by_feature": dict(stats.by_feature),
            "by_capa": dict(stats.by_capa),
            "unassigned_by_capa": dict(stats.unassigned_by_capa),
            "by_fuente": dict(stats.by_fuente),
            "unassigned_by_fuente": dict(stats.unassigned_by_fuente),
            "warnings": warnings,
        }, indent=2, ensure_ascii=False))

    if not args.quiet and not args.as_json:
        _print_summary(stats, use_color, args.ledger)

    if args.min_coverage is not None:
        cov = (stats.assigned / stats.total * 100) if stats.total else 0.0
        if cov < args.min_coverage:
            print(
                f"ERROR: cobertura {cov:.2f}% < umbral {args.min_coverage}%",
                file=sys.stderr,
            )
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
