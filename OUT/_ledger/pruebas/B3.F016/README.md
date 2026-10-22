# Fase B3.F01.6 — Interaccion (slash_menu, block_menu, actions, toolbars, shortcuts, find_and_replace, copy_and_paste)

**Resultado (2026-10-19)**: 7 documentos en `OUT/09-features/F01-documentos-y-editor/` (F01.6.0 indice + F01.6.{1..6} sub-unidades) cubriendo los 115 archivos UI del feature F01.6 distribuídos por: slash menu (27) / block menu + actions + context menu (14) / drag to reorder (5) / toolbars desktop+mobile+items+link (51) / copy & paste (10) / shortcuts + find_and_replace + keyboard (8). Gate revisor 100% × 7 sub-unidades: aprobado sin correcciones.

## Validaciones

| Check | Resultado |
|---|---|
| Template (19 secciones) × 7 docs | 7/7 OK |
| Evidence | 7/7 docs con refs `[fuente:]ruta:línea` (todos verificados contra inventario) |
| Mermaid | 22 bloques totales (3+3+4+3+3+3+3 — flowchart, sequence, state) OK |
| Cobertura | 115/115 archivos F01.6 verificados en `cobertura.csv` |
| Revisor gate-100 × 7 sub-unidades | `aprobado, 0 correcciones` |

## Decisión: dividir F01.6 (115 archivos) en 7 sub-unidades

Siguiendo el patrón F01.0 (split en F01.0.{1,2,3.1-5} + F01.0.0 indice), F01.6 se dividió porque estaba justo debajo del umbral de ~120 archivos. **7 sub-unidades** según cohesión funcional:

| Sub-unidad | Carpeta(s) | Archivos | Doc | Rol principal |
|---|---|---:|---|---|
| F01.6.0 | (n/a) | 0 | `6.0-indice-interaccion.md` | Indice cross-cutting |
| F01.6.1 | `slash_menu/` | 27 | `6.1-slash-menu-elementos.md` | `/` → `SelectionMenuItem` × 25 |
| F01.6.2 | `block_menu/` + `actions/block_action_*` + `actions/option/` + `actions/mobile_block_action_buttons.dart` + `context_menu/` | 14 | `6.2-…md` | Block menu + `BlockActionOptionCubit` + context menu |
| F01.6.3 | `actions/drag_to_reorder/` + `actions/menu_extension.dart` + `options_toolbar_item.dart` | 5 | `6.3-…md` | Drag & drop + options toolbar |
| F01.6.4 | `desktop_toolbar/` + `mobile_toolbar_v3/` + `mobile_floating_toolbar/` + `toolbar_item/` + `undo_redo/` + `align_toolbar_item/` | 51 | `6.4-…md` | Floating + mobile toolbars + items |
| F01.6.5 | `copy_and_paste/` | 10 | `6.5-…md` | `ClipboardService` + detectores paste |
| F01.6.6 | `shortcuts/` + `find_and_replace/` + `keyboard_interceptor/` + `exit_edit_mode_command.dart` | 8 | `6.6-…md` | Atajos globales + find & replace |

## Suite

- `validate-B3.F016.sh`: 7/7 + cobertura 115/115 = **OK**.
- `validate-A4.2.sh`: 7/7 (regresión check).
- `validate-B3.F010/F011/F012/F013/F014/F015.sh`: 4/4 cada uno (sin regresión).

## Adaptaciones a la skill

- **Nueva** `SKILL/scripts/split_F0106.py` (auto-división F01.6 → 7 sub-unidades + 1 indice; análoga a `split_F0103.py` de F01.0).
- **Actualizada** `SKILL/scripts/build_units.py`: no afectada (regenera F01.6.json desde cobertura).
- **Actualizado** `OUT/_ledger/validate-A4.2.sh` Check 3: 106 unidades (= 100 base + 7 F01.6 split − 1 F01.6 maestro); post-build ejecuta `split_F0106.py` tras `split_F0103.py`. Excluye `F01.6.0` (indice) de la suma total.
- **Nueva** `OUT/_ledger/validate-B3.F016.sh` valida 7 docs + cobertura específica F01.6 (115/115).
- **Sin cambios** en `validate_template.py`, `validate_evidence.py`, `validate_mermaid.sh`.

## Artefactos

- 7 documentos (en `OUT/09-features/F01-documentos-y-editor/6.*.md`).
- 7 unit JSON (`F01.6.{0..6}.json`).
- `OUT/_ledger/validate-B3.F016.sh` + log.
- `OUT/_ledger/pruebas/B3.F016/{7 docs, 7 revisor_F01.6.X.json, validate-B3.F016.sh+log, coverage.json, README.md}`.
- Plan: `~/.local/share/kilo/plans/1792429084675-b3-f016-interaccion-plan.md`.
- Split helper: `SKILL/scripts/split_F0106.py`.

## Próxima fase

- **B3.F01.7** — Estilo: font, background_color, page_style (9 archivos según ledger).
- **B3.F01.8** — Infraestructura del editor: transaction_handler, block_transaction_handler, migration, parsers, error, base, extensions, shared_context (20 archivos).
- **B3.F01.9** — IA en el editor: `editor_plugins/ai/` (0 archivos en ledger → scope-correction similar a F01.3).
