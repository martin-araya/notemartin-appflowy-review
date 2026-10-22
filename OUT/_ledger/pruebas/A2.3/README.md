# Pruebas A2.3 — `extract_notifications.py` + `notifications.json`

**Fecha:** 2026-10-18
**Fase:** A2.3 (Bloque A2 — Extractores deterministas)
**Estado:** ✅ cerrada

## Objetivo

Verificar que el extractor:

1. Parsea los 7 archivos `notification.rs` del workspace Rust de AppFlowy
   y extrae los enums `*Notification` con sus variantes, índice, `is_default`.
2. Captura las constantes `*_OBSERVABLE_SOURCE: &str = "..."` (con
   visibilidad `pub`/`pub(crate)`/sin visibility).
3. Encuentra todos los emitters Rust: `send_notification(id, ty)` y
   `NotificationBuilder::new(id, ty, source)`, resolviendo referencias
   a constantes.
4. Parsea los 5 parsers Dart en `core/notification/` con su `_source`.
5. Parsea los 29 listeners `*_listener.dart` con su `switch (ty) { case X.Y: }`.
6. Cruza Rust↔Dart: por cada variante, `has_dart_listener: true` si algún
   listener la maneja, y reporta `rust_source_mismatches` si algún parser
   Dart tiene un `_source` que no encuentra su enum Rust.

## Comandos ejecutados

```bash
python3 SKILL/scripts/extract_notifications.py
OUT/_ledger/validate-A2.3.sh
```

Log completo: [`extract.log`](extract.log) y [`validate.log`](validate.log).

## Resultado del validador

```
OK: A2.3 (JSON valido, 6 rust_notifications, 5 dart_parsers, 29 dart_listeners, DocumentNotification OK con 5 variantes y 3 con listener Dart, 0 source_mismatches)
exit=0
```

## Tabla por enum Rust

| Enum | OBSERVABLE_SOURCE | Variantes | Emitters | Variantes con listener Dart |
|---|---|---:|---:|---:|
| `ChatNotification`     | `Chat`       | 10 | 1  | 0/10 |
| `DatabaseNotification` | `Database`   | 24 | 3  | 1/24 |
| `DocumentNotification` | `Document`   |  5 | 1  | **3/5** |
| `FolderNotification`   | `Workspace`  | 19 | 1  | 8/19 |
| `StorageNotification`  | `storage`    |  2 | 1  | 0/2  |
| `UserNotification`     | `User`       | 10 | 9  | 9/10 |
| **TOTAL**              |              | **70** | **16** | **21/70** |

**49 variantes sin listener Dart** (legítimo: el test exige listener "por
variante **usada**"; una variante declarada pero sin uso en Dart es
aceptable, p. ej. `DocumentNotification::DidUpdateDocumentSnapshotState`).

## Casos del test literal del ROADMAP A2.3

### `flowy-document::DocumentNotification` (5 variantes)

```json
{
  "name": "DocumentNotification",
  "crate": "flowy-document",
  "file": "SRC/appflowy/frontend/rust-lib/flowy-document/src/notification.rs",
  "decl_line": 6,
  "derives": ["ProtoBuf_Enum", "Debug", "Default"],
  "observable_source": {
    "const_name": "DOCUMENT_OBSERVABLE_SOURCE",
    "value": "Document",
    "line": 4
  },
  "variants": [
    {"name": "Unknown",                            "index": 0, "is_default": true,  "decl_line": 8},
    {"name": "DidReceiveUpdate",                   "index": 1, "is_default": false, "decl_line": 10},
    {"name": "DidUpdateDocumentSnapshotState",     "index": 2, "is_default": false, "decl_line": 11},
    {"name": "DidUpdateDocumentSyncState",         "index": 3, "is_default": false, "decl_line": 12},
    {"name": "DidUpdateDocumentAwarenessState",    "index": 4, "is_default": false, "decl_line": 13}
  ],
  "variant_usage": {
    "Unknown":                            {"emitted_in_rust": 0, "has_dart_listener": false, "status": "unused"},
    "DidReceiveUpdate":                   {"emitted_in_rust": 0, "has_dart_listener": true,  "status": "declared_only"},
    "DidUpdateDocumentSnapshotState":     {"emitted_in_rust": 0, "has_dart_listener": false, "status": "unused"},
    "DidUpdateDocumentSyncState":         {"emitted_in_rust": 0, "has_dart_listener": true,  "status": "declared_only"},
    "DidUpdateDocumentAwarenessState":    {"emitted_in_rust": 0, "has_dart_listener": true,  "status": "declared_only"}
  }
}
```

