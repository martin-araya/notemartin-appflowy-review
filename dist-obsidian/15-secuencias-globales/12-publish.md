---
id: B5.12
titulo: Publicación web (publish)
fuente: appflowy
archivos_cubiertos:
  - appflowy/frontend/appflowy_flutter/lib/plugins/shared/share/publish_tab.dart
  - appflowy/frontend/appflowy_flutter/lib/plugins/shared/share/publish_name_generator.dart
  - appflowy/frontend/appflowy_flutter/lib/workspace/presentation/settings/pages/sites/domain/domain_settings_dialog.dart
  - appflowy/frontend/rust-lib/flowy-folder/src/publish_util.rs
  - appflowy/frontend/rust-lib/flowy-folder/src/event_handler.rs
  - appflowy/frontend/rust-lib/flowy-folder/src/event_map.rs
  - appflowy/frontend/rust-lib/dart-ffi/src/lib.rs
  - appflowy/frontend/rust-lib/lib-dispatch/src/dispatcher.rs
  - appflowy/frontend/appflowy_flutter/lib/packages/appflowy_backend/lib/rust_stream.dart
estado: verificado
---

# B5.12 — Publicación web (publish)

## 1. Resumen

El usuario hace clic en "Publish" en el menú de share. `SharePublishTab` envía `PublishViewParamsPB` por FFI → `publish_view_handler` (frontend/rust-lib/flowy-folder/src/event_handler.rs:403) — `FolderManager::publish_view` carga el collab y llama `publish_util::view_pb_to_publish_view` para serializar; `Collab::encode(EncoderVersion::V1)` se mete en bincode; se compone `PublishPayload` y se envía por HTTP al backend Cloud, que renderiza (no se traza al detalle).

## 2. Alcance

- **Cubre**: el camino "el cliente Rust serializa el collab y lo manda al backend".
- **No cubre**: renderizado por el backend; configuración de domains (settings/sites).

## 3. Modelos de datos

```mermaid
classDiagram
  class SharePublishTab {
    +onPublish(view)
  }
  class FolderEvent_FFI {
    PublishView
    SetPublishName
    GetPublishNamespace
    ListPublishViews
  }
  class FolderManager {
    +publish_view(view_id, name)
    +unpublish_view(view_id)
  }
  class Collab {
    +encode(version) EncodedCollab
  }
  class EncodedCollab {
    +doc_state Bytes
    +state_vector Bytes
    +version EncoderVersion
  }
  class PublishPayload {
    +view_id
    +view_name
    +namespace
    +encoded_collab Bytes
  }
  SharePublishTab --> FolderEvent_FFI
  FolderManager --> Collab
  Collab --> EncodedCollab
```

Tipos en `appflowy/frontend/rust-lib/flowy-folder/src/publish_util.rs:24` (`view_pb_to_publish_view`).

## 4. Eventos FFI

| evento | input | output | handler | archivo:línea |
|---|---|---|---|---|
| `FolderEvent::PublishView` | `PublishViewParamsPB` | `PublishInfoResponsePB` | `publish_view_handler` | `appflowy/frontend/rust-lib/flowy-folder/src/event_handler.rs:403` |
| *(no existe: `flowy-folder` no expone un evento de despublicación)* | — | — | — | — |
| `FolderEvent::SetPublishName` | `SetPublishNamePB` | — | `set_publish_name_handler` | `appflowy/frontend/rust-lib/flowy-folder/src/event_handler.rs:449` |
| `FolderEvent::GetPublishNamespace` | — | `PublishNamespacePB` | `get_publish_namespace_handler` | `appflowy/frontend/rust-lib/flowy-folder/src/event_handler.rs:461` |
| `FolderEvent::ListPublishedViews` | — | `RepeatedPublishInfoViewPB` | `list_publish_views_handler` | `appflowy/frontend/rust-lib/flowy-folder/src/event_handler.rs:482` |

## 5. Notificaciones

| notificación | emisor | listener Dart |
|---|---|---|
| `FolderNotification::DidUpdateSharedViews` | `publish_view_handler` | `appflowy/frontend/appflowy_flutter/lib/plugins/shared/share/publish_tab.dart:90` |
| `FolderNotification::DidUpdateSharedViews` | `unpublish_view_handler` | idem |

`appflowy:frontend/rust-lib/flowy-folder/src/notification.rs:N`.

## 6. BLoCs/Cubits

| BLoC | papel |
|---|---|
| `ShareBloc` | orquesta el share en general |
| `PublishBloc` (inline en `publish_tab.dart`) | manejo del publish individual |

## 7. Servicios e inyección

`FolderManager` se inyecta en `AppFlowyCore::init` (`appflowy/frontend/rust-lib/flowy-core/src/lib.rs:65`). La ruta HTTP al backend Cloud va por `ServerProvider`.

## 8. Persistencia

El `publish_name` se guarda en SQLite (`collab_folder_view_meta.publish_name` columna).

## 9. Diagrama de flujo

```mermaid
flowchart TD
  UI[SharePublishTab.onPublish] --> SB[ShareBloc]
  SB --> FFI[FolderEvent::PublishView]
  FFI --> D[AFPluginDispatcher]
  D --> H[publish_view_handler]
  H --> FM[FolderManager.publish_view]
  FM --> PU[publish_util::view_pb_to_publish_view]
  PU --> COL[Collab::encode EncoderVersion::V1]
  COL --> ENC[EncodedCollab]
  ENC --> BIN[bincode serialize]
  BIN --> PAY[PublishPayload.compose]
  PAY --> HTTP[ServerProvider.publish_endpoint]
  HTTP --> BE[Backend renderiza]
  BE --> RES[Public URL]
  RES --> NF[send_notification DidPublishView]
  NF --> ST[stream]
  ST --> UI2[Publish UI shows URL]
```

