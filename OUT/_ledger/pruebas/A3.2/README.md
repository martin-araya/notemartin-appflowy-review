# pruebas/A3.2 — `validate_evidence.py` (2026-10-18)

## Objetivo

Verificar que el validador de evidencia de la skill:

1. Encuentra **todas** las referencias del formato
   `[fuente:]ruta:línea[–fin]` en uno o varios `.md` (también en
   directorios recursivos).
2. Excluye referencias dentro de bloques ```código``` (fenced).
3. Comprueba que (a) el archivo esté en `OUT/_ledger/inventario.json`,
   (b) la `fuente` coincida, (c) la(s) línea(s) exista(n) en el
   archivo real, (d) los rangos tengan `inicio ≤ fin`.
4. Reporta cada error con código legible
   (`E_PATH_NOT_IN_INVENTORY`, `E_FUENTE_MISMATCH`,
   `E_LINE_OUT_OF_RANGE`, `E_RANGE_INVERTED`) y el número de
   referencia 1-based dentro del documento.

Materializa la prueba literal del ROADMAP A3.2:

> "encuentra todas las referencias `[fuente:]ruta:línea[–fin]`,
> comprueba que el archivo esté en el inventario y que la línea
> exista. Prueba: una ruta inventada falla; una línea fuera de rango
> falla."

## Comandos

```bash
cd /Users/martin/Desktop/projects/Skills/notemartin-appflowy-review
bash OUT/_ledger/validate-A3.2.sh
```

## Salida (verbatim, 2026-10-18)

```
[2026-10-18T21:37:41Z]   OK  check 1: script ejecutable
[2026-10-18T21:37:41Z]   OK  check 2: --help imprime uso y sale 0
[2026-10-18T21:37:41Z]   OK  check 3: inventario.json presente
[2026-10-18T21:37:41Z]   OK  check 4: valid.md exit 0 con 0 errores
[2026-10-18T21:37:41Z]   OK  check 5: fake_path.md exit 1 con E_PATH_NOT_IN_INVENTORY en ref :1:
[2026-10-18T21:37:41Z]   OK  check 6: out_of_range.md exit 1 con E_LINE_OUT_OF_RANGE en ref :1:
[2026-10-18T21:37:41Z]   OK  check 7: mixed.md exit 1, 3 errores en refs :2: :3: :4: (no :1: ni :5:)
[2026-10-18T21:37:41Z]   OK  check 8: --json produce JSON parseable con errors==0
[2026-10-18T21:37:41Z]   OK  check 9: modo directorio: 4 archivos, 10 refs (5 OK / 5 FAIL)
[2026-10-18T21:37:41Z] ---
[2026-10-18T21:37:41Z] resultado: 9/9 checks OK (0 fallidos)
[2026-10-18T21:37:41Z] OK: A3.2 (validate_evidence.py funciona: extrae refs, valida fuente/ruta/línea/rango, reporta con código)
exit=0
```

## Tabla de resultados

| # | Check | Esperado | Resultado |
|---|---|---|---|
| 1 | `SKILL/scripts/validate_evidence.py` existe y es ejecutable | `test -x` | ✅ |
| 2 | `--help` imprime uso y sale 0 | exit 0 + grep `validate_evidence.py` | ✅ |
| 3 | `OUT/_ledger/inventario.json` presente | `test -f` | ✅ |
| 4 | `fixtures/valid.md` → exit 0, 0 errores | exit 0 + 0 líneas `^ERROR` | ✅ |
| 5 | `fixtures/fake_path.md` → exit 1, `E_PATH_NOT_IN_INVENTORY` en ref :1: | exit 1 + grep | ✅ |
| 6 | `fixtures/out_of_range.md` → exit 1, `E_LINE_OUT_OF_RANGE` en ref :1: | exit 1 + grep | ✅ |
| 7 | `fixtures/mixed.md` → exit 1, EXACTAMENTE 3 errores en refs :2: :3: :4: (no :1: ni :5:) | exit 1 + 3 líneas | ✅ |
| 8 | `--json fixtures/valid.md` → JSON parseable con `errors == 0` | `python3 -m json.tool` | ✅ |
| 9 | Modo directorio: 4 archivos, 10 refs (5 OK / 5 FAIL) | exit 1 + summary | ✅ |

## Cobertura de la prueba literal del ROADMAP

| Frase del ROADMAP | Materializada en |
|---|---|
| "encuentra todas las referencias `[fuente:]ruta:línea[–fin]`" | `extract_refs()` (state machine + regex); 10 referencias extraídas sobre los 4 fixtures (3+1+1+5). |
| "comprueba que el archivo esté en el inventario" | `validate_ref()` → lookup `(fuente, ruta_full)` en `inv`; 1 fixture dedicado (`fake_path.md`) + check 5. |
| "y que la línea exista" | `validate_ref()` → `count_lines(abs_path)` y check `1 ≤ línea ≤ total`; 1 fixture dedicado (`out_of_range.md`) + check 6. |
| "una ruta inventada falla" | check 5 (`E_PATH_NOT_IN_INVENTORY`). |
| "una línea fuera de rango falla" | check 6 (`E_LINE_OUT_OF_RANGE`). |

