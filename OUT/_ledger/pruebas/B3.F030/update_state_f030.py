#!/usr/bin/env python3
"""update_state_f030.py — Reescribe `## Última fase cerrada` y
`## Próxima fase por abrir` de `OUT/STATE.md` con el cierre de
B3.F03..B3.F07 (2026-10-20).

Uso: python3 OUT/_ledger/pruebas/B3.F030/update_state_f030.py [--dry-run]
"""
from __future__ import annotations

import argparse
from pathlib import Path

STATE = Path(__file__).resolve().parents[4] / "OUT" / "STATE.md"

ULTIMA = """## Última fase cerrada

**B3.F03 → B3.F07 ✅ (2026-10-20)** — Cierre conjunto de las 5 features de "resto de features": **406 archivos**, **10 documentos**, 6 651 líneas, 1 782 refs de evidencia validadas y 47 diagramas Mermaid. Cobertura global: **1 762 verificados / 4 603 asignados (38,28 %)**, 0 `sin_asignar`. Las 10 suites `validate-B3.F0*.sh` en verde (5 checks cada una: template · evidence · mermaid · cobertura · revisor) y los 10 `revisor_output.json` con `veredicto=aprobado, correcciones=0` (F06 con `--gate-100`). Plan ejecutor: `~/.local/share/kilo/plans/1792504481368-b3-f03-f07-cierre-plan.md`.

Detalle por fase:

| Fase | Docs | Líneas | Archivos | Refs | Mermaid | Cobertura | Revisor |
|---|---:|---:|---:|---:|---:|---|---|
| B3.F06 Sync y servidores (`af_cloud` vs `local_server`) | 1 | 469 | 35 | 123 | 5 | 35/35 | aprobado (**gate-100**) |
| B3.F07 Almacenamiento de archivos | 1 | 460 | 58 | 87 | 4 | 58/58 | aprobado |
| B3.F04 Sidebar, favoritos, recientes, papelera, tabs, command palette | 1 | 820 | 66 | 211 | 6 | 66/66 | aprobado |
| B3.F03.0 Índice folder/workspaces/vistas | 1 | 595 | 0 | 102 | 4 | 0/0 (índice) | aprobado |
| B3.F03.1 Vistas/workspaces/sidebar (Dart) | 1 | 779 | 55 | 279 | 5 | 55/55 | aprobado |
| B3.F03.2 `flowy-folder` (Rust) | 1 | 747 | 33 | 262 | 5 | 33/33 | aprobado |
| B3.F03.3 `collab-folder` (Collab) | 1 | 704 | 28 | 286 | 4 | 28/28 | aprobado |
| B3.F05.0 Índice usuario/auth/sesión | 1 | 586 | 0 | 150 | 4 | 0/0 (índice) | aprobado |
| B3.F05.1 Usuario Dart (`lib/user/`) | 1 | 738 | 73 | 209 | 5 | 73/73 | aprobado |
| B3.F05.2 `flowy-user` + `collab-user` (Rust + Collab) | 1 | 753 | 58 | 73 | 5 | 58/58 | aprobado |

**Decisiones tomadas** (confirmadas por el usuario): D1 F03 se divide en **4** por corte de lenguaje/fuente, declarado en `SUBDIVISIONS["F03"]` de `build_units.py`; D2 se crea el índice **F05.0** que las units F05.1/F05.2 declaraban y nadie materializaba; D3 las discrepancias ROADMAP↔ledger se resuelven con **correcciones de scope** en §2 y §13 de cada documento, **sin reasignar archivos**; D4 orquestación **secuencial** feature por feature.

**Correcciones de scope oficializadas** (9): `view_management` → F04 y **vacío** (`ViewManagementBloc` no existe) · espacios → F03.1 · `share_tab` y roles → F12 · migraciones diesel → B1.7 (solo la lógica de datos en F05.2) · awareness de usuario → F05.2 y colaboradores → F01.0.1 · `collab-plugins` (`cloud_storage`, `connect_state`) → F18 · `server_layer` y `plugin_provider` → F00 · `flowy-storage-pub` → F00 · media y archivos de F01.3 → F07.

**Hallazgos materiales** (detalle en los `README.md` de `OUT/_ledger/pruebas/B3.F03*` y `B3.F05*`): `extract_notifications.py` no reconoce el envoltorio `folder_notification_builder` ni las emisiones de `flowy-storage`, por lo que marca `emitted_in_rust: 0` en 21 notificaciones (afecta a F03.2, F04, F06, F07, F12 y F15) · 5 `FolderNotification` declaradas y nunca emitidas · 5 `FolderEvent` huérfanas (3 sin handler, 2 sin consumidor Dart) · `WorkspaceBloc._fetchWorkspaces` descarta la lista recibida (`workspace_bloc.dart:52`) · **B1.6 documenta campos y variantes de `collab-folder` que no existen** en el rev `4dfccef` (pendiente de resolver en C3) · fixtures binarias `folder_{with,without}_fav_v1.zip` no inventariadas.

**Adaptaciones a la skill** (11, todas reversibles): `build_units.py` (`F03_SUBS` + entrada de índice `F05.0`) · `validate_units.py` (salta unidades `B1.x`; invariante contra todas las filas asignadas; nuevo `--estados`) · `record_unit_state.py` (resuelve sub-unidades desde `units/<id>.json`; nuevo `--units-dir`) · `validate-A4.2.sh` Check 3 pasa a **solo lectura** y añade un gate F03..F07 · purga de las units padre obsoletas `F02.0.1.json` y `F02.0.2.json` (425 rutas con doble propiedad) · reanclaje de 135 filas asignadas sin unidad (114 de F02 + 21 de F08) · cesión de 51 rutas Dart duplicadas de `F02.{1,2,3,7,8,12}` a `F02.0.1.2` · 34 suites heredadas corregidas (parsing de Mermaid, `ROOT` a 4 niveles en las 9 de F01, umbral de B3.F01.0 de `=555` a `>=555`) · 2 enlaces `[[F03.0.2]]` → `[[F03.2]]`. Bitácora completa: `OUT/_ledger/pruebas/B3.F030/README-prerequisitos.md`.

**Enlaces cruzados**: `build_index.py --check-links` → 61 no resueltos de 118, **0 realmente rotos** (verificado contra los `id:` existentes). Los no resueltos son features y fases aún no escritas (F00, F01, F02, F09, F12–F19, B4, B6.3), los ids de fase `B1.x`/`B2.x` que no coinciden con los ids reales de `06-…`/`11-…`, y los tokens de ejemplo `<X>`/`<NOEXISTE>`/`<F..>` que este mismo `STATE.md` usa al explicar el comportamiento de `build_index.py`. Registrado en `OUT/22-preguntas-abiertas.md`.

"""

