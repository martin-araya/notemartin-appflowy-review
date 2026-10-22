---
id: 22-preguntas-abiertas
titulo: Preguntas abiertas y notas de campo
fuente: detectadas durante A0.0–B6.5
archivos_cubiertos: [AGENTS.md, ROADMAP.md, PROMPT.md, OUT/STATE.md]
estado: verificado
---

# 22 — Preguntas abiertas y notas de campo

> Este fichero consolida las preguntas, ambigüedades, suposiciones refutadas
> y notas detectadas durante la ejecución de la skill. Las entradas marcadas
> con **[BLOQUEADOR]** bloquean la fase siguiente hasta resolverse; el resto
> se cerró en **B6.5** (consolidación final del Bloque B, 2026-10-21).
>
> **Estado tras B6.5**: 444 entradas. Ninguna está marcada como `[BLOQUEADOR]`
> activo: el Bloque B queda cerrado y la Parte C (verificación y cierre) puede
> arrancar. Las 8 entradas de prioridad `ALTA` que quedan abiertas están
> recogidas en §B6.5 · Resumen ejecutivo y ninguna impide el arranque de C1.
> Los bloques históricos `## Ax.x · …` se conservan tal cual para no perder
> trazabilidad; las entradas nuevas se numeran a partir de `## B6.x`.

---

## Índice de entradas

| Bloque | Entradas | Naturaleza |
|---|---:|---|
| `A0.x`–`A5.x` | 80 | Notas de construcción de la skill: scripts, validadores, ledger y contratos de subagente. Cerradas. |
| `B3.F00`–`B3.F21` | 316 | Preguntas de las features F* recogidas en el cierre del ledger. Descriptivas. |
| `B4.0`–`B4.13` | 10 | Preguntas del motor de export/import (pérdidas, assets, encoding, round-trip). Descriptivas. |
| `B5.2`–`B5.12` | 6 | Preguntas de las secuencias globales extremo a extremo. Descriptivas. |
| `B6.1` | 15 | Build, CI y distribución: secretos, firma de iOS, supply chain, perfiles de build. |
| `B6.2` | 7 | Testing: quién ejecuta qué, perfiles por plataforma, typos heredados. |
| `B6.3` | 8 | Seguridad: SEC-1 (credencial de invitado), cifrado en reposo, rotación de tokens, IA local. |
| `B6.4` | 1 | Discrepancia de `ID_ALIASES` frente a los ids reales de feature. |
| `B6.5` | 1 | Símbolos citados en `AGENTS.md`/`ROADMAP.md` que no existen en `SRC/`. |
| **Total** | **444** | |

---

## B6.5 · Resumen ejecutivo de la consolidación

Ninguna de las 444 entradas bloquea el cierre del Bloque B. Estas son las que
exigen decisión de un tercero y quedan abiertas a propósito:

| # | Entrada | Por qué sigue abierta |
|---|---|---|
| 1 | `B6.3` **SEC-1** — `BackendAuthService.signUpAsGuest` fija una contraseña constante en el código fuente | Requiere acceso al servidor para saber si esos valores coinciden con una cuenta real de AppFlowy Cloud. La remediación real (rotar la constante y revisar el historial) es fuera de alcance de una documentación. Documentado en `[[B6.3]]` §6.1 con el literal redactado como `<REDACTED>` en **todo** `OUT/`. |
| 2 | `B6.3` — Cifrado en reposo del lado servidor | El repositorio solo contiene el cliente. |
| 3 | `B6.3` — Rotación y revocación de tokens en el servidor | Solo se observa el contrato (`TokenState::Refresh` / `TokenState::Invalid`). |
| 4 | `B6.1` — Contenido y ámbito de los secretos de CI | Los secretos se citan por nombre, nunca por valor. |
| 5 | `B6.1` — Firma y notarización del `.ipa` de iOS | No hay ningún paso en el repositorio que lo haga. |
| 6 | `B6.5` — Símbolos citados en `AGENTS.md`/`ROADMAP.md` que no existen en `SRC/`: `FileCache`, `ChunkedByteUploader`, `FramelessWindow`, `LocalAI`, `HNSW`, `TrackedCollab` | La referencia canónica (`AGENTS.md` §4, `ROADMAP.md`) usa nombres que el código no contiene. `[[B6.5]]` §3 documenta el símbolo real que sustituye a cada uno. Corregir `AGENTS.md` y `ROADMAP.md` es una decisión del propietario de la skill. |
| 7 | `B6.4` — `ID_ALIASES` de `build_index.py` frente a los ids reales de feature | No existe ningún `id: F01` en `OUT/`; los índices maestros declaran `F01.0`, `F02.0.1.0`, etc. `build_index.py` resuelve la distancia con una tabla mantenida a mano, que es frágil. |
| 8 | `B6.2` — `spae_cion_test.dart` parece ser un typo heredado | El nombre se preserva tal cual en el repo; su propósito semántico no está documentado. |

---

## B6.5 · Hallazgo de la pasada global de validadores (P5.1)

Al cerrar B6 se ejecutó la **pasada global** de `validate_evidence.py` sobre
todo `OUT/` — la prueba que la Parte C define como C1. Resultado y remediación:

| Clase | Antes | Después | Qué se hizo |
|---|---:|---:|---|
| Referencias sin prefijo de directorio en `OUT/15-secuencias-globales/` (B5) | 82 errores | 34 | Corrección determinista con `SKILL/scripts/fix_evidence_prefix.py`: se antepone el prefijo solo cuando existe **un único** fichero del inventario cuyo sufijo sea el ruta citado. **No se tocó ningún número de línea.** B5 vuelve a pasar `validate_template` (14/14) y `validate_mermaid` (53/53). |
| Referencias con línea fuera de rango o ruta migrada | (incluidas en las 82) | 34 | **No remediado a propósito.** Exigen decidir referencia por referencia si la línea se movió o la cita era errónea; es trabajo de C1/C3, no de un script determinista. |

> **Actualizado en C1 (2026-10-21).** Este bloque describe el estado de la deuda
> **antes** de la Fase C1. C1 la cerró: 38 citas reapuntadas al símbolo real y 10
> retiradas por inventar fichero o símbolo. Ver `## C1 · Pasada global de
> validadores` al final de este fichero y `OUT/_ledger/pruebas/C1/`.
> Las rutas que se citan aquí se dejan **sin resolver a propósito**: son el
> registro del defecto, no evidencia viva.

Quedaban **34 referencias** en `OUT/15-secuencias-globales/` que `validate_evidence.py`
rechazaba. Dos subcasos, ambos preexistentes a B6:

- **`E_LINE_OUT_OF_RANGE` (7)**: la ruta resuelve pero la línea no existe. Ejemplo
  histórico: `flowy-folder/src/notification.rs`, línea 80, en un fichero de 55
  líneas. O la línea se movió al escribir el documento, o la cita copió una ruta
  homónima de otro crate.
- **`E_PATH_NOT_IN_INVENTORY` (27)**: rutas que ya no existen tras la migración de
  la arquitectura Dart a `features/` (p. ej.
  `workspace/application/app/app_bloc.dart`), más rutas de `collab/` que sólo se
  resuelven con un prefijo adicional y que el script no puede desambiguar
  (29 referencias ambiguas las dejó como están por diseño).

**Nota de método**: el `skip` por defecto de `fix_evidence_prefix.py` excluye
`OUT/_ledger`, `OUT/STATE.md` y `OUT/00-INDEX.md`. Los tres no son entregable:
`_ledger/` es el cuaderno de trabajo, `STATE.md` es el estado entre sesiones y
`00-INDEX.md` lo regenera `build_index.py`.

---

## A0.x · Esqueleto de la skill (2026-10-18)

- **A0.0** — `PROMPT.md` reconstruido derivado de `AGENTS.md` + `ROADMAP.md`,
  marcado al inicio del propio fichero como "consolidar en fase posterior".
  Cualquier contradicción detectada durante la ejecución se anota aquí.
- **A0.2** — `pruebas/A0.2/` solo verificó la carga en Kilo Code (1 de 3
  agentes). La validación en Hermes Agent y Cline queda pendiente de prueba
  manual en cada herramienta.

## A0.4 · Esqueleto de salida (2026-10-18)

- **A0.4-a** — Discrepancia de nombre: el `PROMPT.md §3` lista la feature F04
  como `F04-sidebar-...` (con `...` placeholder); el esqueleto lo materializó
  como `F04-sidebar-favoritos-recientes-papelera-tabs-command-palette/`.
  Resolver en fase de consolidación posterior: o se corrige `PROMPT.md` o se
  documenta como "los `...` son intencionales".

## A1.1 · `fetch_sources.sh` (2026-10-18)

- **A1.1-a** — **Estructura del `Cargo.toml` cambió**: la documentación
  (`AGENTS.md §3`) y el plan asumían que el bloque `git = ..., rev = ...` de
  los crates `collab*` estaba en `[patch.crates-io]`. En el commit
  `5cf3a36` (HEAD actual de AppFlowy) ese bloque está **después** de
  `[patch.crates-io]` como continuación de la misma tabla (sin un nuevo
  `[section]`). El parser de A1.1 lo maneja porque captura hasta el final
  del archivo, pero conviene documentarlo:
  > A partir de cierto commit (≥ ?) los crates `collab*` viven en la
  > tabla que sigue a `[profile.profiling]` (líneas 137+ en
  > `SRC/appflowy/frontend/rust-lib/Cargo.toml`). El primer `[patch.crates-io]`
  > solo parchea `rocksdb`. Los `collab*` están justo después, en una
  > sección comentada pero estructuralmente parte de la misma tabla.

- **A1.1-b** — Los SHAs `4dfccef` (collab) y `470c4e7` (editor) NO están
  en refs anunciadas por `git ls-remote` (ninguna rama, ningún tag), pero
  sí son alcanzables en el historial completo. Por eso `resolve_commit_via_clone`
  hace un clon temporal en `/tmp` y `git checkout <sha>` resuelve por
  historia, no por ref. Si en algún commit futuro AppFlowy cambia a tags
  o ramas, la estrategia de resolución debe revisarse.

- **A1.1-c** — El commit "collab" del `Cargo.toml` es el MISMO rev para
  los 8 crates `collab*` (`collab`, `collab-entity`, `collab-folder`,
  `collab-document`, `collab-database`, `collab-plugins`, `collab-user`,
  `collab-importer`). No hubo que usar la regla de mayoría del plan. Si en
  el futuro divergen, el campo `rev_per_crate` del plan debería añadirse a
  `sources.json` (no implementado en A1.1).

- **A1.1-d** — Editor ref extraído: `470c4e7`. Coincide con la referencia
  documentada en `AGENTS.md §3` ("Referencia usada al diseñar"). Bien.

- **A1.1-e** — AppFlowy cloned shallow: `5cf3a36`. Sin ref explícita
  solicitada por el usuario, el script usa `git clone --depth 1`. Cualquier
  `git log` que requiera histórico estará limitado a este commit. Para
  A1.2 (inventory) no es problema; para B1.1 (estructura del repo)
  podría ser necesario un `git fetch --unshallow` o re-clonar con
  `--appflowy-ref` explícito.

## Próximas preguntas a registrar

- [ ] A1.2 — ¿el inventario debe seguir el subtree `SRC/appflowy` o solo el
  monorepo Flutter+Rust (excluyendo `frontend/{android,ios,linux,macos,
  windows,web}/` que son generadores)?
- [ ] A2.5 — `cargo metadata --no-deps` puede tardar >60 s en un workspace
  con `flowy-codegen`; ¿vale la pena o parseamos `Cargo.toml` directamente?
- [ ] A2.7 — ¿el codegen produce `.proto` versionados en algún sitio, o
  siempre hay que regenerar desde el código Rust?

## A1.2 · `inventory.py` (2026-10-18)

- **A1.2-a** — El árbol de AppFlowy bajo `frontend/appflowy_flutter/lib/`
  tiene 4 estructuras distintas coexistiendo: `plugins/`, `workspace/`,
  `features/` (nueva), y `ai/user/core/shared/startup/mobile/packages/`
  (transversales). Las reglas de capa asignan `bloc` a
  `plugins/*/application/` y `workspace/application/`, pero no
  necesariamente a `user/application/` (donde el matching lo hace por nombre
  `*_bloc.dart`). Verificar en A4.1 que ningún BLoC queda con `capa=ui` o
  `capa=service` por descuido.

- **A1.2-b** — El lenguaje `text` con 435 entradas es alto. Corresponde
  mayoritariamente a `.gitignore`, `.gitattributes`, `.editorconfig`,
  `BUILD.bazel` (no contemplado → cae a `text`), `.metadata`, etc. Se
  acepta como categoría "config misceláneo"; si en B1.1 se necesita
  desglosar, añadir reglas específicas.

- **A1.2-c** — `appflowy/frontend/rust-lib/covtest.rs` aparece como
  archivo de 0 bytes con `capa=rust-handler` (porque la regla 34 lo
  captura). Es un fichero vacío raíz de `frontend/rust-lib/`, posiblemente
  un placeholder o un stub de un crate eliminado. Sin acción; queda
  registrado para B6.2 (testing) por si tiene sentido borrarlo o
  documentarlo.

- **A1.2-d** — La distribución por capa muestra `collab=280` para los
  crates `collab*` del repositorio `SRC/collab`. Esto NO incluye los
  1.025 archivos `.rs` del workspace `appflowy/frontend/rust-lib/` (que
  están clasificados como `rust-handler`, `rust-manager`, `service`, etc.,
  según el crate). Verificar en B1.6 que la documentación de "cómo AppFlowy
  usa `collab`" distingue claramente entre "código del workspace
  `appflowy` que es cliente de `collab`" (rust-handler) y "el crate
  `collab` en sí" (capa=collab).

## A1.3 · Esquema del ledger (2026-10-18)

- **A1.3-a** — `init_ledger.py` **regenera el CSV desde cero** cada vez que
  se ejecuta, leyendo `inventario.json`. Cualquier edición manual (p. ej.
  anotaciones de un revisor humano) o mutación previa (de A4.1) se
  sobrescribirá. Esto es **deseado** en A1.3 (fase "init" puro), pero
  `assign_ledger.py` (A4.1) debe gestionar el versionado: leer el CSV
  actual, mutar las filas asignadas, escribir uno nuevo sin perder
  asignaciones ya hechas. Documentar el contrato de no-destructive-merge
  en el plan de A4.1.

- **A1.3-b** — Encoding UTF-8 **sin BOM**. La mayoría de herramientas
  modernas (Notion, Obsidian, Python `csv`, VS Code, Excel para Mac)
  interpretan correctamente el CSV sin BOM. **Excepción**: Excel para
  Windows en configuraciones regionales con codepage legacy puede mostrar
  acentos rotos. Si en una fase futura se observa el problema, abrir
  `A1.3.x` para escribir con `utf-8-sig` (BOM) — `csv.writer` lo soporta
  cambiando `open(..., encoding='utf-8-sig', ...)`. Por ahora, se
  prioriza la compatibilidad con Notion/Obsidian (consumidores primarios
  de `OUT/`).

- **A1.3-c** — La columna `feature_ids` admite valores como `F01,F08`
  (separados por coma) si un archivo es compartido entre features.
  Decisión de A4.1: ¿se usa esa posibilidad o se garantiza 1:1
  archivo↔feature? Si A4.1 confirma 1:1 estricto, se podría simplificar
  el esquema a una sola columna. Por ahora el esquema actual cubre ambos
  casos; no se cambia.

- **A1.3-d** — El CSV ocupa 513 KB con 4.604 líneas. Para crecer con
  A4.1 (que añadirá `feature_ids` poblados) seguirá en el rango de MB.
  Si A4.2 (generador de unidades) genera muchos documentos, el CSV
  seguirá siendo manejable. Sin necesidad de compresión ni formato
  binario alternativo (parquet, sqlite) en esta fase.

## A2.1 · `extract_events.py` (2026-10-18)

