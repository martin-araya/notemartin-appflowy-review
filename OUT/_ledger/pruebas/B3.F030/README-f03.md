# B3.F03 — Folder, workspaces, espacios, vistas, view_management

**ROADMAP ref:** línea 287 (`B3.F03`).

**Resultado (2026-10-20)**: F03 se ha dividido en **4 sub-unidades** (116 archivos) y cerrado con **4 documentos** en `OUT/09-features/F03-folder-workspaces-vistas/`.

| Sub | Doc | Líneas | Archivos | Secciones | Refs | Mermaid | Suite | Revisor |
|---|---|---:|---:|---:|---:|---:|---|---|
| **F03.0** | `0.0-indice-folder-workspaces-vistas.md` | 595 | 0 (índice) | 19 | 102 | 4 | ✅ | aprobado |
| **F03.1** | `0.1-vistas-workspaces-sidebar-dart.md` | 779 | 55 (Dart) | 19 | 279 | 5 | ✅ | aprobado |
| **F03.2** | `0.2-flowy-folder-rust.md` | 747 | 33 (Rust) | 19 | 262 | 5 | ✅ | aprobado |
| **F03.3** | `0.3-collab-folder.md` | 704 | 28 (Collab) | 19 | 286 | 4 | ✅ | aprobado |
| | | **2 825** | **116** | | **929** | **18** | | |

Todas las suites: `template=1/1`, `evidence=N/N`, `mermaid=N OK`, `cobertura=N/N`, `revisor=aprobado, 0 correcciones`.

## Por qué 4 documentos

El plan `~/.local/share/kilo/plans/1792504481368-b3-f03-f07-cierre-plan.md` (§1, D1) decidió el corte **por lenguaje/fuente**, siguiendo el precedente `F02.0.1` (appflowy) / `F02.0.2` (collab) y `F01.0` (índice + sub-unidades). El corte se declara en `SKILL/scripts/build_units.py::SUBDIVISIONS["F03"]`, de modo que sobrevive a cualquier regeneración y no requiere un script de split aparte.

## Suites

| Suite | Fichero | Resultado |
|---|---|---|
| B3.F030 | `validate-B3.F030.sh` | OK (cobertura 0/0, índice) |
| B3.F031 | `validate-B3.F031.sh` | OK (cobertura 55/55) |
| B3.F032 | `validate-B3.F032.sh` | OK (cobertura 33/33) |
| B3.F033 | `validate-B3.F033.sh` | OK (cobertura 28/28) |

## Pruebas literales superadas

- **51/51 `FolderEvent`** tabulados en F03.2 §4, y agrupados en 9 dominios en F03.0 §4: vista (15) + workspace (8) + papelera (5) + recientes (2) + favoritos (2) + publicación (11) + compartido (5) + import (2) + snapshot (1) = **51**.
- **19/19 `FolderNotification`** tabuladas en F03.2 §5 y agrupadas en 8 dominios en F03.0 §5: workspace (5) + vista (5) + papelera (1) + favoritos (2) + recientes (1) + sync/snapshot (2) + compartido (2) + centinela (1) = **19**.
- **14 BLoCs Dart** de F03.1 + 3 listeners reactivos + 3 servicios; **73 eventos freezed**.
- **13 ficheros de test** de `collab-folder/tests/folder_test/` documentados uno a uno en F03.3 §15.
- Distribución de los 51 eventos por consumidor Dart (F03.1 §4): **23** despachados desde la unidad · **23** con consumidor en otra unidad (F04, F01/F02, F11, F05.1) · **5 sin consumidor Dart**.

## Hallazgos materiales

