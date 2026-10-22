# B2.1 — Catálogo de eventos FFI (`11-catalogo-eventos-ffi.md`)

## Artefactos generados

- `OUT/11-catalogo-eventos-ffi.md` (774 líneas, 107 KB, 229 variantes)
- `OUT/_ledger/validate-B2.1.sh` — suite de 4 checks
- `OUT/_ledger/pruebas/B2.1/count_rows_229.py` — prueba literal del ROADMAP
- `OUT/_ledger/pruebas/B2.1/validate-B2.1.log` — log de la corrida en verde
- `SKILL/scripts/build_catalog_events.py` — generador determinista
- `SKILL/scripts/validate_template.py` — extendido con modo `catalogue`

## Estructura del documento

| § | Contenido | Filas |
|---|---|---|
| §1 | Cómo leer este catálogo | ~12 |
| §2 | Arquitectura del registro de eventos (Mermaid `flowchart TD`) | ~28 |
| §3 | Resumen por crate (tabla 8 filas) | ~16 |
| §4 | Índice global de las 229 variantes | 1 + 2 + 229 = 232 |
| §5 | Catálogo por crate (8 sub-secciones, 229 filas) | ~480 |
| §6 | Eventos sin handler registrado (5 filas) | ~10 |
| §7 | Conteo de filas y prueba literal | ~12 |
| §8 | Cobertura y referencias cruzadas | ~10 |
| §9 | Preguntas abiertas (vacío) | ~5 |
| §10 | Relacionado con | ~12 |

## Cobertura

- 229/229 variantes enumeradas.
- 224/224 handlers registrados referenciados (file:line resuelto contra inventario).
- 5/5 eventos `sin_handler` documentados en §6.
- 6 bloques Mermaid validados con `mmdc`.
- 229/229 refs `[fuente:]ruta:línea` validadas contra `inventario.json`.

## Cómo regenerar

```bash
SKILL/scripts/build_catalog_events.py              # genera OUT/11-...md
OUT/_ledger/validate-B2.1.sh                      # corre los 4 checks
```

Si `events.json` cambia (nuevos crates, nuevas variantes), regenerar:

```bash
SKILL/scripts/extract_events.py  # A2.1 (output: OUT/_ledger/extract/events.json)
SKILL/scripts/build_catalog_events.py
OUT/_ledger/validate-B2.1.sh
```

## Estado

- ROADMAP.md línea 173 → ✅
- STATE.md → entrada B2.1 añadida
- 00-INDEX.md → enlace nuevo
- SKILL/CHANGELOG.md → entrada `[0.3.0]`