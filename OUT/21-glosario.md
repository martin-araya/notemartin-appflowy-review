---
id: B6.5
titulo: Glosario consolidado de la documentación de AppFlowy
fuente: OUT/_ledger/briefs/B6.5.md
archivos_cubiertos:
  - appflowy/frontend/rust-lib/flowy-document/src/event_map.rs
  - appflowy/frontend/rust-lib/flowy-folder/src/event_map.rs
  - appflowy/frontend/rust-lib/flowy-database2/src/event_map.rs
  - appflowy/frontend/rust-lib/flowy-user/src/event_map.rs
  - appflowy/frontend/rust-lib/flowy-search/src/event_handler.rs
  - appflowy/frontend/rust-lib/dart-ffi/src/lib.rs
  - appflowy/frontend/rust-lib/lib-dispatch/src/module/module.rs
  - appflowy/frontend/rust-lib/flowy-notification/src/lib.rs
  - appflowy/frontend/rust-lib/flowy-notification/src/debounce.rs
  - appflowy/frontend/rust-lib/flowy-error/src/code.rs
  - appflowy/frontend/appflowy_flutter/packages/appflowy_backend/lib/rust_stream.dart
  - appflowy/frontend/appflowy_flutter/lib/plugins/shared/share/share_bloc.dart
  - collab/collab/src/lib.rs
  - collab/collab-plugins/src/lib.rs
estado: verificado
---

# B6.5 — Glosario consolidado

## 1. Resumen

Este documento es la llave de lectura de todo el resultado de `OUT/`: reúne la terminología que aparece dispersa en los documentos de arquitectura, motor, features y catálogos, y la fija con una evidencia `ruta:línea` real en `SRC/` por entrada. Cada término enlaza con el documento de `OUT/` que más lo desarrolla, de modo que el lector puede ir del glosario al detalle sin ambigüedad. La ordenación es alfabética por la inicial del término (las siglas y acrónimos se ordenan por su nombretal, no por su expansión). Cuando un término de la documentación escrita no tiene símbolo verificable en `SRC/`, se marca explícitamente como conceptual en §3 y no se le inventa evidencia.

## 2. Alcance y criterio de inclusión de términos

El alcance es **terminológico, no conceptual**: no se reexplican arquitecturas aquí (eso es trabajo de [[B1.3]], [[06-00-indice]], [[07-00-indice]] y [[08-00-indice]]), sino que se fija **qué significa exactamente cada palabra** cuando aparece en el resto de la documentación. El criterio de inclusión tiene tres filtros, aplicados en este orden:

1. **Frecuencia y peso en `OUT/`**: entra todo término que aparezca en dos o más documentos de la salida, o que sea el nombre de un tipo, evento, crate, tarea de arranque o artefacto de build citado al menos una vez. Esto cubre las familias exigidas por el brief: CRDT/collab, puente FFI, persistencia, datos protobuf, BLoC, red/sync, IA, plataforma, build/CI, seguridad y catálogos.
2. **Verificabilidad**: el término debe corresponder a un símbolo, fichero, tarea o artefacto real localizable en `SRC/` mediante búsqueda. Se acepta tanto un `struct`/`enum`/`trait`/`fn` en Rust como una `class`/`enum` en Dart, un fichero de configuración o una tarea de `Makefile.toml`. Los términos que sólo existen como jerga de producto o de documentación entran igualmente, pero **sin evidencia de código**, y se declaran como tales en §3.
3. **No duplicación**: `AGENTS.md` §12 ya fija ocho términos mínimos (Collab, View, Space, AFPlugin, PB, Awareness, Snapshot, Publish). Esas entradas **se conservan y se amplían** aquí con el símbolo real que las implementa, el crate donde vive y el enlace al documento que las desarrolla; no se repiten literalmente.

Quedan fuera: los identificadores puramente locales de un solo fichero (variables, campos privados), los símbolos de librerías externas que no aparecen en `SRC/` (por ejemplo `client_api`, `af_mcp` o `async_zip` se citan sólo como dependencias, nunca como definición propia), y los términos cuya única aparición en `OUT/` sea el nombre de un fichero sin contenido terminológico.

## 3. Convenciones de lectura

Cada entrada tiene la forma fija `### **Término**  \`[CATEGORÍA]\``, seguida de una definición de una a tres frases (qué es, para qué sirve y dónde encaja), una línea de evidencia y una línea de desarrollo.

La **etiqueta de categoría** agrupa el término por su plano arquitectónico y es puramente orientativa: `CRDT` (motor colaborativo), `PUENTE` (frontera Flutter↔Rust y `lib-dispatch`), `AUT` (identidad y autenticación), `RED` (conectividad, sync y servidores), `IA` (inteligencia artificial), `PLAT` (ventana, deeplinks, atajos, flags), `MOTOR` (composición del SDK en `flowy-core` y servicios), `PERSIST` (SQLite, KV, caché en disco), `CATÁLOGO` (entidades, eventos y códigos que alimentan `11`–`16`), `UI` (Dart: widgets, BLoCs, navegación), `BUILD` (codegen, empaquetado, CI) y `SEG` (seguridad, token y datos en reposo).

La **evidencia** es una o varias referencias con el formato `[fuente:]ruta:línea` o `ruta:inicio–fin`, resolubles contra `OUT/_ledger/inventario.json`. La fuente por defecto es `appflowy`; los repositorios secondary llevan prefijo explícito (`collab:`, `editor:`). Cuando el mismo dato aparece en las dos fuentes, se citan ambas.

El **enlace de desarrollo** usa la sintaxis de enlace interno (doble corchete alrededor del `id`) con el `id` de frontmatter real del documento de `OUT/` que desarrolla el término (por ejemplo `[[07-01-modelo-collab]]`, `[[F02.12]]`). Ningún enlace apunta a un documento inexistente.

**Términos conceptuales sin evidencia de código.** Un puñado de términos que circulan en `OUT/` y en la especificación del producto no corresponden a ningún símbolo en `SRC/`, porque son nombres de interfaz, de producto o de una librería externa:

| Término | Por qué no tiene evidencia | Dónde se usa |
|---|---|---|
| Space (como nombre de producto) | En el código el concepto existe como `Section`/`SectionMap` de `collab-folder`, no como `Space` | Se documenta en §6 bajo **Space**, anclado en el símbolo real que lo implementa |
| Share, ShareTab | Nombre de la pestaña de la UI en `OUT/`; el símbolo de Rust es `publish_util` y los eventos son `FolderEvent::SharePageWithUser` | Se documenta en §7 bajo **Share** y **SharedPage** |
| Feature (en «feature flag») | El enum real es `FeatureFlag`; «feature» a secas es vocabulario de producto | Se documenta en §4 bajo **FeatureFlag** |
| ChunkedByteUploader | No existe en `SRC/`; el símbolo real es `ChunkedBytes` (troceado) y `FileUploader` (subida) | Se documenta en §3 y §5 bajo **ChunkedBytes** y §7 bajo **FileUploader** |
| FileCache | No existe en `SRC/`; el fichero `appflowy/frontend/rust-lib/flowy-storage/src/file_cache.rs` declara en realidad `FileTempStorage` | Se documenta en §5 bajo **FileTempStorage** |
| HNSW | No aparece en `SRC/`: la búsqueda vectorial usa la extensión `sqlite-vec`, no un índice HNSW propio | Se documenta en §7 bajo **VectorSqliteDB** |

Estos seis casos son correcciones sobre la nomenclatura de `AGENTS.md` §4, cuyo mapa del repo se redactó sobre un snapshot anterior: el glosario usa siempre el símbolo que el código muestra hoy.

> **Ampliación de C3 (2026-10-21).** La revisión cruzada encontró ocho símbolos más, todos ellos **fabricados por documentos de `OUT/`** —no por `AGENTS.md`— y etiquetados `[VERIFICADO]` en su documento de origen. El patrón es consistente: se acumulan en documentos escritos sin consultar el código, y los validadores no los detectan porque `validate_evidence.py` solo comprueba que la ruta exista, no que el símbolo citado esté en ella.

| Símbolo fabricado | Por qué no tiene evidencia | Se documenta en |
|---|---|---|
| `ChunkedByteUploader` | No existe en `SRC/`; el tipo real es `ChunkedBytes` (`appflowy/frontend/rust-lib/flowy-storage-pub/src/chunked_byte.rs:14`) | §5 bajo **ChunkedBytes** |
| `AsyncZipExtractor` | No existe en `SRC/`; `collab/collab-importer/src/zip_tool/async_zip.rs` expone `UnzipFile`, `async_unzip`, `unzip_single_file` | — (ninguna secuencia lo usa: el ZIP de Notion se sube al servidor) |
| `ZipCreator` | No existe en `SRC/`; el empaquetado usa `Archive` y `ZipEncoder` del paquete `archive` (`appflowy/frontend/appflowy_flutter/lib/shared/markdown_to_document.dart:80`) | — |
| `KVFileCache` | No existe en ningún repo; se-lo-buscaba un caché de ficheros que no existe | `OUT/08-persistencia/04-file-cache.md §3` |
| `StorageManager::cache` | No existe; los campos reales son `storage_service`, `cloud_service`, `user_service`, `uploader`, `progress_notifiers`, `global_notifier` | `OUT/08-persistencia/04-file-cache.md §5` |
| `StorageNotification::FileUploadProgress` | `StorageNotification` solo tiene `FileStorageLimitExceeded` y `SingleFileLimitExceeded`; el progreso va por `FileProgress` en JSON | `OUT/15-secuencias-globales/07-subir-imagen.md §5` |
| `StorageNotification::DidFinishUpload` | Misma razón; y no hay ninguna notificación de finalización de subida | ídem |
| `MarkdownDocumentEncoder` | No existe; la clase real es `DocumentMarkdownEncoder` (`editor:editor/lib/src/plugins/markdown/encoder/document_markdown_encoder.dart:6`) | `OUT/15-secuencias-globales/10-export-markdown.md §3` |
| `DatabaseEvent::ImportCsvData` | No existe; el CSV entra por `FolderEvent::ImportData` con `ImportTypePB.CSV` | `OUT/15-secuencias-globales/11-import-csv-zip.md §4` |
| `image_upload.dart` | No existe en `plugins/document/…/image/`; el fichero real es `appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/image/upload_image_menu/upload_image_menu.dart` | `OUT/15-secuencias-globales/07-subir-imagen.md §12` |

