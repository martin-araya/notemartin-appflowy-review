# AGENTS.md — `notemartin-appflowy-review`

Contexto operativo para el agente (y sus subagentes) que construye y ejecuta la skill de ingeniería inversa de **AppFlowy**. Léelo completo antes de cualquier fase del `ROADMAP.md`.

---

## 1. Misión

Producir, desde el código fuente, la documentación técnica más completa posible de AppFlowy en Markdown (español): diagrama de flujo global, cada feature con sus diagramas (flujo, secuencia, estados, datos), todos los archivos involucrados, el motor completo (puente Flutter↔Rust, CRDT, persistencia, sync, búsqueda, IA) y el motor de exportación/importación formato por formato.

El encargo detallado está en `PROMPT.md`. Este archivo define **cómo** se trabaja.

## 2. Qué es la skill

`notemartin-appflowy-review` es una skill portable (Hermes Agent, Cline, Kilo Code) compuesta por:

```
notemartin-appflowy-review/
├── SKILL.md                    # Disparador, flujo de etapas, reglas bloqueantes
├── AGENTS.md                   # Este archivo (copia de referencia)
├── references/
│   ├── repo-map.md             # Mapa del repo (sección 4 de este archivo, mantenido actualizado)
│   ├── patterns.md             # Patrones de arquitectura (sección 5)
│   ├── feature-template.md     # Plantilla obligatoria de feature
│   ├── export-template.md      # Plantilla de formato de export/import
│   ├── diagram-conventions.md  # Convenciones Mermaid
│   └── evidence-rules.md       # Reglas de evidencia y etiquetas
├── scripts/                    # Extracción y validación deterministas
│   ├── fetch_sources.sh
│   ├── inventory.py
│   ├── extract_events.py
│   ├── extract_protobuf.py
│   ├── extract_notifications.py
│   ├── extract_blocs.py
│   ├── extract_deps.py
│   ├── extract_misc.py          # rutas, atajos, flags, claves i18n, error codes
│   ├── assign_ledger.py
│   ├── validate_mermaid.sh
│   ├── validate_evidence.py     # verifica cada ruta:línea citada
│   ├── validate_template.py     # secciones obligatorias presentes
│   ├── validate_coverage.py
│   └── build_index.py
└── templates/
    └── output-skeleton/         # Árbol vacío de appflowy-review/
```

Relación con `notemartin-extension-reviews`: esta skill es un **perfil especializado**. Los scripts genéricos (inventario, ledger, validadores) deben ser reutilizables; lo específico de AppFlowy vive en `references/` y en los extractores de patrones (`event_map.rs`, BLoCs, protobuf).

## 3. Fuentes y versiones

| Fuente | Cómo obtener la versión correcta |
|---|---|
| `AppFlowy-IO/AppFlowy` | `git clone --depth 1` (o el commit que indique el usuario). Registrar `git rev-parse HEAD`. |
| `AppFlowy-IO/AppFlowy-Collab` | Leer el `rev` en `frontend/rust-lib/Cargo.toml` (sección `[patch.crates-io]`, líneas `collab* = { git = …, rev = "…" }`). Clonar en ese `rev`. |
| `AppFlowy-IO/appflowy-editor` | Leer `dependency_overrides.appflowy_editor.git.ref` en `frontend/appflowy_flutter/pubspec.yaml`. Clonar en ese `ref`. |
| `appflowy_editor_plugins` | Versión resuelta en `pubspec.lock`. |
| AppFlowy-Cloud | **Fuera de alcance**. Solo se documenta el contrato desde `flowy-server/src/af_cloud`. |

Referencia usada al diseñar: AppFlowy `5cf3a36` (2026-06-26), Collab `4dfccef`, editor `470c4e7`. **Verificar siempre**; no asumir que siguen iguales.

## 4. Mapa del repositorio (snapshot verificado)

