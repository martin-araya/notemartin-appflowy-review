# B3.F04 — Sidebar, favoritos, recientes, papelera, tabs, command palette, action_navigation

**ROADMAP ref:** línea 288 (`B3.F04`).

**Resultado (2026-10-20)**: 1 documento `OUT/09-features/F04-sidebar-favoritos-recientes-papelera-tabs-command-palette/F04-sidebar-favoritos-recientes-papelera-tabs-command-palette.md` (**820 líneas**, 8 561 LOC de código analizados, 19 secciones) cubriendo los **66 archivos** del ledger F04. 66/66 leídos completos.

## Suite `validate-B3.F04.sh` 5/5

- `template` = 1/1
- `evidence` = **211/211** refs resueltas contra `inventario.json`
- `mermaid` = **6/6** bloques (`classDiagram` §3.1, `flowchart LR` §5.3, `flowchart TD` §9, 2 `sequenceDiagram` §10, `stateDiagram-v2` §11)
- `cobertura` = **66/66** filas `autor_F04`
- `revisor` → **aprobado, 0 correcciones** (`pct_efectivo=30`)

## Distribución del código cubierto

| Subárbol | Archivos |
|---|---:|
| `workspace/presentation/home/menu/sidebar/**` | 20 |
| `workspace/application/{action_navigation 2, command_palette 4, edit_panel 2, favorite 4, recent 4, tabs 1}` | 17 |
| `workspace/presentation/home/**` | 12 |
| `plugins/trash/**` | 9 |
| `features/view_management/**` | 4 |
| `workspace/presentation/widgets/{draggable_item, edit_panel, sidebar_resizer}` | 4 |
| **Total** | **66** |

## Hallazgos materiales

1. **`features/view_management/` está VACÍO**: `README.md` (0 bytes) y `logic/{view_event,view_management_bloc,view_state}.dart` (1 byte, una línea en blanco). `ViewManagementBloc` **no existe** en este snapshot. Es andamiaje preparado para la arquitectura nueva por feature. Documentado en §2.3, §12.1 y §13 (R1); no se puede citar `ruta:línea` en esos 4 ficheros porque cualquier línea daría `E_LINE_OUT_OF_RANGE`.
2. **Hueco del extractor de notificaciones**: `extract_notifications.py` marca `emitted_in_rust = 0` para las **19** variantes de `FolderNotification` porque su heurística solo reconoce llamadas literales a `NotificationBuilder::new`, y `flowy-folder` emite siempre mediante el envoltorio `folder_notification_builder` (frontend/rust-lib/flowy-folder/src/notification.rs:48–55). Los emisores reales están en `manager.rs` (845, 879, 1329, 1927–1951, 1990, 2016, 2449) y `manager_observer.rs` (100, 148, 191, 210, 218, 228, 236, 269).
3. **Variantes `FolderNotification` declaradas y nunca emitidas** en este snapshot: `DidCreateWorkspace`, `DidUpdateWorkspace`, `DidDeleteView`, `DidRestoreView`, `DidUpdateFolderSnapshotState` — pese a que tres tienen rama en Dart.
4. **Código muerto detectado** (documentado en §6, no eliminado): `FavoritePinBloc` (nunca instanciado), `EditPanelBloc` (registrado en `get_it` pero ningún `EditPanelEvent` se despacha), `SliderMenuHoverTrigger`, `openWorkspaceNotifier`. Además los registros `getIt` de `TrashService`/`TrashListener` (frontend/appflowy_flutter/lib/startup/deps_resolver.dart:184–185) no tienen consumidor: `TrashBloc` instancia los suyos (frontend/appflowy_flutter/lib/plugins/trash/application/trash_bloc.dart:13–16).

## Corrección de scope (ROADMAP vs ledger)

| Prometido en el ROADMAP | Realidad en el ledger | Declarado en |
|---|---|---|
| `view_management` bajo **B3.F03** | los 4 archivos de `features/view_management/**` están asignados a **F04**, y están vacíos | §2.3, §13 (R1) |
| — | el lado servidor de favoritos/recientes/papelera está en **F03.2** (`flowy-folder`) y **F03.3** (`collab-folder`) | §2, §13 |

## Preguntas abiertas (→ `OUT/22-preguntas-abiertas.md`)

1. `features/view_management/README.md` está vacío: ¿cuándo se llenará y qué arquitectura sustituirá a los blocs legados de `workspace/application/`? `[NO DETERMINADO]`
2. ¿Cuál es el destino previsto de `ViewManagementBloc`? No hay referencias en el código. `[NO DETERMINADO]`
3. ¿Debe corregirse `extract_notifications.py` para reconocer `folder_notification_builder` como emisor? Afecta a F03.2, F06, F12 y F15. `[NO DETERMINADO]`
4. ¿`DidCreateWorkspace`, `DidUpdateWorkspace`, `DidDeleteView`, `DidRestoreView` deberían emitirse? Están declaradas y tienen rama Dart. `[NO DETERMINADO]`
5. ¿Dónde se consume `RecentViewsListener` si no tiene ningún `switch` sobre las notificaciones? `[NO DETERMINADO]`
6. ¿Se persistirán las tabs entre sesiones? `TabsBloc` no parece escribir en almacenamiento. `[NO DETERMINADO]`

## Artefactos

- `OUT/09-features/F04-sidebar-favoritos-recientes-papelera-tabs-command-palette/F04-sidebar-favoritos-recientes-papelera-tabs-command-palette.md`
- `OUT/_ledger/pruebas/B3.F04/{validate-B3.F04.sh, revisor_output.json, README.md}`

## Cross-references

- **F03.1** — `workspace/application/view/view_ext.dart` y los blocs de vistas consumidos por la sidebar.
- **F03.2** — `flowy-folder`: eventos de favoritos, recientes, papelera y workspaces; `FolderNotification`.
- **F03.3** — `collab-folder`: `favorite_test.rs`, `recent_views_test.rs`, `trash_test.rs`.
- **F08** — backend de búsqueda que consume `command_palette`.
- **B2.4** `14-catalogo-notificaciones.md` — las 19 variantes de `FolderNotification`.
- **B2.6** `16-catalogo-flags-rutas-atajos.md` — los 13 atajos de `hotkeys.dart` y las rutas go_router.
- **F15** — `core/notification/{notification_helper,folder_notification}.dart`.
- **F17** — deeplinks y atajos globales de plataforma.