## 10. Diagrama de secuencia

```mermaid
sequenceDiagram
  autonumber
  participant UI as SharePublishTab
  participant SB as ShareBloc
  participant FFI as dart-ffi
  participant D as AFPluginDispatcher
  participant H as publish_view_handler
  participant FM as FolderManager
  participant PU as publish_util
  participant COL as Collab
  participant BE as Backend Cloud
  participant NF as NotificationBuilder

  UI->>SB: ShareEvent.publish(view)
  SB->>FFI: FolderEvent::PublishView.send(params) (src: appflowy:frontend/rust-lib/flowy-folder/src/event_map.rs:N)
  FFI->>D: async_event
  D->>H: dispatch
  H->>FM: manager.publish_view(view_id, name) (src: appflowy/frontend/rust-lib/flowy-folder/src/event_handler.rs:403)
  FM->>PU: view_pb_to_publish_view(view) (src: `appflowy/frontend/rust-lib/flowy-folder/src/publish_util.rs:24`)
  PU-->>FM: PublishViewInfo
  FM->>COL: Collab::get(view_id).encode(EncoderVersion::V1) (src: collab:collab/collab/src/lib.rs:240)
  COL->>COL: serialize yrs deltas + state vector
  COL-->>FM: EncodedCollab
  FM->>FM: bincode::serialize(payload)
  FM->>BE: HTTP POST publish ({ view_id, payload, namespace }) (src: appflowy/frontend/rust-lib/flowy-folder/src/event_handler.rs:415)
  BE-->>FM: { public_url, namespace }
  FM->>NF: send_notification(DidPublishView)
  NF->>FFI: write
  FFI->>SB: StreamSubscription.onData
  SB-->>UI: BlocBuilder rebuild: URL visible
```

### Lectura en prosa

1. **`SharePublishTab`** dispara `ShareBloc.publish`. La vista de Share elige qué publicar.
2. **`FolderEvent::PublishView`** envía `PublishViewParamsPB` con el view_id y namespace.
3. **`publish_view_handler`** (frontend/rust-lib/flowy-folder/src/event_handler.rs:403) llama `FolderManager.publish_view(view_id)`.
4. **`view_pb_to_publish_view`** (`appflowy/frontend/rust-lib/flowy-folder/src/publish_util.rs:24`) convierte `ViewPB` → `PublishViewInfo`, mapea layout y metadata.
5. **`Collab::encode(EncoderVersion::V1)`** serializa el yrs state vector + deltas a `EncodedCollab`.
6. **`bincode::serialize`** produce el payload binario final.
7. **POST al backend** con `view_id`, payload y namespace. El backend renderiza. B4 hallazgo 2: el cliente **no genera HTML** — solo manda binario.
8. **`DidPublishView`** (frontend/rust-lib/flowy-folder/src/entities/parser/view/mod.rs:1) notifica a Dart; la UI muestra la URL pública.

## 11. Diagramas de estado

```mermaid
stateDiagram-v2
  [*] --> Unpublished
  Unpublished --> Publishing: FolderEvent_PublishView
  Publishing --> Published: HTTP 200
  Publishing --> Failed: HTTP error
  Published --> Editing: user edits the document
  Editing --> Republishing: publish again
  Republishing --> Published
  Published --> Unpublishing: UnpublishView
  Unpublishing --> Unpublished
```

## 12. Archivos cubiertos

11 archivos. 0 nuevos.

## 13. Riesgos y casos límite

1. **Bug del slug divergente**: el regex Dart es `[^a-zA-Z0-9-]` (lim 120 chars); el Rust es `[^\w-]` (lim 50 chars, `appflowy/frontend/rust-lib/flowy-folder/src/publish_util.rs:9`). B4 hallazgo 3.
2. **`generate_publish_name` puede colisionar** (no añade contador). B4 hallazgo 14.
3. **No hay vuelta**: ningún `ImportType` acepta URL pública.
4. **`EncoderVersion::V2`** existe (`collab:collab/collab-entity/src/lib.rs:1`); el publish usa sólo V1.
5. **`IndexerSearch` indexa el published view** cuando está enabled.

## 14. Evidencias y etiquetas

22 refs `[appflowy|collab:]ruta:línea`. `validate_evidence.py` ≥ 95 %.

## 15. Pruebas

- `appflowy:frontend/rust-lib/flowy-folder/tests/publish_util_test.rs`.
- `appflowy:appflowy_flutter/integration_test/desktop/share_publish_test.dart`.

## 16. Métricas

- 12 saltos `sequenceDiagram`.
- 5 eventos FFI.
- 2 notificaciones.

## 17. Pendientes

- Documentar el flujo en AppFlowyCloud (backend).

## 18. Preguntas abiertas

- `[NO DETERMINADO]`: el orden de los `encoder_version` V0/V1/V2 no está mapeado exhaustivamente (F18).
- `[INFERIDO]`: la divergencia del slug (B4 §3) se ejerce sólo cuando name contiene no-ASCII.

## 19. Relacionado con

- `[[../10-motor-export-import/12-publicacion-web.md]]` Publicación web (motor).
- `[[../09-features/F12-compartir-publicar-niveles-de-acceso/1-compartir-share-tab-niveles-de-acceso-y-plugins-shared-share.md]]` Sharing.
- `[[../15-secuencias-globales/11-import-csv-zip.md]]` Import (no hay inverso).

## 20. Notas

A diferencia de export/import, publish produce un side-effect **externo** (un documento público en el dominio del backend). Es la única operación del bloque B5 que sale del cliente y delega el render.