La lista completa, con el documento de origen y la evidencia de la ausencia, está en `OUT/_ledger/pruebas/C3/README-contraste-B5-B2.md` §3.

## 4. Glosario A–F

### **AFPlugin**  `[PUENTE]`
Módulo registrado en `lib-dispatch` que agrupa un nombre, un conjunto de estados y un mapa evento→handler. Se construye de forma encadenada (`AFPlugin::new().name(..).state(..).event(..)`) y su unicidad se impone al aplanar la lista: si dos plugins declaran el mismo `AFPluginEvent`, `plugin_map_or_crash` entra en pánico.
Evidencia: `appflowy/frontend/rust-lib/lib-dispatch/src/module/module.rs:64`, `appflowy/frontend/rust-lib/lib-dispatch/src/module/module.rs:35`.
Desarrollo: [[06-02-lib-dispatch]]

### **AFPluginData**  `[PUENTE]`
Envoltorio newtype del payload deserializado que se pasa al handler como primer argumento. Implementa `Deref` y `DerefMut` hacia el tipo interno, `into_inner()` para consumirse y una conversión desde `Payload` que traduce un fallo de deserialización protobuf a `InternalError::DeserializeFromBytes`.
Evidencia: `appflowy/frontend/rust-lib/lib-dispatch/src/data.rs:21`, `appflowy/frontend/rust-lib/lib-dispatch/src/data.rs:39`, `appflowy/frontend/rust-lib/lib-dispatch/src/data.rs:74`.
Desarrollo: [[06-02-lib-dispatch]]

### **AFPluginDispatcher**  `[PUENTE]`
Punto de entrada del despacho: recibe un `AFPluginRequest`, localiza el `AFPlugin` asociado al evento en el mapa global y ejecuta su handler. Es el objeto que `dart-ffi` conserva en `DartAppFlowyCore` para mandar trabajo al runtime Rust.
Evidencia: `appflowy/frontend/rust-lib/lib-dispatch/src/dispatcher.rs:63`, `appflowy/frontend/rust-lib/dart-ffi/src/lib.rs:71`.
Desarrollo: [[06-02-lib-dispatch]]

### **AFPluginEvent**  `[PUENTE]`
Clave de tipo `String` que identifica un evento dentro del mapa de plugins; se construye con `From<T>` para cualquier tipo que implemente `Display + Eq + Hash + Debug + Clone`, que es exactamente lo que hacen los enums `DocumentEvent`, `FolderEvent`, `DatabaseEvent` y `UserEvent`.
Evidencia: `appflowy/frontend/rust-lib/lib-dispatch/src/module/module.rs:50`, `appflowy/frontend/rust-lib/lib-dispatch/src/module/module.rs:52`.
Desarrollo: [[06-02-lib-dispatch]]

### **AFPluginEventRequest**  `[PUENTE]`
Envoltorio interno que transporta identificador, evento y los estados del plugin ya resueltos. Lo construye el servicio a partir del `AFPluginRequest` público y de él obtiene el estado tipado mediante `get_state::<AFPluginState<T>>()`.
Evidencia: `appflowy/frontend/rust-lib/lib-dispatch/src/request/request.rs:20`, `appflowy/frontend/rust-lib/lib-dispatch/src/module/module.rs:207`.
Desarrollo: [[06-02-lib-dispatch]]

### **AFPluginEventResponse**  `[PUENTE]`
Respuesta que un handler devuelve al puente: lleva los bytes serializados de la entidad de salida o un error. `AFPluginServiceFuture` la extrae separándola del `ServiceResponse` intermedio antes de devolverla al `Runner` de `dart-ffi`.
Evidencia: `appflowy/frontend/rust-lib/lib-dispatch/src/response/response.rs:22`, `appflowy/frontend/rust-lib/dart-ffi/src/lib.rs:242`.
Desarrollo: [[06-02-lib-dispatch]]

### **AFPluginHandler**  `[PUENTE]`
Trait que implementan las funciones handler: firma genérica sobre el tipo de request deserializado y el de respuesta, con la restricción de que ambos sean `AFConcurrent`. `AFPluginHandlerService` lo envuelve en una factoría de servicios cacheable por evento.
Evidencia: `appflowy/frontend/rust-lib/lib-dispatch/src/service/handler.rs:21`, `appflowy/frontend/rust-lib/lib-dispatch/src/module/module.rs:122`.
Desarrollo: [[06-02-lib-dispatch]]

### **AFPluginRequest**  `[PUENTE]`
Petición pública que cruza el FFI: lleva un `id` generado con `nanoid!(6)`, el evento y el payload. La construye Dart codificándolo como `FFIRequest`, y `async_event` la reconstruye en Rust para entregarla al dispatcher.
Evidencia: `appflowy/frontend/rust-lib/lib-dispatch/src/module/module.rs:141`, `appflowy/frontend/rust-lib/lib-dispatch/src/module/module.rs:153`, `appflowy/frontend/rust-lib/dart-ffi/src/lib.rs:176`.
Desarrollo: [[06-01-ffi]]

### **AFPluginRuntime**  `[PUENTE]`
Runtime Tokio dedicado que `init_sdk` crea y arranca en un hilo con un `LocalSet`, para que los handlers puedan usar `spawn_local`. Es la razón por la que `Task` declara `unsafe impl Send`: el `LocalSet` no es `Send` pero el hilo sí.
Evidencia: `appflowy/frontend/rust-lib/lib-dispatch/src/runtime.rs:9`, `appflowy/frontend/rust-lib/dart-ffi/src/lib.rs:158`, `appflowy/frontend/rust-lib/dart-ffi/src/lib.rs:161`.
Desarrollo: [[06-02-lib-dispatch]]

### **AFPluginState**  `[PUENTE]`
Envoltorio `Arc<T>` del estado registrado por un plugin con `.state(manager)`. Se resuelve por tipo desde `AFPluginEventRequest`, de modo que cada crate expone su `Weak<XManager>` sin depender del crate vecino.
Evidencia: `appflowy/frontend/rust-lib/lib-dispatch/src/module/data.rs:10`, `appflowy/frontend/rust-lib/lib-dispatch/src/module/data.rs:63`.
Desarrollo: [[06-02-lib-dispatch]]

### **AIEvent**  `[CATÁLOGO]`
Enum de eventos del crate `flowy-ai` derivado con `Flowy_Event` y `ProtoBuf_Enum`; incluye el evento `RestartLocalAI` que reactiva el cliente local tras detectar que no estaba listo.
Evidencia: `appflowy/frontend/rust-lib/flowy-ai/src/event_map.rs:65`, `appflowy/frontend/rust-lib/flowy-ai/src/event_map.rs:30`.
Desarrollo: [[F09.1]]

### **AIManager**  `[IA]`
Punto de entrada del subsistema de IA en Rust: coordina chat, completions, indexación de embeddings y la recarga del cliente local. Expone los eventos `AIEvent` hacia el puente y es el objeto que registra `flowy-ai` en el dispatcher.
Evidencia: `appflowy/frontend/rust-lib/flowy-ai/src/ai_manager.rs:58`, `appflowy/frontend/rust-lib/flowy-ai/src/ai_manager.rs:159`.
Desarrollo: [[F09.1]]

### **Anonymous (usuario anónimo)**  `[AUT]`
Modo de uso sin cuenta: el evento `UserEvent::OpenAnonUser` crea un usuario efímero y el BLoC Dart `AnonUserBloc` lo refleja en el `context.read<AnonUserBloc>().add(AnonUserEvent.openAnonUser(user))`. Es la vía por la que la app arranca sin servidor configurado.
Evidencia: `appflowy/frontend/rust-lib/flowy-user/src/event_map.rs:45`, `appflowy/frontend/appflowy_flutter/lib/user/presentation/anon_user.dart:89`.
Desarrollo: [[F05.1]]

### **AppFlowyCore**  `[MOTOR]`
Composición del SDK Rust. Levanta su `AppFlowyCoreConfig`, resuelve las dependencias de todos los módulos y expone el `event_dispatcher`. Es lo que `dart-ffi` mantiene vivo dentro de `DART_APPFLOWY_CORE`.
Evidencia: `appflowy/frontend/rust-lib/flowy-core/src/lib.rs:61`, `appflowy/frontend/rust-lib/dart-ffi/src/lib.rs:56`.
Desarrollo: [[B1.3]]

### **AppFlowyCoreConfig**  `[MOTOR]`
Configuración inmutable del core (versión de app, rutas custom y origen, `device_id`, plataforma). La construye `init_sdk` a partir del JSON que Dart serializa, y de ahí sale el `DEFAULT_NAME` con el que se nombra el usuario por defecto.
Evidencia: `appflowy/frontend/rust-lib/flowy-core/src/config.rs:16`, `appflowy/frontend/rust-lib/dart-ffi/src/lib.rs:139`.
Desarrollo: [[B1.4]]

### **AppFlowyDartConfiguration**  `[PUENTE]`
Estructura serde con la que Dart describe el arranque del SDK: versión, rutas, tipo de autenticador y, si es cloud, la configuración de AppFlowy Cloud. `init_sdk` la deserializa y llama a `write_env()` antes de crear el core.
Evidencia: `appflowy/frontend/rust-lib/dart-ffi/src/env_serde.rs:9`, `appflowy/frontend/rust-lib/dart-ffi/src/lib.rs:124`.
Desarrollo: [[06-01-ffi]]

### **ApplyAction**  `[CATÁLOGO]`
Evento que lleva al Rust las acciones de bloque del editor (`ApplyActionPayloadPB`); es el camino por el que una edición hecha en `appflowy_editor` se convierte en mutación CRDT. Lo emite `DocumentService` al construir el payload protobuf.
Evidencia: `appflowy/frontend/rust-lib/flowy-document/src/event_map.rs:19`, `appflowy/frontend/appflowy_flutter/lib/plugins/document/application/document_service.dart:105`.
Desarrollo: [[F01.0.1]]

