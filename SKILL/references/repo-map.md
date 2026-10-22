---
id: R-001
titulo: Mapa del repositorio de AppFlowy
fuente: AGENTS.md §4 (líneas 61–121); SRC/appflowy (snapshot verificado)
archivos_cubiertos: [AGENTS.md]
estado: verificado
---

# R-001 — Mapa del repositorio de AppFlowy

> *Snapshot* verificado del repo monorepo `AppFlowy-IO/AppFlowy` (commit de referencia `5cf3a36`, 2026-06-26). **Verificar siempre** contra el código actual antes de usarlo como fuente; el mapa se mantiene actualizado en `AGENTS.md §4`. Las tres fuentes (AppFlowy, AppFlowy-Collab, appflowy-editor) tienen `rev` fijados y se clonan en `SRC/` siguiendo `AGENTS.md §3`.

## 4.1 Raíz

`README.md`, `ROADMAP.md`, `CHANGELOG.md`, `doc/` (roadmap, contributing), `install.sh`, `codemagic.yaml` (CI), `project.inlang*` (i18n), `commitlint.config.js`, `frontend/`.

## 4.2 `frontend/`

- `Makefile.toml` (cargo-make: tareas de build/codegen), `rust-toolchain.toml`, `scripts/`, `resources/`.
- `appflowy_flutter/` — app Flutter.
- `rust-lib/` — workspace Cargo.

## 4.3 `frontend/appflowy_flutter/lib/` (~1.800 archivos Dart incl. packages)

| Carpeta | Contenido |
|---|---|
| `main.dart` | Punto de entrada |
| `startup/` | `startup.dart`, `entry_point.dart`, `launch_configuration.dart`, `deps_resolver.dart` (get_it), `plugin/`, `tasks/` (`rust_sdk.dart`, `app_widget.dart`, `generate_router.dart`, `appflowy_cloud_task.dart`, `file_storage_task.dart`, `feature_flag_task.dart`, `auto_update_task.dart`, `deeplink/`, `hot_key.dart`, `localization.dart`, `windows.dart`, `platform_error_catcher.dart`, `memory_leak_detector.dart`, `recent_service_task.dart`, `load_plugin.dart`…) |
| `plugins/` | `document`, `database` (`grid`, `board`, `calendar`, `tab_bar`, `application/{cell,field,row,layout,setting,calculations,sync}`), `database_document`, `ai_chat`, `trash`, `emoji`, `inline_actions`, `blank`, `base`, `shared` (`share/`: `export_tab.dart`, `publish_tab.dart`, `share_tab.dart`, `share_bloc.dart`…) |
| `plugins/document/presentation/editor_plugins/` | Un directorio por bloque o capacidad: `actions, ai, align_toolbar_item, background_color, block_menu, block_transaction_handler, bulleted_list, callout, code_block, columns, context_menu, copy_and_paste, cover, database, delta, desktop_toolbar, file, find_and_replace, font, header, heading, i18n, image, inline_math_equation, keyboard_interceptor, link_embed, link_preview, math_equation, mention, menu, migration, mobile_*, numbered_list, outline, page_block, page_style, parsers, quote, shortcuts, simple_table, slash_menu, sub_page, table, todo_list, toggle, toolbar_item, transaction_handler, undo_redo, video` |
| `plugins/document/application/` | `document_bloc.dart`, `document_service.dart`, `document_collab_adapter.dart`, `editor_transaction_adapter.dart`, `document_sync_bloc.dart`, `doc_sync_state_listener.dart`, `document_collaborators_bloc.dart`, `document_awareness_metadata.dart`, `document_diff.dart`, `document_rules.dart`, `document_validator.dart`… |
| `workspace/application/` | `action_navigation, command_palette, edit_panel, export (document_exporter.dart), favorite, home, menu, notification, recent, settings, sidebar, tabs, user, view, view_info, view_title, workspace` |
| `workspace/presentation/` | `command_palette, home (menu/sidebar/import/*), notifications, settings (widgets: files, members, feature_flags, theme_upload, cloud…), widgets` |
| `features/` | `page_access_level, settings, share_tab, shared_section, view_management, workspace, util` (arquitectura más nueva, por feature) |
| `ai/` | servicio y widgets de IA compartidos |
| `user/` | `application, domain, presentation` (auth, perfil) |
| `core/` | `config, helpers, notification, network_monitor.dart, frameless_window.dart` |
| `shared/` | utilidades transversales: `feature_flags.dart`, `markdown_to_document.dart`, `easy_localiation_service.dart`, `icon_emoji_picker`, `permission`, `version_checker`, caché de imágenes… |
| `mobile/` | `application`, `presentation` |
| `packages/` | `appflowy_backend` (FFI + `dispatch/` + `rust_stream.dart`), `appflowy_ui`, `appflowy_popover`, `appflowy_result`, `flowy_infra`, `flowy_infra_ui`, `flowy_svg` |

