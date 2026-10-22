## Foco de esta unidad

`dart-ffi` + `lib-dispatch` + `lib-infra`: la frontera FFI, el registro de plugins
(`AFPlugin`), el dispatcher, el runtime de tokio y los tipos de request/response.

Identificadores que deben aparecer con `ruta:línea` (verifícalos con `rg`):

- Los **8 `extern "C"`** de `dart-ffi/src/lib.rs`: `init_sdk`, `async_event`,
  `sync_event`, `set_stream_port`, `set_log_stream_port`, `link_me_please`,
  `rust_log`, `set_env`, cada uno con su línea exacta.
- `AFPlugin`, `AFPluginDispatcher`, `AFPluginRuntime`, `AFPluginEventRequest`,
  `AFPluginEventResponse`, `boxed_async_send_with_callback`, `Module`,
  `RequestType`/`ResponseType` (o los nombres reales que encuentres).
- `binding.h` y `build.rs` de `dart-ffi`: cómo se genera el header y por qué
  existe `link_me_please`.

## Pruebas literales adicionales

1. **Tabla de los 8 `extern "C"`**: firma, línea, y quién los invoca desde Dart
   (`appflowy/frontend/appflowy_flutter/packages/appflowy_backend/lib/ffi.dart`).
2. **Tabla evento → crate → handler** construida sobre
   `OUT/_ledger/extract/events.json` (229 variantes): confirma cuántos crates
   registran `AFPlugin` y cómo se inicializan en `AppFlowyCore`.
3. `classDiagram` de `AFPluginEventRequest` / `AFPluginEventResponse` y su enum
   de tipo.
4. Explicar el recorrido completo de un `XEvent` de Rust: codificación
   protobuf, `async_event` vs `sync_event`, el camino de vuelta de la respuesta,
   y `RustStreamReceiver` en Dart (este último ya está en B1.5 §01: cross-ref).

## Diagramas mínimos (5)

- 1 `flowchart TD` con `subgraph` por capa: Dart → `async_event` → dispatcher →
  `AFPlugin` → manager → collab → respuesta.
- 2 `sequenceDiagram`: (a) evento asíncrono con respuesta por callback;
  (b) evento síncrono (`sync_event`).
- 1 `stateDiagram-v2` o `classDiagram` del ciclo request/response.
- 1 `classDiagram` de las entidades request/response.