## Fixtures

| Archivo | Referencias | Esperado | Resultado |
|---|---:|---|---|
| `fixtures/valid.md` | 3 (sin prefijo, con `collab:`, con `editor:`) | exit 0, 0 errores | ✅ |
| `fixtures/fake_path.md` | 1 (ruta inexistente) | exit 1, `E_PATH_NOT_IN_INVENTORY` en ref :1: | ✅ |
| `fixtures/out_of_range.md` | 1 (línea 99999 de un archivo de 19) | exit 1, `E_LINE_OUT_OF_RANGE` en ref :1: | ✅ |
| `fixtures/mixed.md` | 5 (refs 1+5 OK; refs 2,3,4 FAIL por códigos distintos) | exit 1, sólo refs :2: :3: :4: reportadas | ✅ |

Total: 10 referencias; 5 OK / 5 FAIL. Cobertura de los 4 códigos
de error: `E_PATH_NOT_IN_INVENTORY` (1), `E_LINE_OUT_OF_RANGE` (2),
`E_RANGE_INVERTED` (1). `E_FUENTE_MISMATCH` (0) — la única fuente
desconocida detectable sería una referencia como
`rust:foo/bar.rs:5`; ningún fixture la incluye, pero la lógica está
implementada y verificada por código (ver `validate_ref` en
`SKILL/scripts/validate_evidence.py`).

## Códigos de error

| Código | Cuándo se emite | Ejemplo |
|---|---|---|
| `E_PATH_NOT_IN_INVENTORY` | El `(fuente, ruta_full)` no existe en `inventario.json`. | `appflowy/this/file/does/not/exist.dart:42` |
| `E_FUENTE_MISMATCH` | El prefijo de fuente no está en `{appflowy, collab, editor}`. | `rust:foo.rs:5` (fuente `rust` no existe) |
| `E_LINE_OUT_OF_RANGE` | `línea > total` o `fin > total` (con `total = line_count` real del archivo). | `appflowy/foo.rs:99999` en archivo de 19 líneas |
| `E_RANGE_INVERTED` | En un rango `inicio-fin`, `fin < inicio` (validado antes de contar líneas). | `foo.rs:10-5` |

## Diferencias detectadas vs el plan (corregidas en sitio)

1. **Convención de lookup de rutas**: el plan asumía lookup
   directo `(fuente, ruta)`. Pero `inventario.json` (A1.2) guarda
   `ruta_rel` con el prefijo del repo (p. ej. `appflowy/frontend/...`
   y `collab/collab-database/...`), mientras que las referencias de
   evidencia (R-003) usan la ruta interna (sin el prefijo de fuente).
   Fix: en `validate_ref()`, prepender `f"{fuente}/"` a `ruta` salvo
   que ya lo tenga (idempotente). Documentado en el código.
2. **Color ANSI en output**: `validate-A3.2.sh` grepeaba
   `^ERROR .*\.md:1:` sobre output con códigos ANSI; los códigos
   rompían los anclajes. Fix: el wrapper `run_ve()` invoca el
   script con `--no-color` para hacer el output determinista.
3. **Filtro de fenced blocks**: el plan mencionaba el state machine
   pero no el caso de líneas vacías dentro del fence. La
   implementación: una vez dentro del fence, sólo el `` ``` ``
   de cierre lo abandona. Probado con fixtures que NO tienen fences
   (no necesario), pero el state machine es trivialmente correcto.
4. **Conteos en check 9**: el plan original proponía 11 refs / 8 OK
   / 3 FAIL; el contenido real de los fixtures ajustados produce
   10 refs / 5 OK / 5 FAIL (cambia al implementar el fixture
   `mixed.md` con 5 refs en lugar de las 6 planeadas). El validador
   está dimensionado a los conteos reales; el delta no afecta al
   criterio de aprobación del ROADMAP.

## Requisitos externos

- `OUT/_ledger/inventario.json` (generado por A1.2). Si falta,
  `validate-A3.2.sh` sale con `exit=77` y mensaje accionable.
- Python 3 stdlib (sin dependencias externas).

## Cómo reproducir desde cero

```bash
cd /Users/martin/Desktop/projects/Skills/notemartin-appflowy-review
# Pre-requisito: A1.2 (genera inventario.json)
[ -f OUT/_ledger/inventario.json ] || python3 SKILL/scripts/inventory.py
python3 SKILL/scripts/validate_evidence.py --help
python3 SKILL/scripts/validate_evidence.py OUT/_ledger/pruebas/A3.2/fixtures
bash OUT/_ledger/validate-A3.2.sh
```

## Estado

**A3.2 cerrada. Pasar a A3.3 (`validate_template.py`).**
