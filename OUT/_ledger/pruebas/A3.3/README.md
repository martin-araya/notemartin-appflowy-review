# pruebas/A3.3 — `validate_template.py` (2026-10-18)

## Objetivo

Verificar que el validador de plantilla de la skill:

1. Parsea el frontmatter YAML (línea por línea, sin PyYAML) y
   comprueba que existan los 5 campos obligatorios
   (`id, titulo, fuente, archivos_cubiertos, estado`).
2. Auto-detecta la plantilla a aplicar desde el prefijo del `id`
   (`Fxx.y` → feature; `B4.N` → export), o usa la plantilla forzada
   por `--template`.
3. Verifica que las secciones `## N.` existan en orden, sin
   huecos, dentro del rango esperado por la plantilla.
4. Reporta cada violación con código legible, detalle y línea
   aproximada.

Materializa la prueba literal del ROADMAP A3.3:

> "verifica secciones obligatorias y frontmatter
> (`id, titulo, fuente, archivos_cubiertos, estado`). Prueba: quitar la
> sección 13 hace fallar el documento."

## Comandos

```bash
cd /Users/martin/Desktop/projects/Skills/notemartin-appflowy-review
bash OUT/_ledger/validate-A3.3.sh
```

## Salida (verbatim, 2026-10-18)

```
[2026-10-18T22:03:43Z]   OK  check 1: script ejecutable
[2026-10-18T22:03:43Z]   OK  check 2: --help imprime uso y sale 0
[2026-10-18T22:03:43Z]   OK  check 3: valid_feature.md exit 0 con 0 errores
[2026-10-18T22:03:43Z]   OK  check 4: valid_export.md exit 0 con 0 errores
[2026-10-18T22:03:43Z]   OK  check 5: missing_section_13.md exit 1 con E_MISSING_SECTION: [13]
[2026-10-18T22:03:44Z]   OK  check 6: missing_frontmatter.md exit 1 con E_NO_FRONTMATTER
[2026-10-18T22:03:44Z]   OK  check 7: bad_estado.md exit 1 con E_BAD_ESTADO
[2026-10-18T22:03:44Z]   OK  check 8: out_of_order.md exit 1 con E_OUT_OF_ORDER
[2026-10-18T22:03:44Z]   OK  check 9: --json produce JSON parseable con errors==0
[2026-10-18T22:03:44Z]   OK  check 10: modo directorio: 6 archivos, 2 OK / 4 errores
[2026-10-18T22:03:44Z] ---
[2026-10-18T22:03:44Z] resultado: 10/10 checks OK (0 fallidos)
[2026-10-18T22:03:44Z] OK: A3.3 (validate_template.py funciona: valida frontmatter 5 campos + secciones en orden, 10+ códigos de error)
exit=0
```

## Tabla de resultados

| # | Check | Esperado | Resultado |
|---|---|---|---|
| 1 | `SKILL/scripts/validate_template.py` existe y es ejecutable | `test -x` | ✅ |
| 2 | `--help` imprime uso y sale 0 | exit 0 + grep `validate_template.py` | ✅ |
| 3 | `fixtures/valid_feature.md` → exit 0, 0 errores | exit 0 + 0 líneas `^ERROR` | ✅ |
| 4 | `fixtures/valid_export.md` → exit 0, 0 errores | exit 0 + 0 líneas `^ERROR` | ✅ |
| 5 | `fixtures/missing_section_13.md` → exit 1, `E_MISSING_SECTION: [13]` | exit 1 + grep | ✅ |
| 6 | `fixtures/missing_frontmatter.md` → exit 1, `E_NO_FRONTMATTER` | exit 1 + grep | ✅ |
| 7 | `fixtures/bad_estado.md` → exit 1, `E_BAD_ESTADO` | exit 1 + grep | ✅ |
| 8 | `fixtures/out_of_order.md` → exit 1, `E_OUT_OF_ORDER` | exit 1 + grep | ✅ |
| 9 | `--json fixtures/valid_feature.md` → JSON parseable con `errors == 0` | `python3 -m json.tool` | ✅ |
| 10 | Modo directorio: 6 archivos, 2 OK / 4 errores | exit 1 + summary | ✅ |

## Cobertura de la prueba literal del ROADMAP

