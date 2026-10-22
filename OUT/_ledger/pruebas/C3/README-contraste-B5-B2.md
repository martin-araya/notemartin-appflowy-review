# C3 · Revisión cruzada de consistencia — bitácora

**Fecha:** 2026-10-21 · **Fase:** C3 · **Plan:** `~/.local/share/kilo/plans/1792619085358-c3-al-cierre-plan.md`

## Por qué esta fase existía

El cierre de C1 dejó una cifra anotada en el `STATE.md`: los 14 documentos de
`OUT/15-secuencias-globales/` (Bloque B5, secuencias extremo a extremo) se
habían escrito **sin consultar los catálogos del Bloque B2**. C1 reparó 48
referencias rotas línea a línea, pero solo comprobaba que la ruta existiera y
que la línea estuviera en rango: no comprobaba que el **símbolo** citado estuviera
en esa línea. La pregunta que C3 tenía que responder es cuánto de lo que los
documentos de secuencia afirman sobre eventos, notificaciones y tipos de Rust
existe realmente en el código.

La respuesta es: **una parte sustancial no existía**.

## Herramientas nuevas

| Script | Qué hace |
|---|---|
| `SKILL/scripts/contrast_B5_B2.py` | Contrasta cada `Enum::Miembro` que aparece en los documentos de B5 contra `extract/events.json` y `extract/notifications.json`, que son exhaustivos por construcción. Clasifica cada referencia en `OK`, `VARIANTE_DESCONOCIDA`, `ENUM_DESCONOCIDO`, `FUERA_DE_CATALOGO`, `METODO_PROPIO`, `METODO_EXTERNO`, `AMBIGUO` o `SPAN_DANADO`. Salida: CSV + JSON. `--check` sale 1 si hay fabricaciones. `--sweep-root` barre cualquier árbol para medir precisión. |
| `SKILL/scripts/expand_short_refs.py` | Expande referencias cortas (`appflowy/frontend/rust-lib/flowy-storage/src/manager.rs:138`) a la ruta completa del inventario, que es lo que `validate_evidence.py` exige. Desempata por sufijo único, por fuente citada o por `--prefer BASE=RUTA_REL` explícito; si no puede resolver con certeza, **lo reporta como ambiguo en vez de adivinar**. Idempotente y no toca bloques `fenced`. |

### Un bug en mi propio detector, y por qué importa

La primera versión de `contrast_B5_B2.py` usaba este regex:

```
\b([A-Z][A-Za-z0-9_]*)::([a-z][A-Za-z0-9_]*)
```

El miembro (`grupo 2`) exigía **minúscula inicial**, así que solo detectaba
llamadas a método (`ChunkedByteUploader::new`) y **nunca** una variante de enum.
La rama de verificación de variantes que yo mismo había escrito en `clasificar()`
—la que decide `VARIANTE_DESCONOCIDA`— era código inalcanzable. El script
informaba «0 fabricaciones» sobre documentos que tenían 53.

Peor aún: informaba **0** con seguridad. Un detector que no puede ver la clase de
error que dice detectar es peor que no tener detector, porque parece una prueba
en verde. El defecto solo se detectó al notar que `AIEvent::StreamChat`, que yo
sabía sospechoso, no aparecía en el informe.

Corregido a `([A-Za-z_][A-Za-z0-9_]*)`. El recuento pasó de 6 a 53.

**Regla que sale de aquí:** un validador que informa «0 hallazgos» debe
contrastarse contra un caso conocido antes de accepting su veredicto. En lo
sucio, `contrast_B5_B2.py` se probó contra `ChunkedByteUploader`, `ZipCreator` y
`AsyncZipExtractor`, que se sabían falsas, y los detecta.

## El hallazgo estructural

Las fabricaciones **no están repartidas al azar**. Se agrupan:

| Bloque | Documentos | Comportamiento |
|---|---|---|
| **B5** (secuencias) | 14 docs, 13 afectados | Trastro de la API desde el nombre, sin leer los catálogos. Peor caso: B5.11 llegó a inventar un camino de importación completo. |
| **B1.7** (`08-persistencia/04-file-cache.md`) | 1 doc, reescrito | Cuatro tipos inventados (`FileCache`, `KVFileCache`, `Uploader`, `StorageManager::cache`), una política de evicción LRU entera, y todo etiquetado `[VERIFICADO]`. |
| **B6** (`21-glosario.md`) | 1 doc | El glosario sí detectó 6 símbolos sin evidencia y los documentó como ausencia. Le faltaban 10 más. |
| **B3/F\*** | 0 afectados | Los features, escritos por subagentes con gate-100, están limpios. |

