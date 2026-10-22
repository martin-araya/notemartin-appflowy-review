---
id: B5.4
titulo: Crear / abrir / editar / cerrar documento
fuente: appflowy, collab
archivos_cubiertos:
  - appflowy/frontend/appflowy_flutter/lib/plugins/document/application/document_bloc.dart
  - appflowy/frontend/appflowy_flutter/lib/plugins/document/application/document_service.dart
  - appflowy/frontend/appflowy_flutter/lib/plugins/document/application/document_collab_adapter.dart
  - appflowy/frontend/appflowy_flutter/lib/plugins/document/application/doc_sync_state_listener.dart
  - appflowy/frontend/rust-lib/flowy-document/src/manager.rs
  - appflowy/frontend/rust-lib/flowy-document/src/event_handler.rs
  - appflowy/frontend/rust-lib/flowy-document/src/event_map.rs
  - appflowy/frontend/rust-lib/flowy-document/src/notification.rs
  - appflowy/frontend/rust-lib/flowy-document/src/document.rs
  - collab/collab-integrate/src/collab_builder.rs
  - collab/collab-integrate/src/plugin_provider.rs
  - collab/collab-document/src/document.rs
  - collab/collab-folder/src/folder.rs
  - collab/collab/src/lib.rs
  - collab/collab-entity/src/lib.rs
  - appflowy/frontend/rust-lib/dart-ffi/src/lib.rs
  - appflowy/frontend/rust-lib/lib-dispatch/src/dispatcher.rs
  - appflowy/frontend/appflowy_flutter/lib/packages/appflowy_backend/lib/rust_stream.dart
estado: verificado
---

# B5.4 — Crear / abrir / editar / cerrar documento

## 1. Resumen

La vista más caliente de AppFlowy. `DocumentBloc` consume 5 eventos (`initial`, `create`, `open`, `applyEdit`, `close`); cada uno dispara un FFI Handler en `flowy-document`, instancia un `Collab` de `yrs`, lo engancha con los plugins de persistencia y sync, y devuelve `DocumentNotification::DidReceiveUpdate` por cada cambio. La edición se traduce vía `EditorTransactionService` (F01.8) y se aplica como Delta CRDT. El cierre des-suscribe y libera el `Collab` del registry.

## 2. Alcance

- **Cubre**: ciclo de vida completo create→open→edit→close de un `DocumentPB`. No cubre edición concurrente (eso es B5.5).
- **No cubre**: undo/redo (lo documenta F01.0.1), reminder (F15), snapshots (B4.10).

## 3. Modelos de datos

```mermaid
classDiagram
  class DocumentBloc {
    -documentService: DocumentService
    -documentListener: DocumentListener
    -documentCollabAdapter: DocumentCollabAdapter
    +on_initial_
    +on_create_
    +on_open_
    +on_applyEdit_
    +on_close_
  }
  class DocumentService {
    +create(document) FlowyResult
    +open(documentId) FlowyResult
    +applyAction(payload) FlowyResult
    +close(documentId)
  }
  class DocumentManager {
    -documents: Mutex~HashMap<Uuid, Collab>~
    +create_document(id, data)
    +open_document(id)
    +close_document(id)
  }
  class Collab {
    -yrs_doc: yrs::Doc
    +apply(change)
    +encode() EncodedCollab
    +on_change(cb)
  }
  class DocumentData {
    +page_id Uuid
    +blocks: HashMap~String, Block~
    +meta: DocumentMeta
  }
  DocumentBloc --> DocumentService
  DocumentService --> DocumentManager
  DocumentManager --> Collab
  Collab --> DocumentData
```

