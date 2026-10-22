# B2.2 — Catálogo de entidades protobuf (`12-catalogo-entidades-protobuf.md`)

## Artefactos generados

- `OUT/12-catalogo-entidades-protobuf.md` (1493 líneas, ~159 KB, 439 entidades)
- `OUT/_ledger/validate-B2.2.sh` — suite de 4 checks
- `OUT/_ledger/pruebas/B2.2/count_rows_439.py` — prueba literal del ROADMAP
- `OUT/_ledger/pruebas/B2.2/validate-B2.2.log` — log de la corrida en verde
- `SKILL/scripts/build_catalog_protobuf.py` — generador determinista
- `SKILL/scripts/validate_template.py` — regex del modo `catalogue` extendido a `^1[1-6]-[a-z0-9-]+$`

## Distribución por crate

| Crate | Structs | Enums | Total | Inputs de eventos | Outputs de eventos | Huérfanas |
|---|---:|---:|---:|---:|---:|---:|
| flowy-database2 | 152 | 18 | 170 | 67 | 41 | 62 |
| flowy-user | 74 | 8 | 82 | 38 | 21 | 23 |
| flowy-folder | 57 | 7 | 64 | 27 | 12 | 25 |
| flowy-ai | 45 | 6 | 51 | 19 | 6 | 26 |
| flowy-document | 44 | 6 | 50 | 16 | 4 | 30 |
| flowy-search | 12 | 1 | 13 | 2 | 0 | 11 |
| flowy-storage | 2 | 1 | 3 | 1 | 0 | 2 |
| dart-ffi | 2 | 1 | 3 | 0 | 0 | 3 |
| flowy-date | 1 | 1 | 2 | 2 | 0 | 0 |
| flowy-notification | 0 | 1 | 1 | 0 | 0 | 1 |
| **TOTAL** | **389** | **50** | **439** | **172** | **84** | **223** |

(Suma de inputs+outputs sobre dos subsets: 172 entidades marcadas como `is_input_of` ≥ 1 + 84 como `is_output_of` ≥ 1 = 216 ≤ 439; las 223 huérfanas son las no marcadas; 439 - 216 = 223. Coherente.)

## Cobertura

- 439/439 entidades enumeradas (§4 + §5.* = 439 + 439).
- 223/223 huérfanas documentadas en §6.
- 1101/1101 refs `[fuente:]ruta:línea` validadas contra `inventario.json`.
- 6 bloques Mermaid validados con `mmdc` (1 arquitectura + 5 por crate con >20 entidades).

## Cómo regenerar

```bash
SKILL/scripts/build_catalog_protobuf.py       # genera OUT/12-...md
OUT/_ledger/validate-B2.2.sh                 # corre los 4 checks
```

Si `protobuf.json` cambia (nuevas entidades), regenerar:

```bash
SKILL/scripts/extract_protobuf.py  # A2.2 (output: OUT/_ledger/extract/protobuf.json)
SKILL/scripts/build_catalog_protobuf.py
OUT/_ledger/validate-B2.2.sh
```

## Estado

- ROADMAP.md línea 174 → ✅
- STATE.md → entrada B2.2 añadida
- 00-INDEX.md → regenerado (enlace nuevo)
- SKILL/CHANGELOG.md → entrada `[0.4.0]`