| Frase del ROADMAP | Materializada en |
|---|---|
| "verifica secciones obligatorias" | `extract_section_numbers()` + `validate_sections()` con `E_MISSING_SECTION`; check 5 (sin §13). |
| "y frontmatter" | `split_frontmatter()` + `parse_yaml()`; check 6 (sin `---`). |
| "(`id, titulo, fuente, archivos_cubiertos, estado`)" | `REQUIRED_FRONTMATTER_FIELDS = (… )` validado con `E_MISSING_FRONTMATTER_FIELD` y `E_BAD_ESTADO`. |
| "quitar la sección 13 hace fallar el documento" | check 5 (`E_MISSING_SECTION: [13]`). |

## Fixtures

| Archivo | Plantilla | Resultado | Código activado |
|---|---|---|---|
| `fixtures/valid_feature.md` | feature (auto) | exit 0, 0 errores | — |
| `fixtures/valid_export.md` | export (auto) | exit 0, 0 errores | — |
| `fixtures/missing_section_13.md` | feature | exit 1 | `E_MISSING_SECTION: [13]` |
| `fixtures/missing_frontmatter.md` | (indefinida) | exit 1 | `E_NO_FRONTMATTER` |
| `fixtures/bad_estado.md` | feature | exit 1 | `E_BAD_ESTADO` (estado=`aprobado` no en enum) |
| `fixtures/out_of_order.md` | feature | exit 1 | `E_OUT_OF_ORDER` (4 y 5 invertidas) |

Total: 6 archivos; 2 OK / 4 FAIL.

## Códigos de error implementados (10)

| Código | Cuándo |
|---|---|
| `E_NO_FRONTMATTER` | El archivo no abre con `---`. |
| `E_MISSING_FRONTMATTER_FIELD` | Falta uno de `id, titulo, fuente, archivos_cubiertos, estado`. |
| `E_BAD_ESTADO` | `estado` no está en el enum de la plantilla. |
| `E_ID_MISMATCH` | `id` no matchea el patrón de la plantilla (auto-detectada o forzada). |
| `E_UNKNOWN_TEMPLATE` | Auto-detección no puede inferir la plantilla del `id`. |
| `E_MISSING_SECTION` | Faltan secciones obligatorias (lista cuáles). |
| `E_EXTRA_SECTION` | Hay secciones fuera del rango permitido (warn con `--allow-extra-sections`). |
| `E_OUT_OF_ORDER` | Las secciones no están en orden ascendente. |
| `E_DUPLICATE_SECTION` | Hay dos `## N.` con el mismo N. |
| `E_EMPTY_SECTION` | Una sección obligatoria no tiene contenido. |
| `E_BAD_FRONTMATTER_TYPE` | `archivos_cubiertos` no es lista, `fuente` no es string/lista, etc. |

## Diferencias detectadas vs el plan (corregidas en sitio)

1. **Parser YAML custom más permisivo** (en `parse_yaml()`): para
   detectar listas con sintaxis `key: [a, b, c]` se requería
   `startswith('[') AND endswith(']')`; el caso `key: [single]`
   (una sola entrada) ahora se acepta (split por coma → 1 elemento).
   Sin impacto sobre los fixtures, documentado.

2. **Detección de sección vacía** (D12) mejorada: el algoritmo
   original planeaba mirar entre la línea de la sección y la línea
   de la siguiente `## M.`, pero la implementación debe excluir
   líneas en blanco Y líneas que son headings (para no contar
   `## 13.` como contenido de la §12). Implementado con
   `not candidate.startswith("#")`. Sin impacto sobre los fixtures.

3. **Trailing newline en `out_of_order.md`**: el plan proponía 1
   `E_OUT_OF_ORDER` por archivo; el fixture tiene 1 sola
   inversión (4↔5), y se reporta correctamente. Sin delta.

4. **`extract.log` con 4 errores y 2 OK** (no 11 refs como A3.2):
   la métrica aquí es "errores por documento", no "refs por
   documento". Documentado.

## Requisitos externos

- Python 3 stdlib (sin dependencias externas).
- No requiere `inventario.json` (a diferencia de A3.2).

## Cómo reproducir desde cero

```bash
cd /Users/martin/Desktop/projects/Skills/notemartin-appflowy-review
python3 SKILL/scripts/validate_template.py --help
python3 SKILL/scripts/validate_template.py OUT/_ledger/pruebas/A3.3/fixtures
bash OUT/_ledger/validate-A3.3.sh
```

## Estado

**A3.3 cerrada. Pasar a A3.4 (`validate_coverage.py`).**