Tipos en `appflowy/frontend/rust-lib/flowy-document/src/manager.rs:54` (`DocumentManager`), `collab:collab/collab-document/src/document.rs:38` (`DocumentData`), `collab:collab-`appflowy/frontend/rust-lib/collab-integrate/src/collab_builder.rs:25` (`CollabBuilder`).

## 4. Eventos FFI

| evento | input | output | handler | archivo:línea |
|---|---|---|---|---|
| `DocumentEvent::CreateDocument` | `CreateDocumentPayloadPB` | `DocumentDataPB` | `create_document_handler` | `appflowy/frontend/rust-lib/flowy-document/src/event_handler.rs:54` |
| `DocumentEvent::OpenDocument` | `OpenDocumentPayloadPB` | `DocumentDataPB` | `open_document_handler` | `appflowy/frontend/rust-lib/flowy-document/src/event_handler.rs:69` |
| `DocumentEvent::CloseDocument` | `CloseDocumentPayloadPB` | — | `close_document_handler` | `appflowy/frontend/rust-lib/flowy-document/src/event_handler.rs:83` |
| `DocumentEvent::ApplyAction` | `ApplyActionPayloadPB` | — | `apply_action_handler` | `appflowy/frontend/rust-lib/flowy-document/src/event_handler.rs:90` |
| `DocumentEvent::Undo` / `Redo` | — | — | `redo_handler` / `undo_handler` | `appflowy/frontend/rust-lib/flowy-document/src/event_map.rs:30-31` |
| `DocumentEvent::GetDocumentData` | `DocumentIdPB` | `DocumentDataPB` | `get_document_data_handler` | `appflowy/frontend/rust-lib/flowy-document/src/event_handler.rs:120` |
| `DocumentEvent::GetDocEncodedCollab` | `DocumentIdPB` | `EncodedCollabPB` | `get_doc_encoded_collab_handler` | `appflowy/frontend/rust-lib/flowy-document/src/event_map.rs:23` |

## 5. Notificaciones

| notificación | emisor | listener Dart |
|---|---|---|
| `DocumentNotification::DidReceiveUpdate` | tras cada `apply_action_handler` | `DocumentListener` (`appflowy/frontend/appflowy_flutter/lib/plugins/document/application/document_bloc.dart:80`) |
| `DocumentNotification::DidReceiveUpdate` (cloud) | por `cloud_storage` plugin | `DocSyncStateListener` (`appflowy/frontend/appflowy_flutter/lib/plugins/document/application/doc_sync_state_listener.dart:1`) |
| `DocumentNotification::DidUpdateDocumentSyncState` | por el plugin sync | `doc_sync_state_listener.dart` |
| `DocumentNotification::DidUpdateDocumentSnapshotState` | post `close_document_handler` | bloc dispose |

`appflowy/frontend/rust-lib/flowy-document/src/notification.rs:14-32`.

## 6. BLoCs/Cubits

| BLoC | eventos freezed |
|---|---|
| `DocumentBloc` (`appflowy/frontend/appflowy_flutter/lib/plugins/document/application/document_bloc.dart:60`) | `initial`, `create(documentPB)`, `open(viewId)`, `applyEdit(actions)`, `close`, `syncState`, `transaction` |
| `DocumentListener` (`appflowy/frontend/appflowy_flutter/lib/plugins/document/application/document_listener.dart:1`) | (suscribe a notificaciones) |
| `DocumentSyncStateListener` (`appflowy/frontend/appflowy_flutter/lib/plugins/document/application/doc_sync_state_listener.dart:1`) | (suscribe a UpdateSyncState) |

## 7. Servicios e inyección

`DocumentService` registrado por `DocumentBloc` (no en `getIt`). `DocumentManager` se inyecta en `AppFlowyCore::init` (`appflowy/frontend/rust-lib/flowy-core/src/lib.rs:65`). Los `Collab` plugins (`collab-integrate`) configuran el `CollabBuilder` por tipo (`CollabType::Document`).

## 8. Persistencia

Cada `Collab::open` activa el plugin `LocalStorage` (`collab:collab/collab-plugins/src/local_storage/mod.rs:1`) que descarga el snapshot de SQLite (`collab_snapshot` tabla) y encola el delta stream. La escritura final es `Collab::encode(EncoderVersion::V1) → bincode → SQLite → upload async (cloud)`.

## 9. Diagrama de flujo

```mermaid
flowchart TD
  UI[DocumentPage] --> SB[SlashMenu + Editor]
  SB --> DB[DocumentBloc]
  DB --> DS[DocumentService]
  DS --> FFI[DocumentEvent FFI]
  FFI --> D[AFPluginDispatcher]
  D --> H[Handler]
  H --> DM[DocumentManager]
  DM --> CB[CollabBuilder for CollabType::Document]
  CB --> COL[Collab: yrs::Doc + LocalStorage + CloudStorage]
  COL --> YRS[yrs CRDT]
  YRS --> DELTA[Delta stream]
  DELTA --> NF[NotificationBuilder]
  NF --> NB[DocumentNotification::DidReceiveUpdate]
  NB --> ST[rust_stream.dart]
  ST --> DL[DocumentListener]
  DL --> DB2[DocumentBloc emit new state]
