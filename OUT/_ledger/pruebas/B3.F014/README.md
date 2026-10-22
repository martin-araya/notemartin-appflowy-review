# Fase B3.F01.4 — Menciones

**Resultado (2026-10-19)**: 1 documento `4-menciones-pagina-fecha-persona-recordatorio-inline-actions.md` (~310 líneas, 19 secciones, gate-100) cubriendo los **10 archivos** del ledger F01.4 (9 ui + 1 bloc) en `appflowy:editor_plugins/mention/`.

## Validaciones

| Check | Resultado |
|---|---|
| Template | 1/1 OK |
| Evidence | 22/22 refs OK |
| Mermaid | 3 bloques: 1 flowchart + 1 sequenceDiagram + 1 stateDiagram-v2 OK |
| Cobertura | 10/10 archivos verificados en `cobertura.csv` (651 F01 global) |
| Revisor gate-100 | **APROBADO** (0 correcciones) |

## Corrección de scope (Riesgo §1, oficializado)

El ROADMAP y el título de la unidad mencionan `inline_actions` y `emoji`, pero el ledger F01.4 sólo asigna 10 archivos en `mention/`. Las 3 unidades responsables:

- `editor_plugins/inline_actions/` — **no existe** como carpeta (no hay archivos físicos en el repo).
- `mobile/presentation/inline_actions/` — 14 archivos en **F16** (mobile).
- `plugins/emoji/` — archivos en **F00** (system).
- `shared/icon_emoji_picker/` — emoji picker widgets en **F21** (shared).

§2.1 y §13 del doc lo declaran explícitamente para que el lector del ROADMAP no los busque en F01.4.

## Suite

- `validate-B3.F014.sh`: 4/4 verde.
- `validate-B3.F010/F011/F012.sh`: 4/4 verde (no regresión).
- `validate-A4.2.sh`: 7/7 verde.

## Adaptaciones a la skill

- Ninguna (reutiliza pattern de `validate-B3.F012.sh`).
- Pequeña corrección en el ledger: `unit["documento"]` de F01.4 apuntaba al nombre corto original; actualizado al nombre completo creado.

## Artefactos

- Documento: `OUT/09-features/F01-documentos-y-editor/4-menciones-pagina-fecha-persona-recordatorio-inline-actions.md`.
- Plan: `~/.local/share/kilo/plans/1792429084675-b3-f014-menciones-plan.md`.
- Revisor: `revisor_output.json` (`aprobado, 0 correcciones`).
- Cobertura: 10 archivos `verificado_por=autor+F01.4`.

## Próxima fase

- **B3.F01.5** — Bases de datos embebidas en documentos.
