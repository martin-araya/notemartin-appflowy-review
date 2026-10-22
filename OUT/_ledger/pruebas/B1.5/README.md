# pruebas/B1.5/ — `06-puente-flutter-rust/` (2026-10-19)

**Objetivo:** verificar que los 6 sub-documentos del Bloque B1.5 cubren el puente FFI entre Dart y Rust: (a) las 8 funciones `extern "C"`, (b) `lib-dispatch`, (c) `flowy-codegen`, (d) las notificaciones con debounce, y (e) un ejemplo end-to-end de `OpenDocument` trazado línea a línea con evidencia en cada uno de los 17 saltos. La prueba literal del ROADMAP ("el ejemplo trazado tiene evidencia en cada salto") se cumple cuando `validate_B1_5_coverage.py` confirma los 17 componentes del trazado, las 8 funciones FFI y los 8 temas del dispatcher.

**Ejecutar:**

```bash
OUT/_ledger/validate-B1.5.sh
SKILL/scripts/run_subagent.py --rol revisor --unit OUT/_ledger/units/B1.5.json \
    --out OUT/_ledger/pruebas/B1.5/revisor_output.json --out-root .
```

**Salida (2026-10-19):**

```
─── validate_template x6 ───
6/6 OK (modo `bridge`, id ∈ ^06-\d{2}-[a-z-]+$)
─── validate_evidence x6 ───
refs totales: 155 → 155 OK, 0 FAIL
─── validate_mermaid x6 ───
10 bloques Mermaid validados con mmdc
─── validate_B1_5_coverage ───
traza_open_document: 17/17 OK
ffi_extern_c: 8/8 OK
dispatch_topics: 8/8 OK

OK: B1.5 (template x6 + evidence x6 + mermaid x6 + coverage, 19/19 checks)
exit=0

[run_subagent] rol=revisor veredicto=aprobado correcciones=0 pct_efectivo=30
exit=0
```

## Resultado por validador (19/19 + revisor)

| Validador | Métrica | Resultado |
|---|---|---|
| `validate_template.py --template bridge` (modo nuevo) | 6/6 docs | OK |
| `validate_evidence.py` | refs totales 155 | 155 / 155 OK |
| `validate_mermaid.sh` | 10 bloques Mermaid | 10 / 10 OK |
| `validate_B1_5_coverage.py` | 17 traza + 8 FFI + 8 dispatch | **100 %** (0 missing) |
| `run_subagent.py --rol revisor` | veredicto | **aprobado** (0 correcciones, 30 % muestreo) |

## Cobertura por categoría

| Categoría | Esperado | Presente | Faltan |
|---|---:|---:|---:|
| Trazado de `OpenDocument` (17 saltos) | 17 | 17 | 0 |
| Funciones `extern "C"` | 8 | 8 | 0 |
| Temas del dispatcher | 8 | 8 | 0 |

## Los 6 sub-documentos

| # | Slug | Tamaño | Refs | Mermaid |
|---:|---|---:|---:|---:|
| 00 | `00-indice` | 130 | 7 | 2 |
| 01 | `01-ffi` | 280 | 27 | 2 |
| 02 | `02-lib-dispatch` | 240 | 32 | 2 |
| 03 | `03-codegen` | 130 | 7 | 1 |
| 04 | `04-notificaciones` | 130 | 14 | 1 |
| 05 | `05-ejemplo-traza-opendocument` | 250 | 68 | 2 |

## Extensión del validador

`SKILL/scripts/validate_template.py` se extendió con un nuevo modo `bridge` para id `^06-\d{2}-[a-z-]+$` (backward-compatible, sienta precedente para B1.6 `07-motor-colaborativo-crdt/` y B1.7 `08-persistencia/`). Diff: +7 líneas.

## Artefactos

| Archivo | Contenido |
|---|---|
| `OUT/06-puente-flutter-rust/00-indice.md` | 130 líneas, 7 refs, 2 Mermaid |
| `OUT/06-puente-flutter-rust/01-ffi.md` | 280 líneas, 27 refs, 2 Mermaid |
| `OUT/06-puente-flutter-rust/02-lib-dispatch.md` | 240 líneas, 32 refs, 2 Mermaid |
| `OUT/06-puente-flutter-rust/03-codegen.md` | 130 líneas, 7 refs, 1 Mermaid |
| `OUT/06-puente-flutter-rust/04-notificaciones.md` | 130 líneas, 14 refs, 1 Mermaid |
| `OUT/06-puente-flutter-rust/05-ejemplo-traza-opendocument.md` | 250 líneas, 68 refs, 2 Mermaid (la pieza central) |
| `OUT/_ledger/pruebas/B1.5/validate_B1_5_coverage.py` | 4,6 KB (nuevo) — verifica 17 + 8 + 8 = 33 componentes |
| `OUT/_ledger/pruebas/B1.5/coverage.json` | Salida estructurada (100 %) |
| `OUT/_ledger/pruebas/B1.5/revisor_output.json` | `veredicto=aprobado` |
| `OUT/_ledger/validate-B1.5.sh` | Suite bash 1,7 KB (19/19 checks) |
| `OUT/_ledger/units/B1.5.json` | Unidad ad-hoc para el revisor |
| `SKILL/scripts/validate_template.py` | +7 líneas (modo `bridge`) |

## Cierre del Bloque B1.5

| Entregable | Estado |
|---|---|
| 6 sub-documentos del puente FFI | ✅ |
| Trazado end-to-end de `OpenDocument` con 17 saltos verificados | ✅ |
| Suite `validate-B1.5.sh` con 19/19 checks | ✅ |
| Revisor aprueba (`veredicto=aprobado, correcciones=0`) | ✅ |
| `validate_template.py` extendido con modo `bridge` | ✅ |

Próxima fase: **B1.6 — `07-motor-colaborativo-crdt/`** (los 9 crates de `collab/`, `Collab::new`/`open`, `yrs` integration, `collab-plugins` traits, snapshot+restore).
