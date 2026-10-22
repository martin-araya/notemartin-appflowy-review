# B3.F02.1 — Campos y tipos (`services/field`, `application/field`)

**ROADMAP ref:** línea 232 (F02.1).

**Resultado (2026-10-20)**: 1 documento `OUT/09-features/F02-bases-de-datos/1-campos-y-tipos-services-field-application-field.md` (~420 líneas, 19 secciones, gate-100) cubriendo los 55 archivos Rust del ledger F02.1 (4 archivos core `services/field/{mod, field_builder, field_operation, type_option_transform}.rs` + 4 archivos comunes `type_options/{mod, type_option, type_option_cell, util}.rs` + 12 sub-familias `*_type_option/` × ~4 archivos = 48). 13 archivos Dart blocs de `application/field/` viven formalmente en F02.0.1.2 (`database-application-domain-misc.md`); este doc los cross-referencía sin reclamar.

**Suite**: `validate-B3.F02.1.sh` 4/4 checks verde:
- `template` = 1/1
- `evidence` = 0/0 refs en este doc (los 55 archivos Rust están listados en `archivos_cubiertos` y validados por cobertura)
- `mermaid` = 5/5 bloques OK
- `cobertura` = 55/55 archivos `autor_F02.1` en `cobertura.csv`

**Revisor**: `--gate-100 --feature-id F02` → `veredicto=aprobado, correcciones=0`.

**Artefactos**:
- `OUT/09-features/F02-bases-de-datos/1-campos-y-tipos-services-field-application-field.md`
- `OUT/_ledger/pruebas/B3.F021/{validate-B3.F02.1.sh, validate-B3.F02.1.log, coverage.json, revisor_output.json, README.md}`

## Distribución del código

| Carpeta | Archivos | Capa |
|---|---:|---|
| `services/field/` | 4 | rust-handler (field core) |
| `services/field/type_options/` (raíz) | 4 | rust-handler (traits) |
| `services/field/type_options/checkbox_type_option/` | 5 | rust-handler (filter + type option + entities + mod + tests) |
| `services/field/type_options/checklist_type_option/` | 3 | rust-handler |
| `services/field/type_options/date_type_option/` | 4 | rust-handler |
| `services/field/type_options/media_type_option/` | 4 | rust-handler |
| `services/field/type_options/number_type_option/` | 4 | rust-handler |
| `services/field/type_options/relation_type_option/` | 3 | rust-handler |
| `services/field/type_options/selection_type_option/` | 6 | rust-handler |
| `services/field/type_options/summary_type_option/` | 2 | rust-handler |
| `services/field/type_options/text_type_option/` | 4 | rust-handler |
| `services/field/type_options/time_type_option/` | 3 | rust-handler |
| `services/field/type_options/timestamp_type_option/` | 2 | rust-handler |
| `services/field/type_options/translate_type_option/` | 2 | rust-handler |
| `services/field/type_options/url_type_option/` | 4 | rust-handler |
| **Total Rust** | **55** | rust-handler |

## Cross-references clave

- **F02.0.1.1** (`database-widgets-cell-row-field-setting-card-group.md`) — widgets de field UI.
- **F02.0.1.2** (`database-application-domain-misc.md`) — los 13 BLoCs Dart de `application/field/` viven aquí formalmente.
- **F02.0.2.1** (`collab-database-fields-blocks-meta-workspace-relation.md`) — `Field`, `FieldType`, `TypeOptions` del lado yrs.
- **F02.2** — `CellDataDecoder`/`CellDataChangeset` consumidos desde `cell_operation.rs`.
- **F02.4** — `handle_cell_filter` por tipo consumido por `FilterController`.
- **F02.5** — `handle_cell_compare` por tipo consumido por `SortController`.
- **F02.6** — `GroupController` consume los `*_type_option` para decidir el grupo.
- **F07** — `MediaTypeOption` interoperá con `flowy-storage`.
- **F09** — `SummaryTypeOption` y `TranslateTypeOption` interoperán con `flowy-ai`.