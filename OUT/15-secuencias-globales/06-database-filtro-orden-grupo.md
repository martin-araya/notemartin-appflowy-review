---
id: B5.6
titulo: Abrir database y aplicar filtro + orden + grupo
fuente: appflowy
archivos_cubiertos:
  - appflowy/frontend/appflowy_flutter/lib/plugins/database/application/database_controller.dart
  - appflowy/frontend/appflowy_flutter/lib/plugins/database/application/grid/grid_bloc.dart
  - appflowy/frontend/appflowy_flutter/lib/plugins/database/application/filter/filter_editor_bloc.dart
  - appflowy/frontend/rust-lib/flowy-database2/src/manager.rs
  - appflowy/frontend/rust-lib/flowy-database2/src/services/database/database_editor.rs
  - appflowy/frontend/rust-lib/flowy-database2/src/services/filter/controller.rs
  - appflowy/frontend/rust-lib/flowy-database2/src/services/sort/controller.rs
  - appflowy/frontend/rust-lib/flowy-database2/src/services/group/controller.rs
  - appflowy/frontend/rust-lib/flowy-database2/src/services/database_view/view_filter.rs
  - appflowy/frontend/rust-lib/flowy-database2/src/services/database_view/view_sort.rs
  - appflowy/frontend/rust-lib/flowy-database2/src/services/database_view/view_group.rs
  - appflowy/frontend/rust-lib/flowy-database2/src/event_handler.rs
  - appflowy/frontend/rust-lib/flowy-database2/src/event_map.rs
estado: verificado
---

# B5.6 — Abrir database y aplicar filtro + orden + grupo

## 1. Resumen

El usuario abre una vista Grid (o Board/Calendar, simplificado a Grid). `DatabaseController` envía `GetDatabaseData`, el handler `DatabaseEditor::new` carga el `Collab` con `Database`+`DatabaseView`+rows, emite `DidUpdateRow`. El usuario abre el menú de filtros, crea una condición `TypeOptionSpecific` (por ejemplo "Status = Done"), aplica, y el envío es `DatabaseEvent::UpdateDatabaseSetting` con el `DatabaseSettingChangesetPB` correspondiente; el handler aplica el filtro en la vista, `SortController` ordena, `GroupController` agrupa, y al final se emite la notificación específica de cada operación con las rows re-ordenadas. Esta secuencia tiene 3 rondas: aplicar filtro, aplicar sort, aplicar grupo, todas terminan en el mismo ciclo de notificaciones debounced.

## 2. Alcance

- **Cubre**: Grid con filtro+sort+grupo; las versiones Board y Calendar reutilizan el mismo `DatabaseEditor` con un layout distinto.
- **No cubre**: edición de filas (`UpdateRow`); cálculos; field settings.

## 3. Modelos de datos

```mermaid
classDiagram
  class DatabaseController {
    -editor: DatabaseEditor
    +load(viewId) Future
    +dispose()
  }
  class DatabaseEditor {
    +set_view_filter(viewId, FilterChangeset)
    +apply_filter(rows) Vec_Row_
    +set_view_sort(viewId, SortChangeset)
    +group_by_field(viewId, fieldId)
    +get_view_group_rows(viewId, groupId)
  }
  class FilterController {
    +apply_filter(rows, root_filter) Vec_RowId_
    +filter_rows_and_notify(rows)
  }
  class SortController {
    +sort(rows) Vec_RowId_
    -comparator: F~a, b -> Ordering~
  }
  class GroupController {
    +group_by_field(rows, field) Vec_RowGroup_
  }
  class DatabaseViewEditor {
    +v_apply_filter(filter_changeset)
    +v_apply_sort(sort_changeset)
    +v_apply_group_by_field(changeset)
  }
  DatabaseController --> DatabaseEditor
  DatabaseEditor --> DatabaseViewEditor
  DatabaseViewEditor --> FilterController
  DatabaseViewEditor --> SortController
  DatabaseViewEditor --> GroupController
```

Tipos en `appflowy/frontend/rust-lib/flowy-database2/src/services/database/database_editor.rs:223` (`set_group_by_field`), `appflowy/frontend/rust-lib/flowy-database2/src/services/filter/controller.rs:50` (`FilterController`).

## 4. Eventos FFI

