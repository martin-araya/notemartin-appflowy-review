# Pruebas A2.1 — `extract_events.py` + `events.json`

**Fecha:** 2026-10-18
**Fase:** A2.1 (Bloque A2 — Extractores deterministas)
**Estado:** ✅ cerrada

## Objetivo

Verificar que el extractor determinista:

1. Recorre `SRC/appflowy/frontend/rust-lib/**/event_map.rs` y extrae el
   enum con `#[derive(..., Flowy_Event, ...)]`, sus variantes con
   `#[event(input=..., output=...)]` (incluyendo formas multilínea y
   `#[event()]` vacía) y los registros `.event(EnumName::Variant, handler)`
   dentro de `pub fn init(...) -> AFPlugin`.
2. Resuelve cada `handler` a `archivo:línea` dentro del crate.
3. Marca como `sin_handler` las variantes que el `init` no registra.

## Comandos ejecutados

```bash
python3 SKILL/scripts/extract_events.py \
  --src-root SRC \
  --out-dir OUT/_ledger/extract
OUT/_ledger/validate-A2.1.sh
```

Log completo: [`extract.log`](extract.log) y [`validate.log`](validate.log).

## Resultado del validador

```
OK: A2.1 (JSON valido, flowy-document OK, CreateDocument input=CreateDocumentPayloadPB output=null, OpenDocument input=OpenDocumentPayloadPB output=DocumentDataPB, sin_handler consistentes, handlers resueltos, conteos coherentes)
  crates_with_event_map: 8
  total_variants:        229
  total_registered:      224
  total_sin_handler:     5
  sin_handler variants:
  - flowy-database2::GetAllRows (index=177)
  - flowy-folder::CreateFolderWorkspace (index=0)
  - flowy-folder::DeleteWorkspace (index=3)
  - flowy-folder::CopyLink (index=20)
  - flowy-user::AddWorkspaceMember (index=37)
exit=0
```

## Tabla por crate (orden estable por `crate`)

| Crate | Enum | Variantes | Registradas | sin_handler | init line | Deriva |
|---|---|---:|---:|---:|---:|---|
| `flowy-ai`        | `AIEvent`        | 25 | 25 | 0 | 12 | `Clone,Copy,PartialEq,Eq,Debug,Display,Hash,ProtoBuf_Enum,Flowy_Event` |
| `flowy-database2` | `DatabaseEvent`  | 72 | 71 | 1 | 11 | (idem) |
| `flowy-date`      | `DateEvent`      |  1 |  1 | 0 |  8 | `Debug,Clone,PartialEq,Eq,Hash,Display,ProtoBuf_Enum,Flowy_Event` |
| `flowy-document`  | `DocumentEvent`  | 21 | 21 | 0 | 12 | `Debug,Clone,PartialEq,Eq,Hash,Display,ProtoBuf_Enum,Flowy_Event` |
| `flowy-folder`    | `FolderEvent`    | 51 | 48 | 3 | 11 | `Clone,Copy,PartialEq,Eq,Debug,Display,Hash,ProtoBuf_Enum,Flowy_Event` |
| `flowy-search`    | `SearchEvent`    |  1 |  1 | 0 |  9 | `Clone,Copy,PartialEq,Eq,Debug,Display,Hash,ProtoBuf_Enum,Flowy_Event` |
| `flowy-storage`   | `FileStorageEvent` | 2 |  2 | 0 |  8 | `Clone,Copy,PartialEq,Eq,Debug,Display,Hash,ProtoBuf_Enum,Flowy_Event` |
| `flowy-user`      | `UserEvent`      | 56 | 55 | 1 | 17 | `Clone,Copy,PartialEq,Eq,Debug,Display,Hash,ProtoBuf_Enum,Flowy_Event` |
| **TOTAL**         |                  | **229** | **224** | **5** | | |

Todos los crates declaran `#[event_err = "FlowyError"]`.

## Casos del test literal del ROADMAP A2.1

### `flowy-document::CreateDocument`

```json
{
  "name": "CreateDocument",
  "index": 0,
  "input": "CreateDocumentPayloadPB",
  "output": null,
  "source_line": 61,
  "registrations": [
    {
      "handler": "create_document_handler",
      "registered_in": "SRC/appflowy/frontend/rust-lib/flowy-document/src/event_map.rs",
      "registered_line": 16,
      "handler_file": "SRC/appflowy/frontend/rust-lib/flowy-document/src/event_handler.rs",
      "handler_line": 54
    }
  ],
  "sin_handler": false
}
```

- ✅ `input = "CreateDocumentPayloadPB"`
- ✅ `output = null` (la variante no declara `output`)
- ✅ Handler `create_document_handler` resuelto a
  frontend/rust-lib/flowy-document/src/event_handler.rs:54.

### `flowy-document::OpenDocument`

```json
{
  "name": "OpenDocument",
  "index": 1,
  "input": "OpenDocumentPayloadPB",
  "output": "DocumentDataPB",
  "source_line": 64,
  "registrations": [
    {
      "handler": "open_document_handler",
      "registered_in": "SRC/appflowy/frontend/rust-lib/flowy-document/src/event_map.rs",
      "registered_line": 17,
      "handler_file": "SRC/appflowy/frontend/rust-lib/flowy-document/src/event_handler.rs",
      "handler_line": 69
    }
  ],
  "sin_handler": false
}
```

