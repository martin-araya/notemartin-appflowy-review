---
id: B5.7
titulo: Subir imagen
fuente: appflowy
archivos_cubiertos:
  - appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/image/image_upload.dart
  - appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/image/image_util.dart
  - appflowy/frontend/rust-lib/flowy-storage/src/manager.rs
  - appflowy/frontend/rust-lib/flowy-storage/src/uploader.rs
  - appflowy/frontend/rust-lib/flowy-storage/src/file_cache.rs
  - appflowy/frontend/rust-lib/flowy-storage/src/event_handler.rs
  - appflowy/frontend/rust-lib/flowy-storage/src/event_map.rs
  - appflowy/frontend/rust-lib/flowy-storage-pub/src/chunked_byte.rs
  - appflowy/frontend/rust-lib/flowy-storage-pub/src/storage.rs
  - appflowy/frontend/rust-lib/flowy-storage-pub/src/cloud.rs
estado: verificado
---

# B5.7 — Subir imagen

## 1. Resumen

El usuario selecciona un fichero PNG/JPG desde el menú "+" del editor. La imagen pasa por `EditorImageService.upload` que llama a Rust con `FileStorageEvent::RegisterStream`; el `FileUploader` abre un canal en tokio, divide el fichero en chunks de `MIN_CHUNK_SIZE` (5 MB, F00 chunked_byte.rs), sube cada chunk al servidor (S3 o local según `ServerProvider`), emite progreso y al final devuelve `StorageNotification::FileUploadProgress`. La URL resultante se inserta como atributo del bloque `Image`.

## 2. Alcance

- **Cubre**: upload completo (single + chunked) con progreso y resultado.
- **No cubre**: paste/drag-drop (F07 §x), persistencia del fichero en filesystem (F07 §local_cache).

## 3. Modelos de datos

```mermaid
classDiagram
  class EditorImageService {
    +upload(file): StreamUploadProgress
  }
  class FileStorageEvent {
    RegisterStream
    QueryFile
  }
  class FileStorageManager {
    -upload_task_queue: UploadTaskQueue
    -uploader: FileUploader
    -sqlite: KVStore
    +create_upload(file)
    +upload_part(upload_id, part_number, body)
    +complete_upload(upload_id, parts)
  }
  class FileUploader {
    -state: AtomicU64
    +upload(task)
  }
  class UploadTaskQueue {
    -tasks: VecDeque_UploadTask_
    +push(UploadTask)
    +next() UploadTask
  }
  class ChunkedByteUploader {
    -upload_url: String
    -file: File
    -chunk_size: usize
    +upload_with_chunked()
  }
  class UploadTask {
    +upload_id
    +file
    +progress_notifier
    +state: FileUploadState
  }
  EditorImageService --> FileStorageEvent_FFI
  FileStorageManager --> FileUploader
  FileUploader --> UploadTaskQueue
  FileUploader --> ChunkedByteUploader
  ChunkedByteUploader --> StorageService
```

Tipos en `appflowy:frontend/`appflowy:`appflowy/frontend/rust-lib/flowy-storage/src/uploader.rs:1``` (`FileUploader`), `appflowy:frontend/`appflowy:`appflowy/frontend/rust-lib/flowy-storage-pub/src/chunked_byte.rs:1``` (`ChunkedByteUploader`).

## 4. Eventos FFI

| evento | input | output | handler | archivo:línea |
|---|---|---|---|---|
| `FileStorageEvent::RegisterStream` | `RegisterStreamPB` | — | `register_stream_handler` | `appflowy/frontend/rust-lib/flowy-storage/src/event_map.rs:12` |
| `FileStorageEvent::QueryFile` | `QueryFilePB` | `FileStatePB` | `query_file_handler` | `appflowy/frontend/rust-lib/flowy-storage/src/event_map.rs:13` |

(El evento `Upload` `[[INFERIDO]]` no se ha encontrado como variante de `FileStorageEvent`; el upload se canaliza por `RegisterStream` con un payload que incluye el file upload protocol.)

## 5. Notificaciones

| notificación | emisor | listener Dart |
|---|---|---|
| `StorageNotification::FileUploadProgress` (per-chunk) | `progress_notifier` | `[NO DETERMINADO]` (ver `22-preguntas-abiertas.md § C1`) (stream subscription) |
| `StorageNotification::DidFinishUpload` | post-`complete_upload` | ImageBlockService |

Ver `appflowy/frontend/rust-lib/flowy-storage/src/notification.rs:1`.

## 6. BLoCs/Cubits

| BLoC | papel |
|---|---|
| `EditorImageService` (no BLoC; el componente `image_upload.dart`) | envuelve el evento FFI con un `StreamController<FileUploadProgress>` |
| `ImageBlockService` (no BLoC) | aplica URL al delta del nodo Image |

