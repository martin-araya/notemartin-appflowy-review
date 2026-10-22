---
id: R-002
titulo: Patrones de arquitectura de AppFlowy
fuente: AGENTS.md §5 (líneas 123–144)
archivos_cubiertos: [AGENTS.md]
estado: verificado
---

# R-002 — Patrones de arquitectura de AppFlowy

> Los 7 patrones que todo subagente (autor y revisor) debe reconocer al documentar AppFlowy. Si un caso no encaja en ninguno, abrir `OUT/22-preguntas-abiertas.md` con la etiqueta `patrón-nuevo` y proponer uno nuevo en lugar de improvisar.

## 1. Registro de eventos (Rust)

Cada crate Rust expone un `event_map.rs` con un `AFPlugin` y un enum derivado de `Flowy_Event`. El handler vive en `event_handler.rs`, llama a `manager.rs`, que a su vez interactúa con la capa collab o de persistencia.

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

Trazabilidad: enum `XEvent` → `XEvent::Foo` → `foo_handler` → `manager.rs` → collab/persistencia.

## 2. Notificaciones (Rust→Dart)

Enum `XNotification` derivado de `ProtoBuf_Enum` en `notification.rs`. Se envía con `NotificationBuilder` (`flowy-notification`) con `debounce`. En Dart, los `*_listener.dart` se suscriben vía `rust_stream.dart`.

```text
Rust: XNotification::DocUpdated → NotificationBuilder → send
Dart: rust_stream.dart → DocumentListener.onDocUpdated → BLoC/UI
```

## 3. Llamada Dart→Rust

Cadena completa:

```text
BLoC → *_service.dart → XEventFoo(payload).send() (código generado
en appflowy_backend/dispatch) → FFI async_event → lib-dispatch
→ handler → FlowyResult<T, FlowyError>
```

El payload se serializa a `bytes` con protobuf (PB) en el lado Dart y se deserializa en el lado Rust. El resultado vuelve como `FlowyResult` o se transforma en una `XNotification` para异步.

## 4. Inyección de dependencias

- **Dart:** `get_it` con registros en `startup/deps_resolver.dart`. Cada feature registra sus BLoCs, servicios y repositorios en una sección de `deps_resolver.dart`.
- **Rust:** `flowy-core/src/deps_resolve/*_deps.rs`, un fichero por módulo (`document_deps.rs`, `folder_deps.rs`, etc.).

## 5. Collab/CRDT

Cada objeto (folder, documento, database, row, user awareness) es un `Collab` de `yrs`. `collab-integrate` le adjunta plugins (persistencia local, sync cloud, indexación). El editor (`appflowy_editor`) traduce transacciones a acciones de bloque mediante `editor_transaction_adapter.dart` → `ApplyAction`.

## 6. Capas `*-pub`

Cada crate público tiene un gemelo `*-pub` que expone solo los traits/contratos. Esto rompe dependencias circulares entre los servicios cloud y las entidades compartidas. Por ejemplo: `flowy-document-pub` define `DocumentCloudService` como trait; `flowy-document` lo consume; las implementaciones viven en `flowy-server-pub`.

## 7. Arquitectura Dart dual

Carpetas legadas (`workspace/`, `plugins/`) y nuevas por feature (`features/<x>/{data,logic,presentation}`). Documentar **ambas** sin asumir cuál es la canónica. La fase B0.2 (triage) detecta los archivos que no encajan en la tabla de `PROMPT.md §4` y crea features `F2x`.

## 8. Canales de retorno Rust→Dart (A5.2, refinado en piloto F08)

No todos los resultados Rust→Dart viajan por `flowy-notification`. Hay tres canales diferenciados:

| Canal | Mecanismo | Caso de uso típico | Identificación |
|---|---|---|---|
| Notificación | `XNotification` + `NotificationBuilder` + `flowy-notification` con debounce; listener Dart vía `rust_stream.dart` | Actualizaciones reactivas (`DocumentNotification::DidUpdate…`, `FolderNotification::DidUpdate…`) | Enum `XNotification` en `notification.rs` del crate; receptor en `*_listener.dart` con `parser = XNotificationParser`. |
| Stream `Isolate` (F08) | `IsolateSink::new(Isolate::new(stream_port))`; payload `SearchQueryPB.stream_port` abierto por Dart; cada resultado se serializa con `try_into()` y se envía al puerto | Búsqueda, chats con streaming, descargas progresivas | `manager.rs::perform_search` o similar con `allo_isolate::Isolate`; el lado Dart usa `allo_isolate` para recibir los chunks. |
| Respuesta síncrona FFI | `FlowyResult<T, FlowyError>` retornado directamente al evento dispatch | Handlers cortos y deterministas (abrir un doc, obtener metadatos) | El handler Rust retorna `Result<…, FlowyError>`; no hay stream ni `send_notification` en el crate. |

**Lección F08 (A5.1)**: la búsqueda usa el **canal `Isolate`**, no notificaciones. El enum `SearchNotification` se compila y se exporta pero está sin uso efectivo (registrado en F08 §5 y `OUT/22-preguntas-abiertas.md`). Documentar siempre el canal real, no inferirlo del enum `XNotification` que exista.

## 9. Mapeo feature ↔ unidad (A5.2, refinado en piloto F08)

La **fuente de verdad** del alcance de cada feature es `OUT/_ledger/units/<id>.json` (producido por `build_units.py` en A4.2), **no** la descripción narrativa del ROADMAP.

Cuando la descripción narrativa del ROADMAP (línea `B3.Fxx` y similares) y la unidad real discrepan, sigue este orden de precedencia:

1. `OUT/_ledger/units/<id>.json::archivos[]` (qué hay que documentar).
2. `OUT/_ledger/cobertura.csv::feature_ids` (a qué feature está asignado cada archivo).
3. `PROMPT.md §4` / `ROADMAP.md` (descripción orientativa, puede estar desfasada).

Si encuentras una discrepancia:

- Si la unidad tiene archivos que la descripción no menciona, **documenta los archivos** y deja una nota en el documento (§2 Alcance) explicando la divergencia.
- Si la descripción menciona áreas (p. ej. `flowy-search-pub`, `command_palette`) que la unidad **no** incluye, **referéncialas en §19 (Relacionado con)** sin reclamar sus archivos.
- El ROADMAP se actualiza después del cierre de la fase (en STATE.md se anota la decisión; en `ROADMAP.md` se ajusta la línea de la fase).

Esto evita que el autor "robe" archivos de features adyacentes o que el revisor rechace el documento por cobertura > 100 %.

## Relacionado con

- `R-003 evidence-rules.md` — reglas de evidencia al documentar estos patrones.
- `R-004 diagram-conventions.md` — cómo diagramar cada patrón.
- `R-008 subagent-contract.md` — contrato de los subagentes; `archivos_extra_detectados` cubre el caso de "necesito citar archivos no asignados a mi unidad" (§9 de este archivo).
- `PROMPT.md §5` — plantilla de feature donde los patrones se documentan por sección.
