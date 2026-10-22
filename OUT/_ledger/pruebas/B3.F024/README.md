# B3.F02.4 — Filtros (`services/filter`)

**ROADMAP ref:** línea 235 (F02.4).

**Resultado (2026-10-20)**: 1 documento `OUT/09-features/F02-bases-de-datos/4-filtros-services-filter.md` (~380 líneas, 19 secciones, gate-100) cubriendo los 4 archivos Rust del ledger F02.4 (`services/filter/{controller, entities, mod, task}.rs`). Cobertura completa (Rust puro).

**Suite `validate-B3.F02.4.sh` 4/4**:
- `template` = 1/1
- `evidence` = 23/23 OK
- `mermaid` = 4/4 bloques OK
- `cobertura` = 4/4 archivos `autor_F02.4`

**Revisor**: `--gate-100 --feature-id F02` → `aprobado, 0 correcciones`.

**Artefactos**:
- `OUT/09-features/F02-bases-de-datos/4-filtros-services-filter.md`
- `OUT/_ledger/pruebas/B3.F024/{validate-B3.F02.4.sh, validate-B3.F02.4.log, coverage.json, revisor_output.json, README.md}`

## Distribución del código

| Carpeta | Archivos | Capa |
|---|---:|---|
| `services/filter/` | 4 | rust-handler (`controller`, `entities`, `mod`, `task`) |
| **Total Rust** | **4** | rust-handler |

## Cross-references clave

- **F02.0.1.2** — orquestación de `FilterController` por vista (manager, services/database_view/).
- **F02.0.2.1** — `FieldType`, `TypeOptions` que proveen los `*_filter.rs` por tipo.
- **F02.0.2.2** — `FilterMap`, `FilterMapBuilder` consumido por `Filter::try_from` / `FilterMap::from`.
- **F02.1** — 12 `services/field/type_options/*/<familia>_filter.rs` implementan los predicados.
- **F02.2** — `CellCache` compartido por `filter_row` y `apply_filter`.
- **F02.3** — `DatabaseEditor` crea/destruye `FilterController` por vista.
- **F02.5** — `SortController` recibe filas filtradas.
- **F02.6** — Agrupación: ortogonal.
- **F02.8** — Field settings + `database_view`: orquestación de sort/filter/group por vista.
- **F02.9.1** — Grid filter UI: `FilterEditorBloc`, 12 `choicechip/*_filter.dart`.