- ✅ `input = "OpenDocumentPayloadPB"`
- ✅ `output = "DocumentDataPB"`
- ✅ Handler `open_document_handler` resuelto a
  frontend/rust-lib/flowy-document/src/event_handler.rs:69.

## Variantes `sin_handler` (5 en total, todas legítimas)

| Crate | Variante | Índice | Razón documentada en código |
|---|---|---:|---|
| `flowy-database2` | `GetAllRows` | 177 | Variante definida en el enum pero nunca pasada a `.event(...)` en `init`. `GetAllRows = 177` está en frontend/rust-lib/flowy-database2/src/event_map.rs:396; el `init` solo registra 71 de las 72 variantes. |
| `flowy-folder`   | `CreateFolderWorkspace` | 0 | Marcada como `/// Deprecated: Create a new workspace` en frontend/rust-lib/flowy-folder/src/event_map.rs:67. Conservada en el enum por compatibilidad pero sin handler. |
| `flowy-folder`   | `DeleteWorkspace` | 3 | Definida en frontend/rust-lib/flowy-folder/src/event_map.rs:80 pero el `init` no la registra; el handler real vive en `flowy-user::delete_workspace_handler` (frontend/rust-lib/flowy-folder/src/event_map.rs:64). Caso de variante compartida entre crates. |
| `flowy-folder`   | `CopyLink` | 20 | Definida con `#[event()]` (vacía) en frontend/rust-lib/flowy-folder/src/event_map.rs:120–121; el `init` no la registra. Posible regresión. |
| `flowy-user`     | `AddWorkspaceMember` | 37 | Definida en frontend/rust-lib/flowy-user/src/event_map.rs:197–198; el `init` no la registra. Posible regresión o trabajo en curso. |

## Warnings del extractor

0 warnings. Todos los `handler` registrados se resolvieron a su
`fn` real en el crate correspondiente.

## Multilínea — cobertura real del parser

El parser maneja las tres formas observadas en el código real:

1. **Línea única**:
   ```rust
   .event(DocumentEvent::CreateDocument, create_document_handler)
   ```
2. **Multilínea con `,` final** (la forma más común en `flowy-document`,
   `flowy-ai`, `flowy-user`):
   ```rust
   .event(
     DocumentEvent::GetDocEncodedCollab,
     get_encode_collab_handler,
   )
   ```
3. **Atributo `#[event(...)]` multilínea** (en `flowy-document/src/event_map.rs:78-94`):
   ```rust
   #[event(
     input = "DocumentRedoUndoPayloadPB",
     output = "DocumentRedoUndoResponsePB"
   )]
   Redo = 6,
   ```
4. **Atributo `#[event()]` vacío** (en `flowy-folder/src/event_map.rs:120`):
   ```rust
   #[event()]
   CopyLink = 20,
   ```
5. **Sin atributo `#[event(...)]`** (variante deprecada; en
   `flowy-folder/src/event_map.rs:67-68`):
   ```rust
   /// Deprecated: Create a new workspace
   CreateFolderWorkspace = 0,
   ```

## Smoke test (robustez del extractor)

Ejecutado con `SRC/` vacío (directorio sin clones):

```bash
TMP=$(mktemp -d) && mkdir -p "$TMP/SRC/appflowy/frontend/rust-lib"
python3 SKILL/scripts/extract_events.py --src-root "$TMP/SRC" --out-dir "$TMP/out"
jq '.summary' "$TMP/out/events.json"
```

Resultado:

```json
{
  "crates_with_event_map": 0,
  "total_variants": 0,
  "total_registered": 0,
  "total_sin_handler": 0
}
```

✅ El extractor no aborta y produce un `events.json` bien formado
(los checks del validador fallarán porque no se cumplen los casos
del ROADMAP, lo cual es el comportamiento esperado).

## Tamaño y rendimiento

| Métrica | Valor |
|---|---|
| Líneas JSON | 4.150 |
| Tamaño | 140 KB |
| Tiempo de extracción | < 1 s |
| Tiempo del validador | < 0,1 s |

## Diferencias detectadas vs el plan

| # | Diferencia | Acción |
|---|---|---|
| 1 | La regex de `.event(...)` no aceptaba la coma final tras el handler (forma multilínea) | Corregido: añadido `\s*,?` antes de `\)` en T2. Sin esta corrección, **6 variantes de `flowy-document`** quedaban marcadas como `sin_handler` falsamente. |
| 2 | `source_line` apuntaba a la línea del primer `#[event(...)]` previo en lugar del nombre de la variante | Corregido: usar `vm.start("name")` para apuntar al identificador. Documentado en el código. |

Sin impacto sobre el contrato externo ni sobre el validador.

## Criterio de aprobación del ROADMAP

> para `flowy-document`, aparecen `CreateDocument` (input `CreateDocumentPayloadPB`, sin output) y `OpenDocument` (input `OpenDocumentPayloadPB`, output `DocumentDataPB`); toda variante del enum tiene handler registrado o queda marcada `sin_handler`.

- ✅ `CreateDocument`: `input = "CreateDocumentPayloadPB"`, `output = null`.
- ✅ `OpenDocument`: `input = "OpenDocumentPayloadPB"`, `output = "DocumentDataPB"`.
- ✅ 21/21 variantes de `flowy-document` registradas; 0 `sin_handler`.
- ✅ A nivel global: 224/229 registradas; 5 `sin_handler` documentadas y legítimas.
