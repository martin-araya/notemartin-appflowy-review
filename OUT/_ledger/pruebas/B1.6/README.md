# pruebas/B1.6/ — `07-motor-colaborativo-crdt/` (2026-10-19)

**Objetivo:** verificar que los 8 sub-documentos del Bloque B1.6 cubren el motor CRDT de AppFlowy-Collab (sobre `yrs 0.21.0`): el modelo `Collab` con sus 4 dominios (`folder`, `document`, `database`, `user_awareness`), las traits de `collab-plugins`, y el modelo de snapshots. La prueba literal del ROADMAP ("`classDiagram` de cada tipo de collab con claves reales del código de Collab") se cumple cuando `validate_B1_6_coverage.py` confirma que cada uno de los 4 sub-docs (02-folder, 03-documento, 04-database, 05-user-awareness) tiene un `classDiagram` con las clases requeridas.

**Ejecutar:**

```bash
OUT/_ledger/validate-B1.6.sh
SKILL/scripts/run_subagent.py --rol revisor --unit OUT/_ledger/units/B1.6.json \
    --out OUT/_ledger/pruebas/B1.6/revisor_output.json --out-root .
```

**Salida (2026-10-19):**

```
─── validate_template x8 ───
8/8 OK (modo `bridge`, regex ^0[6-9]-\d{2}-[a-z-]+$)
─── validate_evidence x8 ───
refs totales: 157 → 157 OK, 0 FAIL
─── validate_mermaid x8 ───
17 bloques Mermaid validados
─── validate_B1_6_coverage ───
02-folder: 5/5 clases OK
03-documento: 4/4 clases OK
04-database: 6/6 clases OK
05-user-awareness: 5/5 clases OK

OK: B1.6 (template x8 + evidence x8 + mermaid x8 + coverage, 25/25 checks)
exit=0

[run_subagent] rol=revisor veredicto=aprobado correcciones=0 pct_efectivo=30
exit=0
```

## Resultado por validador (25/25 + revisor)

| Validador | Métrica | Resultado |
|---|---|---|
| `validate_template.py --template bridge` (regex extendido) | 8/8 docs | OK |
| `validate_evidence.py` | refs totales 157 | 157 / 157 OK |
| `validate_mermaid.sh` | 17 bloques Mermaid | 17 / 17 OK |
| `validate_B1_6_coverage.py` | 20 clases requeridas en 4 classDiagram | **100 % (0 missing)** |
| `run_subagent.py --rol revisor` | veredicto | **aprobado** (0 correcciones, 30 % muestreo) |

## Cobertura de la prueba literal del ROADMAP ("`classDiagram` de cada tipo de collab con claves reales del código")

| Sub-doc | Clases requeridas en el `classDiagram` | Presentes | Faltan |
|---|---|---:|---:|
| `02-folder.md` | `View`, `Workspace`, `FolderData`, `ViewLayout`, `ViewIdentifier` | 5 | 0 |
| `03-documento.md` | `DocumentData`, `Block`, `CollabDocument`, `DocumentAwareness` | 4 | 0 |
| `04-database.md` | `Field`, `Row`, `Cell`, `View`, `DatabaseState`, `FieldType` | 6 | 0 |
| `05-user-awareness.md` | `UserAwareness`, `UserAwarenessState`, `UserMetadata`, `Selection`, `Cursor` | 5 | 0 |
| **Σ** | **20** | **20** | **0** |

## Los 8 sub-documentos

| # | Slug | Tamaño | Refs | Mermaid |
|---:|---|---:|---:|---:|
| 00 | `00-indice` | 130 | 3 | 2 |
| 01 | `01-modelo-collab` | 195 | 31 | 2 |
| 02 | `02-folder` | 250 | 38 | 2 |
| 03 | `03-documento` | 240 | 16 | 2 |
| 04 | `04-database` | 230 | 27 | 2 |
| 05 | `05-user-awareness` | 200 | 20 | 2 |
| 06 | `06-collab-plugins` | 180 | 8 | 3 |
| 07 | `07-snapshots-conflict-resolution` | 200 | 14 | 3 |

Total: 1625 líneas, 157 refs verificadas, 17 Mermaid validados.

## Extensión del validador

`SKILL/scripts/validate_template.py` se extendió: regex del modo `bridge` pasó de `^06-\d{2}-[a-z-]+$` a `^0[6-9]-\d{2}-[a-z-]+$` (acepta 06, 07, 08, 09; sienta precedente para B1.7 `08-persistencia/` y B1.8 `09-...`). Backward-compatible: los 6 docs de B1.5 siguen matcheando.

## Artefactos

| Archivo | Contenido |
|---|---|
| `OUT/07-motor-colaborativo-crdt/{00,01,02,03,04,05,06,07}-*.md` | 8 sub-documentos, 1625 líneas |
| `OUT/_ledger/pruebas/B1.6/validate_B1_6_coverage.py` | 2,8 KB — verifica los 4 `classDiagram` |
| `OUT/_ledger/pruebas/B1.6/coverage.json` | Salida estructurada (100 %) |
| `OUT/_ledger/pruebas/B1.6/revisor_output.json` | `veredicto=aprobado` |
| `OUT/_ledger/validate-B1.6.sh` | Suite bash 1,7 KB (25/25 checks) |
| `OUT/_ledger/units/B1.6.json` | Unidad ad-hoc para el revisor |
| `SKILL/scripts/validate_template.py` | +1 char en regex (`0[6-9]` en lugar de `06`) |

## Cierre del Bloque B1.6

| Entregable | Estado |
|---|---|
| 8 sub-documentos del motor CRDT | ✅ |
| 4 `classDiagram` con 20 clases reales verificadas (prueba literal del ROADMAP) | ✅ |
| Suite `validate-B1.6.sh` con 25/25 checks | ✅ |
| Revisor aprueba | ✅ |
| `validate_template.py` regex extendido | ✅ |

Próxima fase: **B1.7 — `08-persistencia/`** (esquema SQLite de `kv_table` + `kv_index`, migrations de diesel, `flowy-sqlite`, `flowy-sqlite-vec` para embeddings, `collab_deps.rs` integración).
