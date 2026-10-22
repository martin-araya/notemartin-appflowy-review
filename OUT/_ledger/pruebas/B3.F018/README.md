# Fase B3.F01.8 — Infraestructura del editor

**Resultado (2026-10-19)**: 1 documento `8-infraestructura-del-editor-...md` (~478 líneas, 19 secciones, gate-100) cubriendo los **20 archivos** del ledger F01.8 en `appflowy:editor_plugins/{block_transaction_handler, transaction_handler, migration, parsers}/`.

## Validaciones

| Check | Resultado |
|---|---|
| Template (19 secciones) | 1/1 OK |
| Evidence | 6/6 refs OK |
| Mermaid | 3 bloques: 1 flowchart + 1 sequenceDiagram + 1 stateDiagram-v2 OK |
| Cobertura | 20/20 archivos verificados en `cobertura.csv` (798 F01 global) |
| Revisor gate-100 | **APROBADO** (0 correcciones) |

## Distribución por carpeta

| Carpeta | Archivos | Capa |
|---|---:|---|
| `block_transaction_handler/` | 1 (`block_transaction_handler.dart`, 39 líneas) | ui (base abstracta) |
| `transaction_handler/` | 4 (block_transaction_handler.dart + editor_transaction_handler.dart + editor_transaction_service.dart + mention_transaction_handler.dart) | ui (abstractas + servicio) |
| `migration/` | 1 (`editor_migration.dart`, 272 líneas, AppFlowy 0.1.x → 0.2) | ui |
| `parsers/` | 13 (10 `NodeParser` específicos + 1 file parser con 3 clases en `custom_image_node_parser.dart` + 2 `CustomMarkdownParser` + 2 aggregate exports) | ui |
| **TOTAL** | **20 archivos** | **20 ui** |

## Sin BLoCs nuevos

- `EditorTransactionService` es un `StatefulWidget` (no Bloc). Los transaction handlers ya cubiertos en F01.2 (`SubPageTransactionHandler`) y F01.4 (`ChildPageTransactionHandler`, `DateTransactionHandler`) están en otras unidades.
- El único cambio de scope del F01.8 es la infraestructura transversal (no lógica de negocio).

## Corrección de scope oficializada

El ROADMAP línea 219 lista 8 categorías (`error, base, extensions, shared_context`) que **NO** están en el ledger F01.8 — viven en **F01.0.1** (appflowy side, 139 archivos, cerrado). Doc §2 + §13 lo declaran explícitamente.

## Suite

- `validate-B3.F018.sh`: 4/4 verde (template=1/1, evidence=6/6, mermaid=3 OK, cobertura=20/20).
- A4.2 + B3.F010/F011/F012/F013/F014/F015/F016/F017: 4/4 cada uno (sin regresión).
- Cobertura F01 global: 798 archivos verificados.

## Adaptaciones a la skill

- Nueva `OUT/_ledger/validate-B3.F018.sh` (pattern F01.7).
- Sin cambios en `validate_template.py`, `validate_evidence.py`, `validate_mermaid.sh`, ni `validate-A4.2.sh`.

## Artefactos

- Documento: `OUT/09-features/F01-documentos-y-editor/8-infraestructura-…md` (~478 líneas).
- Plan: `~/.local/share/kilo/plans/1792429084675-b3-f018-infraestructura-editor-plan.md`.
- Revisor: `revisor_output.json` (`aprobado, 0 correcciones`).
- Cobertura: 20 archivos `verificado_por=autor+F01.8`.

## Próxima fase

- **B3.F01.9** — IA en el editor: `editor_plugins/ai/` (0 archivos en ledger → scope-correction similar a F01.3).
