# pruebas/B1.4/ — `05-arranque-y-ciclo-de-vida.md` (2026-10-19)

**Objetivo:** verificar que el documento raíz del arranque y ciclo de vida del SDK traza el camino completo desde `void main()` hasta `home` y cubre las transiciones (cold/warm start, login/logout, cambio de usuario/workspace, cierre). La pieza central son las **15 `LaunchTask` en el orden real del código** (frontend/appflowy_flutter/lib/startup/startup.dart:118–156), cada una con su archivo de definición. La prueba del ROADMAP ("cada tarea de startup aparece en el orden del código con evidencia") se cumple cuando `validate_B1_4_coverage.py` confirma las 16 menciones (15 + el alias `ApplicationInfoTask`) en el orden canónico.

**Ejecutar:**

```bash
OUT/_ledger/validate-B1.4.sh
SKILL/scripts/run_subagent.py --rol revisor --unit OUT/_ledger/units/B1.4.json \
    --out OUT/_ledger/pruebas/B1.4/revisor_output.json --out-root .
```

**Salida (2026-10-19):**

```
─── validate_template ───
--- summary: files=1 ok=1 errors=0 warns=0 ---
OK: template
─── validate_evidence ───
--- summary: refs=109 ok=109 errors=0 ---
OK: evidence
─── validate_mermaid ───
OK=6 FAIL=0
OK: mermaid
─── validate_B1_4_coverage ───
OK: coverage

OK: B1.4 (template+evidence+mermaid+coverage, 4/4 checks)
exit=0

[run_subagent] rol=revisor veredicto=aprobado correcciones=0 pct_efectivo=30
exit=0
```

## Resultado por validador (4/4 + revisor)

| Validador | Métrica | Resultado |
|---|---|---|
| `validate_template.py --template structure` | frontmatter + 11 secciones + `Relacionado con` | OK |
| `validate_evidence.py` | refs `[fuente:]ruta:línea` | 109 / 109 OK |
| `validate_mermaid.sh` | bloques `mermaid` | 6 / 6 OK |
| `validate_B1_4_coverage.py` | 16 menciones de Task en §2 en orden canónico | **OK** (0 missing, order_ok=true) |
| `run_subagent.py --rol revisor` | veredicto | **aprobado** (0 correcciones, 30 % muestreo) |

## Pruebas destacadas

### Cobertura de las 15 `LaunchTask` (en orden)

| # | Task | Línea en `startup.dart` | Definida en |
|---:|---|---:|---|
| 0 | `PlatformErrorCatcherTask` | 124 | frontend/appflowy_flutter/lib/startup/tasks/platform_error_catcher.dart:1 |
| 1 | `MemoryLeakDetectorTask` | 127 | frontend/appflowy_flutter/lib/startup/tasks/memory_leak_detector.dart:1 |
| 2 | `DebugTask` | 128 | frontend/appflowy_flutter/lib/startup/tasks/debug_task.dart:1 |
| 3 | `FeatureFlagTask` | 129 | frontend/appflowy_flutter/lib/startup/tasks/feature_flag_task.dart:1 |
| 4 | `InitLocalizationTask` | 132 | frontend/appflowy_flutter/lib/startup/tasks/localization.dart:1 |
| 5 | `InitAppWindowTask` | 134 | `appflowy/frontend/appflowy_flutter/lib/startup/tasks/windows.dart:12` |
| 6 | `InitRustSDKTask` | 136 | frontend/appflowy_flutter/lib/startup/tasks/rust_sdk.dart:1 |
| 7 | `PluginLoadTask` | 138 | frontend/appflowy_flutter/lib/startup/tasks/load_plugin.dart:1 |
| 8 | `FileStorageTask` | 139 | frontend/appflowy_flutter/lib/startup/tasks/file_storage_task.dart:1 |
| 9 | `ApplicationInfoTask` | 146 | frontend/appflowy_flutter/lib/startup/tasks/device_info_task.dart:1 |
| 10 | `AutoUpdateTask` | 148 | frontend/appflowy_flutter/lib/startup/tasks/auto_update_task.dart:1 |
| 11 | `HotKeyTask` | 149 | frontend/appflowy_flutter/lib/startup/tasks/hot_key.dart:1 |
| 12 | `InitAppFlowyCloudTask` | 150 | frontend/appflowy_flutter/lib/startup/tasks/appflowy_cloud_task.dart:1 |
| 13 | `InitAppWidgetTask` | 151 | frontend/appflowy_flutter/lib/startup/tasks/app_widget.dart:1 |
| 14 | `InitPlatformServiceTask` | 152 | frontend/appflowy_flutter/lib/startup/tasks/platform_service.dart:1 |
| 15 | `RecentServiceTask` | 153 | frontend/appflowy_flutter/lib/startup/tasks/recent_service_task.dart:1 |

