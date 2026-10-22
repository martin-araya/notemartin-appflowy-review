# pruebas/A4.1/ — `assign_ledger.py` + fixtures + validador

**Fase**: A4.1 — `assign_ledger.py` (Bloque A4 · Orquestación).
**Fecha**: 2026-10-18.
**Plan completo**: `1792363730747-assign-ledger-a41.md`.

## Entregables

| Archivo | Rol |
|---|---|
| `SKILL/scripts/assign_ledger.py` | Script principal (Python 3 stdlib, ~660 líneas) |
| `OUT/_ledger/pruebas/A4.1/fixtures/toy_inventario.json` | 32 archivos sintéticos con 1 `sin_match` |
| `OUT/_ledger/pruebas/A4.1/fixtures/toy_ledger.csv` | Ledger toy en `sin_asignar` |
| `OUT/_ledger/pruebas/A4.1/fixtures/expected_ledger.csv` | Resultado esperado (31 asignados, 1 `sin_asignar`) |
| `OUT/_ledger/pruebas/A4.1/fixtures/verified_ledger.csv` | Ledger con 2 filas en `verificado` para probar preservación |
| `OUT/_ledger/pruebas/A4.1/fixtures/expected_verified_ledger.csv` | Las 2 filas `verificado` intactas |
| `OUT/_ledger/validate-A4.1.sh` | 8 checks; sale 0 si todo OK |
| `OUT/_ledger/pruebas/A4.1/smoke.log` | Trazas reales |
| `OUT/_ledger/sin_asignar.md` | Listado de los 324 archivos `sin_asignar` con resumen por fuente/capa |
| `OUT/_ledger/sin_asignar.json` | Mismo en JSON para consumo programático |
| `OUT/_ledger/cobertura.csv` | Re-escrito con `feature_ids` y transiciones `sin_asignar → pendiente` |

## Resumen de la prueba literal del ROADMAP A4.1

- **Script**: `assign_ledger.py` ejecutable, `--help` correcto.
- **Cobertura real**: **92.96 %** (4.279 / 4.603 archivos; 324 `sin_asignar`).
- **Cobertura toy**: 96.88 % (31 / 32; 1 `sin_asignar`).
- **Precedencia F14 > F17** (verificada en `OUT/_ledger/cobertura.csv`):
  - `appflowy/frontend/appflowy_flutter/lib/startup/tasks/localization.dart` → `F14` (no `F17`).
  - `appflowy/frontend/appflowy_flutter/lib/shared/easy_localiation_service.dart` → `F14`.
- **Precedencia F01 > genéricos** (verificada en CSV): `plugins/document/...` y `editor/lib/src/...` van a `F01`.
- **`sin_asignar.md`** generado con 324 rutas agrupadas por `capa` y por `fuente` (mayoría en `appflowy/frontend/appflowy_flutter/lib/{workspace,shared,core}` y `appflowy/frontend/rust-lib/flowy-{document,core}/src/`).

## Comandos

```bash
# Corrida real (escribe cobertura.csv, sin_asignar.md, sin_asignar.json)
python3 SKILL/scripts/assign_ledger.py

# Dry-run (solo calcula y reporta)
python3 SKILL/scripts/assign_ledger.py --dry-run

# Modo CI: exit 1 si cobertura < 90
python3 SKILL/scripts/assign_ledger.py --min-coverage 90

# Salida JSON a stdout (consumo programático)
python3 SKILL/scripts/assign_ledger.py --json --no-color --quiet

# Validador de la fase
bash OUT/_ledger/validate-A4.1.sh
```

## Tabla por feature (corrida real)

| Feature | Archivos |
|---|---:|
| F00 Infraestructura compartida (FFI, dispatch, errores, build, paquetes, nativo, tests) | 1.529 |
| F01 Documentos y editor | 710 |
| F02 Bases de datos | 651 |
| F18 Motor Colab (CRDT, plugins, importer, entity, derive) | 113 |
| F09 IA | 166 |
| F16 Mobile | 184 |
| F19 Editor (tests, ejemplos, l10n, configuración) | 354 |
| F03 Folder, workspaces, vistas | 85 |
| F05 Usuario, auth, sesión | 126 |
| F13 Ajustes, apariencia, temas, fuentes | 84 |
| F12 Compartir, publicar, niveles de acceso | 59 |
| F06 Sync y servidores | 35 |
| F07 Almacenamiento de archivos | 55 |
| F15 Notificaciones in-app y recordatorios | 37 |
| F04 Sidebar, favoritos, recientes, papelera, tabs, command palette | 30 |
| F08 Búsqueda e indexación | 21 |
| F17 Plataforma (ventanas, deeplinks, auto-update, hotkeys, feature flags, errores, logging) | 19 |
| F14 Internacionalización | 6 |
| F11 Exportación (UI) | 2 |
| F20 Colab (raíz: configuración, CI, docs, manifests) | 13 |
| **Total asignados** | **4.279** |
| **Sin asignar (triage B0.2)** | **324** |

## Log completo

`smoke.log` (87 líneas) — incluye `--help`, corrida `--dry-run` real y salida del validador.
