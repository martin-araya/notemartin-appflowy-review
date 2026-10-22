# B3.F02.5 — Orden (`services/sort`)

**ROADMAP ref:** línea 236 (F02.5).

**Resultado (2026-10-20)**: 1 documento `OUT/09-features/F02-bases-de-datos/5-orden-services-sort.md` (~330 líneas, 19 secciones, gate-100) cubriendo los 4 archivos Rust del ledger F02.5 (`services/sort/{controller, entities, mod, task}.rs`). Cobertura completa (Rust puro).

**Suite `validate-B3.F02.5.sh` 4/4**:
- `template` = 1/1
- `evidence` = 21/21 OK
- `mermaid` = 5/5 bloques OK
- `cobertura` = 4/4 archivos `autor_F02.5`

**Revisor**: `--gate-100 --feature-id F02` → `aprobado, 0 correcciones`.

**Artefactos**:
- `OUT/09-features/F02-bases-de-datos/5-orden-services-sort.md`
- `OUT/_ledger/pruebas/B3.F025/{validate-B3.F02.5.sh, validate-B3.F02.5.log, coverage.json, revisor_output.json, README.md}`

## Distribución del código

| Carpeta | Archivos | Capa |
|---|---:|---|
| `services/sort/` | 4 | rust-handler (`controller`, `entities`, `mod`, `task`) |
| **Total Rust** | **4** | rust-handler |

## Cross-references clave

- **F02.0.1.2** — orquestación de `SortController` por vista.
- **F02.0.2.1** — `FieldType`, `TypeOptions` que proveen `handle_cell_compare`.
- **F02.0.2.2** — `SortMap`, `SortMapBuilder` consumido por `Sort::try_from` / `SortMap::from`.
- **F02.2** — `CellCache` compartido por `cmp_cell`.
- **F02.3** — `DatabaseEditor` crea/destruye `SortController` por vista.
- **F02.4** — `SortController` recibe filas filtradas.
- **F02.6** — Agrupación: ortogonal.
- **F02.8** — Field settings + `database_view`: orquestación de sort/filter/group por vista.
- **F02.9.2** — Grid sort/header: `SortEditorBloc`, `MobileRowDetailBloc`, `RowDetyBloc`.