PROXIMA = """## Próxima fase por abrir

**B3.F08 — Búsqueda e indexación**: completar el piloto A5.1 (`OUT/09-features/F08-busqueda-e-indexacion/`, 1 doc, 21 archivos ya verificados) con el resto de la unidad y cerrar la feature. Alternativa de mayor valor inmediato: **F00 — Infraestructura compartida** (1 556 archivos, 26 unidades, la mayor del proyecto y de la que dependen F05, F06, F07 y B4). Ambas son de prioridad 1 en `OUT/_ledger/units/_index.json`.

Orden recomendado por dependencia: **F00.1** (FFI + dispatcher) → **F00.2** (errores, SQLite, migraciones) → **F00.5.x** (paquetes Dart internos, que `validate_template` y `validate_evidence` necesitan para cubrir las rutas de `packages/`) → F08 → F09..F21 → B4.

**Nota de bloqueo**: `OUT/_ledger/validate-A4.2.sh` Check 3 incluye un gate que exige F03..F07 al 100 % verificado; se cumple desde 2026-10-20.

"""


def find(lines: list[str], suffix: str) -> int:
    return next(i for i, l in enumerate(lines) if l.startswith("## ") and l.endswith(suffix))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    lines = STATE.read_text(encoding="utf-8").split("\n")
    i_ult = find(lines, "ltima fase cerrada")
    i_idx = find(lines, "ndice de fases")
    assert i_ult < i_idx, f"orden inesperado: {i_ult} vs {i_idx}"

    nuevo = ULTIMA.split("\n") + PROXIMA.split("\n") + lines[i_idx:]
    out = lines[:i_ult] + nuevo

    if args.dry_run:
        print(f"[dry-run] {i_ult}..{i_idx} ({i_idx - i_ult} lineas) -> {len(nuevo)}")
        return 0

    STATE.write_text("\n".join(out), encoding="utf-8")
    print(f"OK: STATE.md {len(lines)} -> {len(out)} lineas")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())