### **Async event**  `[PUENTE]`
Mecanismo de llamada Dart→Rust. La función `extern "C" async_event(port, input, len)` deserializa el `FFIRequest` a `AFPluginRequest` y encola un `Task`; la respuesta vuelve al isolate que 호출 `port` mediante el callback `boxed_async_send_with_callback`.
Evidencia: `appflowy/frontend/rust-lib/dart-ffi/src/lib.rs:175`, `appflowy/frontend/rust-lib/dart-ffi/src/lib.rs:209`.
Desarrollo: [[06-01-ffi]]

### **AuthenticatorType**  `[AUT]`
Enum que decide qué implementación de servidor se instancia: `AppFlowyCloud` dispara el guardado de la configuración cloud en `init_sdk`, y el resto de variantes seleccionan el servidor local.
Evidencia: `appflowy/frontend/rust-lib/flowy-server-pub/src/lib.rs:36`, `appflowy/frontend/rust-lib/dart-ffi/src/lib.rs:127`.
Desarrollo: [[F05.2]]

### **AuthService**  `[AUT]`
Interfaz Dart de autenticación, registrada como factory en `get_it` en el arranque. Todo el resto de la app la consume para cerrar sesión o resolver el estado de autenticación, en lugar de hablar directamente con Rust.
Evidencia: `appflowy/frontend/appflowy_flutter/lib/startup/deps_resolver.dart:109`, `appflowy/frontend/appflowy_flutter/lib/user/presentation/helpers/handle_open_workspace_error.dart:30`.
Desarrollo: [[F05.1]]

### **AuthType**  `[AUT]`
Enumeración Rust del modo de autenticación de una sesión (cloud, local, self-hosted, anon). Es el contrato público de `flowy-user-pub` que consumen los crates que no dependen de `flowy-user`.
Evidencia: `appflowy/frontend/rust-lib/flowy-user-pub/src/entities.rs:309`.
Desarrollo: [[F05.2]]

### **AuthTypePB**  `[CATÁLOGO]`
Contraparte protobuf de `AuthType` que viaja por el puente. Los eventos de `flowy-user` la usan para filtrar qué login está permitido; el propio `UserEvent::SignInWithEmailPassword` documenta que solo aplica con `AuthType` local o self-hosted.
Evidencia: `appflowy/frontend/rust-lib/flowy-user/src/entities/workspace.rs:288`, `appflowy/frontend/rust-lib/flowy-user/src/event_map.rs:89`.
Desarrollo: [[11-catalogo-eventos-ffi]]

### **AutoUpdate**  `[PLAT]`
Tarea de arranque (`AutoUpdateTask`) que registra un `UpdaterListener` sobre `auto_updater` para comprobar y descargar versiones nuevas en escritorio. Modela el resultado con `AppFlowyAutoUpdateVersion`.
Evidencia: `appflowy/frontend/appflowy_flutter/lib/startup/tasks/auto_update_task.dart:17`, `appflowy/frontend/appflowy_flutter/lib/startup/tasks/auto_update_task.dart:104`.
Desarrollo: [[B6.1]]

### **cargo-make**  `[BUILD]`
Runner de tareas del build. `Makefile.toml` lo declara en la cabecera y extiende once ficheros de `scripts/makefile/` (protobuf, tests, docker, flutter, web, tauri…), además de fijar `CARGO_MAKE_CRATE_NAME = "dart-ffi"` y `LIB_NAME = "dart_ffi"`, que es el nombre con el que Dart encuentra el símbolo de la librería.
Evidencia: `appflowy/frontend/Makefile.toml:1`, `appflowy/frontend/Makefile.toml:4`, `appflowy/frontend/Makefile.toml:25`.
Desarrollo: [[B6.1]]

### **cargokit**  `[BUILD]`
Plugin de build de Flutter que empaqueta la librería nativa Rust. La configuración del proyecto activa explícitamente binarios precompilados, que es lo que hace que el FFI funcione sin compilar Rust en el dispositivo del usuario.
Evidencia: `appflowy/frontend/appflowy_flutter/cargokit_options.yaml:1`.
Desarrollo: [[B6.1]]

### **ChatServiceMiddleware**  `[IA]`
Capa intermedia de `flowy-ai` que envuelve la llamada de chat para inyectar el contexto (prompt de sistema, workspace, modelo seleccionado) antes de invocar al proveedor. Es lo que `chat.rs` consume como `Arc<ChatServiceMiddleware>`.
Evidencia: `appflowy/frontend/rust-lib/flowy-ai/src/middleware/chat_service_mw.rs:21`, `appflowy/frontend/rust-lib/flowy-ai/src/chat.rs:38`.
Desarrollo: [[F09.1]]

### **ChunkedBytes**  `[MOTOR]`
Representación troceada de un archivo grande para subirlo por partes. `flowy-storage` la calcula con `MIN_CHUNK_SIZE` y `calculate_offsets`, y los tests de subida múltiple la usan como contrato de tamaños.
Evidencia: `appflowy/frontend/rust-lib/flowy-storage-pub/src/chunked_byte.rs:14`, `appflowy/frontend/rust-lib/flowy-storage/src/manager.rs:17`.
Desarrollo: [[F07]]

### **CocoaWindowChannel**  `[PLAT]`
Canal de plataforma hacia la ventana nativa macOS (`flutter/cocoaWindow`) con el que se posiciona y hace zoom a la ventana. Es el sustituto real del término «frameless window»: no existe ninguna clase `FramelessWindow` en el código.
Evidencia: `appflowy/frontend/appflowy_flutter/lib/core/frameless_window.dart:6`, `appflowy/frontend/appflowy_flutter/lib/core/frameless_window.dart:9`.
Desarrollo: [[F17]]

### **Codegen (flowy-codegen)**  `[BUILD]`
Generador que recorre las entidades Rust anotadas y emite tanto los `.proto` como el código Dart de eventos. Está condicionado por tres características (`features`) (`proto_gen`, `dart_event`, `ts_event`) y comparte el parser de `flowy.toml`.
Evidencia: `appflowy/frontend/rust-lib/build-tool/flowy-codegen/src/lib.rs:1`, `appflowy/frontend/rust-lib/build-tool/flowy-codegen/src/lib.rs:9`.
Desarrollo: [[06-03-codegen]]

### **Collab**  `[CRDT]`
Objeto colaborativo: envuelve un documento `yrs` (`Doc`) junto con sus plugins, el origen y el estado deObservación. Es la unidad sobre la que se sincroniza, se persiste y de la que se derivan snapshots.
Evidencia: `collab:collab/collab/src/core/collab.rs:53`, `collab:collab/collab/src/lib.rs:32`.
Desarrollo: [[07-01-modelo-collab]]

### **CollabBuilder**  `[CRDT]`
Constructor del `Collab`: fija el `Doc`, la lista de plugins y el `CollabOrigin`. `collab-integrate` aporta su propia capa (`CollabBuilderConfig`) para añadir persistencia, sync e indexación sin cambiar el núcleo.
Evidencia: `collab:collab/collab/src/core/collab.rs:615`, `appflowy/frontend/rust-lib/collab-integrate/src/collab_builder.rs:400`.
Desarrollo: [[07-01-modelo-collab]]

### **CollabConnectState**  `[RED]`
Estado de alcanzabilidad de la conexión cloud de un collab (`CollabConnectState` y su gemelo `CollabConnectReachability`). `collab-integrate` lo lee para decidir si se encola un update o se envía de inmediato.
Evidencia: `collab:collab/collab-plugins/src/connect_state.rs:6`, `appflowy/frontend/rust-lib/collab-integrate/src/collab_builder.rs:18`.
Desarrollo: [[F06]]

### **CollabKVDB**  `[PERSIST]`
Alias del almacén local de collabs según plataforma: `KVTransactionDBRocksdbImpl` en nativo e `CollabIndexeddb` en wasm. Toda la API de `collab-plugins` se escribe contra este alias, por lo que el resto de la app no distingue backend.
Evidencia: `collab:collab/collab-plugins/src/lib.rs:24`, `collab:collab/collab-plugins/src/lib.rs:28`.
Desarrollo: [[08-03-collab-db]]

### **CollabPersistence**  `[CRDT]`
Trait que un plugin de disco implementa para cargar y guardar el `Collab` codificado. Sus implementaciones reales viven en `collab-plugins` (RocksDB) y en `collab-database` para el estado de las bases de datos.
Evidencia: `collab:collab/collab/src/core/collab_plugin.rs:25`, `collab:collab/collab-plugins/src/local_storage/rocksdb/util.rs:39`.
Desarrollo: [[07-06-collab-plugins]]

### **CollabPlugin**  `[CRDT]`
Trait que extiende la vida de un `Collab`: se le notifica de cada cambio del documento y puede actuar (persistir, enviar, indexar). Los tipos se discriminan con `CollabPluginType`.
Evidencia: `collab:collab/collab/src/core/collab_plugin.rs:49`, `collab:collab/collab/src/core/collab_plugin.rs:15`.
Desarrollo: [[07-06-collab-plugins]]

### **CollabPluginType**  `[CRDT]`
Discriminante de los plugins: `CloudStorage` para el que sincroniza remoto (sólo uno por documento) y `Other(String)` para el resto.
Evidencia: `collab:collab/collab/src/core/collab_plugin.rs:15`, `collab:collab/collab/src/core/collab_plugin.rs:17`.
Desarrollo: [[07-06-collab-plugins]]

### **CollabSink**  `[RED]`
Cola de envío del plugin de nube: `CollabSink<Sink, Msg>` serializa las mutaciones locales y las entrega al transporte websocket cuando la conexión está disponible; si no, quedan encoladas.
Evidencia: `collab:collab/collab-plugins/src/cloud_storage/sink.rs:34`, `collab:collab/collab-plugins/src/cloud_storage/sink.rs:283`.
Desarrollo: [[F06]]

### **ConnectState**  `[RED]`
Estado de la conexión websocket reported por el cliente de AppFlowy Cloud (`WSConnectStateReceiver`); es lo que `af_cloud` consume para saber si puede reintentar la subida de updates.
Evidencia: `appflowy/frontend/rust-lib/flowy-server/src/af_cloud/server.rs:12`, `appflowy/frontend/rust-lib/flowy-server/src/server.rs:1`.
Desarrollo: [[F06]]

