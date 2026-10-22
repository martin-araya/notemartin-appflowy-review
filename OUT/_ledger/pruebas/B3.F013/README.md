# Fase B3.F01.3 — Media y archivos (scope-correction)

**Resultado (2026-10-19)**: 1 documento `3-media-y-archivos-…md` (231 líneas, 19 secciones, gate-100) cerrando la unidad F01.3 como **scope-correction**. El ledger F01.3 tiene **0 archivos** asignados porque B0.2.2 triage clasificó los widgets de media (image/video/file/cover/link_preview/link_embed, ~47 archivos físicos) en **F07** (Almacenamiento de archivos).

## Validaciones

| Check | Resultado |
|---|---|
| Template (19 secciones) | 1/1 OK |
| Evidence (refs `[fuente:]ruta:línea`) | 2/2 refs OK (referencias cruzadas a F01.1 cover) |
| Mermaid | 3 bloques: 1 flowchart + 1 sequenceDiagram + 1 stateDiagram-v2 OK |
| Cobertura | **0/0** scope-corrected (los 42 widgets viven en F07; 6 cover clásico ya en F01.1; 1 video en F07) |
| Revisor gate-100 | **APROBADO** (0 correcciones) |

## Corrección de scope oficializada

Las 6 categorías listadas en el ROADMAP **no tienen archivos en F01.3**. Su ubicación real:

| Carpeta física | ROADMAP F01.3 | Ubicación real |
|---|---|---|
| `editor_plugins/image/*` (21 archivos) | image | **F07** |
| `editor_plugins/video/*` (1) | video | **F07** |
| `editor_plugins/file/*` (7) | file | **F07** |
| `editor_plugins/cover/*` (2, inmersivo) | cover | **F07** |
| `editor_plugins/header/cover_*` (6, clásico) | (parte de cover) | **F01.1** (cerrado) |
| `editor_plugins/link_preview/*` (8+) | link_preview | **F07** |
| `editor_plugins/link_embed/*` (2) | link_embed | **F07** |

Detalle en §13 del doc con tabla explícita.

## Suite

- `validate-B3.F013.sh`: 4/4 verde (template + evidence + mermaid + 0/0 cobertura).
- `validate-B3.F010/F011/F012/F014.sh`: 4/4 verde (no regresión).
- `validate-A4.2.sh`: 7/7 verde.

## Adaptaciones a la skill

- Ninguna a `validate_template.py` / `validate_evidence.py` / `validate_mermaid.sh`.
- Nueva `validate-B3.F013.sh` que acepta explícitamente `0 archivos` en cobertura (pattern `awk -F, '$4=="F01" && $2 ~ /editor_plugins\/(image|video|file|cover|link_preview|link_embed)\/ && $6=="verificado"` retorna 0).

## Artefactos

- Documento: `OUT/09-features/F01-documentos-y-editor/3-media-y-archivos-image-video-file-cover-link-preview-link-embed.md`.
- Plan: `~/.local/share/kilo/plans/1792429084675-b3-f013-media-archivos-plan.md`.
- Revisor: `revisor_output.json` (`aprobado, 0 correcciones`).
- Cobertura: `coverage.json` (0 archivos F01.3).

## Próxima fase

- **F01.5** — Bases embebidas en documentos (3 archivos físicos).