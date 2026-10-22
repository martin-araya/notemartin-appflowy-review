# C3 · Preparación — huérfanos del ledger resueltos (T0)

**Fecha:** 2026-10-21 · **Fase:** C3 · **Prerrequisito bloqueante**

## Qué anunciaba `resume-plan.md`

3 documentos de F02 marcados como huérfanos, con ids inferidos del nombre de archivo:

| Doc | id inferido |
|---|---|
| `09-features/F02-bases-de-datos/15-cierre-f02-bateria-de-tests-de-flowy-database2-tests-database.md` | `F15` |
| `09-features/F02-bases-de-datos/12-tab-bar-de-vistas-sync-de-database-snapshots.md` | `F12` |
| `09-features/F02-bases-de-datos/13-cierre-f02-raiz-de-flowy-database2-event-map-event-handler-manager-notification-.md` | `F13` |

## Hallazgo: los tres no eran huérfanos, y el cuarto sí lo era

`scan_orphan_docs()` en `SKILL/scripts/resume.py` infería el `unit_id` del
**nombre del archivo** con `PARTIAL_UNIT_RE = ^(F?\d{2}(?:\.\d+)?)-`. Dentro de
`F02-bases-de-datos/` la convención `12-tab-bar-…md` codifica el **sub-índice**
(12), no el id completo (`F02.12`), así que los tres documentos se comparaban
contra `F12`/`F13`/`F15` en vez de contra `F02.12`/`F02.13`/`F02.15` y salían
como huérfanos pese a que sus unidades existen en `units/_index.json` y los
apuntan (`documento:` correcto en los tres).

Los ids reales se leen del frontmatter:

```
F02.12 → units/F02.12.json  →  7 archivos  (documento: …/12-tab-bar-…md)
F02.13 → units/F02.13.json  → 14 archivos  (documento: …/13-cierre-f02-raiz-…md)
F02.15 → units/F02.15.json  → 51 archivos  (documento: …/15-cierre-f02-bateria-…md)
```

Al corregir la lectura del id aparecieron **cero** huérfanos para esos tres, pero
**uno nuevo** que el bug anterior tapaba por completo:

| Doc | id de frontmatter | ¿Existe la unidad? |
|---|---|---|
| `09-features/F02-bases-de-datos/0.1.3-database-tests.md` | `F02.0.1.3` | **No** |

Es un documento de **scope-correction** (`archivos_cubiertos: []`,
`archivos_total: 0`) que cierra formalmente la ausencia de las carpetas
`plugins/database/*_test*/` y de `plugins/database/mock_data/`: ninguna existe
como sub-carpeta física en `SRC/appflowy/frontend/appflowy_flutter/lib/plugins/database/`;
los tests Dart viven en `appflowy_flutter/test/` y los Rust inline en
`flowy-database2/src/services/**/mod.rs`. Su propio §1 remite a
`OUT/_ledger/units/F02.0.1.3.json` como fichero esperado, y
`units/F02.0.1.0.json` lo declara como sub-unidad en `dependencias[]` — pero el
fichero nunca se emitió. Es el mismo patrón de fuga que corrigió el cierre de B3
con `F02.13/14/15`, aquí en el sub-árbol `F02.0.1`.

## Correcciones aplicadas

### 1. `SKILL/scripts/resume.py` — el id se lee del frontmatter

Nueva función `read_frontmatter_id(path)` (líneas 187–203) que parsea el campo
`id:` del bloque YAML. `scan_orphan_docs()` la usa como fuente de verdad y solo
cae al nombre del archivo cuando el doc no tiene frontmatter legible
(`origin` se propaga al motivo reportado, de modo que un huérfano se puede
auditar sin abrir el fichero).

Además, un doc cuyo `id` sea un `feature_id` conocido del ledger (`F02`, `F00`,
…) se filtra: no es una unidad, es un documento y no debe contar como huérfano.