### **Cubit**  `[UI]`
Variante de gestión de estado sin eventos, propia de `flutter_bloc`. Se usa para estado de interfaz de vida corta (selector de prompt de IA, lista de bases de datos relacionadas) donde un `Bloc` completo sería ruido.
Evidencia: `appflowy/frontend/appflowy_flutter/lib/ai/service/ai_prompt_selector_cubit.dart:19`, `appflowy/frontend/appflowy_flutter/lib/plugins/database/application/field/type_option/relation_type_option_cubit.dart:10`.
Desarrollo: [[13-catalogo-blocs]]

### **DatabaseEvent**  `[CATÁLOGO]`
Enum de eventos de `flowy-database2` (campos, filas, celdas, filtros, orden, grupos, cálculos, layout, exportación CSV y snapshots). Su `init` los registra todos contra el `DatabaseManager` compartido por referencia débil.
Evidencia: `appflowy/frontend/rust-lib/flowy-database2/src/event_map.rs:109`, `appflowy/frontend/rust-lib/flowy-database2/src/event_map.rs:12`.
Desarrollo: [[11-catalogo-eventos-ffi]]

### **Debounce (DebounceNotificationSender)**  `[PUENTE]`
Envolvente que agrupa notificaciones por clave `fuente-id-tipo`: al llegar una nueva cancela la tarea anterior mediante un `CancellationToken` y duerme `debounce_in_millis` antes de enviar. Sin ella, una ráfaga de ediciones generaría una notificación por pulsación.
Evidencia: `appflowy/frontend/rust-lib/flowy-notification/src/debounce.rs:8`, `appflowy/frontend/rust-lib/flowy-notification/src/debounce.rs:29`, `appflowy/frontend/rust-lib/flowy-notification/src/debounce.rs:44`.
Desarrollo: [[06-04-notificaciones]]

### **DeepLinkHandler**  `[PLAT]`
Contrato de manejador de enlaces profundos, con su registro (`DeepLinkHandlerRegistry`) y su resultado tipado (`DeepLinkResult<T>`). Cada esquema —login, invitación, pago, apertura de app— tiene su propia implementación.
Evidencia: `appflowy/frontend/appflowy_flutter/lib/startup/tasks/deeplink/deeplink_handler.dart:21`, `appflowy/frontend/appflowy_flutter/lib/startup/tasks/deeplink/deeplink_handler.dart:33`.
Desarrollo: [[F17]]

### **Deref**  `[PUENTE]`
Implementación de `std::ops::Deref` que da a los handlers acceso transparente a lo envuelto: `AFPluginData<T>` dereferencia al payload y `AFPluginState<T>` al `Arc<T>` del estado. No está implementado sobre `AFPluginRequest`, que es una estructura plana de campos privados.
Evidencia: `appflowy/frontend/rust-lib/lib-dispatch/src/data.rs:39`, `appflowy/frontend/rust-lib/lib-dispatch/src/module/data.rs:25`.
Desarrollo: [[06-02-lib-dispatch]]

### **Diesel**  `[PERSIST]`
ORM y gestor de migraciones del lado Rust; se usa como dependencia de workspace con características activas y es el que genera el cliente SQLite y el `schema.rs` de 16 tablas.
Evidencia: `appflowy/frontend/rust-lib/Cargo.toml:75`, `appflowy/frontend/rust-lib/flowy-sqlite/src/schema.rs:3`.
Desarrollo: [[08-01-sqlite-schema]]

### **DocumentData**  `[CRDT]`
Estructura en memoria del documento dentro del collab: bloques, mapa de hijos y mapa de texto. Es lo que el parser Rust produce y lo que `DocumentDataPB` serializa hacia Dart.
Evidencia: `collab:collab/collab-document/src/blocks/entities.rs:39`, `appflowy/frontend/rust-lib/flowy-document/src/entities.rs:202`.
Desarrollo: [[07-03-documento]]

### **DocumentEvent**  `[CATÁLOGO]`
Enum de eventos de `flowy-document` derivado con `Flowy_Event` y `ProtoBuf_Enum`, con `#[event_err = "FlowyError"]` como tipo de error. Cubre apertura, edición, snapshots, undo/redo, conversión y subida de archivos.
Evidencia: `appflowy/frontend/rust-lib/flowy-document/src/event_map.rs:57`, `appflowy/frontend/rust-lib/flowy-document/src/event_map.rs:59`.
Desarrollo: [[11-catalogo-eventos-ffi]]

### **DocumentManager**  `[MOTOR]`
Gestor Rust que cachea los documentos abiertos por `view_id` y coordina sus collabs. Cada `flowy-document` lo registra como estado débil del plugin, de modo que el dispatcher no mantiene ninguna referencia fuerte.
Evidencia: `appflowy/frontend/rust-lib/flowy-document/src/manager.rs:54`, `appflowy/frontend/rust-lib/flowy-document/src/event_map.rs:15`.
Desarrollo: [[F01.0.1]]

### **EncodedCollab**  `[CRDT]`
Representación serializada de un collab: bytes del documento `yrs` más el `StateVector` que losproduced, con `EncodedCollabV0` como formato heredado. Es la unidad que se persiste, se sincroniza y se devuelve en `GetDocEncodedCollab`.
Evidencia: `collab:collab/collab/src/entity.rs:6`, `collab:collab/collab/src/entity.rs:62`.
Desarrollo: [[07-01-modelo-collab]]

### **EncryptionTypePB**  `[SEG]`
Entidad protobuf que declara el cifrado en reposo elegido por el usuario. Hoy se documenta como parte del perfil (`NoEncryption` es el valor por defecto) y aparece referenciada en la vista de gestión de datos de Ajustes.
Evidencia: `appflowy/frontend/rust-lib/flowy-user/src/entities/user_profile.rs:49`, `appflowy/frontend/appflowy_flutter/lib/workspace/presentation/settings/pages/settings_manage_data_view.dart:226`.
Desarrollo: [[B6.3]]

### **ErrorCode**  `[CATÁLOGO]`
Enum `u8` de códigos de error de dominio, derivado con `ProtoBuf_Enum` y `Serialize_repr`, de modo que llega a Dart como enumeración protobuf. Es el contrato de error que el puente traduce a `FlowyError`.
Evidencia: `appflowy/frontend/rust-lib/flowy-error/src/code.rs:11`, `appflowy/frontend/rust-lib/flowy-error/src/code.rs:6`.
Desarrollo: [[15-catalogo-errores]]

### **FeatureFlag**  `[PLAT]`
Enum Dart de banderas de funcionalidad experimentales; `FeatureFlagTask` lo puebla al arrancar y la pantalla de Ajustes permite alternarlas. Es el interruptor que hoy protege partes del motor de importación/exportación y la IA local.
Evidencia: `appflowy/frontend/appflowy_flutter/lib/shared/feature_flags.dart:14`, `appflowy/frontend/appflowy_flutter/lib/startup/tasks/feature_flag_task.dart:6`.
Desarrollo: [[16-catalogo-flags-rutas-atajos]]

### **FFIRequest**  `[PUENTE]`
Cabecera en bytes que Dart entrega a `async_event`: lleva versión, `id`, nombre del evento y payload protobuf. `FFIRequest::from_u8_pointer` la reconstruye en el lado Rust.
Evidencia: `appflowy/frontend/rust-lib/dart-ffi/src/model/ffi_request.rs:7`, `appflowy/frontend/rust-lib/dart-ffi/src/lib.rs:176`.
Desarrollo: [[06-01-ffi]]

### **FFIResponse**  `[PUENTE]`
Respuesta simétrica que Rust devuelve al isolate: `FFIResponse::from(response)` serializa el `AFPluginEventResponse` y lo publica con `allo_isolate`. Si el isolate falla, el error se registra y no se propaga a Dart.
Evidencia: `appflowy/frontend/rust-lib/dart-ffi/src/model/ffi_response.rs:13`, `appflowy/frontend/rust-lib/dart-ffi/src/lib.rs:262`.
Desarrollo: [[06-01-ffi]]

### **FlowyError**  `[CATÁLOGO]`
Tipo de error de dominio de Rust, con constructor `FlowyError::internal()` y contexto encadenado (`with_context`). Todo handler declara `FlowyError` como tipo de error del evento y el puente lo traduce a la entidad protobuf de error.
Evidencia: `appflowy/frontend/rust-lib/flowy-error/src/errors.rs:17`, `appflowy/frontend/rust-lib/flowy-search/src/event_handler.rs:13`.
Desarrollo: [[15-catalogo-errores]]

### **FlowyEvent**  `[BUILD]`
Derive procedural (`#[proc_macro_derive(Flowy_Event, attributes(event, event_err))]`) que genera, a partir de un enum anotado, el nombre del evento, el `Display` y el glue entre `AFPlugin` y el handler.
Evidencia: `appflowy/frontend/rust-lib/build-tool/flowy-derive/src/lib.rs:32`.
Desarrollo: [[06-03-codegen]]

### **FlowyResult (Dart)**  `[CATÁLOGO]`
Resultado tipado del lado Dart, con `FlowySuccess` y `FlowyFailure` y los accesores `isSuccess`/`isFailure`. Es el tipo que devuelven los servicios Dart antes de convertir a entidades de dominio.
Evidencia: `appflowy/frontend/appflowy_flutter/packages/appflowy_result/lib/src/result.dart:1`, `appflowy/frontend/appflowy_flutter/packages/appflowy_result/lib/src/result.dart:13`.
Desarrollo: [[F00.5.3]]

### **FlowyResult (Rust)**  `[CATÁLOGO]`
Alias `Result<T, FlowyError>` usado en todos los handlers y managers. `anyhow` queda encapsulado detrás de este alias, de modo que el error que sale del puente es siempre tipado.
Evidencia: `appflowy/frontend/rust-lib/flowy-error/src/errors.rs:13`, `appflowy/frontend/rust-lib/flowy-search/src/event_handler.rs:3`.
Desarrollo: [[F00.2]]

### **FolderEvent**  `[CATÁLOGO]`
Enum de eventos del árbol de vistas: workspaces, CRUD de vistas, mover, papelera, favoritos, recientes, import, publicación y compartición. Su `init` nombra el plugin `Flowy-Folder` y lo registra contra `FolderManager`.
Evidencia: `appflowy/frontend/rust-lib/flowy-folder/src/event_map.rs:66`, `appflowy/frontend/rust-lib/flowy-folder/src/event_map.rs:12`.
Desarrollo: [[11-catalogo-eventos-ffi]]