La diferencia entre B5/B1.7 y B3 no es de rigor del revisor sino de **pipeline**:
los features pasaron por autor → revisor independiente que abría `SRC/`, y ninguno
fabricó un tipo. Los documentos de B5 y B1.7 se escribieron en una sola pasada sin
revisor que leyera el código, y el validador automático no podía pillarlos porque
comprobaba rutas, no símbolos.

## Qué se corrigió en esta sesión

### Reescrituras completas (3 documentos)

**`B5.7 — Subir imagen`**. La versión anterior tenía tres tipos inventados
(`ChunkedByteUploader`, `FileCache`, `ImageBlockService`), dos notificaciones
inexistentes (`StorageNotification::FileUploadProgress`, `DidFinishUpload`) y un
fichero inexistente (`image_upload.dart`). La reescritura se apoyó en una
revisión semántica de gate-100 ejecutada por un subagente independiente con acceso
a `SRC/`, que **rechazó** la primera versión con 27 afirmaciones falsas. Los
errores graves eran de trazado, no de sintaxis:

- Atribuía a `UploadImageMenu` una llamada a `FileStorageService` que no existe;
  el consumidor real es `ImagePlaceholderState.insertMultipleLocalImages`.
- Atribuía el disparo de la subida a `RegisterStream`, cuando el evento real es
  `DocumentEvent::UploadFile`, del crate `flowy-document` (otro crate).
- Confundía `FileProgress` (lo que se publica por fragmento y se serializa a JSON)
  con `FileUploadState` (derivado internamente, nunca serializado).
- **Afirmaba que el progreso llegaba a la UI.** No llega: `onFileProgress` no tiene
  un solo consumidor en todo `appflowy_flutter/lib/`, así que el mapa de notifiers
  queda siempre vacío. El transporte existe; el consumidor no.
- Dos de los tres ficheros de prueba de §15 no existían.

Resultado: 74/74 referencias, 4/4 diagramas, 0 fabricaciones.

**`B5.10 — Export (Markdown)`**. Atribuía la conversión a
`MarkdownDocumentEncoder.encode` y `MarkdownParsers` (los reales son
`DocumentMarkdownEncoder.convert` y una lista `customParsers` de 13 `NodeParser`),
nombraba una clase `ZipCreator` para el empaquetado (es `Archive` + `ZipEncoder`
del paquete `archive`) y arrastraba un span de referencia con el prefijo duplicado
que el reparador de C1 no cubrió. El documento además **omitía** que
`DocumentExportType.text` lanza `UnimplementedError()`. Resultado: 18/18, 3/3.

**`B5.11 — Import (CSV/ZIP/Notion)`**. El más grave: la premisa entera era falsa.
`ImportType` no tiene variantes de ZIP ni de Notion (`appflowy/frontend/appflowy_flutter/lib/workspace/presentation/home/menu/sidebar/import/import_type.dart:7` declara
cinco: `historyDocument`, `historyDatabase`, `markdownOrText`, `csv`, `afDatabase`,
y `allowedExtensions` no incluye `.zip`). El documento afirmaba además que el ZIP se
descomprimía en el cliente vía `collab-importer`, cuando el handler real solo pide
una URL prefirmada a AppFlowy-Cloud y sube el fichero: **la extracción ocurre en el
servidor**. Y el `NotionImporter` de Rust, que sí parsea, no tiene ningún
llamador en producción: sus únicas referencias están en los tests de su propio
crate. Resultado: 32/32, 4/4, 0 fabricaciones.

### Correcciones puntuales (11 documentos)

Se aplicaron 25 sustituciones de símbolos inventados por sus equivalentes
verificados, cada una con su evidencia:

| Símbolo retirado | Sustituto | Evidencia |
|---|---|---|
| `DocumentNotification::DidUpdateDocument` (×7) | `DidReceiveUpdate` | `appflowy/frontend/rust-lib/flowy-user/src/notification.rs:11`; emitida desde el `on_change` del collab en `appflowy/frontend/rust-lib/flowy-document/src/document.rs:24` con payload `DocEventPB` |
| `UserNotification::DidSignIn` (×8) | `UserAuthStateChanged` | `appflowy/frontend/rust-lib/flowy-user/src/notification.rs:14`; el enum no distingue entrada de salida |
| `UserNotification::DidSignOut`, `DidFailToSignIn` | `UserAuthStateChanged` | ídem; el error viaja en el `FlowyError` del propio FFI |
| `DocumentNotification::UpdateSyncState` (×2) | `DidUpdateDocumentSyncState` | `appflowy/frontend/rust-lib/flowy-user/src/notification.rs:13` |
| `DocumentNotification::DidCloseDocument` | `DidUpdateDocumentSnapshotState` | `appflowy/frontend/rust-lib/flowy-user/src/notification.rs:12`; no hay variante de cierre |
| `FolderNotification::DidPublishView`, `DidUnpublishView` | `DidUpdateSharedViews` | no hay ninguna variante de publicación |
| `FolderNotification::CurrentWorkspaceSettingChanged` | `DidUpdateWorkspaceSetting` | — |
| `StorageNotification::DidFinishUpload` | (eliminado) | `appflowy/frontend/rust-lib/flowy-user/src/notification.rs:7`: solo hay dos variantes, ambas de cuota |
| `AIEvent::StreamChat` | `AIEvent::StreamMessage` | `events.json` |