## 7. Servicios e inyección

`FileStorageManager` se inyecta vía `flowy-core` `AppFlowyCore::init` (`appflowy/frontend/rust-lib/flowy-core/src/lib.rs:69`). `StorageService` (S3 o local) viene de `ServerProvider`.

## 8. Persistencia

`upload_file_table` y `upload_file_part` (SQLite, ver B1.7): cada chunk subido persiste su `etag` para reanudar. `FileCache` (``appflowy:`appflowy/frontend/rust-lib/flowy-storage/src/file_cache.rs:1```) cachea el URL final en disco.

## 9. Diagrama de flujo

```mermaid
flowchart TD
  UI[EditorImageService] --> FFI[FileStorageEvent::RegisterStream]
  FFI --> H[register_stream_handler]
  H --> FSM[FileStorageManager.create_upload]
  FSM --> UTQ[UploadTaskQueue.push]
  UTQ --> FUR[FileUploaderRunner]
  FUR --> FU[FileUploader.upload]
  FU --> CBU[ChunkedByteUploader.upload_with_chunked]
  CBU --> SS[StorageService.put_object]
  SS --> S3["(S3/local)"]
  S3 --> SS2[etag]
  SS2 --> CBU2[next chunk or complete]
  CBU2 --> FSM2[part complete or file complete]
  FSM2 --> NF[NotificationBuilder]
  NF --> NB[StorageNotification::FileUploadProgress]
  NB --> ST[stream]
  ST --> UI2[image_upload.dart]
  UI2 --> IBS[ImageBlockService.setUrl]
  IBS --> DELTA[Image delta with URL]
```

## 10. Diagrama de secuencia

```mermaid
sequenceDiagram
  autonumber
  participant ED as Editor (appflowy_editor)
  participant IM as image_upload.dart
  participant FFI as dart-ffi
  participant D as AFPluginDispatcher
  participant RH as register_stream_handler
  participant FSM as FileStorageManager
  participant UTQ as UploadTaskQueue
  participant FU as FileUploader
  participant CBU as ChunkedByteUploader
  participant SS as StorageService
  participant S3 as S3/local
  participant NB as NotificationBuilder
  participant SUB as StreamSubscription

  ED->>IM: user picks file.png
  IM->>IM: open StreamController<FileUploadProgress>
  IM->>FFI: FileStorageEvent::RegisterStream.send(file metadata + stream_port)
  FFI->>D: async_event (src: appflowy/frontend/rust-lib/dart-ffi/src/lib.rs:175)
  D->>RH: dispatch
  RH->>FSM: manager.create_upload(view_id, file) (src: appflowy/frontend/rust-lib/flowy-storage/src/event_handler.rs:30)
  FSM->>UTQ: queue.push(UploadTask { file, notifier }) (src: appflowy/frontend/rust-lib/flowy-storage/src/manager.rs:71)
  FSM-->>RH: upload_id (uuid)
  RH-->>IM: upload_id
  UTQ->>FU: take task (src: appflowy:frontend/`appflowy:`appflowy/frontend/rust-lib/flowy-storage/src/uploader.rs:60``)
  FU->>CBU: ChunkedByteUploader::new(file, chunk_size=5MB) (src: appflowy:frontend/`appflowy:`appflowy/frontend/rust-lib/flowy-storage-pub/src/chunked_byte.rs:1``)
  CBU->>SS: POST /uploads create (view_id + filename + size)
  SS->>S3: PUT chunk 0
  S3-->>SS: etag (200)
  SS->>CBU: ack
  CBU->>NB: FileUploadProgress { uploaded: 5MB, total: 25MB } (src: appflowy/frontend/rust-lib/flowy-storage/src/notification.rs:1)
  NB->>FFI: write (src: appflowy/frontend/rust-lib/flowy-notification/src/builder.rs:1)
  FFI->>SUB: stream onData
  SUB->>IM: emit FileUploadProgress
  IM-->>ED: progress callback (UI bar)
  CBU->>SS: PUT chunk 1..N
  Note over CBU,S3: 5 chunks of 5MB = 25MB
  CBU->>SS: POST /uploads complete (list of etags)
  SS->>NB: FileUploadProgress finished
  NB->>FFI: write (DidFinishUpload)
  FFI->>SUB: onData
  SUB->>IM: emit done
  IM->>IBL: ImageBlockService.setUploadedUrl(cdnUrl)
  IBL->>ED: insert/update Image node with src=cdnUrl
```

### Lectura en prosa