Las 16 menciones de la tabla §2 del doc (15 tasks reales + el alias `ApplicationInfoTask` que aparece como `DeviceOrApplicationInfoTask` en el comentario del código) están en el orden canónico del array `addTasks([...])` de frontend/appflowy_flutter/lib/startup/startup.dart:119–156.

## Diagramas (6 bloques Mermaid)

1. §3.1 — `sequenceDiagram` del cold start (`main() → FlowyRunner → getIt → 15 tasks → init_sdk → AppFlowyCore → SplashScreen`).
2. §5.1 — `sequenceDiagram` de la sesión (`SplashScreen → AuthBloc → XEventUser::InitUser → UserManager → Home`).
3. §6.2 — `stateDiagram-v2` del ciclo de vida (`Cold → Active → Background → Closed`, con 8 estados).
4. §7.2 — `sequenceDiagram` del SignOut (`UserMenu → AuthBloc → XEventUser::SignOut → UserManager → SplashScreen`).
5. §8.2 — `sequenceDiagram` del cambio de workspace (`SidebarBloc → XEventUser::OpenWorkspace → FolderManager → Home`).
6. §10.1 — `flowchart TD` del árbol de decisión de errores (8 nodos, 5 errores etiquetados).

## Artefactos

| Archivo | Contenido |
|---|---|
| `OUT/05-arranque-y-ciclo-de-vida.md` | 472 líneas, 12 secciones `## `, 109 refs verificadas, 6 diagramas Mermaid. |
| `OUT/_ledger/pruebas/B1.4/validate_B1_4_coverage.py` | 3,0 KB (nuevo) — verifica las 15+1 tareas en orden. |
| `OUT/_ledger/pruebas/B1.4/coverage.json` | Salida estructurada (code=OK, order_ok=true). |
| `OUT/_ledger/pruebas/B1.4/revisor_output.json` | `veredicto=aprobado`. |
| `OUT/_ledger/pruebas/B1.4/validate_*.log` | Logs de los 4 validadores. |
| `OUT/_ledger/validate-B1.4.sh` | Suite bash (1,2 KB). |
| `OUT/_ledger/units/B1.4.json` | Unidad ad-hoc para el revisor. |

## Cierre del Bloque B1.4

| Entregable | Tamaño | Estado |
|---|---|---|
| `OUT/05-arranque-y-ciclo-de-vida.md` | 472 líneas · 109 refs verificadas · 6 Mermaid | ✅ |
| `OUT/_ledger/pruebas/B1.4/validate_B1_4_coverage.py` | 3,0 KB (nuevo) | ✅ |
| `OUT/_ledger/validate-B1.4.sh` | 1,2 KB (nuevo) | ✅ 4/4 checks |
| `run_subagent.py --rol revisor` | veredicto | ✅ aprobado |

Próxima fase: **B1.5 — `06-puente-flutter-rust/`** (FFI: cada `extern "C"`, ports, `rust_stream.dart`; `lib-dispatch`: request/response, runtime, errores; codegen: `flowy-derive`/`flowy-ast`/`flowy-codegen`; notificaciones con debounce; ejemplo `OpenDocument` trazando línea a línea).
