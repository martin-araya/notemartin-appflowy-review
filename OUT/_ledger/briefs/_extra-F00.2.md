## Foco de esta unidad

`flowy-error` + `flowy-sqlite`: el catálogo de errores tipado y la capa de
persistencia local.

### flowy-error

- `ErrorCode` (`#[repr(u8)]`) con sus **133 variantes** y su conversión a
  protobuf; ya está catalogado en `OUT/15-catalogo-errores.md` (B2.5): coteja y
  referencia, no repitas la tabla completa.
- `FlowyError` / `Error` y sus `From` impl: qué crates convierten sus errores
  al tipo común.
- Cómo un error Rust viaja de vuelta a Dart: el canal `lib_dispatch::Error` →
  `FFIResponse` → `ErrorCode` en Dart. Contrasta con F00.1.

### flowy-sqlite

- `KVStore` y su API (`set_str`/`get_str`/`set_bool`/`set_object`/`set_i64`…).
- `schema.rs` y las **16 tablas** del esquema SQLite; ya documentadas en
  `08-persistencia/` (B1.7): referencia, no repitas el `erDiagram`.
- Migraciones diesel: dónde viven y quién las aplica (las de `flowy-user` están
  en F05.2; las de `flowy-database2` no aplican).
- Qué crates dependen de `flowy-sqlite` (tabla desde `extract/deps.json`).

## Pruebas literales adicionales

1. **Tabla de los 133 `ErrorCode`** agrupados por categoría, con la variante y su
   línea, y contraste explícito con B2.5 (`15-catalogo-errores.md`): el número
   debe coincidir exactamente.
2. Tabla de los `From<…>` implementados en `flowy-error` (crate de origen →
   tipo de error → línea).
3. Tabla de la API pública de `KVStore` (método → tipo → línea).
4. Tabla de las 16 tablas SQLite: nombre, fichero de la migración que la crea y
   qué crate la consume. Marca las que ya están en B1.7.
5. `erDiagram` o tabla de las relaciones entre las tablas de `flowy-sqlite`.
6. Diagrama `flowchart TD` de: crate de dominio → `FlowyError` → FFI response →
   `ErrorCode` → `error_code_map.dart` en Dart (este último está en F17).

## Diagramas mínimos (4)

- 1 `flowchart TD` con `subgraph` por capa del camino de un error.
- 1 `sequenceDiagram`: crate de dominio lanza un error → dispatcher → respuesta
  FFI → `ErrorCode` en Dart.
- 1 `classDiagram` de `FlowyError`/`ErrorCode` y su relación.
- 1 `flowchart LR` de los crates que dependen de `flowy-error` y de
  `flowy-sqlite`.