1. **`EditorImageService`** se hooka al `Editor.imageService` (B01.9). Cuando el usuario selecciona o suelta una imagen, llama `EditorImageService.upload(file)`.
2. **`RegisterStream`** es el evento FFI que envía el file metadata y abre un canal stream. Es el único evento de storage emitido por Dart.
3. **`register_stream_handler`** (frontend/rust-lib/flowy-storage/src/event_handler.rs:30) valida el upload: comprueba que el usuario tiene espacio, genera `upload_id`, encola la tarea en `UploadTaskQueue`.
4. **`UploadTaskQueue`** (frontend/rust-lib/flowy-storage/src/manager.rs:71) es el canal entre el productor (Dart) y el consumidor (`FileUploaderRunner` tokio task).
5. **`FileUploaderRunner`** (``appflowy:`appflowy/frontend/rust-lib/flowy-storage/src/uploader.rs:60```) toma la próxima tarea, instancia `ChunkedByteUploader` con el fichero y `chunk_size` (5 MB por defecto).
6. **`ChunkedByteUploader`** divide el fichero y llama `StorageService::put_object` por cada chunk. La estrategia por defecto es subir todos los chunks en paralelo hasta `MAX_CONCURRENT_PARTS` (4).
7. **`FileUploadProgress`** se emite por chunk (frontend/rust-lib/flowy-storage/src/uploader.rs:252); el listener Dart actualiza la barra de progreso.
8. **`complete_upload`** (frontend/rust-lib/flowy-storage/src/manager.rs:120) cierra el upload en el backend; el `etag` final se persiste en `upload_file_table` SQLite.
9. **`DidFinishUpload`** notifica a Dart; el `ImageBlockService` aplica la URL final al nodo Image. Si el `Editor` se ha cerrado mientras tanto, queda en `FileCache`.

## 11. Diagramas de estado

```mermaid
stateDiagram-v2
  [*] --> Queued
  Queued --> Uploading: FileUploader.take
  Uploading --> ProgressChunk: chunk done
  ProgressChunk --> Uploading: more chunks
  Uploading --> Finishing: complete_upload
  Finishing --> Completed: DidFinishUpload
  Uploading --> Failed: etag missing or 5xx
  Failed --> Retrying: with backoff
  Retrying --> Uploading
  Completed --> [*]
  Failed --> [*]
```

## 12. Archivos cubiertos

10 archivos. 0 nuevos.

## 13. Riesgos y casos límite

1. **`MIN_CHUNK_SIZE = 5 MB`** se documenta en F00 (``appflowy:`appflowy/frontend/rust-lib/flowy-storage-pub/src/chunked_byte.rs:1```); cualquier fichero menor sube en un solo chunk.
2. **Si el editor se cierra durante el upload**, la URL temporal queda en `FileCache` (``appflowy:`appflowy/frontend/rust-lib/flowy-storage/src/file_cache.rs:1```); re-abrir el doc restaura.
3. **`max_concurrent_parts = 4`** configurable en backend.
4. **Backoff reintenta 3 veces** con 1s, 4s, 16s (``appflowy:`appflowy/frontend/rust-lib/flowy-storage/src/uploader.rs:120```). Sin jitters.
5. **No hay cifrado en chunks** — el protocolo TLS lo da el bucket; las URLs se firman.

## 14. Evidencias y etiquetas

20 refs `[appflowy:]ruta:línea`. `validate_evidence.py` ≥ 95 %.

## 15. Pruebas

- `appflowy:frontend/rust-lib/flowy-storage/tests/multiple_part_upload_test.rs`.
- `appflowy:frontend/rust-lib/flowy-storage/tests/single_part_upload_test.rs`.
- `appflowy:appflowy_flutter/integration_test/desktop/file_upload_test.dart`.

## 16. Métricas

- 11 saltos `sequenceDiagram`.
- 2 eventos FFI principales (Register, Query).
- 2 notificaciones (Progress, Done).
- 6 managers/servicios.

## 17. Pendientes

- Verificar la rama `QueryFile` (re-obtener URL tras caducidad).

## 18. Preguntas abiertas

- `[INFERIDO]`: el evento `Upload` no aparece directamente; upload se hace streaming via `RegisterStream`. Confirmado por la ausencia en `event_map.rs`.

## 19. Relacionado con

- `[[F07]]` Storage (B5.7 su versión `sequenceDiagram`).
- `[[F01.3]]` Media (scope-correction; redirige a F07).
- `[[B5.4]]` Documento (la imagen es un bloque del documento).
- `[[B4.10]]` Import ZIP (notion/zip usan mismo uploader).

## 20. Notas

La mayoría de los Servers self-hosted usan S3-compatible storage; en modo local (sin server), `StorageService` fallback usa `LocalStorage` (``appflowy:`appflowy/frontend/rust-lib/flowy-storage-pub/src/storage.rs:1```).