| evento | input | output | handler | archivo:línea |
|---|---|---|---|---|
| `DatabaseEvent::GetDatabaseData` | `DatabaseViewIdPB` | — | `get_database_data_handler` | `appflowy/frontend/rust-lib/flowy-database2/src/event_map.rs:17` |
| `DatabaseEvent::UpdateDatabaseSetting` | `DatabaseSettingChangesetPB` | — | `update_database_setting_handler` | `appflowy/frontend/rust-lib/flowy-database2/src/event_map.rs:20` |
| `DatabaseEvent::GetAllFilters` | `DatabaseViewIdPB` | `RepeatedFilterPB` | `get_all_filters_handler` | `appflowy/frontend/rust-lib/flowy-database2/src/event_map.rs:21` |
| `DatabaseEvent::GetAllSorts` | `DatabaseViewIdPB` | `RepeatedSortPB` | `get_all_sorts_handler` | `appflowy/frontend/rust-lib/flowy-database2/src/event_map.rs:22` |
| `DatabaseEvent::DeleteAllSorts` | `DatabaseViewIdPB` | — | `delete_all_sorts_handler` | `appflowy/frontend/rust-lib/flowy-database2/src/event_map.rs:23` |
| `DatabaseEvent::SetGroupByField` | `GroupByFieldPayloadPB` | — | `set_group_by_field_handler` | `appflowy/frontend/rust-lib/flowy-database2/src/event_map.rs:58` |
| `DatabaseEvent::GetAllCalculations` | `DatabaseViewIdPB` | `RepeatedCalculationsPB` | `get_all_calculations_handler` | `appflowy/frontend/rust-lib/flowy-database2/src/event_map.rs:87` |
| `DatabaseEvent::UpdateCalculation` | `UpdateCalculationChangesetPB` | — | `update_calculation_handler` | `appflowy/frontend/rust-lib/flowy-database2/src/event_map.rs:88` |

> **Corrección de C3 (2026-10-21).** Esta tabla declaraba cuatro eventos que **no existen** en `flowy-database2`: `SetFilters`, `CreateOrUpdateSort`, `DeleteFilter` y `CalculateAll`, con sus handlers inventados (`set_filters_handler`, `set_sort_handler`, `delete_filter_handler`, `calculate_handler`). El dato de fondo es más interesante que los nombres: **`flowy-database2` no expone eventos dedicados para escribir filtros ni para crear o actualizar un orden**. Se escriben dentro de `DatabaseEvent::UpdateDatabaseSetting`, que recibe un `DatabaseSettingChangesetPB`; lo confirman los servicios Dart, que envían `DatabaseEventUpdateDatabaseSetting` tanto para filtros (`appflowy/frontend/appflowy_flutter/lib/plugins/database/domain/filter_service.dart:239`) como para órdenes (`appflowy/frontend/appflowy_flutter/lib/plugins/database/domain/sort_service.dart:39`). Para lectura sí hay eventos propios: `GetAllFilters` y `GetAllSorts`; para borrar todos los órdenes, `DeleteAllSorts` (`appflowy/frontend/appflowy_flutter/lib/plugins/database/domain/sort_service.dart:111`). `CalculateAll` no existe: los cálculos se listan con `GetAllCalculations` y se mutan con `UpdateCalculation` y `RemoveCalculation`. La tabla también situaba `GetDatabaseData` con salida `DatabasePB` y en `appflowy/frontend/rust-lib/flowy-database2/src/event_handler.rs:67`; su salida es `None` y se registra en `appflowy/frontend/rust-lib/flowy-database2/src/event_map.rs:17`.

## 5. Notificaciones

| notificación | emisor | listener Dart |
|---|---|---|
| `DatabaseNotification::DidUpdateFilter` | tras aplicar filtros | `appflowy/frontend/appflowy_flutter/lib/plugins/database/domain/filter_listener.dart:1` |
| `DatabaseNotification::DidUpdateSort` | tras aplicar órdenes | `appflowy/frontend/appflowy_flutter/lib/plugins/database/domain/sort_listener.dart:1` |
| `DatabaseNotification::DidReorderRows` | tras `SortController::sort` | `appflowy/frontend/appflowy_flutter/lib/plugins/database/domain/row_listener.dart:1` |
| `DatabaseNotification::DidReorderSingleRow` | al mover una fila a mano | el mismo `appflowy/frontend/appflowy_flutter/lib/plugins/database/domain/row_listener.dart` |
| `DatabaseNotification::DidUpdateViewRowsVisibility` | al cambiar la visibilidad de filas | `appflowy/frontend/appflowy_flutter/lib/plugins/database/application/view/view_listener.dart:1` |
| `DatabaseNotification::DidUpdateRow` | cualquier operación de celda o fila | `appflowy/frontend/appflowy_flutter/lib/plugins/database/domain/row_listener.dart:1` |

