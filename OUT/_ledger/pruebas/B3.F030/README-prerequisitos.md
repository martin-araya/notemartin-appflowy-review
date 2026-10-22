# B3.F030 — Prerrequisitos de skill para el cierre de B3.F03..F07

Este directorio contiene las reparaciones de la skill que Execute el plan
`~/.local/share/kilo/plans/1792504481368-b3-f03-f07-cierre-plan.md` §0 (Fase 0,
bloqueante). Sin ellas no era posible cerrar ninguna de las 5 features.

## Problemas encontrados y reparados

### 1. `validate_units.py` crasheaba con las unidades B1.x

`units/B1.{3..7}.json` usan otro esquema: su campo `archivos` es una lista de
**documentos de `OUT/`**, no de ficheros de `SRC/`. `check_inventario()` hacía
`f.get(...)` sobre `str` → `AttributeError`. Reparado saltándose las unidades
cuyo `id` empieza por `B`, igual que ya hacía `validate-A4.2.sh` Check 3.

### 2. Doble propiedad de 425 rutas por units padre obsoletas

`build_units.py` recrea `F02.0.1.json` y `F02.0.2.json` (los padres) cada vez
que corre, mientras sus hijos `F02.0.1.{0..3}` y `F02.0.2.{0..3}` fueron creados
a mano por `split_F0201.py` / `split_F0202.py`. Resultado: 425 rutas con dos
propietarios. Las dos unidades padre se purgaron (copia en `units/.stale-bak/`).

### 3. 135 filas asignadas sin unidad

- **114 de F02**: raíz de `flowy-database2` (`Cargo.toml`, `Flowy.toml`, `build.rs`,
  `src/{lib,event_handler,event_map,manager,notification,template}.rs`,
  `src/services/{mod,setting/*}`, `src/utils/*`), `src/entities/**` (49) y
  `tests/**` (51). Reancladas según la atribución del ROADMAP: entidades →
  `F02.0.1.1`, tests → `F02.0.1.3`, raíz → `F02.0.1.2`.
- **21 de F08**: al cerrarse el piloto A5.1 sus filas pasaron a `verificado`, y
  `build_units.py` (que solo lee filas `pendiente`) dejó de emitirlas.
  Recuperadas en `units/F08.json`.

### 4. 51 rutas Dart en dos unidades F02

`F02.{1,2,3,7,8,12}.json` reclamaban los blocs Dart de `application/{cell,field,
row,calculations}` que el ROADMAP atribuye a **F02.0.1.2**. Cedidas.

### 5. `generado_en` ausente en 3 unidades índice

`F01.6.0`, `F02.0.1.0`, `F02.0.2.0` no lo tenían (campo obligatorio de
`check_schema`). Añadido.

### 6. Invariante del ledger corregido en `validate_units.py`

Antes comparaba `suma(archivos_total)` contra las filas **`pendiente`** de
`cobertura.csv`. En cuanto una sub-fase se cerraba, sus archivos seguían en su
`unit.json` pero pasaban a `verificado`, así que el validador quedaba roto de
forma permanente. Ahora compara contra **todas** las filas asignadas
(`feature_ids` no vacío), que es el invariante real. Se añadió `--estados
{all,pendiente}` para validar builds temporales de `build_units.py` previos al
cierre de sub-fases.

### 7. `record_unit_state.py` no resolví sub-unidades

`cobertura.csv::feature_ids` solo guarda el id de **feature** (`F03`), nunca el
de la sub-unidad (`F03.2`), así que `--unit F03.2 --accion verificar` afectaba
**0 filas**. Ahora, para ids con punto, resuelve el conjunto real de ficheros
desde `OUT/_ledger/units/<id>.json` (nuevo flag `--units-dir`).

### 8. `validate-A4.2.sh` Check 3 era un validador que mutaba el ledger

Regeneraba `OUT/_ledger/units/` con `build_units.py` y solo re-aplicaba 2 de los
5 scripts de split, dejando obsoletas las sub-unidades de F02. Además esperaba
`N_REAL = 106` cuando en disco había 118 ficheros de unidad. Reescrito como
check **de solo lectura** sobre el invariante real (`suma == filas asignadas`,
0 doble propiedad, 0 asignadas sin unidad) **más** un gate de F03..F07 al 100 %
verificado. Los splits por script (`split_F0103/0106/0201/0202/0209`) se aplican
ahora **fuera** del validador; los de F03 y F05 son declarativos
(`SUBDIVISIONS` en `build_units.py`) y sobreviven a la regeneración.

### 9. Parsing de Mermaid en las suites heredadas

`validate_mermaid.sh --quiet` emite `OK=n FAIL=n` (mayúsculas) mientras
`validate_evidence.py --quiet` emite `ok=n` (minúsculas). Se comprobó el formato
real de ambos y se dejaron coherentes las 34 suites `OUT/_ledger/pruebas/B3.F0*/`.

### 10. Suites F01 con `ROOT` calculado a 3 niveles

`OUT/_ledger/pruebas/B3.F01{0..9}/validate-*.sh` usaban
`ROOT="$(cd "$(dirname "$0")/../.." && pwd)"`, que resuelve a `OUT/_ledger/` en
vez de la raíz del proyecto. Corregido a 4 niveles.

### 11. Suite B3.F01.0 con cobertura exacta obsoleta

Exigía exactamente 555 archivos F01 verificados; hoy son 798 porque se cerraron
F01.1..F01.9. Relajado a `>= 555` (el propio ROADMAP ya lo había autorizado para
F01.1).

## Resultado

`validate_units.py` y `validate-A4.2.sh` en verde:

```
[validate_units] unidades=109 archivos=4603 asignados_csv=4603 → OK
  real: 113 unidades, suma=4603 = filas asignadas=4603,
        0 solapamiento, 0 sin unidad, F03..F07 100% verificado  (gate pendiente de cerrar)
```

## Ficheros de este directorio

| Fichero | Qué es |
|---|---|
| `repair_orphan_units.py` | Reparación one-off de los puntos 2–5. Idempotente, con `--dry-run`. |
| `set_unit_docs.py` | Fija las rutas `documento` de F03.x/F05.x y regenera `_index.json` desde el directorio completo. |
| `make_phase_suite.py` | Generador de las 5-check suites (`validate-B3.F0XX.sh`) de todas las fases B3.F03..F07. |
| `validate-A4.2.sh` | Copia del validador de A4.2 tras la reparación (el canónico está en `OUT/_ledger/`). |
| `README-f03.md` | Bitácora de la feature F03 completa (copiada como `README.md` en `B3.F031..F033`). |