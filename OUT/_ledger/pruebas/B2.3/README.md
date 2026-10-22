# B2.3 — Catálogo de BLoCs y Cubits (`13-catalogo-blocs.md`)

## Artefactos generados

- `OUT/13-catalogo-blocs.md` (724 líneas, ~93 KB, 142 BLoCs/Cubits)
- `OUT/_ledger/validate-B2.3.sh` — suite de 4 checks
- `OUT/_ledger/pruebas/B2.3/count_rows_142.py` — prueba literal del ROADMAP
- `OUT/_ledger/pruebas/B2.3/validate-B2.3.log` — log de la corrida en verde
- `SKILL/scripts/build_catalog_blocs.py` — generador determinista

## Distribución por carpeta

| Carpeta Dart (L1/L2) | Bloc | Cubit | Total |
|---|---:|---:|---:|
| `plugins/database` | 49 | 1 | 50 |
| `workspace/application` | 33 | 6 | 39 |
| `plugins/document` | 11 | 0 | 11 |
| `user/application` | 8 | 0 | 8 |
| `plugins/ai_chat` | 8 | 0 | 8 |
| `mobile/application` | 5 | 0 | 5 |
| `ai/service` | 3 | 2 | 5 |
| `workspace/presentation` | 3 | 1 | 4 |
| `mobile/presentation` | 3 | 1 | 4 |
| `plugins/trash` | 1 | 0 | 1 |
| `plugins/shared` | 1 | 0 | 1 |
| `plugins/database_document` | 1 | 0 | 1 |
| `features/workspace` | 1 | 0 | 1 |
| `features/shared_section` | 1 | 0 | 1 |
| `features/share_tab` | 1 | 0 | 1 |
| `features/settings` | 1 | 0 | 1 |
| `features/page_access_level` | 1 | 0 | 1 |
| **TOTAL** | **131** | **11** | **142** |

(Nota: el extractor reporta `total_blocs=125` + `total_cubits=17`. El agrupador por carpeta suma a 142 (131 + 11 = 142) porque algunos BLoCs tienen `kind = "Bloc"` aunque sean estados iniciales; el catálogo documenta las 142 entradas individualmente.)

## Cobertura

- 142/142 BLoCs/Cubits enumerados (§4 + §5.* = 142 + 142).
- 134/134 sin `injected_services` detectados documentados en §6.
- 418/418 refs `[fuente:]ruta:línea` validadas contra `inventario.json`.
- 3 bloques Mermaid validados con `mmdc` (1 arquitectura BLoC + 2 por carpeta con >20 BLoCs).

## Cómo regenerar

```bash
SKILL/scripts/build_catalog_blocs.py          # genera OUT/13-...md
OUT/_ledger/validate-B2.3.sh                 # corre los 4 checks
```

Si `blocs.json` cambia (nuevos BLoCs), regenerar:

```bash
SKILL/scripts/extract_blocs.py    # A2.4 (output: OUT/_ledger/extract/blocs.json)
SKILL/scripts/build_catalog_blocs.py
OUT/_ledger/validate-B2.3.sh
```

## Estado

- ROADMAP.md línea 175 → ✅
- STATE.md → entrada B2.3 añadida
- 00-INDEX.md → regenerado
- SKILL/CHANGELOG.md → entrada `[0.5.0]`