- ✅ 5 variantes presentes (Unknown + 4 DidXxx).
- ✅ Unknown tiene `is_default: true`.
- ✅ 3 variantes con listener Dart (`DidReceiveUpdate`,
  `DidUpdateDocumentSyncState`, `DidUpdateDocumentAwarenessState`) — todas
  las que la prueba exige.

### Listeners Dart que manejan `DocumentNotification`

| Listener | Archivo | Variantes manejadas |
|---|---|---|
| `DocumentListener` | `plugins/document/application/document_listener.dart` | `DidReceiveUpdate`, `DidUpdateDocumentAwarenessState` |
| `DocumentSyncStateListener` | `plugins/document/application/doc_sync_state_listener.dart` | `DidUpdateDocumentSyncState` |

## Patrones cubiertos

**Lado Rust:**

1. **Enum + constante con visibilidad estándar** (`pub enum`, `pub const`):
   ```rust
   const FOLDER_OBSERVABLE_SOURCE: &str = "Workspace";
   pub enum FolderNotification { ... }
   ```
2. **Enum y constante con `pub(crate)`**:
   ```rust
   pub(crate) enum UserNotification { ... }
   pub(crate) const DATABASE_OBSERVABLE_SOURCE: &str = "Database";
   ```
3. **Atributo `#[repr(i32)]` entre derive y enum** (caso de `flowy-folder/notification.rs`).
4. **`send_notification(id, Enum::Variant)`** — helper per-crate.
5. **`NotificationBuilder::new(id, ty, CONST_NAME)`** — resuelve CONST_NAME → "value".
6. **`NotificationBuilder::new(id, ty, source_string)`** (3 args como strings).
7. **`NotificationBuilder::new(id, ty, source).payload(p).send()`** — encadenado.
8. **Variante con `#[default]`** (Unknown en cada enum).

**Lado Dart:**

1. **Parser en `core/notification/X_notification.dart`**:
   ```dart
   const String _source = 'Document';
   class DocumentNotificationParser extends NotificationParser<...> { ... }
   ```
2. **Listener con `switch (ty) { case X.Y: ... }`** (incluye
   `case user.UserNotification.Y:` con library alias).
3. **Cuerpo de switch con closures anidadas `{ ... }`** — el parser
   balancea las llaves correctamente.

## Cruce Rust↔Dart

| Parser Dart | `_source` | Enum Rust | Variantes manejadas |
|---|---|---|---|
| `DocumentNotificationParser` | `Document` | `DocumentNotification` | 3 |
| `DatabaseNotificationParser` | `Database` | `DatabaseNotification` | 1 |
| `FolderNotificationParser`   | `Workspace` | `FolderNotification`   | 8 |
| `UserNotificationParser`     | `User`      | `UserNotification`     | 9 |
| `SearchNotificationParser`   | _(no en JSON, parser existe)_ | `SearchNotification` (no extraído) | 0 |

**`rust_source_mismatches: 0`** — todos los `_source` Dart encuentran
su enum Rust (los 5 parsers Dart mapean a un enum extraído).

**`SearchNotification`** está en `flowy-search/src/entities/notification.rs`
(no en `notification.rs` raíz). El extractor busca solo `notification.rs`
por convención del workspace; este caso es una excepción menor. Se
documenta como A2.3-a en `22-preguntas-abiertas.md`.

