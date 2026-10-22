# Pruebas A2.2 — `extract_protobuf.py` + `protobuf.json`

**Fecha:** 2026-10-18
**Fase:** A2.2 (Bloque A2 — Extractores deterministas)
**Estado:** ✅ cerrada

## Objetivo

Verificar que el extractor:

1. Recorre `SRC/appflowy/frontend/rust-lib/**/*.rs` y extrae todos los
   `#[derive(... ProtoBuf ...)]` (structs) y `#[derive(... ProtoBuf_Enum ...)]`
   (enums).
2. Para cada struct: `name`, `kind`, `file`, `decl_line`, `end_line`,
   `derives`, `generics`, `fields[]` con `{name, type, pb: {index, one_of, extra}, vis, decl_line}`.
3. Para cada enum: `variants[]` con `{name, index, attrs, decl_line}`.
4. **Cruza con `events.json` (A2.1)**: cada `input`/`output` único se
   marca como `resolved` o se reporta en `missing_event_pbs`.

## Comandos ejecutados

```bash
python3 SKILL/scripts/extract_protobuf.py
OUT/_ledger/validate-A2.2.sh
```

Log completo: [`extract.log`](extract.log) y [`validate.log`](validate.log).

## Resultado del validador

```
OK: A2.2 (JSON valido, 439 entidades (389 structs + 50 enums), cruce con events.json resuelto: 141/141 inputs + 84/84 outputs, 0 missing reportados)
exit=0
```

## Tabla por crate

| Crate | Structs | Enums | Archivos escaneados | Total entidades |
|---|---:|---:|---:|---:|
| `dart-ffi`         |   2 |  1 |  2 |   3 |
| `flowy-ai`         |  41 | 10 |  2 |  51 |
| `flowy-database2`  | 163 |  7 | 42 | 170 |
| `flowy-date`       |   2 |  0 |  1 |   2 |
| `flowy-document`   |  43 |  7 |  3 |  50 |
| `flowy-folder`     |  57 |  7 |  6 |  64 |
| `flowy-notification` | 1 |  0 |  1 |   1 |
| `flowy-search`     |  11 |  2 |  4 |  13 |
| `flowy-storage`    |   3 |  0 |  1 |   3 |
| `flowy-user`       |  66 | 16 |  8 |  82 |
| **TOTAL**          | **389** | **50** | **70** | **439** |

(70 archivos con entidades; 745 archivos `.rs` totales escaneados.)

**Totales adicionales:**
- 1.030 campos protobuf en structs.
- 158 campos con `pb.one_of = true` (campos opcionales de un `oneof`).
- 0 campos con `pb: null` (todos los campos extraídos tienen un `#[pb(...)]`).

## Casos del test literal del ROADMAP A2.2

### `flowy-document::CreateDocumentPayloadPB`

```json
{
  "name": "CreateDocumentPayloadPB",
  "kind": "struct",
  "file": "SRC/appflowy/frontend/rust-lib/flowy-document/src/entities.rs",
  "decl_line": 125,
  "end_line": 133,
  "derives": ["Default", "ProtoBuf"],
  "generics": "",
  "fields": [
    {"name": "document_id", "type": "String", "pb": {"index": 1, "one_of": false, "extra": {}}, "vis": "pub", "decl_line": 127},
    {"name": "initial_data", "type": "Option<DocumentDataPB>", "pb": {"index": 2, "one_of": true, "extra": {}}, "vis": "pub", "decl_line": 130}
  ],
  "is_input_of": ["flowy-document::CreateDocument"],
  "is_output_of": []
}
```

### `flowy-document::OpenDocumentPayloadPB`

```json
{
  "name": "OpenDocumentPayloadPB",
  "kind": "struct",
  "file": "SRC/appflowy/frontend/rust-lib/flowy-document/src/entities.rs",
  "decl_line": 28,
  "end_line": 31,
  "derives": ["Default", "ProtoBuf"],
  "fields": [
    {"name": "document_id", "type": "String", "pb": {"index": 1, "one_of": false, "extra": {}}, "vis": "pub", "decl_line": 30}
  ],
  "is_input_of": ["flowy-document::OpenDocument", "flowy-document::GetDocumentData", "flowy-document::GetDocumentSnapshotMeta", "flowy-document::GetDocEncodedCollab", "flowy-document::GetDocumentText"]
}
```

### `flowy-document::DocumentDataPB`

```json
{
  "name": "DocumentDataPB",
  "kind": "struct",
  "file": "SRC/appflowy/frontend/rust-lib/flowy-document/src/entities.rs",
  "decl_line": 202,
  "end_line": 215,
  "derives": ["Default", "ProtoBuf"],
  "fields": 3
}
```

## Cruce con `events.json`

