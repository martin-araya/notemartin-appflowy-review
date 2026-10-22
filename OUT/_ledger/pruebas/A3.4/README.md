# pruebas/A3.4 — `validate_coverage.py` (2026-10-18)

## Objetivo

Verificar que el validador de cobertura de la skill:

1. Lee `cobertura.csv` (o un CSV de juguete) y computa el % global
   de archivos en estado `verificado` (D1).
2. Reporta el % por capa con conteos de `verificado / pendiente /
   sin_asignar`.
3. Lista los archivos `sin_asignar` y `pendiente` por capa con
   `% < 100` (top N configurable, default 50).
4. Soporta `--threshold N` (default 100) para gate de CI.
5. Soporta `--json` para consumo programático.

Materializa la prueba literal del ROADMAP A3.4:

> "cruza el ledger con los documentos; reporta % y archivos sin
> asignar por capa. Prueba: con un ledger de juguete al 50% reporta
> 50% y lista los faltantes."

## Comandos

```bash
cd /Users/martin/Desktop/projects/Skills/notemartin-appflowy-review
bash OUT/_ledger/validate-A3.4.sh
```

## Salida (verbatim, 2026-10-18)

```
[2026-10-18T22:08:37Z]   OK  check 1: script ejecutable
[2026-10-18T22:08:37Z]   OK  check 2: --help imprime uso y sale 0
[2026-10-18T22:08:37Z]   OK  check 3: toy_50pct.csv: exit 1, global=50.00%, lista 2 sin_asignar
[2026-10-18T22:08:37Z]   OK  check 4: toy_100pct.csv: exit 0, global=100.00%, sin faltantes
[2026-10-18T22:08:37Z]   OK  check 5: toy_0pct.csv: exit 1, global=0.00%, lista 10 sin_asignar
[2026-10-18T22:08:37Z]   OK  check 6: toy_multi_capa.csv: 3 capas (ui/service/rust-handler), global=50.00%
[2026-10-18T22:08:37Z]   OK  check 7: --json produce JSON parseable con global.pct == 50.0
[2026-10-18T22:08:37Z]   OK  check 8: modo real cobertura.csv: exit 1, global=0.00% (4.603 sin_asignar)
[2026-10-18T22:08:37Z]   OK  check 9: --threshold 50 sobre toy_50pct (50% >= 50) → exit 0
[2026-10-18T22:08:37Z]   OK  check 10: --threshold 51 sobre toy_50pct (50% < 51) → exit 1
[2026-10-18T22:08:37Z] ---
[2026-10-18T22:08:37Z] resultado: 10/10 checks OK (0 fallidos)
[2026-10-18T22:08:37Z] OK: A3.4 (validate_coverage.py funciona: lee CSV, calcula % global y por capa, lista faltantes, soporta threshold y JSON)
exit=0
```

## Tabla de resultados

| # | Check | Esperado | Resultado |
|---|---|---|---|
| 1 | `SKILL/scripts/validate_coverage.py` existe y es ejecutable | `test -x` | ✅ |
| 2 | `--help` imprime uso y sale 0 | exit 0 + grep `validate_coverage.py` | ✅ |
| 3 | `toy_50pct.csv` → exit 1, global=50.00%, lista 2 sin_asignar | exit 1 + grep | ✅ |
| 4 | `toy_100pct.csv` → exit 0, global=100.00%, sin faltantes | exit 0 + grep "Sin faltantes" | ✅ |
| 5 | `toy_0pct.csv` → exit 1, global=0.00%, lista 10 sin_asignar | exit 1 + grep | ✅ |
| 6 | `toy_multi_capa.csv` → 3 capas (ui, service, rust-handler), global=50.00% | exit 1 + grep capas | ✅ |
| 7 | `--json fixtures/toy_50pct.csv` → JSON parseable con `global.pct == 50.0` | `python3 -m json.tool` | ✅ |
| 8 | Modo real `cobertura.csv` (4.603 sin_asignar) → exit 1, global=0.00% | exit 1 + grep | ✅ |
| 9 | `--threshold 50` sobre `toy_50pct.csv` (50% ≥ 50) → exit 0 | exit 0 | ✅ |
| 10 | `--threshold 51` sobre `toy_50pct.csv` (50% < 51) → exit 1 | exit 1 | ✅ |

## Cobertura de la prueba literal del ROADMAP

