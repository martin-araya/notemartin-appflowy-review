# Auditoría de la fuga de F02 (Fase 0.1)

Audita los archivos con `feature_ids=F02` que siguen en `pendiente` tras el
cierre de F02 declarado en el ROADMAP. Cada ruta se clasifica comparándola con
las referencias `[fuente:]ruta:línea` extraídas por `validate_evidence.extract_refs`
de los 21 documentos de `OUT/09-features/F02-bases-de-datos/`.

## Resultado

- Fugas detectadas: **114**
- (a) citadas literalmente en algún doc: **10** → marcables como `verificado` con `verificado_por=autor_<doc>`
- (b) mencionadas (frontmatter o §12) pero sin cita `ruta:línea`: **0** → hay que **añadir la cita** al doc y re-validar antes de marcar
- (c) sin cobertura en ningún doc: **104** → requieren documento nuevo

## Distribución por grupo

| Grupo | (a) citado | (b) mencionado sin cita | (c) sin cubrir | Total |
|---|---:|---:|---:|---:|
| `raiz de flowy-database2` | 4 | 0 | 5 | 9 |
| `src/entities/**` | 4 | 0 | 45 | 49 |
| `src/{services,utils}` | 2 | 0 | 3 | 5 |
| `tests/database/**` | 0 | 0 | 51 | 51 |
| **Total** | **10** | **0** | **104** | **114** |

## Detalle (a) — citadas literalmente

| Ruta | Cita |
|---|---|
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/calculation/calculation_changeset.rs` | 7-calculos-services-calculations-application-calculations.md:133, 7-calculos-services-calculations-application-calculations.md:435 |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/calculation/calculation_entities.rs` | 7-calculos-services-calculations-application-calculations.md:83, 7-calculos-services-calculations-application-calculations.md:133, 7-calculos-services-calculations-application-calculations.md:455, 7-calculos-services-calculations-application-calculations.md:456, 7-calculos-services-calculations-application-calculations.md:507, 7-calculos-services-calculations-application-calculations.md:525 |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/database_entities.rs` | 12-tab-bar-de-vistas-sync-de-database-snapshots.md:247 |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/setting_entities.rs` | 9.1-grid-filtros-y-filter-choicechips.md:116, 9.1-grid-filtros-y-filter-choicechips.md:117, 9.1-grid-filtros-y-filter-choicechips.md:118, 9.1-grid-filtros-y-filter-choicechips.md:119, 9.1-grid-filtros-y-filter-choicechips.md:200 |
| `appflowy/frontend/rust-lib/flowy-database2/src/event_handler.rs` | 12-tab-bar-de-vistas-sync-de-database-snapshots.md:101, 12-tab-bar-de-vistas-sync-de-database-snapshots.md:212, 12-tab-bar-de-vistas-sync-de-database-snapshots.md:453, 7-calculos-services-calculations-application-calculations.md:206, 7-calculos-services-calculations-application-calculations.md:207, 7-calculos-services-calculations-application-calculations.md:208, 7-calculos-services-calculations-application-calculations.md:410, 7-calculos-services-calculations-application-calculations.md:466, 9.1-grid-filtros-y-filter-choicechips.md:407 |
| `appflowy/frontend/rust-lib/flowy-database2/src/event_map.rs` | 12-tab-bar-de-vistas-sync-de-database-snapshots.md:212, 12-tab-bar-de-vistas-sync-de-database-snapshots.md:212, 7-calculos-services-calculations-application-calculations.md:30, 7-calculos-services-calculations-application-calculations.md:30, 7-calculos-services-calculations-application-calculations.md:206, 7-calculos-services-calculations-application-calculations.md:207, 7-calculos-services-calculations-application-calculations.md:208, 7-calculos-services-calculations-application-calculations.md:466, 9.1-grid-filtros-y-filter-choicechips.md:115, 9.1-grid-filtros-y-filter-choicechips.md:115, 9.1-grid-filtros-y-filter-choicechips.md:116, 9.1-grid-filtros-y-filter-choicechips.md:120, 9.1-grid-filtros-y-filter-choicechips.md:120, 9.1-grid-filtros-y-filter-choicechips.md:121, 9.1-grid-filtros-y-filter-choicechips.md:121, 9.1-grid-filtros-y-filter-choicechips.md:122, 9.1-grid-filtros-y-filter-choicechips.md:122 |
| `appflowy/frontend/rust-lib/flowy-database2/src/manager.rs` | 12-tab-bar-de-vistas-sync-de-database-snapshots.md:100, 12-tab-bar-de-vistas-sync-de-database-snapshots.md:242, 12-tab-bar-de-vistas-sync-de-database-snapshots.md:242, 12-tab-bar-de-vistas-sync-de-database-snapshots.md:464 |
| `appflowy/frontend/rust-lib/flowy-database2/src/notification.rs` | 12-tab-bar-de-vistas-sync-de-database-snapshots.md:70, 12-tab-bar-de-vistas-sync-de-database-snapshots.md:89, 12-tab-bar-de-vistas-sync-de-database-snapshots.md:222, 12-tab-bar-de-vistas-sync-de-database-snapshots.md:223, 7-calculos-services-calculations-application-calculations.md:31, 7-calculos-services-calculations-application-calculations.md:230, 7-calculos-services-calculations-application-calculations.md:466, 9.1-grid-filtros-y-filter-choicechips.md:132, 9.1-grid-filtros-y-filter-choicechips.md:133, 9.1-grid-filtros-y-filter-choicechips.md:135 |
| `appflowy/frontend/rust-lib/flowy-database2/src/services/mod.rs` | 12-tab-bar-de-vistas-sync-de-database-snapshots.md:98 |
| `appflowy/frontend/rust-lib/flowy-database2/src/utils/cache.rs` | 7-calculos-services-calculations-application-calculations.md:142, 7-calculos-services-calculations-application-calculations.md:142 |