- **A2.1-a** — **5 variantes `sin_handler` legítimas pero no documentadas en
  el ROADMAP**. El validador las acepta (regla D4 del plan: "toda variante
  sin handler o registrada"), pero conviene que B-fases las tengan en cuenta
  para no marcarlas como bugs del código:

  | Crate | Variante | Razón |
  |---|---|---|
  | `flowy-database2::GetAllRows` (idx 177) | definida en enum, nunca pasada a `.event(...)` en `init`. Probable trabajo en curso o regresión. |
  | `flowy-folder::CreateFolderWorkspace` (idx 0) | `/// Deprecated:`; conservada por compatibilidad. |
  | `flowy-folder::DeleteWorkspace` (idx 3) | handler real vive en `flowy-user::delete_workspace_handler` (caso cross-crate). |
  | `flowy-folder::CopyLink` (idx 20) | `#[event()]` (vacía); `init` no la registra. Posible regresión. |
  | `flowy-user::AddWorkspaceMember` (idx 37) | definida en el enum, `init` no la registra. Posible regresión. |

  Acción para B6.3 (testing) o B6.5 (consolidación): documentar cada caso
  como "definida pero no conectada a handler" para no reabrirlo en revisión.

- **A2.1-b** — **5 formas distintas de `#[event(...)]` y `.event(...)` que el
  parser tuvo que aceptar**. Documentado en `OUT/_ledger/pruebas/A2.1/README.md §Multilínea`.
  Si el código evoluciona (p. ej. nuevo patrón de atributo, llamada con
  generics en el handler), el regex puede romperse silenciosamente. Sugerencia
  para B6.2 (testing): añadir un test de regresión que ejecute el extractor
  sobre los 8 event_map.rs y verifique que la cuenta de `sin_handler`
  no supera 5.

- **A2.1-c** — **D1 del plan asume que `event_map.rs` es exclusivo del
  workspace de AppFlowy**. Verificado: los 3 repos `collab`, `editor`
  clonados en `SRC/` no contienen ningún `event_map.rs`. Si en una
  actualización futura `appflowy-editor` añadiera su propio event_map.rs
  (poco probable, pero no imposible), `extract_events.py` lo procesaría
  como si fuera un crate más; habría que ajustar `--fuente` o filtrar por
  directorio.

- **A2.1-d** — **Resolución de handler ambiguo (política D3 del plan)**. El
  extractor toma la primera coincidencia en orden lexicográfico de ruta.
  En esta ejecución no hubo ambigüedades (0 warnings). Si en el futuro
  dos crates definen el mismo `fn` con el mismo nombre (p. ej. helper
  en `lib-dispatch` y un duplicado en un crate de feature), el primero
  por orden alfabético ganará. Política aceptable, pero conviene
  documentar en A2.2 (`extract_protobuf.py`) si la ambigüedad se vuelve
  un problema.

- **A2.1-e** — **`source_line` apunta al nombre de la variante, no al
  primer `#[event(...)]` previo**. Decisión de implementación tomada en T2
  (corregido en sitio tras detectar que apuntaba a la línea del
  atributo). Documentado en el docstring del regex. Si en B-fases se
  prefiere tener también la línea del atributo para enlazar a la
  declaración completa, añadir campo `attr_source_line` (no rompe el
  esquema actual).

- **A2.1-f** — **El campo `enum.derives` captura todos los derives en el
  orden en que aparecen**. Útil para B2.1 (catálogo de eventos) y B1.5
  (puente Flutter↔Rust). Si un crate cambiase el orden de los derives
  (poco probable), el JSON se mantendría estable: el orden no es
  semánticamente significativo para `Flowy_Event`.

## A2.2 · `extract_protobuf.py` (2026-10-18)

- **A2.2-a** — **3 campos `#[pb(...)]` comentados en el código fuente,
  correctamente excluidos** de la extracción. El parser los detecta
  porque su atributo aparece como `// #[pb(...)]` (línea de comentario),
  no como atributo real. Verificado en:
  - `flowy-ai/src/entities.rs:ChatMessagePB::should_fetch_related_question`
  - `flowy-folder/src/entities/view.rs:ViewIdPB::workspace_id`
  - (No aplica a `UpdateViewPayloadPB::extra`, que es un campo real con
    `#[pb(index=7, one_of)]` + bloque de `//` comentarios previo. El parser
    lo extrae correctamente.)

  Acción para B6.2 (testing): añadir un test de regresión que verifique
  que el conteo de `fields_with_pb` coincide con el conteo manual para
  estos structs.

- **A2.2-b** — **El campo `type` se captura como string crudo**, sin
  expandir genéricos (`Vec<u8>`, `Option<String>`, `HashMap<K, V>`,
  `Cow<'a, T>`). Decisión D3 del plan confirmada. Si en una fase futura
  B-fases necesita resolver tipos para construir un modelo de datos
  (B1.6 motor CRDT, B1.7 persistencia), el extractor puede extenderse
  con un parser de tipos en una fase nueva (no rompería el esquema actual,
  solo añadiría un campo `type_expanded: {base, generics, ...}` opcional).

- **A2.2-c** — **Solo `appflowy/frontend/rust-lib/**` se procesa**;
  los crates `collab-*` externos en `SRC/collab` no se escanean (no
  tienen el patrón `ProtoBuf`/`ProtoBuf_Enum`; usan otro esquema
  basado en `serde` y tipos propios de `yrs`). Documentado en D1 del
  plan. Si en el futuro `collab-importer` añadiera derives de
  `ProtoBuf` (lo cual es plausible: el `Cargo.toml` lista
  `collab-importer` como dep), la fase de ejecución `B0.1` debería
  ampliar el alcance.

- **A2.2-d** — **0 `missing_event_pbs`**: cruce 100 % limpio entre
  `events.json` (A2.1) y `protobuf.json` (A2.2). Esto valida la prueba
  literal del ROADMAP A2.2:
  > cada `input`/`output` de `events.json` existe como entidad extraída
  > (o se reporta faltante).
  Si en una fase futura algún `input`/`output` deja de existir (porque
  se refactoriza el evento), el validador A2.2 lo detectará como
  `missing_event_pbs` y bloqueará la ejecución. Documentar este
  contrato como regresión esperada en B6.2.

- **A2.2-e** — **Cada entity tiene `is_input_of` / `is_output_of`**
  con la lista de eventos (`crate::event_name`) que la referencian.
  Útil para B2.1 (catálogo de eventos) y para la documentación
  per-feature (B3): "qué PBs necesita esta feature". Si un evento se
  reasigna entre crates, este campo se actualiza automáticamente al
  re-ejecutar el extractor (no se requiere actualización manual).

- **A2.2-f** — **El campo `raw_excerpt` puede contener hasta 25 líneas**
  del struct/enum, incluyendo el `#[derive(...)]` previo. Esto cumple
  la regla de evidence de `AGENTS.md §6` ("fragmentos ≤ 25 líneas con
  referencia"). En el JSON actual, ningún excerpt supera 25 líneas (el
  struct más grande tiene ~12 líneas). Sin acción.

## A2.3 · `extract_notifications.py` (2026-10-18)

- **A2.3-a** — **`SearchNotification` (en `flowy-search/src/entities/notification.rs`,
  no en `notification.rs` raíz) NO se extrae**. El extractor busca solo
  `notification.rs` por convención del workspace; este caso vive en
  `entities/notification.rs`. El parser Dart `SearchNotificationParser`
  existe pero su `_source` no se ha encontrado (`null` en el JSON), y
  el enum Rust queda sin mapear. Acción para A2.4/B-fases: ampliar el
  extractor para buscar también `**/entities/notification.rs` y/o
  `**/notification.rs` (más profundo). Mejora: añadir un parámetro
  `--rustlib-paths` que acepte una lista de subpaths.

- **A2.3-b** — **Emitters con `ty` (parámetro genérico) muestran
  `emitted_in_rust: 0` por variante pero `emitters: 1` por enum**. Esto
  ocurre cuando el emisor es un helper como
  `pub(crate) fn document_notification_builder<T: ToString>(id: T, ty: DocumentNotification)`
  → `NotificationBuilder::new(id, ty, DOCUMENT_OBSERVABLE_SOURCE)`. El
  parser captura la llamada, pero el `ty` es un parámetro bare (no una
  variante específica). Decisión D3 del plan: registrar el emisor como
  "genérico" y NO atribuirlo a una variante concreta. Esto es coherente
  con la realidad del código: la función helper emite "alguna variante
  del enum" sin que el extractor pueda saber cuál. Útil para el catálogo
  B2.4 (notificaciones): indica que el enum tiene actividad sin
  granularidad por variante.

- **A2.3-c** — **0 source_mismatches en esta ejecución, pero 5 parsers
  Dart y solo 4 mapean a un enum extraído con datos**. El 5º parser
  (`SearchNotificationParser`) tiene `source: null` en el JSON (porque
  su archivo no tiene `const String _source = '...';` o la línea no
  matchea). Verificado: `search_notification.dart` SÍ tiene `const
  String _source = 'Search';`. La razón: el archivo no se escaneó
  porque su path no incluye `core/notification/` exactamente, o el
  parser tiene un patrón distinto. Acción: revisar manualmente
  `search_notification.dart` y ajustar el regex `RE_DART_SOURCE` si
  fuera necesario. (No bloquea A2.3 porque el test del ROADMAP solo
  exige `DocumentNotification`.)

- **A2.3-d** — **`variants_without_dart_listener: 49` (no es error)**.
  49 variantes declaradas en Rust que no tienen listener Dart
  correspondiente. Esto es legítimo: el código Rust puede emitir
  notificaciones que la UI actual ignora (p. ej. `DatabaseNotification`
  tiene 24 variantes declaradas y solo 1 con listener activo). El
  validador lo tolera (D6 del plan). Acción para B6.5 (consolidación):
  cruzar esta lista con los emitters para identificar variantes
  emitidas sin consumidor (potencial bug de código muerto).

- **A2.3-e** — **El campo `is_default` se basa en la presencia literal
  de `#[default]` en los atributos previos a la variante**. Coincide
  con la convención de Rust (atributo `#[default]` en enums derivados
  con `Default`). Si en el futuro un crate usase `#[serde(default)]`
  o similar, no se detectaría como default; convendría refinar la
  detección.

## A2.4 · `extract_blocs.py` (2026-10-18)

- **A2.4-a** — **Cross-file resolution de eventos** (decisión D13 del plan,
  implementada a posteriori). Los BLoCs de la nueva arquitectura
  (`features/`) declaran sus eventos en archivos separados
  (`logic/*_event.dart`). El extractor pre-indexa todos los `sealed class XEvent`
  y `factory` en el primer pase (FASE 1) y los usa en el segundo pase
  (FASE 2) para resolver el `event_type` declarado en cada BLoC. Esto
  requiere una pasada adicional sobre todos los archivos, pero el
  rendimiento sigue siendo < 5 s sobre 1.525 archivos.

- **A2.4-b** — **`sealed class` con `factory =>` (arrow form)**. El workspace
  usa DOS formas de declarar factories en clases sealed:
  1. `const factory X.foo(args) = Concrete;` (estilo freezed).
  2. `factory X.foo(args) => Concrete(args);` (estilo arrow, sin `= Concrete`).
  El extractor maneja ambas con dos regex: `RE_FREEZED_FACTORY` (con `const`
  opcional) y `RE_SEALED_FACTORY` (arrow). Si en el futuro aparece un
  tercer estilo (p. ej. con `late` o `external`), habría que añadir un
  nuevo regex.

- **A2.4-c** — **Servicios `late final T _name;` sin inicialización (5 casos)
  no se capturan**. El regex `RE_INJECTED` requiere `= T(...);` al final.
  Campos como `late DocumentCollabAdapter _documentCollabAdapter;` se asignan
  dentro de `_initAppFlowyEditorState()` (no en la declaración). Decisión
  D4 del plan: solo capturar los inicializados en línea. Si B6.2
  (testing) necesita todos los campos, habría que parsear también el
  cuerpo del constructor para detectar asignaciones `this._x = X(...)`.

- **A2.4-d** — **33 BLoCs en `plugins/database/application/` (umbral ≥ 5)**.
  El ROADMAP no especifica un número exacto; el test del validador pide
  `>= 5`. Valor real: 33, que incluye BLoCs en subcarpetas
  (`setting/`, `cell/`, `field/`, `row/`, `view/`, `layout/`, `calculations/`,
  `sync/`). Decisión D11 confirmada: incluir subcarpetas.

- **A2.4-e** — **125 BLoCs con eventos extraídos (100 %)**. El validador
  exige que cada BLoC con `event_type` declarado tenga al menos 1 evento
  en `events[]`. Esto se cumple al 100 % gracias al cross-file resolution.
  Si en el futuro un BLoC declara un `event_type` cuyo `sealed class`
  NO existe en el código, el BLoC quedaría con `events: []` y warning
  implícito (no se captura, pero la ausencia de `events` es detectable).

- **A2.4-f** — **17 Cubits sin eventos**. Los `Cubit<…>` no tienen
  `event_type` por convención; el campo queda `null` y `events: []` por
  diseño. Esto es coherente con la API de `flutter_bloc`.

- **A2.4-g** — **Los `state_fields[]` no capturan `@Default(value)` como
  default real**. La regex `RE_FIELD` solo captura defaults con sintaxis
  `name = value`. El atributo `@Default(null)` (como en
  `DocumentAwarenessStatesPB? awarenessStates`) NO se interpreta como
  default. Documentar como limitación menor: el extractor podría
  extenderse para detectar `@Default(expr)` en una fase futura (no
  rompe el esquema actual, solo añade un campo opcional
  `default_annotation`).

## A2.5 · `extract_deps.py` (2026-10-18)

- **A2.5-a** — **Decisión D2 del plan confirmada**: parseo directo de
  `Cargo.toml`/`pubspec.yaml` con `tomllib`/`tomli` (sin `cargo metadata`).
  En el entorno actual (Python 3.9) se usa `tomli` (fallback). El script
  detecta automáticamente cuál está disponible. Si en una fase futura
  la fuente incluye deps con un formato TOML exótico (multi-línea en
  arrays, etc.), podría requerir ajuste del parser. No se ha observado.

- **A2.5-b** — **Dependencia externa `tomli` para Python < 3.11**. El plan
  recomendaba `tomllib` (stdlib 3.11+). En el entorno actual (3.9.6) se
  usa `tomli`, instalable con `pip3 install tomli`. La API de ambos es
  idéntica (`toml.load(f)`); el script no nota la diferencia. Documentar
  en README para reproducibilidad.

- **A2.5-c** — **31 crates en `rust.crates` (no 28)**. El plan
  estimaba 28 crates; en realidad son 31 (incluye `event-integration-test`
  y los 3 de `build-tool/`). El validador se adapta dinámicamente al
  conteo real (`RC` en el check 9). Decisión D3 del plan: usar
  `[workspace.members]` como fuente única de verdad (en lugar de un
  número hardcoded).

- **A2.5-d** — **`flowy-core` tiene 23 internal_dependencies (no 8)**.
  El test del ROADMAP exige "los `flowy-*` de feature" — hay 8
  (`user`, `folder`, `document`, `database2`, `storage`, `ai`, `search`,
  `date`) y el validador los enumera explícitamente. `flowy-core`
  también depende de las 9 variantes `*-pub`, `flowy-error`,
  `flowy-server`, `flowy-server-pub`, `flowy-sqlite`, los 3 `lib-*`, y
  `collab-integrate` = 23 totales. El script reporta TODAS, no solo
  las 8 de feature; el validador filtra.

- **A2.5-e** — **El parser YAML para `pubspec.yaml` es custom
  (mini-parser de 70 líneas)**. No usamos `yaml` (PyYAML) ni
  `tomli` (que no parsea YAML). El formato YAML del pubspec.yaml
  es simple (mapas anidados, listas, scalars) y nuestro parser
  cubre el subconjunto usado. Si en el futuro el pubspec.yaml usa
  características YAML avanzadas (anchors, multi-documento, flow
  style), requeriría reescribir. Por ahora funciona con el workspace
  real (8 archivos pubspec.yaml parseados correctamente).

- **A2.5-f** — **`pubspec.lock` parser custom (~80 líneas)**. Mismo
  argumento que A2.5-e: el formato pseudo-YAML del lockfile no es
  estándar, pero es estable. Si pub.dev cambia el formato, el parser
  requeriría actualización. Documentado para reproducibilidad.

- **A2.5-g** — **326 paquetes resueltos en `pubspec.lock` (transitivas
  + directas)**. El script los cuenta en `summary.total_resolved_packages`
  pero NO los emite individualmente en el JSON (mantiene el tamaño
  manejable: 104 KB vs ~2 MB si se emitieran todos). Decisión D6 del
  plan: solo contar. Si en una fase futura B6.2 (testing) necesita
  el grafo completo de transitivas, se puede añadir un parámetro
  `--include-transitives` al extractor.

- **A2.5-h** — **Mermaid tiene 150 aristas (Rust) + 7 aristas (Dart)**.
  La validación contra el grafo completo de Mermaid podría hacerse con
  `npx @mermaid-js/mermaid-cli` (instalable vía npx), pero consume
  >100 MB y tarda >5 s. El validador actual hace grep para aristas
  específicas (más rápido, suficiente para el test del ROADMAP).

## A2.6 · `extract_misc.py` (2026-10-18)

- **A2.6-a** — **`CommandShortcutEvent` no se define en este workspace**.
  El plan asumía que el enum existía en `appflowy/frontend/appflowy_flutter/lib/`.
  Confirmado: vive en el paquete externo `appflowy_editor` (`SRC/editor/lib/src/...`),
  importado por `command_shortcuts.dart` y `shortcuts_model.dart`. El
  extractor captura `HotKeyItem` (13 instancias con nombres legibles)
  como la fuente principal de atajos. Decisión D4 del plan: ambos se
  capturan; uno está vacío, el otro tiene datos. Documentado.

- **A2.6-b** — **`HotKeyItem` no usa strings para `key`** (usa
  `KeyCode.backslash` + `modifiers`). El nombre se infiere del
  comentario `// ...` anterior a la llamada `HotKeyItem(`. Esto
  produce nombres como "Toggle theme mode light/dark" que son
  legibles pero no son el "key" real (que sería `Ctrl+Shift+L`).
  El extractor podría capturar también el `KeyCode.xxx` y los
  `modifiers` para reconstruir la key, pero esa lógica se reserva
  para una fase futura (no requerida por el test del ROADMAP).

- **A2.6-c** — **`GoRoute` usa referencias a constantes en el 100 %**
  de los casos (`path: SomeScreen.routeName`), no strings literales.
  La regex original (D2) aceptaba solo strings; ampliada para aceptar
  tanto `'<literal>'` como `<Identifier>(.<identifier>)*`. Si en el
  futuro hay un mix, ambos se capturan.

- **A2.6-d** — **`InProgress = 107` tenía un comentario `// ...`
  entre `#[error("...")]` y el nombre**, lo que la regex original
  no aceptaba. Sin este cambio, 1 de 133 ErrorCodes (el último de
  una sección) quedaba sin capturar. La regex ampliada con
  `(?:\s*(?://[^\n]*|/\*.*?\*/)\s*)*` entre attrs y nombre
  resuelve el caso general.

- **A2.6-e** — **`find_matching_brace` requiere `text.find("{", m.end() - 1)`**
  cuando el regex no consume la `{` final. Si se usa `m.end()` sin
  `-1`, el `find` salta al siguiente `{` y se desbalancea el parser.
  Patrón observado en A2.1, A2.2, A2.3, A2.4 y A2.6 (todos los
  extractores que buscan un `enum/struct/sealed class`).

- **A2.6-f** — **1.637 claves i18n únicas con > 1.637 usos `.tr()`**.
  Las claves se agrupan por `LocaleKeys.X` y `'X'`. Ambos patrones
  conviven en el código. Las claves con mayor uso son las globales
  (`appName`, `common.cancel`, etc.). El JSON incluye `usages` y
  `sources` para que B2 (catálogo de i18n) pueda priorizar.

- **A2.6-g** — **`startup_tasks.ordered_tasks` registra 15 clases
  (no 12 como estimé el plan)**. Las 3 adicionales son:
  `ApplicationInfoTask`, `AutoUpdateTask`, `HotKeyTask`, que se
  registran condicionalmente. El validador no exige un número
  fijo; solo `> 0` y `PlatformErrorCatcherTask` en posición 0-3.

## A2.7 · `extract_codegen.sh` (2026-10-18)

- **A2.7-a** — **`cargo` SÍ está presente** en el sistema
  (`$CARGO_HOME/bin/cargo`, normalmente `~/.cargo/bin/cargo`). El plan original asumía que
  faltaba toolchain completo. Reordenado: la estrategia 3 (`cargo_build_manual`)
  SÍ se intenta y compila exitosamente (las dependencias de flowy-codegen
  ya estaban cacheadas de un intento previo). El problema NO es la
  compilación sino la EJECUCIÓN: `flowy-codegen` no expone binario, solo
  una librería. Documentado en `codegen-fallido.md`.

- **A2.7-b** — **`Makefile.toml` no está presente en este snapshot del repo**.
  El ROADMAP A2.7 lo menciona como ruta canónica (`cargo make` según
  `Makefile.toml`), pero el archivo no existe en
  `SRC/appflowy/frontend/rust-lib/`. Esto puede deberse a (a) un archivo
  `.gitignore`'d intencionalmente (build/generated); (b) falta en este
  snapshot. Acción: si el usuario quiere habilitar codegen, recuperar
  `Makefile.toml` de la fuente original (commit anterior) o crearlo
  manualmente con tareas `codegen` y `proto`.

- **A2.7-c** — **Bash `echo` no interpreta `\t`** (a diferencia de
  `printf`). El script usa `printf 'present\t%s\n'` para garantizar
  que el separador sea un tab real (no la cadena literal `\t`).
  Documentado para futuros mantenedores.

- **A2.7-d** — **Bash export con tabs en valores manglea el contenido
  en env vars**. Solución: escribir a `.prereq.env` (archivo de texto)
  con `|` como separador, leer en Python y convertir `|` → `\t`. Esto
  es más robusto que los env vars para datos con caracteres especiales.

- **A2.7-e** — **A2.2 es independiente de A2.7**. A2.2
  (`extract_protobuf.py`) parsea los `.rs` directamente con regex sobre
  los `#[derive(ProtoBuf)]`/`#[derive(ProtoBuf_Enum)]`, sin requerir
  los `.proto` generados. Esto significa que aunque A2.7 falle (caso
  documentado), el catálogo A2.2 sigue siendo válido. La integración
  con el sistema de codegen se haría en una fase futura (B0.1) si se
  quiere cruzar nombres A2.2 con `.proto` reales.

- **A2.7-f** — **El `cargo build -p flowy-codegen` se completa en < 1 s**
  con dependencias cacheadas (el primer build descarga ~200 MB y tarda
  >60 s, lo cual excede el timeout del shell de 120 s). En este
  entorno, las dependencias ya están en `target/` de intentos
  anteriores del propio skill. El timeout de 60 s del script es
  suficiente para builds incrementales pero puede fallar en el primer
  build limpio.

- **A2.7-g** — **322 `.pb.dart` files ya están commiteados en el repo**
  (en `packages/appflowy_backend/lib/protobuf/` y otros paths), lo que
  confirma que el codegen se ejecutó al menos una vez. Estos archivos
  NO son `.proto` (estos sí están generados dinámicamente). El
  pipeline actual: (1) devs ejecutan `cargo make codegen` para generar
  `.proto`; (2) `protoc --dart_out=...` genera los `.pb.dart`. Sin
  paso (1), el repositorio solo tiene los `.pb.dart` ya generados.

## A3.1 · `validate_mermaid.sh` (2026-10-18)

- **A3.1-a** — **Fences de 4+ backticks no soportados.** El extractor
  `awk` busca apertura con ```` ```mermaid ```` (3 backticks) y cierre
  con ```` ``` ```` (3 backticks). El estándar CommonMark permite
  abrir un bloque con N backticks y cerrar con N+ backticks del mismo
  tamaño; la skill no contempla ese caso porque todos los esqueletos
  de `diagram-conventions.md` y `feature-template.md` usan 3. Si
  durante la ejecución B aparece un documento con fences de 4+
  backticks, se reabre la fase para añadir soporte.

- **A3.1-b** — **`flock(1)` no existe en macOS**; el contador
  paralelo usa `fcntl.flock` vía Python 3 stdlib. Portabilidad
  confirmada: el script se ejecutó en este entorno (macOS, sin
  `flock`) y en cualquier Linux (con `flock` se podría simplificar,
  pero la solución Python es POSIX y suficiente). No requiere
  acción.

- **A3.1-c** — **Atributos de bloque mermaid** (p. ej.
  ```` ```mermaid {…} ````): la regex `/^```mermaid([[:space:]]|\{|$)/`
  los acepta. Si los esqueletos oficiales evolucionan a ```` ```mermaid theme=forest ````
  (sin `{ }`), añadir el modificador a la regex. Sin acción hoy.

- **A3.1-d** — **Cold start de `mmdc` (~1–2 s)** se debe a la carga
  de Chromium por Puppeteer. En CI esto multiplica el coste de C1
  (pasada global sobre todo `OUT/`) por el número de archivos. Si el
  tiempo total excede el budget, considerar migrar a `@mermaid-js/mermaid`
  directo en Node (sin Puppeteer) o usar `mermaid.render` en un
  browser headless compartido. Documentado, sin acción.

## A3.2 · `validate_evidence.py` (2026-10-18)

- **A3.2-a** — **Falsos positivos tipo `RFC:4180`** o `tag:v1.0`: la
  regex exige un `.` antes del `:` (extensión de archivo), por lo
  que estos casos no se capturan. Si en la salida B aparecen
  referencias que el validador confunde con evidencia (p. ej. un
  SHA `abc1234:5:6` con dos `:`), se reabre la fase para añadir
  whitelist de prefijos no-evidencia (semver, RFC, etc.).

- **A3.2-b** — **Convención de `ruta_rel` en `inventario.json`**: las
  entradas guardan `ruta_rel = "<fuente>/<rest>"` (con el prefijo
  del repo). Las referencias de R-003 usan la ruta interna sin
  prefijo (`collab-database/src/blocks/block.rs`, no
  `collab/collab-database/...`). El validador resuelve esto
  prepending `f"{fuente}/"` a la ruta en el lookup, salvo que ya lo
  tenga. Si en una fase futura el inventario cambia de convención,
  este fallback se rompe. Documentado para revisión.

- **A3.2-c** — **Exclusión de bloques fenced**: la state machine
  ignora refs dentro de ` ```código``` ` (3 backticks). Los fixtures
  de A3.2 no contienen fences con refs dentro (no necesario para la
  prueba del ROADMAP), pero la lógica es trivialmente correcta.
  Cobertura vía tests del propio script al evolucionar.

- **A3.2-d** — **Performance en C1**: con 4.603 entradas en el
  inventario y cache de `line_count` por archivo único, el validador
  procesa los ~300 docs esperados de `OUT/` en < 30 s. Si en CI el
  tiempo excede este presupuesto, añadir cache persistente de
  `line_count` en `OUT/_ledger/cache/` (clave = sha1 del archivo,
  valor = line_count).

## A3.3 · `validate_template.py` (2026-10-18)

- **A3.3-a** — **Parser YAML custom limitado**: el parser soporta
  sólo `key: value`, `key: [a, b]`, y `key:` + lista indentada con
  `- valor`. NO soporta multi-línea con `>` o `|`, anclas `&`,
  aliases `*`, ni tags `!!str`. Si en la salida B un documento usa
  alguna de estas formas (improbable en los esqueletos
  `output-skeleton/`), se reabre la fase para añadir soporte o
  migrar a PyYAML.

- **A3.3-b** — **Exclusión de `## N.` en fenced blocks**: la state
  machine ignora headings dentro de ` ```código``` ` (3 backticks).
  Ningún fixture de A3.3 contiene fences con `## N.` (no necesario
  para la prueba del ROADMAP), pero la lógica es trivialmente
  correcta. Cobertura vía tests del propio script al evolucionar.

- **A3.3-c** — **Auto-detección por prefijo de `id`**: la v1 detecta
  por regex `^F\d+` o `^B\d+`. Si en una fase futura se añaden
  prefijos nuevos (p. ej. `M` para motor), hay que extender
  `detect_template()` y `TEMPLATES`. Documentado.

- **A3.3-d** — **Validación de archivos cubiertos no implementada**:
  `validate_template.py` valida que `archivos_cubiertos` sea una
  lista, pero no que cada elemento apunte a un archivo del
  inventario. Esto se delega a A3.4 (`validate_coverage.py`), que
  cruza el ledger con los documentos. Sin acción aquí.

## A3.4 · `validate_coverage.py` (2026-10-18)

- **A3.4-a** — **CLI sin positional args**: el plan proponía
  `validate_coverage.py [PATH]` posicional; se implementó como
  `--ledger PATH` (consistente con `--threshold`, `--limit`).
  Sin impacto funcional; documentado.

- **A3.4-b** — **Cruce con `documento` (columna del CSV) no
  implementado**: el validador lee la columna `documento` (path al
  `.md` que cubre la fila) pero no comprueba que el archivo exista
  ni que sea parseable. La validación semántica de cada doc vive
  en A3.3 (template) y A3.5 (índice). A3.4 sólo cuenta estados
  agregados. Sin acción.

- **A3.4-c** — **Agrupación por `feature_ids` no implementada**:
  la v1 agrupa por `capa` (15 valores en el ledger real) pero
  ignora `feature_ids` (que en el ledger actual está todo vacío,
  porque A4.1 aún no ha asignado). Cuando A4.1 (`assign_ledger.py`)
  pueble `feature_ids`, se reabre A3.4 para añadir `--by-feature`.
  Documentado.

## A3.5 · `build_index.py` (2026-10-18)

- **A3.5-a** — **Lógica de cobertura duplicada entre A3.4 y A3.5**:
  `build_index.py` reimplementa la lectura de `cobertura.csv` con
  conteo por capa + global (≈30 líneas), en lugar de extraer un
  módulo compartido. Decisión consciente: mantener el patrón "1
  script = 1 fichero" del Bloque A3. Cuando la skill genérica
  `notemartin-extension-reviews` se lleve los scripts en C7, se
  refactoriza a `_coverage_helper.py` compartido. Sin acción
  aquí.

- **A3.5-b** — **Ids duplicados no fallan**: si 2 `.md` tienen el
  mismo `id` en frontmatter, el script emite un `WARN` por
  stderr y conserva el último en el dict. NO falla. Decisión
  consciente: en fase de autoría es común tener docs en proceso
  con ids provisionales. Se reabre si C2 (gate de 100%
  verificado) exige unicidad.

- **A3.5-c** — **Auto-referencia del índice excluida del scan**:
  `extract_cross_refs()` no escanea el archivo `00-INDEX.md`
  generado, porque su sección "no resueltos" contiene
  literalmente `<X>` (metadatos, no enlaces del producto). Si
  en una fase futura alguien quiere enlazar desde el propio
  índice a otros docs, se reabre la fase para permitir refs
  legítimas en `00-INDEX.md` (p. ej. excluyendo sólo la sección
  "no resueltos").

---
## De F08 — Búsqueda e indexación (2026-10-18)

1. `[NO DETERMINADO]` ¿Está previsto usar `SearchFilterPB` en una variante futura de `SearchEvent` o es API muerta? (referencia: `appflowy:appflowy/frontend/rust-lib/flowy-search/src/entities/search_filter.rs:4–7`).
2. `[NO DETERMINADO]` ¿Por qué `SearchNotification` se compila y se exporta pero no se registra como `rust_notifications` en A2.3? (referencia: `appflowy:appflowy/frontend/rust-lib/flowy-search/src/entities/notification.rs:14–18`).
3. `[NO DETERMINADO]` ¿Qué condiciones exactas producen el cutoff `0.4` en `state.read().await.search(...)`? (referencia: `appflowy:appflowy/frontend/rust-lib/flowy-search/src/document/local_search_handler.rs:53`).
4. `[NO DETERMINADO]` ¿`event-integration-test` tiene fixtures para `StreamSearch`? (referencia: aparece como dependencia en `OUT/_ledger/extract/deps.json` pero los archivos concretos no están en F08.json).

---
## De B3.F03 — Folder, workspaces, vistas (2026-10-20)

1. `[NO DETERMINADO]` **`features/view_management/` está vacío**: `README.md` 0 bytes y `logic/{view_event,view_management_bloc,view_state}.dart` 1 byte. `ViewManagementBloc` no existe en el snapshot `5cf3a36`. ¿Migración abandonada, andamiaje de una feature futura, o errata del triage B0.2?
2. `[NO DETERMINADO]` **Hueco del extractor de notificaciones**: `extract_notifications.py` marca `emitted_in_rust = 0` para las 19 variantes de `FolderNotification` porque su heurística solo reconoce llamadas literales a `NotificationBuilder::new`, y `flowy-folder` emite siempre vía el envoltorio `folder_notification_builder` (`appflowy/frontend/rust-lib/flowy-folder/src/notification.rs:48–55`). Afecta a F03.2, F04, F06, F12 y F15. Referencia: `OUT/_ledger/pruebas/B3.F030/README-f03.md`.
3. `[NO DETERMINADO]` **`DidCreateWorkspace`, `DidUpdateWorkspace`, `DidDeleteView`, `DidRestoreView` y `DidUpdateFolderSnapshotState`** están declaradas en `notification.rs` y tres tienen rama en Dart, pero nunca se emiten. ¿Intencional o regresión?
4. `[NO DETERMINADO]` **`CreateFolderWorkspace`, `DeleteWorkspace` y `CopyLink`** son `FolderEvent` declarados **sin handler**. ¿Reservados, deprecados o olvidados?
5. `[NO DETERMINADO]` **`GetFolderSnapshots` y `ReadCurrentWorkspaceViews`** tienen handler (`flowy-folder/src/event_handler.rs:42–49` y `:378–386`) pero **ningún consumidor Dart**. ¿API muerta o pendiente de cliente?
6. `[INFERIDO]` **`WorkspaceBloc._fetchWorkspaces` descarta la lista recibida** (`appflowy/frontend/appflowy_flutter/lib/workspace/application/workspace/workspace_bloc.dart:52`): el bloc es hoy un no-op. ¿Regresión o placeholder?
7. `[NO DETERMINADO]` **B1.6 documenta campos y variantes de `collab-folder` que no existen** en el rev `4dfccef`: `layout_settings`, `cover`, `is_space`, `display_mode`, `view_space_status`, `desc` (como campo del struct) y `ViewLayout::AIChat`. **Pendiente de resolver en la fase C3 (revisión cruzada de consistencia)**; la tabla de discrepancias está en `OUT/09-features/F03-folder-workspaces-vistas/0.3-collab-folder.md` §2.
8. `[NO DETERMINADO]` **Fixtures binarias no inventariadas**: `collab-folder/tests/folder_test/history_folder/folder_{with,without}_fav_v1.zip` son necesarias para los tests de migración (`util.rs:207` las descomprime) pero no están en `inventario.json`.
9. `[NO DETERMINADO]` **Tipos que el encargo daba por reales y no existen** en `collab-folder`: `ViewId`, `WorkspaceId`, `Trash`, `ViewRelation`, `ViewMetadata`.
10. `[NO DETERMINADO]` ¿Quién orquesta el evento `ImportZipFile` (`flowy-folder/src/event_handler.rs:367`)? No se localiza el caller Dart.
11. `[NO DETERMINADO]` `DidUpdateSharedViews` / `DidUpdateSharedUsers`: no se ha identificado un suscriptor dedicado fuera de la propia pantalla de compartir de cada vista.

---
## De B3.F04 — Sidebar, favoritos, recientes, papelera, tabs, command palette (2026-10-20)

1. `[NO DETERMINADO]` `features/view_management/README.md` vacío: ¿cuándo se llenará y qué arquitectura sustituirá a los blocs legados de `workspace/application/`? (misma raíz que F03.1)
2. `[NO DETERMINADO]` ¿Debe corregirse `extract_notifications.py` para reconocer `folder_notification_builder` como emisor? (ver F03-2)
3. `[NO DETERMINADO]` ¿`DidCreateWorkspace`, `DidUpdateWorkspace`, `DidDeleteView`, `DidRestoreView` deberían emitirse? (ver F03-3)
4. `[NO DETERMINADO]` ¿Dónde se consume `RecentViewsListener`? La clase existe (frontend/appflowy_flutter/lib/workspace/application/recent/recent_listener.dart:16) pero **no contiene ningún `case FolderNotification`**: filtra solo por subject.
5. `[NO DETERMINADO]` ¿Se persistirán las tabs entre sesiones? `TabsBloc` no parece escribir en almacenamiento.
6. `[INFERIDO]` **Código muerto detectado** (documentado, no eliminado): `FavoritePinBloc` (nunca instanciado), `EditPanelBloc` (registrado en `get_it` pero ningún `EditPanelEvent` se despacha), `SliderMenuHoverTrigger`, `openWorkspaceNotifier`. Además los registros `getIt` de `TrashService`/`TrashListener` (frontend/appflowy_flutter/lib/startup/deps_resolver.dart:184–185) no tienen consumidor: `TrashBloc` instancia los suyos.

---
## De B3.F06 — Sync y servidores (2026-10-20)

1. `[INFERIDO]` ¿`update_network_state_handler` (`appflowy/frontend/rust-lib/flowy-user/src/event_handler.rs:473`) muta directamente `AppFlowyCloudServer::network_reachable` o hay un canal intermedio?
2. `[NO DETERMINADO]` ¿Quién invoca `set_network_reachable(true|false)` desde Dart? Candidato: `startup/tasks/appflowy_cloud_task.dart`, asignado a F00.
3. `[NO DETERMINADO]` ¿Existen tests de `flowy-server`, de `network_monitor.dart` o de `doc_sync_state_listener.dart`? La búsqueda exhaustiva en `SRC/` no devuelve resultados.

---
## De B3.F07 — Almacenamiento de archivos (2026-10-20)

1. `[NO DETERMINADO]` ¿Existe test de widget/integration para `ImagePlaceholder` + `FileBlockComponent` + `UploadImageMenu`? Búsqueda sin resultados en `appflowy_flutter/test/`.
2. `[NO DETERMINADO]` ¿Hay mecanismo que migre bloques `CustomImageType.local` a nube al cambiar de workspace local a AppFlowy Cloud? No aparece en los 58 archivos ni en `ImageBlockData`.
3. `[NO DETERMINADO]` ¿Por qué `notifications.json` marca ambas variantes de `StorageNotification` como `emitted_in_rust: 0` si el código emite en frontend/rust-lib/flowy-storage/src/manager.rs:751–764? Posible hueco del extractor (mismo patrón que F03-2).
4. `[NO DETERMINADO]` ¿`Signal::Stop` cierra limpiamente los `IsolateSink` abiertos vía `RegisterStream`? No hay test que cubra el orden de cierre.

---
## De B3.F05 — Usuario, auth, sesión (2026-10-20)

1. `[NO DETERMINADO]` `AuthProvider` y `SignUpMethod` no existen como tipos Dart: lo real es `ProviderTypePB`, `AuthenticatorType` y `ProviderTypePBExtension`.
2. `[NO DETERMINADO]` **5 `UserEvent` sin despachar desde F05.1**: `GetUserWorkspace` (22), `GetMemberInfo` (56), `SetCloudConfig` (13), `GetCloudConfig` (14), `UpdateNetworkState` (24). Falta decidir qué unidad los cubre.
3. `[NO DETERMINADO]` `SignUpBloc` existe pero no hay `SignUpScreen`: ¿funcionalidad planificada o código muerto?
4. `[NO DETERMINADO]` `workspace/application/user/user_workspace_bloc.dart` (692 LOC reales) es un **re-export de una línea** a `lib/features/workspace/logic/`, que quedó fuera del ledger de F05. ¿Se reasigna a F05.1 o se crea una unidad para la arquitectura `features/*`?
5. `[NO DETERMINADO]` ¿`AppFlowyCloudAuthService.signUp` es alcanzable? Lanza `UnimplementedError`.
6. `[INFERIDO]` `UserListener._userNotificationCallback` (frontend/appflowy_flutter/lib/user/application/user_listener.dart:98–106) tiene un `switch` **sin `break`**: el caso `DidUpdateUserWorkspace` cae también en `DidUpdateWorkspaceSetting`. Hoy es inocuo porque los PB tienen formatos distintos.
7. `[NO DETERMINADO]` ¿Hay reintento de `load_awareness_from_server` al cambiar el `WorkspaceType`?
8. `[NO DETERMINADO]` ¿Cómo reacciona `notify_did_switch_plan_handler` ante `response_timeout()`?
9. `[NO DETERMINADO]` ¿Cuál es el payload futuro de `DidUpdateReminder`?
10. `[NO DETERMINADO]` ¿Cómo se sincroniza `UserAwareness` al rotar el `device_id`?

---
## De la ejecución de B3.F03..F07 — tooling y convenciones (2026-10-20)

1. `[RESUELTO 2026-10-20]` **`build_index.py` no resolvía los ids de fase `B1.x` / `B2.x`**: los docs de `OUT/06-puente-flutter-rust/`, `OUT/08-persistencia/` y los catálogos `11-…`/`12-…` declaran ids como `06-00-indice`, `07-00-indice`, `08-00-indice` o `11-catalogo-eventos-ffi`, no `B1.5` / `B2.1`. **Arreglado** añadiendo la constante `ID_ALIASES` a `SKILL/scripts/build_index.py`, que mapea `B1.5`–`B1.7` y `B2.1`–`B2.6` al sub-documento índice de cada carpeta. Los no resueltos bajaron de 66 a 47.
2. `[NO DETERMINADO]` **Los ids de feature padre no resuelven cuando la feature está dividida**: `[[F01]]`, `[[F02]]`, `[[F03]]` no encuentran documento porque solo existen `F03.0`…`F03.3`. Evaluar un id de feature "virtual" que resuelva al subdocumento índice.
3. `[NO DETERMINADO]` **`STATE.md` contiene tokens `<X>`, `<NOEXISTE>` y `<F..>`** al explicar el comportamiento de `build_index.py`, y `build_index.py` los escanea como enlaces reales. Es ruido conocido (ver A3.5-c) pero infla el recuento de "no resueltos" de 61 a 63.
4. `[NO DETERMINADO]` **`doc_sync_state_listener.dart` está en F06** pero su gemelo `database_sync_state_listener.dart` está en F02.0.1.2 y `document_sync_bloc.dart` en F01.0.1: los tres listeners de estado de sync quedan en features distintas. ¿Vale la pena una unidad transversal de sync?

### Nota de estado — validadores de la Fase A que fallan por deriva histórica (2026-10-20)

Al pasar la regresión completa tras el cierre de B3.F03..F07, 4 de las 21 suites del Bloque A fallan. **Ninguna es consecuencia de este trabajo**; las tres primeras comprueban el estado del ledger tal como estaba en su fase y la cuarta quedó obsoleta por el refactor de A5.2:

| Suite | Fallo | Causa | ¿Arreglable? |
|---|---|---|---|
| `validate-A0.3.sh` | `se esperaban 6 .md en SKILL/references, hay 9` | A5.2 (2026-10-19) añadió `subagent-contract.md`, `subagent-autor-prompt.md` y `subagent-revisor-prompt.md` sin actualizar la expectativa | Sí: subir el número a 9 y validar los 3 ficheros nuevos |
| `validate-A1.3.sh` | `4603 filas con estado != sin_asignar` | El test comprueba el ledger recién inicializado; hoy hay 1 762 `verificado` | Sí, pero solo tiene sentido sobre una copia de `cobertura.csv` de la época |
| `validate-A3.4.sh` (check 8) | `modo real cobertura.csv: global=0.00% (4.603 sin_asignar)` | Igual que A1.3: la expectativa fija está congelada en el instante de la fase | Sí, actualizando el porcentaje esperado o retirando el check |
| `validate-A4.3.sh` | `argument --rol: invalid choice: 'autor' (choose from 'revisor')` | A5.2 movió el rol `autor` a `run_subagent_placeholder.py` y dejó `run_subagent.py` solo con `revisor` | Sí: apuntar el check al script placeholder |

`[NO DETERMINADO]` ¿Abrir una fase de reparación de las suites del Bloque A, o dejarlas como tests históricos congelados y sacarlas de la regresión continua? Decidir antes de la fase C1 (pasada global de validadores), que exige 0 errores.

## B3.F00–F21 · Cierre del ledger (2026-10-20)

Preguntas recogidas de la sección 18 de los documentos escritos en el
cierre del Bloque B3. Todas están **descritivas**, no bloqueantes:
ninguna impide cerrar la fase; todas se resuelven en B6.5.

### B3.F00.1 (4)

- **B3.F00.1** — `[NO DETERMINADO]` Contenido exacto de `dart-ffi/src/protobuf.rs`: el módulo se declara en `appflowy/frontend/rust-lib/dart-ffi/src/lib.rs:38` pero el fichero no está en el inventario porque lo genera el build script; sin él no se puede verificar qué mensajes protobuf quedan registrados en el crate más allá de `FFIRequest`/`FFIResponse`.
- **B3.F00.1** — `[NO DETERMINADO]` ¿Puede alguna vez producirse `FFIStatusCode::Internal`? La variante existe en `appflowy/frontend/rust-lib/dart-ffi/src/model/ffi_response.rs:9` y el cliente Dart la maneja en `appflowy/frontend/appflowy_flutter/packages/appflowy_backend/lib/dispatch/dispatch.dart:87–90`, pero la única conversión de Rust (`From<AFPluginEventResponse> for FFIResponse`, `appflowy/frontend/rust-lib/dart-ffi/src/model/ffi_response.rs:28–31`) mapea solo `Ok` y `Err`, y `InternalError::as_response` construye siempre `StatusCode::Err` (`appflowy/frontend/rust-lib/lib-dispatch/src/errors/errors.rs:130–134`).
- **B3.F00.1** — `[NO DETERMINADO]` Semántica exacta de `singleCompletePort`: el helper viene del paquete externo `isolates` (`isolates: ^3.0.3+8` en `appflowy/frontend/appflowy_flutter/packages/appflowy_backend/pubspec.yaml:15`) y su código no está en el repositorio; se usa en `appflowy/frontend/appflowy_flutter/packages/appflowy_backend/lib/dispatch/dispatch.dart:129` y su contrato se infiere del uso.
- **B3.F00.1** — `[NO DETERMINADO]` Destino de las 5 variantes de evento sin handler (`CreateFolderWorkspace`, `DeleteWorkspace`, `CopyLink` en `flowy-folder`; `GetAllRows` en `flowy-database2`; `AddWorkspaceMember` en `flowy-user`): ¿se registran desde otro punto del código, son residuo de una refactorización, o son invocables desde Dart y devuelven `HandleNotFound`?

### B3.F00.2 (7)

- **B3.F00.2** — Las siguientes afirmaciones están marcadas como `[NO DETERMINADO]` y se copian literalmente a `OUT/22-preguntas-abiertas.md`:
- **B3.F00.2** — `[NO DETERMINADO]` **Quién consume `chat_local_setting_table`.** La tabla se crea en la migración `2024-06-26-015936_chat_setting` y se declara en `schema.rs`, pero una búsqueda del identificador en todo `frontend/rust-lib` solo devuelve sus dos apariciones en `schema.rs`. No se ha determinado si el código que la usaba se eliminó en algún commit, si se migrated a columnas de `chat_table`, o si el consumidor esperado está en un crate no presente en este snapshot.
- **B3.F00.2** — `[NO DETERMINADO]` **Contenido del módulo generado `flowy-error/src/protobuf`.** `appflowy/frontend/rust-lib/flowy-error/src/lib.rs:4` declara `pub mod protobuf;` y el crate no contiene `src/protobuf.rs` ni `src/protobuf/mod.rs` en el árbol de fuentes, porque `flowy-codegen` los escribe en tiempo de compilación en la ruta por defecto `src/protobuf` (`appflowy/frontend/rust-lib/build-tool/flowy-codegen/src/flowy_toml.rs:28–32`). No se ha inspeccionado el código generado, así que no se puede afirmar qué nombres exactos reciben las clases Rust ni qué índices protobuf se asignan a `FlowyError` más allá de los tres `#[pb(index)]` declarados en el fuente.
- **B3.F00.2** — `[NO DETERMINADO]` **Estado real de `flowy-date` como consumidor de `flowy-error`.** `appflowy/frontend/rust-lib/flowy-date/Cargo.toml:12` declara `flowy-error = { path = "../flowy-error" }` sin features, y no se ha encontrado ninguna función en el crate que use `FlowyError`. No está claro si la dependencia es genuina, está planificada, o es residuo de una refactorización.
- **B3.F00.2** — `[NO DETERMINADO]` **Existencia de `appflowy_backend/lib/src/flowy_error.dart`.** El catálogo `[[B2.5]]` cita ese fichero como parte de su cobertura, pero no existe en este snapshot: el `FlowyError` de Dart es el mensaje protobuf generado, importado como `package:appflowy_backend/protobuf/flowy-error/errors.pb.dart` (`appflowy/frontend/appflowy_flutter/packages/appflowy_backend/lib/dispatch/error.dart:4`). No se ha determinado si el fichero se movió, se renombró o se eliminó entre el commit de referencia del catálogo y el actual, ni en qué documento de la skill hay que corregir esa referencia.
- **B3.F00.2** — `[NO DETERMINADO]` **Cobertura de traducción de los 133 códigos en Dart.** `appflowy/frontend/appflowy_flutter/lib/shared/error_code/error_code_map.dart:1–45` solo traduce 13 variantes (6 de publicación y 7 de espacio de nombres). No se ha determinado, sin recorrer las 439 entidades del catálogo de protobuf y los widgets de las features, cuántos de los 133 códigos llegan a la UI con el `msg` de Rust y cuántos con un texto propio de la capa Dart.
- **B3.F00.2** — `[NO DETERMINADO]` **Comportamiento ante migración fallida en producción.** El diagrama de `§11` razona la reversión transaccional a partir del uso de `run_pending_migrations`, pero no se ha localizado ninguna prueba ni ningún manejador de recuperación en el repo que documente qué ve el usuario cuando la base queda con migraciones a medias en una versión de producción concreta.

### B3.F00.4 (5)

- **B3.F00.4** — `[NO DETERMINADO]` ¿Quién lee realmente `CollabConnectReachability`? `AppFlowyCollabBuilder::update_network` lo mantiene actualizado (`appflowy/frontend/rust-lib/collab-integrate/src/collab_builder.rs:114–124`) pero dentro de `collab-integrate` no hay ninguna lectura del campo. No se ha localizado el consumidor fuera del crate. Afecta a F06 (sync) y F18 (connect_state).
- **B3.F00.4** — `[NO DETERMINADO]` ¿Es intencionado que `build_collab` use `RocksdbDiskPlugin` sin condición de plataforma? La importación `if_wasm!` de `IndexeddbDiskPlugin` (`appflowy/frontend/rust-lib/collab-integrate/src/collab_builder.rs:25–27`) no se referencia en ninguna línea posterior. Habría que comprobar si el build wasm de AppFlowy compila este crate.
- **B3.F00.4** — `[NO DETERMINADO]` ¿Debe eliminarse `appflowy/frontend/rust-lib/flowy-server-pub/src/af_cloud_config.rs`? No está declarado como módulo en `appflowy/frontend/rust-lib/flowy-server-pub/src/lib.rs:18–30`, por lo que no compila, y su `AFCloudConfiguration` diverge de las variantes nativa y wasm. Es un residuo de la refactorización por plataforma.
- **B3.F00.4** — `[NO DETERMINADO]` ¿Quién consume `CollabCloudPluginProvider::is_sync_enabled`? El método existe (`appflowy/frontend/rust-lib/collab-integrate/src/plugin_provider.rs:10`), tiene blanket impl y es implementado por `ServerProvider`, pero la decisión de sync usa `CollabBuilderConfig::sync_enable`, que es un flag del llamante.
- **B3.F00.4** — `[NO DETERMINADO]` **Discrepancias con `[[B1.6]]`** que se Detectan al contrastar: (a) B1.6 (`OUT/07-motor-colaborativo-crdt/06-collab-plugins.md`) afirma que `LocalStorage` persiste el `yrs::Doc` en una tabla SQLite `kv_table` con clave `(object_id, collab_type)`; en este rev la persistencia va a RocksDB mediante `CollabKVDB`, que es un alias a `KVTransactionDBRocksdbImpl` (`collab:collab/collab-plugins/src/lib.rs:24`), y `build_collab` engancha `RocksdbDiskPlugin` (`appflowy/frontend/rust-lib/collab-integrate/src/collab_builder.rs:287–296`). (b) B1.6 describe el plugin de nube como `CloudStorage`/`RemoteCollabStorage`; el camino real desde AppFlowy es `SyncPlugin` construido en `appflowy/frontend/rust-lib/flowy-core/src/deps_resolve/cloud_service_impl.rs:652–659`. (c) El enum `CollabType` de B1.6 **sí** coincide con este rev (7 variantes, mismos discriminantes), a diferencia de lo que sugería el hallazgo 5 de ROADMAP.md (linea 341), que se refiere a `collab-folder`, no a `collab-entity`. Pendiente de resolver en C3.

### B3.F00.5.1 (2)

- **B3.F00.5.1** — `[NO DETERMINADO] F00.5.1-Q1` — Nombres exactos de las **5 variantes sin handler** Rust (3 en `flowy-folder`, 1 en `flowy-database2`, 1 en `flowy-user`). El catálogo tiene los totales pero el listado debe extraerse de `OUT/_ledger/extract/events.json:crates[].variants[].sin_handler==true`. Asignar a `B2.1` (`OUT/13-catalogo-eventos-ffi.md`).
- **B3.F00.5.1** — `[NO DETERMINADO] F00.5.1-Q2` — Las **51 variantes** Rust con `NotificationBuilder` pero sin listener Dart (`OUT/_ledger/extract/notifications.json:summary.variants_without_dart_listener`): ¿se deben a listeners en localizaciones no escaneadas por `A2.4`, o a superficie no cableada todavía? Asignar a `B2.4` (`OUT/14-catalogo-notificaciones.md`).

### B3.F02.13 (3)

- **B3.F02.13** — `[NO DETERMINADO]` Línea exacta del `case DatabaseNotification::DidUpdateRow` en `view_listener.dart` — el catálogo `OUT/_ledger/extract/notifications.json` lo apunta a `view_listener.dart`, pero la ruta completa del switch (línea) requiere abrir el archivo `appflowy/frontend/appflowy_flutter/lib/plugins/database/application/view/view_listener.dart` (cubierto por `[[F02.0.1.2]]`).
- **B3.F02.13** — `[NO DETERMINADO]` ¿`DatabaseEvent::GetAllRows` es un fallback no cableado por error o está en desuso intencional? El handler existe (`appflowy/frontend/rust-lib/flowy-database2/src/event_handler.rs:57–73`) pero nunca se registra en `appflowy/frontend/rust-lib/flowy-database2/src/event_map.rs:11–103`. Revisar `git log -p SRC/appflowy/frontend/rust-lib/flowy-database2/src/event_map.rs` para confirmar.
- **B3.F02.13** — `[NO DETERMINADO]` Confirmar que el `appflowy/frontend/rust-lib/flowy-database2/build.rs:1–6` solo afecta a la feature `dart` y no hay una generación análoga para Tauri habilitable (el bloque comentado `:9–22` lo sugiere pero está inactivo).

### B3.F02.14 (8)

- **B3.F02.14** — `[NO DETERMINADO]` ¿Por qué `appflowy/frontend/rust-lib/flowy-database2/src/entities/filter_entities/relation_filter.rs:1–22` define `RelationFilterPB { condition: i64 }` sin discriminar variantes, mientras que el resto de filtros exponen su `*FilterConditionPB`? [NO DETERMINADO]
- **B3.F02.14** — `[NO DETERMINADO]` ¿Qué BLoC Dart consume actualmente `FieldChangesetPB::desc` (`appflowy/frontend/rust-lib/flowy-database2/src/entities/field_entities.rs:399`) y `frozen` (`:400`) si `OUT/_ledger/extract/events.json::flowy-database2.UpdateField = 11` no las mapea explícitamente? [NO DETERMINADO]
- **B3.F02.14** — `[NO DETERMINADO]` ¿`appflowy/frontend/rust-lib/flowy-database2/src/entities/database_entities.rs:361–376 CustomPromptPB` es interno al crate o se cruza a Dart? No aparece en `events.json::flowy-database2` salvo en `GetDatabaseCustomPrompts = 500` como `RepeatedCustomPromptPB output` (`appflowy/frontend/rust-lib/flowy-database2/src/entities/database_entities.rs:355`). El input/salida sin handler está claro en el catálogo pero no hay consumidor Dart catalogado. [NO DETERMINADO]
- **B3.F02.14** — `[NO DETERMINADO]` ¿`appflowy/frontend/rust-lib/flowy-database2/src/entities/view_entities.rs:116–147 DidFetchRowPB` se usa fuera de la notificación `DatabaseNotification::DidFetchRow = 19`? Si sí, ¿dónde? El catálogo events.json no la referencia. [NO DETERMINADO]
- **B3.F02.14** — `[NO DETERMINADO]` Confirmar que `appflowy/frontend/rust-lib/flowy-database2/src/entities/filter_entities/util.rs:280–282` (rechazar `UpdateFilterTypePB { filter_type: Data }`) es el único invariante explícito del estado de un `Filter`; no se localizó ningún otro en `services/filter/controller.rs` dentro de esta unidad. [NO DETERMINADO]
- **B3.F02.14** — `[NO DETERMINADO]` Si las versiones futuras del proyecto renumeran `#[pb(index)]`, ¿el codegen vuelve a generar `DatabaseEventFooPB` con índices nuevos o conserva los antiguos? (No leído de `flowy-codegen`; preguntar al mantenedor). [NO DETERMINADO]
- **B3.F02.14** — `[NO DETERMINADO]` ¿`GetRow = 51` produce `OptionalRowPB` (`appflowy/frontend/rust-lib/flowy-database2/src/entities/row_entities.rs:333`) que es `Option<RowPB>`, mientras que `GetRowMeta = 55` produce `RowMetaPB` no-opcional — la diferencia semántica es que `GetRow` puede no encontrar fila? Verificado en `events.json` pero el porqué exacto del diseño no está documentado. [NO DETERMINADO]
- **B3.F02.14** — `[NO DETERMINADO]` ¿`appflowy/frontend/rust-lib/flowy-database2/src/entities/database_entities.rs:355–377 RepeatedCustomPromptPB / CustomPromptPB / CustomPromptDatabaseConfigPB` pertenecen al paquete de **AI row prompt** (ver `DatabaseEvent::GetDatabaseCustomPrompts = 500`)? Si es así, podría tener más sentido en un documento `[[F02.X.1]]` AI row. [NO DETERMINADO]

### B3.F02.15 (6)

- **B3.F02.15** — `[NO DETERMINADO]` ¿Por qué `appflowy/frontend/rust-lib/flowy-database2/tests/database/field_test/script.rs:1–111` y `appflowy/frontend/rust-lib/flowy-database2/tests/database/field_settings_test/script.rs:1–111` son idénticos y ambos declaran `pub struct DatabaseFieldTest` (`:6` en los dos)? ¿Fue un copy-paste al crear la carpeta, o la carpeta existe paraermarcar una futura suite de `field_settings`? Ninguna referencia en `src/` ni en `Cargo.toml` justifica tener dos carpetas idénticas. [NO DETERMINADO]
- **B3.F02.15** — `[NO DETERMINADO]` ¿Quién invoca `DatabaseEvent::GetAllRows = 177`? Es la única variante de las 72 sin handler registrado en `appflowy/frontend/rust-lib/flowy-database2/src/event_map.rs:11–103` y `events.json` la marca `sin_handler: true`; si el dispatcher la recibe, no hay a dónde ir. [NO DETERMINADO]
- **B3.F02.15** — `[NO DETERMINADO]` ¿Existe alguna otra batería de tests que sí recorra la frontera FFI (`dart-ffi` ↔ `lib-dispatch`) para `flowy-database2`? En el crate `event-integration-test` se registran handlers reales, pero el `AFPlugin` de `flowy-database2` solo se registra cuando `AppFlowyCore` arranca, y esta suite no lo invoca por nombre. Confirmar si algún test del workspace manda un `DatabaseEventFoo` real. [NO DETERMINADO]
- **B3.F02.15** — `[NO DETERMINADO]` ¿Por qué `DatabaseCalculationTest` abre la suscripción a `DatabaseViewChanged` (`appflowy/frontend/rust-lib/flowy-database2/tests/database/calculations_test/script.rs:28–35`) y nunca consume `CalculationValueNotification`? ¿Se abrió la suscripción esperando una sincronización determinista que se sustituyó por `sleep(3s)`? [NO DETERMINADO]
- **B3.F02.15** — `[NO DETERMINADO]` ¿`assert_group_row_count` duerme 3 s **antes** de cada aserción (`appflowy/frontend/rust-lib/flowy-database2/tests/database/group_test/script.rs:24–27`), es decir incluso cuando no hay ninguna mutación previa en ese test? ¿Es un resto de un diseño asíncrono que ya no aplica o una salvaguarda real contra la propagación del `TaskDispatcher`? [NO DETERMINADO]
- **B3.F02.15** — `[NO DETERMINADO]` ¿Existe equivalente Dart de esta batería? La afirmación de `F02.0.1.3` de que los tests viven solo en `appflowy_flutter/test/` + `integration_test/desktop_runner_*.dart` no se ha re-verificado en esta unidad, que solo cubre Rust. La confirmación corresponde a `[[B6.2]]` (`19-testing.md`). [NO DETERMINADO]

### B3.F08 (5)

- **B3.F08** — `[NO DETERMINADO]` ¿Quién emite `SearchNotification`? El enum existe en Rust y el listener existe en Dart, pero no hay ningún `NotificationBuilder` con la fuente `'Search'` en `flowy-search/**` ni en `flowy-search-pub/**`, ni una instanciación de `SearchNotificationListener` en `lib/`. Sin el commit que introdujo o eliminó esa cadena no puede decidirse si es residuo o una funcionalidad a medio migrar al canal de isolate.
- **B3.F08** — `[NO DETERMINADO]` ¿Por qué `SearchQueryPB.limit` existe y nadie lo lee? La búsqueda local usa el literal `10` y la de nube no recibe límite; no se localiza ningún punto de la cadena, ni en Dart ni en Rust, que pretenda respetarlo.
- **B3.F08** — `[NO DETERMINADO]` ¿Cuál es el `SearchType::Folder` para? La variante existe en el enum y hay un `FolderSearchHandler` comentado en el resolver, pero ningún handler la implementa; no se ha podido determinar si la búsqueda por carpetas existió y se retiró o si está planificada.
- **B3.F08** — `[NO DETERMINADO]` Reloj entre procesos: `search_id` se genera con `DateTime.now().millisecondsSinceEpoch` en el isolate de Dart y se compara con enteros en Rust. No se ha verificado que ambos lados compartan base temporal ni que el formato decimal producido en Dart sea idéntico al `parse::<i64>()` de Rust en todos los casos, dado que Dart construye el `String` con `toString()` de `int`.
- **B3.F08** — `[NO DETERMINADO]` Comportamiento exacto cuando el usuario cambia de workspace **con el diálogo abierto**: `CommandPaletteEvent.workspaceChanged` limpia el estado pero no cierra el overlay ni cancela el `search_id` en Rust; no se ha trazado si el `SearchManager` detecta el cambio (el campo `workspace_id` es un `ArcSwapOption` que se sobrescribe en el siguiente ciclo de vida) antes de que llegue un lote con vistas del workspace anterior.

### B3.F09.0 (1)

- **B3.F09.0** — Las cinco `[NO DETERMINADO]` de esta feature estántodas en `F09.1` §18 y se vuelcan en `OUT/22-preguntas-abiertas.md`:

### B3.F09.1 (5)

- **B3.F09.1** — Las cuatro preguntas marcadas `[NO DETERMINADO]` en este documento, destined a `OUT/22-preguntas-abiertas.md`:
- **B3.F09.1** — `[NO DETERMINADO]` Herramientas MCP disponibles. `MCPClientManager::tool_list` (`appflowy/frontend/rust-lib/flowy-ai/src/mcp/manager.rs:33–38`) delega íntegramente en `af_mcp::client::MCPClient::list_tools`, y el crate `af-mcp` no está declarado en `appflowy/frontend/rust-lib/flowy-ai/Cargo.toml:8–56` ni el módulo está habilitado en `appflowy/frontend/rust-lib/flowy-ai/src/lib.rs:10–11`. No es posible enumerar qué herramientas habría ni su firma; hace falta localizar el workspace donde vive `af-mcp`.
- **B3.F09.1** — `[NO DETERMINADO]` Semántica de `AIEvent::GetChatInfo` en el lado Dart. El handler real (`get_chat_info_handler`, `appflowy/frontend/rust-lib/flowy-ai/src/event_handler.rs:299–308`) devuelve `ChatInfoPB { chat_id, files }` leyendo `select_chat_metadata`, pero como el evento está registrado contra el handler no-op, el valor que recibe Dart actualmente es siempre `nil` o vacío. No se ha podido determinar si la UI depende de ese campo en `[[F09.3]]`.
- **B3.F09.1** — `[NO DETERMINADO]` Destino de `is_sync` tras un fallo de red prolongado. `AutoSyncChatService` marca `is_sync = true` incondicionalmente después de `create_question` y `create_answer` (`appflowy/frontend/rust-lib/flowy-ai/src/offline/offline_message_sync.rs:105`, `:127`, `:157`) sin esperar confirmación del servidor. Ningún consumidor de `flowy-ai` lee esa columna, y el comportamiento esperado (reintentar al recuperar la red) no aparece en ninguna parte del crate.
- **B3.F09.1** — `[NO DETERMINADO]` Efecto real de `DidUpdateChatSettings`. El catálogo `notifications.json` no encuentra ningún listener Dart para la variante 7, y `rg` sobre `lib/` lo confirma, pero no se ha inspeccionado el código generado `appflowy_backend/protobuf/flowy-ai/notification.pb.dart` (que se produce en build y no está en el repo) para descartar que algún `switch` genérico lo consuma.

### B3.F09.2 (5)

- **B3.F09.2** — `[NO DETERMINADO]` **Métrica de distancia efectiva de `vec0`.** La declaración `USING vec0(...)` no incluye `distance_metric` (`appflowy/frontend/rust-lib/flowy-sqlite-vec/migrations/001-init/up.sql:1–12`) y el crate no la nombra en ningún punto; la extensión `sqlite-vec 0.1.6` es código externo al repositorio y su valor por defecto no está fijado en el código de AppFlowy. Lo único verificable es el contrato de puntuación que lo rodea: `max_distance = 1.0 - min_score` y `score = 1.0 - distance` (`appflowy/frontend/rust-lib/flowy-sqlite-vec/src/db.rs:424`, `appflowy/frontend/rust-lib/flowy-sqlite-vec/src/db.rs:439`).
- **B3.F09.2** — `[NO DETERMINADO]` **Consumidor de `af_pending_index_collab`.** Las tres únicas APIs que escriben o borran en esa tabla (`queue_pending_indexed_collab`, `batch_queue_pending_indexed_collabs`, `delete_pending_indexed_collab`) no tienen ningún lector en el workspace: no existe ningún `SELECT` sobre `af_pending_index_collab` en `frontend/rust-lib`. No se localizó el worker que debería drenar la cola, ni si el pipeline actual la usa en absoluto (el `EmbeddingScheduler` opera directamente sobre `af_collab_embeddings`, `appflowy/frontend/rust-lib/flowy-ai/src/embeddings/scheduler.rs:225–228`).
- **B3.F09.2** — `[NO DETERMINADO]` **Estrategia de evolución del esquema.** Solo existe `001-init/up.sql`, sin `down.sql` ni migraciones posteriores. Si el modelo de embeddings cambia de dimensión o si `vec0` actualiza su formato de blob, no hay en el repo el mecanismo (ni el `up.sql` correspondiente) que migre los datos ya indexados; habría que recrear `vector.db` y reindexar.
- **B3.F09.2** — `[NO DETERMINADO]` **Dependencia declarada y no usada.** `flowy-core` declara `flowy-sqlite-vec = { workspace = true }` (`appflowy/frontend/rust-lib/flowy-core/Cargo.toml:66`) pero no se localizó ningún `use flowy_sqlite_vec` en su código Rust; la inicialización real se hace a través de `flowy_ai::embeddings::context::EmbedContext` (`appflowy/frontend/rust-lib/flowy-core/src/lib.rs:131–133`). Queda por determinar si es una dependencia vestigial o si sirve para fijar el build del crate en las releases de escritorio.
- **B3.F09.2** — `[NO DETERMINADO]` **Codificación de `content_type`.** Ni el esquema ni el crate definen el enumerado de valores de `content_type` (el pipeline escribe `0`, `appflowy/frontend/rust-lib/flowy-ai/src/embeddings/document_indexer.rs:122`, y los tests escriben `1`, `appflowy/frontend/rust-lib/flowy-sqlite-vec/tests/main.rs:376`); la columna está hoy sin interpretación.

### B3.F09.3 (5)

- **B3.F09.3** — Las cuatro preguntas marcadas `[NO DETERMINADO]` en este documento, destinadas a `OUT/22-preguntas-abiertas.md`:
- **B3.F09.3** — `[NO DETERMINADO]` Intención original del camino de adjuntos por mensaje. El código Dart está completo y bien formado desde `ChatFile.fromFilePath` hasta `metadataPBFromMetadata`, pero los tres puntos de rotura de §13 son independientes entre sí y ninguno está marcado como `TODO` ni comentado. No es posible determinar con el código disponible si se trata de una funcionalidad en construcción que se deactivate a la espera del backend, o de un residuo de una versión anterior en la que el payload sí llevaba los adjuntos. Determinarlo requiere el historial de `StreamChatPayloadPB` en `appflowy/frontend/rust-lib/flowy-ai/src/entities.rs:53–75`.
- **B3.F09.3** — `[NO DETERMINADO]` Semántica de `UpdateFileIndicator` en el widget de adjunto. `ChatInputFileBloc` y su `UploadFileIndicator` declaran tres estados —`uploading`, `finish` y `error` con su mensaje— y `ChatFilePreview` los observa con un `BlocBuilder`, pero el `build` del widget **no lee `state.uploadFileIndicator` en ninguna rama**: solo usa el `state` para reconstruir el `BlocBuilder` (`appflowy/frontend/appflowy_flutter/lib/ai/widgets/prompt_input/file_attachment_list.dart:68–131`). No hay ningún emisor de `ChatInputFileEvent.updateUploadState` en `lib/`. No se ha podido determinar si la subida debía hacerse desde Dart antes de enviar el mensaje, o si el indicador se alimentará de una notificación de Rust que todavía no existe.
- **B3.F09.3** — `[NO DETERMINADO]` Efecto real de `DidUpdateChatSettings` en la UI. `rg` no encuentra ningún `case ChatNotification.DidUpdateChatSettings` en `lib/`, y la clase `ChatSettingsManager` solo se actualiza con el retorno de su propia llamada (`appflowy/frontend/appflowy_flutter/lib/plugins/ai_chat/application/chat_settings_manager.dart:33–42`). No se ha inspeccionado el código generado `appflowy_backend/protobuf/flowy-ai/notification.pb.dart`, que se produce en build y no está en el repositorio, para descartar que algún `switch` genérico lo consuma; y no se ha revisado si el chat se abre en más de una ventana a la vez, condición que sería necesaria para que la notificación tuviera efecto observable.
- **B3.F09.3** — `[NO DETERMINADO]` Uso real de `AIEvent::ChatWithFile`. El evento existe en Rust con payload `ChatFilePB { file_path, chat_id }` y su handler `chat_file_handler` (`appflowy/frontend/rust-lib/flowy-ai/src/event_handler.rs:213`), pero `rg` no encuentra ninguna invocación `AIEventChatWithFile` en `lib/`. No está documentado si el indexado de ficheros al chat debe dispararse desde Dart al enviar el mensaje, si lo hace `stream_chat_message_handler` como efecto secundario, o si quedó sin uso cuando el contexto pasó a gestionarse por `rag_ids` a nivel de chat.

### B3.F09.4 (5)

- **B3.F09.4** — Las cuatro preguntas marcadas `[NO DETERMINADO]` en este documento, destinadas a `OUT/22-preguntas-abiertas.md`:
- **B3.F09.4** — `[NO DETERMINADO]` Efecto de un `CompleteText` fallido sobre la UI. Cuando `AppFlowyAIService.streamCompletion` devuelve `null` por un `FlowyError` en el evento FFI, los cuatro arrancantes omiten la emisión de `GeneratingAiWriterState` (`appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/ai/operations/ai_writer_cubit.dart:449–456`, `:544–548`, `:649–653`, `:724–728`) y solo queda un `Log.error` en el servicio (`appflowy/frontend/appflowy_flutter/lib/ai/service/appflowy_ai_service.dart:99–102`). No se ha determinado si el usuario permanece indefinidamente en el overlay con el prompt escrito, si algún listener global muestra un toast, o si el nodo `ai_writer` queda registrado de forma que el siguiente clic en cualquier parte del documento lo cierra. Determinarlo requiere revisar los `showToastNotification` y los handlers de `FlowyError` del arranque de la aplicación, fuera de los 10 ficheros de esta unidad.
- **B3.F09.4** — `[NO DETERMINADO]` Destino de los nodos `ai_writer` que quedan persistidos. La unidad solo cubre el ciclo completo —insertar el nodo, generar, aceptar o descartar, eliminar el nodo en `exit`—, pero `exit` no es la única forma de disappearance del nodo: si otro cliente edita el documento y borra el bloque, o si el documento se revierte a un snapshot anterior, el nodo reaparece sin cubit asociado. `register` aborta ante un nodo ya inicializado (`appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/ai/operations/ai_writer_cubit.dart:93–95`) pero no ante un nodo con `is_initialized: false`, y no se ha encontrado en `lib/` ningún barrido de nodos `ai_writer` huérfanos. No puede determinarse con el código de esta unidad si Rust los filtra al reconstruir el documento o si la UI queda con un placeholder de altura 1.0 sin overlay.
- **B3.F09.4** — `[NO DETERMINADO]` Sentido de `progress` en `GeneratingAiWriterState`. El campo existe (`appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/ai/operations/ai_writer_cubit.dart:764–778`) pero ningún constructor de los cuatro arrancantes lo rellena: todos pasan `taskId` y `markdownText`. No se ha encontrado ningún emisor de un estado de progreso en Rust para `CompleteText` —el canal de `completion.rs` solo emite `start:`, `data:`, `comment:`, `finish:` y las variantes de error—, ni ningún consumidor del campo en `lib/`. No puede determinarse si quedó preparado para un progreso por porcentaje que el backend nunca envió, o si el modelo de progreso previsto era distinto (por ejemplo, número de tokens) y se implementará más adelante.
- **B3.F09.4** — `[NO DETERMINADO]` Comportamiento de `AskAIReplacementType.plainText`. La constante `kdefaultReplacementType` vale `markdown` (`appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/ai/operations/ai_writer_entities.dart:11`), y `SaveAIResponseExtension.replace` hace un `switch` sobre ella que solo ejecuta `_replaceWithPlainText` en el valor alternativo (`appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/ai/operations/ai_writer_block_operations.dart:189–195`). El código de `_replaceWithPlainText` (`:226–257`) existe y está completo, y en su rama `replaceTexts` incluye la selección original —a diferencia de `_replaceWithMarkdown`, que inserta y borra— pero no se ha encontrado ningún punto del producto que cambie `kdefaultReplacementType`, ni ningún test que lo haga. No puede determinarse si es una opción pendiente de exponer al usuario, una variante que se active con una preferencia, o código muerto de una versión anterior en la que el reemplazo con saltos de línea simples era el comportamiento por defecto.

### B3.F10 (2)

- **B3.F10** — `[NO DETERMINADO]` Variante exacta de `FolderNotification` que dispara `FolderManager::import` vía `notify_parent_view_did_change(workspace_id, &folder, vec![parent_view_id])` (`appflowy/frontend/rust-lib/flowy-folder/src/manager.rs:2140–2143`). El helper `notify_parent_view_did_change` se llama desde varios sitios y reenvía usando el `View` actualizada — sin localizar la variante específica (probablemente `DidUpdateView` o `DidChangeChildViews`) se omite una fila precisa en §5.
- **B3.F10** — `[NO DETERMINADO]` Si la crate `appflowy_backend/dispatch/dart_event/flowy-folder/dart_event.dart` referenciada por `part of` en `appflowy/frontend/appflowy_flutter/packages/appflowy_backend/lib/dispatch/dispatch.dart:32` se almacena o no en `SRC/` durante la snapshot. La búsqueda `find SRC/...dart_event` no devuelve resultados; lo más probable es que se genere en build por el `flowy-codegen` (ver §3 `Makefile.toml` del repo raíz). Confirmar en la fase de codegen del orquestador.

### B3.F11 (3)

- **B3.F11** — `[NO DETERMINADO]` El texto visible del botón de Markdown (`LocaleKeys.shareAction_markdown`, `appflowy/frontend/appflowy_flutter/lib/plugins/shared/share/export_tab.dart:45`) anuncia "Markdown" pero el artefacto es un ZIP con un `.md` dentro y un directorio de recursos (`appflowy/frontend/appflowy_flutter/lib/shared/markdown_to_document.dart:74–95`). ¿Existe una decisión de producto documentada sobre si el bundle debe ir comprimido siempre o solo cuando hay imágenes?
- **B3.F11** — `[NO DETERMINADO]` `DocumentExportType.text` y `ShareType.text` existen en el código pero el caso del `switch` es `throw UnimplementedError()` (`appflowy/frontend/appflowy_flutter/lib/workspace/application/export/document_exporter.dart:55–56`) y ningún botón de `ExportTab` lo ofrece. ¿El formato "texto plano" está previsto como formato de exportación en el roadmap de B4.3 o es un resto de una versión anterior?
- **B3.F11** — `[NO DETERMINADO]` ¿Existe alguna prueba de integración que ejercite el popover de compartir de extremo a extremo? La búsqueda en `frontend/appflowy_flutter/test/` e `frontend/appflowy_flutter/integration_test/` no devuelve ninguna coincidencia de `ShareType`, y los `integration_test/desktop_runner_*.dart` no se pudieron correlacionar con este recorrido en esta unidad.

### B3.F12.1 (3)

- **B3.F12.1** — `[NO DETERMINADO]` ¿Cuál es la rama HTTP-only de `ShareWithUserRepository` mencionada en `appflowy/frontend/appflowy_flutter/lib/features/share_tab/data/repositories/share_with_user_repository.dart:8–9`? El comentario declara `we can still use the http api for the future` pero no existe clase HTTP en la unidad. Pendiente de cross-ref con `[[F06]]`.
- **B3.F12.1** — `[NO DETERMINADO]` ¿Existe un límite duro para el número de caracteres que acepta `FolderEvent::SharePageWithUser` antes de trocearse, o `RustShareWithUserRepositoryImpl` confía en el parser del backend? No hay validación en `appflowy/frontend/appflowy_flutter/lib/features/share_tab/data/repositories/rust_share_with_user_repository_impl.dart:70–100`.
- **B3.F12.1** — `[NO DETERMINADO]` ¿De dónde sale `WorkspaceTypePB.LocalW` cuando el workspace es de tipo `ServerW` pero el usuario aún no está autenticado? El `ShareButton` decide inicializar el `ShareTabBloc` sólo si `workspaceType != LocalW` (`appflowy/frontend/appflowy_flutter/lib/plugins/shared/share/share_button.dart:55–57`).

### B3.F12.2 (6)

- **B3.F12.2** — `[NO DETERMINADO]` ¿Cuándo se limpia la caché estática `_namespaceCache`? Sólo se leen cuatro usos en `appflowy/frontend/appflowy_flutter/lib/workspace/presentation/settings/pages/sites/settings_sites_bloc.dart:19`, `:56`, `:108` y `:109`, y ninguno la invalida al cerrar sesión; falta localizar un posible `reset` en el arranque que no se ha encontrado con `rg`.
- **B3.F12.2** — `[NO DETERMINADO]` ¿Qué devuelve `get_publish_namespace` cuando el workspace es local y por qué la página de sitios no muestra un estado de error específico? El servicio local responde `local_version_not_support()` (`appflowy/frontend/rust-lib/flowy-server/src/local_server/impls/folder.rs:166–168`) pero `_fetchPublishNamespace` colapsa el fallo a cadena vacía sin registrarlo (`appflowy/frontend/appflowy_flutter/lib/workspace/presentation/settings/pages/sites/settings_sites_bloc.dart:106–110`).
- **B3.F12.2** — `[NO DETERMINADO]` ¿Existe alguna métrica o traza que permita distinguir "no hay vistas compartidas" de "el backend no responde" en la shared section? El código colapsa ambos casos a `errorMessage` con el `msg` del `FlowyError`, sin inspeccionar el `ErrorCode`.
- **B3.F12.2** — `[NO DETERMINADO]` ¿El enlace `[[F18.2]]` (crate `collab-importer`) existe como unidad en el ledger? En `OUT/_ledger/units/` sólo figura `F18.json`; la referencia se mantiene porque el encargo la exige, pero el índice de `build_index.py` la resolverá cuando se cree esa sub-unidad.
- **B3.F12.2** — `[NO DETERMINADO]` Las variantes `SettingsSitesActionType.none`, `.fetchPublishedViews` y `.fetchUserSubscription` se declaran en `appflowy/frontend/appflowy_flutter/lib/workspace/presentation/settings/pages/sites/settings_sites_bloc.dart:339–349` pero no se emiten en ningún manejador; no queda claro si son andamiaje para código forthcoming o residuo de una versión anterior.
- **B3.F12.2** — `[NO DETERMINADO]` ¿Es intencionada la ausencia total de tests para `SettingsSitesBloc` y `SettingsSitesPage`? No existe ningún fichero bajo `test/` que los mencione, y tampoco pruebas de los dos diálogos de la página de sitios, pese a ser la única superficie que traduce `ErrorCode` del backend a mensajes de usuario.

### B3.F13.1 (4)

- **B3.F13.1** — `[NO DETERMINADO]` **Quién emite `UserNotification.DidUpdateCloudConfig`.** `AppFlowyCloudSettingBloc` espera el evento, y el catálogo `notifications.json` registra el listener, pero en los ficheros de esta unidad no aparece el punto de emisión; habría que seguir `NotificationBuilder` dentro de `flowy-user` (`services/cloud_config.rs`) y en el `cloud_service` de `flowy-server` para saber si el cambio llega desde el servidor o desde una escritura local.
- **B3.F13.1** — `[NO DETERMINADO]` **Proveedor del `GetCloudConfig` usado para la whitelist de billing.** La comparación contra `https://beta.appflowy.cloud` y `https://test.appflowy.cloud` (`appflowy/frontend/appflowy_flutter/lib/workspace/application/settings/settings_dialog_bloc.dart:112–117`) depende del `serverUrl` que devuelve el evento, pero no está documentado en este snapshot qué configuración de servidor se escribe en una build de producción ni cuándo se considera que el usuario está en la whitelist.
- **B3.F13.1** — `[NO DETERMINADO]` **Efecto real de `UserEventUpdateWorkspaceSetting` en el motor de IA.** `SettingsAIBloc` envía `disableSearchIndexing` y `aiModel` (`appflowy/frontend/appflowy_flutter/lib/workspace/application/settings/ai/settings_ai_bloc.dart:104–123`) y el handler Rust solo persiste (`appflowy/frontend/rust-lib/flowy-user/src/event_handler.rs:833`); falta localizar en `flowy-ai` o `flowy-search` quién consume el valor para reconstruir o no el índice.
- **B3.F13.1** — `[NO DETERMINADO]` **Consecuencias de `UpdateWorkspaceSetting` con `workspaceId` de un workspace no abierto.** El ajuste de IA por workspace se escribe sin comprobar que el workspace esté abierto en Rust; no está verificado si `flowy-user` lo rechaza o si el valor queda guardado sin efecto hasta la próxima apertura.

### B3.F13.2 (2)

- **B3.F13.2** — `[NO DETERMINADO]` ¿`UserEventAddWorkspaceMember` (`flowy-user.proto`, evento 37) está implementado en el lado Rust? El catálogo `OUT/_ledger/extract/events.json (evento 37, sin_handler=true)` lo marca `sin_handler: true`, pero el widget `WorkspaceMemberBloc._onAddWorkspaceMember` se basa en la respuesta del SDK Dart — ¿qué ocurre exactamente cuando se invoca? Es plausible que se confunda con `InviteWorkspaceMember` (evento 47) en algunas builds. La documentación oficial puede ayudar.
- **B3.F13.2** — `[NO DETERMINADO]` `_onInviteWorkspaceMemberByLink` en `appflowy/frontend/appflowy_flutter/lib/workspace/presentation/settings/widgets/members/workspace_member_bloc.dart:237–240` tiene cuerpo `{}` (no implementado). ¿Está pendiente de una llamada HTTP directa al AppFlowy Cloud (`MemberHttpService`) que nunca se cableó, o se delega a otro flujo?

### B3.F13.3 (1)

- **B3.F13.3** — Cuatro cuestiones quedan marcadas como `[NO DETERMINADO]` y deben acabar en `OUT/22-preguntas-abiertas.md`. **Primera**: `[NO DETERMINADO]` ¿Quién implementa el `MethodChannel('emoji_picker_flutter')` en el lado nativo Android? El invocador está en `appflowy/frontend/appflowy_flutter/lib/workspace/presentation/settings/widgets/emoji_picker/src/emoji_picker.dart:109` y `:262–279`, pero el código Kotlin/Java correspondiente no se ha localizado en el inventario. **Segunda**: `[NO DETERMINADO]` ¿Existe una implementación en iOS, macOS o Windows del mismo canal, o la rama `else` de `_getPlatformAvailableEmoji` que devuelve el mapa completo es intencionada? **Tercera**: `[NO DETERMINADO]` ¿Cuál es el valor por defecto de `FeatureFlag.membersSettings` y `FeatureFlag.planBilling` en producción? Ambos gobiernan la visibilidad de páginas del menú (`appflowy/frontend/appflowy_flutter/lib/workspace/presentation/settings/widgets/settings_menu.dart:64` y `:122`) y el catálogo `misc.json` los declara con `default: null`. **Cuarta**: `[NO DETERMINADO]` ¿Hay soporte de i18n para las cadenas internas del emoji picker? `EmojiPickerConfig` fija `'Search emoji'`, `'No recent emoji'` y `'No emoji found'` como literales en inglés (`:43`, `:48`, `:51`), mientras que `flowy_emoji_picker_config.dart` las sobrescribe con `LocaleKeys`; al no existir consumidores de esa función de fábrica, no puede determinarse si el picker se vería en otro idioma si se activase.

### B3.F14 (4)

- **B3.F14** — `[NO DETERMINADO]` **¿Cuál de los dos ficheros de inlang manda?** `appflowy/project.inlang.json` (versionado, 28 tags) y `appflowy/project.inlang/settings.json` (no versionado, 31 tags) declaran el mismo esquema pero conjuntos de idiomas distintos (§13). El `project_id` sugiere que el segundo es el estado local de un proyecto remoto, pero nada en el repo declara la precedencia, y el ledger asigna a F14 ambos ficheros sin jerarquizarlos.
- **B3.F14** — `[NO DETERMINADO]` **¿Qué clave y formato persiste `easy_localization` en `SharedPreferences`?** La app no pasa `saveLocale: false` (`appflowy/frontend/appflowy_flutter/lib/startup/tasks/app_widget.dart:74–121`), así que el paquete guarda el idioma, pero el código del paquete no está en el snapshot y el nombre de la clave no se ha podido leer. Afecta al modelo de datos de §8 y a la prioridad entre las dos fuentes de verdad.
- **B3.F14** — `[NO DETERMINADO]` **¿Qué devuelve exactamente `tr()` cuando la clave no existe en el bundle activo?** El comportamiento exacto depende de `easy_localization ^3.0.2` (no está en el snapshot): con `useFallbackTranslations: true` se espera que caiga al bundle de `en-US`, pero no se ha podido verificar si devuelve la cadena vacía, la clave literal o la del fallback. En `EasyLocalizationService` sí está verificado que devuelve `"null"` (§13), pero ese camino es propio del servicio y no de la extensión `tr()`.
- **B3.F14** — `[NO DETERMINADO]` **¿Se mantiene la paridad de los 1637 claves entre los 36 bundles?** inlang declara una regla de lint `message-lint-rule-missing-translation`, pero no hay en el repo ninguna salida de su ejecución, así que no se puede afirmar qué claves están realmente traducidas en cada idioma.

### B3.F15.1 (4)

- **B3.F15.1** — `[NO DETERMINADO]` **¿Por qué `UserNotification::DidUpdateReminder` está declarada pero nunca emitida?** La variante existe en `appflowy/frontend/rust-lib/flowy-user/src/notification.rs:22`, Dart la maneja en `appflowy/frontend/appflowy_flutter/lib/user/application/reminder/reminder_listener.dart:58`, pero `rg "DidUpdateReminder" SRC/appflowy/frontend/rust-lib` no encuentra ninguna llamada a `NotificationBuilder`. ¿Es un mecanismo planned pero no conectado, o un residuo de una versión anterior al sondeo de 30 s? De ello depende si el retraso de hasta 30 s del panel es un bug o el comportamiento previsto.
- **B3.F15.1** — `[NO DETERMINADO]` **¿Cuáles son los valores reales de debounce por crate?** El único dato disponible es que el emisor colapsa envíos en una ventana configurable; los milisegundos concretos de `flowy-user`, `flowy-folder` y `flowy-database2` no se han verificado en esta unidad (el lado Rust pertenece a `[[F15.2]]` y a `[[B1.5]]`).
- **B3.F15.1** — `[NO DETERMINADO]` **¿Existe una ruta de notificaciones del sistema operativo para los recordatorios vencidos?** `NotificationService` se inicializa y `NotificationMessage` nunca se usa [VERIFICADO], así que no hay evidencia en esta unidad de que un recordatorio vencido muestre un aviso del sistema operativo; si lo hubiera, el wiring estaría fuera de los 37 ficheros.
- **B3.F15.1** — `[NO DETERMINADO]` **¿Por qué el catálogo no recoge `SearchNotification` ni `StorageNotification` como pares equilibrados?** `SearchNotification` está en `entities/notification.rs` (ruta que el extractor no barre) y `StorageNotification` sí está en `src/notification.rs` pero su parser Dart vive fuera de `core/notification/`. Son dos causas distintas con el mismo síntoma en el resumen.

### B3.F15.2 (3)

- **B3.F15.2** — `[NO DETERMINADO]` **Qué expresiones acepta realmente `date_time_parser 0.2.0`.** El crate es externo (crates.io), está declarado como dependencia directa (`appflowy/frontend/rust-lib/flowy-date/Cargo.toml:18`) y no está vendorizado en `SRC/`, así que solo se ha podido verificar la llamada `DateParser::parse(&query)` (`appflowy/frontend/rust-lib/flowy-date/src/event_handler.rs:21`), no la gramática que implementa: ni los relativos ("next monday"), ni los idiomas que soporta, ni si exige algún dígito. De ello depende si el `unwrap` de la línea 25 es alcanzable.
- **B3.F15.2** — `[NO DETERMINADO]` **Si existe un camino previsto para `DidUpdateReminder` que no esté en el workspace.** El comentario `// TODO: implement reminder observer` (`appflowy/frontend/rust-lib/flowy-user/src/notification.rs:21`) sugiere que el observer se planifica sobre el `UserAwarenessNotifier`, y `collab-user/src/user_awareness.rs` ya tiene un parámetro `reminder_change_tx` que se pasa a `Reminders::new` (`collab:collab-user/src/user_awareness.rs:199–204`), pero en `flowy-user` se construye el awareness pasando `None` como notifier (`appflowy/frontend/rust-lib/flowy-user/src/user_manager/manager_user_awareness.rs:182`). Falta determinar si ese canal está previsto para esta variante o para otra cosa.
- **B3.F15.2** — `[NO DETERMINADO]` **Quién consume hoy `DocumentReminderAction::Update`.** La ruta existe y está cableada (`appflowy/frontend/rust-lib/flowy-core/src/deps_resolve/reminder_deps.rs:44–56`), pero el receptor la descarta; no se ha averiguado si el objetivo original era actualizar el bloque de la mención o algo del awareness.

### B3.F16.1.1 (3)

- **B3.F16.1.1** — `[NO DETERMINADO]` **Dispatch generado ausente.** Las clases Dart `FolderEventGetView`, `FolderEventUpdateView`, `UserEventGetUserProfile`, `FolderEventGetCurrentWorkspaceSetting`, `FolderEventUpdateRecentViews` y `DocumentEventOpenDocument` no existen en `SRC/`: se generan en build a partir de los derives `Flowy_Event` de Rust, y el árbol `appflowy/frontend/appflowy_flutter/lib/packages/appflowy_backend/lib/dispatch/` está vacío en este snapshot. En §4 se documentan por su **contrato Rust** (variante de `event_map.rs`, payload y PB de salida), que es verificable, pero no por su firma Dart. Queda pendiente el documento de codegen (`OUT/06-puente-flutter-rust/03-codegen.md`) para cerrar la firma exacta.
- **B3.F16.1.1** — `[NO DETERMINADO]` **Origen de `WorkspaceLatestPB` para `UserProfileBloc`.** `getIt<AuthService>().getUser()` devuelve `UserProfilePB` (`appflowy/frontend/appflowy_flutter/lib/user/application/auth/auth_service.dart:96`) y `FolderEventGetCurrentWorkspaceSetting()` devuelve `WorkspaceLatestPB`; el bloc los combina en `UserProfileState.success`. No se ha trazado qué campos de `WorkspaceLatestPB` consume realmente el `UserProfileBloc` más allá de reenviarlos como payload opaco al widget, porque esos widgets están asignados a `F16.1.2.1`.
- **B3.F16.1.1** — `[NO DETERMINADO]` **Cobertura de tests en CI.** La búsqueda en `test/` e `integration_test/` no encuentra referencias (§15), pero no se ha inspeccionado la configuración de `codemagic.yaml` ni los runners de integración para descartar que estos BLoCs se cubran de forma indirecta a través de `desktop_runner_*.dart` o de pruebas de humo que monten `MobileViewPage`.

### B3.F16.1.2.2 (4)

- **B3.F16.1.2.2** — `[NO DETERMINADO]` ¿Qué valor toma exactamente `UniversalPlatform.isMobile` en la variante web de AppFlowy? Ninguno de los nueve ficheros lo consulta directamente (la decisión se toma en `appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/slash_menu/slash_command.dart:100`, `appflowy/frontend/appflowy_flutter/lib/plugins/inline_actions/inline_actions_command.dart:57` y `appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/base/page_reference_commands.dart:117`), y la implementación de `universal_platform` es una dependencia externa no presente en `SRC/`. Pendiente de inspeccionar el paquete en `pubspec.lock`.
- **B3.F16.1.2.2** — `[NO DETERMINADO]` ¿Se admite alguna vez el menú de slash móvil en horizontal o en tablet? No hay ninguna rama por `MediaQuery` ni por `OrientationBuilder` en los nueve ficheros; toda la lógica de volteo asume el diseño vertical del parámetro `showAtTop` de `appflowy/frontend/appflowy_flutter/lib/mobile/presentation/selection_menu/mobile_selection_menu_widget.dart:183` y `:207`.
- **B3.F16.1.2.2** — `[NO DETERMINADO]` ¿Quién consume `MobileSelectionMenuStyle` además del slash menu? Solo se ha verificado `appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/slash_menu/slash_command.dart:108–110`; no está claro si `bottom_sheet/` o las toolbars de `F01.6.4` reciben una instancia de este estilo.
- **B3.F16.1.2.2** — `[NO DETERMINADO]` ¿Existe una versión *web* de estos menús? La web pasa por la rama `else` de las tres guardas de plataforma, es decir, usa la implementación de escritorio, pero no se ha encontrado en este snapshot ninguna ruta `GoRoute` condicionada a `UniversalPlatform.isWeb` que lo confirme.

### B3.F16.2 (1)

- **B3.F16.2** — **[NO DETERMINADO]** ¿Existe, en alguna rama no incluida en este snapshot del repo AppFlowy (`5cf3a36` o superior), un directorio `editor_plugins/mobile_*` que SÍ sea responsabilidad del shell móvil (p. ej. gestos globales de la `MobileEditorWrapper`, captura de teclado móvil, full-screen mode)? Si la respuesta es sí, esos ficheros deberían poblar `F16.2` y este documento se reabre con contenido real; si la respuesta es no, la corrección de scope queda como definitiva. (Esta pregunta se copiará literalmente a `OUT/22-preguntas-abiertas.md` al cerrar la unidad.)

### B3.F17 (1)

- **B3.F17** — `[NO DETERMINADO]` ¿Cuántos `HotKeyItem` se cuentan como "atajos"? El brief del usuario afirma 13 y el extractor `OUT/_ledger/extract/misc.json §5 hotkey_items` también (`total: 13`), pero el código declara 16. Documentar la discrepancia y la convención semántica (acción vs registro) en `OUT/22-preguntas-abiertas.md`.

### B3.F18 (5)

- **B3.F18** — `[NO DETERMINADO]` **Segundo macro proc-macro de `collab-derive`.** El brief de la unidad anticipa "los 2 macros proc-macro", pero `collab:collab-derive/src/lib.rs:14` solo declara `#[proc_macro_derive(Collab, attributes(collab, collab_key))]` y `rg "proc_macro" SRC/collab/collab-derive/` no devuelve un segundo `#[proc_macro*]`. ¿Se eliminó un derive en este commit (`4dfccef`) o el brief se apoyó en una versión anterior? El soporte residual de `#[yrs(ty = "...")]` (`collab:collab-derive/src/internal/ast.rs:96–126`) sugiere que existió otro derive cuyo andamiaje quedó sin uso.
- **B3.F18** — `[NO DETERMINADO]` **Número de `.proto` en `collab-entity`.** El brief indica 5 y el repositorio contiene 6 (`common`, `encoding`, `params`, `protocol`, `pubsub`, `realtime`); los seis están en el ledger de la unidad (`OUT/_ledger/units/F18.json`). ¿Se esperaba excluir `pubsub.proto` por no tener mensajes usados por el cliente? Documento los seis para no perder información.
- **B3.F18** — `[NO DETERMINADO]` **Estado de compilación del backend IndexedDB.** `IndexeddbDiskPlugin` implementa una firma de `did_init` con tres parámetros, expone un método `flush` inexistente en `CollabPlugin` y no declara `plugin_type()` (`collab:collab-plugins/src/local_storage/indexeddb/indexeddb_plugin.rs:66–120`), y llama a una API de `CollabIndexeddb` con firmas distintas de `CollabKVAction`. No es posible determinar desde el código si el target `wasm32-unknown-unknown` se compila en CI; `[[F20]]` puede confirmar si existe un job de `wasm-pack` que lo haga.
- **B3.F18** — `[NO DETERMINADO]` **Destino de `CollabConnectReachability`.** Está exportado (`collab:collab-plugins/src/lib.rs:21`) pero ninguna constructora dentro de `AppFlowy-Collab` lo instancia; el emisor de `CollabConnectState::Disconnected` debe estar en `flowy-core`/`flowy-server` (repo principal), fuera del alcance de esta fuente.
- **B3.F18** — `[NO DETERMINADO]` **Efecto real de `SinkConfig::max_merge_size`.** El campo existe (`collab:collab-plugins/src/cloud_storage/sink.rs:323`) y tiene setter (`345–348`) pero la decisión de fusión usa el literal `1024 * 4` hardcodeado en `Message::mergeable` (`collab:collab-plugins/src/cloud_storage/remote_collab.rs:522`); no se puede determinar si el config está pensado para activarse en el cliente de producción o si es residuo.

### B3.F20 (3)

- **B3.F20** — `[NO DETERMINADO]` ¿Cuál es el rol intencionado de `collab-derive`? Aparece como crate con `proc-macro = true` (`collab:collab/collab-derive/Cargo.toml:14–16`) pero no está en el workspace y no se importa desde ningún otro crate miembro. Pendiente: revisar historial de git o issue tracker para confirmar si es un proc-macro en preparación o un experimento abandonado.
- **B3.F20** — `[NO DETERMINADO]` ¿Qué versión exacta de `client-api` (AppFlowy-Cloud) es compatible con el `rev = 4dfccef` fijado en `appflowy:frontend/rust-lib/Cargo.toml:150–157`? El repo `AppFlowy-Collab` no declara tests de integración contra el cloud; la matriz de compatibilidad debe existir fuera de este snapshot.
- **B3.F20** — `[NO DETERMINADO]` ¿Por qué `collab:README.md:11` y `collab:README.md:39` declaran `collab-sync` cuando ese crate no está en el workspace ni en disco? Inconsistencia heredada de versiones anteriores; pendiente confirmar la versión en la que se eliminó.

### B3.F21 (4)

- **B3.F21** — `[NO DETERMINADO]` **Cota y validación del icono personalizado**: `saveImageToCloudStorage` distingue `isStorageLimitExceeded` y devuelve un mensaje de cuota (`appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/image/image_util.dart:62–71`), pero no se encontró ninguna verificación de **dimensiones, peso o tipo de imagen** aplicada específicamente al icono personalizado en los 11 ficheros: el único filtro es extensión/MIME en `loadImage` (`appflowy/frontend/appflowy_flutter/lib/shared/icon_emoji_picker/icon_uploader.dart:247–256`). Si existe un límite de tamaño para iconos, está en el motor de F07 o en el servidor y no es visible desde el picker.
- **B3.F21** — `[NO DETERMINADO]` **Origen del asset `icons.json`**: los SVG llevan identificadores del tipo `clip0_1068_189544` y el propio código atribuye la iconografía a Streamline (`appflowy/frontend/appflowy_flutter/lib/shared/icon_emoji_picker/icon_picker.dart:509`, `:530`), pero **no se encontró en el repo** el script que genera `assets/icons/icons.json` ni la versión exacta del set Streamline: la atribución es una etiqueta de UI, no una dependencia de build verificable.
- **B3.F21** — `[NO DETERMINADO]` **Limpieza de iconos personalizados huérfanos**: `ViewBackendService.updateViewIcon` borra el fichero anterior al sustituirlo (`appflowy/frontend/appflowy_flutter/lib/workspace/application/view/view_service.dart:210–219`), pero no se localizó el camino equivalente cuando una vista **se borra** — si existe, está en el flujo de papelera de `[[F03]]`, fuera de los 11 ficheros de esta unidad.
- **B3.F21** — `[NO DETERMINADO]` **`ImagePicker.pickMultiImage` en el uploader**: `pickImage` pide multi-selección en móvil (`appflowy/frontend/appflowy_flutter/lib/shared/icon_emoji_picker/icon_uploader.dart:283`) pero `loadImage` solo conserva `imageFiles.first` (`:261`). No queda claro en el código si el diseño es "una sola imagen por icono" (y la selección múltiple es un residuo) o si falta la parte de recorte/elección múltiple.

## B3.F00–F21 · Cierre del ledger (2026-10-20)

Preguntas recogidas de la sección 18 de los documentos escritos en el
cierre del Bloque B3. Todas están **descritivas**, no bloqueantes:
ninguna impide cerrar la fase; todas se resuelven en B6.5.

### B3.F00.0 (9)

- **B3.F00.0** — `[NO DETERMINADO]` ¿Quién consume `appflowy_backend`'s `MethodChannel('appflowy_backend').getPlatformVersion`? F00.5.1.2 §18 confirma que `lib/` no contiene ninguna referencia a `platformVersion`; el canal parece heredado del andamiaje de plugin y nunca se invoca desde la app real, pero su presencia sigue permitiendo un ataque de superficie de MethodChannel (quien controle el MethodChannel puede devolver cualquier versión).
- **B3.F00.0** — `[NO DETERMINADO]` ¿Puede alguna vez producirse `FFIStatusCode::Internal`? La variante existe en `appflowy/frontend/rust-lib/dart-ffi/src/model/ffi_response.rs:9` y el cliente Dart la maneja en `appflowy/frontend/appflowy_flutter/packages/appflowy_backend/lib/dispatch/dispatch.dart:87-90`, pero la única conversión de Rust mapea solo `Ok` y `Err` (F00.1 §18.2).
- **B3.F00.0** — `[NO DETERMINADO]` Semántica exacta de `singleCompletePort`: el helper viene del paquete externo `isolates: ^3.0.3+8` (`appflowy/frontend/appflowy_flutter/packages/appflowy_backend/pubspec.yaml:15`) y su código no está en el repositorio (F00.1 §18.3).
- **B3.F00.0** — `[NO DETERMINADO]` Destino de las 5 variantes de evento sin handler (`CreateFolderWorkspace`, `DeleteWorkspace`, `CopyLink` en `flowy-folder`; `GetAllRows` en `flowy-database2`; `AddWorkspaceMember` en `flowy-user`): ¿se registran desde otro punto del código, son residuo de una refactorización, o son invocables desde Dart y devuelven `HandleNotFound`? (F00.1 §18.4).
- **B3.F00.0** — `[NO DETERMINADO]` ¿Existe un binario o ejecutable de `flowy-codegen` que no esté declarado en `Cargo.toml`? La build A2.7 (`OUT/_ledger/pruebas/A2.7/codegen-result.json`) compiló sin error pero sin ejecutar codegen; no queda claro si hay un punto de entrada escondido.
- **B3.F00.0** — `[NO DETERMINADO]` ¿Por qué `appflowy/frontend/appflowy_flutter/packages/flowy_infra_ui/pubspec.yaml:47-49` deja comentada la declaración de Android pese a que la carpeta existe? El plugin declara cinco plataformas pero la entrada `android` está comentada.
- **B3.F00.0** — `[NO DETERMINADO]` ¿Cuál es el contrato de `mr-IN` (679 claves inaccesibles desde Dart)? ¿Se ha previsto un segundo `-s` para `mr-IN.json` o el bundle se conservará para una futura versión de pago?
- **B3.F00.0** — `[NO DETERMINADO]` ¿Qué política de release aplica para los 41 placeholders `{}` que perdieron su nombre (`am-ET`, `cs-CZ`, `id-ID`, `pl-PL`, `pt-PT`, `uk-UA`, `zh-TW`)? `appflowy/frontend/appflowy_flutter/lib/plugins/database/calendar/presentation/calendar_page.dart:481` los pasa con `namedArgs`, pero el `{}` posicional del bundle no se sustituye (F00.7.1 §13.3).
- **B3.F00.0** — `[NO DETERMINADO]` ¿Existen los 7 archivos `native/key_event.rs` que faltan en `flowy_infra_ui/ios/`? F00.5.6.2 §13 documenta que el teclado está cableado en disco pero `FlowyInfraUIPlugin.m` no lo invoca desde Dart; no queda claro si quedaron a medias o si el contrato es solo Android.

### B3.F00.3 (2)

- **B3.F00.3** — Las afirmaciones marcadas como `[NO DETERMINADO]` y otros huecos que se mantienen abiertos tras la lectura:
- **B3.F00.3** — ¿Cómo invoca exactamente el `build.rs` de un crate downstream a `flowy_codegen::dart_event::r#gen(crate_name)` y `protobuf_file::dart_gen(crate_name)`? No hay `build.rs` inventariado en esta unidad; el `lib.rs` exige que **alguien** llame `r#gen(...)` desde fuera — la conjetura es que cada `flowy-*/Cargo.toml` tenga un `build = "build.rs"` que no está en `archivos_cubiertos`. `[NO DETERMINADO]` por ausencia de evidencia en esta unidad.

### B3.F00.5.1.2 (4)

- **B3.F00.5.1.2** — `[NO DETERMINADO] F00.5.1.2-Q1` — ¿Por qué `windows/appflowy_backend_plugin_c_api.cpp` sigue en el árbol si `appflowy/frontend/appflowy_flutter/packages/appflowy_backend/windows/CMakeLists.txt:9–11` no lo compila y su `#include` de la línea 5 apunta a una cabecera inexistente? ¿Desactivación deliberada tras un cambio de plantilla, o fichero olvidado? Requiere revisar el historial git de `packages/appflowy_backend/windows/`.
- **B3.F00.5.1.2** — `[NO DETERMINADO] F00.5.1.2-Q2` — ¿Existe intención de dar soporte Linux al plugin? `appflowy/frontend/appflowy_flutter/packages/appflowy_backend/pubspec.yaml:37–47` no declara `linux`, pero `linux/Classes/binding.h` existe con una ABI obsoleta. Sin `CMakeLists.txt` ni `.cc` de plugin, el soporte no es posible tal como está; hay que decidir entre borrar la carpeta o escribir la implementación.
- **B3.F00.5.1.2** — `[NO DETERMINADO] F00.5.1.2-Q3` — ¿Debe `binding.h` declarar `store_dart_post_cobject` para mantener el contrato C completo, o se considera definitivamente obsoleto y procede eliminar los tres `binding.h` (iOS, macOS, Linux) junto con `s.public_header_files` del podspec de macOS (`appflowy/frontend/appflowy_flutter/packages/appflowy_backend/macos/appflowy_backend.podspec:17`)?
- **B3.F00.5.1.2** — `[NO DETERMINADO] F00.5.1.2-Q4` — ¿Se regenera alguna vez `example/macos/Podfile.lock`? Su contenido (`flowy_sqlite`, `path_provider_macos`) no corresponde al árbol actual, así que el ejemplo de macOS no es reproducible tal como está versionado.

### B3.F00.5.2 (1)

- **B3.F00.5.2** — `[NO DETERMINADO] F00.5.2-Q1` — ¿Por qué `appflowy/frontend/appflowy_flutter/packages/appflowy_popover/lib/src/follower.dart` está en el paquete si `PopoverCompositedTransformFollower`/`PopoverRenderFollowerLayer`/`EdgeFollowerLayer` no se usan en `appflowy_flutter/lib/`? Comprobar si hay consumo fuera de `packages/`. Asignar a revisión B1.2 (`OUT/17-grafo-dependencias.md`) o a limpieza en B2.7.

### B3.F00.5.3 (1)

- **B3.F00.5.3** — `[NO DETERMINADO] F00.5.3-Q1` — **Conteo exacto de consumidores y método dominante.** El §13.3 da estimaciones (~25 `fold`, ~8 `onFailure`, ~10 `await`, ~3 `isFailure`), pero no se ha hecho un `rg` exhaustivo sobre `lib/` (excluyendo los paquetes internos) con un patrón que distinga `FlowyResult.fold` de `Iterable.fold` y `List.fold`. El conteo fino (con desglose por feature) es la métrica que falta para dimensionar el impacto de un cambio en el paquete y para saber si `fold` de verdad copa el 60% del uso como sugiere el muestreo. Bloquea la planificación del test suite propuesto en §15.

### B3.F00.5.4 (3)

- **B3.F00.5.4** — `[NO DETERMINADO] F00.5.4-Q1` — **Volumen real de la migración de tema.** No se ha contado cuántos de los ~1.800 ficheros Dart de `lib/` siguen resolviendo color por `Theme.of(context).colorScheme` / `AFThemeExtension` en lugar de `AppFlowyTheme.of(context)`. Se sabe que 131 ficheros usan `AppFlowyTheme.of` y que `AFThemeExtension` tiene 265 referencias, pero falta el denominador clasificado por feature. Bloquea la planificación de `[[F13]]` y de `[[F00.5.5]]`.
- **B3.F00.5.4** — `[NO DETERMINADO] F00.5.4-Q2` — **Integridad del codegen.** No se ha ejecutado `script/generate_theme.dart` (AGENTS.md §11 prohíbe ejecutar los fuentes del repo analizado) y por tanto no se puede afirmar que los `primitive.dart` y `semantic.dart` versionados estén sincronizados con los tres JSON de `script/`. El único indicio es el timestamp de cabecera `2025-05-15T16:35:45.557032` (`appflowy/frontend/appflowy_flutter/packages/appflowy_ui/lib/src/theme/data/appflowy_default/primitive.dart:6`) frente a `…572178` (`appflowy/frontend/appflowy_flutter/packages/appflowy_ui/lib/src/theme/data/appflowy_default/semantic.dart:6`). Requiere un entorno con `dart run` y la dependencia `collection` resuelta (§13.6).
- **B3.F00.5.4** — `[NO DETERMINADO] F00.5.4-Q3` — **Estado legal del paquete.** `LICENSE` contiene un placeholder y `appflowy/frontend/appflowy_flutter/packages/appflowy_ui/pubspec.yaml:3` declara `version: 1.0.0` con `homepage` apuntando al repo. No se ha determinado la licencia real que aplicar ni si el paquete tiene intención de publicarse en pub.dev o de quedarse interno. Asignar a la coordinación de `F00`.

### B3.F00.5.5 (3)

- **B3.F00.5.5** — `[NO DETERMINADO] F00.5.5-Q1` — **Origen de la pista de `UniversalPlatform`.** El brief identificó `appflowy/frontend/appflowy_flutter/lib/startup/tasks/generate_router.dart:62` y un `slash_command.dart` como consumidores de `UniversalPlatform`. El primero es correcto (`appflowy/frontend/appflowy_flutter/lib/startup/tasks/generate_router.dart:60` y `:62`), pero `UniversalPlatform` se importa de `package:universal_platform`, no de `flowy_infra/platform_extension.dart`. La existencia de `slash_command.dart` no se ha verificado en este snapshot y queda pendiente confirmar el patrón compartido.
- **B3.F00.5.5** — `[NO DETERMINADO] F00.5.5-Q2` — **Cobertura real de `Insets`/`Sizes`/`Corners`.** Las 7+9+7 constantes de `lib/size.dart` no aparecen importadas en `lib/`, pero los símbolos `EdgeInsets.*`, `BorderRadius.circular(8)` y `kDefaultFontSize` sí. ¿Se sigue usando la escala vía indirecciones (re-exports en `flowy_infra_ui`) o está obsoleta? Bloquea cualquier limpieza de §13.5.
- **B3.F00.5.5** — `[NO DETERMINADO] F00.5.5-Q3` — **Estado del legado `flowy_infra_ui_platform_interface`.** `analyzer: 6.11.0` se declara en `appflowy/frontend/appflowy_flutter/packages/flowy_infra/pubspec.yaml:22` pero no tiene import directo en `appflowy/frontend/appflowy_flutter/packages/flowy_infra/lib/`. La hipótesis es que sea consumo de la interfaz de plataforma del paquete hermano, pero no se ha clonado para verificar.

### B3.F00.5.6 (2)

- **B3.F00.5.6** — `[NO DETERMINADO] F00.5.6-Q1` — **Volumen real de la migración de tema.** Al igual que `F00.5.4-Q1`, se sabe que 131 ficheros de `lib/` usan `AppFlowyTheme.of` y que `AFThemeExtension` tiene 265 referencias, pero no se ha contado cuántos de los **48 widgets** de este paquete (ni de los ~1.800 ficheros de la app) deben migrar al sistema `appflowy_ui`. La pregunta concreta que queda abierta: ¿los `Flowy*` se reemplazan por `AF*` uno a uno (y cuáles quedan), o conviven por función? Bloquea la planificación de `[[F00.5.4]]` §13.2 y `[[F13]]`.
- **B3.F00.5.6** — `[NO DETERMINADO] F00.5.6-Q2` — **Intención de `FlowyOverlay` frente al `Overlay` de Flutter.** `FlowyOverlayState.build` construye un `MaterialApp` anidado con su propio `Stack` (`appflowy/frontend/appflowy_flutter/packages/flowy_infra_ui/lib/src/flowy_overlay/flowy_overlay.dart:390–393`) y su `show`/`pop` no usan el `Navigator` real más que en `pop`. No se ha determinado si esto es un andamiaje heredado de una época en la que no había `Navigator`, o si responde a una necesidad concreta (p. ej. overlays por encima del command palette). Determinarlo decide si el sistema de overlays se puede simplificar a `showDialog`/`showGeneralDialog` estándar, lo que eliminaría de raíz los ~1.100 LOC de §13.5. Asignar a la coordinación de `F00`.

### B3.F00.5.7 (4)

- **B3.F00.5.7** — ¿Existe un hook de pre-commit o un step de CI que **ejecute** `appflowy/frontend/scripts/code_generation/flowy_icons/generate_flowy_icons.sh` antes de validar un PR? El workflow `main.yaml` solo corre `very_good_workflows/flutter_package.yml@v1` (`appflowy/frontend/appflowy_flutter/packages/flowy_svg/.github/workflows/main.yaml:23–25`), que en paquetes sin `test/` no tocaría el codegen. `[NO DETERMINADO]` — no se localizó un hook ejecutando el script.
- **B3.F00.5.7** — ¿Cuántas constantes `FlowySvgs.x` **existen** realmente en el archivo generado, deduplicadas? El conteo de 742 es la suma de `ls | wc -l`, no el número de líneas del archivo. Un mismo nombre (p. ej. `delete_m`) puede aparecer en `20x` y `24x` tras `sizeMap`. `[NO DETERMINADO]` — depende de la ejecución del codegen sobre el snapshot actual.
- **B3.F00.5.7** — ¿Existen iconos "huérfanos" en `resources/flowy_icons/` que ya no se usan en la app (referenciados por 0 ficheros de `lib/`)? Útil para podar el catálogo. `[NO DETERMINADO]` — requiere análisis cruzado.
- **B3.F00.5.7** — ¿Se ha fijado un orden de generación estable (lexicográfico) o el archivo `flowy_svgs.g.dart` cambia arbitrariamente entre ejecuciones, ensuciando el diff de PRs? El script ordena según `dirContents` (`appflowy/frontend/appflowy_flutter/packages/flowy_svg/bin/flowy_svg.dart:178–182`) que delega en `Directory.list(recursive: true).listen(...)` — orden **no garantizado**. `[NO DETERMINADO]` — habría que ejecutar el script dos veces y comparar.

### B3.F00.7.0 (4)

- **B3.F00.7.0** — **¿Cuál es la configuración de inlang canónica?** Existen `project.inlang.json` (29 idiomas) y `project.inlang/settings.json` (31 idiomas) con el mismo `pathPattern` y módulos idénticos pero listas divergentes. `[NO DETERMINADO]` cuál gana: `project.inlang/settings.json` es el nombre que usa la CLI moderna de inlang, pero `project.inlang.json` es el que el badge del README enlaza (`appflowy/README.md:96`). Nada en la raíz declara la precedencia.
- **B3.F00.7.0** — **¿Quién mantiene `android_ci.yaml.bak`?** El fichero contiene un pipeline Android completo y funcional, con emulador API 33 y `cloud_runner.dart`, pero está desactivado por extensión. `[NO DETERMINADO]` si es un trabajo en curso, un respaldo deliberado de una CI que ahora vive en Codemagic, o una reliquia. El hecho de que su `CLOUD_VERSION` (`:24`) sea dos versiones anterior sugiere que no se mantiene.
- **B3.F00.7.0** — **¿Existe realmente un job `android-workflow` en Codemagic?** `mobile_ci.yml` lo ofrece como opción (`appflowy/.github/workflows/mobile_ci.yml:17`) y `codemagic.yaml` no lo define (`appflowy/codemagic.yaml:2`). `[NO DETERMINADO]` si está definido en el panel de Codemagic (que puede tener configuración no versionada) o si la opción está rota.
- **B3.F00.7.0** — **¿Qué consume los artefactos de `prepare-windows` y `prepare-macos`?** Ambos jobs suben `appflowy_flutter.tar.gz` con nombre `${{ github.run_id }}-${{ matrix.os }}` (`appflowy/.github/actions/flutter_build/action.yml:99-102`) y ningún job del repo los descarga: `unit_test` descarga sólo `-ubuntu-latest` (`appflowy/.github/workflows/flutter_ci.yaml:193-195`) y `flutter_integration_test` tiene el literal fijado (`:65`). `[NO DETERMINADO]` si existe un consumidor externo (por ejemplo un job de la rama de releases) o si son simplemente subproductos.

### B3.F00.7.2 (1)

- **B3.F00.7.2** — Esta unidad no genera preguntas abiertas dirigidas a `22-preguntas-abiertas.md`. Todos los hallazgos materiales son asertivos (no `[NO DETERMINADO]`); las decisiones pendientes están registradas en §17 como tareas de remediación.

### B3.F00.7.3 (1)

- **B3.F00.7.3** — No hay entradas. Todos los puntos potencialmente abiertos se resolvieron con código (`[NO DETERMINADO]` no se aplica).

### B3.F00.7.4 (4)

- **B3.F00.7.4** — **¿Se ejecuta `document_sync_test.dart` deliberadamente o es un olvido?** Es el único test de ida y vuelta al servidor de toda la unidad, su cabecera documenta la intención con claridad (`appflowy/frontend/appflowy_flutter/integration_test/desktop/cloud/uncategorized/document_sync_test.dart:14-16`) y su runner simplemente no lo importa (`appflowy/frontend/appflowy_flutter/integration_test/desktop/cloud/uncategorized/uncategorized_test_runner.dart:1-2`). `[NO DETERMINADO]` si la omisión es una decisión —p. ej. porque el round-trip era intermitente— o un descuido sin registrar. `OUT/22-preguntas-abiertas.md` debe recibir esta pregunta.
- **B3.F00.7.4** — **¿Por qué `workspace_settings_test.dart` se descomentó antes de que existiera el caso de *Publish* que hoy lo cubre?** El comentario dice *"Enable it after implementing the share feature"* (`appflowy/frontend/appflowy_flutter/integration_test/desktop/cloud/workspace/workspace_test_runner.dart:13`), pero el fichero contiene tres bloques comentados dentro de sus propios tests con el motivo *"it's not allowed to update the namespace in free plan"* (`appflowy/frontend/appflowy_flutter/integration_test/desktop/cloud/workspace/workspace_settings_test.dart:129`, `:187`, `:199`). `[NO DETERMINADO]` si el bloqueo es por plan de AppFlowy-Cloud (fuera de alcance, `[[F06]]`) o por una limitación del self-hosted de la CI.
- **B3.F00.7.4** — **¿Existe un `.env.cloud.test` en algún entorno de desarrollo que no esté en el repo?** `TestEnv.afCloudUrl` lo declara con `defaultValue: 'http://localhost'` (`appflowy/frontend/appflowy_flutter/lib/env/cloud_env_test.dart:13-18`) y el fichero no está versionado ni lo crea la CI (`appflowy/.github/workflows/flutter_ci.yaml:334-340`). `[NO DETERMINADO]` si algún desarrollador apunta así la suite a un cloud remoto, o si el valor por defecto es efectivamente el único modo soportado (§13.6).
- **B3.F00.7.4** — **¿El segundo `testWidgets` de `appflowy/frontend/appflowy_flutter/integration_test/desktop/document/document_with_simple_table_test.dart:631` es un olvido o una variante deliberada?** Los dos `testWidgets` tienen el mismo nombre y cuerpos idénticos línea a línea. `[NO DETERMINADO]` si el segundo iba a probar algo distinto (por ejemplo el efecto sobre una celda en edición) y se quedó copiado (§13.8).

### B3.F00.7.5 (3)

- **B3.F00.7.5** — `appflowy/frontend/appflowy_flutter/integration_test/desktop/command_palette/command_palette_test_runner.dart:5` declara `void startTesting()` en lugar de `void main()`. ¿Cuál es la razón histórica? ¿Es un fallo pendiente de refactorizar o una decisión deliberada? `[NO DETERMINADO]`.
- **B3.F00.7.5** — `appflowy/frontend/appflowy_flutter/integration_test/desktop/reminder/document_reminder_test.dart` no se importa desde ningún runner. ¿Se ejecuta manualmente desde algún script de CI que no esté en este árbol, o es un test huérfano olvidado? `[NO DETERMINADO]`.
- **B3.F00.7.5** — `appflowy/frontend/appflowy_flutter/integration_test/desktop/sidebar/sidebar_expand_test.dart` está comentado en `appflowy/frontend/appflowy_flutter/integration_test/desktop/sidebar/sidebar_test_runner.dart:11`. ¿Debe descomentarse como parte del fix de `[[F03]]`, o es intencional mientras se refactoriza el modelo de espacios? `[NO DETERMINADO]`.

### B3.F00.7.6 (3)

- **B3.F00.7.6** — `appflowy/frontend/appflowy_flutter/test/bloc_test/view_selector_test.dart:142`, `:188`, `:222`, `:253`, `:283` usan `skip: N` dentro de `blocTest`. En el paquete `bloc_test` ese parámetro descarta los **primeros N estados** de la lista `expect`, no desactiva el caso, de modo que ninguno de los 11 tests queda sin ejecutar. `[NO DETERMINADO]` si el equipo conoce esta semántica o si 일부 de esos `skip` se Menjadi con la intención de desactivar tests; si fuera lo segundo, 5 de los 11 casos de `ViewSelectorCubit` estarían muertos sin señal visible. Debe confirmarse con una ejecución real del fichero.
- **B3.F00.7.6** — `appflowy/frontend/appflowy_flutter/test/bloc_test/lib/features/share_tab/share_tab_bloc_test.dart:14` usa `LocalShareWithUserRepositoryImpl()` real sin backend inicializado mediante `AppFlowyUnitTest.ensureInitialized()`. `[NO DETERMINADO]` si el repositorio resuelve contra FFI (y por tanto contra la `cdylib` cargada por el perfil de test) o contra un almacén en memoria, y si el test es estable en un runner limpio. Requiere ejecutar `flutter test bloc_test/lib/features/share_tab/share_tab_bloc_test.dart` y observar.
- **B3.F00.7.6** — `appflowy/frontend/appflowy_flutter/test/bloc_test/grid_test/util.dart:19–20` declara `v020GridFileName`/`v069GridFileName` para ficheros `.afdb` que existen en `assets/test/workspaces/database/`, pero su único consumidor (`makeTestGridFromImportedData`) no se invoca en ninguna parte. `[NO DETERMINADO]` si el formato `.afdb` sigue siendo soportado por `ImportTypePB.AFDatabase` en `flowy-folder` (`[[F06]]`) o si son restos de una migración ya retirada; en el segundo caso el código debería borrarse para que no sugiera cobertura inexistente.

### B3.F00.7.7 (2)

- **B3.F00.7.7** — ¿Existe algún `.env` de producción o de self-hosted en la infraestructura de release que dependa del comportamiento actual (con el bug) de `Env.enableCustomCloud`? Si existe, arreglar la precedencia de `appflowy/frontend/appflowy_flutter/lib/env/env.dart:12-16` rompería esos builds. `[NO DETERMINADO]` — los `.env` están fuera del repo (`appflowy/frontend/appflowy_flutter/.gitignore:72-73`) y no hay ningún `dev.env`-equivalent por destino.
- **B3.F00.7.7** — ¿Quién consume `Env.internalBuild` y `Env.sentryDsn` (`appflowy/frontend/appflowy_flutter/lib/env/env.dart:34-46`)? En el código Dart de esta unidad no hay ninguna lectura de ambas constantes; puede que el consumo esté en Rust (`set_env` vía `env_serde.rs`, ver `[[F00.1]]`) o que sean campos muertos. `[NO DETERMINADO]`.

### B3.F00.7.8 (5)

- **B3.F00.7.8** — `appflowy/frontend/rust-lib/covtest.rs` es un fichero de 0 bytes sin ninguna referencia en manifiestos ni código. ¿Es el resto de un harness de cobertura Rust retirado (el nombre sugiere `cov + test`), o un placeholder para una futura integración con `cargo-llvm-cov`? No hay ninguna sección `[test]` en `appflowy/frontend/rust-lib/Cargo.toml:1–36` que lo Pudiera reclamar `[NO DETERMINADO]`.
- **B3.F00.7.8** — `FolderViewObserverImpl::new` recibe `workspace_id` y lo descarta con prefijo `_` (`appflowy/frontend/rust-lib/flowy-core/src/folder_view_observer.rs:16`). Dado que el estado que envuelve (`DocumentTantivyState`) **sí** es por workspace (`appflowy/frontend/rust-lib/flowy-core/src/app_life_cycle.rs:201–203` lo crea con `workspace_id`), ¿es un resto de una versión donde el observer era global? ¿Va a usarse para particionar la indexación cuando hay varios workspaces abiertos? `[NO DETERMINADO]`.
- **B3.F00.7.8** — `appflowy/frontend/rust-lib/flowy-core/src/deps_resolve/search_deps.rs:13` tiene comentado `// let folder_handler = Arc::new(FolderSearchHandler::new(folder_indexer));` y solo registra `DocumentCloudSearchHandler` (`:14–17`). ¿Se descartó intencionadamente la búsqueda de títulos de vista (folder) a favor de la de contenido de documento, o es una funcionalidad pendiente? El `folder_manager` sigue pasándose al resolver (`:11`) aunque solo lo usa el handler de documentos `[NO DETERMINADO]`.
- **B3.F00.7.8** — `appflowy/frontend/rust-lib/flowy-core/src/deps_resolve/cloud_service_impl.rs:519–547` implementa `DatabaseAIService for ServerProvider`, pero `DatabaseDepsResolver::resolve` (`appflowy/frontend/rust-lib/flowy-core/src/deps_resolve/database_deps.rs:34–37`) inyecta como `ai_service` un `DatabaseAIServiceMiddleware` que ya envuelve al `ServerProvider`. ¿Existe algún consumidor del `impl` directo, o son 29 líneas muertas? No se ha encontrado ningún `Arc<dyn DatabaseAIService>` construido a partir de `ServerProvider` fuera del middleware `[NO DETERMINADO]`.
- **B3.F00.7.8** — `appflowy/frontend/rust-lib/flowy-core/src/deps_resolve/collab_deps.rs:183–209` marca `CollabSnapshotSql::delete` con `#[allow(dead_code)]`. ¿Se conserva para la limpieza de snapshots al borrar un documento (cuyo `delete_view` en `appflowy/frontend/rust-lib/flowy-core/src/deps_resolve/folder_deps/folder_deps_doc_impl.rs:80–92` solo limpia el índice tantivy), o es residuo de la API de snapshots? `[NO DETERMINADO]`.

### B3.F01.0 (2)

- **B3.F01.0** — **B3.F010.0-a**: ¿La fusión de undo local + undo remoto en `yrs::UndoManager` + `editor:editor/lib/src/history/undo_manager.dart` produce siempre la convergencia esperada en presencia de inserciones concurrentes? [NO DETERMINADO]
- **B3.F01.0** — **B3.F010.0-b**: ¿Existe una cota máxima razonable de notificaciones `DocumentNotification` por segundo que un `DocumentBloc` puede procesar sin saturar? [NO DETERMINADO]

### B3.F01.0.1 (2)

- **B3.F01.0.1** — **B3.F010.0.1-a**: ¿`appflowy:appflowy/frontend/appflowy_flutter/lib/shared/markdown_to_document.dart` se invoca en algún sitio fuera de los tests? El extractor `misc.json` lo lista como dependencia del workspace pero no encontré call-sites en producción. [NO DETERMINADO]
- **B3.F01.0.1** — **B3.F010.0.1-b**: ¿Cómo se reconcilia el undo local (cliente) con el undo remoto cuando hay merges CRDT en `DocumentManager::undo_handler`? [NO DETERMINADO] — el código actual delega al `yrs::UndoManager` interno del manager.

### B3.F01.0.2 (2)

- **B3.F01.0.2** — **B3.F010.0.2-a**: ¿`Document::open_with_options(DataSource::DocStateV1)` se llama alguna vez desde producción, o sólo desde tests? [NO DETERMINADO] (no encontré call-sites en `flowy-document/src/manager.rs` durante la inspección).
- **B3.F01.0.2** — **B3.F010.0.2-b**: ¿Cómo se reconcilia un `Document` cargado de LocalStorage con uno recién editado en cloud? El riesgo es divergencia en `children_map`. [NO DETERMINADO] — la respuesta está en `OUT/06-puente-flutter-rust/04-notificaciones.md` y `B6.3`.

### B3.F01.0.3.1 (1)

- **B3.F01.0.3.1** — **B3.F010.0.3.1-a**: ¿`UndoManager` local es compatible con multi-cliente (dos clientes A y B con su propio undo stack)? [NO DETERMINADO]

### B3.F01.0.3.2 (2)

- **B3.F01.0.3.2** — **B3.F010.0.3.X-a**: ¿Cuál es el ciclo de release de los plugins de bloques y cuándo entran en `standard_block_components.dart`? [NO DETERMINADO]
- **B3.F01.0.3.2** — **B3.F010.0.3.X-b**: ¿La decodificación de HTML cubre todas las etiquetas estándar o sólo un subset de Notion? [NO DETERMINADO]

### B3.F01.0.3.3 (2)

- **B3.F01.0.3.3** — **B3.F010.0.3.X-a**: ¿Cuál es el ciclo de release de los plugins de bloques y cuándo entran en `standard_block_components.dart`? [NO DETERMINADO]
- **B3.F01.0.3.3** — **B3.F010.0.3.X-b**: ¿La decodificación de HTML cubre todas las etiquetas estándar o sólo un subset de Notion? [NO DETERMINADO]

### B3.F01.0.3.4 (2)

- **B3.F01.0.3.4** — **B3.F010.0.3.X-a**: ¿Cuál es el ciclo de release de los plugins de bloques y cuándo entran en `standard_block_components.dart`? [NO DETERMINADO]
- **B3.F01.0.3.4** — **B3.F010.0.3.X-b**: ¿La decodificación de HTML cubre todas las etiquetas estándar o sólo un subset de Notion? [NO DETERMINADO]

### B3.F01.0.3.5 (2)

- **B3.F01.0.3.5** — **B3.F010.0.3.X-a**: ¿Cuál es el ciclo de release de los plugins de bloques y cuándo entran en `standard_block_components.dart`? [NO DETERMINADO]
- **B3.F01.0.3.5** — **B3.F010.0.3.X-b**: ¿La decodificación de HTML cubre todas las etiquetas estándar o sólo un subset de Notion? [NO DETERMINADO]

### B3.F01.1 (1)

- **B3.F01.1** — **B3.F011-a**: ¿Cuál es la diferencia exacta entre `ToggleListBlockKeys` y un `heading` colapsable? ¿Comparten el atributo `level`? El atributo `level` (`:29`) aparece opcional (`int?`), pero un `Heading` puro también lo tiene. ¿Se duplica lógica? [NO DETERMINADO]

### B3.F01.2 (1)

- **B3.F01.2** — **B3.F012-c**: `appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/simple_table/simple_table_widgets/_desktop_simple_table_widget.dart` vs `_mobile_*: ¿qué variables distinguen ambos comportamiento? (drag handle, popover, etc.). [NO DETERMINADO]

### B3.F01.3 (1)

- **B3.F01.3** — **B3.F013-c**: Si en el futuro se separa F01 en sub-features por bloque, ¿qué número debería absorber `image`/`video`/`file` como widgets? Posible: una sub-F "F01.media" con `image/`+`video/`+`file/` y otra sub-F "F01.embed" con `link_*`+`cover/`. [NO DETERMINADO]

### B3.F01.4 (2)

- **B3.F01.4** — **B3.F014-a**: ¿`MentionPageBloc` (`isSubPage = true`) se usa realmente para `MentionSubPageBlock`, o `SubPageBlockComponent` (F01.2) tiene su propia `BlockTransactionHandler` (`appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/sub_page/sub_page_transaction_handler.dart`) que no usa MentionPageBloc? Hay solapamiento conceptual. [NO DETERMINADO]
- **B3.F01.4** — **B3.F014-c**: ¿Hay flag legacy `mentioned_page_name` o `page_name` que se mantenga por compat con versiones anteriores? No encontrado en `appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/mention/mention_page_bloc.dart`. [NO DETERMINADO]

### B3.F01.6.0 (1)

- **B3.F01.6.0** — **B3.F016-c**: ¿Hay un registro canónico de todos los `ToolbarItem` (en `toolbar_item/builder/`, cf. línea 1 de F01.0.3.2 §3)? El `appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/slash_menu/slash_command.dart:8` define `SlashMenuItemsBuilder`, análogo de `ToolbarItemBuilder`. ¿Algún día se unifican? [NO DETERMINADO]

### B3.F01.6.1 (2)

- **B3.F01.6.1** — **B3.F016.1-b**: `paragraph_item` está duplicado implícitamente con el node default (Enter crea un paragraph). ¿Conviene eliminarlo del slash menu? [NO DETERMINADO]
- **B3.F01.6.1** — **B3.F016.1-c**: ¿El `ai_writer_item` consume créditos IA o sólo reordena prompt? [NO DETERMINADO]

### B3.F01.6.2 (1)

- **B3.F01.6.2** — **B3.F016.2-b**: ¿`appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/block_menu/block_menu_button.dart` se registra globalmente o por bloque? ¿Se solapa con el `appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/base/link_to_page_widget.dart` de F01.0.3.2? [NO DETERMINADO]

### B3.F01.6.3 (1)

- **B3.F01.6.3** — **B3.F016.3-a**: ¿`draggable_option_button` se deshabilita en mobile en favor de `mobile_block_action_buttons` (F01.6.2) o coexisten? [NO DETERMINADO]

### B3.F01.6.4 (3)

- **B3.F01.6.4** — **B3.F016.4-a**: ¿Por qué `appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/toolbar_item/custom_format_toolbar_items.dart` (plural) pero `appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/toolbar_item/custom_text_align_toolbar_item.dart` (singular)? ¿Conviene renombrar a singular? [NO DETERMINADO]
- **B3.F01.6.4** — **B3.F016.4-b**: ¿`appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/slash_menu/slash_menu_items/mobile_items.dart` reexporta items definidos en `appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/slash_menu/slash_menu_items/mobile_items.dart` (F01.6.1)? Si sí, hay duplicación. [NO DETERMINADO]
- **B3.F01.6.4** — **B3.F016.4-c**: ¿Por qué existen `appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/mobile_toolbar_v3/aa_toolbar_item.dart` y `appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/mobile_toolbar_v3/aa_toolbar_item.dart`? ¿Mismo código copy-pasted? [NO DETERMINADO]

### B3.F01.6.5 (2)

- **B3.F01.6.5** — **B3.F016.5-a**: ¿Por qué el frontmatter lista 11 archivos pero el ledger sólo 10? ¿Falta algún header `@Deprecated`? [NO DETERMINADO]
- **B3.F01.6.5** — **B3.F016.5-b**: ¿`appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/copy_and_paste/paste_from_block_link.dart` debería fusionarse con `appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/copy_and_paste/paste_from_in_app_json.dart`? [NO DETERMINADO]

### B3.F01.6.6 (2)

- **B3.F01.6.6** — **B3.F016.6-b**: ¿`search_service_v1.dart` y `v2.dart` están *deprecated* (marcado en el archivo)? ¿Conviene removerlos? [NO DETERMINADO]
- **B3.F01.6.6** — **B3.F016.6-c**: ¿Cuándo conviene mover `find_and_replace` a su propia feature (F17.x)? [NO DETERMINADO]

### B3.F01.7 (2)

- **B3.F01.7** — **B3.F017-b**: ¿`appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/page_style/_page_style_layout.dart` y `appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/page_style/_page_style_util.dart` fueron intencionalmente separados, o `appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/page_style/_page_style_layout.dart` podría sub-dividirse en `font_size_layout.dart` y `font_family_layout.dart`? [NO DETERMINADO]
- **B3.F01.7** — **B3.F017-c**: ¿El `appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/font/customize_font_toolbar_item.dart` se reusa en otros sitios fuera de la page style settings? El widget es genérico para elegir font. [NO DETERMINADO]

### B3.F01.8 (3)

- **B3.F01.8** — **B3.F018-a**: ¿`MentionTransactionHandler<T>` debería ser abstract o interface? El typedef `MentionBlockData = (Node, Map, int)` es opaco. ¿Conviene usar `record` (Dart 3+) o una clase explícita? [NO DETERMINADO]
- **B3.F01.8** — **B3.F018-b**: ¿Los parsers de markdown (custom + simple_table) se invocan en orden específico durante round-trip? El aggregate `appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/parsers/markdown_parsers.dart:1–2` exporta en orden (code, simple_table), pero ¿`DocumentMarkdownEncoder` los invoca en ese orden? [NO DETERMINADO]
- **B3.F01.8** — **B3.F018-c**: ¿`EditorMigration.migrateDocument` es idempotente? Si se invoca dos veces sobre el mismo JSON v0.1, ¿produce v0.2 estable? [NO DETERMINADO]

### B3.F01.9 (3)

- **B3.F01.9** — **B3.F019-b**: ¿`AiWriterBlock` es un `Node` de tipo `'ai_writer_block'` (custom) o reusa un `paragraph` con atributos `ai = true`? Sin docs F09.4 no se sabe. [NO DETERMINADO]
- **B3.F01.9** — **B3.F019-c**: ¿El `AiWriterCubit` consume `DocumentBloc` (F01.0.1) directamente, o un servicio wrapper para evitar coupling? [NO DETERMINADO]
- **B3.F01.9** — **B3.F019-d**: ¿El `flowy-ai` Rust implementa streaming real (SSE/WebSocket) o polling? [NO DETERMINADO]

### B3.F02.0.1.0 (1)

- **B3.F02.0.1.0** — Ninguna `[NO DETERMINADO]` en este indice.

### B3.F02.0.1.1 (4)

- **B3.F02.0.1.1** — Ninguna marcada como `[NO DETERMINADO]`. Quedan en `OUT/22-preguntas-abiertas.md` las siguientes observaciones a resolver en iteraciones posteriores:
- **B3.F02.0.1.1** — ¿Existe `appflowy/frontend/appflowy_flutter/lib/plugins/database/widgets/field/field_type_list.dart:26` (comentario `// FieldType.Time`) que previene creación de `FieldType.Time` por limitación de UI o por bug conocido? El enum Rust lo soporta (F02.0.1.2). `[NO DETERMINADO]`
- **B3.F02.0.1.1** — ¿La rama `_ => throw UnimplementedError()` en `appflowy/frontend/appflowy_flutter/lib/plugins/database/widgets/cell/card_cell_builder.dart:123` y `appflowy/frontend/appflowy_flutter/lib/plugins/database/widgets/cell/editable_cell_builder.dart:145` se sustituye por un fallback de "unsupported" cuando se añada un nuevo `FieldType` en el futuro? `[NO DETERMINADO]`
- **B3.F02.0.1.1** — ¿El typo `destop_row_detail_translate_cell.dart` se va a renombrar a `desktop_row_detail_translate_cell.dart`? `[NO DETERMINADO]`

### B3.F02.0.1.2 (1)

- **B3.F02.0.1.2** — Ninguna `[NO DETERMINADO]`. Los siguientes puntos quedan como información derivada y se confirman al cruzar con F02.0.2:

### B3.F02.0.2.0 (1)

- **B3.F02.0.2.0** — Ninguna `[NO DETERMINADO]` en este indice.

### B3.F02.0.2.1 (1)

- **B3.F02.0.2.1** — Ninguna `[NO DETERMINADO]`.

### B3.F02.0.2.2 (1)

- **B3.F02.0.2.2** — Ninguna etiqueta `[NO DETERMINADO]`. Las afirmaciones están todas verificadas con `collab:collab-database/src/...:línea` o razonadas explícitamente como `[INFERIDO]` (sección §4 / §5).

### B3.F02.0.2.3 (1)

- **B3.F02.0.2.3** — Ninguna `[NO DETERMINADO]`.

### B3.F02.1 (1)

- **B3.F02.1** — Ninguna marcada como `[NO DETERMINADO]` propia de este doc. La firma de eventos FFI en §4 está marcada `[INFERIDO]` (es un patrón consistente en todos los F02.X docs; el catálogo B2.1 los valida pero este doc no inspecciona `event_handler.rs`).

### B3.F02.10 (1)

- **B3.F02.10** — Ninguna marcada como `[NO DETERMINADO]`. Las tres etiquetadas como `[INFERIDO]` en §13.4, §13.6 y §13.8 no son bloqueantes porque su efecto ya está acotado al comportamiento actual; pueden responderse leyendo `F02.0.1` (accesos por view), `frontend/appflowy_flutter/lib/mobile/presentation/database/board/mobile_board_page.dart` (camino mobile) y `frontend/rust-lib/flowy-database2/src/services/group/controller_impls/checkbox_controller.rs` (constante `CHECK`).

### B3.F02.11 (1)

- **B3.F02.11** — Ninguna `[NO DETERMINADO]`.

### B3.F02.12 (1)

- **B3.F02.12** — Ninguna `[NO DETERMINADO]`.

### B3.F02.2 (1)

- **B3.F02.2** — Ninguna marcada como `[NO DETERMINADO]`.

### B3.F02.3 (1)

- **B3.F02.3** — ¿Por qué `observe_field_change` está comentado en `DatabaseEditor::new` (`appflowy/frontend/rust-lib/flowy-database2/src/services/database/database_editor.rs:99`)? Posiblemente reemplazado por notificaciones de `DatabaseViewEditor` (F02.8) pero no confirmado en este scope. Marcado como `[NO DETERMINADO]`.

### B3.F02.4 (1)

- **B3.F02.4** — Ninguna marcada como `[NO DETERMINADO]`. Las firmas FFI (§4) están etiquetadas `[INFERIDO]` porque este doc no cubre `event_handler.rs` (vive en F02.0.1.2).

### B3.F02.5 (1)

- **B3.F02.5** — Ninguna marcada como `[NO DETERMINADO]`. Las firmas de los eventos FFI (§4) están marcadas `[INFERIDO]` porque este doc no cubre `event_handler.rs` (vive en F02.0.1.2).

### B3.F02.6 (1)

- **B3.F02.6** — Ninguna `[NO DETERMINADO]`.

### B3.F02.7 (1)

- **B3.F02.7** — Ninguna `[NO DETERMINADO]` en esta unidad.

### B3.F02.8 (1)

- **B3.F02.8** — Ninguna `[NO DETERMINADO]`.

### B3.F02.9.0 (1)

- **B3.F02.9.0** — Ninguna `[NO DETERMINADO]`.

### B3.F02.9.1 (1)

- **B3.F02.9.1** — Ninguna `[NO DETERMINADO]`.

### B3.F02.9.2 (1)

- **B3.F02.9.2** — Ninguna `[NO DETERMINADO]`. Las cuestiones de §17 quedan como pendientes internas de la unidad y se consolidarán en `OUT/22-preguntas-abiertas.md` por el orquestador al cierre.

### B3.F03.0 (1)

- **B3.F03.0** — Consolidación de las preguntas `[NO DETERMINADO]` declaradas por los tres documentos hermanos. Se copian literalmente a `OUT/22-preguntas-abiertas.md`:

### B3.F03.1 (6)

- **B3.F03.1** — Cinco cuestiones quedan marcadas `[NO DETERMINADO]`; se copian literalmente a `OUT/22-preguntas-abiertas.md`:
- **B3.F03.1** — `[NO DETERMINADO]` — **`ViewMetaPB` no existe.** No se ha localizado ningún tipo con ese nombre en `SRC/appflowy`, `SRC/collab` ni `SRC/editor` (`grep -rl "ViewMetaPB"` → 0 ficheros). Los metadatos de la vista se componen en `ViewInfoState` (`appflowy/frontend/appflowy_flutter/lib/workspace/application/view_info/view_info_bloc.dart:114–121`) y se pintan con `ViewMetaInfo` (`appflowy/frontend/appflowy_flutter/lib/workspace/presentation/widgets/more_view_actions/widgets/view_meta_info.dart:10`). ¿Existe un PB de metadatos en una versión posterior del snapshot, o el nombre era una suposición?
- **B3.F03.1** — `[NO DETERMINADO]` — **`SpaceViewPB` y `RepeatingBloc` no existen.** Ninguno de los dos nombres aparece en el repo. Los espacios son `ViewPB` con `extra["is_space"]` (`appflowy/frontend/appflowy_flutter/lib/workspace/application/view/view_ext.dart:150–162`) y la repetición de nodos del árbol se resuelve con la recursión de `ViewItem` (`appflowy/frontend/appflowy_flutter/lib/workspace/presentation/home/menu/view/view_item.dart:340–363`) y `ViewExpanderRegistry` (`appflowy/frontend/appflowy_flutter/lib/workspace/application/view/view_bloc.dart:42`). ¿Había previsto un tipo dedicado?
- **B3.F03.1** — `[NO DETERMINADO]` — **`GetFolderSnapshots` y `ReadCurrentWorkspaceViews` tienen handler Rust y ningún consumidor Dart** (§4.1(c)). No se ha determinado si están llamados desde otro proceso (por ejemplo, la CLI de `AppFlowy-Cloud` o una tool de escritorio externa), si quedaron como andamiaje tras una refactorización, o si su ausencia es un bug. Requiere preguntar al equipo o revisar el historial de `flowy-folder`.
- **B3.F03.1** — `[NO DETERMINADO]` — **`FolderEventCreateFolderWorkspace`, `DeleteWorkspace` y `CopyLink` están declarados en Rust y sin handler** (F03.2 §4) y sin consumidor Dart. No se ha determinado si deben eliminarse del enum `FolderEvent` (lo que rompería la numeración de discriminantes y, por tanto, la compatibilidad del protocolo con clientes antiguos) o si se mantienen como reservas.
- **B3.F03.1** — `[NO DETERMINADO]` — **El destino de `view_management` no está determinado.** Los cuatro ficheros están vacíos y asignados a F04, y `ViewManagementBloc` no existe. No se ha determinado si la carpeta es un andamiaje para una feature futura (capa `features/<x>/{data,logic,presentation}`), un artefacto de una migración abandonada, o una errata en el ROADMAP que debería haber reasignado `WorkspaceBloc`/`SidebarSectionsBloc` a este árbol.

### B3.F03.2 (7)

- **B3.F03.2** — ¿Existe un suscriptor Dart real para `DidUpdateWorkspaceSetting` o el flag `latest_view` se guarda sin notificar al UI (lectura por polling)? [NO DETERMINADO]
- **B3.F03.2** — ¿Por qué `CreateFolderWorkspace`, `DeleteWorkspace` y `CopyLink` están en el enum pero `lib-dispatch` no los enruta? ¿Deprecated planificado o regresión? [NO DETERMINADO]
- **B3.F03.2** — ¿`DidDeleteView` y `DidRestoreView` deberían sustituirse/complementarse por `DidMoveViewToTrash` + un futuro `DidRestoreFromTrash`? El catálogo confirma `DidRestoreView` declarado pero no emitido. [NO DETERMINADO]
- **B3.F03.2** — ¿Quién orquesta el `ImportZipFile` (`appflowy/frontend/rust-lib/flowy-folder/src/event_handler.rs:367`) y qué consumidores Dart lo invocan? No se localizó el caller en `appflowy/frontend/appflowy_flutter/lib/` dentro del scope de esta unidad. [NO DETERMINADO]
- **B3.F03.2** — ¿Existe un suscriptor para `DidUpdateSharedViews`/`DidUpdateSharedUsers` más allá de la propia pantalla de compartición de cada vista? El BLoC Dart específico no aparece en el catálogo de blocs. [NO DETERMINADO]
- **B3.F03.2** — ¿Cómo expone `view_management/logic/view_management_bloc.dart` la API de "view management" del ROADMAP si el archivo tiene 1 byte? Confirmar cancelación. [NO DETERMINADO]
- **B3.F03.2** — ¿`PublishViewParamsPB.selected_view_ids: Option<RepeatedViewIdPB>` (subconjunto de vistas en una database a publicar, `appflowy/frontend/rust-lib/flowy-folder/src/entities/publish.rs:14–16`) está realmente ejercitado por algún caller Dart? El catálogo de blocs no muestra `PublishViewCubit`. [NO DETERMINADO]

### B3.F03.3 (3)

- **B3.F03.3** — **Tipos `ViewId`, `WorkspaceId`, `Trash`, `ViewRelation` y `ViewMetadata`**: el encargo de esta unidad los mencionaba como tipos reales, pero no existen en `SRC/collab/collab-folder/` (rev `4dfccef`). Un `rg` exhaustivo sobre todo el crate no encuentra ninguno de esos identificadores. ¿Se trata de nombres de otra versión del crate, o de otro crate del workspace `AppFlowy-Collab`? `[NO DETERMINADO]`
- **B3.F03.3** — **Punto de invocación de las migraciones del folder**: `migrate_workspace_to_view` y `get_favorite_v1` se invocan desde `flowy-folder` (`appflowy/frontend/rust-lib/flowy-folder/src/manager.rs:355`), pero no se ha determinado si existe **otro** punto de invocación (por ejemplo, en el arranque de `flowy-core` o dentro de `appflowy/frontend/rust-lib/flowy-user/src/migrations/workspace_and_favorite_v1.rs`) que aplique esas migraciones antes de abrir el folder. Hay que revisar esos ficheros para saber si existe doble vía. `[NO DETERMINADO]`
- **B3.F03.3** — **Debounce del canal `SectionChange`**: los tests usan `broadcast::channel(100)` y un timeout de 2 s (`collab:collab/collab-folder/tests/folder_test/trash_test.rs:70`). No se ha determinado si en producción el `FolderManager` aplica algún debounce o filtro antes de emitir `FolderNotification::DidUpdateTrash`, ni con qué valor. `[NO DETERMINADO]`

### B3.F04 (6)

- **B3.F04** — **`features/view_management/README.md` está vacío** (0 bytes) y los tres ficheros de `logic/` contienen una línea en blanco cada uno. ¿Existe un contrato de arquitectura para la migración de la gestión de vistas al patrón `features/<x>/{data,logic,presentation}` que se haya perdido, o el directorio es un marcador de posición abandonado? No hay forma de reconstruirlo desde el código. `[NO DETERMINADO]`
- **B3.F04** — **¿Cuál es el destino de `ViewManagementBloc`?** Si la rama nueva no se va a implementar, los 4 archivos deberían eliminarse del inventario; si se va a implementar, falta saber qué BLoC de `workspace/application/` es el que se migra y en qué orden. `[NO DETERMINADO]`
- **B3.F04** — **¿Por qué `notifications.json` no detecta los emisores de `folder_notification_builder`?** La respuesta es técnica (heurística del extractor) y se propone como corrección de `SKILL/scripts/extract_notifications.py`, pero no consta si hay más wrappers de notificación fuera de `flowy-folder` con el mismo problema. `[NO DETERMINADO]`
- **B3.F04** — **¿Deben emitirse alguna vez `DidDeleteView`, `DidRestoreView`, `DidUpdateWorkspace` y `DidCreateWorkspace`?** Los cuatro están declarados en Rust y tres tienen ramas Dart, pero ningún emisor Rust los produce en el snapshot. ¿Están planificados para un emisor cloud, o son restos de una API que se redujo? `[NO DETERMINADO]`
- **B3.F04** — **¿Cuál es el destino de `RecentViewsListener` sin `switch`?** La lectura del código no permite distinguir entre «decisión deliberada porque sólo hay un emisor» y «refactor pendiente». `[NO DETERMINADO]`
- **B3.F04** — **¿Se persisten las tabs entre sesiones en algún commit posterior?** En este snapshot no hay ninguna clave en `kv_keys.dart` para el estado de pestañas; el objetivo de producto (restauración de sesión) no es deducible del código. `[NO DETERMINADO]`

### B3.F05.0 (13)

- **B3.F05.0** — Consolidación de las preguntas `[NO DETERMINADO]` de este índice y de los dos documentos hermanos. Se copian literalmente a `OUT/22-preguntas-abiertas.md`:
- **B3.F05.0** — **`UserInfo` y `UserPB` no existen `[NO DETERMINADO]`.** El encargo asumía esos dos nombres para el tipo interno de usuario. En `5cf3a36` solo hay `UserProfile` (`appflowy/frontend/rust-lib/flowy-user-pub/src/entities.rs:146–155`) y su proyección de cable `UserProfilePB` (`appflowy/frontend/rust-lib/flowy-user/src/entities/user_profile.rs:25–45`). ¿Se documenta la entidad `UserProfile` en F05.2 §3 o se considera que su papel queda cubierto por la tabla `user_table` de B1.7?
- **B3.F05.0** — **`AuthProvider` y `SignUpMethod` no existen `[NO DETERMINADO]`.** El encargo asumía dos tipos Dart con esos nombres; no hay ninguna declaración con ellos en `appflowy_flutter/lib/`. Lo que existe es el enum generado `ProviderTypePB` (`appflowy/frontend/rust-lib/flowy-user/src/entities/auth.rs:172`), el enum de entorno `AuthenticatorType` (`appflowy/frontend/appflowy_flutter/lib/env/cloud_env.dart:112`) y la extensión `ProviderTypePBExtension` (`appflowy/frontend/appflowy_flutter/lib/user/application/auth/af_cloud_auth_service.dart:131`). ¿Se documenta el enum `ProviderTypePB` completo en [[F06]]? (F05.1 §18 #1)
- **B3.F05.0** — **Cinco `UserEvent` sin despachar desde F05.1 `[NO DETERMINADO]`.** `GetUserWorkspace` (22), `GetMemberInfo` (56), `SetCloudConfig` (13), `GetCloudConfig` (14) y `UpdateNetworkState` (24). Se necesita la unidad que los consume: `features/workspace/logic/` para los dos primeros, `startup/tasks/appflowy_cloud_task.dart` y `workspace/application/settings/` para los de cloud, `appflowy/frontend/appflowy_flutter/lib/core/network_monitor.dart:53` para el de red. ¿Alguna de esas unidades está ya asignada? (F05.1 §18 #2)
- **B3.F05.0** — **`SignUpBloc` sin pantalla `[NO DETERMINADO]`.** ¿Es funcionalidad planificada, migrada a `features/`, o código muerto que debe eliminarse? (F05.1 §18 #3)
- **B3.F05.0** — **`UserWorkspaceBloc` fuera de alcance `[NO DETERMINADO]`.** El ledger asignó el re-export de una línea pero no la implementación de `appflowy/frontend/appflowy_flutter/lib/features/workspace/logic/workspace_bloc.dart:37`. ¿Se documenta en una unidad propia bajo F05 o bajo la feature `features/workspace/`? (F05.1 §18 #4)
- **B3.F05.0** — **Alcanzabilidad de `AppFlowyCloudAuthService.signUp` `[NO DETERMINADO]`.** Lanza `UnimplementedError` pero forma parte del contrato; no se pudo determinar si algún flujo la invoca con el `AuthService` cloud registrado. (F05.1 §18 #5)
- **B3.F05.0** — **Reintento de `load_awareness_from_server` `[NO DETERMINADO]`.** ¿Cuántas veces se ejecuta por workspace cuando cambia `WorkspaceType` o se reautentica el usuario? La rama `if should_init { … } else { error }` de `appflowy/frontend/rust-lib/flowy-user/src/user_manager/manager_user_awareness.rs:293–297` no reintenta. (F05.2 §18 #1)
- **B3.F05.0** — **Reacción ante fallo de `PeriodicallyCheckBillingState` `[NO DETERMINADO]`.** ¿`notify_did_switch_plan_handler` revierte el plan o lo deja como estaba cuando el polling devuelve `response_timeout()`? (F05.2 §18 #2)
- **B3.F05.0** — **Destino de `DidUpdateReminder` `[NO DETERMINADO]`.** Si algún día se emite, ¿qué PB llevará? Solo está declarado en `appflowy/frontend/rust-lib/flowy-user/src/notification.rs:22`. (F05.2 §18 #3)
- **B3.F05.0** — **Rotación de cifrado del awareness por cambio de `device_id` `[NO DETERMINADO]`.** Parece que no se rota el cifrado de `UserAwareness`, pero no está confirmado en el código. (F05.2 §18 #4)
- **B3.F05.0** — **`subscribe_full_indexed_finish` en `flowy-user` `[NO DETERMINADO]`.** El trait se declara en `appflowy/frontend/rust-lib/flowy-user/src/event_map.rs:352` y se hereda, pero `flowy-user` no lo sobrescribe: ¿debe hacerlo o es residuo de una versión anterior? (F05.2 §14)
- **B3.F05.0** — **Recuento de BLoCs que participan en F05 `[NO DETERMINADO]`.** El encargo fijaba 20 BLoCs Dart; el barrido verificado da 24 (9 de F05.1 más 15 externos). La diferencia son los 7 BLoCs de `plugins/**` que despachan `GetUserProfile` y `GetMemberInfo`. ¿Se cuentan como parte de F05 o se dejan exclusivamente en F02 y F09.3?

### B3.F05.1 (5)

- **B3.F05.1** — **`AuthProvider` y `SignUpMethod` `[NO DETERMINADO]`.** El encargo asumía dos tipos Dart con esos nombres. Ninguno existe en `appflowy_flutter/lib/` en el snapshot `5cf3a36`. Lo que hay es el enum generado `ProviderTypePB` (`appflowy/frontend/rust-lib/flowy-user/src/entities/auth.rs:172`), el enum de entorno `AuthenticatorType` (`appflowy/frontend/appflowy_flutter/lib/env/cloud_env.dart:112`) y la extensión `ProviderTypePBExtension` (`appflowy/frontend/appflowy_flutter/lib/user/application/auth/af_cloud_auth_service.dart:131`). ¿Se documents el enum `ProviderTypePB` completo (25 variantes) en [[F06]]?
- **B3.F05.1** — **Cinco eventos del encargo no despachados por la unidad `[NO DETERMINADO]`.** `GetUserWorkspace` (discriminante 22), `GetMemberInfo` (56), `SetCloudConfig` (13), `GetCloudConfig` (14) y `UpdateNetworkState` (24) existen en `event_map.rs` pero ningún fichero de F05.1 los invoca. Se necesita la unidad que los consume: `features/workspace/logic/` para los dos primeros, `startup/tasks/appflowy_cloud_task.dart` para los de cloud, y el `NetworkListener` para el último. ¿Alguna de esas unidades está ya asignada?
- **B3.F05.1** — **`SignUpBloc` sin pantalla `[NO DETERMINADO]`.** ¿Es functionality planned, migrada a `features/`, o código muerto?
- **B3.F05.1** — **`UserWorkspaceBloc` fuera de alcance `[NO DETERMINADO]`.** ¿Se documenta en una unidad propia bajo F05 o bajo la feature `features/workspace/`? El ledger asignó el re-export de una línea pero no la implementación de 692 líneas, lo que deja un hueco.
- **B3.F05.1** — **Reachable de `AppFlowyCloudAuthService.signUp` `[NO DETERMINADO]`.** Lanza `UnimplementedError` pero es parte del contrato; no se pudo determinar si algún flujo la invoca con el `AuthService` cloud registrado.

### B3.F05.2 (4)

- **B3.F05.2** — **[NO DETERMINADO]** ¿Cuántas veces se ejecuta `manager_user_awareness::load_awareness_from_server` por workspace cuando cambian `WorkspaceType` o se reautentica el usuario? (El bloqueo `is_loading_awareness` parece idempotente pero la rama `if should_init { ... } else { error }` no reintenta).
- **B3.F05.2** — **[NO DETERMINADO]** Comportamiento exacto de `notify_did_switch_plan_handler` cuando `PeriodicallyCheckBillingState::start` retorna `Err(response_timeout())`: ¿revierte el plan o lo deja como estaba?
- **B3.F05.2** — **[NO DETERMINADO]** ¿`DidUpdateReminder` se llegará a emitir y qué PB de payload llevará? Solo `appflowy/frontend/rust-lib/flowy-user/src/notification.rs:22` lo declara.
- **B3.F05.2** — **[NO DETERMINADO]** Cómo se sincroniza `UserAwareness` cuando el dispositivo cambia `device_id`: parece que no se rota el cifrado del awareness pero no se ha confirmado.

### B3.F06 (1)

- **B3.F06** — ¿El `appflowy_cloud_task.dart` Dart (no cubierto por F06) realiza el `set_network_reachable` en respuesta al `NetworkListener`, o existe un flujo Dart adicional? `[NO DETERMINADO]`

### B3.F07 (2)

- **B3.F07** — ¿Existe un test de widget / integration que cubra `ImagePlaceholder` + `FileBlockComponent` + `UploadImageMenu`? [NO DETERMINADO] — la unidad `link_preview_test.dart` no cubre `ImagePlaceholder`. Buscar con `rg "ImagePlaceholder\|FileBlockComponent"` bajo `appflowy_flutter/test/` no devolvió ningún match.
- **B3.F07** — ¿Existe un mecanismo que mueva bloques `CustomImageType.local` a nube cuando se cambia `WorkspaceTypePB.LocalW → AppFlowy Cloud`? [NO DETERMINADO] — no encontrado en los 58 archivos ni en `ImageBlockData` (`appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/image/common.dart:35–63`).

### B3.F16.1.2.1 (4)

- **B3.F16.1.2.1** — `[NO DETERMINADO]` ¿Qué valor exacto devuelve `isAuthEnabled` y dónde se define? La condición que decide mostrar el grupo de ajustes de IA en `appflowy/frontend/appflowy_flutter/lib/mobile/presentation/home/mobile_home_setting_page.dart:100` depende de ese símbolo, que se importa transitivamente por `startup/startup.dart` pero no está declarado en ningún fichero bajo `lib/user/`. Pendiente de revisar el paquete `flowy_infra` en `pubspec.lock`.
- **B3.F16.1.2.1** — `[NO DETERMINADO]` ¿Existe realmente la clave i18n `settings_appearance_fontScaleFactor`? El test de escala la referencia (`appflowy/frontend/appflowy_flutter/integration_test/mobile/settings/scale_factor_test.dart:25`) pero no aparece entre las 1.637 claves únicas del catálogo `OUT/_ledger/extract/misc.json`, mientras que `settings_appearance_displaySize` sí aparece con dos usos. Como `lib/generated/locale_keys.g.dart` no está presente en `SRC/`, no se puede confirmar si el fichero generado aún declara ese símbolo y, por tanto, si el test llega a compilar.
- **B3.F16.1.2.1** — `[NO DETERMINADO]` ¿Quién consume `RoundUnderlineTabIndicator` desde `appflowy/frontend/appflowy_flutter/lib/mobile/presentation/home/tab/_round_underline_tab_indicator.dart:3` fuera de esta unidad? Se ha verificado su uso en `MobileSpaceTabBar` (`appflowy/frontend/appflowy_flutter/lib/mobile/presentation/home/tab/_tab_bar.dart:48`), en `NotificationTabBar` (`appflowy/frontend/appflowy_flutter/lib/workspace/presentation/notifications/widgets/notification_tab_bar.dart:62`), en `ShareMenu` (`appflowy/frontend/appflowy_flutter/lib/plugins/shared/share/share_menu.dart:113`) y en el selector de iconos (`appflowy/frontend/appflowy_flutter/lib/shared/icon_emoji_picker/tab.dart:63`), pero no está claro cuál de ellos es el propietario canónico ni si debería vivir en un paquete compartido.
- **B3.F16.1.2.1** — `[NO DETERMINADO]` ¿Existe una variante *web* del shell? Las cuatro ramas del `StatefulShellRoute` solo se registran bajo `if (UniversalPlatform.isMobile)` (`appflowy/frontend/appflowy_flutter/lib/startup/tasks/generate_router.dart:62`), pero no se ha encontrado en este snapshot ninguna rama `UniversalPlatform.isWeb` que confirme que la web usa deliberadamente el shell de escritorio (`DesktopHomeScreen`).

### B3.F16.1.2.3 (4)

- **B3.F16.1.2.3** — `[NO DETERMINADO]` ¿Existe una notificación de Rust que invalide `ViewAncestorCache`? La caché solo se refresca por lectura (`appflowy/frontend/appflowy_flutter/lib/mobile/presentation/search/view_ancestor_cache.dart:18–23`) y en la escritura no hay ninguna: renombrar o mover una vista deja la ruta de ancestros desactualizada en el sidebar y en los resultados de búsqueda hasta que el proceso se reinicie. No se ha localizado ningún `listen` sobre `FolderNotification::DidUpdateView` que llame a un método de invalidación de esta clase.
- **B3.F16.1.2.3** — `[NO DETERMINADO]` ¿Quién consume `List<SearchSummaryPB>? _mockSummary` (`appflowy/frontend/appflowy_flutter/lib/mobile/presentation/search/mobile_search_ask_ai_entrance.dart:205`)? Es una variable top-level nullable inicializada a `null` que solo se lee en dos sitios (`:25` y `:151`) y nunca se escribe dentro de la aplicación, lo que sugiere un gancho de depuración previsto para futuras pruebas, pero no hay ninguna asignación en el repositorio.
- **B3.F16.1.2.3** — `[NO DETERMINADO]` ¿Se usan `MobileCalendarScreen` y `MobileBoardScreen` en rutas distintas de `/calendar` y `/board`? Ambas pasan `ViewLayoutPB.Document` (`:25` en cada fichero) y ambas son ignoradas por `MobileViewPage`. No se ha localizado ningún otro consumidor de esas dos clases que compense el valor, así que no puede determinarse si el parámetro es un residuo o si falta una corrección.
- **B3.F16.1.2.3** — `[NO DETERMINADO]` ¿Está `MobileNotificationsScreen` (V1) planificada para una vuelta atrás, o es residuo de una migración? El router registra exclusivamente la V2 (`appflowy/frontend/appflowy_flutter/lib/startup/tasks/generate_router.dart:205–209`) y `bottomNavigationBarItemType.notification` apunta a `MobileNotificationsScreenV2.routeName` (`appflowy/frontend/appflowy_flutter/lib/mobile/presentation/mobile_bottom_navigation_bar.dart:48`), pero nada declara la V1 como obsoleta ni la marca con un `// ignore`.

### B3.F19.1 (4)

- **B3.F19.1** — ¿La lista `commandShortcutEvents` y la lista `characterShortcutEvents` de `editor:lib/src/editor/block_component/standard_block_components.dart:59–157` se prueban de forma agregada en algún test de `test/new/`? `[NO DETERMINADO]` (no se encontró un test dedicado; §13.3).
- **B3.F19.1** — ¿Qué pasa exactamente cuando un test en `test/new/block_component/` utiliza `paragraphNode(text:)` vs `paragraphNode(delta:)`? La signatura ofrece ambos (`editor/lib/src/editor/block_component/paragraph_block_component/paragraph_block_component.dart`); algunos tests usan `text:`, otros `delta:`. ¿Es por compatibilidad o por preferencia de un autor? `[NO DETERMINADO]`.
- **B3.F19.1** — ¿La heurística `await tester.pumpAndSettle(const Duration(seconds: 1))` dentro de `editor.dispose()` (`editor:test/new/infra/testable_editor.dart:180`) sigue siendo necesaria en Flutter 3.16+? El comentario enlaza a `flutter/flutter#11181` que era relevante en versiones antiguas. `[NO DETERMINADO]`.
- **B3.F19.1** — ¿Hay un patrón intencional detrás de la mezcla `test(…)/testWidgets(…)` en `service/shortcuts/character_shortcut_events/`? Por ejemplo, `editor:test/new/service/shortcuts/character_shortcut_events/format_by_wrapping_with_single_char/format_code_test.dart:13` ejecuta `testWidgets`, mientras `editor:test/new/service/shortcuts/character_shortcut_events/format_by_wrapping_with_single_char/format_italic_test.dart:13` ejecuta `test(`. Cobertura similar, motor diferente. `[NO DETERMINADO]`.

### B3.F19.2.1 (2)

- **B3.F19.2.1** — **F19.2.1-a**: ¿la ausencia de `AtLeastOneEditableNodeRule` en la app es intencionada (la regla quedó como API pública para integradores) o es una regresión? Sólo consta que `AppFlowyEditor` la admite (`editor:lib/src/editor/editor_component/service/editor.dart:232`) y que nadie la pasa `[NO DETERMINADO]`.
- **B3.F19.2.1** — **F19.2.1-b**: ¿la rama `a.path.isAncestorOf(b.path)` de `transformOperation` (`editor:lib/src/core/transform/operation.dart:261`) tiene alguna garantía externa —por ejemplo del lado del `TransactionAdapter` o del servidor— que haga seguro descartar la operación anulada? No se ha encontrado ninguna `[NO DETERMINADO]`.

### B3.F19.2.10 (2)

- **B3.F19.2.10** — **F19.2.10-a**: ¿por qué `toolbar_service_test.dart` quedó íntegramente comentado (`editor:test/service/toolbar_service_test.dart:8–233`) en lugar de portarse a `test/new/editor/toolbar/`? Sólo consta que `group('toolbar_service.dart', …)` está cerrado bajo `//` y que un `_itemWidgetForId` privado se definió para esta suite. `[NO DETERMINADO]`.
- **B3.F19.2.10** — **F19.2.10-b**: ¿hay un plan de deprecación formal de `MobileSelectionGestureDetector` (`editor:lib/src/service/selection/mobile_selection_gesture.dart:8–144`)? La búsqueda en `SRC/appflowy/frontend` devuelve 0 ocurrencias para `MobileSelectionGestureDetector`; la app usa otro mecanismo móvil (cubierto por `[[F16.1.2.2]]`). `[NO DETERMINADO]`.

### B3.F19.2.2 (1)

- **B3.F19.2.2** — **F19.2.2-a**: ¿la ausencia de test para `EditorStyle.textSpanOverlayBuilder`, `dropTargetStyle`, `disableSelectionService`, etc., se debe a que ya están cubiertos fuera de `test/customer/` (por ejemplo en `test/new/` o en tests de `plugins/` de la app) o son huecos reales? Sin contar `test/new` no se ha encontrado ningún test que los ejercite `[NO DETERMINADO]`.

### B3.F19.2.3 (2)

- **B3.F19.2.3** — **F19.2.3-a**: ¿`DeltaTextInputService` está previsto que se use por algún consumidor distinto al test de la unidad? Buscar `new DeltaTextInputService` en `SRC/editor/lib/` no devuelve ningún resultado en producción; `KeyboardServiceWidget.buildTextInputService` siempre construye `NonDeltaTextInputService` (`editor:lib/src/editor/editor_component/service/keyboard_service_widget.dart:360`). Si es API pública pensada para integradores, debería tener doc-comment que lo justifique. `[NO DETERMINADO]`.
- **B3.F19.2.3** — **F19.2.3-b**: ¿`MobileScrollService` se ha migrado a un nuevo sitio y por eso sus 4 tests quedaron comentados con un TODO genérico desde 2023? Comparando con `test/service/scroll_service_test.dart` (no en esta unidad) la cobertura puede haber sido absorbida por otra rama; el `mobile_scroll_service_test.dart` quedó como placeholder y nunca se eliminó. `[NO DETERMINADO]`.

### B3.F19.2.4 (3)

- **B3.F19.2.4** — **F19.2.4-a**: ¿`ColorExtension2` se introdujo para un consumidor futuro de serialización (por ejemplo, un serializador CSS para el exportador HTML que vive en `editor:lib/src/plugins/html/`)? `editor:lib/src/plugins/html/encoder/delta_html_encoder.dart:45–150` ya usa `attributes.color`/`attributes.backgroundColor` pero toma `String` directamente, no `Color`. `[NO DETERMINADO]`.
- **B3.F19.2.4** — **F19.2.4-b**: ¿la rama "scheme vacío" de `safeLaunchUrl` (`editor:lib/src/extensions/url_launcher_extension.dart:9` — anteponer `'http://$href'` si `uri.scheme.isEmpty`) es intencional o un *workaround* para un bug específico? El test no la cubre. `[NO DETERMINADO]`.
- **B3.F19.2.4** — **F19.2.4-c**: ¿`TextNodeExtension::` (el grupo vacío de `editor:test/extensions/text_node_extensions_test.dart:4`) fue renombrado a `NodeExtensions` y se migró a `editor:lib/src/extensions/node_extensions.dart`, dejando el fichero huérfano, o desapareció por otro motivo? No hay rastro en el repo de una migración similar. `[NO DETERMINADO]`.

### B3.F19.2.5 (1)

- **B3.F19.2.5** — **F19.2.5-a**: ¿el handler de `SystemChannels.platform` debería instalar `case "Clipboard.hasStrings"` para futuros consumidores? El servicio `Clipboard` de Flutter lo expone, pero ni `AppFlowyClipboard` (sólo usa `getData(kTextPlain)` y `setData(ClipboardData)`) ni los tests lo piden hoy. Una búsqueda `rg 'Clipboard.kHtml|kTextPlain'` sobre `editor/lib` confirma que sólo aparecen `setData`/`getData(Clipboard.kTextPlain)` (`editor:lib/src/infra/clipboard.dart:29`, `:41`) `[NO DETERMINADO]`.

### B3.F19.2.6 (2)

- **B3.F19.2.6** — **F19.2.6-a**: ¿`test/legacy/` es una carpeta consciously mantenida —con la intención de conservar pruebas de comportamiento histórico del editor v0, aunque sus fixtures ya no existan— o es simplemente un directorio donde se aparcaron tests que quedaron rotos durante el refactor del selection menu (`1b1fb25e`, 2022-08-19)? No hay ninguna nota en `CONTRIBUTING`, `CHANGELOG` ni en el propio repo que lo declare `[NO DETERMINADO]`.
- **B3.F19.2.6** — **F19.2.6-b**: ¿existe un plan de deprecación para `DocumentV0`/`NodeV0` (`editor:lib/src/core/document/deprecated/document.dart:8–13`) o son un resto que nadie ha borrado en tres años? Están exportados por el barrel, lo que impide saber si algún integrador externo los usa `[NO DETERMINADO]`.

### B3.F19.2.7 (1)

- **B3.F19.2.7** — Ninguna que califique como `[NO DETERMINADO]`: todas las afirmaciones relevantes (incluida la no-utilización por la app) son de código directamente verificable con `rg`.

### B3.F19.2.8 (1)

- **B3.F19.2.8** — **F19.2.8-a**: ¿se ha activado alguna vez `DocumentHTMLDecoder.enableColorParse = false` por el flujo de la app, o es un interruptor pensado para tests `html_document_test.dart` que nunca se usa en producción? El campo es público (`editor:lib/src/plugins/html/html_document_decoder.dart:12`) pero ningún test lo cambia `[NO DETERMINADO]`.

### B3.F19.2.9 (2)

- **B3.F19.2.9** — **F19.2.9-a**: ¿La existencia de `ToolbarItemWidget` en `editor:lib/src/render/toolbar/toolbar_item_widget.dart` es residuo de una migración previa (cuando la app no proveía `ToolbarItem.builder` propios) o es API pública intencional que aún no se ha consumido? El hecho de que `editor:test/service/toolbar_service_test.dart:236` declare la función `_itemWidgetForId` comentado sugiere migración a medio terminar `[NO DETERMINADO]`.
- **B3.F19.2.9** — **F19.2.9-b**: ¿Hay voluntad de cubrir sistemáticamente el widget `FloatingToolbarWidget` (no sólo `_computeActiveItems` aislado) con tests de render, dado que la app lo usa como entrada (`appflowy:frontend/appflowy_flutter/lib/plugins/document/presentation/editor_page.dart:444`) y `editor:lib/src/editor/toolbar/desktop/floating_toolbar_widget.dart:104–117` sí podría probarse con un `List<ToolbarItem>` con `builder` reales? `[NO DETERMINADO]`.

### B3.F19.4 (2)

- **B3.F19.4** — **F19.4-a**: ¿el conjunto de 23 `.arb` se mantiene por historical para el editor como librería independiente, o es un resto de cuando el editor servía a la UI de AppFlowy? Sólo consta que la app lo consume parcialmente (67 getters, sobre todo `pt-BR`) y que nunca registra el delegate `[NO DETERMINADO]`.
- **B3.F19.4** — **F19.4-b**: ¿qué mecanismo decide el comportamiento de `Intl.message` cuando el locale activo no tiene la clave — repliegue al literal inglés de `l10n.dart`, texto vacío, o excepción? Requiere ejecutar el runtime o leer `package:intl`; en esta unidad sólo se ha deducido el primer caso `[NO DETERMINADO]`.

### B3.F19.5 (5)

- **B3.F19.5** — **¿Existe `test/infra/test_editor.dart` en otra rama o fue eliminado sin actualizar la documentación?** Estado: `[NO DETERMINADO]`. Evidencia: `ls SRC/editor/test/infra/` devuelve sólo tres ficheros (`clipboard_test.dart`, `flowy_svg_test.dart`, `log_test.dart`), mientras `editor:documentation/testing.md:117` lo importa. El helper real hoy es `test/new/infra/testable_editor.dart`, usado por `editor:test/l10n/l10n_test.dart:3`. Si la doc se actualizó tras `470c4e7` y el snapshot A1.1 lo perdió, el orquestador de revisiones debe reconsultar la rama `main` del editor upstream y emitir un patch a `documentation/testing.md`.
- **B3.F19.5** — **¿El job `desktop` cubre iOS Simulator o Android Emulator en algún nivel?** Estado: `[NO DETERMINADO]`. La matriz declarada en `editor:.github/workflows/test.yml` (sección `strategy.matrix.os`, líneas 25 a 27) sólo enumera `macos-latest, ubuntu-latest`. Los tests móviles (`test/mobile/**`) se ejecutan, pero se asume que corren con bindings host; la CI real del simulador queda en `[[F00.7.0]]`. Una verificación útil sería descargar el log de un job real y contar cuántos `mobile/` se ejecutan vs. cuántos se saltan.
- **B3.F19.5** — **¿Cuál es la política para subir versión en `pubspec.yaml` vs. cortar rama en `main`/`stable`?** Estado: `[NO DETERMINADO]**. El `editor:pubspec.yaml:3` declara 5.2.0 y el CHANGELOG arranca con 5.2.0; los triggers de CI son `main` y `stable` (sección `on.push.branches` y `on.pull_request.branches` en `editor:.github/workflows/test.yml`, líneas 3 a 13). El flujo concreto de release (¿tag? ¿merge? cherry-pick desde `main` a `stable`?) no está en este repo y debe consultarse en `[[F00.7.2]]`. La existencia de dos ramas dispara el flujo de release, pero el cómo subir la línea de versión permanece implícito.
- **B3.F19.5** — **¿`flutter test --coverage` falla de forma dura si algún test `mobile/` requiere un binding que sólo existe en el simulador?** Estado: `[NO DETERMINADO]`. Sólo se observa que el job corre; el log completo de una corrida real validaría si los 18 tests `mobile/` se ejecutan o se saltan. El patrón mobile-host es fuente habitual de falsos positivos (test "pasa" porque su binding no se carga), por lo que auditar la cobertura de `lib/src/editor/editor_component/service/shortcuts/` (consumida por mobile) ayudaría a descartar regresiones silenciosas.
- **B3.F19.5** — **¿Hay política explícita para cuándo fusionar PRs a `stable`?** Estado: `[NO DETERMINADO]`. La rama `stable` aparece sólo como destino de PRs y push en el workflow (en `editor:.github/workflows/test.yml`, secciones `on.push.branches` y `on.pull_request.branches` hacia main/stable en líneas 3 a 13), pero no hay docs internas en este repo que expliquen su rol frente a `main` (¿backports? ¿releases ya publicadas?).

## B3.F00–F21 · Cierre del ledger (2026-10-20)

Preguntas recogidas de la sección 18 de los documentos escritos en el
cierre del Bloque B3. Todas están **descritivas**, no bloqueantes:
ninguna impide cerrar la fase; todas se resuelven en B6.5.

### B4.0 (2)

- **B4.0** — `[VERIFICADO]` para las dieciséis familias; el [NO DETERMINADO] más importante es la cuantificación del porcentaje exacto de pérdida del PDF al renderizar `bg_color`/`font_color` (trazado a `22-preguntas-abiertas.md` pregunta P-XX-002 de `B4.13 §4.3`).
- **B4.0** — Las tres longitudes **coexisten** sin reconciliación: la divergencia Dart 120 vs Rust 50 está documentada como `[NO DETERMINADO]` y trazada a `OUT/22-preguntas-abiertas.md` (pregunta P-XX-005 en `B4.13 §4.3`).

### B4.1 (1)

- **B4.1** — [NO DETERMINADO] No existe ningún test que ejercite la rama `path == null` del `switch` de `appflowy/frontend/appflowy_flutter/lib/workspace/application/export/document_exporter.dart:50–54` ni el manejo de `Exception('Delta is null')` desde el call site real; los cuatro tests de `appflowy/frontend/appflowy_flutter/test/unit_test/markdown/markdown_parser_test.dart:10–96` solo llaman a `customDocumentToMarkdown(document)` sin `path`.

### B4.11 (1)

- **B4.11** — [NO DETERMINADO] Para la rama Cloud no es posible conocer las pérdidas exactas — AppFlowy-Cloud es privado y no hay registro de su mapeo en este repo.

### B4.13 (3)

- **B4.13** — Si `EditorMigration.migrateCoverIfNeeded` se invoca solo desde el widget de portada y no desde el import, una cover migrada por `.afdoc` **no** sobrevive sin un click explícito del usuario. `[NO DETERMINADO]` para B4.10 round-trip, trazado a `OUT/22-preguntas-abiertas.md` pregunta P-XX-003.
- **B4.13** — El porcentaje exacto de pérdida del PDF al renderizar un delta con `bg_color`/`font_color` no es cuantificable desde las fuentes (la mayoría están en `package:pdf`, fuera de las tres fuentes de esta skill). `[NO DETERMINADO]` para B4.7, trazado a `OUT/22-preguntas-abiertas.md` pregunta P-XX-004.
- **B4.13** — Catálogo consolidado de los seis **categorías de error** que el motor presenta al usuario. Las celdas vacías del §8 del documento B4 correspondiente se documentan como `[NO DETERMINADO]` trazadas a `OUT/22-preguntas-abiertas.md`.

### B4.2 (1)

- **B4.2** — **Atributos simples no mapeados.** Si un `TextInsert` tiene **exactamente un** atributo cuya clave no está en `keyToTag`, la expresión `keyToTag[attributes.keys.first]` devuelve `null` y ese `null` se pasa a `dom.Element.tag(...)` (`editor:lib/src/plugins/html/encoder/delta_html_encoder.dart:65–66`). Qué emite exactamente el paquete `html` ante un nombre de etiqueta nulo no es determinable desde las fuentes de esta skill `[NO DETERMINADO]`, y ningún test cubre el caso `[VERIFICADO: por ausencia en editor:test/plugins/html/delta_encoder_test.dart]`.

### B4.4 (1)

- **B4.4** — **`MentionBlockKeys.type != 'page'` con un `page_id` que no sea válido.** Se conserva como atributo del Delta, pero `Document.fromJson` no filtra nada; un JSON con `attributes.mention.page_id == null` se acepta y puede romper consumidores posteriores `[NO DETERMINADO]`.

## Harvest automático · 2026-10-21 · 39 preguntas

Preguntas recogidas automáticamente de las secciones de `[NO DETERMINADO]` de los documentos de `OUT/`. Recogidas por `SKILL/scripts/harvest_open_questions.py`; el bloque es idempotente (una entrada ya escrita no se vuelve a copiar).

### B3.F00.0 (1)

- **B3.F00.0** — Lo marcado como [NO DETERMINADO] que va a 22-preguntas-abiertas.md.

### B3.F02.14 (1)

- **B3.F02.14** — `[NO DETERMINADO]` ¿`appflowy/frontend/rust-lib/flowy-database2/src/entities/database_entities.rs:355–377 RepeatedCustomPromptPB / CustomPromptPB / CustomPromptDatabaseConfigPB` pertenecen al paquete de **AI row prompt** (ver `DatabaseEvent::GetDatabaseCustomPrompts = 500`)? Si es así, podría tener más sentido en un documento de AI row. [NO DETERMINADO]

### B4.13 (1)

- **B4.13** — Catálogo consolidado de los seis **categorías de error** que el motor presenta al usuario. Las celdas vacías del la §8 del documento B4 correspondiente correspondiente se documentan como `[NO DETERMINADO]` trazadas a `OUT/22-preguntas-abiertas.md`.

### B5.12 (1)

- **B5.12** — `[NO DETERMINADO]`: el orden de los `encoder_version` V0/V1/V2 no está mapeado exhaustivamente (F18).

### B5.2 (1)

- **B5.2** — `[NO DETERMINADO]` (resuelto en B6.5): ¿existe `flowy-user/tests/sign_in_with_password_test.rs`? **No.** El crate `flowy-user` no tiene directorio `tests/` en este snapshot: solo `Cargo.toml`, `Flowy.toml`, `build.rs` y `src/`. `rg 'sign_in_with_password_test' SRC/` devuelve 0 coincidencias. Es decir, el login con contraseña de `flowy-user` **no tiene test de integración por evento**, lo que es una laguna de cobertura de F05 y no una ubicación desconocida. Registrado en `[[B6.2]]` como hueco de cobertura.

### B5.3 (1)

- **B5.3** — `[NO DETERMINADO]`: ruta exacta del `RouterConfig` que escucha `AppBloc.state.currentWorkspaceId`.

### B5.4 (1)

- **B5.4** — `[NO DETERMINADO]`: línea exacta de la tabla `collab_snapshot` en `flowy-sqlite/src/schema.rs` (F01.0.1 lo cubre).

### B5.5 (1)

- **B5.5** — `[NO DETERMINADO]`: si dos clientes escriben a la vez y ambos tienen colisiones locales, el `state_vector` es el mismo; ¿cuál gana?

### B5.9 (1)

- **B5.9** — `[NO DETERMINADO]`: ¿los chunks llegan tal cual del backend o se pre-buferean? El código muestra `stream_buffer` pero no hay `flush` explícito.

### B6.1 (15)

- **B6.1** — Ambos ficheros existen y son válidos, pero **no se ha encontrado en el repo ninguna declaración de build hook que los active**: no hay sección `hooks:`, ni `native_assets`, ni referencia a `cargokit` en `appflowy_flutter/pubspec.yaml` ni en los `pubspec.yaml` de `packages/`, y `appflowy_flutter/build.yaml` tiene 0 bytes. La búsqueda ha sido textual sobre todo el árbol con los términos `cargokit`, `hooks:` y `native_assets`, sin resultados. **[NO DETERMINADO]** ¿Quién lee `cargokit_options.yaml` en este snapshot, y con qué criterio decide usar binarios precompilados en lugar de compilar `dart-ffi`? ¿Está `distribute_options.yaml` conectado a `flutter_distribute`, o es andamiaje heredado de una versión anterior? Pregunta para `22-preguntas-abiertas.md`.
- **B6.1** — Se citan por nombre, nunca por valor: `secrets.TOKEN` (`appflowy/.github/workflows/build_command.yml:39`), `secrets.CODEMAGIC_API_TOKEN` (`appflowy/.github/workflows/mobile_ci.yml:20`), `secrets.RELEASE_SLACK_WEBHOOK` (`appflowy/.github/workflows/mobile_ci.yml:83`, `appflowy/.github/workflows/release.yml:505`), `secrets.DISCORD` (`appflowy/.github/workflows/release.yml:520`), `secrets.DISCORD_WEBHOOK` (`appflowy/.github/workflows/translation_notify.yml:14`), `secrets.DOCKER_HUB_USERNAME` y `secrets.DOCKER_HUB_ACCESS_TOKEN` (`appflowy/.github/workflows/release.yml:473–474`), y los seis de firma de macOS: `MACOS_CERTIFICATE`, `MACOS_CERTIFICATE_PWD`, `MACOS_CODESIGN_ID`, `MACOS_NOTARY_USER`, `MACOS_TEAM_ID`, `MACOS_NOTARY_PWD` (`appflowy/.github/workflows/release.yml:172–203`, repetidos en `appflowy/.github/workflows/release.yml:277–301`). **[NO DETERMINADO]** Cuáles existen realmente, con qué ámbito y con qué rotación. No es deducible del repositorio.
- **B6.1** — A diferencia de macOS, **no existe ningún paso de firma, provisioning profile ni notarización de iOS en el repositorio**. `codemagic.yaml` compila para el simulador (`aarch64-apple-ios-sim`), `ios_ci.yaml` también, y `flutter.toml` define `flutter build ipa --split-debug-info=./ --obfuscate` (`appflowy/frontend/scripts/makefile/flutter.toml:249–255`) como única ruta de empaquetado iOS, pero ningún workflow del repo la invoca. **[NO DETERMINADO]** Dónde se firma el `.ipa` y con qué certificados; si ocurre dentro de Codemagic bajo un workflow no declarado en este `codemagic.yaml`, o en el repositorio externo `AppFlowy-Builder`. El hecho de que `codemagic.yaml` declare `build/ios/ipa/*.ipa` como artefacto (`appflowy/codemagic.yaml:37`) sugiere que la expectativa es que Codemagic lo produzca, pero ningún paso visible lo hace.
- **B6.1** — El workflow reenvía a `https://api.github.com/repos/AppFlowy-IO/AppFlowy-Builder/actions/workflows/$platform.yaml/dispatches` (`appflowy/.github/workflows/build_command.yml:41`) con `ref: "main"` y `repo: "LucasXu0/AppFlowy"` hardcodeados (`appflowy/.github/workflows/build_command.yml:26–27`). `AppFlowy-Builder` no está entre las tres fuentes clonadas (`OUT/_ledger/sources.json` sólo contiene `appflowy`, `collab` y `editor`). **[NO DETERMINADO]** Qué workflows contiene ese repositorio, qué artefactos produce y qué relación tiene con `release.yml`. Nótese además que el `ref` que se envía es siempre `main`, mientras que `$branch` se manda como input `branch` — el dispatch apunta al workflow de `main` con una rama distinta como parámetro, combinación que no se puede validar desde aquí.
- **B6.1** — **Reversión no garantizada del `pubspec.yaml`.** `run` en `build_flowy.dart` comenta, construye y descomenta sin `try/finally` (`appflowy/frontend/scripts/flutter_release_build/tool.dart:115–121`); un fallo de build deja los assets de test declarados como comentados y el árbol sucio. El mismo patrón aparece en `set-app-version` y en el white-label de fuentes.
- **B6.1** — **Mutación de manifiesto Rust sin transacción.** `setup-crate-type`/`restore-crate-type` dependen de que `on_error_task = "catch"` se ejecute (`appflowy/frontend/Makefile.toml:16–20`); una interrupción abrupta no lo ejecuta.
- **B6.1** — **Un release puede salir sin AppImage.** `continue-on-error: true` en el paso del AppImage (`appflowy/.github/workflows/release.yml:414`) y, además, el job `build-for-linux` sube el asset del AppImage aunque el fichero no exista.
- **B6.1** — **`build-for-docker` corre fuera del grafo del release** (`appflowy/.github/workflows/release.yml:464–466`) y no lo notifica ni `notify-failure` ni `notify-discord`.
- **B6.1** — **Versiones de `cargo-make` divergentes o ausentes** (§5.2), con el release como el caso más expuesto.
- **B6.1** — **Dos scripts `postrm` con lógica de borrado desalineada**: `linux_installer/postrm` comprueba `/usr/local/bin/appflowy` en minúsculas (`appflowy/frontend/scripts/linux_installer/postrm:2`) mientras su `postinst` creó `/usr/local/bin/AppFlowy` en CamelCase (`appflowy/frontend/scripts/linux_installer/postinst:6`), así que el symlink sobrevive a la desinstalación.
- **B6.1** — **`install.sh` inservible contra los artefactos actuales** (§5.11) y con un *fallback* de sha-256 roto (`install.sh:328–330`).
- **B6.1** — **Dos actions fijadas a ramas mutables con privilegio elevado** (§5.16) y `langchain-rust` resuelto por rama en Rust (`appflowy/frontend/rust-lib/Cargo.toml:159`).
- **B6.1** — **Cobertura de Rust parcialmente ficticia** (§5.12): `cd ../shared-lib` a un directorio inexistente y dos interpolaciones de `matrix` sin `matrix` definida.
- **B6.1** — **Filtro de `translation_notify.yml` sobre una ruta que el build sustituye**: el workflow vigila `frontend/appflowy_flutter/assets/translations/en.json` (`appflowy/.github/workflows/translation_notify.yml:6`), un directorio **generado** y borrado en cada build (`appflowy/frontend/scripts/code_generation/language_files/generate_language_files.sh:50–52`), mientras la fuente de verdad es `frontend/resources/translations/en-US.json` (`project.inlang.json:42`). La notificación sólo puede dispararse si alguien commitea artefactos generados.
- **B6.1** — **Dos workflows filtran `mobile_ci.yaml` cuando el fichero se llama `mobile_ci.yml`** (`appflowy/.github/workflows/ios_ci.yaml:8`, `appflowy/.github/workflows/ios_ci.yaml:16`; `appflowy/.github/workflows/android_ci.yaml.bak:8`, `appflowy/.github/workflows/android_ci.yaml.bak:15`), lo que además interactúa con el hecho de que Android esté en `.bak`: si alguien restaurase el fichero con nombre correcto, sus filtros seguirían apuntando al nombre equivocado.

### B6.2 (7)

- **B6.2** — Para cada feature, el directorio de test que la cubre en la batería de AppFlowy (Dart o Rust event-integration-test) o `[NO DETERMINADO]` si no existe. Verificado con `find`/`rg` desde el repositorio clonado.
- **B6.2** — [NO DETERMINADO] Quién ejecuta `flutter test integration_test/desktop/cloud/cloud_runner.dart` desde `Makefile.toml` / `tests.toml`: el target `flutter_test` (`appflowy/frontend/scripts/makefile/tests.toml:3–9`) sólo acepta un `path` como `${@}`, no una ruta fija de `cloud_runner.dart`. La invocación CI vive sólo en `appflowy/.github/workflows/flutter_ci.yaml:332–340`.
- **B6.2** — [NO DETERMINADO] Por qué `desktop_runner_*.dart` se ejecutan en serie desde un único `runner.dart` si CI los paraleliza con un job por `test_number`: el comentario `appflowy/frontend/appflowy_flutter/integration_test/runner.dart:14–20` sólo menciona el workaround de flutter/flutter#101031; no hay nota sobre la decisión arquitectónica.
- **B6.2** — [NO DETERMINADO] Cómo se seleccionan los perfiles en `appflowy/frontend/scripts/makefile/tests.toml` cuando ambos `macOS x86_64` y `arm64` quieren su perfil: `APP_ENVIRONMENT = "local"` está en `appflowy/frontend/Makefile.toml:45–48` (`CRATE_TYPE = "staticlib"`, `LIB_EXT = "a"` en `:45–46`); `test-macos-x86_64` (`appflowy/frontend/Makefile.toml:259–268`) y `test-macos-arm64` (`appflowy/frontend/Makefile.toml:265–268`) usan `cdylib`/`dylib`. El selector real está en `appflowy/frontend/scripts/makefile/tests.toml:11–27` con `uname -m`, pero el patrón de invocación queda fuera del snapshot.
- **B6.2** — [NO DETERMINADO] Cobertura real de `skipAIChatWelcomePage = true` y `loadDefaultMessages`: el flag se asigna al inicio de `appflowy/frontend/appflowy_flutter/integration_test/desktop/chat/chat_page_test.dart:15`, pero su efecto sobre el flujo del `AIWelcomePage` y el `ChatPage` no se rastrea por test unit; sólo se ejercita por la suite integration. Idem para `appflowy/frontend/appflowy_flutter/integration_test/shared/ai_test_op.dart` (helper).
- **B6.2** — [NO DETERMINADO] `appflowy/frontend/appflowy_flutter/test/widget_test/spae_cion_test.dart` parece ser un typo (`spae_cion` ≠ `space_ion`/`spanning`). El nombre se preserva tal cual en el repo (`find … -name "*.dart"` lo enumera), pero el propósito semántico del test queda por documentar.
- **B6.2** — Nota sobre `appflowy/frontend/appflowy_flutter/test/util.dart:106–108`: `blocResponseFuture(millisecond: 200)` SÍ tiene consumidores reales en `appflowy/frontend/appflowy_flutter/test/bloc_test/ai_writer_test/ai_writer_bloc_test.dart` (7 llamadas: `:19`, `:28`, `:37`, `:46`, `:62`, `:74`, `:85` entre otras), `appflowy/frontend/appflowy_flutter/test/bloc_test/app_setting_test/appearance_test.dart:1`, `appflowy/frontend/appflowy_flutter/test/bloc_test/home_test/home_bloc_test.dart:6` (sincronización de streams), `appflowy/frontend/appflowy_flutter/test/bloc_test/home_test/sidebar_section_bloc_test.dart:3`, `appflowy/frontend/appflowy_flutter/test/bloc_test/home_test/view_bloc_test.dart:2` y `appflowy/frontend/appflowy_flutter/integration_test/shared/ai_test_op.dart:3` (`:54`, `:61`, `:67`). El `[NO DETERMINADO]` previo (que afirmaba "ningún consumidor directo") era incorrecto y se elimina en esta revisión.

### B6.3 (8)

- **B6.3** — **SEC-1** — `BackendAuthService.signUpAsGuest` crea el usuario invitado con una **contraseña fija escrita en el código fuente** y un correo también fijo: `const password = <REDACTED>` y `userEmail = "anon@appflowy.io"` (`appflowy/frontend/appflowy_flutter/lib/user/application/auth/backend_auth_service.dart:67–68`). **[NO DETERMINADO]** Si esos mismos valores coinciden con una cuenta real del servidor AppFlowy Cloud y si, por tanto, cualquiera que firmara con ellos obtendría acceso a los datos del usuario anónimo. Impacto potencial alto; la comprobación requiere acceso al servidor, que queda fuera de alcance.
- **B6.3** — **Cifrado en reposo del lado servidor.** El repositorio solo contiene el cliente. No hay forma de determinar desde estas fuentes si AppFlowy-Cloud cifra la base de datos en reposo ni con qué clave.
- **B6.3** — **Rotación y revocación de tokens en el servidor.** Se observa el contrato (`TokenState:Refresh`, `TokenState:Invalid`), pero la política de vida máxima del `refresh_token`, la revocación al cerrar sesión y el comportamiento ante `sign_out` local son externos.
- **B6.3** — **Literales de encabezado del cliente Rust.** `client-api` se resuelve desde el repositorio externo `AppFlowy-IO/AppFlowy-Cloud` en `rev = "592f644"` (`appflowy/frontend/rust-lib/Cargo.toml:113–114`) y no está vendorizado. Los nombres de encabezado que Rust envía en cada petición no son determinables; solo se documentan los de la capa Dart.
- **B6.3** — **Clave del proveedor de LLM.** El cliente IA no contiene claves; dónde reside y cómo se rota la del proveedor es información del servidor.
- **B6.3** — **Contenido de los secretos de CI.** Los pipelines y la configuración de firma se analizan en `[[B6.1]]`; si algún secreto se inyecta como variable de entorno de build no es determinable desde el código de aplicación.
- **B6.3** — **Permisos del sistema de ficheros sobre los datos en reposo.** El cliente crea los directorios con `create_dir_all` (`appflowy/frontend/rust-lib/flowy-core/src/config.rs:75–91`) sin fijar permisos restrictivos; `[INFERIDO]` que heredan el `umask` del proceso, pero el modo final depende del sistema y no se comprueba en el código.
- **B6.3** — **Alcance real del cifrado `enable_encrypt`.** El interruptor se propaga al servidor (`appflowy/frontend/rust-lib/flowy-core/src/app_life_cycle.rs:151–160`) y la firma cubre el `uid`, pero qué objetos cifra el backend no es determinable desde el cliente.

## Harvest automático · 2026-10-21 · 2 preguntas

Preguntas recogidas automáticamente de las secciones de `[NO DETERMINADO]` de los documentos de `OUT/`. Recogidas por `SKILL/scripts/harvest_open_questions.py`; el bloque es idempotente (una entrada ya escrita no se vuelve a copiar).

### B6.4 (1)

- **B6.4** — Ninguna de las afirmaciones de este resumen es `[NO DETERMINADO]`: todo lo que aquí se afirma está anclado en un fichero de `SRC/` que el validador de evidencia resuelve contra el inventario. Las preguntas abiertas que sí existen pertenecen a documentos concretos y están acumuladas en `OUT/22-preguntas-abiertas.md`; las que afectan al alcance de este resumen son cuatro:

### B6.5 (1)

- **B6.5** — Registra cada `[NO DETERMINADO]` en la sección de riesgos para que `harvest_open_questions.py` lo volque en `22-preguntas-abiertas.md`.


## C1 · Pasada global de validadores — 2026-10-21 · 10 citas retiradas

La Fase C1 tenía que decidir, una a una, si las 48 referencias rotas de
`OUT/15-secuencias-globales/` se habían movido al escribir el documento o eran
erróneas. Resultado: **38 resueltas** (ruta y línea ancladas al símbolo real) y
**10 retiradas**, porque el fichero citado no existe en el snapshot `5cf3a36` y
el símbolo tampoco. `AGENTS.md §6` prohíbe citar ficheros o inventar nombres que
no estén en el inventario, así que la cita se sustituyó por un marcador
`[NO DETERMINADO]` y se registra aquí. Trazabilidad completa en
`OUT/_ledger/pruebas/C1/refs_retiradas.csv`.

### Símbolos que no existen en el código

- **`AppBloc` / `app_bloc.dart`** — 4 citas (B5.3 ×3, B5.13 ×1, B5.0 ×1 en el
  índice). `rg 'app_bloc' SRC/` no devuelve ningún fichero: la arquitectura
  dual de `AGENTS.md §5.7` mueve el estado global de workspace a
  `appflowy/frontend/appflowy_flutter/lib/features/workspace/logic/workspace_bloc.dart`
  (`WorkspaceBloc extends Bloc<WorkspaceEvent, WorkspaceState>`, línea 12), pero
  **no existe una clase `AppBloc`**. Los documentos B5.3 y B5.13 describen una
  arquitectura de sidebar (`AppBloc → FolderCubit → SidebarBuilder`) que este
  snapshot no implementa con ese nombre. Queda por determinar cuál es el
  `BlocListener<RouterConfig>` real que actualiza el `GoRouter`.

- **`StorageEvent::Upload`** — 1 cita (B5.0). El enum real es `FileStorageEvent`
  con exactamente dos variantes: `RegisterStream = 0` y `QueryFile = 1`
  (`appflowy/frontend/rust-lib/flowy-storage/src/event_map.rs:21`, `:24`).
  Ni el nombre del enum ni la variante `Upload` existen. `[[B2.1]]` ya había
  documentado las 2 variantes reales.

- **`FileUploadProgress`** — 1 cita (B5.7, y otra en el mismo `sequenceDiagram`).
  `StorageNotification` solo declara `FileStorageLimitExceeded` y
  `SingleFileLimitExceeded`
  (`appflowy/frontend/rust-lib/flowy-storage/src/notification.rs:9`, `:11`), y
  `rg 'FileUploadProgress' SRC/` no encuentra nada. **No hay notificación de
  progreso de subida por chunk en este snapshot**, lo que contradice el
  diagrama de B5.7 que la daba por emitida.

- **`DidPublishView`** — 1 cita (B5.12). `FolderNotification` tiene 19 variantes
  (`appflowy/frontend/rust-lib/flowy-folder/src/notification.rs:10–45`) y
  ninguna es `DidPublishView`. Ninguna de las 19 menciona publicación. El
  evento real de publicación es `FolderEvent::PublishView`, que se gestiona en
  `publish_view_handler` (`appflowy/frontend/rust-lib/flowy-folder/src/event_handler.rs:402`).

- **`DocumentSyncEvent::DidUpdateSyncState` como evento Rust** — 1 cita (B5.0).
  `rg 'DidUpdateSyncState' SRC/` no devuelve nada y `rg 'DocumentSyncEvent'`
  solo encuentra código Dart (frontend/appflowy_flutter/lib/plugins/document/application/document_sync_bloc.dart:83,
  un `freezed` generado). El enum Rust real es `DocumentNotification`, con
  `DidUpdateDocumentSyncState = 3` (`appflowy/frontend/rust-lib/flowy-document/src/notification.rs:13`).

- **`ZipCreator`** en `document_exporter.dart` — 1 cita (B5.10). El fichero
  `appflowy/frontend/appflowy_flutter/lib/workspace/application/export/document_exporter.dart`
  tiene 67 líneas y no menciona `ZipCreator`: el tipo pertenece a
  `appflowy_editor`, que no está vendorizado en `SRC/`. Queda por determinar si
  el export a Markdown empaqueta assets de imagen en el mismo `document_exporter.dart`
  o en otro punto de la cadena.

- **`image_upload.dart`** — 2 citas (B5.0, B5.7). No existe en `SRC/`: el plugin
  de imagen de la app se compone de `image_util.dart`, `image_picker_screen.dart`,
  `common.dart`, `custom_image_block_component/` y `multi_image_block_component/`
  (`appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/image/`).
  La subida de ficheros se resuelve en `[[B3.F07]]` (F07, Almacenamiento de archivos).

- **`collab:collab/collab/src/lib.rs:240`** — 1 cita (B5.0, celda «B5.5 concurrent»).
  `lib.rs` tiene 41 líneas. `EncodedCollab` y sus métodos están en
  `collab:collab/collab/src/entity.rs:6`, que es donde C1 reapuntó las otras dos citas
  del mismo símbolo.

### Entidades que sí existen pero en otro fichero

Estas no se retiraron; C1 las reapuntó. Se listan porque **el ROADMAP y los
documentos B4/B5 las situaban en un fichero que no existe**, y cualquier
documento que las cite por su ruta antigua arrastra el mismo error:

| Símbolo | Ruta citada (inexistente) | Ruta real |
|---|---|---|
| `FileStorageEvent` / `StorageNotification` | `collab-plugins/src/cloud_storage/sync_state.rs` | `appflowy/frontend/rust-lib/flowy-document/src/notification.rs:13` |
| `DatabaseEditor` | `flowy-database2/src/database_editor.rs` | `appflowy/frontend/rust-lib/flowy-database2/src/services/database/database_editor.rs:77` |
| `DatabaseView` | `collab-database/src/views/database_view.rs` | `collab/collab-database/src/views/view.rs` |
| `LocalSearchHandler` | `flowy-search/src/services/local_search_handler.rs` | `appflowy/frontend/rust-lib/flowy-search/src/document/local_search_handler.rs` |
| `CommandPaletteBloc` | `search_menu_bloc.dart` | `appflowy/frontend/appflowy_flutter/lib/workspace/application/command_palette/command_palette_bloc.dart` |
| `EncodedCollab` | `collab/collab/src/lib.rs` | collab:collab/collab/src/entity.rs:6 |

### Deuda residual que hereda C3

- **Citas resueltas por ancla más próxima, no por verificación semántica.** Son
  las que el resolutor tuvo que apuntar a la línea que declara el símbolo cuando
  el símbolo aparece varias veces en el fichero. Las tres citas originales
  (ahora retiradas o reapuntadas) eran:

  - `chat.rs`, línea 60 (B5.9, chat con streaming)
  - `notification.rs`, línea 48 (B5.0, índice de secuencias)
  - `lib.rs`, línea 35 (B5.5, edición concurrente)

  La ruta y la línea resultantes **existen**, pero la afirmación que las respalda
  puede ser falsa: `chat.rs:60` es `stream_buffer: Arc::new(...)` mientras el
  documento atribuye la línea a `stop_stream_message`. Solo una revisión
  semántica (C3) puede zanjarlo.
- **Un fallo de tooling de B6 que C1 ha cerrado:** `fix_evidence_prefix.py` no
  era idempotente ni saltaba los bloques ```fenced```, y dejó **98 spans de
  ``inline code`` rotos** en los 14 documentos de B5 (prefijo duplicado y
  desemparejamiento de backticks). `validate_evidence` no lo detectaba porque las
  referencias siguen resolviendo; el síntoma era Markdown inválido. Reparado con
  `SKILL/scripts/repair_markdown_damage.py` y corregido en origen.

## Harvest automático · 2026-10-21 · 1 preguntas

Preguntas recogidas automáticamente de las secciones de `[NO DETERMINADO]` de los documentos de `OUT/`. Recogidas por `SKILL/scripts/harvest_open_questions.py`; el bloque es idempotente (una entrada ya escrita no se vuelve a copiar).

### B5.2 (1)

- **B5.2** — `[NO DETERMINADO]`: ¿existe `flowy-user/tests/sign_in_with_password_test.rs`? **Resuelto en B6.5: no existe.** El crate `flowy-user` no tiene directorio `tests/` en este snapshot (`rg 'sign_in_with_password_test' SRC/` → 0 coincidencias); el login con contraseña no tiene test de integración por evento. Ver `OUT/22-preguntas-abiertas.md` §B5.2.