Más la reconstrucción de la tabla de notificaciones transversales de `B5.0`, que
tenía **cinco de seis** filas inventadas, y la ampliación de la tabla de símbolos
sin evidencia de `21-glosario.md`, que pasó de 6 a 16 entradas.

### Las tres citas que C1 resolvió por ancla

| Cita | Veredicto | Corrección aplicada |
|---|---|---|
| `appflowy/frontend/rust-lib/flowy-ai/src/chat.rs:60` (B5.9) | **Falsa por 6 líneas** | `stop_stream_message` está en `appflowy/frontend/rust-lib/flowy-ai/src/chat.rs:66`; la línea 60 cae dentro del literal de la struct `Chat` en su constructor. |
| `appflowy/frontend/rust-lib/flowy-ai/src/notification.rs:48` (B5.0) | **Cierta** | `folder_notification_builder` está exactamente en `appflowy/frontend/rust-lib/flowy-folder/src/notification.rs:48`. La resolución de C1 fue correcta. |
| la cita de B5.5 | **Falsa** | la línea 35 de `collab/collab/src/lib.rs` es `pub use crate::core::collab::{Collab, CollabBuilder};`, un reexport. `Collab::transact_mut` real está en `collab:collab/collab/src/core/collab.rs:169` y `Collab` se declara en la línea 53 del mismo fichero. |

## Daño en Markdown que C1 no cubrió

`SPAN_DANADO` detectó dos líneas cuyo prefijo de fuente estaba duplicado dentro de
un span de `inline code`:

```
OUT/15-secuencias-globales/10-export-markdown.md:133
   2. **`MarkdownDocumentEncoder.encode`** (``editor:`editor:editor/lib/src/…``)
OUT/15-secuencias-globales/11-import-csv-zip.md:159
   IZH->>ZT: AsyncZipExtractor::decode (src: collab:collab-`collab:`collab:collab/…``)