### 4.1 Raíz
`README.md`, `ROADMAP.md`, `CHANGELOG.md`, `doc/` (roadmap, contributing), `install.sh`, `codemagic.yaml` (CI), `project.inlang*` (i18n), `commitlint.config.js`, `frontend/`.

### 4.2 `frontend/`
- `Makefile.toml` (cargo-make: tareas de build/codegen), `rust-toolchain.toml`, `scripts/`, `resources/`.
- `appflowy_flutter/` — app Flutter.
- `rust-lib/` — workspace Cargo.

### 4.3 `frontend/appflowy_flutter/lib/` (~1.800 archivos Dart incl. packages)

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

### 4.4 `frontend/rust-lib/` (~745 archivos `.rs`)

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

## 5. Patrones de arquitectura que debes reconocer

1. **Registro de eventos (Rust)**: cada crate expone `event_map.rs` con
   ```rust
   pub fn init(manager: Weak<XManager>) -> AFPlugin {
     AFPlugin::new().name(..).state(manager)
       .event(XEvent::Foo, foo_handler) ...
   }
   #[derive(Flowy_Event, ProtoBuf_Enum, ...)]
   #[event_err = "FlowyError"]
   pub enum XEvent {
     #[event(input = "FooPB", output = "BarPB")]
     Foo = 0,
   }
   ```
   Handler en `event_handler.rs` → `manager.rs` → collab/persistencia.
2. **Notificaciones (Rust→Dart)**: enum `XNotification` (`ProtoBuf_Enum`) en `notification.rs`, enviado con `NotificationBuilder` (`flowy-notification`), con `debounce`. En Dart: `*_listener.dart` suscritos vía `rust_stream.dart`.
3. **Llamada Dart→Rust**: BLoC → `*_service.dart` → `XEventFoo(payload).send()` (código generado en `appflowy_backend/dispatch`) → FFI `async_event` → `lib-dispatch` → handler → `FlowyResult<T, FlowyError>`.
4. **Inyección de dependencias**: Dart con `get_it` en `startup/deps_resolver.dart`; Rust en `flowy-core/src/deps_resolve/*_deps.rs`.
5. **Collab/CRDT**: cada objeto (folder, documento, database, row, user awareness) es un `Collab` de `yrs`; `collab-integrate` le adjunta plugins (persistencia local, sync cloud, indexación). El editor traduce transacciones de `appflowy_editor` a acciones de bloque (`editor_transaction_adapter.dart` → `ApplyAction`).
6. **Capas `*-pub`**: traits/contratos públicos para romper dependencias circulares (cloud services, entidades compartidas).
7. **Arquitectura Dart dual**: carpetas legadas (`workspace/`, `plugins/`) y nuevas por feature (`features/<x>/{data,logic,presentation}`). Documentar ambas sin asumir cuál es la canónica.

## 6. Reglas de evidencia (bloqueantes)

- Toda afirmación técnica lleva `ruta:línea` o `ruta:inicio–fin`, ruta relativa a la raíz de su repo con prefijo de fuente si no es el principal: `collab:collab-document/src/document.rs:120`, `editor:lib/src/plugins/html/html_document_encoder.dart:40`.
- Etiquetas: `[VERIFICADO]` (por defecto, con evidencia), `[INFERIDO]` (razonamiento explícito), `[NO DETERMINADO]` (va a `22-preguntas-abiertas.md`).
- Prohibido inventar nombres de clases, eventos, archivos o campos. Si dudas, búscalo (`rg`) antes de escribirlo.
- Fragmentos de código ≤ 25 líneas, siempre con referencia.
- Nunca citar un archivo que no esté en el inventario.

## 7. Convenciones de diagramas (Mermaid)

| Uso | Tipo |
|---|---|
| Flujo global / por feature | `flowchart TD` con `subgraph` por capa (UI, BLoC, Servicio, FFI, Rust, Collab, Persistencia, Cloud) |
| Interacciones extremo a extremo | `sequenceDiagram` con participantes nombrados como la clase real |
| Ciclos de vida | `stateDiagram-v2` |
| Modelo de datos | `classDiagram`, `erDiagram` (SQLite) |
| Arquitectura | `flowchart` estilo C4 (contexto → contenedores → componentes) |
| Dependencias | `flowchart LR` |