### **FolderManager**  `[MOTOR]`
Gestor del árbol de vistas y de la papelera. Traduce cada `FolderEvent` a operaciones sobre el collab de carpeta y es el único que conoce la jerarquía padre-hijo.
Evidencia: `appflowy/frontend/rust-lib/flowy-folder/src/manager.rs:74`, `appflowy/frontend/rust-lib/flowy-folder/src/manager.rs:15`.
Desarrollo: [[F03.2]]

## 5. Glosario G–M

### **FileTempStorage**  `[PERSIST]`
Almacén de archivos temporales de subida: crea el directorio, copia o escribe el archivo a subir y lo borra cuando termina. Es el símbolo real que declara `appflowy/frontend/rust-lib/flowy-storage/src/file_cache.rs`; el nombre «FileCache» no aparece en el código.
Evidencia: `appflowy/frontend/rust-lib/flowy-storage/src/file_cache.rs:8`, `appflowy/frontend/rust-lib/flowy-storage/src/file_cache.rs:31`, `appflowy/frontend/rust-lib/flowy-storage/src/file_cache.rs:85`.
Desarrollo: [[08-04-file-cache]]

### **Generate (script de codegen)**  `[BUILD]`
Script bash que encadena la generación de iconos, `freezed` y ficheros de idioma antes de compilar Flutter. Los flags `--skip-pub-get` y `--skip-pub-packages-get` evitan resolver dependencias cuando el objetivo es sólo regenerar.
Evidencia: `appflowy/frontend/scripts/code_generation/generate.sh:1`, `appflowy/frontend/scripts/code_generation/generate.sh:13`.
Desarrollo: [[B6.1]]

### **GetIt**  `[UI]`
Contenedor de inyección de dependencias de Dart. `appflowy/frontend/appflowy_flutter/lib/startup/deps_resolver.dart` es el punto donde se registran `AuthService`, `EasyLocalizationService`, `AIRepository` y las factorías de BLoCs.
Evidencia: `appflowy/frontend/appflowy_flutter/lib/startup/deps_resolver.dart:42`, `appflowy/frontend/appflowy_flutter/lib/startup/deps_resolver.dart:65`.
Desarrollo: [[B1.4]]

### **GoRouter**  `[UI]`
Enrutador declarativo de Flutter. `generate_router` construye el árbol de rutas y `ApplicationWidget` lo guarda en `routerConfig`, evitando reconstruirlo cuando cambia el tema.
Evidencia: `appflowy/frontend/appflowy_flutter/lib/startup/tasks/generate_router.dart:46`, `appflowy/frontend/appflowy_flutter/lib/startup/tasks/app_widget.dart:146`.
Desarrollo: [[B1.4]]

### **Grid**  `[UI]`
Layout principal de una base de datos: `GridBloc` transforma el estado del `DatabaseController` en filas, columnas y opciones de edición visibles.
Evidencia: `appflowy/frontend/appflowy_flutter/lib/plugins/database/grid/application/grid_bloc.dart:22`.
Desarrollo: [[F02.9.0]]

### **HotKey**  `[PLAT]`
Atajo global de escritorio. `HotKeyItem` modela cada atajo y se registra sobre el `HotKeyManager` del paquete `hotkey_manager`; la lista completa está en `appflowy/frontend/appflowy_flutter/lib/workspace/presentation/home/hotkeys.dart`.
Evidencia: `appflowy/frontend/appflowy_flutter/lib/workspace/presentation/home/hotkeys.dart:42`, `appflowy/frontend/appflowy_flutter/lib/workspace/presentation/home/hotkeys.dart:35`.
Desarrollo: [[16-catalogo-flags-rutas-atajos]]

### **HotKeyManager**  `[PLAT]`
Servicio del paquete `hotkey_manager` que captura combinaciones de teclas del sistema. AppFlowy lo inicializa como `HotKeyTask` durante el arranque y lo consume tanto en el home como en la barra lateral.
Evidencia: `appflowy/frontend/appflowy_flutter/lib/startup/tasks/hot_key.dart:1`, `appflowy/frontend/appflowy_flutter/lib/startup/tasks/hot_key.dart:6`.
Desarrollo: [[F17]]

### **i18n (EasyLocalization)**  `[UI]`
Capa de localización: `EasyLocalizationService` envuelve `EasyLocalization` y centraliza la carga de bundles y el cambio de idioma; se registra como singleton en el contenedor de dependencias.
Evidencia: `appflowy/frontend/appflowy_flutter/lib/shared/easy_localiation_service.dart:6`, `appflowy/frontend/appflowy_flutter/lib/startup/deps_resolver.dart:103`.
Desarrollo: [[F14]]

### **IndexedData (indexación)**  `[MOTOR]`
Infraestructura que mantiene una vista indexada de los datos para búsqueda y embeddings: `FullIndexedDataWriter` en `flowy-core` y `InstantIndexedDataWriter` en `collab-integrate`, con un consumidor aparte que lee de esa vista.
Evidencia: `appflowy/frontend/rust-lib/flowy-core/src/indexing_data_runner.rs:2`, `appflowy/frontend/rust-lib/collab-integrate/src/collab_builder.rs:36`, `appflowy/frontend/rust-lib/flowy-core/src/indexed_data_consumer.rs:2`.
Desarrollo: [[F08]]

### **InitRustSDKTask**  `[MOTOR]`
Tarea de arranque que invoca `init_sdk` con la configuración serializada desde Dart y espera a que el core Rust quede disponible antes de continuar con el resto de tareas.
Evidencia: `appflowy/frontend/appflowy_flutter/lib/startup/tasks/rust_sdk.dart:13`, `appflowy/frontend/appflowy_flutter/lib/startup/tasks/rust_sdk.dart:18`.
Desarrollo: [[B5.1]]

### **KVStore**  `[PERSIST]`
Trait de acceso clave-valor sobre el que se implementa toda la persistencia de collabs. `CollabKVAction` lo extiende con operaciones de documento (cargar y guardar el `Collab` codificado) y es lo que permite que el mismo código sirva a RocksDB en nativo e IndexedDB en web.
Evidencia: `collab:collab/collab-plugins/src/local_storage/kv/db.rs:34`, `collab:collab/collab-plugins/src/local_storage/kv/doc.rs:12`.
Desarrollo: [[08-02-kv]]

### **KVStorePreferences**  `[PERSIST]`
Preferencias tipadas del KV store de la sesión de usuario (token, configuración cloud, ruta de datos). `flowy-user` las lee y escribe desde varios servicios, por lo que es el punto de encuentro entre sesión y disco.
Evidencia: `appflowy/frontend/rust-lib/flowy-sqlite/src/kv/kv.rs:17`, `appflowy/frontend/rust-lib/flowy-user/src/services/cloud_config.rs:4`.
Desarrollo: [[08-02-kv]]

### **LaunchTask**  `[MOTOR]`
Unidad de trabajo del arranque Dart: cada tarea (`InitRustSDKTask`, `HotKeyTask`, `AutoUpdateTask`, `InitAppWidgetTask`) implementa este contrato y se ejecuta según su `LaunchTaskType`.
Evidencia: `appflowy/frontend/appflowy_flutter/lib/startup/startup.dart:218`, `appflowy/frontend/appflowy_flutter/lib/startup/tasks/app_widget.dart:41`, `appflowy/frontend/appflowy_flutter/lib/startup/tasks/app_widget.dart:45`.
Desarrollo: [[B1.4]]

### **LazyLock**  `[PERSIST]`
Primitiva de inicialización perezosa usada como estático global en la capa de migraciones de `flowy-sqlite-vec`: el directorio de migraciones embebido se resuelve una sola vez.
Evidencia: `appflowy/frontend/rust-lib/flowy-sqlite-vec/src/migration.rs:5`, `appflowy/frontend/rust-lib/flowy-sqlite-vec/src/migration.rs:7`.
Desarrollo: [[08-05-sqlite-vec]]

### **LocalServer**  `[MOTOR]`
Implementación de servidor que opera contra el propio disco, sin red. Se usa cuando `AuthType` es local y es la que sirve de contrato de referencia frente a `af_cloud`.
Evidencia: `appflowy/frontend/rust-lib/flowy-server/src/local_server/server.rs:2`.
Desarrollo: [[F06]]

### **LocalStorage (plugin de collab)**  `[PERSIST]`
Módulo de `collab-plugins` que agrupa las implementaciones de disco: `rocksdb` en nativo e `indexeddb` en wasm, más la configuración de almacenamiento compartida.
Evidencia: `collab:collab/collab-plugins/src/local_storage/mod.rs:1`, `collab:collab/collab-plugins/src/local_storage/mod.rs:11`.
Desarrollo: [[08-03-collab-db]]

### **Log (Dart)**  `[MOTOR]`
Envoltorio Dart de logging con niveles `info`/`debug`/`warn`; los errores de deserialización del `RustStreamReceiver` se reportan por aquí antes de relanzarse.
Evidencia: `appflowy/frontend/appflowy_flutter/packages/appflowy_backend/lib/log.dart:10`, `appflowy/frontend/appflowy_flutter/packages/appflowy_backend/lib/log.dart:44`.
Desarrollo: [[F00.5.1]]

### **Log filter**  `[MOTOR]`
Mecanismo de `flowy-core` que enciende o apaga la traza por crate en tiempo de ejecución (`flowy_sqlite_vec=` y compañía), en lugar de depender solo de `RUST_LOG`.
Evidencia: `appflowy/frontend/rust-lib/flowy-core/src/log_filter.rs:65`.
Desarrollo: [[F17]]

### **Manager**  `[MOTOR]`
Convención de nombres para el gestor Rust de cada módulo (`DocumentManager`, `FolderManager`, `DatabaseManager`, `UserManager`, `SearchManager`). Todos se registran como `Weak<XManager>` en su `AFPlugin`, de modo que el dispatcher no los mantiene vivos.
Evidencia: `appflowy/frontend/rust-lib/flowy-database2/src/manager.rs:56`, `appflowy/frontend/rust-lib/flowy-user/src/user_manager/manager.rs:45`, `appflowy/frontend/rust-lib/flowy-search/src/services/manager.rs:42`.
Desarrollo: [[B1.3]]