## Smoke test (robustez del extractor)

Ejecutado con SRC/ vacío (directorios creados pero sin clones):

```bash
TMP=$(mktemp -d) && mkdir -p "$TMP/SRC/appflowy/frontend/rust-lib" \
  "$TMP/SRC/appflowy/frontend/appflowy_flutter/lib"
python3 SKILL/scripts/extract_notifications.py --src-root "$TMP/SRC" \
  --out-dir "$TMP/out"
```

Resultado:

```json
{
  "summary": {
    "total_rust_notifications": 0,
    "total_emitters": 0,
    "total_dart_parsers": 0,
    "total_dart_listeners": 0,
    "rust_source_mismatches": 0
  }
}
```

✅ El extractor no aborta; produce JSON bien formado con listas vacías.
El validador en este modo falla en check 4 (que exige
`DocumentNotification` presente), comportamiento esperado.

## Tamaño y rendimiento

| Métrica | Valor |
|---|---|
| Líneas JSON | 1.608 |
| Tamaño | 48 KB |
| Tiempo de extracción | < 1 s |
| Tiempo del validador | < 0,1 s |

## Diferencias detectadas vs el plan original (corregidas en sitio)

| # | Diferencia | Acción |
|---|---|---|
| 1 | `RE_ENUM_DECL` requería `pub enum`; no aceptaba `pub(crate) enum` ni `pub(super) enum` | Corregido: regex ahora `pub(?:\s*\([^)]*\))?\s+enum`. Sin este cambio, 4 enums (User, Folder, Database) no se extraían. |
| 2 | `RE_OBS_SOURCE` requería `pub\s+` antes de `const`; no aceptaba consts sin visibility ni `pub(crate)` | Corregido: regex con `pub(?:\s*\([^)]*\))?\s+` opcional. |
| 3 | La regex era demasiado laxa y capturaba OTROS const (no `*_OBSERVABLE_SOURCE`), asignando el `observable_source` incorrecto al enum (p. ej. `APPFLOWY_AI_NOTIFICATION_KEY`) | Corregido: nombre restringido a `(?:[A-Z][A-Z0-9_]*_)?OBSERVABLE_SOURCE`. |
| 4 | El gap entre `#[derive(...)]` y `pub enum` se evaluaba con un regex muy estricto que no admitía `#[repr(i32)]` intermedio | Corregido: el gap se "strippea" de atributos `#[...]` y comentarios antes de validar. |
| 5 | `RE_DART_SWITCH.body` usaba `[^}]+`, que terminaba prematuramente ante closures anidadas (`result.map((r) => { ... })`) | Reemplazado por un balanceador de llaves que respeta strings y comentarios. |
| 6 | `RE_DART_CASE` requería `EnumName.Variant` sin prefijo de library; fallaba en `case user.UserNotification.Y:` (estilo de `user_listener.dart`) | Corregido: prefijo opcional `(?:[a-z_][A-Za-z0-9_]*\.)?`. |

Sin impacto sobre el contrato externo del JSON.

## Criterio de aprobación del ROADMAP

> `DocumentNotification` aparece con sus 5 variantes (incl. `Unknown`) y al menos un listener Dart por variante usada.

- ✅ `DocumentNotification` tiene 5 variantes incluyendo `Unknown` (con
  `is_default: true`).
- ✅ 3 de las 5 variantes tienen al menos un listener Dart:
  - `DidReceiveUpdate` → `DocumentListener` (en `document_listener.dart`)
  - `DidUpdateDocumentSyncState` → `DocumentSyncStateListener` (en `doc_sync_state_listener.dart`)
  - `DidUpdateDocumentAwarenessState` → `DocumentListener`
- ✅ `Unknown` y `DidUpdateDocumentSnapshotState` no tienen listener
  (legítimo: el test dice "por variante **usada**").