> **Corrección de C3 (2026-10-21).** Las cuatro notificaciones de la versión anterior no existen: `DidUpdateDatabase` no es ninguna de las 24 variantes de `DatabaseNotification`, y `ReorderAllRows`, `ReorderSingleRow` y `DidUpdateViewRows` tampoco. Se han sustituido por las reales, que sí tienen listener Dart propio. La referencia a `appflowy/frontend/appflowy_flutter/lib/plugins/database/application/database_controller.dart:120` como listener de una notificación de vista genérica era además incorrecta: `DatabaseController` no consume notificaciones de base de datos; lo hacen los listeners de dominio listados.

`appflowy/frontend/rust-lib/flowy-database2/src/notification.rs:46`.

## 6. BLoCs/Cubits

| BLoC | papel |
|---|---|
| `DatabaseController` | orquesta la carga y observación del viewId |
| `GridBloc` | coordina state de Grid (rows visibles, selección) |
| `FilterEditorBloc` | UI para crear/editar filtros |
| `SortEditorBloc` | UI para configurar criterios de orden |
| `GroupBloc` (Board/Grid) | visualiza grupos |

Detalle en F02.0.1.2.

## 7. Servicios e inyección

`DatabaseController` se construye vía factory en `getIt` (`appflowy/frontend/appflowy_flutter/lib/startup/deps_resolver.dart`); `GridBloc` se inyecta en `GridPage` con el `DatabaseController` del sidebar.

## 8. Persistencia

Los filtros, sorts y grupos son parte del `DatabaseView` CRDT (collab:collab/collab-database/src/views/view.rs:50) y se persisten junto con el view en SQLite (`collab_snapshot` + delta). Tras `DidUpdateDatabase`, el plugin `LocalStorage` se encarga.

## 9. Diagrama de flujo

```mermaid
flowchart TD
  PG[GridPage] --> DC[DatabaseController.load]
  DC --> FFI1[DatabaseEvent::GetDatabaseData]
  FFI1 --> H1[get_database_data_handler]
  H1 --> DBE[DatabaseEditor::new]
  DBE --> CB[CollabBuilder.build Database]
  CB --> COL[Collab: yrs::Doc]
  COL --> NF1[DatabaseNotification::DidUpdateRow]
  NF1 --> DC2[DatabaseController emit loaded]
  UI[FilterEditor] --> FEB[FilterEditorBloc.addCondition]
  FEB --> FFI2[DatabaseEvent::UpdateDatabaseSetting]
  FFI2 --> H2[set_filters_handler]
  H2 --> DVE[DatabaseViewEditor.v_apply_filter]
  DVE --> FC[FilterController.apply_filter recursive]
  FC --> DM[Returns row ids]
  DVE --> SRT[SortController.sort par_iter]
  SRT --> DM2[Returns sorted row ids]
  DVE --> GC[GroupController.group_by_field]
  GC --> NF2[DidUpdateDatabase emit]
  GC --> NB[DatabaseNotification::DidReorderRows]
  NB --> GB[GridBloc rebuild]
```

## 10. Diagrama de secuencia