| Métrica | Valor |
|---|---:|
| `unique_event_inputs` | 141 |
| `unique_event_outputs` | 84 |
| `resolved_inputs` | **141** |
| `resolved_outputs` | **84** |
| `missing_event_pbs` | **0** |

✅ Cada `input`/`output` único de `events.json` se ha extraído como entidad
de `protobuf.json`. No hay PB referenciados por eventos que falten.

## Patrones cubiertos

El parser maneja correctamente las siguientes variantes de `#[pb(...)]`:

1. **Simple:** `#[pb(index = 1)]`
2. **Con `one_of`:** `#[pb(index = 2, one_of)]`
3. **Multilínea** (no se observa en el código actual, pero soportado):
   ```rust
   #[pb(
     index = 1,
     one_of,
   )]
   ```
4. **Con `#[pb(...)]` seguido de `//` comentarios antes del campo** (caso
   real en `flowy-folder/.../view.rs:UpdateViewPayloadPB::extra`):
   ```rust
   #[pb(index = 7, one_of)]
   // this value used to store the extra data with JSON format
   // for document:
   //  - cover: { type: "", value: "" }
   //  - line_height_layout: "small" or "normal" or "large"
   pub extra: Option<String>,
   ```
   El parser neutraliza los `//` antes de aplicar `RE_FIELD`, así que el
   campo se extrae correctamente con `pb.index=7, one_of=true`.

5. **Campos comentados excluidos** (3 casos reales en el código):
   - `ChatMessagePB::should_fetch_related_question` (`// #[pb(index = 8)]`)
   - `ViewIdPB::workspace_id` (3 líneas `//`)
   - `UpdateViewPayloadPB` no se ve afectado: el `#[pb(index=7,one_of)]` real
     precede al bloque de `//` comentarios, y `extra` se extrae correctamente.

## Smoke test (robustez del extractor)

Ejecutado con `--events-json` apuntando a archivo inexistente:

```bash
TMP=$(mktemp -d)
python3 SKILL/scripts/extract_protobuf.py --out-dir "$TMP/out" \
  --events-json "$TMP/no_events.json"
jq '{summary, cross_ref}' "$TMP/out/protobuf.json"
```

Resultado:

```json
{
  "summary": {"total_entities": 439, "total_structs": 389, "total_enums": 50, "files_scanned": 745, "crates_with_entities": 10},
  "cross_ref": {
    "events_json": null,
    "unique_event_inputs": [],
    "unique_event_outputs": [],
    "resolved_inputs": [],
    "resolved_outputs": [],
    "missing_event_pbs": []
  }
}
```

✅ El extractor no aborta y produce JSON bien formado con `cross_ref`
vacío. El validador en este modo fallaría en check 5 (que requiere
`events.json`), comportamiento esperado.

## Tamaño y rendimiento

| Métrica | Valor |
|---|---|
| Líneas JSON | 22.412 |
| Tamaño | 616 KB |
| Tiempo de extracción | < 1 s |
| Tiempo del validador | < 0,1 s |

## Diferencias detectadas vs el plan original (corregidas en sitio)

| # | Diferencia | Acción |
|---|---|---|
| 1 | Bug de typo: `path` en vez de `args.events_json` en `build_cross_ref` | Corregido en T2; sin impacto en la salida. |
| 2 | `parts[3]` no era el nombre del crate sino `rust-lib` (constante) → `crates: 1` incorrecto | Corregido: usar `parts[4]`. Ahora `crates: 10`. |
| 3 | El regex `RE_FIELD` aceptaba `//` como "atributo" y producía **falsos positivos** en bloques de comentarios con texto tipo `// - font_layout: "small"` | Corregido: (a) el regex requiere al menos un `#[...]` real; (b) `strip_line_comments_in_place` neutraliza los `//` antes de aplicar el regex, conservando posiciones. Sin este cambio, hasta **4 campos falsos** se extraían de `UpdateViewPayloadPB`. |
| 4 | Sin el cambio 3, los 3 campos comentados (`should_fetch_related_question`, `workspace_id`, `extra` antes del fix) se extraían con `pb: null` | Con el cambio 3, los 3 campos comentados quedan excluidos limpiamente, y el `extra` real de `UpdateViewPayloadPB` se extrae con `pb.index=7, one_of=true`. |

Sin impacto sobre el contrato externo del JSON.

## Criterio de aprobación del ROADMAP

> cada `input`/`output` de `events.json` existe como entidad extraída (o se reporta faltante).

- ✅ Los 141 inputs únicos y los 84 outputs únicos de `events.json` existen
  como entidad extraída en `protobuf.json`.
- ✅ 0 entradas en `missing_event_pbs` (cruce 100% limpio).
- ✅ Cada entidad está anclada a `file:decl_line` real.
- ✅ Conteos internos coherentes (validador check 4).
