# Fase B3.F01.5 — Bases embebidas en documentos

**Resultado (2026-10-19)**: 1 documento `5-bases-de-datos-embebidas-en-documentos.md` (293 líneas, 19 secciones, gate-100) cubriendo los **3 archivos** del ledger F01.5 (`editor_plugins/database/`) más la corrección de scope para `plugins/database_document/`.

## Validaciones

| Check | Resultado |
|---|---|
| Template (19 secciones) | 1/1 OK |
| Evidence (refs `[fuente:]ruta:línea`) | 7/7 refs OK |
| Mermaid | 3 bloques: 1 flowchart + 1 sequenceDiagram + 1 stateDiagram-v2 OK |
| Cobertura | 3/3 archivos verificados en `cobertura.csv` (654 F01 global) |
| Revisor gate-100 | **APROBADO** (0 correcciones) |

## Distinción inline vs referenced

| Tipo | Inline (`inline_*_menu_item.dart`) | Referenced (`referenced_*_menu_item.dart`) |
|---|---|---|
| Grid | ✓ `inlineGridMenuItem` | ✓ `referencedGridMenuItem` |
| Board | ✓ `inlineBoardMenuItem` | ✓ `referencedBoardMenuItem` |
| Calendar | — | ✓ `referencedCalendarMenuItem` (única vía) |
| Document | — | ✓ `referencedDocumentMenuItem` |

- **Inline**: `ViewBackendService.createView(parentViewId, "Untitled", ViewLayoutPB.X)` → `editorState.insertInlinePage(...)`.
- **Referenced**: `showLinkToPageMenu(editorState, menuService, pageType)` permite elegir un view existente.

## Atributos cubiertos

`DatabaseBlockKeys` (6): `gridType`, `boardType`, `calendarType`, `parentID`, `viewID`, `enableCompactMode`. Validador del builder exige `node.children.isEmpty && parentID is String && viewID is String`.

`overflowTypes = {grid, board}` (calendar siempre cabe).

## Suite

- `validate-B3.F015.sh`: 4/4 verde.
- `validate-B3.F010/F011/F012/F013/F014.sh`: 4/4 verde (no regresión).
- `validate-A4.2.sh`: 7/7 verde.

## Adaptaciones a la skill

- Ninguna a `validate_template.py` / `validate_evidence.py` / `validate_mermaid.sh`/`validate-A4.2.sh`.
- Nueva suite `validate-B3.F015.sh` siguiendo patrón F01.4 (para 3 archivos con cobertura esperada).

## Artefactos

- Documento: `OUT/09-features/F01-documentos-y-editor/5-bases-de-datos-embebidas-en-documentos.md`.
- Plan: `~/.local/share/kilo/plans/1792429084675-b3-f015-bases-de-datos-embebidas-plan.md`.
- Revisor: `revisor_output.json` (`aprobado, 0 correcciones`).
- Cobertura: 3 archivos `verificado_por=autor+F01.5`.

## Próxima fase

- **F01.6** — Interacción: slash_menu, block_menu, context_menu, actions, toolbars, shortcuts, find_and_replace, copy_and_paste (115 archivos).