#!/usr/bin/env python3
"""append_phase_rows.py — Añade las 6 filas de B3.F03..F03..F07 al final de la
tabla `## Índice de fases` de `OUT/STATE.md`.

Uso: python3 OUT/_ledger/pruebas/B3.F030/append_phase_rows.py [--dry-run]
"""
from __future__ import annotations

import argparse
from pathlib import Path

STATE = Path(__file__).resolve().parents[4] / "OUT" / "STATE.md"

ROWS = [
 "| **B3.F06 — Sync y servidores (`af_cloud` vs `local_server`)** | B3 | ✅ | 2026-10-20 | `OUT/09-features/F06-sync-y-servidores/F06-sync-y-servidores.md` (469 líneas, 19 secciones, **gate-100**) cubriendo los **35 archivos** del ledger F06: `flowy-server/` completo (4 raíz + 16 `af_cloud/**` + 14 `local_server/**` + `Cargo.toml`), `core/network_monitor.dart` y `plugins/document/application/doc_sync_state_listener.dart`. 123 refs validadas; 5 Mermaid (1 `classDiagram`, 1 `flowchart TD`, 2 `sequenceDiagram`, 1 `stateDiagram-v2`). Tabla comparativa método de trait → impl `af_cloud` → impl `local_server` → divergencia. `NetworkStatus` con todas sus variantes. **Hallazgo**: `flowy-server` no registra ningún `XEvent` (no tiene `event_map.rs`); se consume vía los traits de `flowy-*-pub`. **Correcciones de scope** (4): awareness → F05.2, colaboradores → F01.0.1, `collab-plugins` → F18, `server_layer`/`plugin_provider` → F00. Suite `OUT/_ledger/pruebas/B3.F06/validate-B3.F06.sh` 5/5 (template=1/1, evidence=123/123, mermaid=5 OK, cobertura=35/35, revisor=aprobado). |",
 "| **B3.F07 — Almacenamiento de archivos** | B3 | ✅ | 2026-10-20 | `OUT/09-features/F07-almacenamiento-de-archivos/F07-almacenamiento-de-archivos.md` (460 líneas, 19 secciones) cubriendo los **58 archivos** del ledger F07: `flowy-storage` Rust (12: `manager.rs`, `uploader.rs`, `file_cache.rs`, `entities.rs`, `event_map.rs`, `event_handler.rs`, `notification.rs`, `sqlite_sql.rs` + config/build + `tests/multiple_part_upload_test.rs`) y el Dart de `image`/`video`/`file`/`cover`/`link_preview`/`link_embed`/`image_viewer` (46). 87 refs; 4 Mermaid (1 `classDiagram`, 1 `flowchart TD`, 1 `sequenceDiagram`, 1 `stateDiagram-v2`). **2/2** eventos de `flowy-storage` y **2/2** variantes de `StorageNotification`. Máquina de estados de subida extraída de `uploader.rs`/`entities.rs`; `MIN_CHUNK_SIZE = 5 MB` en `flowy-storage-pub/src/chunked_byte.rs` (**F00**). **Correcciones de scope** (5): F01.3 → F07 (triage B0.2), `flowy-storage-pub` → F00, lado servidor → F06, `file_storage_deps.rs`/`file_storage_task.dart` → F00, listener Dart → F00. Suite `B3.F07/validate-B3.F07.sh` 5/5 (evidence=87/87, cobertura=58/58, revisor=aprobado). |",
 "| **B3.F04 — Sidebar, favoritos, recientes, papelera, tabs, command palette** | B3 | ✅ | 2026-10-20 | `OUT/09-features/F04-sidebar-favoritos-recientes-papelera-tabs-command-palette/F04-…md` (**820 líneas**, 19 secciones, 8 561 LOC analizados) cubriendo los **66 archivos** del ledger F04 (20 sidebar + 17 `workspace/application/{action_navigation,command_palette,edit_panel,favorite,recent,tabs}` + 12 `presentation/home` + 9 `plugins/trash` + 4 `features/view_management` + 4 widgets). 211 refs; 6 Mermaid. Tabla de los 26 BLoCs; arquitectura Dart dual `ViewManagementBloc` vs blocs legados; `TrashBloc` ↔ las 19 `FolderNotification`; los 13 hotkeys cotejados con `extract/misc.json`. **Hallazgos**: `features/view_management/` **vacío** (`ViewManagementBloc` no existe) y código muerto (`FavoritePinBloc`, `EditPanelBloc`, `SliderMenuHoverTrigger`, `openWorkspaceNotifier`). Suite `B3.F04/validate-B3.F04.sh` 5/5 (evidence=211/211, cobertura=66/66, revisor=aprobado). |",
 "| **B3.F03 — Folder, workspaces, espacios, vistas (split en 4)** | B3 | ✅ | 2026-10-20 | F03 se divide por corte de lenguaje/fuente en **F03.0** (índice, 0 arch), **F03.1** (Dart `workspace/`, 55), **F03.2** (`flowy-folder` Rust, 33) y **F03.3** (`collab-folder`, 28). 4 documentos en `OUT/09-features/F03-folder-workspaces-vistas/`, 2 825 líneas, 929 refs, 18 Mermaid. **Pruebas literales**: 51/51 `FolderEvent` (F03.2 §4, agrupadas en 9 dominios en F03.0 §4) y 19/19 `FolderNotification` (F03.2 §5, agrupadas en 8 dominios en F03.0 §5); 14 BLoCs Dart + 73 eventos freezed en F03.1; 13 ficheros de `collab-folder/tests/folder_test/` en F03.3. Distribución de los 51 eventos por consumidor Dart: 23 desde F03.1 · 23 desde otras unidades · **5 huérfanas**. El split se declara en `SUBDIVISIONS[\"F03\"]` de `build_units.py`, no con un script aparte, para que sobreviva a la regeneración. 4 suites 5/5. Bitácora: `OUT/_ledger/pruebas/B3.F030/README-f03.md`. |",
 "| **B3.F05 — Usuario, auth, sesión, miembros, roles, migraciones (split en 3)** | B3 | ✅ | 2026-10-20 | F05 se divide en **F05.0** (índice, 0 arch — creado porque `F05.1` y `F05.2` declaraban esa dependencia y `F05_SUBS` no tenía entrada de índice), **F05.1** (Dart `lib/user/` + `workspace/application/user/`, 73) y **F05.2** (`flowy-user` + `collab-user`, 58). 3 documentos en `OUT/09-features/F05-usuario-auth-sesion/`, 2 077 líneas, 432 refs, 14 Mermaid. **Pruebas literales**: 56/56 `UserEvent` (F05.2 §4, agrupadas en 11 dominios en F05.0 §4) y 10/10 `UserNotification` (F05.2 §5); los 5 eventos de miembros con evidencia en `flowy-user/src/event_map.rs:57–68` y `event_handler.rs:574–827`; 10 BLoCs Dart con 53 eventos freezed; los 6 ficheros de `user/application/auth/` con sus clases reales (`AuthService`, `BackendAuthService`, `AppFlowyCloudAuthService`, `AppFlowyCloudMockAuthService`, `AuthError`, `getDeviceId()`); los 3 caminos de login. **Correcciones de scope** (7): UI de miembros y roles → F12, esquema diesel → B1.7, colaboradores → F01.0.1, auth cloud servidor → F06, recordatorios → F15, `user_deps` → F00, billing Dart → F13. 3 suites 5/5. Bitácora: `OUT/_ledger/pruebas/B3.F050/README.md`. |",
 "| **B3.F03..F07 — cierre conjunto y reparación del ledger** | B3 | ✅ | 2026-10-20 | **406 archivos**, **10 documentos**, 6 651 líneas, 1 782 refs, 47 Mermaid. Cobertura global **1 762 verificados / 4 603 asignados (38,28 %)**, 0 `sin_asignar`. 10 suites 5/5 y 10 revisores `aprobado, 0 correcciones` (F06 con gate-100). 9 correcciones de scope oficializadas y 31 preguntas abiertas volcadas en `OUT/22-preguntas-abiertas.md`. **Fase 0 (prerrequisitos de skill)**: `validate_units.py` crasheaba con las unidades `B1.x`; 425 rutas con doble propiedad por units padre obsoletas `F02.0.1.json`/`F02.0.2.json` (purgadas); 135 filas asignadas sin unidad (114 de F02 + 21 de F08) reancladas; 51 rutas Dart duplicadas cedidas a `F02.0.1.2`; invariante del ledger corregido (compara contra todas las filas asignadas, no solo `pendiente`) con nuevo flag `--estados`; `record_unit_state.py` resuelve sub-unidades desde `units/<id>.json` (nuevo `--units-dir`); `validate-A4.2.sh` Check 3 pasa a solo lectura con gate F03..F07; 34 suites heredadas corregidas (parsing de Mermaid `OK=` vs `ok=`, `ROOT` a 4 niveles en las 9 de F01, umbral de B3.F01.0 `=555` → `>=555`); 2 enlaces `[[F03.0.2]]` → `[[F03.2]]`. `validate_units.py` y `validate-A4.2.sh` en verde: 113 unidades, 4 603 archivos = 4 603 filas asignadas, 0 solapamiento, 0 sin unidad. Plan: `1792504481368-b3-f03-f07-cierre-plan.md`. Bitácora: `OUT/_ledger/pruebas/B3.F030/README-prerequisitos.md`. |",
]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    lines = STATE.read_text(encoding="utf-8").split("\n")
    i_pruebas = next(i for i, l in enumerate(lines) if l.startswith("## Pruebas"))
    j = i_pruebas - 2                      # ultima fila de la tabla de indice
    assert lines[j].startswith("|"), f"fila inesperada: {lines[j][:60]!r}"

    out = lines[: j + 1] + ROWS + lines[j + 1:]
    if args.dry_run:
        print(f"[dry-run] insertando {len(ROWS)} filas tras la linea {j + 1}")
        return 0

    STATE.write_text("\n".join(out), encoding="utf-8")
    print(f"OK: {len(ROWS)} filas añadidas al indice de fases")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())