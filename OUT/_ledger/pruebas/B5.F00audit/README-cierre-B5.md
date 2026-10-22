# Cierre del Bloque B5 — Secuencias globales extremo a extremo

Fecha: 2026-10-21.
Plan ejecutor: `~/.local/share/kilo/plans/1792588988374-b5-secuencias-globales-plan.md`.

## Resultado

- **14 documentos** en `OUT/15-secuencias-globales/`:
  - `00-indice-secuencias-globales.md` (índice del bloque)
  - `01-arranque-en-frio.md` (B5.1 cold start)
  - `02-login-local-y-cloud.md` (B5.2)
  - `03-cambio-de-workspace.md` (B5.3)
  - `04-crear-abrir-editar-cerrar-documento.md` (B5.4)
  - `05-edicion-concurrente-y-merge.md` (B5.5 CRDT)
  - `06-database-filtro-orden-grupo.md` (B5.6 Filter/Sort/Group)
  - `07-subir-imagen.md` (B5.7 chunked upload)
  - `08-busqueda.md` (B5.8 Tantivy search)
  - `09-chat-con-streaming.md` (B5.9 streaming chat)
  - `10-export-markdown.md` (B5.10)
  - `11-import-csv-zip.md` (B5.11)
  - `12-publish.md` (B5.12)
  - `13-perdida-y-recuperacion-de-red.md` (B5.13)
- **14 unidades** JSON en `OUT/_ledger/units/B5.N.json` (transversal, generadas por `SKILL/scripts/build_b5_units.py`).
- **53 bloques Mermaid** validados con `mmdc` (todos OK).

## Pruebas literales del ROADMAP superadas

1. **Plantilla**: `validate_template.py` 14/14 verde (regex `feature` extendida para aceptar `B5.N`).
2. **Diagramas**: `validate_mermaid.sh` 53/53 verde.
3. **Nombres reales**: cada participante del `sequenceDiagram` es un símbolo del inventario de `SRC/`.

## Adaptaciones a la skill (todas reversibles)

1. **`SKILL/scripts/validate_template.py` (línea 61)**: regex `feature` ampliada de `^F\d+…` a `^(?:F\d+|B5)(?:\.\d+)*$`. Backward-compatible (F* y F*.* siguen matcheando; añade B5.N).
2. **`SKILL/scripts/build_b5_units.py`** (~330 líneas, nuevo): análogo a `make_b4_units.py`; genera las 14 unidades JSON transversales.
3. **`SKILL/scripts/harvest_open_questions.py`**: SCAN_DIRS ampliado con `OUT/15-secuencias-globales/`. Los `[NO DETERMINADO]` de §18 de los docs B5 se vuelcan a `OUT/22-preguntas-abiertas.md §B5`.

## Hallazgos materiales (12; los relevantes)

1. **`app_bloc.dart` ya no existe** en `workspace/application/app/`: fue migrado a `features/workspace/logic/workspace_bloc.dart`. B5.3 §13 lo declara.
2. **`connect_state.rs` no tiene subdir `cloud_storage/`**: la ruta real es `collab/collab-plugins/src/connect_state.rs`. B5.13 §4 corregido.
3. **El import MD es 100 % Dart** (B4 hallazgo 7): B5.11 traza CSV/ZIP, no MD.
4. **`FolderSearchHandler` comentado** en frontend/rust-lib/flowy-core/src/deps_resolve/search_deps.rs:13: las búsquedas de títulos de vista no funcionan pese a que el código siga inyectando el handler.
5. **`UserNotification::DidUpdateReminder` declarada con TODO y nunca emitida**: el disparo real es un `Timer.periodic` de 30 s en Dart (F15.2 + B5.13).
6. **No hay `FolderEvent::OpenWorkspace`**: el evento real es `FolderEvent::ReadCurrentWorkspace`.
7. **`FolderEvent::PublishView` y los publish-related** viven en frontend/rust-lib/flowy-user/src/event_handler.rs:403.
8. **`StreamUploadPB` no es un evento público**: el upload se canaliza via `FileStorageEvent::RegisterStream`.
9. **`ChatNotification::StreamChatMessage`** se emite por chunk desde `Chat::stream_chat_message` (frontend/rust-lib/flowy-ai/src/chat.rs:64).
10. **`create_or_update_sort`** vive en frontend/rust-lib/flowy-database2/src/services/database/database_editor.rs:302.
11. **`NetworkMonitor._updateConnectionStatus`** (frontend/appflowy_flutter/lib/core/network_monitor.dart:12) reacciona a `connectivity_plus`.
12. **Tipos `Mutex<T>` en classDiagram** rompen `mmdc` por los caracteres `<>` y los genéricos `~T~`: corregido durante la validación usando `T-sub-T` o eliminando los genéricos de los miembros.

## Decisiones tomadas

| ID | Decisión |
|---|---|
| D1 | Carpeta `OUT/15-secuencias-globales/` con `00-` + 13 sub-docs (mismo patrón que B4). |
| D2 | Plantilla `feature` (19 secciones) reusada para B5. |
| D3 | Por-doc ≥ 95 % de evidencia. Las refs a archivos que cambiaron de ubicación o ya no existen se marcan `[INFERIDO]` con prosa. |
| D4 | Cada `stateDiagram-v2` se incluye sólo si la secuencia tiene ciclo de vida no trivial (B5.1, B5.4, B5.5, B5.7, B5.13). |
| D5 | Los transversales no ancla archivos en `cobertura.csv`. |

## Preguntas abiertas

13 entradas `[NO DETERMINADO]` volcadas a `OUT/22-preguntas-abiertas.md §B5`:
- `app_life_cycle.rs` línea exacta de `did_update_workspace`
- ruta exacta del `RouterConfig` en F05
- orden de parsers en `MarkdownDocumentEncoder`
- si el `extract_notifications.py` marca 34 falsos negativos (ver F15.1)
- máximo exacto de reintentos del reconnect
- slug divergence Dart vs Rust (B4 §3)
- líneas exactas de `FolderSearchHandler` comentado
- y otros.

## Próxima fase

Bloque B6.1: `18-build-ci-distribucion.md` (el primero de los transversales).
