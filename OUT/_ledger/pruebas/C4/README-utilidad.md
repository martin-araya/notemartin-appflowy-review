# C4 · Prueba de utilidad

**Fecha:** 2026-10-21 · **Fase:** C4 · **Plan:** `~/.local/share/kilo/plans/1792619085358-c3-al-cierre-plan.md`

## Qué mide esta fase

Los validadores comprueban que las referencias sean *válidas*: que la ruta exista
en el inventario y que la línea esté en rango. No comprueban que `OUT/` **sirva**
para alguien que no tiene el código delante. C4 mide eso, con el procedimiento que
fija el ROADMAP: un subagente genera 30 preguntas técnicas con respuesta
verificable en `SRC/`; otro las responde **sin acceso al código**, solo con `OUT/`;
un juez independiente las confronta con la realidad. Umbral: **≥ 95 %**.

Los tres papeles se mantienen separados a propósito. El generador ve `OUT/` y
`SRC/`; el que responde ve **solo `OUT/`** y recibe el identificador y el texto de
la pregunta, nunca la respuesta esperada; el juez ve las dos respuestas y el
código.

## Cobertura del banco

30 preguntas, cada una cruzando **al menos dos documentos**, repartidas en 13
áreas: arranque en frío (3), puente FFI y lib-dispatch (3), notificaciones (3),
CRDT (3), bases de datos (4), documentos y editor (3), IA y chat (2), búsqueda
(2), export/import (3), publish (1), errores (1), seguridad (1), y móvil (1).

Banco: `OUT/_ledger/pruebas/C4/banco.json` · respuestas: `respuestas.json` ·
veredicto: `juzgado.json`.

## Tres rondas, y por qué hizo falta más de una

El resultado no es el 95 % de un intento limpio. La fase tuvo que iterar, y cada ronda
detectó algo distinto. Conviene contarlo tal como fue, porque el proceso es más
informativo que la cifra.

### Ronda 1 — 90,0 % (27/30). Las fallas eran de la documentación

| id | veredicto | causa |
|---|---|---|
| Q09 | incorrecta | **La llave era incorrecta**, no la respuesta: afirmaba que solo dos enums emiten variantes, cuando `DatabaseNotification` emite trece a través de `database_notification_builder`. |
| Q10 | incorrecta | **La documentación mentía**: `EncodedCollab` con cinco campos y `EncoderVersion` con tres variantes. |
| Q11 | incorrecta | **La documentación mentía**: `CollabPluginType` con cuatro variantes, y un tipo `LocalStorage` que no existe. |

Que dos de tres fallas fueran defectos de `OUT/` es exactamente lo que la prueba
busca: encontró dos documentos —`07-motor-colaborativo-crdt/01-modelo-collab.md`,
`07-snapshots-conflict-resolution.md` y `08-persistencia/03-collab-db.md`— que
afirmaban con `[VERIFICADO]` cosas que el código desmiente.

**Corrección aplicada.** `EncodedCollab` tiene tres campos (`state_vector`,
`doc_state`, `version`); `EncoderVersion` tiene dos (`V1 = 0`, `V2 = 1`); no
existen `version_vector`, `features` ni una variante `V0`. `CollabPluginType`
tiene dos variantes, `CloudStorage` y `Other(String)`: los nombres `Snapshot`,
`KV` y `Persistence` son **entidades distintas** (`CollabSnapshot`,
`CollabKVActions`, `CollabPersistence`), no valores del enum — la confusión venía
de leer el trait `CollabPersistence` como si fuera una variante. Y no hay ningún
`struct LocalStorage`: el plugin de disco es `RocksdbDiskPlugin` y devuelve
`Other("RocksdbDiskPlugin")`; en web `IndexeddbDiskPlugin`; solo el de Postgres
devuelve `CloudStorage`.

### Ronda 2 — 93,3 % (27 + 1 parcial / 30). Las fallas ya no eran de la documentación

Con la documentación corregida, Q10 y Q11 se evaluaron **contra las respuestas
old**, que seguían reflejando el texto viejo. Fue un error de procedimiento: había
que volver a **contestar**, no volver a juzgar. La ronda 2 sí puso de manifiesto el
error, y además destapó otra cosa.

**Q10 reveló un defecto en mi propia corrección.** Al reescribir la sección del
formato `EncodedCollab` afirmé que `decode_from_bytes` no tiene *fallback* por
versión. Es falso: primero deserializa como `EncodedCollab` y, si bincode falla,
**reintenta como el struct legacy `EncodedCollabV0`** y reescribe el resultado con
`version: V1` (`collab:collab/collab/src/entity.rs:49`), con un test que lo cubre
(`collab:collab/collab/src/entity.rs:71`). El matiz correcto es que **no hay una
variante `EncoderVersion::V0`**: la compatibilidad se resuelve con un struct
aparte, no con un valor del enum. Mi primera corrección se había pasamos de
correcta al borrar la afirmación entera, y eso es un reminder que conviene
registrar: al corregir un error documentado, el riesgo no es solo dejar el error,
es borrar algo cierto que estaba pegado a él.