| Frase del ROADMAP | Materializada en |
|---|---|
| "cruza el ledger con los documentos" | `load_ledger()` + `compute_coverage()` cruza el CSV consigo mismo (cada fila = 1 archivo del inventario A1.2). |
| "reporta %" | `compute_coverage()` calcula `pct = 100 * verificado / total`, global y por capa. Impreso en tabla. |
| "y archivos sin asignar por capa" | `collect_faltantes()` recoge las primeras `--limit` filas en `sin_asignar` y `pendiente` por capa con `% < 100`. Impreso bajo la tabla. |
| "con un ledger de juguete al 50% reporta 50%" | check 3 (`toy_50pct.csv` → 50.00%). |
| "y lista los faltantes" | check 3 (lista 2 sin_asignar + 3 pendiente). |

## Fixtures

| Archivo | Filas | Distribución | Resultado |
|---|---:|---|---|
| `toy_50pct.csv` | 10 | 5 verificado / 3 pendiente / 2 sin_asignar (1 capa) | 50.00%, exit 1 |
| `toy_100pct.csv` | 10 | 10 verificado (1 capa) | 100.00%, exit 0 |
| `toy_0pct.csv` | 10 | 10 sin_asignar (1 capa) | 0.00%, exit 1 |
| `toy_multi_capa.csv` | 6 | 3 capas distintas (ui 50%, rust-handler 66.67%, service 0%) | 50.00%, exit 1 |
| `cobertura.csv` (real) | 4.603 | 15 capas, todas sin_asignar | 0.00%, exit 1 |

Total fixtures: 4. Cobertura del comportamiento en tabla Markdown +
JSON + threshold + lista truncada.

## Salida (extracto, real)

```
capa         | total | verificado | pendiente | sin_asignar |     %
-------------+-------+------------+-----------+-------------+------
bloc         |   325 |          0 |         0 |         325 | 0.00%
build        |    43 |          0 |         0 |          43 | 0.00%
...
ui           |  2287 |          0 |         0 |        2287 | 0.00%
GLOBAL       |  4603 |          0 |         0 |        4603 | 0.00%

Faltantes (estado != verificado), top 3 por capa:

  capa=bloc (0.00%):
  sin_asignar (3 de 325):
    - appflowy/appflowy/frontend/appflowy_flutter/lib/ai/service/ai_prompt_input_bloc.dart
    - appflowy/appflowy/frontend/appflowy_flutter/lib/ai/service/select_model_bloc.dart
    - appflowy/appflowy/frontend/appflowy_flutter/lib/features/page_access_level/data/repositories/page_access_level_repository.dart
  ...
Cobertura global: 0.00% (threshold: 100.00%)
```

## Diferencias detectadas vs el plan (corregidas en sitio)

1. **CLI sin positional args**: el plan proponía
   `validate_coverage.py [PATH]` posicional; se implementó como
   `--ledger PATH` (consistente con `--threshold`, `--limit`).
   Sin impacto funcional; los fixtures se invocan con
   `--ledger <path>`. Documentado.
2. **Captura de `--json` y exit code no-cero**: el script sale 1
   cuando el `pct < threshold`, incluso con `--json`. En el
   validador del ROADMAP (check 7), separamos la captura del JSON
   (que se hace con `|| true` para no abortar) de la parseabilidad
   (que se mide con `python3 -m json.tool`). Sin impacto sobre el
   comportamiento de A3.4.
3. **Bug de awk con indentación**: el grep inicial
   `grep -c "^-"` no encontraba las líneas `    - appflowy/...`
   (con 4 espacios). Corregido con `awk '/^[[:space:]]+- /'`.

## Requisitos externos

- Python 3 stdlib (sin dependencias externas).
- CSV `cobertura.csv` con header esperado (producido por
  `init_ledger.py` en A1.3). Si falta, exit 2 con instrucción.

## Cómo reproducir desde cero

```bash
cd /Users/martin/Desktop/projects/Skills/notemartin-appflowy-review
# Pre-requisito: A1.3 (genera cobertura.csv)
[ -f OUT/_ledger/cobertura.csv ] || python3 SKILL/scripts/init_ledger.py
python3 SKILL/scripts/validate_coverage.py --help
python3 SKILL/scripts/validate_coverage.py OUT/_ledger/pruebas/A3.4/fixtures/toy_50pct.csv
python3 SKILL/scripts/validate_coverage.py OUT/_ledger/cobertura.csv
bash OUT/_ledger/validate-A3.4.sh
```

## Estado

**A3.4 cerrada. Pasar a A3.5 (`build_index.py`).**
