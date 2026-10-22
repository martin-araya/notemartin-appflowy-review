# B3.F06 — Sync y servidores (`af_cloud` vs `local_server`)

**ROADMAP ref:** línea 290 (`B3.F06`).

**Resultado (2026-10-20)**: 1 documento `OUT/09-features/F06-sync-y-servidores/F06-sync-y-servidores.md` (469 líneas, 19 secciones, **gate-100**) cubriendo los **35 archivos** del ledger F06.

## Suite `validate-B3.F06.sh` 5/5

- `template` = 1/1 (`validate_template.py -t feature`)
- `evidence` = **123/123** refs `` `[fuente:]ruta:línea` `` resueltas contra `inventario.json`
- `mermaid` = **5/5** bloques validados con `mmdc` (1 `classDiagram` §3, 1 `flowchart TD` §9, 2 `sequenceDiagram` §10, 1 `stateDiagram-v2` §11)
- `cobertura` = **35/35** filas `verificado_por = autor_F06`
- `revisor` = `run_subagent.py --rol revisor --gate-100 --feature-id F06` → **aprobado, 0 correcciones** (`pct_efectivo=100`, F06 está en `GATE_100_FEATURES`)

## Distribución del código cubierto

| Subárbol | Archivos | Capa |
|---|---:|---|
| `flowy-server/src/{lib,server,response,util}.rs` | 4 | server |
| `flowy-server/src/af_cloud/**` | 16 | server |
| `flowy-server/src/local_server/**` | 14 | server |
| `flowy-server/Cargo.toml` | 1 | config |
| `core/network_monitor.dart` | 1 | service |
| `plugins/document/application/doc_sync_state_listener.dart` | 1 | bloc |
| **Total** | **35** | |

## Hallazgos estructurales

- **`flowy-server` no registra ningún `XEvent`.** No tiene `event_map.rs`: los servidores se consumen a través de los traits de `flowy-*-pub` desde los managers, nunca por dispatch FFI directo. Declarado explícitamente en §4.
- El documento incluye una **tabla comparativa método → `af_cloud` → `local_server` → divergencia** para cada trait de servicio.

## Correcciones de scope (ROADMAP vs ledger)

| Prometido en el ROADMAP para F06 | Realidad en el ledger | Declarado en |
|---|---|---|
| awareness | `flowy-user/src/user_manager/manager_user_awareness.rs`, `collab:collab-user/src/user_awareness.rs` → **F05.2** | §2, §13 |
| colaboradores | `document_collaborators_bloc.dart`, `document_awareness_metadata.dart`, `collaborator_avatar_stack.dart`, `document_collaborators.dart` → **F01.0.1** (cerrado) | §2, §13 |
| estado de sync de bajo nivel | `collab:collab-plugins/src/cloud_storage/**`, `connect_state.rs` → **F18** | §2, §13 |
| proveedor de servidor | `flowy-core/src/server_layer.rs`, `deps_resolve/cloud_service_impl.rs`, `collab-integrate/src/plugin_provider.rs` → **F00** | §2, §13 |

## Preguntas abiertas (→ `OUT/22-preguntas-abiertas.md`)

1. ¿`update_network_state_handler` (`appflowy/frontend/rust-lib/flowy-user/src/event_handler.rs:473`) muta directamente `AppFlowyCloudServer::network_reachable` o hay un canal intermedio? `[INFERIDO]`
2. ¿Quién invoca `set_network_reachable(true|false)` desde Dart? (`startup/tasks/appflowy_cloud_task.dart`, en F00). `[NO DETERMINADO]`
3. ¿Existen tests de `flowy-server` o de `network_monitor.dart`? Búsqueda exhaustiva sin resultados. `[NO DETERMINADO]`

## Artefactos

- `OUT/09-features/F06-sync-y-servidores/F06-sync-y-servidores.md`
- `OUT/_ledger/pruebas/B3.F06/{validate-B3.F06.sh, revisor_output.json, README.md}`

## Cross-references

- **B1.3** `04-arquitectura-global.md` — contenedores y capas cruzadas.
- **B1.5** `06-puente-flutter-rust/` — `async_event` / `sync_event`, canal de retorno.
- **B1.7** `08-persistencia/` — `upload_file_table` / `upload_file_part` que consume `af_cloud/impls/file_storage.rs`.
- **F01.0.1** — `DocumentSyncBloc` y `document_collaborators_bloc.dart`.
- **F02.0.1.2** — `DatabaseSyncBloc` y `database_sync_state_listener.dart`.
- **F05.2** — `UserManager`, `manager_user_awareness.rs` y `UpdateNetworkState`.
- **F07** — `flowy-storage` (`uploader.rs`, `file_cache.rs`) sobre el `FileStorageService`.
- **F18** — `collab-plugins` (`cloud_storage`, `connect_state.rs`).