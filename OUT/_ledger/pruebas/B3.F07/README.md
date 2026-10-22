# B3.F07 — Almacenamiento de archivos (upload por chunks, reintentos, caché, estados)

**ROADMAP ref:** línea 291 (`B3.F07`).

**Resultado (2026-10-20)**: 1 documento `OUT/09-features/F07-almacenamiento-de-archivos/F07-almacenamiento-de-archivos.md` (460 líneas, 19 secciones) cubriendo los **58 archivos** del ledger F07.

## Suite `validate-B3.F07.sh` 5/5

- `template` = 1/1
- `evidence` = **87/87** refs resueltas contra `inventario.json`
- `mermaid` = **4/4** bloques (`classDiagram` §3, `flowchart TD` §9, `sequenceDiagram` §10, `stateDiagram-v2` §11)
- `cobertura` = **58/58** filas `autor_F07`
- `revisor` → **aprobado, 0 correcciones** (`pct_efectivo=30`, F07 no está en `GATE_100_FEATURES`)

## Distribución del código cubierto

| Subárbol | Archivos |
|---|---:|
| `flowy-storage/` Rust (núcleo: `manager`, `uploader`, `file_cache`, `entities`, `event_*`, `notification`, `sqlite_sql` + config/build + test) | 12 |
| `editor_plugins/image/**` (incl. `multi_image_block_component`, `custom_image_block_component`, `upload_image_menu`) | 21 |
| `editor_plugins/file/**` | 8 |
| `editor_plugins/link_preview/**` | 9 |
| `editor_plugins/link_embed/**` | 2 |
| `editor_plugins/cover/**` (immersivo) | 2 |
| `editor_plugins/video/**` | 1 |
| `workspace/presentation/widgets/image_viewer/**` | 3 |
| `Cargo.toml` / `Flowy.toml` | 2 |
| **Total** | **58** |

## Hallazgos estructurales

- **`flowy-storage` registra 2 eventos FFI** y emite **2 variantes de `StorageNotification`**.
- El troceo de subida vive en `flowy-storage-pub/src/chunked_byte.rs` (`MIN_CHUNK_SIZE = 5 MB`, `ChunkedBytes`), que está asignado a **F00** (contratos públicos).
- Las tablas `upload_file_table` y `upload_file_part` ya están documentadas en **B1.7**; el doc de F07 las referencia sin redeclararlas.

## Correcciones de scope (ROADMAP vs ledger)

| Prometido en el ROADMAP | Realidad en el ledger | Declarado en |
|---|---|---|
| F01.3 "media y archivos" (image/video/file/cover/link_preview/link_embed) | reasignado por el triage de B0.2 a **F07** (42+ archivos); F01.3 quedó como scope-correction | §2, §13 |
| contrato de chunking | `flowy-storage-pub/src/{chunked_byte,cloud,storage}.rs` → **F00** | §2, §13 |
| lado servidor del upload | `flowy-server/src/af_cloud/impls/file_storage.rs` → **F06** | §2, §13 |
| construcción del manager | `flowy-core/src/deps_resolve/file_storage_deps.rs`, `startup/tasks/file_storage_task.dart` → **F00** | §2, §13 |
| listener Dart de `StorageNotification` | `workspace/application/settings/file_storage/file_storage_listener.dart` → **F00** | §2, §13 |

## Preguntas abiertas (→ `OUT/22-preguntas-abiertas.md`)

1. ¿Existe test de widget/integration para `ImagePlaceholder` + `FileBlockComponent` + `UploadImageMenu`? Búsqueda sin resultados. `[NO DETERMINADO]`
2. ¿Hay mecanismo que migre bloques `CustomImageType.local` a nube al cambiar de workspace local a AppFlowy Cloud? `[NO DETERMINADO]`
3. ¿Por qué `notifications.json` marca ambas variantes de `StorageNotification` como `emitted_in_rust: 0` si el código emite en frontend/rust-lib/flowy-storage/src/manager.rs:751–764? Posible hueco del extractor. `[NO DETERMINADO]`
4. ¿`Signal::Stop` cierra limpiamente los `IsolateSink` abiertos vía `RegisterStream`? No hay test de orden de cierre. `[NO DETERMINADO]`

## Cross-references

- **B1.7** `08-persistencia/` — `upload_file_table`, `upload_file_part`, `FileCache`.
- **B1.5** `06-puente-flutter-rust/` — `RegisterStreamPB` y `set_stream_port`.
- **F01.1** — cover clásico (`header/cover_*`) que también sube ficheros.
- **F01.3** — scope-correction que redirigió media y archivos a F07.
- **F02.2** — `MediaCellBloc` (celda tipo media) y `flowy-storage`.
- **F06** — `af_cloud/impls/file_storage.rs`, lado servidor del multipart upload.
- **F00** — `flowy-storage-pub` (contratos), `file_storage_deps.rs`, `file_storage_task.dart`.