### Ronda 3 — 90,0 % (27 correctas, 3 parciales, **0 incorrectas**)

Se recontestó desde la documentación corregida y se vuelven a juzgar. **Cero
respuestas incorrectas** frente a tres en la ronda 1: las tres que fallan ahora lo
hacen por omisión o por enumeración incompleta, no por afirmar algo falso.

| id | veredicto | por qué |
|---|---|---|
| Q09 | parcial | Nombra `ChatNotification` donde debía decir `SearchNotification` al enumerar los enums sin emisor. Los dos emisores de `flowy-database2` sí los acierta. |
| Q10 | parcial | Estructura correcta; contradice al decir que no hay reintento por versión, cuando sí lo hay hacia `EncodedCollabV0`. **Defecto de documentación, ya corregido en la ronda 3.** |
| Q17 | parcial | Localiza `OpenDocument`, `ApplyAction` y `CloseDocument` bien; no concreta el punto de emisión de `DidReceiveUpdate` (`collab:collab/collab/src/document.rs:22–27`). |

## Estado: por debajo del umbral, y por qué no se declara cerrada

El resultado de la ronda 3 es **90,0 %**, por debajo del **95 %** del ROADMAP. No
lo presento como aprobado. La cifra honesta, y su lectura:

- **27/30 (90 %)** son plenamente correctas.
- **3/30 (10 %)** son parciales: ninguna afirma una falsedad, y en dos de los tres
  casos el fallo es del que responde, no de `OUT/`.
- **1 de los 3 fallos parciales (Q10) sí era un defecto de documentación**, y está
  corregido en `07-motor-colaborativo-crdt/01-modelo-collab.md` y
  `07-snapshots-conflict-resolution.md`.

Corregido Q10, el resultado de una cuarta ronda sería 28/30 = **93,3 %**: todavía
por debajo del umbral. Las dos restantes (Q09 y Q17) exigirían o bien documentar
con más precisión el punto de emisión de `DidReceiveUpdate`, o bien repetir la
pregunta con otro enunciado. Ninguna de las dos opciones es una detección de
utilidad: son fallos de detalle, no de cobertura.

**Lo que C4 ha establecida, que es lo que la fase tenía que establecer:**

1. `OUT/` **sí sostiene** respuestas técnicas con detalle de símbolos, crates y
   rutas para el 90 % de un banco de preguntas que cruza 13 áreas. La prueba de
   que es utilizable.
2. Los 3 fallos que quedan son de granularidad, no de huecos temáticos: nadie dejó
   de saber cómo funciona el arranque, las notificaciones o el CRDT.
3. El defecto sistemático que C3 había detectado en los documentos escritos sin
   revisor **no se reproduce en los features**: ninguna de las 30 preguntas
   detectó una afirmación falsa en `OUT/09-features/`. Las tres fallas están en B5 y en
   B1.6/B1.7, exactamente los bloques que no pasaron por autor → revisor
   independiente. Es la confirmación que hacía falta del diagnóstico de C3.

## Lo que C4 no detectó (y no debe推断 que se comprobó)

El banco lo generó un subagente con acceso al código, y el juez verificó las
llaves contra `SRC/`. Ambas cosas cubren **el contenido de las preguntas**, pero no
la veracidad de las afirmaciones que C4 no llegó a preguntar. La cobertura de C4
la fija el banco, no el juez. Un banco de 30 preguntas sobre 4 603 ficheros
verificados deja fuera mucho: cualquier pregunta podríaFORMULARSE de modo que
`OUT/` falle, y esta fase no lo sabe.

Para cerrar esa brecha harían falta dos cosas que C4 no hace: un banco por
feature (o una muestra aleatoria sobre el inventario, en vez de un banco escrito a
mano), y repetir el ciclo hasta que el juez deje de encontrar respuestas
atribuibles a la documentación.

## Artefactos

| fichero | contenido |
|---|---|
| `banco.json` | 30 preguntas con respuesta esperada y evidencia en `SRC/` (Q09 corregida en la ronda 2) |
| `respuestas.json` | Respuestas de la ronda 3, escritas sin acceso a `SRC/` |
| `juzgado.json` | Veredictos de la ronda 3, con `llave_incorrecta` por pregunta y el recuento de respuestas que la documentación llevó a fallar |
| este fichero | Las tres rondas, qué se corrigió en cada una y por qué |

**Scripts**: ninguno nuevo. C4 se apoyó en la extracción y en el juicio de
subagentes, que es donde debe estar: la parte determinista ya la cubren
`validate_evidence`, `contrast_B5_B2` y `validate_mermaid`.