### **MCPClient**  `[IA]`
Cliente de Model Context Protocol que `flowy-ai` usa para hablar con servidores de herramientas externas. La configuración de cada servidor viaja como `MCPServerConfig` dentro de `appflowy/frontend/rust-lib/flowy-ai/src/mcp/manager.rs`.
Evidencia: `appflowy/frontend/rust-lib/flowy-ai/src/mcp/manager.rs:1`.
Desarrollo: [[F09.1]]

### **Merge**  `[CRDT]`
Resolución automática de conflictos: una `Update` entrante se aplica dentro de una transacción (`try_apply_update`) y `yrs` decide el orden. El sync de nube marca los mensajes como `mergeable` para que el servidor acepte Fusionarlos.
Evidencia: `collab:collab/collab-plugins/src/local_storage/kv/doc.rs:97`, `collab:collab/collab-plugins/src/cloud_storage/remote_collab.rs:96`, `collab:collab/collab-plugins/src/cloud_storage/msg.rs:16`.
Desarrollo: [[07-07-snapshots-conflict-resolution]]

### **Middleware (chat)**  `[IA]`
Capa que envuelve la llamada de chat antes de llegar al proveedor. `chat.rs` la inyecta como dependencia del struct de servicio, lo que permite añadir RAG, prompts y control de modelo sin tocar el cliente.
Evidencia: `appflowy/frontend/rust-lib/flowy-ai/src/chat.rs:5`, `appflowy/frontend/rust-lib/flowy-ai/src/chat.rs:266`.
Desarrollo: [[F09.1]]

### **MoveWindowDetector**  `[PLAT]`
Widget que convierte una zona de arrastre de la ventana en movimiento de ventana nativo. Es la pieza que hace posible la interfaz sin marco de escritorio.
Evidencia: `appflowy/frontend/appflowy_flutter/lib/core/frameless_window.dart:29`, `appflowy/frontend/appflowy_flutter/lib/core/frameless_window.dart:41`.
Desarrollo: [[F17]]

## 6. Glosario N–S

### **Nanoid**  `[PUENTE]`
Generador de identificadores cortos usado para el `id` de cada petición FFI, de modo que logs de Rust y Dart puedan correlacionarse sin un contador global.
Evidencia: `appflowy/frontend/rust-lib/lib-dispatch/src/module/module.rs:14`, `appflowy/frontend/rust-lib/lib-dispatch/src/module/module.rs:153`.
Desarrollo: [[06-02-lib-dispatch]]

### **NotificationBuilder**  `[PUENTE]`
Constructor de la notificación que Rust envía a Dart: compone `SubscribeObject` con `id`, tipo y origen, y adjunta el payload protobuf.
Evidencia: `appflowy/frontend/rust-lib/flowy-notification/src/builder.rs:6`, `appflowy/frontend/rust-lib/flowy-notification/src/debounce.rs:22`.
Desarrollo: [[06-04-notificaciones]]

### **NotificationSender**  `[PUENTE]`
Trait de salida de notificaciones con registro global en un `RwLock<Vec<Box<dyn NotificationSender>>>`. `set_stream_port` limpia los emisores previos antes de registrar el de Dart, porque el hot reload registraría duplicados.
Evidencia: `appflowy/frontend/rust-lib/flowy-notification/src/lib.rs:37`, `appflowy/frontend/rust-lib/flowy-notification/src/lib.rs:15`, `appflowy/frontend/rust-lib/dart-ffi/src/lib.rs:241`.
Desarrollo: [[14-catalogo-notificaciones]]

### **OauthProvider**  `[AUT]`
Entidad protobuf del proveedor OAuth (Google, GitHub, Discord…) usada por `OauthSignIn` y `GetOauthURLWithProvider`; la respuesta correspondiente es `OauthProviderDataPB`.
Evidencia: `appflowy/frontend/rust-lib/flowy-user/src/entities/auth.rs:166`, `appflowy/frontend/rust-lib/flowy-user/src/entities/auth.rs:226`, `appflowy/frontend/rust-lib/flowy-user/src/event_map.rs:136`.
Desarrollo: [[F05.1]]

### **Ollama**  `[IA]`
Motor de IA local sobre el que se construyen embeddings y completaciones sin salir del dispositivo. `AIManager` recarga el cliente cuando cambia el workspace y `model_select` consulta los modelos disponibles.
Evidencia: `appflowy/frontend/rust-lib/flowy-ai/src/model_select.rs:306`, `appflowy/frontend/rust-lib/flowy-ai/src/ai_manager.rs:159`, `appflowy/frontend/rust-lib/Cargo.toml:87`.
Desarrollo: [[F09.1]]

### **Payload**  `[PUENTE]`
Variante `None | Bytes` que transporta el cuerpo del evento dentro de la petición. `AFPluginData::from_request` la convierte en entidad tipada y devuelve `UnexpectedNone` cuando el evento no declara payload.
Evidencia: `appflowy/frontend/rust-lib/lib-dispatch/src/request/payload.rs:7`, `appflowy/frontend/rust-lib/lib-dispatch/src/data.rs:73`.
Desarrollo: [[06-02-lib-dispatch]]

### **PB**  `[CATÁLOGO]`
Sufijo que marca una entidad protobuf en Rust, con su derive `ProtoBuf`. Es la convención que permite a `flowy-codegen` emitirlas y a `AFPluginData<T>` deserializarlas. `PB` es la clave con la que se ordenan las entradas de este glosario.
Evidencia: `appflowy/frontend/rust-lib/flowy-database2/src/entities/cell_entities.rs:11`, `appflowy/frontend/rust-lib/build-tool/flowy-derive/src/lib.rs:16`.
Desarrollo: [[12-catalogo-entidades-protobuf]]

### **ProtoBuf_Enum**  `[BUILD]`
Derive procedural (`#[proc_macro_derive(ProtoBuf, attributes(pb))]` y su variante de enum) que genera la definición `.proto` y la enumeración Dart correspondiente. Es lo que hace que `ErrorCode`, `FolderEvent` o `ViewLayoutPB` existan en ambos lenguajes sin código escrito a mano.
Evidencia: `appflowy/frontend/rust-lib/build-tool/flowy-derive/src/lib.rs:16`, `appflowy/frontend/rust-lib/flowy-error/src/code.rs:6`.
Desarrollo: [[06-03-codegen]]

### **Publish**  `[CATÁLOGO]`
Publicación web de una vista. El conjunto de eventos (`PublishView`, `SetPublishName`, `SetPublishNamespace`, `ListPublishedViews`, `RemoveDefaultPublishView`) está en `flowy-folder`, y el nombre público se genera en `publish_util`.
Evidencia: `appflowy/frontend/rust-lib/flowy-folder/src/event_map.rs:45`, `appflowy/frontend/rust-lib/flowy-folder/src/event_map.rs:52`, `appflowy/frontend/rust-lib/flowy-folder/src/lib.rs:15`.
Desarrollo: [[B4.12]]

### **PublishInfoViewPB**  `[CATÁLOGO]`
Entidad protobuf con los datos de publicación de una vista (nombre público, namespace y visited). Es lo que `ShareBloc` consume para pintar el estado publicado en la UI.
Evidencia: `appflowy/frontend/rust-lib/flowy-folder/src/entities/publish.rs:26`, `appflowy/frontend/rust-lib/flowy-folder/src/manager.rs:15`.
Desarrollo: [[F12.2]]

### **PushRealtimeEvent**  `[RED]`
Evento de `flowy-user` que reenvía al servidor una acción en tiempo real (por ejemplo cambiar la visibilidad de una vista) sin pasar por el ciclo completo de guardado.
Evidencia: `appflowy/frontend/rust-lib/flowy-user/src/event_map.rs:47`.
Desarrollo: [[F06]]

### **Reminder**  `[CATÁLOGO]`
Recordatorio asociado a un bloque de documento. El modelo CRDT es `Reminder` en `collab-entity` y su reflejo por el puente es `ReminderPB`; los eventos `CreateReminder`, `GetAllReminders`, `UpdateReminder` y `RemoveReminder` lo gestionan.
Evidencia: `collab:collab/collab-entity/src/reminder.rs:11`, `appflowy/frontend/rust-lib/flowy-user/src/entities/reminder.rs:6`, `appflowy/frontend/rust-lib/flowy-user/src/event_map.rs:48`.
Desarrollo: [[F15.2]]

### **Reminders**  `[CRDT]`
Colección CRDT de recordatorios de un documento (`Reminders` en `collab-user`), que se actualiza dentro de una transacción `yrs` cuando un recordatorio cambia o se inserta una mención con fecha.
Evidencia: `collab:collab/collab-user/src/reminder.rs:23`, `collab:collab/collab-user/src/reminder.rs:6`.
Desarrollo: [[07-05-user-awareness]]

### **Repository**  `[UI]`
Capa de acceso a datos de la arquitectura nueva por feature (`features/<x>/data/repositories/`), con implementaciones `Rust…RepositoryImpl`. Convive con los BLoCs de `plugins/` y `workspace/`, y `AIRepository` es su caso más simple.
Evidencia: `appflowy/frontend/appflowy_flutter/lib/features/shared_section/presentation/shared_section.dart:37`, `appflowy/frontend/appflowy_flutter/lib/ai/service/appflowy_ai_service.dart:27`, `appflowy/frontend/appflowy_flutter/lib/startup/deps_resolver.dart:65`.
Desarrollo: [[B1.3]]

### **Retry**  `[RED]`
Reintento de operaciones de red. El `FileUploader` lleva un contador (`retry_count`) que se reinicia al encolar y se fija a tres cuando se programa el reintento, de modo que un archivo fallido no se pierde entre reinicios.
Evidencia: `appflowy/frontend/rust-lib/flowy-storage/src/manager.rs:251`, `appflowy/frontend/rust-lib/flowy-storage/src/manager.rs:412`.
Desarrollo: [[B5.13]]