Otros: `test/` (`bloc_test`, `unit_test`, `widget_test`), `integration_test/` (`desktop_runner_1..9.dart`, `desktop/`), `android/ ios/ linux/ macos/ windows/ web/`, `cargokit_options.yaml`, `distribute_options.yaml`, `build.yaml`.

Dependencias Dart clave: `flutter_bloc`, `get_it`, `go_router`, `appflowy_editor` (git, ref fijado), `appflowy_editor_plugins`, `flutter_chat_ui/core`, `hive_flutter`, `google_fonts`, `hotkey_manager`.

## 4.4 `frontend/rust-lib/` (~745 archivos `.rs`)

| Crate | Rol |
|---|---|
| `dart-ffi` | Frontera C/FFI con Dart (`c.rs`, `lib.rs`, `model/`, `notification/`, `env_serde.rs`, `appflowy_yaml.rs`). Funciones `extern "C"` en `lib.rs`: `init_sdk`, `async_event`, `sync_event`, `set_stream_port`, `set_log_stream_port`, `rust_log`, `set_env`, `link_me_please` |
| `lib-dispatch` | Dispatcher de eventos: `AFPlugin`, `dispatcher.rs`, `request/`, `response/`, `service/`, `runtime.rs` |
| `flowy-core` | Composición del SDK: `lib.rs`, `module.rs`, `config.rs`, `app_life_cycle.rs`, `server_layer.rs`, `deps_resolve/` (`*_deps.rs` por módulo), indexación (`indexing_data_runner.rs`, `full_indexed_data_provider.rs`, `indexed_data_consumer.rs`), `folder_view_observer.rs`, `log_filter.rs` |
| `collab-integrate` | Construcción de objetos collab (`collab_builder.rs`), plugins de persistencia/sync (`plugin_provider.rs`), config |
| `flowy-user` / `-pub` | Usuario, sesión, workspaces, auth, migraciones, settings |
| `flowy-folder` / `-pub` | Workspace, vistas, jerarquía, `share/import.rs`, `publish_util.rs`, `user_default.rs` |
| `flowy-document` / `-pub` | Documentos: `manager.rs`, `document.rs`, `document_data.rs`, `parse.rs`, `parser/`, `reminder.rs` |
| `flowy-database2` / `-pub` | Databases: `manager.rs`, `template.rs`, `services/{calculations,cell,database,database_view,field,field_settings,filter,group,setting,share/csv,snapshot,sort}` |
| `flowy-ai` / `-pub` | IA: `ai_manager.rs`, `chat.rs`, `completion.rs`, `local_ai/`, `mcp/`, `embeddings/`, `model_select.rs`, `offline/`, `search/`, `middleware/`, `ai_tool/` |
| `flowy-search` / `-pub` | Búsqueda (tantivy: `tantivy_state.rs`, `schema.rs`) |
| `flowy-storage` / `-pub` | Archivos: `manager.rs`, `uploader.rs`, `file_cache.rs`, `chunked_byte.rs` |
| `flowy-server` / `-pub` | Implementaciones de servidor: `af_cloud/`, `local_server/` |
| `flowy-sqlite` | SQLite (diesel), `kv/`, `schema.rs` |
| `flowy-sqlite-vec` | Vectores para embeddings |
| `flowy-notification` | Builder y debounce de notificaciones Rust→Dart |
| `flowy-date` | Parsing de fechas |
| `flowy-error` | `code.rs` (ErrorCode), `errors.rs`, conversiones |
| `lib-infra`, `lib-log` | Utilidades, logging |
| `build-tool/{flowy-ast,flowy-codegen,flowy-derive}` | Macros `ProtoBuf`, `ProtoBuf_Enum`, `Flowy_Event` y generador de `.proto` + código Dart |
| `event-integration-test` | Tests de integración por eventos |

Dependencias Rust clave: `collab`, `collab-entity`, `collab-folder`, `collab-document`, `collab-database`, `collab-plugins`, `collab-user`, `collab-importer` (git AppFlowy-Collab, `rev` fijado), `yrs`, `tantivy`, `diesel`, `tokio`, `protobuf 2.x`.

> **Importante:** el repo **no** contiene archivos `.proto` ni el código Dart de eventos: se generan en build a partir de los derives. Ver fase de codegen en el roadmap.

## Relacionado con

- `SKILL/AGENTS.md §4` — fuente original.
- `SKILL/AGENTS.md §2` — composición de la skill.
- `SKILL/AGENTS.md §3` — cómo obtener las tres fuentes en el `rev` correcto.
- `PROMPT.md §4` — mapa inicial de features → archivos.