1. **`features/view_management/` está vacío**: `README.md` 0 bytes y los 3 `.dart` 1 byte. `ViewManagementBloc` **no existe** en este snapshot. El ROADMAP asignaba ese feature a B3.F03; el triage de B0.2 lo dejó en F04. Declarado en F03.0 §2/§13, F03.1 y F04 §2.3/§13 (R1).
2. **Hueco del extractor de notificaciones**: `extract_notifications.py` marca `emitted_in_rust = 0` para las 19 variantes de `FolderNotification` porque solo reconoce `NotificationBuilder::new` literal y `flowy-folder` emite vía el envoltorio `folder_notification_builder` (frontend/rust-lib/flowy-folder/src/notification.rs:48–55). Emisores reales: `manager.rs` (845, 879, 1329, 1927–1951, 1990, 2016, 2449) y `manager_observer.rs` (100, 148, 191, 210, 218, 228, 236, 269). **Afecta a F03.2, F04, F06, F12 y F15.**
3. **5 `FolderNotification` declaradas y nunca emitidas**: `DidCreateWorkspace`, `DidUpdateWorkspace`, `DidDeleteView`, `DidRestoreView`, `DidUpdateFolderSnapshotState` (tres tienen rama Dart).
4. **Nombres reales de evento** (verificados contra `event_map.rs`): `UpdateView` (no `RenameView`), `DeleteView` (no `MoveViewToTrash`), `ListTrashItems` (no `GetTrashViews`). La clase real del listener es `RecentViewsListener` y **no contiene ningún `case FolderNotification`** (filtra solo por subject).
5. **5 `FolderEvent` huérfanas**: `CreateFolderWorkspace`, `DeleteWorkspace`, `CopyLink` (declaradas, **sin handler**) y `GetFolderSnapshots`, `ReadCurrentWorkspaceViews` (con handler frontend/rust-lib/flowy-database2/src/event_handler.rs:31–39 y `:42–49`, **sin consumidor Dart**).
6. **`WorkspaceBloc._fetchWorkspaces` descarta la lista recibida** (frontend/appflowy_flutter/lib/workspace/application/workspace/workspace_bloc.dart:52): el bloc es hoy un no-op.
7. **B1.6 contiene campos y variantes que no existen** en `collab-folder` rev `4dfccef`: `layout_settings`, `cover`, `is_space`, `display_mode`, `view_space_status`, `desc` (como campo del struct) y la variante `ViewLayout::AIChat`. F03.3 §2 traza qué repite B1.6 y qué corrige. **Pendiente de resolver en la fase C3 (revisión cruzada de consistencia).**
8. **Fixtures binarias no inventariadas**: `collab-folder/tests/folder_test/history_folder/folder_{with,without}_fav_v1.zip` son necesarias para los tests de migración (`util.rs:207` las descomprime) pero no están en `inventario.json`.

## Correcciones de scope (ROADMAP vs ledger)

| Prometido en el ROADMAP B3.F03 | Realidad en el ledger | Declarado en |
|---|---|---|
| `view_management` | 4 archivos en **F04**, **vacíos**; `ViewManagementBloc` no existe | F03.0 §2/§13, F03.1 §2/§13, F04 §2.3/§13 |
| espacios (spaces) | 12 widgets de `sidebar/space/` + `space_bloc`/`space_search_bloc` en **F03.1** (no hay feature propia) | F03.1 §2/§13, F03.0 §13 |
| papelera / favoritos / recientes / sidebar | **F04** (`plugins/trash/**`, `application/favorite/**`, `application/recent/**`, `presentation/home/menu/sidebar/*`) | F03.0 §13, F03.1 §13, F03.2 §2 |
| `FolderEvent` sin handler | `CreateFolderWorkspace`, `DeleteWorkspace`, `CopyLink` sin handler ni consumidor Dart | F03.2 §4/§18, F03.0 §13 |
| migraciones | `collab-folder/src/folder_migration.rs` (F03.3) ≠ `flowy-user/src/migrations/**` (**F05.2**) ≠ esquema diesel (**B1.7**) | F03.0 §13, F03.3 §2/§13 |

## Artefactos

- `OUT/09-features/F03-folder-workspaces-vistas/{0.0-indice-folder-workspaces-vistas.md, 0.1-vistas-workspaces-sidebar-dart.md, 0.2-flowy-folder-rust.md, 0.3-collab-folder.md}`
- `OUT/_ledger/pruebas/B3.F03{0,1,2,3}/{validate-B3.F03*.sh, revisor_output.json, README.md}`

## Cross-references

- **F04** — sidebar, favoritos, recientes, papelera, tabs, command palette, `view_management` (vacío).
- **F05** — `Workspace` visto desde el usuario (`manager_user_workspace.rs`, `migrations/workspace_*.rs`).
- **F06** — `af_cloud/impls/folder.rs`: lado servidor del sync de folder.
- **F07** — `flowy-server/impls/file_storage.rs` y covers que referencian vistas.
- **F12** — `DidUpdateSharedViews` / `DidUpdateSharedUsers` y la UI de compartir.
- **F11 / B4** — `entities/import.rs`, `share/mod.rs`, `publish.rs` (import, export y publicación web).
- **B1.6** `07-motor-colaborativo-crdt/` — modelo `Collab`, `CollabType::Folder`, `EncodedCollab` (con las correcciones del hallazgo 7).
- **B1.7** `08-persistencia/` — `collab_snapshot`, `LocalStorage`, paths por plataforma.
- **B1.3** `04-arquitectura-global.md` — arquitectura Dart dual y capas cruzadas.