Reglas: IDs de nodo sin espacios; etiquetas con nombres literales entre comillas si llevan símbolos; un diagrama no supera ~60 nodos (si crece, dividir y enlazar); cada diagrama precedido de una frase que diga qué muestra y seguido de su lectura en prosa. Todo diagrama pasa `validate_mermaid.sh`.

## 8. Protocolo de subagentes

- **Orquestador**: ejecuta scripts, mantiene el ledger, crea unidades de trabajo, asigna, integra, dispara verificación. No escribe documentos de feature.
- **Unidad de trabajo** = `{id, título, archivos[] del ledger, catálogos relevantes, plantilla, documentos dependientes ya terminados}`. Una por feature o sub-feature; si una feature supera ~120 archivos se divide (ej. F01 → un sub-documento por grupo de bloques).
- **Subagente autor**: lee todos sus archivos (no excerpts), escribe el documento con la plantilla, devuelve `{documento, filas_ledger_cubiertas, archivos_extra_detectados, preguntas_abiertas}`. Si detecta archivos fuera de su lista que son necesarios, los declara; el orquestador reasigna.
- **Subagente revisor**: distinto del autor, sin acceso a su razonamiento. Corre `validate_evidence.py`, `validate_template.py`, `validate_mermaid.sh` y además verifica semánticamente una muestra ≥ 30% de afirmaciones (100% en F01, F02, F06 y motor export/import). Devuelve `aprobado | rechazado + lista de correcciones`.
- **Concurrencia**: configurable por plataforma (`MAX_PARALLEL`). Las unidades de catálogo y arquitectura global van primero porque alimentan a las features.
- **Estado**: todo el progreso vive en `_ledger/` y en un `STATE.md` en la raíz de la salida, para poder reanudar en otra sesión o en otra herramienta (Hermes ↔ Cline ↔ Kilo).

## 9. Compatibilidad multiplataforma

- `SKILL.md` en formato estándar (frontmatter `name`, `description`) y sin depender de herramientas propietarias: solo shell, lectura/escritura de archivos y subagentes.
- Los scripts usan Python 3 stdlib + `ripgrep` + `git`; `mermaid-cli` (`npx -y @mermaid-js/mermaid-cli`) para validar.
- Si la plataforma no soporta subagentes, el orquestador ejecuta las unidades en serie con el mismo contrato de entrada/salida (el revisor sigue siendo una pasada separada con contexto limpio).

## 10. Idioma y estilo

- Prosa en español técnico; identificadores, rutas, comandos y código en original.
- Párrafos explicativos completos: qué, cómo, por qué, dónde. Nada de bullets vacíos.
- Cada documento abre con 3–6 líneas de resumen y cierra con "Relacionado con".

## 11. Lo que NO se hace

- No documentar AppFlowy-Cloud por dentro (solo su contrato cliente).
- No ejecutar la app ni hacer cambios al repo analizado (lectura y build de codegen permitidos en un directorio aparte).
- No reducir alcance por tamaño: la extensión no es un criterio.
- No reemplazar análisis por lectura de README/docs oficiales; esos solo sirven como pista y se contrastan con código.

## 12. Glosario mínimo

| Término | Significado |
|---|---|
| Collab | Objeto colaborativo de AppFlowy-Collab sobre un doc `yrs` |
| View | Nodo del árbol del folder (documento, grid, board, calendar, chat…) |
| Space | Agrupación de vistas en el sidebar |
| AFPlugin | Módulo registrado en `lib-dispatch` con sus eventos |
| PB | Sufijo de entidades protobuf (`ViewPB`, `DocumentDataPB`) |
| Awareness | Presencia/cursores de colaboradores en tiempo real |
| Snapshot | Estado serializado de un collab para historial/recuperación |
| Publish | Publicación web de una vista |