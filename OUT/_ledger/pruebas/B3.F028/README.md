# Fase B3.F02.8 — Field settings y database_view

**Resultado (2026-10-19)**: 1 documento de feature (`F02.8-8-field-settings-settings-de-vista-database-view.md`) cubriendo los **21 archivos** listados en `OUT/_ledger/units/F02.8.json`.

## Validaciones

| Check | Comando | Resultado |
|---|---|---|
| Template (19 secciones) | `python3 SKILL/scripts/validate_template.py -t feature …` | OK (1/1) |
| Evidencia | `python3 SKILL/scripts/validate_evidence.py …` | OK (94/94 refs) |
| Mermaid | `bash SKILL/scripts/validate_mermaid.sh …` | OK |
| Cobertura | `awk` sobre `cobertura.csv` | OK (21/21) |
| Revisor gate-100 | `--gate-100 --feature-id F02` | **APROBADO** (0 correcciones) |

## Artefactos

- Documento: `OUT/09-features/F02-bases-de-datos/F02.8-8-field-settings-settings-de-vista-database-view.md`.
- Plan: `~/.local/share/kilo/plans/1792453115498-f02-6-to-12-completion.md`.
- Revisor: `revisor_output.json` (veredicto=aprobado).
- Cobertura: 21 archivos `verificado_por=autor_F02.8` en `cobertura.csv`.

## Próxima fase

Siguiente sub-feature F02 (según `_ledger/units/F0*.json`).
