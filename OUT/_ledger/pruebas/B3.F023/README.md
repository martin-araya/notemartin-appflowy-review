# B3.F02.3 — Filas y row detail (`application/row`), relaciones

**ROADMAP ref:** línea 234 (F02.3).

**Resultado (2026-10-20)**: 1 documento `OUT/09-features/F02-bases-de-datos/3-filas-y-row-detail-application-row-relaciones.md` (~480 líneas, 19 secciones, gate-100) cubriendo los 5 archivos Rust del ledger F02.3 (`services/database/{database_editor, database_observe, entities, mod, util}.rs`). Los 6 archivos Dart bloc de `application/row/` viven en F02.0.1.2 (`database-application-domain-misc.md`) y se cross-referencian sin reclamar.

**Suite `validate-B3.F02.3.sh` 4/4**:
- `template` = 1/1
- `evidence` = 25/25 OK
- `mermaid` = 7/7 bloques OK
- `cobertura` = 5/5 archivos `autor_F02.3`

**Revisor**: `--gate-100 --feature-id F02` → `aprobado, 0 correcciones`.

**Artefactos**:
- `OUT/09-features/F02-bases-de-datos/3-filas-y-row-detail-application-row-relaciones.md`
- `OUT/_ledger/pruebas/B3.F023/{validate-B3.F02.3.sh, validate-B3.F02.3.log, coverage.json, revisor_output.json, README.md}`

## Distribución del código (5 Rust + 6 Dart cubiertos por F02.0.1.2)

| Carpeta | Archivos | Capa |
|---|---:|---|
| `services/database/` | 5 | rust-handler (`database_editor`, `database_observe`, `entities`, `mod`, `util`) |
| `application/row/` | 6 | bloc (`related_row_detail_bloc`, `row_banner_bloc`, `row_cache`, `row_controller`, `row_list`, `row_service`) — F02.0.1.2 |
| **Total Rust cubierto por F02.3** | **5** | rust-handler |

## Cross-references clave

- **F02.0.1.1** — widgets de row.
- **F02.0.1.2** — los 6 BLoCs Dart de `application/row/`.
- **F02.0.2.1** — `Row`, `RowCell`, `RowUpdate`, `RelationTypeOption` del lado yrs.
- **F02.1** — `FieldController` usado por `RowBannerBloc`.
- **F02.2** — `CellController` + `CellMemCache` usado por `RowCache`.
- **F02.4** — `FilterController` se dispara por `RowDidChanged`.
- **F02.5** — `SortController` se dispara por `RowDidChanged`.
- **F02.6** — `GroupController` se dispara por `RowDidChanged`.
- **F02.8** — `DatabaseViewEditor` orquesta los `*Controller` por view.
- **F02.9.2** — Grid row/footer: widgets UI de row.