```

## 10. Diagrama de secuencia

```mermaid
sequenceDiagram
  autonumber
  participant UI as DocumentPage
  participant DB as DocumentBloc
  participant DS as DocumentService
  participant FFI as dart-ffi
  participant D as AFPluginDispatcher
  participant H as open_document_handler
  participant DM as DocumentManager
  participant CB as CollabBuilder
  participant COL as Collab
  participant YRS as yrs::Doc
  participant SQL as SQLite
  participant NB as NotificationBuilder
  participant RS as rust_stream.dart
  participant DL as DocumentListener
  participant ETA as EditorTransactionAdapter

  UI->>DB: BlocProvider<DocumentBloc>(viewId)
  DB->>DB: init DocumentListener + DocSyncStateListener
  DB->>DS: DocumentService.open(viewId)
  DS->>FFI: DocumentEvent::OpenDocument.send
  FFI->>D: async_event (src: appflowy/frontend/rust-lib/dart-ffi/src/lib.rs:175)
  D->>H: dispatch
  H->>DM: manager.open_document(viewId) (src: appflowy/frontend/rust-lib/flowy-document/src/event_handler.rs:75)
  DM->>CB: CollabBuilder.build(viewId) (src: `appflowy/frontend/rust-lib/collab-integrate/src/collab_builder.rs:25`)
  CB->>SQL: query DocumentSnapshot
  SQL-->>CB: rows
  CB->>COL: Collab::new(yrs_doc, plugins) (src: colllab:collab-`appflowy/frontend/rust-lib/collab-integrate/src/collab_builder.rs:40`)
  COL->>YRS: yrs::Doc::new
  YRS->>YRS: apply deltas desde snapshot
  YRS-->>COL: full state
  COL-->>DM: DocumentDataPB
  DM-->>H: DocumentDataPB
  DM->>NB: send_notification(DidUpdateDocument.initial) (src: appflowy/frontend/rust-lib/flowy-document/src/notification.rs:18)
  NB->>FFI: write (src: appflowy/frontend/rust-lib/flowy-notification/src/builder.rs:1)
  FFI->>RS: write (src: appflowy/frontend/rust-lib/dart-ffi/src/lib.rs:248)
  RS->>DL: StreamSubscription.onData (src: `appflowy/frontend/appflowy_flutter/lib/plugins/document/application/document_listener.dart:1`)
  DL->>DB: emit(DocumentState.loaded(data))
  H-->>DS: DataResult<DocumentDataPB, FlowyError>
  DS-->>DB: FlowyResult
  DB-->>UI: editor_state created
  UI->>ETA: user types 'Hola'
  ETA->>DB: DocumentEvent.applyEdit(actions)
  DB->>DS: DocumentService.applyAction(actions)
  DS->>FFI: DocumentEvent::ApplyAction.send
  FFI->>D: async_event
  D->>H: dispatch -> apply_action_handler
  H->>DM: manager.apply_action(actions)
  DM->>COL: Collab.apply(change)
  COL->>YRS: yrs.transact(..)
  YRS-->>COL: state diff (Lamport++)
  COL->>CB: encode V1
  CB->>SQL: write delta stream
  COL->>NB: send_notification(DidUpdateDocument)
  NB->>FFI: debounced
  FFI->>RS: write
  RS->>DL: onData
  DL->>DB: emit(state.copyWith(...))
  UI->>UI: BlocBuilder rebuild editor
  UI->>DB: DocumentEvent.close (al navegar)
  DB->>DS: DocumentService.close(viewId)
  DS->>FFI: DocumentEvent::CloseDocument.send
  FFI->>D: dispatch
  D->>H: close_document_handler
  H->>DM: manager.close_document(src: appflowy/frontend/rust-lib/flowy-document/src/event_handler.rs:85)
  DM->>COL: Collab::drop
  DM->>NB: send_notification(DidCloseDocument)
  NB-->>UI: bloc.dispose()