```python
if unit_id in valid_unit_ids:
    continue
if unit_id in all_feature_ids:
    continue
```

**Por qué el bug era silencioso**: `F12` es un id de feature *válido* (Folders &
workspaces), así que ni siquiera entraba en la rama de documentar como huérfano
"con id desconocido"; entraba por el nombre y se comparaba contra el conjunto
`valid_unit_ids` (unidades), donde `F12` tampoco existe. Dos conjuntos
desalineados (`feature_ids` del ledger vs `unit_id` de las unidades) y un id
derivado del nombre en lugar del frontmatter.

### 2. `OUT/_ledger/units/F02.0.1.3.json` — nuevo fichero de unidad (0 archivos)

Espeja la forma de `F02.0.1.0.json` (unidad índice sister, también 0 archivos) y
de `F02.0.2.3.json` (gemela de collab-side con 39 archivos):

- `feature_id: F02`, `sub_index: 3`, `titulo: "Database tests (scope-correction cerrada)"`.
- `archivos: []`, `archivos_total: 0`, `metricas.scope_correction: true`.
- `dependencias: [{id: F02.0.1.0, relacion: indice}]`.
- `documento: OUT/09-features/F02-bases-de-datos/0.1.3-database-tests.md`.
- `prioridad: 3`, `concurrencia: paralela` (mismo nivel que su gemela `F02.0.2.3`).

No se toca `cobertura.csv`: una unidad de 0 archivos no tiene filas que marcar, y
las 4 603 filas siguen en `verificado` (`verificado_por=revisor_C1`).

### 3. `OUT/_ledger/units/_index.json` — entrada registrada

Añadida `F02.0.1.3` (`total_unidades` 124 → 125), reordenada por
`(prioridad, id)` como el resto del índice.

### 4. `OUT/_ledger/validate-A4.2.sh` — expectativa `N_REAL` obsoleta

El check 3 seguía esperando **143** ficheros de unidad, una cifra de antes de
B4/B5/B6. El recuento real es **164**, que se descompone en 125 unidades de
feature (`F*`) + 5 transversales `B1.*` + 14 del motor `B4.*` + 14 de
secuencias `B5.*` + 6 de transversales `B6.*`. La suite estaba **fallando desde
el cierre de B4** y `validate-C1.sh` no la incluye, así que C1 no podía verla.

Se actualizó el literal **y** el bloque de comentario, que ahora documenta la
evolución del número en vez de describir solo el estado de B3.

## Resultado

```
[validate_units]            OK   (125 unidades F* + B*; 4603 = 4603, 0 solapamiento)
[validate-A4.2.sh]          OK   (check 3: 125 unidades, suma 4603 = filas asignadas)
[validate-A4.4.sh]          OK   (fixture 134v/2if + real: huerfanos=0)
[resume.py --json]          huerfanos: 0   asignados=4603  verificados=4603  pendientes=0
```

`resume-plan.md` regenerado con `Huérfanas: (ninguna)`.

## Consecuencia para C3

`unidades_huerfanas` era el único término del `Stats` que quedaba en rojo al
cerrar C1, y era un artefacto del propio orquestador, no de los documentos.
Con T0 cerrado, el único trabajo real que queda es la consistencia de contenido
entre documentos (T1.1–T1.3), que es exactamente lo que es exactamente lo que C3 define como revisión cruzada.

## Nota sobre la definición de "huérfano"

El criterio pasa a ser: **un `.md` bajo `OUT/09-features/` cuyo `id:` de
frontmatter no resuelva ni a una unidad de `units/_index.json` ni a un
`feature_id` de `cobertura.csv`**. Ni el nombre del archivo ni el sub-índice
numérico intervienen. Esto no cambia lo que C3 audita (los documentos B5 bajo
`OUT/15-secuencias-globales/` no entran en `DOCS_ROOT_DEFAULT`, que sigue siendo
`OUT/09-features/`), pero fija el criterio para cualquier barrido futuro.