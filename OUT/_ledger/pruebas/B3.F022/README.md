# B3.F02.2 — Celdas (`services/cell`, `application/cell`)

**ROADMAP ref:** línea 233 (F02.2).

**Resultado (2026-10-20)**: 1 documento `OUT/09-features/F02-bases-de-datos/2-celdas-services-cell-application-cell.md` (~570 líneas, 19 secciones, gate-100) cubriendo los 4 archivos Rust del ledger F02.2 (foco principal de este doc). Los 23 archivos Dart bloc de `application/cell/` viven en F02.0.1.2 (`database-application-domain-misc.md`) y se cross-referencian sin reclamar.

**Suite `validate-B3.F02.2.sh` 4/4**:
- `template` = 1/1
- `evidence` = 11/11 OK
- `mermaid` = 5/5 bloques OK
- `cobertura` = 4/4 archivos `autor_F02.2`

**Revisor**: `--gate-100 --feature-id F02` → `aprobado, 0 correcciones`.

**Artefactos**:
- `OUT/09-features/F02-bases-de-datos/2-celdas-services-cell-application-cell.md`
- `OUT/_ledger/pruebas/B3.F022/{validate-B3.F02.2.sh, validate-B3.F02.2.log, coverage.json, revisor_output.json, README.md}`

## Distribución del código (4 Rust + 23 Dart cubiertos por F02.0.1.2)

| Carpeta | Archivos | Capa |
|---|---:|---|
| `services/cell/` | 4 | rust-handler (`cell_data_cache`, `cell_operation`, `mod`, `type_cell_data`) |
| `application/cell/bloc/` | 18 | bloc (uno por FieldType) — F02.0.1.2 |
| `application/cell/` (raíz) | 5 | bloc (`cell_cache`, `cell_controller`, `cell_controller_builder`, `cell_data_loader`, `cell_data_persistence`) — F02.0.1.2 |
| **Total Rust cubierto por F02.2** | **4** | rust-handler |

## Cross-references clave

- **F02.0.1.1** — widgets de cell.
- **F02.0.1.2** — `database-application-domain-misc.md` §3.1 (DatabaseController, `CellBackendService`, los 23 BLoCs Dart).
- **F02.1** — `services/field/type_options/*` implementan `CellDataDecoder` + `CellDataChangeset` consumidos por `cell_operation.rs`.
- **F02.3** — `DatabaseEditor` invoca `apply_cell_changeset`; `CellCache` se inyecta en `DatabaseEditor`, `FilterController`, `SortController`.
- **F02.4** — `FilterController::filter_row` usa `handle_cell_filter` con `CellCache`.
- **F02.5** — `SortController::cmp_cell` usa `handle_cell_compare` con `CellCache`.
- **F07** — `MediaCellBloc` interoperá con `flowy-storage`.
- **F09** — `SummaryRowBloc` + `TranslateRowBloc` disparan procesamiento AI.