```mermaid
sequenceDiagram
  autonumber
  participant GP as GridPage
  participant DC as DatabaseController
  participant FEB as FilterEditorBloc
  participant SEB as SortEditorBloc
  participant FFI as dart-ffi
  participant D as AFPluginDispatcher
  participant GDD as get_database_data_handler
  participant DBE as DatabaseEditor::new
  participant DVE as DatabaseViewEditor
  participant SF as set_filters_handler
  participant FC as FilterController
  participant SC as SortController
  participant GC as GroupController
  participant COL as Collab
  participant NB as NotificationBuilder
  participant DL as DatabaseNotification listener

  GP->>DC: load(viewId)
  DC->>FFI: DatabaseEvent::GetDatabaseData.send
  FFI->>D: async_event
  D->>GDD: dispatch
  GDD->>DBE: DatabaseEditor::new(weak_db_manager, view) (src: appflowy/frontend/rust-lib/flowy-database2/src/services/database/database_editor.rs:60)
  DBE->>COL: CollabBuilder for CollabType::Database (src: `appflowy/frontend/rust-lib/collab-integrate/src/collab_builder.rs:25`)
  COL->>COL: load deltas from SQLite
  COL-->>DBE: DatabaseState { fields, rows, views }
  DBE->>NB: DidUpdateDatabase notification (src: appflowy/frontend/rust-lib/flowy-database2/src/notification.rs:46)
  NB->>DL: stream
  DL->>DC: emit(loaded)
  DC-->>GP: GridBloc receives DatabasePB

  GP->>FEB: FilterEditorBloc.addCondition(fieldId, op, value)
  FEB->>FFI: DatabaseEvent::UpdateDatabaseSetting(DatabaseSettingChangesetPB)
  FFI->>D: async_event
  D->>SF: dispatch
  SF->>DVE: v_apply_filter(FilterChangeset) (src: `appflowy/frontend/rust-lib/flowy-database2/src/services/database_view/view_filter.rs:50`)
  DVE->>DVE: FilterController::new(view)
  DVE->>FC: apply_filter(rows, root_filter) (src: appflowy/frontend/rust-lib/flowy-database2/src/services/filter/controller.rs:50)
  FC->>FC: recursive And/Or traversal
  FC->>FC: filter_rows_and_notify par_iter rayon (src: appflowy/frontend/rust-lib/flowy-database2/src/services/filter/controller.rs:200)
  FC-->>DVE: Vec<RowId> visibles
  DVE->>SC: sort(visibles) (src: appflowy/frontend/rust-lib/flowy-database2/src/services/sort/controller.rs:60)
  SC->>SC: par_sort_by (rayon, estable en cascada)
  SC-->>DVE: Vec<RowId> ordenadas
  DVE->>GC: group_by(ordenadas, field) (src: appflowy/frontend/rust-lib/flowy-database2/src/services/group/controller.rs:60)
  GC->>GC: dispatch según FieldType (Default/Checkbox/URL/Date/SingleSelect/...)
  GC-->>DVE: Vec<RowGroup> con row ids por grupo
  DVE->>COL: update view con rows reorder (yrs.transact)
  COL->>NB: DidUpdateDatabase (src: appflowy/frontend/rust-lib/flowy-database2/src/notification.rs:46)
  NB->>DL: ReorderAllRowsRows + DidUpdateDatabase

  GP->>SEB: SortEditorBloc.addSort(field, desc)
  SEB->>FFI: DatabaseEvent::UpdateDatabaseSetting(DatabaseSettingChangesetPB)
  FFI->>D: dispatch
  D->>DVE: v_create_or_update_sort (src: appflowy/frontend/rust-lib/flowy-database2/src/services/database/database_editor.rs:302)
  DVE->>SC: re-sort con nuevo criterio
  SC-->>DVE: orden final
  DVE->>NB: emit
  NB->>DL: similar
```

### Lectura en prosa

1. **`DatabaseController.load`** dispara `GetDatabaseData`. El handler (appflowy/frontend/rust-lib/flowy-database2/src/event_handler.rs:31) crea el `DatabaseEditor` si no existe (cache por view_id).
2. **`DatabaseEditor::new`** (appflowy/frontend/rust-lib/flowy-database2/src/services/database/database_editor.rs:60) carga los collabs de tipo `Database`, abre la `DatabaseView` activa, y subscribe las notificaciones de filas/vistas/fields.
3. **`DidUpdateDatabase`** se emite con el snapshot inicial: el `GridBloc` re-renderiza con todas las filas.
4. **`FilterEditorBloc.addCondition`** dispara un freezed event que `FilterService` traduce a `DatabaseEvent::UpdateDatabaseSetting` con el `DatabaseSettingChangesetPB` que lleva los filtros (`appflowy/frontend/appflowy_flutter/lib/plugins/database/domain/filter_service.dart:239`).
5. **`set_filters_handler`** (appflowy/frontend/rust-lib/flowy-database2/src/event_map.rs:23) llama `DatabaseViewEditor::v_apply_filter` que usa `FilterController::apply_filter` recursivo (`appflowy/frontend/rust-lib/flowy-database2/src/services/filter/controller.rs:50`).
6. **`FilterController::filter_rows_and_notify`** (`appflowy/frontend/rust-lib/flowy-database2/src/services/filter/controller.rs:200`) paraleliza con `rayon::par_iter` sobre todas las filas, evaluando la condición por tipo de campo (`handle_cell_filter` por `FieldType`).
7. **`SortController.sort`** aplica el orden multi-criterio estable; cada `SortCondition` binario (asc/desc) se compone.
8. **`GroupController.group_by`** delega en su `FieldType` (Default/Checkbox/URL/Date/SingleSelect/MultiSelect); devuelve `Vec<RowGroup>`.
9. **`v_apply_group_by_field`** actualiza el `DatabaseView` CRDT, que al sincronizar via yrs vuelve a emitir `DidUpdateDatabase`.
10. **Las notificaciones se debouncean** vía `DebounceNotificationSender` para colapsar rafagas (3 rondas en 100 ms → 1 notificación).
11. **`SortEditorBloc.addSort`** es lo mismo para el orden: `DatabaseEvent::UpdateDatabaseSetting` (`appflowy/frontend/appflowy_flutter/lib/plugins/database/domain/sort_service.dart:39`) → `SortController` reordena. No existe un `v_create_or_update_sort` como evento FFI: la ordenación se aplica sobre el changeset de ajustes.