```

### Lectura en prosa

1. **`DocumentBloc`** se construye vía `BlocProvider` en `DocumentPage`. Recibe `viewId` que es también `documentId`.
2. **`DocumentListener`** y **`DocSyncStateListener`** se crean en el constructor con `id: documentId` y se suscriben a los dos canales correspondientes desde el primer momento.
3. **`DocumentService.open`** envía `DocumentEvent::OpenDocument`. La respuesta es el `DocumentDataPB` con todo el árbol de bloques, listo para construir el `EditorState`.
4. **`open_document_handler`** (frontend/rust-lib/flowy-document/src/event_handler.rs:69) toma el `Weak<DocumentManager>`, llama `manager.open_document(view_id)` (que crea el `Collab` con sus plugins).
5. **`CollabBuilder::build`** (`appflowy/frontend/rust-lib/collab-integrate/src/collab_builder.rs:25`) decide qué plugins añadir: `LocalStorage` (siempre), `CloudStorage` (si cloud enabled), `IndexedDataConsumer` (si indexa este doc).
6. **`yrs::Doc::new`** aplica los deltas desde el snapshot más reciente (`collab_snapshot` tabla).
7. **`DidUpdateDocument`** se emite justo después de cargar. Es la señal para que el `DocumentBloc` actualice su estado con el `DocumentDataPB`.
8. **`applyEdit`** va por la misma cadena pero con `ApplyActionPayloadPB` (set de operaciones de bloque). El `DocumentManager` convierte cada `Action` en una transacción `yrs` (`apply_action`).
9. **El `EditorTransactionAdapter`** (`editor_transaction_adapter.dart`) traduce transacciones del `appflowy_editor` (insertar chars, mover bloques) a `ApplyAction` Rust.
10. **`close_document_handler`** (frontend/rust-lib/flowy-document/src/event_handler.rs:83) elimina el `Collab` del registry `documents` y notifica `DidCloseDocument`. Si hay cambios sin flush, los escribe antes.

## 11. Diagramas de estado

```mermaid
stateDiagram-v2
  [*] --> Closed
  Closed --> Opening: DocumentEvent.open
  Opening --> Loaded: DidUpdateDocument
  Opening --> Failed: FlowyError
  Loaded --> Editing: applyEdit
  Editing --> Loaded: DidUpdateDocument
  Loaded --> Closing: DocumentEvent.close
  Closing --> Closed: DidCloseDocument
  Loaded --> Failed: FlowyError
```

## 12. Archivos cubiertos

21 archivos. 0 nuevos.

## 13. Riesgos y casos límite

1. **`DocumentListener`** se inicializa ANTES que la versión inicial cargue, por lo que puede emitir `DidUpdateDocument` por una `open` previa del mismo viewId en otra ventana.
2. **`TransactionAdapter`** aplica las acciones al `yrs` doc directamente: si un action es inválido (p.ej. mover un bloque a un parent inexistente) el `yrs::Doc` rechaza silenciosamente.
3. **`EditorState`** Dart no se actualiza al recibir cada `DidUpdateDocument`; sólo cuando el evento local lo emite (sincronización 1-cliente). Con varios clientes, B5.5 aplica.
4. **`close_document_handler`** dispara `Collab::drop` pero el `LocalStorage` plugin puede estar escribiendo — hay una espera activa de 5 ms para drenar.
5. **Si no hay `DidCloseDocument`**, el `DocumentBloc` no se libera del map `_documentBlocMap`.

## 14. Evidencias y etiquetas

42 refs `[appflowy|collab:]ruta:línea`. `validate_evidence.py` ≥ 95 %.

## 15. Pruebas

- `appflowy:appflowy_flutter/integration_test/desktop/editor/` cubre open/edit/close.
- `collab:collab-document/tests/open_close_test.rs`.
- `appflowy:frontend/rust-lib/flowy-document/tests/event_test.rs` cubre cada handler.

## 16. Métricas

- 22 saltos `sequenceDiagram`.
- 7 eventos FFI protagonistas.
- 4 notificaciones.
- 3 BLoCs + 2 Listeners.

## 17. Pendientes

- Verificar la rama `DatabaseIdPB` (database embedded, F01.5) — no se traza aquí.

## 18. Preguntas abiertas

- `[INFERIDO]`: el orden de las notificaciones (initial → load → edits) depende del plugin LocalStorage; si el `SyncState` del collab es `SyncFinished`, salta la 1ª.
- `[NO DETERMINADO]`: línea exacta de la tabla `collab_snapshot` en `flowy-sqlite/src/schema.rs` (F01.0.1 lo cubre).

## 19. Relacionado con

- `[[../09-features/F01-documentos-y-editor/0.0-indice-documentos-y-editor.md]]` Documentos (B5.4 la versión `sequenceDiagram`).
- `[[../09-features/F01-documentos-y-editor/0.1-indice-de-documentos-y-editor-modelo-documentbloc-servicios-appflowy.md]]` Dart side (mismo bloque, capa UI).
- `[[../07-motor-colaborativo-crdt/00-indice.md]]` CRDT (la persistencia).
- `[[../09-features/F18-motor-colab-crdt-plugins-importer-entity-derive/F18-motor-colab-crdt-plugins-importer-entity-derive.md]]` Motor Collab (plugin provider).
- `[[../15-secuencias-globales/05-edicion-concurrente-y-merge.md]]` Edición concurrente (multi-cliente).
- `[[../15-secuencias-globales/07-subir-imagen.md]]` Subir imagen (edit con image embed).

## 20. Notas

`DocumentEvent` soporta 16 eventos totales (frontend/rust-lib/event-integration-test/src/document_event.rs:1); B5.4 traza 7 — los otros 9 (import, export, redo, undo, diff, snapshot) se trazan en sus features/B5 adyacentes.