## Detalle (b) — mencionadas sin cita

| Ruta | Grupo |
|---|---|

## Detalle (c) — sin cubrir

| Ruta | Grupo |
|---|---|
| `appflowy/frontend/rust-lib/flowy-database2/Cargo.toml` | `raiz de flowy-database2` |
| `appflowy/frontend/rust-lib/flowy-database2/Flowy.toml` | `raiz de flowy-database2` |
| `appflowy/frontend/rust-lib/flowy-database2/build.rs` | `raiz de flowy-database2` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/board_entities.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/calculation/mod.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/calendar_entities.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/cell_entities.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/field_entities.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/field_settings_entities.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/file_entities.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/filter_entities/checkbox_filter.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/filter_entities/checklist_filter.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/filter_entities/date_filter.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/filter_entities/filter_changeset.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/filter_entities/media_filter.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/filter_entities/mod.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/filter_entities/number_filter.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/filter_entities/relation_filter.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/filter_entities/select_option_filter.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/filter_entities/text_filter.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/filter_entities/time_filter.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/filter_entities/util.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/group_entities/configuration.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/group_entities/group.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/group_entities/group_changeset.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/group_entities/mod.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/macros.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/mod.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/parser.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/position_entities.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/row_entities.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/share_entities.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/sort_entities.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/type_option_entities/checkbox_entities.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/type_option_entities/checklist_entities.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/type_option_entities/date_entities.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/type_option_entities/media_entities.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/type_option_entities/mod.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/type_option_entities/number_entities.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/type_option_entities/relation_entities.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/type_option_entities/select_option_entities.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/type_option_entities/summary_entities.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/type_option_entities/text_entities.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/type_option_entities/time_entities.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/type_option_entities/timestamp_entities.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/type_option_entities/translate_entities.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/type_option_entities/url_entities.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/entities/view_entities.rs` | `src/entities/**` |
| `appflowy/frontend/rust-lib/flowy-database2/src/lib.rs` | `raiz de flowy-database2` |
| `appflowy/frontend/rust-lib/flowy-database2/src/services/setting/entities.rs` | `src/{services,utils}` |
| `appflowy/frontend/rust-lib/flowy-database2/src/services/setting/mod.rs` | `src/{services,utils}` |
| `appflowy/frontend/rust-lib/flowy-database2/src/template.rs` | `raiz de flowy-database2` |
| `appflowy/frontend/rust-lib/flowy-database2/src/utils/mod.rs` | `src/{services,utils}` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/block_test/mod.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/block_test/row_test.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/block_test/script.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/calculations_test/calculation_test.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/calculations_test/mod.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/calculations_test/script.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/cell_test/mod.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/cell_test/script.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/cell_test/test.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/database_editor.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/field_settings_test/mod.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/field_settings_test/script.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/field_settings_test/test.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/field_test/mod.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/field_test/script.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/field_test/test.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/field_test/util.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/filter_test/advanced_filter_test.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/filter_test/checkbox_filter_test.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/filter_test/checklist_filter_test.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/filter_test/date_filter_test.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/filter_test/mod.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/filter_test/number_filter_test.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/filter_test/script.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/filter_test/select_option_filter_test.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/filter_test/text_filter_test.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/filter_test/time_filter_test.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/group_test/date_group_test.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/group_test/mod.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/group_test/script.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/group_test/test.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/group_test/url_group_test.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/layout_test/mod.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/layout_test/script.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/layout_test/test.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/mock_data/board_mock_data.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/mock_data/calendar_mock_data.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/mock_data/grid_mock_data.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/mock_data/mod.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/mod.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/pre_fill_cell_test/mod.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/pre_fill_cell_test/pre_fill_row_according_to_filter_test.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/pre_fill_cell_test/pre_fill_row_with_payload_test.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/pre_fill_cell_test/script.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/share_test/export_test.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/share_test/mod.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/sort_test/mod.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/sort_test/multi_sort_test.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/sort_test/script.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/database/sort_test/single_sort_test.rs` | `tests/database/**` |
| `appflowy/frontend/rust-lib/flowy-database2/tests/main.rs` | `tests/database/**` |
