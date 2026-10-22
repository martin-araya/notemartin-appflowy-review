# B2.5 — Catálogo de ErrorCode (`15-catalogo-errores.md`)

## Artefactos generados

- `OUT/15-catalogo-errores.md` (661 líneas, ~95 KB, 133 ErrorCode variants)
- `OUT/_ledger/validate-B2.5.sh` — suite de 4 checks
- `OUT/_ledger/pruebas/B2.5/count_rows_133.py` — prueba literal del ROADMAP
- `OUT/_ledger/pruebas/B2.5/validate-B2.5.log` — log de la corrida en verde
- `SKILL/scripts/build_catalog_errors.py` — generador determinista

## Distribución por categoría

| Categoría | Variantes | Crane típico |
|---|---:|---|
| Database | 25 | flowy-database2 |
| Workspace | 14 | flowy-user |
| Auth | 13 | flowy-user |
| View | 7 | flowy-folder |
| Generic | 7 | cualquier |
| User | 5 | flowy-user |
| Document | 5 | flowy-document |
| LocalAI | 5 | flowy-ai |
| Network | 8 | flowy-server |
| AI | 4 | flowy-ai |
| Customization | 6 | flowy-user |
| Storage | 8 | flowy-storage |
| Search | 4 | flowy-search |
| … | … | … |
| **TOTAL** | **133** | — |

(Ver §3 del documento para el desglose completo de las 30 categorías.)

## Cobertura

- 133/133 ErrorCode enumerados (§4 + §5.* = 133 + 133).
- 1/1 sentinels documentado en §6 (sólo `Internal`; no hay variantes `Unknown*` en este snapshot).
- 267/267 refs `[fuente:]ruta:línea` validadas contra `inventario.json`.
- 4 bloques Mermaid validados con `mmdc` (1 arquitectura + 3 por categoría con ≥10 variantes).

## Cómo regenerar

```bash
SKILL/scripts/build_catalog_errors.py        # genera OUT/15-...md
OUT/_ledger/validate-B2.5.sh               # corre los 4 checks
```

Si `misc.json` cambia (nuevos códigos), regenerar:

```bash
SKILL/scripts/extract_misc.py    # A2.6 (output: OUT/_ledger/extract/misc.json)
SKILL/scripts/build_catalog_errors.py
OUT/_ledger/validate-B2.5.sh
```

## Estado

- ROADMAP.md línea 177 → ✅
- STATE.md → entrada B2.5 añadida
- 00-INDEX.md → regenerado
- SKILL/CHANGELOG.md → entrada `[0.7.0]`