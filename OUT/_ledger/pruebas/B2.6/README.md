# B2.6 — Catálogo de flags/rutas/atajos/i18n/startup (`16-catalogo-flags-rutas-atajos.md`)

## Artefactos generados

- `OUT/16-catalogo-flags-rutas-atajos.md` (1 826 líneas, ~270 KB, 1 709 entradas)
- `OUT/_ledger/validate-B2.6.sh` — suite de 4 checks
- `OUT/_ledger/pruebas/B2.6/count_rows_misc.py` — prueba literal del ROADMAP
- `OUT/_ledger/pruebas/B2.6/validate-B2.6.log` — log de la corrida en verde
- `SKILL/scripts/build_catalog_misc.py` — generador determinista

## Distribución por categoría

| Categoría | Entradas | Archivo |
|---|---:|---|
| §4 Rutas (`go_router`) | 35 | `lib/startup/tasks/generate_router.dart` |
| §5 Atajos / hotkeys | 13 | `lib/workspace/presentation/home/hotkeys.dart` |
| §6 Feature flags | 9 | `lib/shared/feature_flags.dart` |
| §7 i18n keys | 1637 | (`easy_localization` keys en `**/*.dart`) |
| §8 Startup tasks | 15 | `lib/startup/startup.dart` |
| **TOTAL** | **1709** | — |

Adicional:
- §5.2 nota: `CommandShortcutEvent` tiene **0 variantes** detectadas por el extractor (AppFlowy no usa este patrón; todos los atajos viven en `hotkeys.dart`).

## Cobertura

- 35 + 13 + 9 + 1637 + 15 = **1709 entradas**.
- 57/57 refs `[fuente:]ruta:línea` validadas contra `inventario.json`.
- 1 bloque Mermaid validados con `mmdc` (arquitectura discovery).

## Cómo regenerar

```bash
SKILL/scripts/build_catalog_misc.py         # genera OUT/16-...md
OUT/_ledger/validate-B2.6.sh                # corre los 4 checks
```

Si `misc.json` cambia (nuevas rutas/atajos/flags/keys/tasks), regenerar:

```bash
SKILL/scripts/extract_misc.py    # A2.6 (output: OUT/_ledger/extract/misc.json)
SKILL/scripts/build_catalog_misc.py
OUT/_ledger/validate-B2.6.sh
```

## Estado

- ROADMAP.md línea 178 → ✅
- STATE.md → entrada B2.6 añadida
- 00-INDEX.md → regenerado
- SKILL/CHANGELOG.md → entrada `[0.8.0]`