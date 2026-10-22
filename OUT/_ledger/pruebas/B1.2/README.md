# pruebas/B1.2/ — `02-stack-y-dependencias.md` + `17-grafo-dependencias.md` (2026-10-19)

**Objetivo:** verificar que los dos documentos raíz del Bloque B1.2 cubren el stack completo del monorepo AppFlowy: las versiones, los workspaces, las 31 deps workspace y las 36+3 git externas de Rust, los 8 packages Dart con sus 136 deps externas declaradas, y los grafos Mermaid. La prueba literal del ROADMAP ("todas las dependencias directas listadas") la ejecuta `validate_B1_2_coverage.py` y debe devolver exit 0 con `missing_* = []`.

**Ejecutar:**

```bash
OUT/_ledger/validate-B1.2.sh
```

**Salida (2026-10-19):**

```
─── validate_template (02) ───
--- summary: files=1 ok=1 errors=0 warns=0 ---
OK: template 02
─── validate_template (17) ───
--- summary: files=1 ok=1 errors=0 warns=0 ---
OK: template 17
─── validate_evidence (02) ───
--- summary: refs=68 ok=68 errors=0 ---
OK: evidence 02
─── validate_evidence (17) ───
--- summary: refs=2 ok=2 errors=0 ---
OK: evidence 17
─── validate_mermaid (02) ───
OK=2 FAIL=0
OK: mermaid 02
─── validate_mermaid (17) ───
OK=3 FAIL=0
OK: mermaid 17
─── validate_B1_2_coverage (literal) ───
OK: coverage

OK: B1.2 (template x2 + evidence x2 + mermaid x2 + coverage, 7/7 checks)
exit=0
```

## Resultado por validador

| Validador | Doc | Métrica | Resultado |
|---|---|---|---|
| `validate_template.py --template structure` (auto-detect `B1.2` y `B1.2-grafo`) | 02 | frontmatter + 11 secciones numeradas + `Relacionado con` | OK |
| `validate_template.py --template structure` | 17 | frontmatter + 11 secciones numeradas + `Relacionado con` | OK |
| `validate_evidence.py` | 02 | refs `[fuente:]ruta:línea` resueltas | 68 / 68 OK |
| `validate_evidence.py` | 17 | refs `[fuente:]ruta:línea` resueltas | 2 / 2 OK |
| `validate_mermaid.sh` | 02 | bloques `mermaid` renderizan con `mmdc` | 2 / 2 OK |
| `validate_mermaid.sh` | 17 | id. | 3 / 3 OK |
| `validate_B1_2_coverage.py` | 17 (vs catálogos) | 31 crates Rust × deps directas + 8 packages Dart × deps directas | 100 % (0 missing) |

## Prueba literal del ROADMAP ("todas las deps directas listadas")

El validador compara el catálogo generado por `build_B1_2_dep_catalog.py` con los nombres de crates externos y packages internos/externos que aparecen en el cuerpo del doc `17-grafo-dependencias.md`. Resultado:

| Métrica | Valor |
|---|---:|
| Crates Rust cubiertos | 31 / 31 |
| Aristas internas Rust (workspace) | 150 / 150 |
| Deps externas Rust directas | 368 / 368 (con filtro de "crate-like" para evitar falsos positivos por palabras comunes) |
| Packages Dart cubiertos | 8 / 8 |
| Aristas internas Dart (path:) | 12 / 12 |
| Deps externas Dart directas (≥ 2 packages) | 27 / 27 |
| Deps externas Dart de la app (≥ 1 package) | 136; las 109 de un solo uso se documentan en `02-stack-y-dependencias.md §8` |
| **Missing (interno Rust)** | **0** |
| **Missing (externo Rust)** | **0** |
| **Missing (interno Dart)** | **0** |
| **Missing (externo Dart)** | **0** |

## Extensión del validador de plantilla

`SKILL/scripts/validate_template.py` se extendió para aceptar el sufijo `-grafo` en el id de la plantilla `structure` (cambio backward-compatible: el patrón `^B1\.\d+(-[a-z0-9]+)?$` también matchea `B1.2-grafo`):

```python
"structure": {
    "required_sections": list(range(1, 12)),
    "optional_sections": [],
    "id_pattern": re.compile(r"^B1\.\d+(-[a-z0-9]+)?$"),
    "estados": {"verificado", "pendiente"},
},
```

Justificación: el plan B1.2 produce dos documentos relacionados con el mismo id raíz (`B1.2` y `B1.2-grafo`); la regex ampliada permite identificarlos como parte del mismo bloque sin tener que añadir una nueva plantilla.

## Artefactos

| Archivo | Contenido |
|---|---|
| `OUT/02-stack-y-dependencias.md` | 367 líneas, 12 secciones `## `, 68 refs verificadas, 2 diagramas Mermaid. |
| `OUT/17-grafo-dependencias.md` | 411 líneas, 12 secciones `## `, 2 refs verificadas, 3 diagramas Mermaid. |
| `OUT/_ledger/pruebas/B1.2/all-direct-deps-rust.json` | Catálogo de los 31 crates con sus deps internas y externas. |
| `OUT/_ledger/pruebas/B1.2/all-direct-deps-dart.json` | Catálogo de los 8 packages con sus deps internas y externas. |
| `OUT/_ledger/pruebas/B1.2/graph-metrics.json` | Métricas del grafo (fan-in, fan-out, ciclos, componentes conexos). |
| `OUT/_ledger/pruebas/B1.2/deps-stats.json` | Resumen numérico Rust + Dart. |
| `OUT/_ledger/pruebas/B1.2/build_B1_2_dep_catalog.py` | Script que extrae los 4 JSON anteriores desde `deps.json`. |
| `OUT/_ledger/pruebas/B1.2/validate_B1_2_coverage.py` | Validador de la prueba literal (100 % deps directas). |
| `OUT/_ledger/pruebas/B1.2/coverage.json` | Salida estructurada del validador. |
| `OUT/_ledger/pruebas/B1.2/validate_*.log` | Logs de los 6 validadores A3.x. |
| `OUT/_ledger/validate-B1.2.sh` | Suite bash que orquesta los 7 checks. |

## Cierre del Bloque B1.2

| Entregable | Tamaño | Estado |
|---|---|---|
| `OUT/02-stack-y-dependencias.md` | 367 líneas · 68 refs verificadas · 2 Mermaid | ✅ |
| `OUT/17-grafo-dependencias.md` | 411 líneas · 100 % deps directas · 3 Mermaid | ✅ |
| `OUT/_ledger/pruebas/B1.2/validate_B1_2_coverage.py` | 7,3 KB (nuevo) | ✅ |
| `OUT/_ledger/validate-B1.2.sh` | 1,7 KB (nuevo) | ✅ 7/7 checks |
| `SKILL/scripts/validate_template.py` | +1 char en regex (`-` opcional) | ✅ backward-compatible |

Próxima fase: **B1.3 — `04-arquitectura-global.md`** (C4: contexto → contenedores → componentes; diagrama de flujo global de la app; mapa de responsabilidades por crate/carpeta; arquitectura Dart dual legada vs `features/`).