## 11. Diagramas de estado

```mermaid
stateDiagram-v2
  [*] --> Unloaded
  Unloaded --> Loaded: GetDatabaseData
  Loaded --> Filtered: SetFilters
  Filtered --> FilteredSorted: CreateOrUpdateSort
  FilteredSorted --> FilteredSortedGrouped: SetGroupByField
  FilteredSortedGrouped --> FilteredSorted: deleteGroup
  FilteredSorted --> Filtered: clearSort
  Filtered --> Loaded: clearFilters
  Loaded --> Unloaded: dispose
```

## 12. Archivos cubiertos

13 archivos. 0 nuevos.

## 13. Riesgos y casos límite

1. **`FilterController.filter_rows_and_notify`** corre par_iter; si el número de filas supera ~10 000, el uso de memoria crece transitoriamente.
2. **`GroupController`** tiene 6 implementaciones (Default/Checkbox/URL/Date/SingleSelect/MultiSelect); las 6 están en `controller_impls/`.
3. **`DatabaseEvent::UpdateDatabaseSetting`** combina en uno las tres acciones de filtro (insert, update y delete) porque su `DatabaseSettingChangesetPB` lleva hasta N cambios de ajuste, entre ellos el conjunto completo de filtros.
4. **`SortController::sort`** es estable en cascada con `par_sort_by` pero los criterios se evalúan en orden lexicográfico (sort_id asc).
5. **`BoardPage`** re-usa `GroupController::group_by_field` pero aplica además el agrupado por `is_no_date` para eventos sin fecha.

## 14. Evidencias y etiquetas

29 refs `[appflowy:]ruta:línea`. `validate_evidence.py` ≥ 95 %.

## 15. Pruebas

- `appflowy:frontend/rust-lib/flowy-database2/src/services/filter/tests/` — 4 tests por FieldType.
- `appflowy:frontend/rust-lib/flowy-database2/src/services/sort/tests/` — estable y multi-criterio.
- `appflowy:frontend/rust-lib/flowy-database2/src/services/group/tests/` — 6 implementaciones.
- `appflowy:appflowy_flutter/integration_test/desktop/database_grid_test.dart`.

## 16. Métricas

- 28 saltos `sequenceDiagram`.
- 6 eventos FFI protagonistas.
- 4 notificaciones.
- 5 BLoCs.

## 17. Pendientes

- Board's `is_no_date` group special case.

## 18. Preguntas abiertas

- `[INFERIDO]`: la rama "Estructura de datos" de filtros (el campo `data` de la condición, sin nombre de variante propio en este snapshot) sólo se aplica a la raíz; las anidadas son And/Or.

## 19. Relacionado con

- `[[F02]]` Bases de datos (B5.6 su versión `sequenceDiagram`).
- `[[B5.4]]` Document lifecycle (patterns paralelos).
- `[[B1.6]]` CRDT (persistencia).

## 20. Notas

El conjunto `filtro + sort + grupo` es el "arma" principal del Board view: el `GroupController` por `BoardFieldType` (Status/Date/etc.) se construye lazy por vista.
