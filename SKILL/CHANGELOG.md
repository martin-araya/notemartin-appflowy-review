# Changelog — `notemartin-appflowy-review`

Todas las modificaciones relevantes de la **skill** (no del análisis que produce). Formato [Keep a Changelog 1.1](https://keepachangelog.com/es/1.1.0/); versión semántica.

El cambio de versión se documenta en la primera entrada de cada release. La skill se distribuye en `SKILL/` y la salida del análisis vive en `OUT/` (cambios de OUT no entran aquí).

## [0.12.0] — 2026-10-21 · Cierre de las fases C1 y C2 (pasada global de validadores y cobertura)

Primera fase de la **Parte C**. C1 decide, referencia por referencia, si una cita rota se movió al escribir el documento o era errónea; C2 confirma que el ledger sigue al 100 %. Esta entrada documenta solo los cambios de la **skill**.

### Added

- **`SKILL/scripts/fix_line_offsets.py`** (~780 líneas) — resuelve las referencias de evidencia rotas en **cuatro capas deterministas**, cada una con su motivo en el CSV de salida: (1) la ruta resuelve tal cual contra `inventario.json`; (2) **`basename` + ancla de contexto** — para `event_handler.rs:73` hay 8 candidatos, y descartar los que no **declaran** el símbolo que la frase nombra deja uno; (3) mapa explícito de migraciones; (4) **búsqueda por ámbito de crate** — si la línea está fuera de rango y el fichero citado no menciona el símbolo, se busca el único fichero **del mismo crate** que lo declara (así `dart-ffi/src/c.rs:58` acaba en `dart-ffi/src/lib.rs:114`). Idempotente: la segunda pasada encuentra 0.
  - **Desambiguación de anclas.** Extrae identificadores de la línea del `.md` y sus 2 anteriores, los **parte por `::` poniendo el tipo delante** y los ordena por poder discriminante **real** (nº de candidatos que los declaran). Sin las dos reglas fallaba: `FolderManager::initialize_after_open_workspace` —que comparten cuatro crates— colapsaba a uno antes de que `FolderManager` lo desambiguara, y `FlowyError::RecordNotFound` ganaba a `read_current_workspace_handler` solo por aparecer antes.
  - **Deprioriza `tests/`** frente a producción cuando ambos candidatos comparten basename (`database_editor.rs` existe en `src/services/database/` y en `tests/database/`).
- **`SKILL/scripts/path_migrations.json`** — 21 entradas `de → para` de rutas movidas o citadas inexistentes. Soporta `para: null` (retirar la cita: el fichero **y** el símbolo no existen, y `AGENTS.md §6` los prohíbe) y `linea` (fijar el destino cuando el nombre del handler difiere del nombre del evento, como `GetDatabaseData` → `get_database_data_handler:31`). Cada entrada lleva su `motivo`, verificable con `rg` contra `SRC/`.
- **`SKILL/scripts/repair_markdown_damage.py`** (~230 líneas) — repara los spans de ``inline code`` rotos extrayendo la **referencia válida que sobrevive dentro del run** y reconstruyendo el span con una backtick. Solo aplica si la referencia reconstruida existe en el inventario; si no, deja el run intacto y lo reporta.
- **`OUT/_ledger/validate-C1.sh`** — 5 checks: plantilla, evidencia, mermaid, cobertura (`--threshold 100`) e idempotencia de los tres reparadores más trazabilidad (`refs_rotas.csv` con la deuda inventariada, `refs_retiradas.csv` con las citas retiradas, § C1 de `22-preguntas-abiertas.md`). El check 5a escribe su CSV en un temporal: los CSV de `OUT/_ledger/pruebas/C1/` son el **registro de auditoría** y una ejecución en vivo no debe sobrescribirlos con cero filas.

### Changed

- **`validate_evidence.py` — `META_DOCS` + `_ledger/` excluidos por defecto**, con `--incluir-meta` / `--incluir-ledger` para incluirlos. Alinea el validador con `validate_template.py`, que ya excluía los mismos cuatro ficheros (`00-INDEX.md`, `22-preguntas-abiertas.md`, `STATE.md` y `_ledger/`); los meta-ficheros citan documentos internos de `OUT/`, no código fuente. La pasada global deja **288 errores → 0** sobre 190 documentos entregables.
- **`validate_mermaid.sh` — excluye `_ledger/` y los meta-ficheros**, con `--all` para incluirlos. `OUT/_ledger/pruebas/A3.1/fixtures/{broken,mixed}.md` están **deliberadamente rotos** (prueban que el script detecta fallos) y hacían fallar la suite global con 2 errores phantom.
- **`--skip` normalizado a ruta relativa al proyecto** en los tres reparadores. Los prefijos de `args.skip` (`OUT/_ledger`, …) se comparaban contra `str(m)` tal cual venía del `rglob`, así que al pasar `OUT/` en **absoluto** no casaba ninguno: `fix_line_offsets.py --apply "$PWD/OUT/"` reescribió 12 citas válidas fuera de B5 y las retiró por el gate de abajo.

### Fixed

- **`fix_evidence_prefix.py` no era idempotente y rompía el Markdown de los diagramas.** Doble fallo: (a) `RE_REF` absorbía como grupo `fuente` un prefijo ya presente (`appflowy:frontend/rust-lib/…` → `appflowy:appflowy/frontend/rust-lib/…`), de modo que aplicarlo dos veces duplicaba el prefijo otra vez; (b) reescribía dentro de los bloques ```fenced```, y como el resultado se escribía de vuelta **enmascarando** el fence, dejaba 98 spans de ``inline code`` rotos en los 14 documentos de B5 (`` `appflowy:frontend/`appflowy:`…:1``` ``). Las referencias seguían resolviendo, así que **ningún validador lo veía**: el síntoma era Markdown inválido. Corregido con `referencia_valida()` (replica el criterio de `validate_evidence`, sin tocar líneas), procesamiento línea a línea que salta los fences, y `recolectar()` con skip normalizado.
- **`fix_line_offsets.py` — gate de retirada demasiado agresivo (corregido tras ver el daño).** Retiraba cualquier cita cuyo fichero no contuviera un token del ancla, y el conjunto de anclas es heurístico: llegó a retirar `sidebar_test_runner.dart:14` y `_page_style_icon_bloc.dart:10`, que existen. **Nunca** se retira la cita a un fichero de nombre único, existente y con línea válida; la retirada queda para las citas cuyo fichero no existía con ese nombre o cuya línea estaba fuera de rango.
- **`fix_line_offsets.py` — `formatear()` perdía el prefijo de fuente.** Para `collab` y `editor` emitía `collab:collab/src/entity.rs:6` (faltaba un segmento) en vez de `collab:collab/collab/src/entity.rs:6`, porque `validate_evidence.py` solo antepone `<fuente>/` cuando la ruta **no** empieza por `<fuente>/` y el resto del path ya empieza por el nombre del repo.

## [0.11.0] — 2026-10-21 · Cierre del Bloque B6 (transversales: build/CI, testing, seguridad, resumen, glosario)

Cierre de las 6 unidades B6, que cierran el Bloque B entero. Esta entrada documenta solo los cambios de la **skill**.

### Added

- **`SKILL/scripts/make_b6_units.py`** — genera las 6 unidades de B6 en `OUT/_ledger/units/B6.*.json`. **Valida que las 176 rutas existan en `SRC/` antes de escribir el JSON.** Las unidades de síntesis (B6.4, B6.5, B6.5.2) declaran `archivos` como anclajes SRC verificables y `documentos_representados` aparte: `validate_evidence.py` solo resuelve referencias contra `inventario.json`, así que citar `OUT/…` como evidencia no es validable y un resumen ejecutivo no puede apoyarse solo en eso.
- **`SKILL/scripts/fix_evidence_prefix.py`** — normaliza referencias `ruta:línea` a las que les falta el prefijo de directorio (`flowy-user/src/notification.rs:18` → `appflowy/frontend/rust-lib/flowy-user/src/notification.rs:18`). Es **conservador por diseño**: solo reescribe cuando existe **exactamente un** fichero del inventario cuyo sufijo sea el ruta citado; con cero candidatos lo deja como está (error real) y con más de uno lo deja y avisa (ambigüedad → decisión humana). **Nunca toca números de línea.** Bajó los errores de evidencia de `OUT/15-secuencias-globales/` de 82 a 48 sin romper `validate_template` (14/14) ni `validate_mermaid` (53/53).

### Changed

- **`validate_template.py` — tres plantillas nuevas para B6**: `transversal` (8 secciones, id `^B6\.[123]$`), `resumen` (7 secciones, id `^B6\.4$`) y `glosario` (8 secciones, id `^B6\.5$`). Se resuelven **antes** que `export` en `detect_template`, cuyo patrón `^B\d+(\.\d+)?$` también matchearía `B6.1`, `B6.4` y `B6.5`: sin ese orden, los tres transversales se validarían contra la plantilla equivocada.
- **`validate_template.py` — `collect_md_files` excluye `_ledger/` y los meta-ficheros.** `OUT/_ledger/` es el cuaderno de trabajo de la skill (inventario, briefs, artefactos de prueba de subagentes) y sus `.md` no llevan frontmatter por diseño; `00-INDEX.md` lo regenera `build_index.py`, `22-preguntas-abiertas.md` se organiza en secciones `## Ax.y` y `STATE.md` es el cuaderno de estado entre sesiones. Ninguno es un documento de plantilla. Con la exclusión, la pasada global pasa de **164 errores a 0** (190/190 documentos).
- **`harvest_open_questions.py` — aprende las tres plantillas de B6.** Recorta `## 6.` para `transversal`, `### Preguntas abiertas` para `resumen` y el cuerpo entero para `glosario`, porque en cada una las `[NO DETERMINADO]` viven en un sitio distinto. Añade además:
  - **regla que también recoge los ítems de lista bajo un heading etiquetado**, no solo las líneas que llevan la etiqueta: B6.3 titula su subsección `### 6.2 \`[NO DETERMINADO]\` — huecos reales` y no repite la etiqueta en cada ítem, y sin esa regla 7 de sus 8 preguntas nunca habrían llegado al fichero;
  - **deduplicación dentro de la misma pasada** (comparación de la entrada completa contra el fichero *y* contra lo ya recogido): antes, un mismo `[NO DETERMINADO]` repetido en un documento entraba dos veces;
  - `EXCLUIDOS_RAIZ` para no cosechar `22-preguntas-abiertas.md`, `STATE.md` ni `00-INDEX.md` al recorrer la raíz de `OUT/`.
- **`make_unit_brief.py` — esquema transversal.** `archivos` puede ser una lista de rutas planas (B4/B5/B6) en vez de una lista de dicts `{ruta, capa, fuente}` (features F*); antes el script reventaba con `TypeError: string indices must be integers` al abrir cualquiera de ellas. Los briefs transversales llevan las secciones obligatorias de su plantilla, el foco del ROADMAP y los comandos de validación correctos.

### Fixed

- **`harvest_open_questions.py` — los `[NO DETERMINADO]` de B6.1, B6.2, B6.3, B6.4 y B6.5 no llegaban a `22-preguntas-abiertas.md`.** El script solo leía `## 18.` (feature) y `## 5.` (export). B6 producía 32 preguntas huérfanas en su propio documento de origen.
- **`validate_evidence.py` no se puede usar como prueba global sin excluir `_ledger/`.** Al ejecutarlo sobre `OUT/` a pelo, 319 de los 319 errores venían de `OUT/_ledger/pruebas/**`, que guarda copias de trabajo de documentos para subagentes y cita rutas relativas a propósito.

### Fixed

- **17 fragmentos de texto en chino inyectados en prosa en español**, dispersos por 14 documentos ya aprobados de B3, B4 y B5 (`主要集中在`, `遗漏`, `遗留`, `理论`, `奔赴`, `吸收`, `合同`, `与之`, `精度`, `去处`, `是否存在`, `三条`, `的支持`). Eran el mismo defecto de contaminación de idioma que se detectó en los documentos de B6 durante su revisión. Corregidos en una pasada. **Se dejó intacto el chino que es evidencia**: `简体中文` (nombre de locale citado en F14), `开始` (cadena de un test de idioma en F14) y `一个`/`两个` (literales de `text_diff_test.dart` en F19) son cadenas reales del código y quitarlas habría destruido la cita.

### Security

- Se cerró una **fuga de credencial en un documento ya aprobado**: la contraseña fija de `BackendAuthService.signUpAsGuest` aparecía literal en `OUT/09-features/F05-usuario-auth-sesion/1-usuario-appflowy-flutter-lib-user-dart.md` (dos ocurrencias). Sustituida por `<REDACTED>` con remisión a `[[B6.3]] §6.1`. El control de redacción es **documental, no de código**: el literal sigue siendo legible por cualquiera con acceso al repositorio o al binario, y la skill lo declara así en vez de presentarlo como una mitigación.

## [0.10.0] — 2026-10-21 · Cierre del Bloque B4 (motor de export/import/publicación) + deuda C5

Cierre de las 14 fases B4.0–B4.13 (6 900 líneas, 2 167 refs, 61 diagramas) y, antes, de la deuda de ids que arrastraba el cierre de B3. Esta entrada documenta solo los cambios de la **skill**.

### Added

- **`SKILL/scripts/make_b4_units.py`** — genera las 14 unidades de B4 en `OUT/_ledger/units/B4.*.json` con su lista real de archivos. **Valida que las 124 rutas existan en `SRC/` antes de escribir el JSON** y falla con el listado de las que falten: sin esa comprobación, 6 de las 124 rutas iniciales no existían (nombres inventados como `export_error.dart`, `pdf_encoder.dart`, `share_with_user_repository_impl.dart`) y el fallo solo aparecía en el quinto check de la suite, después de escribir el documento.
- **`make_phase_suite.py --template` y `--transversal`** — el quinto check de una unidad transversal valida que el frontmatter declare exactamente N rutas y que todas existan en `SRC/`, en vez de contar filas marcadas en `cobertura.csv` (que para una unidad transversal es 0). El parser acepta las tres formas de escribir la fuente: `appflowy/…`, `collab:collab-database/…` y `editor:lib/…`.

### Changed

- **`close_unit.sh` — dispatch de plantilla y fase por prefijo de unidad.** `B4.*` → plantilla `export` (11 secciones de `export-template.md`) y `PHASE=$UNIT`; `B1.*` → `structure`; el resto → `feature` y `PHASE=B3.$UNIT`, como antes. Antes ambos estaban fijados a `feature`/`B3.` y ningún doc de B4 habría pasado el primer check.
- **`close_unit.sh` — las unidades `B*` no tocan `cobertura.csv`.** Sus archivos ya pertenecen a una feature F* y están verificados; el ledger se mantiene en 100 % global. Documentado en el propio script: re-trazar el motor es documentalizar, no re-declarar propiedad.
- **`harvest_open_questions.py` — recorre `OUT/10-motor-export-import/` y lee las secciones 5–8.** Antes solo escaneaba `OUT/09-features` y la sección `## 18.`, que no existe en la plantilla export: **todos los `[NO DETERMINADO]` de B4 eran invisibles** para el volcado a `22-preguntas-abiertas.md`.

### Fixed

- **42 erratas de id y 11 tokens de ejemplo en documentos ya aprobados.** Los tokens de ejemplo (`<X>`, `<NOEXISTE>`, `<F..>`) se reescribieron con ángulos y la sintaxis TOML de Cargo (`[[bin]]`, `[[test]]`) como `[bin]`/`[test]`, porque `build_index.py` las escaneaba como enlaces reales. Los ids se mapearon al equivalente válido más cercano (`B18.1`→`B6.1`, `F01.0.3`→`F01.0.3.3`, `F02.9.4`→`F02.9.1`+`F02.9.2`, `F00.8`→`F00.7.8`, `B1`→`B2.1`+`B2.2`, …) o se reescribieron a prosa cuando no existía equivalente. **`build_index.py --check-links`: 131 → 50 no resueltos**, y los 50 son exclusivamente `B6.1`/`B6.2`/`B6.3`.
- `make_b4_units.py` generaba `B4.3` con un archivo duplicado en la lista y con 3 rutas donde debía tener 5. Detectado por el quinto check de la suite, no por el generador.

## [0.9.0] — 2026-10-20 · Cierre del Bloque B3 (F16 + F00 + F19), ledger al 100 %

Cierre de las 37 unidades que quedaban (1 850 archivos) con `close_unit.sh --unit <ID>`. El análisis resultante vive en `OUT/`, no aquí; esta entrada documenta solo los cambios de la skill que hicieron falta para ello.

### Added

- (Ninguno. No hubo script nuevo: el pipeline `make_unit_brief.py` → autor → `close_unit.sh` ya cubría el ciclo completo.)

### Changed

- **`OUT/_ledger/validate-A4.2.sh` — checks 4–6 sobre un ledger pendiente.** `build_units.py::distribute()` salta las filas con `estado == verificado`, así que con el ledger real al 100 % (`--max-files 50` y `--no-split`) no emitía ninguna unidad y los checks fallaban con `0 unidades`. Los tres checks miden la **lógica de división**, no el estado del proyecto, así que ahora corren contra `LEDGER_PEND`: una copia temporal de `cobertura.csv` con todo en `pendiente`. **La aserción no se relajó** (`> 22` unidades sigue exigiéndose, y ahora da 269); se corrigió el escenario. Los checks 1–3 y 7–8 siguen validando el ledger real.
- **`SKILL/scripts/build_index.py` — 15 alias nuevos en `ID_ALIASES`**: 11 de feature (`F00→F00.0`, `F01→F01.0`, `F02→F02.0.1.0`, `F03→F03.0`, `F05→F05.0`, `F09→F09.0`, `F12→F12.1`, `F13→F13.1`, `F15→F15.1`, `F16→F16.0`, `F19→F19.0`) y 4 de familia de sub-unidades (`F00.5`, `F00.7`, `F01.6`, `F02.9`). Los documentos enlazan a la feature (`[[F01]]`) mientras el id real del sub-documento índice es `F01.0`. Bajó los enlaces no resueltos de 192 a 125 **sin tocar un solo documento**.

### Fixed

- **`units/F19.0.json` apuntaba a un documento inexistente.** `make_unit_brief.py` genera el nombre de destino, pero el autor eligió un nombre más largo; `close_unit.sh` falló con `ERROR: no existe el documento`. Reapuntado con `set_unit_docs.py F19.0=<ruta real>` y reindexado. Recordatorio operativo: si `close_unit.sh` falla con ese error, el fix es `set_unit_docs.py`, no reescribir el doc.

### Removed

- (Nada.)

### Nota operativa

- Los briefs de las 37 unidades se regeneraron con `make_unit_brief.py --feature F00` y `--feature F19`: solo 10 existían de 37. La skill no avisa cuando un brief falta.

## [0.8.0] — 2026-10-19 · Fase B2.6 (Catálogo de flags/rutas/atajos/i18n/startup)

### Added

- `SKILL/scripts/build_catalog_misc.py` — generador que produce `OUT/16-catalogo-flags-rutas-atajos.md` desde `OUT/_ledger/extract/misc.json`. Verifica `len(items) == summary.total_*` para las 5 sub-tablas antes de generar (rutas, hotkeys, flags, i18n keys, startup tasks); normaliza `SRC/<fuente>/` → `<fuente>/` para alinear con `inventario.json::ruta_rel`; trunca `i18n_keys.sources` a 3 + `…+N` para legibilidad.
- `OUT/_ledger/validate-B2.6.sh` — suite de 4 checks para la fase B2.6 (template + evidence + mermaid + count_rows_misc).
- `OUT/_ledger/pruebas/B2.6/count_rows_misc.py` — prueba literal del ROADMAP: cuenta filas de §4–§8 con sus headers fijos y exige coincidencia con `summary.total_routes + total_shortcuts + total_feature_flags + total_i18n_keys + total_startup_tasks = 1709`.
- `OUT/_ledger/pruebas/B2.6/README.md` — bitácora con tabla de distribución por categoría y comandos para regenerar.

### Changed

- (Sin cambios.)

### Removed

- (Nada.)

## [0.7.0] — 2026-10-19 · Fase B2.5 (Catálogo de ErrorCode)

### Added

- `SKILL/scripts/build_catalog_errors.py` — generador que produce `OUT/15-catalogo-errores.md` desde `OUT/_ledger/extract/misc.json::error_codes`. Carga el JSON, verifica `len(variants) == total == 133`, agrupa por categoría heurística (prefijo CamelCase; `Database`/`Workspace`/`Auth`/`Network`/`Storage`/`View`/`Document`/`User`/`AI`/`LocalAI`/`Customization`/`Search`/etc., 30 categorías), deriva **mensaje** del campo `&'static str` del enum, **emisor típico** (`flowy-<x>`) por tabla `EMITTER_BY_CATEGORY`, **UI típica** por regex (`Inline error`, `SnackBar + login`, `Overlay upgrade plan`, `SnackBar con retry`, `Toast`, etc.). Etiqueta `[INFERIDO]` siempre.
- `OUT/_ledger/validate-B2.5.sh` — suite de 4 checks para la fase B2.5 (template + evidence + mermaid + count_rows_133).
- `OUT/_ledger/pruebas/B2.5/count_rows_133.py` — prueba literal del ROADMAP: cuenta filas en §4 (133), suma §5.* (133) y §6 (1 sentinels = `Internal`).
- `OUT/_ledger/pruebas/B2.5/README.md` — bitácora con tabla de distribución por categoría y comandos para regenerar.

### Changed

- (Sin cambios.)

### Removed

- (Nada.)

## [0.6.0] — 2026-10-19 · Fase B2.4 (Catálogo de notificaciones Rust → Dart)

### Added

- `SKILL/scripts/build_catalog_notifications.py` — generador que produce `OUT/14-catalogo-notificaciones.md` desde `OUT/_ledger/extract/notifications.json`. Carga el JSON, verifica `sum(len(rust_notifications[i].variants)) == 70`, genera una fila por variante con su `emitter` (cuando `variant != null` en `emitters[]`), su `listener` (cuando `has_dart_listener == true` desde `dart_listeners[]`) y un `Efecto UI` heurístico por nombre (regex sobre `DidUpdate*`, `DidCreate*`, `Stream*Error`, `FinishStreaming`, `FileStorageLimitExceeded`, etc.) etiquetado `[INFERIDO]`.
- `OUT/_ledger/validate-B2.4.sh` — suite de 4 checks para la fase B2.4 (template + evidence + mermaid + count_rows_70).
- `OUT/_ledger/pruebas/B2.4/count_rows_70.py` — prueba literal del ROADMAP: cuenta filas en §4 (70), suma §5.* (70) y §6 (49 = 47 `unused` + 2 `emitted_only`).
- `OUT/_ledger/pruebas/B2.4/README.md` — bitácora con tabla de distribución por enum y comandos para regenerar.

### Changed

- (Sin cambios.)

### Removed

- (Nada.)

## [0.5.0] — 2026-10-19 · Fase B2.3 (Catálogo de BLoCs y Cubits)

### Added

- `SKILL/scripts/build_catalog_blocs.py` — generador que produce `OUT/13-catalogo-blocs.md` desde `OUT/_ledger/extract/blocs.json`. Carga el JSON, verifica `len(blocs) == total_blocs + total_cubits = 142`, agrupa por carpeta L1/L2 (`lib/<x>/<y>/`), deriva semántica `[INFERIDO]` por heurística de nombre (`View*`, `Database*`, `Document*`, `Cell*`, `Field*`, `Row*`, `Settings*`, `Sidebar*`, etc.) + carpeta, y normaliza las rutas `SRC/<fuente>/` → `<fuente>/` para alinear con `inventario.json::ruta_rel`.
- `OUT/_ledger/validate-B2.3.sh` — suite de 4 checks para la fase B2.3 (template + evidence + mermaid + count_rows_142).
- `OUT/_ledger/pruebas/B2.3/count_rows_142.py` — prueba literal del ROADMAP: cuenta filas en §4 (142), suma §5.* (142) y §6 (134 sin services) y exige coincidencia con `blocs.json::summary.{total_blocs + total_cubits}` y con la cuenta de BLoCs con `injected_services = []`.
- `OUT/_ledger/pruebas/B2.3/README.md` — bitácora con tabla de distribución por carpeta y comandos para regenerar.

### Changed

- `OUT/00-INDEX.md` — regenerado vía `build_index.py`; ahora lista `OUT/13-catalogo-blocs.md` (verificado) en §5 y §6.

### Fixed

- (Sin correcciones; la fase cierra en verde con 418/418 refs de evidencia y 3/3 Mermaid.)

## [0.4.0] — 2026-10-19 · Fase B2.2 (Catálogo de entidades protobuf)

### Added

- `SKILL/scripts/build_catalog_protobuf.py` — generador que produce `OUT/12-catalogo-entidades-protobuf.md` desde `OUT/_ledger/extract/protobuf.json`. Carga el JSON, verifica `summary.total_entities == len(entities)`, agrupa por `crate` (vía regex `rust-lib/([^/]+)/`), deriva semántica `[INFERIDO]` por heurística de nombre (struct: `*SettingsPB`, `*PayloadPB`, `*IdPB`, `*ChangesetPB`, etc.; enum: `*TypePB`, `*Status`, `*Layout`, `*Role`, etc.), y normaliza las rutas `SRC/<fuente>/` → `<fuente>/` para alinear con `inventario.json::ruta_rel`.
- `OUT/_ledger/validate-B2.2.sh` — suite de 4 checks para la fase B2.2 (template + evidence + mermaid + count_rows_439).
- `OUT/_ledger/pruebas/B2.2/count_rows_439.py` — prueba literal del ROADMAP: cuenta filas en §4 (439), suma §5.* (439) y §6 (223 huérfanas) y exige coincidencia con `protobuf.json::summary.total_entities` y con la cuenta de entidades sin `is_input_of` ni `is_output_of`.
- `OUT/_ledger/pruebas/B2.2/README.md` — bitácora de la fase con tabla de distribución por crate y comandos para regenerar.

### Changed

- `SKILL/scripts/validate_template.py` — regex del modo `catalogue` extendido de `^11-[a-z0-9-]+$` a `^1[1-6]-[a-z0-9-]+$`. Backward-compatible: `11-*` (B2.1) sigue válido; sienta precedente para los catálogos 12-, 13-, 14-, 15-, 16- del Bloque B2.
- `OUT/00-INDEX.md` — regenerado vía `build_index.py`; ahora lista `OUT/12-catalogo-entidades-protobuf.md` (verificado) en §5 y §6.

### Fixed

- (Sin correcciones; la fase cierra en verde con 1 101/1 101 refs de evidencia y 6/6 Mermaid.)

## [0.4.0] — 2026-10-20 · Fase 0 + cierre del Bloque B3 (F00–F21)

### Added

- `SKILL/scripts/rebuild_units.sh` — pipeline canónico de reconstrucción de `OUT/_ledger/units/`: `build_units --prune` → `sync_units_from_docs` → `build_units --index-only` → `validate_units`. Los pasos no son intercambiables y el script lo explica.
- `SKILL/scripts/sync_units_from_docs.py` — **el frontmatter `archivos_cubiertos` del documento pasa a ser la fuente de verdad** de `archivos[]` en las unidades con documento. Resuelve conflictos a favor de la unidad más específica, conserva los ficheros que la unidad ya poseía y que ningún otro documento reclama, y reancla a la unidad de prefijo común más largo las filas asignadas que ningún documento reclama. Idempotente.
- `SKILL/scripts/close_unit.sh` — cierre de una unidad en un comando: valida la plantilla, lanza el revisor, genera la suite de 5 checks, **actualiza el ledger antes de correr la suite** (el check de cobertura cuenta filas) y falla si el revisor no aprueba.
- `SKILL/scripts/make_unit_brief.py` — genera `OUT/_ledger/briefs/<UNIT>.md` con la unidad, sus ficheros, el foco heredado del ROADMAP y las correcciones de scope aplicables. Evita reescribir un prompt largo por subagente y garantiza que orquestador y autor ven los mismos datos.
- `SKILL/scripts/coverage_report.py` — estado de cobertura por feature y **por unidad**, leyendo el estado real del ledger (el `estado` congelado dentro del JSON de unidad no se actualiza). Escribe `--csv` opcional.
- `SKILL/scripts/harvest_open_questions.py` — vuelca las `[NO DETERMINADO]` de la §18 de los documentos a `OUT/22-preguntas-abiertas.md`, con `origen = B3.<id>` y dedupe por documento.
- `SKILL/scripts/mermaid_debug.py` — renderiza cada bloque Mermaid por separado y muestra el error real del que falle; `validate_mermaid.sh` concatena los bloques y su "FAIL" no dice cuál es.
- `SKILL/scripts/align_units.py` y `restore_unit_files.py` — reparaciones puntuales de doble propiedad y de cierre parcial. **No forman parte del pipeline** (el primero vaciaba unidades cerradas con su heurística por defecto; está documentado en su docstring).
- `SKILL/scripts/make_phase_suite.py` y `set_unit_docs.py` — promovidos desde `OUT/_ledger/pruebas/B3.F030/` a `SKILL/scripts/` (el primero tenía `PROJECT_ROOT` calculado a 4 niveles, que solo funcionaba desde su ruta original).
- `OUT/_ledger/briefs/` con 27 briefs de unidad ya generados para las fases pendientes.

### Changed

- `SKILL/scripts/build_units.py` — 12 subdivisiones nuevas o reescritas, todas declarativas: `F00.0` + `F00.7.0`–`F00.7.8` (sustituye el corte por primer segmento que producía 11 unidades de 1 archivo y una de 517), `F00.5.1`/`.1.2` y `F00.5.6`/`.6.2`/`.6.3` (los dos paquetes Dart por encima del umbral), `F09.0`, `F12_SUBS`, `F13_SUBS`, `F15_SUBS`, `F16_SUBS` reescrito (las unidades `F16.1.1`/`F16.1.2` existían solo en disco y cualquier regeneración las borraba) y entrada de índice en `F19_SUBS`. Añadidos `F02.13`/`F02.14`/`F02.15` para la fuga de F02. `FEATURE_TITLES["F21"]` y recorte de `FEATURE_TITLES["F00"]` a 80 caracteres (el slug generaba una ruta recortada de forma inconsistente). Nuevo `ALWAYS_EMIT` para materializar unidades de scope-correction con 0 archivos. Nuevos flags `--prune` (purga a `.stale-bak/` las unidades obsoletas, protegiendo las que cubren filas verificadas y las de 0 archivos) y `--index-only` (reconstruye `_index.json` leyendo el directorio completo). `write_index` deja de generarse desde las units recién producidas.
- `_split_recursive()` añadida **y no usada**: la división recursiva se probó y se descartó porque fragmentaba los paquetes Dart en ~35 unidades de 1–15 archivos (`example/`, `android/`, `ios/` son andamiaje). Se conserva con el motivo en el docstring para que nadie la reintroduzca.
- `OUT/_ledger/validate-A4.2.sh` — `N_REAL` re-baselined de 118 a **129** ficheros de unidad.

### Fixed

- **Fuga de F02**: F02 estaba marcada ✅ en el ROADMAP con 114 de sus 651 archivos sin documentar (raíz de `flowy-database2`, 49 entidades, 51 tests). Auditados y cubiertos con `F02.13`/`F02.14`/`F02.15`; **F02 pasa a 651/651**.
- **Unidades maestro con doble propiedad**: `F02.0.1`, `F02.0.2` y `F03` (425 rutas) purgadas a `.stale-bak/`.
- **`F01.0` apuntaba a un documento inexistente** (`0-indice-de-documentos-y-editor-modelo-documentbloc-servicios.md`); el real es `0.0-indice-documentos-y-editor.md`.
- **`units/F21.json` con `titulo: "F21"`** y ruta `F21-f21/F21-f21.md`.
- `OUT/OUT/` (artefacto de un `--out-root OUT/` mal pasado) eliminado.

## [0.3.0] — 2026-10-19 · Fase B2.1 (Catálogo de eventos FFI)

### Added

- `SKILL/scripts/build_catalog_events.py` — generador determinista que produce `OUT/11-catalogo-eventos-ffi.md` desde `OUT/_ledger/extract/events.json`. Carga el JSON, verifica `summary.total_variants == sum(len(crate.variants))`, renderiza 10 secciones (resumen + arquitectura Mermaid + resumen por crate + índice global de 229 + 8 sub-tablas por crate + tabla de sin_handler + prueba literal + cobertura cross-ref + preguntas abiertas + relacionado con) y normaliza las rutas `SRC/<fuente>/...` para que casen con `inventario.json::ruta_rel`.
- Modo `catalogue` en `SKILL/scripts/validate_template.py` — plantilla para documentos `11-*` del Bloque B2: id `^11-[a-z0-9-]+$`, 10 secciones obligatorias (`## 1.` … `## 10.`), estados `verificado`/`pendiente`. Sienta precedente para B2.2 (`12-`), B2.3 (`13-`), B2.4 (`14-`), B2.5 (`15-`) y B2.6 (`16-`).
- `OUT/_ledger/validate-B2.1.sh` — suite de 4 checks para la fase B2.1 (template + evidence + mermaid + count_rows).
- `OUT/_ledger/pruebas/B2.1/count_rows_229.py` — prueba literal del ROADMAP: cuenta filas en §4 (229), suma §5.* (229) y §6 (5) y exige coincidencia con `events.json::summary.{total_variants, total_sin_handler}`.
- `OUT/_ledger/pruebas/B2.1/README.md` — bitácora de la fase con métricas y comandos para regenerar.

### Changed

- `SKILL/scripts/validate_template.py` — auto-detección añade `catalogue` antes de `export` para `id` ∈ `^11-[a-z0-9-]+$`. Backward-compatible: las plantillas `feature`/`export`/`structure`/`bridge` y sus IDs existentes no se tocan.
- `OUT/00-INDEX.md` — regenerado vía `SKILL/scripts/build_index.py`; ahora lista `OUT/11-catalogo-eventos-ffi.md` (verificado) en §5 y §6, y resuelve el `[[11]]` que añade `build_index.py`.

### Fixed

- (Sin correcciones; la fase cierra en verde.)

## [0.2.0] — 2026-10-19 · Fase A5.2 (Ajuste de la skill)

### Added

- `SKILL/CHANGELOG.md` (este archivo). El ROADMAP y SKILL.md ya lo referenciaban como entregable de A5.2.
- `SKILL/scripts/run_subagent_placeholder.py` — copia del antiguo modo `autor` de `run_subagent.py`, renombrada y marcada como **mock de contrato A4.3**. **No** produce documentos reales.
- `SKILL/scripts/run_subagent_author.sh` — wrapper que invoca un LLM externo (variable `KILO_AUTHOR_CMD`, default `kilo --rol autor --input -`) para producir un `AutorOutput` real a partir de una unidad. Documenta cómo configurar el comando externo.
- Flag `--gate-100` en `SKILL/scripts/run_subagent.py` (modo `revisor`) para forzar `evidencia_minima_pct=100` sin importar la `feature_id`.
- Auto-elevación del `evidencia_minima_pct` al 100 % para `feature_id ∈ {F01, F02, F06}` y para unidades cuya `dependencias[].id` empieza por `B4.` (motor de export/import). El JSON de salida incluye los campos `muestreo_verificado.gate_100_explicit` y `muestreo_verificado.gate_100_auto` para que el orquestador exija el muestreo correcto.
- Campos de telemetría `muestreo_verificado.gate_100_explicit` y `muestreo_verificado.gate_100_auto` en el `RevisorOutput`.
- `OUT/_ledger/pruebas/A5.2/{README.md, validate-A5.2.sh, diff-references.patch}` — bitácora + smoke del gate + diff unificado de los cambios en `references/`.

### Changed

- `SKILL/scripts/run_subagent.py` — **solo** modo `revisor`. El modo `autor` se ha movido a `run_subagent_placeholder.py`. La ayuda (`--help`) y el docstring aclaran el flujo: placeholder para el contrato A4.3, `run_subagent_author.sh` para producción, `run_subagent.py --rol revisor` para validar.
- `SKILL/references/diagram-conventions.md` — añadidas 2 trampas de Mermaid detectadas en el piloto F08:
  - `classDiagram`: campos con `Option<T>` o `Vec<T>` rompen el parser; usar `Option` / `Vec` a secas (o un nombre sin `<>`).
  - `stateDiagram-v2`: los labels después de `:` son texto plano; nada de `<br/>` ni de paréntesis que contengan `:`.
- `SKILL/references/evidence-rules.md` — añadido ejemplo canónico con tres formas (válida con prefijo, válida con `appflowy:`, inválida ruta corta) y fila nueva en la tabla de consecuencias operativas para "ruta corta".
- `SKILL/references/subagent-contract.md` — nota explícita sobre `out_root` (raíz del proyecto, **no** `OUT/`), tabla de auto-elevación del `pct` y refuerzo del flujo de triage de `archivos_extra_detectados`.
- `SKILL/references/subagent-autor-prompt.md` — aviso de no usar `run_subagent_placeholder.py` esperando contenido real; recordatorio de ruta completa (`appflowy/...`) en las evidencias.
- `SKILL/references/subagent-revisor-prompt.md` — fila explícita `B4.* (motor export/import) → 100` en la tabla de muestreo; caso nuevo en "Errores recuperables" para cuando el orquestador invoca con `--gate-100` y el `pct` efectivo < 100.
- `SKILL/references/patterns.md` — sección nueva §9 que declara `OUT/_ledger/units/<id>.json` (A4.2) como la **fuente de verdad** del alcance de cada feature; las descripciones narrativas del ROADMAP son orientativas.

### Fixed

- **H1** (F08 §3): `classDiagram` con `Option~i64~` y `Vec~T~` →规范的写法: usar `Option` / `Vec` sin genéricos. Documentado en `diagram-conventions.md`.
- **H2** (F08 §11): `stateDiagram-v2` con `<br/>` y con `:` múltiples en labels →规范的写法: texto plano sin HTML, mover notas a la prosa. Documentado.
- **H3** (F08 §3–§19): rutas cortas tipo `manager.rs:42` en evidencias →规范的写法: `appflowy/frontend/rust-lib/.../manager.rs:42`. Documentado en `evidence-rules.md`.
- **H5** (F08 pre-flight): confusión sobre `--out-root` (se esperaba `OUT/`, debe ser raíz del proyecto) → documentado en docstring del script y en `subagent-contract.md` §2.
- **H6** (A5.1 revisión): auto-elevación del `evidencia_minima_pct` para features 🔒 no implementada → `--gate-100` y mapeo `feature_id → 100` ya activos.
- **H9** (F08 §18): 4 preguntas abiertas del piloto no volcadas al global → añadidas a `OUT/22-preguntas-abiertas.md` bajo "De F08 — Búsqueda e indexación (2026-10-18)".

### Removed

- (Nada eliminado; el modo `autor` se renombró, no se borró.)

## [0.1.0] — 2026-10-08 · Fases A0–A5.1

Esqueleto de la skill, extractores deterministas (A2.1–A2.7), validadores (A3.1–A3.5), orquestación (A4.1–A4.4) y primer piloto end-to-end (A5.1, F08 Búsqueda) aprobado con 21/21 archivos, 5/5 diagramas Mermaid, 101/101 referencias de evidencia y revisor `aprobado, 0 correcciones`. Detalle del cierre en `OUT/_ledger/pruebas/A5.1/README.md`.

Notas que aplican a todo 0.1.0:

- `run_subagent.py` (versión pre-A5.2) tenía **dos** modos (`autor` mock + `revisor` real). En 0.2.0 se separaron en `run_subagent_placeholder.py` y `run_subagent.py` para que el contrato A4.3 y la producción no compartan archivo.
- El piloto F08 descubrió 4 archivos no asignados a la unidad (`flowy-core/src/{deps_resolve/search_deps.rs, module.rs, lib.rs, app_life_cycle.rs}`) que el autor necesitó citar. Declarados en `OUT/_ledger/autor_f08_output.json::archivos_extra_detectados`. Triage: o se reasignan a F08, o se crean features nuevas `F2x`. Decisión pendiente para Parte B.
- Hallazgo técnico: la búsqueda NO viaja por `flowy-notification`; usa `IsolateSink` con `stream_port` (canal propio). El enum `SearchNotification` se compila pero está sin uso efectivo. Documentado en F08 §5 y en `OUT/22-preguntas-abiertas.md`.

## Cómo usar este CHANGELOG

- Antes de cada release (o cada vez que se cierre una fase A* / B*), añadir una entrada `## [X.Y.Z] — YYYY-MM-DD · Fase …` siguiendo el formato.
- Los cambios del análisis (`OUT/`) van en `OUT/22-preguntas-abiertas.md` o en el README de la fase correspondiente (`OUT/_ledger/pruebas/<fase>/README.md`), **no** aquí.
- Las entradas `### Removed` deben justificar el motivo y, si aplica, apuntar al archivo de migración.