### **Row**  `[CATÁLOGO]`
Fila de una base de datos. Los eventos `CreateRow`, `GetRow`, `InitRow`, `GetRowMeta`, `UpdateRowMeta`, `DeleteRows`, `DuplicateRow` y `MoveRow` la gestionan; su metadato persistente es `RowMetaPB`.
Evidencia: `appflowy/frontend/rust-lib/flowy-database2/src/event_map.rs:33`, `appflowy/frontend/rust-lib/flowy-database2/src/entities/row_entities.rs:57`.
Desarrollo: [[F02.3]]

### **RowMeta**  `[CRDT]`
Estructura de metadatos de fila (`RowMetaUpdate`) dentro del collab de base de datos: altura, collapsed y fecha de creación, que el CRDT debe poder fusionar sin intervención.
Evidencia: `collab:collab/collab-database/src/rows/row_meta.rs:11`.
Desarrollo: [[07-04-database]]

### **RustStreamReceiver**  `[PUENTE]`
Extremo Dart del canal de notificaciones. Mantiene un `RawReceivePort`, deserializa cada mensaje en un `SubscribeObject` y lo reparte por un `StreamController.broadcast`, al que se suscriben todos los listeners.
Evidencia: `appflowy/frontend/appflowy_flutter/packages/appflowy_backend/lib/rust_stream.dart:11`, `appflowy/frontend/appflowy_flutter/packages/appflowy_backend/lib/rust_stream.dart:34`, `appflowy/frontend/appflowy_flutter/packages/appflowy_backend/lib/rust_stream.dart:41`.
Desarrollo: [[06-04-notificaciones]]

### **SearchManager**  `[MOTOR]`
Gestor de búsqueda full-text: mantiene el índice `tantivy`, genera un `search_id` (el timestamp si no viene en la consulta) y publica los resultados por el puerto de streaming de la consulta.
Evidencia: `appflowy/frontend/rust-lib/flowy-search/src/services/manager.rs:42`, `appflowy/frontend/rust-lib/flowy-search/src/event_handler.rs:24`, `appflowy/frontend/rust-lib/flowy-search/src/event_handler.rs:31`.
Desarrollo: [[F08]]

### **SearchQueryPB**  `[CATÁLOGO]`
Entidad protobuf de la consulta de búsqueda: texto, `search_id` y `stream_port`. Si el texto viene vacío, el handler aborta antes de tocar el índice.
Evidencia: `appflowy/frontend/rust-lib/flowy-search/src/entities/query.rs:4`, `appflowy/frontend/rust-lib/flowy-search/src/event_handler.rs:27`.
Desarrollo: [[12-catalogo-entidades-protobuf]]

### **SelectOption**  `[CATÁLOGO]`
Opción de un campo de selección simple o múltiple, con su color e identidad estable. El CRDT la declara en `collab-database` y el puente la expone como `SelectOptionPB`.
Evidencia: `collab:collab/collab-database/src/fields/type_option/select_type_option.rs:98`, `appflowy/frontend/rust-lib/flowy-database2/src/entities/type_option_entities/select_option_entities.rs:12`.
Desarrollo: [[F02.1]]

### **ShareBloc**  `[UI]`
BLoC de la pestaña de compartir: reúne el estado de publicación, la vista seleccionada, la compartición por enlace y el nombre de ruta. Es el ejemplo canónico de BLoC generado con Freezed.
Evidencia: `appflowy/frontend/appflowy_flutter/lib/plugins/shared/share/share_bloc.dart:23`, `appflowy/frontend/appflowy_flutter/lib/plugins/shared/share/share_bloc.dart:26`, `appflowy/frontend/appflowy_flutter/lib/plugins/shared/share/share_bloc.dart:29`.
Desarrollo: [[F12.1]]

### **SharedPage**  `[CATÁLOGO]`
Página compartida con otro usuario. Los eventos correspondientes son `SharePageWithUser`, `RemoveUserFromSharedPage`, `GetSharedUsers`, `GetSharedViews` y `GetSharedViewSection`.
Evidencia: `appflowy/frontend/rust-lib/flowy-folder/src/event_map.rs:57`, `appflowy/frontend/rust-lib/flowy-folder/src/event_map.rs:61`.
Desarrollo: [[F12.2]]

### **Snapshot**  `[CRDT]`
Estado serializado e inmutable de un documento en un instante, con su metadato (`DocumentSnapshotMetaPB` y `DocumentSnapshotMeta`). Sirve para historial y recuperación, y su lectura va por el evento `GetDocumentSnapshot`.
Evidencia: `appflowy/frontend/rust-lib/flowy-document/src/entities.rs:462`, `appflowy/frontend/rust-lib/flowy-document/src/event_map.rs:122`, `appflowy/frontend/rust-lib/flowy-core/src/deps_resolve/collab_deps.rs:17`.
Desarrollo: [[07-07-snapshots-conflict-resolution]]

### **Space**  `[CRDT]`
Agrupación de vistas en la barra lateral. En el código no existe un tipo `Space`: el concepto está implementado como `SectionMap`, `SectionItem` y su entidad de transporte `SectionViewsPB`. Es la ampliación del término de `AGENTS.md` §12 al símbolo real.
Evidencia: `collab:collab/collab-folder/src/section.rs:13`, `collab:collab/collab-folder/src/section.rs:305`, `appflowy/frontend/rust-lib/flowy-folder/src/entities/view.rs:231`.
Desarrollo: [[07-02-folder]]

### **SQLite**  `[PERSIST]`
Base de datos local que almacena el esquema de dominio (workspaces, vistas, ajustes, metadatos de base de datos) y, en web, los collabs vía IndexedDB. Diesel gestiona el esquema y `embed_migrations!` incrusta las migraciones en el binario.
Evidencia: `appflowy/frontend/rust-lib/flowy-sqlite/src/lib.rs:29`, `appflowy/frontend/rust-lib/flowy-sqlite/src/schema.rs:3`.
Desarrollo: [[08-01-sqlite-schema]]

### **Stream port**  `[PUENTE]`
Puerto de isolate por el que Rust devuelve respuestas y resultados de streaming (búsqueda, chat con tokens). `post_to_flutter` lo encapsula en un `Isolate` de `allo_isolate` y aísla los panics con `catch_unwind`.
Evidencia: `appflowy/frontend/rust-lib/dart-ffi/src/lib.rs:259`, `appflowy/frontend/rust-lib/dart-ffi/src/lib.rs:261`, `appflowy/frontend/rust-lib/flowy-search/src/event_handler.rs:33`.
Desarrollo: [[06-01-ffi]]

### **SubscribeObject**  `[PUENTE]`
Mensaje de notificación ya serializado, con `source`, `id` y `ty` más el payload. Es la unidad que cruza de Rust a Dart y la clave con la que el debounce agrupa ráfagas.
Evidencia: `appflowy/frontend/rust-lib/flowy-notification/src/entities/subject.rs:6`, `appflowy/frontend/rust-lib/flowy-notification/src/debounce.rs:29`, `appflowy/frontend/appflowy_flutter/packages/appflowy_backend/lib/rust_stream.dart:7`.
Desarrollo: [[14-catalogo-notificaciones]]

### **Sync (plugin de nube)**  `[RED]`
Replicación de los updates de un collab contra el servidor. El plugin de tipo `CloudStorage` es único por documento y usa `CollabConnectState` más `CollabSink` para decidir si envía ahora o reencola.
Evidencia: `collab:collab/collab/src/core/collab_plugin.rs:17`, `collab:collab/collab-plugins/src/connect_state.rs:6`, `collab:collab/collab-plugins/src/cloud_storage/sink.rs:34`.
Desarrollo: [[F06]]

### **Sync event**  `[PUENTE]`
Función `extern "C" sync_event` reservada para el camino síncrono. En el snapshot actual está sin implementar y devuelve error de forma explícita, junto con un buffer vacío.
Evidencia: `appflowy/frontend/rust-lib/dart-ffi/src/lib.rs:231`, `appflowy/frontend/rust-lib/dart-ffi/src/lib.rs:232`.
Desarrollo: [[06-01-ffi]]

## 7. Glosario T–Z

### **Tantivy**  `[CATÁLOGO]`
Motor de búsqueda full-text sobre el que se apoya la búsqueda de AppFlowy; se declara como dependencia de workspace y se aísla en el crate `flowy-search-pub` para que `flowy-error` pueda convertir sus errores sin dependencia directa.
Evidencia: `appflowy/frontend/rust-lib/Cargo.toml:104`, `appflowy/frontend/rust-lib/flowy-error/Cargo.toml:36`.
Desarrollo: [[F08]]

### **Task (FFI)**  `[PUENTE]`
Unidad de trabajo encolable que cruza el hilo del runtime: lleva el dispatcher, la petición, el puerto de respuesta y un canal opcional de retorno síncrono. `Runner` la consume y lanza un `spawn_local` por tarea.
Evidencia: `appflowy/frontend/rust-lib/dart-ffi/src/lib.rs:45`, `appflowy/frontend/rust-lib/dart-ffi/src/lib.rs:96`, `appflowy/frontend/rust-lib/dart-ffi/src/lib.rs:208`.
Desarrollo: [[06-01-ffi]]

### **TrackedCollab**  `[CRDT]`
Término conceptual que aparece en la documentación histórica pero **no corresponde a ningún tipo en este snapshot**: el seguimiento de cambios lo aporta `CollabPlugin` con su ciclo de notificaciones. Se incluye aquí para evitar que se busque un símbolo inexistente.
Evidencia: `collab:collab/collab/src/core/collab_plugin.rs:49`, `collab:collab/collab/src/core/collab.rs:53`.
Desarrollo: [[07-06-collab-plugins]]

### **Transaction (yrs)**  `[CRDT]`
Transacción mutable sobre el documento `yrs`; es el contexto dentro del cual se aplican updates, se serializa el estado y se emiten los eventos del plugin.
Evidencia: `collab:collab/collab-plugins/src/local_storage/kv/doc.rs:10`, `collab:collab/collab-plugins/src/local_storage/kv/db.rs:11`.
Desarrollo: [[07-01-modelo-collab]]

### **TransactionMutExt**  `[CRDT]`
Extensión de `TransactionMut` que `collab-plugins` añade para convertir transactions en `EncodedCollab` sin repetir la lógica de codificación en cada plugin.
Evidencia: `collab:collab/collab-plugins/src/cloud_storage/remote_collab.rs:9`.
Desarrollo: [[07-06-collab-plugins]]