```

`repair_markdown_damage.py` (C1) reparó 98 spans, pero solo cuando el síntoma era
Markdown inválido. Estos **resuelven** como ruta, así que `validate_evidence` los
aceptaba; el síntoma era que el render mostraba texto plano en vez de código, y en
el caso de B5.11 la ruta tenía además un segmento `collab/` de más.

La firma exacta del daño es la **repetición** del prefijo con un acento grave
intercalado (`` `collab:`collab: ``), no un prefijo suelto: la prosa legítima dice
«con el prefijo `appflowy:`» y no debe tocarse. Con esa firma, el barrido de los
**411 documentos** de `OUT/` devuelve 4 aciertos: las 2 líneas reales y sus 2 copias
en `OUT/_ledger/pruebas/C1/backup/`. Cero falsos positivos.

## Cierre de C3.1: las 36 restantes, resueltas

Tras el primer pase quedaban **36 fabricaciones en 12 documentos**. Se resolvieron
en la misma sesión, con la misma regla: ninguna corrección por coincidencia de
nombre, todas leyendo el código. Reparto y sustituciones:

| Documento | Pendientes | Resolución |
|---|---:|---|
| `06-database-filtro-orden-grupo.md` | 18 | Tabla de eventos y de notificaciones reconstruidas. El hallazgo de fondo: **`flowy-database2` no expone eventos dedicados para escribir filtros ni órdenes**; ambos van dentro de `DatabaseEvent::UpdateDatabaseSetting`, que lo confirman `appflowy/frontend/appflowy_flutter/lib/plugins/database/domain/filter_service.dart:239` y `appflowy/frontend/appflowy_flutter/lib/plugins/database/domain/sort_service.dart:39`. El documento declaraba además cuatro eventos y cuatro notificaciones inexistentes, con handlers inventados. |
| `00-indice-secuencias-globales.md` | 9 | Tabla-resumen de enums por dominio: seis nombres de umbrella inventados (`StorageEvent`, `SearchEvent`, `ImportEvent`, `PublishEvent`, `DocumentSyncEvent`) sustituidos por los enums reales del crate que corresponde a cada dominio. |
| `09-chat-con-streaming.md` | 6 | `ChatNotification::StreamChatMessage`, `…Start` y `ChatMessageDidReceive` no existen: el enum tiene diez variantes y las de streaming son `DidReceiveChatMessage`, `StreamChatMessageError` y `FinishStreaming`. |
| `13-perdida-y-recuperacion-de-red.md` | 4 | El enum de estado de red es `CollabConnectState` (`collab:collab/collab-plugins/src/connect_state.rs:6`) con `Connected` y `Disconnected`; no hay `LostConnecting`. Y `UserNotification::DidUpdateNetworkState` no existe: lo real es `DidUpdateCloudConfig`. |
| `02-login-local-y-cloud.md` | 2 | `UserEvent::SignInWithMagicLink` → `MagicLinkSignIn`; no hay evento de «invitado», el más cercano es `PasscodeSignIn`. |
| `03-cambio-de-workspace.md` | 2 | `FolderEvent::GetCurrentWorkspaceViews` → `ReadCurrentWorkspaceViews`; el de ajustes es `GetCurrentWorkspaceSetting` (es una lectura). |
| `12-publish.md` | 2 | `ListPublishViews` → `ListPublishedViews`. **`FolderEvent::UnpublishView` no existe**: `flowy-folder` no expone evento de despublicación, y la fila se documenta ahora como tal. |
| `04`, `05`, `07`, `08`, `11` | 5 | `SyncMode::PullOnly` → `SyncState::SyncFinished` (`collab:collab/collab/src/core/collab_state.rs:46`); `CowSyncEvent::Update` → `SyncState::Syncing`; `Tantivy::Index` → índice del crate externo; y las tres menciones que quedaban dentro de notas de corrección propias, reescritas para que el símbolo retirado no quede en forma parseable (si no, el detector las cuenta como errores propios). |

**Cierre: `contrast_B5_B2.py --check` sale 0 con 0 fabricaciones en 257
referencias.** Reparto final: 147 `OK`, 88 `METODO_PROPIO` (métodos del repo),
16 `FUERA_DE_CATALOGO` (símbolo real de una familia que B2.1/B2.4 no cubren, como
`Collab` o `FieldType`), 6 `EXTERNO`.

Dos ajustes más al clasificador que cette correction hizo necesarios:

- La comprobación de `EXTERNOS_POR_TIPO` estaba **solo en la rama de miembro en
  minúscula**, así que `Ordering::SeqCst` —una *constante* de `std`, que empieza
  por mayúscula— se clasificaba como variante de enum inventada. Se movió la
  comprobación **antes** de la rama de catálogo, porque ahora cubre los dos casos:
  métodos (`Arc::new`) y constantes (`Ordering::SeqCst`), indistinguibles por
  sintaxis.
- Se descartó el término `METODO_EXTERNO` en favour de `EXTERNO`, que describe lo
  que la clasificación afirma en realidad.

## Estado de los validadores tras C3

| Validador | Antes de C3 | Después |
|---|---|---|
| `validate_evidence` | 17 875 / 17 875 | **18 005 / 18 005**, 0 errores |
| `validate_mermaid` | 791 / 791 | **791 / 791**, 0 fallos |
| `validate_template` | 190 / 190 | **190 / 190**, 0 errores |
| `validate_coverage --threshold 100` | 4 603 / 4 603 | **4 603 / 4 603 = 100,00 %** |
| `contrast_B5_B2 --check` | (no existía) | **0 fabricaciones** en 257 referencias |
| `validate-C1.sh` | 5 / 5 | **5 / 5** |
| `validate-C3.sh` | — | **7 / 7** |

## Lección operativa

Las tres fases de la Parte C hasta hasta ahora han encontrado fallos que ningún
validador ve, y los tres eran de la misma familia:

1. **C1** encontró daño de Markdown que el parser de referencias aceptaba.
2. **C1** encontró referencias que resuelven a la línea correcta pero describen algo
   que no está en ella.
3. **C3** encuentra símbolos que no existen dentro de líneas que sí existen.

El patrón es que **validar la forma no valida el contenido**. Una referencia
`ruta:línea` puede ser correcta en sus tres componentes y seguir diciendo una
falsedad. Solo la lectura del código lo detecta, y por eso la revisión semántica
por subagente —el mecanismo de `AGENTS.md §8`— resulta ser la única defensa real,
mientras que los validadores deterministas defienden la integridad mecánica).