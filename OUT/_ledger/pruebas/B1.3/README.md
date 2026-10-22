# pruebas/B1.3/ — `04-arquitectura-global.md` (2026-10-19)

**Objetivo:** verificar que el documento raíz de la arquitectura global cubre los 5 contenedores C4, los 30 crates Rust del SDK, los 17 features Dart + F21 y las 9 capas del inventario, con un diagrama de flujo global de la app (la pieza estrella de la fase) trazando el camino desde un clic del usuario hasta la mutación del CRDT y la notificación de vuelta. La prueba del ROADMAP ("validadores en verde; revisor aprueba") se cumple cuando los 4 validadores A3.x y el revisor (`run_subagent.py --rol revisor`) emiten `aprobado`.

**Ejecutar:**

```bash
OUT/_ledger/validate-B1.3.sh
```

**Salida (2026-10-19):**

```
─── validate_template ───
--- summary: files=1 ok=1 errors=0 warns=0 ---
OK: template
─── validate_evidence ───
--- summary: refs=17 ok=17 errors=0 ---
OK: evidence
─── validate_mermaid ───
OK=6 FAIL=0
OK: mermaid
─── validate_B1_3_coverage ───
OK: coverage

OK: B1.3 (template+evidence+mermaid+coverage, 4/4 checks)
exit=0
```

**Revisor:**

```
[run_subagent] rol=revisor veredicto=aprobado correcciones=0 pct_efectivo=30
exit=0
```

## Resultado por validador

| Validador | Métrica | Resultado |
|---|---|---|
| `validate_template.py --template structure` (auto-detect `B1.3`) | frontmatter + 11 secciones numeradas + `Relacionado con` | OK, 0 errors / 0 warns |
| `validate_evidence.py` | refs `[fuente:]ruta:línea` resueltas contra `inventario.json` | 17 / 17 OK |
| `validate_mermaid.sh` | bloques `mermaid` renderizan con `mmdc` | 6 / 6 OK |
| `validate_B1_3_coverage.py` | prueba de cobertura: 5 contenedores C4, 31 crates Rust, 18 features Dart, 9 capas | **100 % (0 missing)** |
| `run_subagent.py --rol revisor` | veredicto | **aprobado** (0 correcciones, 30 % muestreo) |

## Cobertura por categoría

| Categoría | Esperado | Presente | Faltan |
|---|---:|---:|---|
| Contenedores C4 | 5 | 5 | 0 |
| Crates Rust | 31 | 31 | 0 |
| Features Dart (F01–F17, F21) | 18 | 18 | 0 |
| Capas (Capa 1–9) | 9 | 9 | 0 |

## Diagramas (6 bloques Mermaid)

1. §T3.2 — C4 contexto (1 actor central + 8 periféricos).
2. §T4.6 — C4 contenedores (5 contenedores + etiquetas de protocolo).
3. §T5.1 — 9 capas en `flowchart TD` con flechas verticales.
4. **§T7.1 — Flujo global de la app** (`flowchart TD` con 16 nodos en 9 subgraphs por capa; ejemplo `DocumentBloc → DocumentService → FFI → open_document_handler → DocumentManager → Collab → persistencia → notification → listener → state`).
5. **§T7.2 — Mismo flujo en `sequenceDiagram`** con 9 participantes y 17 saltos numerados.
6. §T8.4 — Arquitectura Dart dual (legado vs nuevo) en `flowchart LR`.

## Artefactos

| Archivo | Contenido |
|---|---|
| `OUT/04-arquitectura-global.md` | 600 líneas, 12 secciones `## `, 17 refs verificadas, 6 diagramas Mermaid. |
| `OUT/_ledger/pruebas/B1.3/component-counts.json` | 8 crates con su # de variantes de eventos. |
| `OUT/_ledger/pruebas/B1.3/blocs-by-folder.json` | 6 carpetas de `lib/` con su # de BLoCs. |
| `OUT/_ledger/pruebas/B1.3/validate_B1_3_coverage.py` | 3,8 KB (nuevo) — verifica los 4 grupos. |
| `OUT/_ledger/pruebas/B1.3/coverage.json` | Salida estructurada (100 % OK). |
| `OUT/_ledger/pruebas/B1.3/revisor_output.json` | `veredicto=aprobado, correcciones=0`. |
| `OUT/_ledger/pruebas/B1.3/validate_*.log` | Logs de los 4 validadores. |
| `OUT/_ledger/validate-B1.3.sh` | Suite bash que orquesta los 4 checks. |
| `OUT/_ledger/units/B1.3.json` | Unidad ad-hoc para `run_subagent.py --rol revisor`. |

## Cierre del Bloque B1.3

| Entregable | Tamaño | Estado |
|---|---|---|
| `OUT/04-arquitectura-global.md` | 600 líneas · 17 refs verificadas · 6 Mermaid | ✅ |
| `OUT/_ledger/pruebas/B1.3/validate_B1_3_coverage.py` | 3,8 KB (nuevo) | ✅ |
| `OUT/_ledger/validate-B1.3.sh` | 1,2 KB (nuevo) | ✅ 4/4 checks |
| `SKILL/scripts/run_subagent.py --rol revisor` | veredicto | ✅ aprobado |

Próxima fase: **B1.4 — `05-arranque-y-ciclo-de-vida.md`** (las 15 `LaunchTask` en orden, `flowy-core` AppFlowyCore, AppLifeCycle, cambio de usuario/workspace, cold/warm start).