### **Update**  `[CRDT]`
Incremento CRDT serializado que un cliente envía a los demás. Se aplica con `try_apply_update` dentro de una transacción, tanto al leer de disco como al recibir del servidor.
Evidencia: `collab:collab/collab-plugins/src/local_storage/kv/doc.rs:10`, `collab:collab/collab-plugins/src/cloud_storage/remote_collab.rs:96`, `collab:collab/collab-folder/src/folder_diff.rs:83`.
Desarrollo: [[07-07-snapshots-conflict-resolution]]

### **UploadTask**  `[MOTOR]`
Tarea de subida encolada por `FileUploader` (`Signal`, `UploadTaskQueue` y el propio enum), con estado propio para poder reanudar tras un fallo sin repetir el trabajo ya hecho.
Evidencia: `appflowy/frontend/rust-lib/flowy-storage/src/uploader.rs:298`, `appflowy/frontend/rust-lib/flowy-storage/src/uploader.rs:21`, `appflowy/frontend/rust-lib/flowy-storage/src/uploader.rs:252`.
Desarrollo: [[F07]]

### **UserAwareness**  `[CRDT]`
Estado de presencia de un usuario dentro de un documento: cursor, selección y metadatos de colaboración, sobre el `Awareness` de `yrs`. Es lo que alimenta los cursores de los colaboradores en el editor.
Evidencia: `collab:collab/collab-user/src/user_awareness.rs:19`, `collab:collab/collab-document/src/document_awareness.rs:1`, `appflowy/frontend/rust-lib/flowy-document/src/event_map.rs:132`.
Desarrollo: [[07-05-user-awareness]]

### **UserEvent**  `[CATÁLOGO]`
Enum de eventos de `flowy-user`: autenticación (email, magic link, OAuth, passcode, anónimo), perfil, ajustes de apariencia, workspaces, invitaciones, facturación, red y recordatorios. Su `init` registra dos estados: el manager y las preferencias.
Evidencia: `appflowy/frontend/rust-lib/flowy-user/src/event_map.rs:86`, `appflowy/frontend/rust-lib/flowy-user/src/event_map.rs:88`, `appflowy/frontend/rust-lib/flowy-user/src/event_map.rs:25`.
Desarrollo: [[11-catalogo-eventos-ffi]]

### **UserManager**  `[MOTOR]`
Gestor de sesión y workspaces:cachea el usuario actual, expone las preferencias de almacenamiento y coordina login, logout y cambio de workspace.
Evidencia: `appflowy/frontend/rust-lib/flowy-user/src/user_manager/manager.rs:45`, `appflowy/frontend/rust-lib/flowy-user/src/user_manager/manager.rs:754`.
Desarrollo: [[F05.2]]

### **UserTokenPB**  `[SEG]`
Entidad protobuf con el token de sesión del usuario; es lo que se guarda en las preferencias del KV store y lo que `SignInWithEmailPassword` deja disponible tras autenticar.
Evidencia: `appflowy/frontend/rust-lib/flowy-user/src/entities/user_profile.rs:13`, `appflowy/frontend/rust-lib/flowy-user/src/services/authenticate_user.rs:10`.
Desarrollo: [[B6.3]]

### **UUID**  `[MOTOR]`
Identificador de 128 bits usado para recursos de servidor (workspaces, invitaciones). `flowy-user` lo importa directamente, a diferencia del `nanoid` del puente FFI, que es deliberadamente corto.
Evidencia: `appflowy/frontend/rust-lib/flowy-user/src/event_map.rs:10`.
Desarrollo: [[F05.2]]

### **VectorSqliteDB**  `[PERSIST]`
Base de datos vectorial sobre la extensión `sqlite-vec`: guarda embeddings de fragmentos y documentos, y ofrece búsqueda con y sin puntuación. `init_sqlite_vector_extension` carga la extensión antes de usarla.
Evidencia: `appflowy/frontend/rust-lib/flowy-sqlite-vec/src/db.rs:18`, `appflowy/frontend/rust-lib/flowy-sqlite-vec/src/lib.rs:9`, `appflowy/frontend/rust-lib/flowy-sqlite-vec/src/db.rs:391`.
Desarrollo: [[08-05-sqlite-vec]]

### **View**  `[CRDT]`
Nodo del árbol del folder: documento, grid, board, calendar o chat. En el CRDT es `View` con su `ViewLayout`, y en el puente su entidad `ViewPB` y su layout `ViewLayoutPB`.
Evidencia: `collab:collab/collab-folder/src/view.rs:834`, `appflowy/frontend/rust-lib/flowy-folder/src/entities/view.rs:188`, `appflowy/frontend/rust-lib/flowy-folder/src/event_map.rs:19`.
Desarrollo: [[07-02-folder]]

### **ViewLayout**  `[CATÁLOGO]`
Tipo de contenido de una vista. El enum del CRDT (`ViewLayout`) y el del puente (`ViewLayoutPB`) se mantienen en paralelo y se convierten uno en otro al cruzar el FFI.
Evidencia: `collab:collab/collab-folder/src/view.rs:834`, `appflowy/frontend/rust-lib/flowy-folder/src/entities/view.rs:188`.
Desarrollo: [[12-catalogo-entidades-protobuf]]

### **ViewListener**  `[UI]`
Suscripción Dart a las notificaciones de una vista concreta (`onViewUpdated`, `onViewMoveToTrash`). `ShareBloc` la usa para reaccionar a cambios de nombre y para despublicar cuando la vista va a la papelera.
Evidencia: `appflowy/frontend/appflowy_flutter/lib/workspace/application/view/view_listener.dart:22`, `appflowy/frontend/appflowy_flutter/lib/plugins/shared/share/share_bloc.dart:30`.
Desarrollo: [[F03.1]]

### **white_label**  `[BUILD]`
Personalización de marca por plataforma: scripts que sustituyen iconos, nombres y tipografías antes de empaquetar. El script raíz delega por sistema operativo y los bloques generados se delimitan con marcadores en el `pubspec.yaml`.
Evidencia: `appflowy/frontend/scripts/white_label/white_label.sh:105`, `appflowy/frontend/scripts/white_label/font_white_label.sh:89`, `appflowy/frontend/appflowy_flutter/pubspec.yaml:288`.
Desarrollo: [[B6.1]]

### **Workspace**  `[CRDT]`
Agrupeación raíz de vistas. En el CRDT es `Workspace` dentro de `collab-folder`; los eventos que la gestionan son `ReadCurrentWorkspace`, `CreateWorkspace`, `DeleteWorkspace`, `RenameWorkspace` y `LeaveWorkspace`.
Evidencia: `collab:collab/collab-folder/src/workspace.rs:6`, `appflowy/frontend/rust-lib/flowy-user/src/event_map.rs:62`, `appflowy/frontend/rust-lib/flowy-user/src/event_map.rs:67`.
Desarrollo: [[07-02-folder]]

### **WSClient / WSClientConfig**  `[RED]`
Cliente websocket de AppFlowy Cloud y su configuración. `af_cloud` los combina con `WebSocketChannel` y `WSConnectStateReceiver` para gestionar el ciclo de conexión y la recepción de mensajes.
Evidencia: `appflowy/frontend/rust-lib/flowy-server/src/af_cloud/server.rs:12`.
Desarrollo: [[F06]]

### **yrs**  `[CRDT]`
Motor CRDT sobre el que está construido todo `collab`: provee `Doc`, `TransactionMut`, `Update`, `Awareness`, `StateVector` y los tipos reexportados en el `prelude` de `collab` (que incluye `YrsInput`, `YrsValue` y `YrsDelta` para no colisionar con `std::io`).
Evidencia: `appflowy/frontend/rust-lib/Cargo.toml:98`, `collab:collab/collab/Cargo.toml:23`, `collab:collab/collab/src/lib.rs:26`.
Desarrollo: [[07-01-modelo-collab]]

### **ZipFileReader**  `[MOTOR]`
Lector de ZIP en streaming (`async_zip`) que usa el importador para abrir paquetes de Notion, exportaciones y copias de AppFlowy sin cargar el archivo entero en memoria.
Evidencia: `collab:collab/collab-importer/src/util.rs:4`, `collab:collab/collab-importer/src/zip_tool/util.rs:25`.
Desarrollo: [[B4.11]]

## 8. Relacionado con

- `OUT/00-INDEX.md` — índice general de la skill; punto de entrada para quien no sepa por dónde empezar.
- `OUT/02-stack-y-dependencias.md` y `OUT/03-estructura-del-repo.md` — origen de los términos de crate, directorio y dependencia que aquí se condensan.
- `OUT/04-arquitectura-global.md` y `OUT/05-arranque-y-ciclo-de-vida.md` — capas y tareas de arranque (`LaunchTask`, `GetIt`, `AppFlowyCore`).
- `OUT/06-puente-flutter-rust/` — desarrollo completo de `AFPlugin`, `AFPluginRequest`, `async_event`, `NotificationBuilder` y `RustStreamReceiver`.
- `OUT/07-motor-colaborativo-crdt/` — desarrollo de `Collab`, `EncodedCollab`, `CollabPlugin`, `Space`, `View` y resolución de conflictos.
- `OUT/08-persistencia/` — desarrollo de `SQLite`, `KVStore`, `VectorSqliteDB` y `FileTempStorage`.
- `OUT/09-features/` — una unidad por feature, donde cada término de UI, IA, base de datos o plataforma encuentra su contexto de producto.
- `OUT/11-catalogo-eventos-ffi.md`, `OUT/12-catalogo-entidades-protobuf.md`, `OUT/13-catalogo-blocs.md`, `OUT/14-catalogo-notificaciones.md`, `OUT/15-catalogo-errores.md`, `OUT/16-catalogo-flags-rutas-atajos.md` — listados extensos de los `PB`, eventos, BLoCs, notificaciones, códigos y banderas nombrados aquí.
- `OUT/15-secuencias-globales/` — los mismos términos en trayecto a extremo, que es la forma más rápida de entender quién llama a quién.
- `OUT/18-build-ci-distribucion.md`, `OUT/19-testing.md`, `OUT/20-seguridad-y-privacidad.md` — `cargo-make`, `cargokit`, `white_label`, tokens y cifrado en el contexto de su entrega.
