# pruebas/B1.7/ — `08-persistencia/` (2026-10-19)

**Objetivo:** verificar que los 8 sub-documentos del Bloque B1.7 cubren la capa de persistencia de AppFlowy: `flowy-sqlite` (motor SQLite con diesel 2.1.0), `flowy-sqlite-vec` (extensión `vector0`), `KVStore`, `LocalStorage` de `collab-plugins`, `FileCache` de `flowy-storage`, migraciones diesel, y paths en disco por plataforma. La prueba literal del ROADMAP ("el `erDiagram` contiene todas las tablas de `schema.rs`") se cumple cuando `validate_B1_7_coverage.py` confirma que las 16 tablas del esquema están en el `erDiagram` de `01-sqlite-schema.md`.

**Ejecutar:**

```bash
OUT/_ledger/validate-B1.7.sh
SKILL/scripts/run_subagent.py --rol revisor --unit OUT/_ledger/units/B1.7.json \
    --out OUT/_ledger/pruebas/B1.7/revisor_output.json --out-root .
```

**Salida (2026-10-19):**

```
─── validate_template x8 ───
8/8 OK (modo `bridge`, regex ^0[6-9]-\d{2}-[a-z-]+$)
─── validate_evidence x8 ───
refs totales: 79 → 79 OK, 0 FAIL
─── validate_mermaid x8 ───
13 bloques Mermaid validados (incluye 1 `erDiagram` con 16 tablas)
─── validate_B1_7_coverage ───
schema_total: 16, doc_total: 16
missing_in_doc: []
extra_in_doc: []
code: OK

OK: B1.7 (template x8 + evidence x8 + mermaid x8 + coverage, 25/25 checks)
exit=0

[run_subagent] rol=revisor veredicto=aprobado correcciones=0 pct_efectivo=30
exit=0
```

## Resultado por validador (25/25 + revisor)

| Validador | Métrica | Resultado |
|---|---|---|
| `validate_template.py --template bridge` | 8/8 docs | OK |
| `validate_evidence.py` | refs totales 79 | 79 / 79 OK |
| `validate_mermaid.sh` | 13 bloques Mermaid | 13 / 13 OK |
| `validate_B1_7_coverage.py` | 16 tablas del esquema | **16 / 16 (100 %)** |
| `run_subagent.py --rol revisor` | veredicto | **aprobado** (0 correcciones, 30 % muestreo) |

## Cobertura de la prueba literal del ROADMAP ("`erDiagram` con todas las tablas de `schema.rs`")

Las 16 tablas declaradas con `diesel::table!` en `flowy-sqlite/src/schema.rs:3–170`, todas presentes en el `erDiagram` de `01-sqlite-schema.md §3`:

| Tabla | PK |
|---|---|
| `af_collab_metadata` | `object_id` |
| `chat_local_setting_table` | `chat_id` |
| `chat_message_table` | `message_id` |
| `chat_table` | `chat_id` |
| `collab_snapshot` | `id` |
| `index_collab_record_table` | `oid` |
| `local_ai_model_table` | `name` |
| `upload_file_part` | `(upload_id, e_tag)` |
| `upload_file_table` | `(workspace_id, file_id, parent_dir)` |
| `user_data_migration_records` | `id` |
| `user_table` | `id` |
| `user_workspace_table` | `id` |
| `workspace_members_table` | `(email, workspace_id)` |
| `workspace_setting_table` | `id` |
| `workspace_shared_user` | `(workspace_id, view_id, email)` |
| `workspace_shared_view` | `(uid, workspace_id, view_id)` |

## Los 8 sub-documentos

| # | Slug | Tamaño | Refs | Mermaid |
|---:|---|---:|---:|---:|
| 00 | `00-indice` | 130 | 1 | 1 (flowchart) |
| 01 | `01-sqlite-schema` | 250 | 12 | 2 (erDiagram + flowchart) |
| 02 | `02-kv` | 220 | 12 | 1 (classDiagram) |
| 03 | `03-collab-db` | 190 | 10 | 3 (classDiagram + 2 sequenceDiagram) |
| 04 | `04-file-cache` | 230 | 14 | 1 (classDiagram) |
| 05 | `05-sqlite-vec` | 200 | 11 | 3 (classDiagram + sequenceDiagram + flowchart) |
| 06 | `06-migraciones` | 170 | 8 | 1 (flowchart) |
| 07 | `07-rutas-plataforma` | 200 | 11 | 1 (flowchart) |

Total: ~1590 líneas, 79 refs verificadas, 13 Mermaid validados (incluye 1 `erDiagram` con 16 tablas).

## Artefactos

| Archivo | Contenido |
|---|---|
| `OUT/08-persistencia/{00,01,02,03,04,05,06,07}-*.md` | 8 sub-documentos, ~1590 líneas |
| `OUT/_ledger/pruebas/B1.7/validate_B1_7_coverage.py` | 2,2 KB — extrae las 16 tablas de `schema.rs` y del `erDiagram`, diff |
| `OUT/_ledger/pruebas/B1.7/coverage.json` | Salida estructurada (100 %: 16/16) |
| `OUT/_ledger/pruebas/B1.7/revisor_output.json` | `veredicto=aprobado` |
| `OUT/_ledger/validate-B1.7.sh` | Suite bash 1,7 KB (25/25 checks) |
| `OUT/_ledger/units/B1.7.json` | Unidad ad-hoc para el revisor |

## Cierre del Bloque B1.7

| Entregable | Estado |
|---|---|
| 8 sub-documentos de persistencia | ✅ |
| 1 `erDiagram` con las 16 tablas de `schema.rs` (prueba literal del ROADMAP) | ✅ |
| Suite `validate-B1.7.sh` con 25/25 checks | ✅ |
| Revisor aprueba | ✅ |
| `validate_template.py` ya soportaba `08-NN-*` por la regex extendida en B1.6 | ✅ |

Próxima fase: **B1.8 — `09-motor-ia/`** (modelo completo del motor de IA: `flowy-ai`, modelos locales, embeddings, MCP, ai_tool, middleware, search).
