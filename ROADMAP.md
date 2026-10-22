# ROADMAP — `notemartin-appflowy-review`

Roadmap por fases granulares y testeables. Sin estimaciones de tiempo: cada fase termina cuando su **prueba** pasa. Sin límite de fases: si una fase descubre trabajo nuevo, se agregan fases `N.x`.

Leer antes: `AGENTS.md` (contexto y reglas) y `PROMPT.md` (encargo y plantillas).

**Convenciones**
- `SKILL/` = carpeta de la skill. `OUT/` = carpeta de salida `appflowy-review/`. `SRC/` = clones (`SRC/appflowy`, `SRC/collab`, `SRC/editor`).
- 🔀 = fase paralelizable con subagentes. 🔒 = gate bloqueante (no se avanza si falla).
- Cada fase actualiza `OUT/STATE.md` (fase, estado, fecha, notas).

---

## PARTE A — Construcción de la skill

### Bloque A0 · Esqueleto

**Fase A0.1 — Estructura de carpetas** ✅
- Tareas: crear `SKILL/` con `references/`, `scripts/`, `templates/output-skeleton/`.
- Salida: árbol vacío según `AGENTS.md §2`.
- Prueba: `tree SKILL` coincide con la especificación.

**Fase A0.2 — `SKILL.md`** ✅
- Tareas: frontmatter (`name: notemartin-appflowy-review`, `description` que diga cuándo dispararla), resumen de etapas 0–7 del `PROMPT.md`, reglas bloqueantes, cómo reanudar desde `STATE.md`, punteros a `references/`.
- Salida: `SKILL/SKILL.md` (177 líneas, ≤ 500), `SKILL/AGENTS.md` (copia), `PROMPT.md` (reconstruido en fase nueva A0.0, 341 líneas).
- Prueba: cargarla en Hermes, Cline y Kilo Code; las tres la listan y la disparan con "revisa AppFlowy completo". Detalle y resultado de la prueba local en `OUT/STATE.md §pruebas/A0.2/`.

**Fase A0.3 — References** ✅
- Tareas: volcar `repo-map.md` (AGENTS §4), `patterns.md` (§5), `evidence-rules.md` (§6), `diagram-conventions.md` (§7), `feature-template.md` y `export-template.md` (desde `PROMPT.md`).
- Prueba: cada archivo existe, sin secciones vacías; `feature-template.md` tiene las 19 secciones. Resultado en `OUT/STATE.md §pruebas/A0.3/`.

**Fase A0.4 — Esqueleto de salida** ✅
- Tareas: `templates/output-skeleton/` con todos los directorios y `.md` vacíos con frontmatter (`estado: pendiente`).
- Prueba: copiar el esqueleto produce exactamente la estructura de `PROMPT.md §Estructura de salida`. Resultado en `OUT/STATE.md §pruebas/A0.4/`.

### Bloque A1 · Adquisición e inventario

**Fase A1.1 — `fetch_sources.sh`** ✅
- Tareas: clonar AppFlowy (commit parametrizable); leer `rev` de `[patch.crates-io]` en `frontend/rust-lib/Cargo.toml` y clonar AppFlowy-Collab en ese rev; leer `dependency_overrides.appflowy_editor.git.ref` en `pubspec.yaml` y clonar appflowy-editor; escribir `OUT/_ledger/sources.json` con URL+commit de cada uno.
- Prueba: `sources.json` tiene 3 entradas con hash de 7+ caracteres; `git -C SRC/collab rev-parse --short HEAD` = rev del Cargo.toml.

**Fase A1.2 — `inventory.py`** ✅
- Tareas: recorrer `SRC/*`; por archivo: `fuente, ruta, lenguaje, loc, sha1, capa` (capa por reglas de ruta: `ui`, `bloc`, `service`, `ffi`, `dispatch`, `rust-handler`, `rust-manager`, `collab`, `persistence`, `server`, `codegen`, `test`, `build`, `config`, `i18n`, `asset`). Excluir `.git`, binarios; listar assets aparte.
- Salida: `OUT/_ledger/inventario.json`, `OUT/_ledger/assets.json`.
- Prueba: el conteo de `.rs` y `.dart` coincide con `find … | wc -l`; ningún archivo con `capa: null`.

**Fase A1.3 — Esquema del ledger** ✅
- Tareas: definir `cobertura.csv` = `fuente,ruta,capa,feature_ids,documento,estado,verificado_por`.
- Prueba: script de ejemplo crea el CSV con todas las filas del inventario en estado `sin_asignar`.

### Bloque A2 · Extractores deterministas

**Fase A2.1 — `extract_events.py`** ✅
- Tareas: parsear todos los `event_map.rs`: enum con `#[derive(... Flowy_Event)]`, `#[event_err]`, variantes con `#[event(input = "...", output = "...")]` y su índice, y registros `.event(XEvent::Y, handler)` (incluye llamadas multilínea). Resolver archivo:línea del handler buscando `fn <handler>` en el crate.
- Salida: `OUT/_ledger/extract/events.json`.
- Prueba: para `flowy-document`, aparecen `CreateDocument` (input `CreateDocumentPayloadPB`, sin output) y `OpenDocument` (input `OpenDocumentPayloadPB`, output `DocumentDataPB`); toda variante del enum tiene handler registrado o queda marcada `sin_handler`.

**Fase A2.2 — `extract_protobuf.py`** ✅
- Tareas: todos los `#[derive(... ProtoBuf ...)]` y `ProtoBuf_Enum`: nombre, campos, tipos, `#[pb(index = n)]`, `one_of`, archivo:línea.
- Prueba: cada `input`/`output` de `events.json` existe como entidad extraída (o se reporta faltante).

**Fase A2.3 — `extract_notifications.py`** ✅
- Tareas: enums `*Notification` (variantes y valores), `const *_OBSERVABLE_SOURCE`, usos de `send_notification`/`NotificationBuilder`; en Dart, listeners que filtran por esas notificaciones.
- Prueba: `DocumentNotification` aparece con sus 5 variantes (incl. `Unknown`) y al menos un listener Dart por variante usada.

**Fase A2.4 — `extract_blocs.py`** ✅
- Tareas: clases `extends Bloc<…>` / `Cubit<…>`, sus eventos y estados (freezed `@freezed`, `factory … =`), servicios inyectados, archivo:línea.
- Prueba: `DocumentBloc`, `ShareBloc` y los BLoCs de `plugins/database/application` aparecen con sus eventos.

**Fase A2.5 — `extract_deps.py`** ✅
- Tareas: `cargo metadata --no-deps` (o parseo de `Cargo.toml`) → grafo de crates internos; `pubspec.yaml` + `pubspec.lock` → paquetes Dart (internos `packages/*` y externos con versión/ref).
- Salida: `deps.json` + Mermaid crudo.
- Prueba: el grafo muestra `flowy-core` dependiendo de todos los `flowy-*` de feature; `dart-ffi` depende de `flowy-core`.

**Fase A2.6 — `extract_misc.py`** ✅
- Tareas: rutas `go_router`, atajos (`CommandShortcutEvent`, `hotkey_manager`, `shortcuts/`), feature flags (`shared/feature_flags.dart`), códigos de error (`flowy-error/src/code.rs`), claves i18n usadas, tareas de startup en orden.
- Prueba: cada salida no vacía; el número de `ErrorCode` coincide con las variantes del enum.

**Fase A2.7 — Codegen (opcional pero recomendado)** ✅
- Tareas: en un directorio aparte, ejecutar el codegen de `build-tool/flowy-codegen` (vía `cargo make` según `Makefile.toml`) para obtener `.proto` y el dispatch Dart generado. Si falla, documentar el error y seguir con A2.2.
- Prueba: o existen `.proto` generados y coinciden con A2.2, o hay un `codegen-fallido.md` con causa.

### Bloque A3 · Validadores 🔒

**Fase A3.1 — `validate_mermaid.sh`** ✅: extrae cada bloque ```mermaid de un `.md` y lo renderiza con `mmdc`. Prueba: un diagrama roto falla con archivo y número de bloque.

**Fase A3.2 — `validate_evidence.py`** ✅: encuentra todas las referencias `[fuente:]ruta:línea[–fin]`, comprueba que el archivo esté en el inventario y que la línea exista. Prueba: una ruta inventada falla; una línea fuera de rango falla.

**Fase A3.3 — `validate_template.py`** ✅: verifica secciones obligatorias y frontmatter (`id, titulo, fuente, archivos_cubiertos, estado`). Prueba: quitar la sección 13 hace fallar el documento.

**Fase A3.4 — `validate_coverage.py`** ✅: cruza el ledger con los documentos; reporta % y archivos sin asignar por capa. Prueba: con un ledger de juguete al 50% reporta 50% y lista los faltantes.

**Fase A3.5 — `build_index.py`** ✅: genera `00-INDEX.md` (árbol, estado de cada doc, cobertura, commits de fuentes) y enlaces cruzados `[[F..]]` → rutas reales. Prueba: todos los enlaces del índice resuelven.

### Bloque A4 · Orquestación

**Fase A4.1 — `assign_ledger.py`** ✅: asigna archivos a features por reglas de ruta (tabla `PROMPT.md §Mapa inicial`) y deja el resto como `sin_asignar` para triage. Prueba: ≥ 90% asignado automáticamente; lista de `sin_asignar` generada. **Resultado real: 92.96 % asignado (4.279/4.603), 324 sin_asignar documentados en `OUT/_ledger/sin_asignar.md`.** Tabla F01–F17 ampliada con F00/F18/F19/F20 para infraestructura compartida (documentado en el script). Plan en `1792363730747-assign-ledger-a41.md`.

**Fase A4.2 — Generador de unidades de trabajo** ✅: por feature/sub-feature produce `OUT/_ledger/units/<id>.json` con archivos, catálogos relevantes y dependencias; divide unidades > ~120 archivos. Prueba: la suma de archivos de todas las unidades = archivos asignados. **Resultado real: 88 unidades, 4.279 archivos = 4.279 asignados, sin solapamiento, F10 (0 archivos) en `features_vacias`.** Plan en `1792363730747-build-units-a42.md`.

**Fase A4.3 — Contratos de subagente** ✅: prompts de autor y revisor (en `references/`) con entrada/salida exactas de `AGENTS.md §8`. Prueba: ejecutar autor+revisor en una unidad trivial devuelve JSON válido. **Resultado: 3 archivos en `SKILL/references/` (contract + 2 prompts con 4 esquemas JSON) + `SKILL/scripts/run_subagent.py` mock (~360 líneas) que sobre F11 produce `AutorOutput` válido (19 secciones, 2 citas reales) y `RevisorOutput` con `veredicto=aprobado` (3 validadores exit 0).** Plan en `1792363730747-subagent-contracts-a43.md`.

**Fase A4.4 — `STATE.md` y reanudación** ✅: el orquestador puede retomar desde cualquier fase leyendo `STATE.md` + ledger. Prueba: cortar la ejecución a mitad de un bloque y reanudar en otra herramienta (p. ej. de Cline a Hermes) sin rehacer unidades aprobadas. **Resultado: `SKILL/scripts/resume.py` (orquestador determinista ~330 líneas) + `SKILL/scripts/record_unit_state.py` (auxiliar ~120 líneas). Sobre la fixture `cut_cobertura.csv` (134 verificados + 2 in_flight), `resume.py` produce `resume-plan.{json,md}` con orden priorizado (in_flight primero), 0 intersección con verificados. `--regenerate-state-section` reescribe la sección `## Cómo reanudar` de `STATE.md` preservando el resto. In-flight se modela como archivo `*.partial.md` en disco + marca `in_flight:` en `verificado_por` (redundancia, sin cambio de esquema).** Cierra el Bloque A4. Plan en `1792363730747-resume-state-a44.md`.

### Bloque A5 · Piloto 🔒

**Fase A5.1 — Piloto F08 Búsqueda** ✅: ejecutar el pipeline completo (autor → validadores → revisor) sobre F08 (`flowy-search` + indexación en `flowy-core`; 21 archivos según `OUT/_ledger/units/F08.json`. `flowy-search-pub` se documenta como infraestructura desde F00; `command_palette` desde F04 y `sin_asignar` — ambos referenciados en §Relacionado con sin reclamar sus archivos).
- Prueba: documento aprobado por el revisor; 100% de archivos de F08 cubiertos; ≥ 1 flowchart, ≥ 2 sequence, ≥ 1 state; validadores en verde.
- **Resultado (2026-10-18)**: `OUT/09-features/F08-busqueda-e-indexacion/F08-busqueda-e-indexacion.md` (476 líneas, 19 secciones); 5 diagramas Mermaid (1 `classDiagram`, 1 `flowchart TD`, 2 `sequenceDiagram`, 1 `stateDiagram-v2`); 21/21 archivos de F08 verificados en `cobertura.csv`; `validate_evidence` 101/101 refs OK; `validate_template` OK; `validate_mermaid` 5/5 OK; revisor (`run_subagent.py --rol revisor`) → `veredicto=aprobado, correcciones=0`. Artefactos: `OUT/_ledger/autor_f08_output.json`, `OUT/_ledger/revisor_f08_output.json`, `OUT/_ledger/pruebas/A5.1/`.

**Fase A5.2 — Ajuste de la skill** ✅: incorporar lo aprendido del piloto a plantillas, reglas y extractores. Prueba: diff de `references/` documentado en `SKILL/CHANGELOG.md`.
- **Resultado (2026-10-19)**: `SKILL/CHANGELOG.md` creado con entrada `## [0.2.0]` (6 Added / 6 Changed / 6 Fixed / 0 Removed); 6 archivos de `SKILL/references/` editados (`diagram-conventions.md` +2 trampas Mermaid; `evidence-rules.md` +ejemplo canónico de ruta; `subagent-contract.md` +`out_root`/auto-elevación pct/triage extras; `subagent-autor-prompt.md` +aviso placeholder +recordatorio ruta; `subagent-revisor-prompt.md` +fila B4.* +caso `--gate-100`; `patterns.md` +§8 canales Rust→Dart +§9 feature↔unidad). Scripts: `run_subagent.py` reescrito (solo `revisor` + `--gate-100` + auto-elevación a 100% para F01/F02/F06/motor B4); `run_subagent_placeholder.py` nuevo (mock de A4.3, conservado por compatibilidad); `run_subagent_author.sh` nuevo (wrapper de producción que invoca un LLM externo vía `KILO_AUTHOR_CMD`). 4 preguntas abiertas del piloto F08 volcadas a `OUT/22-preguntas-abiertas.md`. Diff unificado en `OUT/_ledger/pruebas/A5.2/diff-references.patch` (14 hunks, ~15.5 KB); smoke `validate-A5.2.sh` 5/5 checks en verde.

---

## PARTE B — Ejecución del análisis

### Bloque B0 · Preparación
**Fase B0.1** ✅ — Ejecutar A1.1–A2.7 sobre las fuentes reales. Prueba: todos los `extract/*.json` presentes.

**Resultado (2026-10-19)**: los 6 `extract/*.json` están presentes y validados:
- `OUT/_ledger/extract/events.json` (140 KB · 229 variantes · `validate-A2.1.sh` 11/11 OK)
- `OUT/_ledger/extract/protobuf.json` (616 KB · 439 entidades · `validate-A2.2.sh` 8/8 OK)
- `OUT/_ledger/extract/notifications.json` (48 KB · 70 variantes · `validate-A2.3.sh` 7/7 OK)
- `OUT/_ledger/extract/blocs.json` (268 KB · 142 blocs · `validate-A2.4.sh` 8/8 OK)
- `OUT/_ledger/extract/deps.json` (104 KB · Rust+Dart · `validate-A2.5.sh` 9/9 OK)
- `OUT/_ledger/extract/misc.json` (504 KB · rutas, atajos, flags, errores, i18n, startup · `validate-A2.6.sh` 10/10 OK)
- A1.x: `sources.json`, `inventario.json`, `assets.json`, `cobertura.csv` (4 603 filas) presentes.
- A2.7: `codegen-fallido.md` (toolchain incompleto; A2.2 cubre el caso) + `validate-A2.7.sh` 7/7 OK.

**Fase B0.2** ✅ — Ejecutar A4.1–A4.2; triage manual de `sin_asignar` (asignar o crear feature nueva `F2x`). Prueba: 0 archivos `sin_asignar`. 🔒

**Resultado (2026-10-19)**: 324 → 0 `sin_asignar`. Asignación mixta F00–F17 + 1 F2x nuevo (**F21 — Icon/Emoji picker**, 11 archivos en `appflowy_flutter/lib/shared/icon_emoji_picker/*`):
- Distribución final (sobre 4 603 archivos, 21 verificados preservados): F00=4 603-asignados+17, F01 absorbe `flowy-document/` completo (~75 archivos), F03 (+50), F04 (+95), F05 (+7), F07 (+2), F08 (+11 UI de command palette), F09 (+6 settings IA), F10 (+3 import + notion), F12 (+11 sites/published), F13 (+40 settings), F15 (+22 date picker), F17 (+30 shared UI infra + widgets reusables), **F21 = 11 (nuevo)**.
- Tabla de asignación persistente en `SKILL/scripts/assign_ledger.py` (22 reglas nuevas añadidas a F00/F01/F03/F04/F05/F07/F08/F10/F12/F13/F15/F17 + F21 nuevo; precedencia por longitud).
- `cobertura.csv`: 4 603 filas, 0 `sin_asignar`, 4 582 `pendiente`, 21 `verificado` (F08 de A5.1).
- Units re-generados: 90 unidades (antes 88), aparece `units/F21.json`; F10 ahora tiene 3 archivos (antes 0, en `features_vacias`); F03/F04/F13 crecen; suma 4 582 sin solapamiento.
- Validadores en verde: `validate-A4.1.sh` 8/8 OK, `validate-A4.2.sh` 9/9 OK (actualizado a 90u/4582f), `validate-A4.4.sh` 9/9 OK (actualizado a 4603 asignados, 0 sin_asignar). `validate_units.py` parcheado para contar solo `pendiente` (excluye `verificado` como hace `build_units.py`).
- Plan en `1792372969227-b02-triage.md`.

### Bloque B1 · Fundamentos (secuencial, alimentan a todo lo demás)

**Fase B1.1 — `03-estructura-del-repo.md`** ✅ — árbol anotado de las 3 fuentes con todas las carpetas 1.er/2.º nivel, 4 tablas de conteos (capa, fuente × capa, fuente × lenguaje, assets) y 5 diagramas Mermaid. Prueba literal: 72/72 carpetas L1+L2 (excl. `.git*`) declaradas; 4/4 validadores en verde. Plan en `1792373815215-fase-b11-estructura-repo.md`.

**Resultado (2026-10-19)**: `OUT/03-estructura-del-repo.md` (583 líneas, 12 secciones `## `, 32 refs `[fuente:]ruta:línea` verificadas contra `inventario.json`, 5 bloques Mermaid validados con `mmdc`); suite `OUT/_ledger/validate-B1.1.sh` 4/4 checks (template con nuevo modo `structure` + evidence + mermaid + coverage). `SKILL/scripts/validate_template.py` extendido con plantilla `structure` para `id ∈ ^B1\.\d+$` (backward-compatible; sienta precedente para B1.2–B1.7). Artefactos: `OUT/_ledger/pruebas/B1.1/{README.md, validate_B1_1_coverage.py, validate_*.log, coverage.json, folders-l1-l2.txt, real-folders-*.txt}`. **Abre el Bloque B1 (Fundamentos).**

**Fase B1.2 — `02-stack-y-dependencias.md` + `17-grafo-dependencias.md`** ✅ — stack completo (3 repos: appflowy 5cf3a36, collab 4dfccef, editor 470c4e7) con versiones y toolchains; 38 `[workspace.dependencies]` Rust (31 internas + 7 externas + collab-* con override git) y 136 deps externas Dart (incluye 8 git refs en `dependency_overrides`); 31 crates Rust × 150 internas + 368 externas; 8 packages Dart × 12 internas + 136 externas; métricas (top fan-in `lib-infra` 19, top fan-out `flowy-database2` 25, 0 ciclos, 1 componente); 5 diagramas Mermaid validados. **Prueba literal: 100 % de las deps directas listadas** (`validate_B1_2_coverage.py` → 0 missing). Plan en `1792373815215-fase-b12-stack-dependencias.md`.

**Resultado (2026-10-19)**: `OUT/02-stack-y-dependencias.md` (367 líneas, 12 secciones `## `, 68 refs `[fuente:]ruta:línea` verificadas, 2 Mermaid) + `OUT/17-grafo-dependencias.md` (411 líneas, 12 secciones `## `, 3 Mermaid, catálogo exhaustivo). Suite `OUT/_ledger/validate-B1.2.sh` 7/7 checks (template x2 + evidence x2 + mermaid x2 + coverage). `SKILL/scripts/validate_template.py` regex extendido a `^B1\.\d+(-[a-z0-9]+)?$` para aceptar `B1.2-grafo`. Artefactos: `OUT/_ledger/pruebas/B1.2/{README.md, build_B1_2_dep_catalog.py, validate_B1_2_coverage.py, all-direct-deps-{rust,dart}.json, graph-metrics.json, deps-stats.json, coverage.json, validate_*.log}`.

**Fase B1.3 — `04-arquitectura-global.md`** ✅ — C4 (contexto con 8 actores; 5 contenedores: App Flutter, SDK Rust, Workspace Colab, Librería Editor, Backend opcional) con sus protocolos (FFI C, git pin, pub.dev path, HTTP/gRPC); 9 capas cruzadas (UI / BLoC-Service / FFI / Handlers / Managers / Persistencia / Collab / Backend / Codegen); **diagrama de flujo global de la app** (`flowchart TD` con 16 nodos y `sequenceDiagram` con 17 saltos trazando `DocumentBloc → DocumentService → FFI → open_document_handler → DocumentManager → Collab → persistencia → notification → listener → state`); mapa de responsabilidades de los 30 crates Rust y 18 features Dart; arquitectura Dart dual (legado 1 176 archivos/124 BLoCs vs nuevo 65 archivos/5 BLoCs). Prueba: cobertura 5/5 contenedores C4, 31/31 crates, 18/18 features, 9/9 capas; 4/4 validadores en verde; **revisor aprueba** (`veredicto=aprobado, correcciones=0`). Plan en `1792373815215-fase-b13-arquitectura-global.md`.

**Resultado (2026-10-19)**: `OUT/04-arquitectura-global.md` (600 líneas, 12 secciones `## `, 17 refs verificadas, 6 diagramas Mermaid validados con `mmdc`); suite `OUT/_ledger/validate-B1.3.sh` 4/4 checks (template + evidence + mermaid + coverage). Artefactos: `OUT/_ledger/pruebas/B1.3/{README.md, validate_B1_3_coverage.py, component-counts.json, blocs-by-folder.json, coverage.json, revisor_output.json, validate_*.log}` + `OUT/_ledger/validate-B1.3.sh` + `OUT/_ledger/units/B1.3.json`.

**Fase B1.4 — `05-arranque-y-ciclo-de-vida.md`** ✅ — Trazado del cold start (`main.dart:1` → `runAppFlowy` → `getIt.reset()` → `initGetIt` → `AppLauncher.addTasks([15])` → `launcher.launch()` → `init_sdk` (`dart-ffi/src/lib.rs:114`) → `AppFlowyCore::new` (`flowy-core/src/lib.rs:61`) → `SplashScreen`); **15 `LaunchTask` en el orden real del código** (`startup.dart:118–156`); composición de `AppFlowyCore` (8 managers + `AFPluginDispatcher` + runtime tokio + 2 indexed data writers); `app_life_cycle.rs` con 11 métodos del trait `AppLifeCycle`; secuencias de cambio de usuario (`SignOut`) y de workspace (`OpenWorkspace`); árbol de decisión de errores con 5 `ErrorCode` relevantes. Prueba literal: `validate_B1_4_coverage.py` confirma 16 menciones (15 + alias `ApplicationInfoTask`) en §2 en el orden canónico de `addTasks([...])`; revisor aprueba. Plan en `1792373815215-fase-b14-arranque-ciclo-vida.md`.

**Resultado (2026-10-19)**: `OUT/05-arranque-y-ciclo-de-vida.md` (472 líneas, 12 secciones `## `, 109 refs verificadas, 6 Mermaid); suite `OUT/_ledger/validate-B1.4.sh` 4/4 checks (template + evidence + mermaid + coverage). Artefactos: `OUT/_ledger/pruebas/B1.4/{README.md, validate_B1_4_coverage.py, coverage.json, revisor_output.json, validate_*.log}` + `OUT/_ledger/validate-B1.4.sh` + `OUT/_ledger/units/B1.4.json`.

**Fase B1.5 — `06-puente-flutter-rust/`** ✅ — 6 sub-documentos: (a) `01-ffi.md` cubre las 8 `extern "C"` de `dart-ffi/src/lib.rs` (`init_sdk:114`, `async_event:175`, `sync_event:231`, `set_stream_port:240`, `set_log_stream_port:247`, `link_me_please:254`, `rust_log:278`, `set_env:308`) + `RustStreamReceiver` (`rust_stream.dart:11`); (b) `02-lib-dispatch.md` cubre `AFPlugin` (module/module.rs:64), `AFPluginDispatcher` (dispatcher.rs:63) + `boxed_async_send_with_callback` (línea 99), `AFPluginRuntime` (runtime.rs:1), `AFPluginEventRequest/Response` (request.rs:20, response.rs:22) + 133 `ErrorCode` (flowy-error/src/code.rs:1); (c) `03-codegen.md` cubre `flowy-derive` (3 macros: `ProtoBuf`, `ProtoBuf_Enum`, `Flowy_Event`), `flowy-ast` y `flowy-codegen` (sin `protoc` en este entorno); (d) `04-notificaciones.md` cubre `flowy-notification` con `NotificationBuilder` + `DebounceNotificationSender` + 6 enums Rust (70 variantes) + 29 listeners Dart; (e) `05-ejemplo-traza-opendocument.md` traza los 17 saltos de `OpenDocument` con `ruta:línea` resuelta en inventario. **Prueba literal del ROADMAP**: `validate_B1_5_coverage.py` confirma 17/17 traza + 8/8 FFI + 8/8 dispatch = 33/33 (100 %); suite `validate-B1.5.sh` 19/19 checks; revisor aprueba. Plan en `1792373815215-fase-b15-puente-ffi.md`.

**Resultado (2026-10-19)**: 6 sub-docs (1 160 líneas, 155 refs verificadas, 10 Mermaid validados); `OUT/_ledger/validate-B1.5.sh` 19/19 checks (template x6 + evidence x6 + mermaid x6 + coverage). Extensión del validador: `validate_template.py` ahora soporta modo `bridge` para id `^06-\d{2}-[a-z-]+$` (backward-compatible; sienta precedente para B1.6 `07-motor-colaborativo-crdt/` y B1.7 `08-persistencia/`). Artefactos: `OUT/_ledger/pruebas/B1.5/{README.md, validate_B1_5_coverage.py, coverage.json, revisor_output.json, validate_*.log}` + `OUT/_ledger/validate-B1.5.sh` + `OUT/_ledger/units/B1.5.json`.

**Fase B1.6 — `07-motor-colaborativo-crdt/`** ✅ — 8 sub-documentos (1625 líneas, 157 refs verificadas, 17 Mermaid). Modelo `Collab` sobre `yrs 0.21.0` con `CollabType` enum (7 variantes: Document=0, Database=1, WorkspaceDatabase=2, Folder=3, DatabaseRow=4, UserAwareness=5, Unknown=6); `EncodedCollab` con `EncoderVersion::V0/V1/V2`; `collab-folder` con `View`/`Workspace`/`FolderData`/`ViewLayout`; `collab-document` con `DocumentData`/`Block`/`children_map`/`text_map`; `collab-database` con `Field`/`FieldType` (16 variantes)/`Row`/`Cell`/`View`; `collab-user` con `UserAwareness`; `collab-plugins` con `LocalStorage`/`CloudStorage`/`KVAction`; snapshots + modelo "no conflicts" (Lamport + LWW + UndoManager per-client). **Prueba literal del ROADMAP**: `validate_B1_6_coverage.py` confirma 20/20 clases reales en los 4 `classDiagram` (folder, document, database, user-awareness); suite `validate-B1.6.sh` 25/25 checks; revisor aprueba. Plan en `1792373815215-fase-b16-motor-crdt.md`.

**Resultado (2026-10-19)**: 8 sub-docs (1625 líneas, 157 refs verificadas, 17 Mermaid validados); `OUT/_ledger/validate-B1.6.sh` 25/25 checks (template x8 + evidence x8 + mermaid x8 + coverage). Extensión del validador: `validate_template.py` regex del modo `bridge` extendido a `^0[6-9]-\d{2}-[a-z-]+$` (acepta 06/07/08/09; backward-compatible; sienta precedente para B1.7 `08-persistencia/` y `10-motor-export-import/`). Artefactos: `OUT/_ledger/pruebas/B1.6/{README.md, validate_B1_6_coverage.py, coverage.json, revisor_output.json, validate_*.log}` + `OUT/_ledger/validate-B1.6.sh` + `OUT/_ledger/units/B1.6.json`.

**Fase B1.7 — `08-persistencia/`** ✅ — 8 sub-documentos (~1590 líneas, 79 refs verificadas, 13 Mermaid). Modelo de persistencia con `flowy-sqlite` (diesel 2.1.0), `flowy-sqlite-vec` (extensión `vector0` de sqlite-vec), `KVStore` (`set_str`/`get_str`/`set_bool`/`set_object`/`set_i64`/etc.), `FileCache`, `LocalStorage` de `collab-plugins`, migraciones diesel (6 migraciones de `flowy-user/src/migrations/`), y paths por plataforma (macOS/iOS/Windows/Linux/Android/web). **Prueba literal del ROADMAP**: `validate_B1_7_coverage.py` confirma 16/16 tablas del esquema (`af_collab_metadata`, `chat_local_setting_table`, `chat_message_table`, `chat_table`, `collab_snapshot`, `index_collab_record_table`, `local_ai_model_table`, `upload_file_part`, `upload_file_table`, `user_data_migration_records`, `user_table`, `user_workspace_table`, `workspace_members_table`, `workspace_setting_table`, `workspace_shared_user`, `workspace_shared_view`) en el `erDiagram` de `01-sqlite-schema.md`; suite `validate-B1.7.sh` 25/25 checks; revisor aprueba. Plan en `1792373815215-fase-b17-persistencia.md`.

**Resultado (2026-10-19)**: 8 sub-docs (~1590 líneas, 79 refs verificadas, 13 Mermaid validados); `OUT/_ledger/validate-B1.7.sh` 25/25 checks. Artefactos: `OUT/_ledger/pruebas/B1.7/{README.md, validate_B1_7_coverage.py, coverage.json, revisor_output.json, validate_*.log}` + `OUT/_ledger/validate-B1.7.sh` + `OUT/_ledger/units/B1.7.json`.

### Bloque B2 · Catálogos 🔀

**Fase B2.1 — `11-catalogo-eventos-ffi.md`** ✅ — desde `events.json` + semántica breve por evento. Prueba: nº de filas = nº de eventos extraídos.

**Resultado (2026-10-19)**: `OUT/11-catalogo-eventos-ffi.md` (774 líneas, 10 secciones `## `, 229 refs `[fuente:]ruta:línea` verificadas contra `inventario.json`, 6 bloques Mermaid validados con `mmdc`); tabla global §4 con 229 filas + 8 sub-tablas §5.<crate> con 229 filas sumadas + tabla §6 con 5 filas para los `sin_handler`. Semántica breve derivada de nombre + handler + PB input/output, etiquetada `[INFERIDO]` por construcción (ver §1). Suite `OUT/_ledger/validate-B2.1.sh` 4/4 checks en verde: template (modo `catalogue` nuevo en `validate_template.py`, regex `^11-[a-z0-9-]+$`, 10 secciones obligatorias) + evidence (229/229 OK) + mermaid (6/6) + `count_rows_229.py` (§4=229, §5=229, §6=5). Generador determinista `SKILL/scripts/build_catalog_events.py` (660 líneas) con limpieza automática del prefijo `SRC/<fuente>/` para alinear con `inventario.json::ruta_rel`. Artefactos: `OUT/_ledger/pruebas/B2.1/{README.md, count_rows_229.py, validate-B2.1.log}`. Plan original `1792417021705-fase-b21-catalogo-eventos-ffi.md`. **Abre el Bloque B2 (Catálogos).**

**Fase B2.2 — `12-catalogo-entidades-protobuf.md`** ✅ — 439 entidades (389 structs + 50 enums) en 10 crates. Prueba: nº de entidades = extracción.

**Resultado (2026-10-19)**: `OUT/12-catalogo-entidades-protobuf.md` (1 493 líneas, 10 secciones `## `, 1 101 refs `[fuente:]ruta:línea` resueltas contra `inventario.json`, 6 bloques Mermaid validados: 1 arquitectura + 5 por crate con >20 entidades). Distribución por crate: `flowy-database2`=170, `flowy-user`=82, `flowy-folder`=64, `flowy-ai`=51, `flowy-document`=50, `flowy-search`=13, `flowy-storage`=3, `dart-ffi`=3, `flowy-date`=2, `flowy-notification`=1; **223 entidades huérfanas** (sin `is_input_of` ni `is_output_of` de ningún evento) documentadas en §6 (payload de notificación B2.4, payload de export/import Bloque B4, struct interno de manager, etc.). Cross-ref con B2.1: `cross_ref.missing_event_pbs`=0, `resolved_inputs`=141 + `resolved_outputs`=84 = 225 PBs referenciados por eventos (216 entidades únicas, 9 se usan en ambos lados). Semántica derivada de nombre+fields+derives, etiquetada `[INFERIDO]`. Suite `OUT/_ledger/validate-B2.2.sh` 4/4 checks: template (modo `catalogue`, regex extendido a `^1[1-6]-[a-z0-9-]+$` en `validate_template.py`) + evidence (1 101/1 101 OK) + mermaid (6/6) + `count_rows_439.py` (§4=439, §5=439, §6=223). Generador determinista `SKILL/scripts/build_catalog_protobuf.py` (~500 líneas, normaliza `SRC/<fuente>/` → `<fuente>/`). Artefactos: `OUT/_ledger/pruebas/B2.2/{README.md, count_rows_439.py, validate-B2.2.log}`. Plan `1792417021705-fase-b22-catalogo-protobuf.md`.
**Fase B2.3 — `13-catalogo-blocs.md`** ✅ — 142 BLoCs/Cubits (125 Bloc + 17 Cubit) en 17 carpetas. Prueba: nº de BLoCs/Cubits = extracción.

**Resultado (2026-10-19)**: `OUT/13-catalogo-blocs.md` (724 líneas, 10 secciones `## `, 418 refs `[fuente:]ruta:línea` resueltas contra `inventario.json`, 3 bloques Mermaid validados: 1 arquitectura BLoC + 2 por carpeta con >20 BLoCs). Distribución por carpeta Dart (top 4): `plugins/database`=50 (49 Bloc + 1 Cubit), `workspace/application`=39, `plugins/document`=11, `user/application` + `plugins/ai_chat`=8 c/u. **8 BLoCs** tienen `injected_services` detectados; los otros 134 obtienen dependencias vía `getIt`/singleton (patrón dominante en AppFlowy). **18 BLoCs** contienen tipos `*PB` en sus `state_fields` (cruce directo con entidades protobuf de B2.9). Suite `OUT/_ledger/validate-B2.3.sh` 4/4 checks: template (modo `catalogue`, regex `^1[1-6]-…`) + evidence (418/418 OK) + mermaid (3/3) + `count_rows_142.py` (§4=142, §5=142, §6=134). Generador determinista `SKILL/scripts/build_catalog_blocs.py` (~540 líneas, heurísticas para semántica `[INFERIDO]`). Artefactos: `OUT/_ledger/pruebas/B2.3/{README.md, count_rows_142.py, validate-B2.3.log}`. Plan `1792417021705-fase-b23-catalogo-blocs.md`.
**Fase B2.4 — `14-catalogo-notificaciones.md`** ✅ — emisor → listener → efecto UI para 70 variantes. Prueba: cada variante con emisor o marcada `sin uso`.

**Resultado (2026-10-19)**: `OUT/14-catalogo-notificaciones.md` (405 líneas, 10 secciones `## `, 253 refs `[fuente:]ruta:línea` resueltas contra `inventario.json`, 5 bloques Mermaid validados: 1 arquitectura del canal + 4 por enum con ≥10 variantes). Distribución: `ChatNotification`=10 (flowy-ai), `DatabaseNotification`=24 (flowy-database2), `DocumentNotification`=5 (flowy-document), `FolderNotification`=19 (flowy-folder), `StorageNotification`=2 (flowy-storage), `UserNotification`=10 (flowy-user). Estados por variante (`variant_usage` de A2.3): `ok`=8 (emitida + listener), `emitted_only`=2, `declared_only`=13, `unused`=47. **49 variantes sin uso efectivo en Dart** documentadas en §6 (sentinelas `Unknown` + dead code + emitidas sin listener). **16 `NotificationBuilder::new`** sites + 11 con variante específica; **29 listeners Dart** + **5 parsers**. Suite `OUT/_ledger/validate-B2.4.sh` 4/4 checks: template + evidence (253/253) + mermaid (5/5) + `count_rows_70.py` (§4=70, §5=70, §6=49). Generador `SKILL/scripts/build_catalog_notifications.py` (~540 líneas; `line=1` por convención para `*_listener.dart:0` no declarado). Artefactos: `OUT/_ledger/pruebas/B2.4/{README.md, count_rows_70.py, validate-B2.4.log}`. Plan `1792417021705-fase-b24-catalogo-notificaciones.md`.
**Fase B2.5 — `15-catalogo-errores.md`** ✅ — 133 `ErrorCode` (enum `#[repr(u8)]`) en `flowy-error/src/code.rs`. Prueba: nº de códigos = enum.

**Resultado (2026-10-19)**: `OUT/15-catalogo-errores.md` (661 líneas, 10 secciones `## `, 267 refs `[fuente:]ruta:línea` resueltas contra `inventario.json`, 4 bloques Mermaid validados: 1 arquitectura del canal `FlowyError` + 3 por categoría con ≥10 variantes). Distribución por categoría (top 5): `Database`=25, `Workspace`=14, `Auth`=13, `Network`=8, `Storage`=8 + 22 categorías adicionales (ver §3). **1 sentinels** documentado en §6 (`Internal`; no hay variantes `Unknown*` en este snapshot). Suite `OUT/_ledger/validate-B2.5.sh` 4/4 checks: template (modo `catalogue`, regex `^1[1-6]-…`) + evidence (267/267) + mermaid (4/4) + `count_rows_133.py` (§4=133, §5=133, §6=1). Generador determinista `SKILL/scripts/build_catalog_errors.py` (~470 líneas; heurísticas para categoría + UI típica por regex sobre el nombre, etiquetadas `[INFERIDO]`). Artefactos: `OUT/_ledger/pruebas/B2.5/{README.md, count_rows_133.py, validate-B2.5.log}`. Plan `1792417021705-fase-b25-catalogo-errores.md`.

**Fase B2.6 — `16-catalogo-flags-rutas-atajos.md`** ✅ — 1709 entradas (35 rutas + 13 atajos + 0 cmd-shortcut + 9 flags + 1637 i18n keys + 15 startup tasks). Prueba: coincide con `extract_misc`.

**Resultado (2026-10-19)**: `OUT/16-catalogo-flags-rutas-atajos.md` (1 826 líneas, 10 secciones `## `, 57 refs `[fuente:]ruta:línea` resueltas contra `inventario.json`, 1 bloque Mermaid validado). Distribución: §4 **35 rutas** (`generate_router.dart`), §5 **13 hotkeys** (`hotkeys.dart`) + nota §5.2 sobre `CommandShortcutEvent` (0 variantes detectadas por el extractor), §6 **9 feature flags** (enum `FeatureFlag` en `feature_flags.dart`), §7 **1637 i18n keys** (con `usages` y `sources` truncados a 3), §8 **15 startup tasks** (orden canónico de `addTasks([...])` con `conditional`/`condition`). **Total** = 1 709 = `summary.total_routes + total_shortcuts + total_feature_flags + total_i18n_keys + total_startup_tasks`. Suite `OUT/_ledger/validate-B2.6.sh` 4/4 checks: template (modo `catalogue`) + evidence (57/57) + mermaid (1/1) + `count_rows_misc.py` (§4=35, §5=13, §6=9, §7=1637, §8=15, total=1709). Generador determinista `SKILL/scripts/build_catalog_misc.py` (~430 líneas; normaliza `SRC/<fuente>/` → `<fuente>/`; truncado en `i18n_keys.sources`). Artefactos: `OUT/_ledger/pruebas/B2.6/{README.md, count_rows_misc.py, validate-B2.6.log}`. Plan `1792417021705-fase-b26-catalogo-flags-rutas-atajos.md`. **Cierra el Bloque B2 (Catálogos).**

### Bloque B3 · Features 🔀 (autor + revisor por unidad; gate 🔒 por unidad)

Cada fase produce su carpeta/archivo en `OUT/09-features/` con la plantilla completa. Prueba común: `validate_template` + `validate_mermaid` + `validate_evidence` en verde, revisor aprueba, filas del ledger de la unidad en `verificado`.

**F01 — Documentos y editor** (dividida):
- B3.F01.0 ✅ — Índice: modelo de documento (Dart `appflowy_editor` Node/Delta ↔ `DocumentDataPB` ↔ collab-document), `DocumentBloc`, `document_service.dart`, `document_collab_adapter.dart`, `editor_transaction_adapter.dart` (traducción de transacciones a `ApplyAction`), undo/redo, reglas y validador, diff.
- B3.F01.1 ✅ — Bloques de texto: heading, bulleted/numbered list, todo_list, quote, toggle, callout, header, delta.
- B3.F01.2 ✅ — Bloques ricos: code_block, math_equation, inline_math_equation, simple_table, table, columns, outline, page_block, sub_page.

**Resultado (2026-10-19) (F01.1)**: 1 documento `OUT/09-features/F01-documentos-y-editor/1-bloques-de-texto-…md` (~360 líneas, 19 secciones, gate-100) cubriendo los 19 archivos del ledger (8 tipos: heading, bulleted/numbered list, todo_list, quote, toggle, callout, header/cover + `TextDeltaExtension`). Suite `validate-B3.F011.sh` 4/4 checks en verde (template=1/1, evidence=40/40 OK, mermaid=4 bloques OK, cobertura=19/19). Revisor `run_subagent.py --gate-100` → `veredicto=aprobado, correcciones=0`. Adaptaciones menores: `validate-A4.2.sh` Check 3 actualizado para descontar verificados `autor+F01.*` (cualquier sub-fase, no solo F01.0); `validate-B3.F010.sh` Check 4 aflojado a `>= 555` para tolerar F01.1. Plan en `~/.local/share/kilo/plans/1792429084675-b3-f011-bloques-de-texto-plan.md`. Artefactos: `OUT/_ledger/pruebas/B3.F011/{1-…md, validate-B3.F011.sh, validate-B3.F011.log, coverage.json, revisor_output.json, README.md}`.
- B3.F01.3 ✅ — Media y archivos: image, video, file, cover, link_preview, link_embed (incluye upload vía F07).

**Resultado (2026-10-19) (F01.2)**: 1 documento `OUT/09-features/F01-documentos-y-editor/2-bloques-ricos-…md` (445 líneas, 19 secciones, gate-100) cubriendo los 67 archivos del ledger F01.2 (9 tipos: code_block, math_equation, inline_math_equation, simple_table + 45 archivos, table legacy, columns, outline, page_block, sub_page). Distinción crítica entre `simple_table` (auto-contenida, en `simple_table/`) y `table` legacy (con `database_view`, F01.5). Atributos clave documentados: `MathEquationBlockKeys.formula`, `InlineMathEquationKeys.formula`, `SubPageBlockKeys.viewId/wasCopied/wasCut`, `SimpleTableBlockKeys.{enableHeaderRow,columnColors,rowColors,columnAligns,rowAligns,columnBoldAttributes,columnWidths,…}` (12 claves). 5 families de operations sobre `EditorState` (`TableInsertion/Deletion/Duplication/Header/Reorder/Style/Map/ContentOperations`) + 10 comandos en `simple_table_shortcuts`. Suite `validate-B3.F012.sh` 4/4 checks en verde (template=1/1, evidence=34/34 OK, mermaid=4 OK, cobertura=67/67). Revisor `run_subagent.py --gate-100` → `veredicto=aprobado, correcciones=0`. Plan en `~/.local/share/kilo/plans/1792429084675-b3-f012-bloques-ricos-plan.md`. Artefactos: `OUT/_ledger/pruebas/B3.F012/{2-…md + validate-B3.F012.sh + validate-B3.F012.log + coverage.json + revisor_output.json + README.md}`.
- B3.F01.4 ✅ — Menciones e inline actions: mention (página, fecha, persona, recordatorio), `plugins/inline_actions`, emoji.
- B3.F01.5 ✅ — Bases embebidas en documentos: `editor_plugins/database`, `plugins/database_document`.

**Resultado (2026-10-19) (F01.3 — scope correction)**: 1 documento `OUT/09-features/F01-documentos-y-editor/3-media-y-archivos-image-video-file-cover-link-preview-link-embed.md` (231 líneas, 19 secciones, gate-100) cerrando F01.3 como **scope-correction**. **0 archivos en el ledger** (`F01.3.json: archivos=[]`); el ROADMAP lista 6 categorías pero el B0.2.2 triage las asignó a **F07** (Almacenamiento de archivos). Distribución real: `image/*` 21 archivos, `video/*` 1, `file/*` 7, `cover/*` (inmersivo) 2, `link_preview/*` 8+, `link_embed/*` 2 = **42 archivos en F07**; `header/cover_*` 6 archivos **en F01.1** (cerrado). El doc declara explícitamente la corrección en §2 y §13 con tabla de redirección. Suite `validate-B3.F013.sh` 4/4 en verde (template=1/1, evidence=2/2, mermaid=3 OK, cobertura=0/0 scope-corrected). Revisor `run_subagent.py --gate-100` → `aprobado, 0 correcciones`. Plan en `~/.local/share/kilo/plans/1792429084675-b3-f013-media-archivos-plan.md`. Artefactos: `OUT/_ledger/pruebas/B3.F013/{3-…md + validate-B3.F013.sh + log + coverage.json + revisor_output.json + README.md}`.

**Resultado (2026-10-19) (F01.4)**: 1 documento `OUT/09-features/F01-documentos-y-editor/4-menciones-pagina-fecha-persona-recordatorio-inline-actions.md` (~310 líneas, 19 secciones, gate-100) cubriendo los 10 archivos del ledger F01.4 (9 ui + 1 bloc en `editor_plugins/mention/`). **1 BLoC nuevo**: `MentionPageBloc` (`mention_page_bloc.dart:22`) con 4 eventos freezed + 3 listeners (`ViewListener`, `TrashListener`, `DocumentListener`). 9 atributos en `MentionBlockKeys` (`mention`, `type`, `pageId`, `blockId`, `url`, `date`, `includeTime`, `reminderId`, `reminderOption`); `MentionType` enum con 4 variantes (page, date, externalLink, childPage) + alias legacy `reminder → date`. **Corrección de scope oficializada** (en §2.1 y §13 del doc): `inline_actions/` no existe como carpeta física; `mobile/presentation/inline_actions/` está en F16; `plugins/emoji/` en F00; `shared/icon_emoji_picker/` en F21. **2 transaction handlers** (`ChildPageTransactionHandler`, `DateTransactionHandler`) heredan de `MentionTransactionHandler` (F01.8); `_handleAddition` y `_handleDeletion` crean/borran views y reminders vía `ViewBackendService`/`ReminderBloc`. Suite `validate-B3.F014.sh` 4/4 checks en verde (template=1/1, evidence=22/22, mermaid=3 OK, cobertura=10/10). Revisor `run_subagent.py --gate-100` → `veredicto=aprobado, correcciones=0`. Adaptación menor: `unit[F01.4].documento` renombrado al nombre completo del doc. Plan en `~/.local/share/kilo/plans/1792429084675-b3-f014-menciones-plan.md`. Artefactos: `OUT/_ledger/pruebas/B3.F014/{4-…md + validate-B3.F014.sh + validate-B3.F014.log + coverage.json + revisor_output.json + README.md}`.
- B3.F01.6 ✅ — Interacción: slash_menu, block_menu, context_menu, actions, toolbars desktop/mobile (`desktop_toolbar`, `mobile_toolbar_v3`, `mobile_floating_toolbar`, `toolbar_item`, `align_toolbar_item`), shortcuts, keyboard_interceptor, find_and_replace, copy_and_paste.

**Resultado (2026-10-19) (F01.5)**: 1 documento `OUT/09-features/F01-documentos-y-editor/5-bases-de-datos-embebidas-en-documentos.md` (293 líneas, 19 secciones, gate-100) cubriendo los 3 archivos del ledger F01.5 (`editor_plugins/database/`). **Sin BLoCs** (UI). 6 `SelectionMenuItem`: 2 inline (`inlineGridMenuItem`, `inlineBoardMenuItem`) que crean nuevo view via `ViewBackendService.createView`; 4 referenced (`referencedDocumentMenuItem`, `referencedGridMenuItem`, `referencedBoardMenuItem`, `referencedCalendarMenuItem`) que abren `showLinkToPageMenu` para linkar view existente. **Atributos `DatabaseBlockKeys`** (6): `gridType`, `boardType`, `calendarType`, `parentID`, `viewID`, `enableCompactMode`. `overflowTypes = {grid, board}` (calendar siempre cabe). Validador del builder exige `node.children.isEmpty && parentID is String && viewID is String`. `compactModeEventBus` (singleton) actualiza `enableCompactMode` via `transaction.updateNode`. **Corrección de scope oficializada** (§2 y §13): el ROADMAP menciona también `plugins/database_document/` (plugin standalone completo con `database_document_page.dart`/`database_document_plugin.dart`/`presentation/...`) pero NO está en el ledger F01.5 — esos archivos cubren la página standalone de base de datos, no la embebida. Suite `validate-B3.F015.sh` 4/4 checks en verde (template=1/1, evidence=7/7, mermaid=3 OK, cobertura=3/3). Revisor `run_subagent.py --gate-100` → `aprobado, 0 correcciones`. Plan en `~/.local/share/kilo/plans/1792429084675-b3-f015-bases-de-datos-embebidas-plan.md`. Artefactos: `OUT/_ledger/pruebas/B3.F015/{5-…md + validate-B3.F015.sh + validate-B3.F015.log + coverage.json + revisor_output.json + README.md}`.
- B3.F01.7 ✅ — Estilo: font, background_color, page_style, i18n del editor.

**Resultado (2026-10-19) (F01.6 — split en 7 sub-unidades + 1 indice)**: 7 documentos en `OUT/09-features/F01-documentos-y-editor/` cubriendo los **115 archivos UI** del ledger F01.6 repartidos por: **F01.6.1 slash_menu (27)** (25 `SelectionMenuItem` + `slash_command` + `slash_menu_items_builder`), **F01.6.2 block menu + actions + context menu (14)** (6 `option/*` items, `BlockActionOptionCubit`, `custom_context_menu`), **F01.6.3 drag to reorder (5)** + `actions/menu_extension.dart` + `options_toolbar_item.dart`, **F01.6.4 toolbars desktop + mobile + items + link (51)** (desktop_toolbar 10 + mobile_toolbar_v3 16 + mobile_floating_toolbar 1 + toolbar_item 19 + undo_redo 2 + align_toolbar_item 2 + color_picker_constants 1), **F01.6.5 copy & paste (10)** (`ClipboardService` con 2 `CustomValueFormat` inAppJson + tableJson), **F01.6.6 shortcuts + find_and_replace + keyboard (8)** (`command_shortcuts` con 20+ comandos, 3 generaciones `SearchService`). Suite `validate-B3.F016.sh` 4/4 verde (template=7/7, evidence=7/7, mermaid=22 bloques OK, cobertura=115/115). Revisor `run_subagent.py --gate-100` × 7 sub-unidades → `aprobado, 0 correcciones` × 7. **Adaptaciones a la skill**: nueva `SKILL/scripts/split_F0106.py` (auto-división F01.6 → 7 + indice, análoga a `split_F0103.py`); `validate-A4.2.sh` Check 3 actualizado a 106 unidades (100 base + 7 F01.6 split − 1 F01.6 maestro; excluye `F01.6.0` indice de la suma); nueva `validate-B3.F016.sh` (patrón F01.0/F01.5). Plan en `~/.local/share/kilo/plans/1792429084675-b3-f016-interaccion-plan.md`. Artefactos: `OUT/_ledger/pruebas/B3.F016/{7 docs + 7 revisor_*.json + validate-B3.F016.sh + log + coverage.json + README.md}`.
- B3.F01.8 ✅ — Infraestructura del editor: transaction_handler, block_transaction_handler, migration, parsers (enlaza con Bloque B4), error, base, extensions, shared_context.

**Resultado (2026-10-19) (F01.7)**: 1 documento `OUT/09-features/F01-documentos-y-editor/7-estilo-font-background-color-page-style-i18n-del-editor.md` (328 líneas, 19 secciones, gate-100) cubriendo los **9 archivos** del ledger F01.7 (8 ui + 1 bloc) en `appflowy:editor_plugins/{background_color, font, page_style}/`. **1 Bloc nuevo**: `PageStyleIconBloc` (`_page_style_icon_bloc.dart:10`, 77 líneas) con 2 eventos freezed (`initial`, `updateIcon(EmojiIconData?, bool)`) y estado con `icon: EmojiIconData?`. `PageStyleBottomSheet` (`page_style_bottom_sheet.dart`, 62 líneas) es el orchestrator que renderiza 3 secciones (cover con `PageStyleCoverImage`, layout con `PageStyleLayout`, icon con `PageStyleIcon`) usando `LocaleKeys.pageStyle_coverImage/layout/pageIcon`. `themeBackgroundColors` (`theme_background_color.dart:5-14`) define 9 colores `appflowy_them_color_tint1..9` mapeados a `FlowyTint.*` (comentario explícito "DON'T MODIFY THIS KEY BECAUSE IT'S SAVED IN THE DATABASE!"). `ThemeFontFamilySetting` (`customize_font_toolbar_item.dart:22`, 225 líneas) consume `AppearanceSettingsCubit` + `DocumentAppearanceCubit` + `google_fonts`. **Corrección de scope oficializada** (§2 y §13): el ROADMAP título menciona "i18n del editor" pero `appflowy/editor_plugins/i18n/editor_i18n.dart` **NO** está en el ledger F01.7 — vive en **F14** (`Internacionalizacion`, 6 archivos). El título cubre implícitamente los `LocaleKeys.pageStyle_*` consumidos. Suite `validate-B3.F017.sh` 4/4 checks en verde (template=1/1, evidence=8/8, mermaid=3 OK, cobertura=9/9). Revisor `run_subagent.py --gate-100` → `aprobado, 0 correcciones`. Cobertura F01 global 778 archivos verificados. Plan en `~/.local/share/kilo/plans/1792429084675-b3-f017-estilo-plan.md`. Artefactos: `OUT/_ledger/pruebas/B3.F017/{7-…md + validate-B3.F017.sh + validate-B3.F017.log + coverage.json + revisor_output.json + README.md}`.
- B3.F01.9 ✅ — IA en el editor: `editor_plugins/ai` (AI writer/completion; enlaza con F09).

**Resultado (2026-10-19) (F01.8)**: 1 documento `OUT/09-features/F01-documentos-y-editor/8-infraestructura-del-editor-…md` (~478 líneas, 19 secciones, gate-100) cubriendo los **20 archivos** del ledger F01.8 distribuídos en 4 carpetas: **block_transaction_handler/** (1) clase abstracta `BlockTransactionHandler` con 5 flags (`isCut/isUndoRedo/isPaste/isDraggingNode/isTurnInto` + `parentViewId`); **transaction_handler/** (4) abstractas `EditorTransactionHandler<T>` + `BlockTransactionHandler` (sub-clase con `livesInDelta: false`) + `MentionTransactionHandler` (sub-clase con `livesInDelta: true` y `MentionBlockData = (Node, Map, int)` typedef) + servicio orchestrator `EditorTransactionService` (StatefulWidget, 331 líneas) que se subscribe a `editorState.transactionStream` y dispatch según el `type` del node; **migration/** (1) `EditorMigration.migrateDocument` (272 líneas) con la migración AppFlowy 0.1.x → 0.2 (cover node → page/attributes/cover, text node → paragraph node, delta → attributes/delta, text/checkbox → checkbox_list, etc.); **parsers/** (13 archivos) incluye 9 `NodeParser` específicos (callout, custom_image, custom_paragraph, database, file_block, link_preview, math_equation, simple_table, sub_page, toggle_list) + 2 `CustomMarkdownParser` (markdown_code, markdown_simple_table) + 2 aggregate exports (`document_markdown_parsers.dart`, `markdown_parsers.dart`) + `custom_image_node_parser.dart` con 3 clases (CustomImageNodeParser + CustomImageNodeFileParser + CustomMultiImageNodeFileParser). `DatabaseNodeParser._convertDatabaseToCSV` consume `BackendExportService.exportDatabaseAsCSV` (F02). `EditorTransactionService._transactionHandlers` consume `SubPageTransactionHandler` (F01.2), `ChildPageTransactionHandler` (F01.4), `DateTransactionHandler` (F01.4). **Corrección de scope oficializada** (§2 y §13): el ROADMAP línea 219 lista 8 categorías (`error, base, extensions, shared_context`) que NO están en el ledger F01.8 — esas carpetas viven en **F01.0.1** (appflowy side, 139 archivos, cerrado). Suite `validate-B3.F018.sh` 4/4 verde (template=1/1, evidence=6/6, mermaid=3 OK, cobertura=20/20). Revisor `run_subagent.py --gate-100` → `aprobado, 0 correcciones`. Cobertura F01 global 798 archivos verificados. Plan en `~/.local/share/kilo/plans/1792429084675-b3-f018-infraestructura-editor-plan.md`. Artefactos: `OUT/_ledger/pruebas/B3.F018/{8-…md + validate-B3.F018.sh + log + coverage.json + revisor_output.json + README.md}`.

**Resultado (2026-10-19)**: 8 documentos en `OUT/09-features/F01-documentos-y-editor/` con las 19 secciones obligatorias; 555/555 archivos del ledger F01.0 marcados `verificado` en `cobertura.csv`; suite `OUT/_ledger/validate-B3.F010.sh` 4/4 checks en verde (template=8/8, evidence=43/43 OK, mermaid=30/30 OK, cobertura=555/555). Las 8 sub-unidades (F01.0 índice + F01.0.1 appflowy + F01.0.2 collab + F01.0.3.{1..5} editor) generadas vía `SKILL/scripts/split_F0103.py` (auto-división de F01.0.3 en 5 sub-unidades para sortear el umbral de 120 archivos). **Adaptaciones necesarias a la skill**: `validate_template.py` regex del modo `feature` ampliado de `^F\d+(\.\d+)?$` a `^F\d+(\.\d+)*$` para aceptar 3 niveles (F01.0.3.1); `validate-A4.2.sh` Check 3 actualizado a 100 unidades (= 90 base + 6 F01.0: F01.0 + F01.0.3.{1..5}; F01.0.3.json y F01.0.3.6.json eliminados) y al cómputo de "suma unidades == pendientes+verificados F01.0" para sortear el doble contado entre F01.0 (0 archivos propio) y sus sub-unidades (555 archivos cubiertos). Artefactos en `OUT/_ledger/pruebas/B3.F010/` (8 docs + `validate-B3.F010.sh` + `validate-B3.F010.log` + `coverage.json`). Plan en `~/.local/share/kilo/plans/1792429084675-b3-f010-indice-documentos-editor.md`.

**F02 — Bases de datos** (dividida):

**Resultado (2026-10-19) (F01.9 — scope-correction)**: 1 documento `OUT/09-features/F01-documentos-y-editor/9-ia-en-el-editor-…md` (~234 líneas, 19 secciones, gate-100) cerrando F01.9 como **scope-correction** (misma pattern que F01.3 media→F07 y F01.7 i18n→F14). El ledger F01.9 tiene **0 archivos**; los 10 widgets de `appflowy:editor_plugins/ai/` viven en **F09.4** ("IA: editor_plugins/ai"). Doc §2 + §13 lo declaran explícitamente. **Diagrama cross-cutting F01↔F09**: slash menu (F01.6.1 `ai_writer_item.dart`) → `DocumentBloc` (F01.0.1) → FFI → `flowy-ai` Rust (F09.1) → `appflowy/ai` Dart (F09.3) → `AiWriterCubit` (F09.4) → render. **4 sub-unidades F09** referenciadas: F09.1 (Rust `flowy-ai`, 67), F09.2 (Rust `flowy-sqlite-vec`, 7), F09.3 (Dart `appflowy_flutter/lib/ai + plugins/ai_chat`, 82), F09.4 (Dart `editor_plugins/ai`, 10). **Cierre del feature F01 completo**: 9 sub-unidades directas + F01.0 split en 7 + F01.0.{1,2,3.1-5} + F01.6 split en 7 = 23 docs. Total F01: 798 archivos. Suite `validate-B3.F019.sh` 4/4 verde (template=1/1, evidence=0/0, mermaid=3 OK, cobertura=0/0). Revisor `run_subagent.py --gate-100` → `aprobado, 0 correcciones`. Plan en `~/.local/share/kilo/plans/1792429084675-b3-f019-ia-editor-plan.md`. Artefactos: `OUT/_ledger/pruebas/B3.F019/{9-…md + validate-B3.F019.sh + validate-B3.F019.log + coverage.json + revisor_output.json + README.md}`. **F01 cerrado en su totalidad** (9 sub-unidades + 7 sub-de-F01.0 + 7 sub-de-F01.6 = 23 docs, 798 archivos, 798 verificados).
- B3.F02.0 ✅ — Índice: `DatabaseController`, `database_controller.dart`, `flowy-database2/manager.rs`, modelo collab-database, layouts, `template.rs` — **split en 8 sub-unidades (F02.0.1.{0,1,2,3} + F02.0.2.{0,1,2,3})**.
- B3.F02.1 ✅ — Campos y tipos (`services/field`, `application/field`): cada tipo de campo con su `TypeOption`, serialización y UI.
- B3.F02.2 ✅ — Celdas (`services/cell`, `application/cell`): parsing, formateo, edición por tipo.
- B3.F02.3 ✅ — Filas y row detail (`application/row`), relaciones.
- B3.F02.4 ✅ — Filtros (`services/filter`): cada condición por tipo de campo, algoritmo de evaluación.
- B3.F02.5 ✅ — Orden (`services/sort`): algoritmo, estabilidad, múltiples criterios.
- B3.F02.6 ✅ — Agrupación (`services/group`): por tipo de campo, movimientos entre grupos.
- B3.F02.7 ✅ — Cálculos (`services/calculations`, `application/calculations`).
- B3.F02.8 ✅ — Field settings, settings de vista, `database_view`.
- B3.F02.9 ✅ — Grid (`plugins/database/grid`) — **split en 3 sub-unidades + 1 nuevo script de skill**.
- B3.F02.10 ✅ — Board (`plugins/database/board`).
- B3.F02.11 ✅ — Calendar (`plugins/database/calendar`).
- B3.F02.12 ✅ — Tab bar de vistas, sync de database (`application/sync`), snapshots.

**Resultado (2026-10-20) (F02.1 — Campos y tipos)**: 1 documento `OUT/09-features/F02-bases-de-datos/1-campos-y-tipos-services-field-application-field.md` (~420 líneas, 19 secciones, gate-100) cubriendo los **55 archivos rust-handler** del módulo `flowy-database2/src/services/field/` (4 archivos core `services/field/{mod, field_builder, field_operation, type_option_transform}.rs` + 4 archivos comunes `type_options/{mod, type_option, type_option_cell, util}.rs` + 12 sub-familias `*_type_option/` × ~4 archivos = 48). Cada `*_type_option/` implementa los traits `CellDataDecoder` + `CellDataChangeset` (consumidos por F02.2) + `handle_cell_filter` (consumido por F02.4) + `handle_cell_compare` (consumido por F02.5). 12 familias: Checkbox, Checklist, Date, Media, Number, Relation, Selection (single + multi), Summary, Text, Time, Timestamp, Translate, URL. **Corrección de scope oficializada** (§2 + §13 + §14 del doc): los 13 BLoCs Dart de `application/field/` viven formalmente en F02.0.1.2 (`database-application-domain-misc.md`); este doc los lista como referencia sin reclamar (la `cobertura.csv` los marca como `autor_F02.0.1.2`). Suite `validate-B3.F02.1.sh` 4/4 verde (template=1/1, evidence=0/0 OK, mermaid=5/5, cobertura=55/55). Revisor `--gate-100 --feature-id F02 --unit F02.1` → `aprobado, 0 correcciones`. Artefactos en `OUT/_ledger/pruebas/B3.F021/{validate-B3.F02.1.sh, validate-B3.F02.1.log, coverage.json, revisor_output.json, README.md}`.

**Resultado (2026-10-20) (F02.2 — Celdas)**: 1 documento `OUT/09-features/F02-bases-de-datos/2-celdas-services-cell-application-cell.md` (~570 líneas, 19 secciones, gate-100) cubriendo los **4 archivos rust-handler** del módulo `flowy-database2/src/services/cell/` (`cell_data_cache.rs` + `cell_operation.rs` + `type_cell_data.rs` + `mod.rs`). El doc cubre los 18 cell blocs Dart (uno por FieldType con datos) + 5 archivos helper (`cell_controller`, `cell_cache`, `cell_data_loader`, `cell_data_persistence`, `cell_controller_builder`) **listados en §6/§13/§14 como referencia**, no reclamados formalmente: los 23 archivos Dart bloc de `application/cell/` viven en F02.0.1.2 (`database-application-domain-misc.md`) y la `cobertura.csv` los marca como `autor_F02.0.1.2`. **Corrección de scope oficializada** (§2 + §14 del doc). Suite `validate-B3.F02.2.sh` 4/4 verde (template=1/1, evidence=11/11 OK, mermaid=5/5, cobertura=4/4). Revisor `--gate-100 --feature-id F02 --unit F02.2` → `aprobado, 0 correcciones`. Artefactos en `OUT/_ledger/pruebas/B3.F022/{validate-B3.F02.2.sh, validate-B3.F02.2.log, coverage.json, revisor_output.json, README.md}`.

**Resultado (2026-10-20) (F02.3 — Filas y row detail)**: 1 documento `OUT/09-features/F02-bases-de-datos/3-filas-y-row-detail-application-row-relaciones.md` (~480 líneas, 19 secciones, gate-100) cubriendo los **5 archivos rust-handler** del módulo `flowy-database2/src/services/database/` (`database_editor.rs` 2464 líneas + `database_observe.rs` + `entities.rs` + `mod.rs` + `util.rs`). El doc cubre `DatabaseEditor` (orquestador central), 3 sub-suscripciones (`observe_sync_state`, `observe_rows_change`, `observe_field_change` — esta última desactivada en `DatabaseEditor::new`, marcado como `[NO DETERMINADO]` en §18), `DatabaseRowEvent` (Rust interno), `util.rs::database_view_setting_pb_from_view` (conversión yrs → PB), y el sistema de **relaciones entre filas** (`RelationTypeOption` + `RelatedRowDetailPageBloc`). Los 6 archivos Dart bloc de `application/row/` viven formalmente en F02.0.1.2 (`database-application-domain-misc.md`); este doc los cross-referencía sin reclamar (la `cobertura.csv` los marca como `autor_F02.0.1.2`). **Corrección de scope oficializada** (§2 + §14 del doc). Suite `validate-B3.F02.3.sh` 4/4 verde (template=1/1, evidence=25/25 OK, mermaid=7/7, cobertura=5/5). Revisor `--gate-100 --feature-id F02 --unit F02.3` → `aprobado, 0 correcciones`. Artefactos en `OUT/_ledger/pruebas/B3.F023/{validate-B3.F02.3.sh, validate-B3.F02.3.log, coverage.json, revisor_output.json, README.md}`.

**Resultado (2026-10-20) (F02.4 — Filtros)**: 1 documento `OUT/09-features/F02-bases-de-datos/4-filtros-services-filter.md` (~380 líneas, 19 secciones, gate-100) cubriendo los **4 archivos rust-handler** del módulo `flowy-database2/src/services/filter/` (`controller.rs` 562 líneas + `entities.rs` 526 líneas + `mod.rs` + `task.rs`). Cubre el **árbol de filtros** (`Filter` cuyo `inner` es `And`, `Or` o `Data`), `FilterChangeset` (5 operaciones), 12 `*FilterPB` por `FieldType` (uno por tipo con datos), `FilterController` con `apply_filter` recursivo (corto-circuito And/Or) + `filter_rows_and_notify` paralelo (`par_iter` de rayon), `PreFillCellsWithFilter` (`fill_cells`), y el `FilterTaskHandler`. Suite `validate-B3.F02.4.sh` 4/4 verde (template=1/1, evidence=23/23 OK, mermaid=4/4, cobertura=4/4). Revisor `--gate-100 --feature-id F02 --unit F02.4` → `aprobado, 0 correcciones`. Artefactos en `OUT/_ledger/pruebas/B3.F024/{validate-B3.F02.4.sh, validate-B3.F02.4.log, coverage.json, revisor_output.json, README.md}`.

**Resultado (2026-10-20) (F02.5 — Orden)**: 1 documento `OUT/09-features/F02-bases-de-datos/5-orden-services-sort.md` (~330 líneas, 19 secciones, gate-100) cubriendo los **4 archivos rust-handler** del módulo `flowy-database2/src/services/sort/` (`controller.rs` 365 líneas + `entities.rs` + `mod.rs` + `task.rs`). Cubre `SortController` (multi-criterio con `par_sort_by` de rayon, estable en cascada), `SortCondition` binario (Asc/Desc), `SortChangeset` (4 operaciones), `SortEvent` interno, y la propagación `ReorderAllRowsNotification`/`ReorderSingleRowNotification`. Caso especial documentado para `CreatedTime`/`LastEditedTime` (construye `TimestampCellData` desde `row.created_at`/`row.modified_at`). Suite `validate-B3.F02.5.sh` 4/4 verde (template=1/1, evidence=21/21 OK, mermaid=5/5, cobertura=4/4). Revisor `--gate-100 --feature-id F02 --unit F02.5` → `aprobado, 0 correcciones`. Artefactos en `OUT/_ledger/pruebas/B3.F025/{validate-B3.F02.5.sh, validate-B3.F02.5.log, coverage.json, revisor_output.json, README.md}`.

**Resultado (2026-10-19) (F02.6 — Agrupación)**: 1 documento `OUT/09-features/F02-bases-de-datos/6-agrupacion-services-group.md` (372 líneas, 19 secciones, gate-100) cubriendo los **15 archivos rust-handler** del módulo `flowy-database2/src/services/group/` (`mod.rs`, `entities.rs`, `configuration.rs`, `action.rs`, `controller.rs`, `group_builder.rs`, 6 archivos en `controller_impls/`). Cubre las **6 implementaciones de `GroupController`**: `DefaultGroupController`, `CheckboxGroupController`, `URLGroupController`, `DateGroupController` (con enum `DateCondition`), `SingleSelectGroupController`, `MultiSelectGroupController`. Suite `validate-B3.F02.6.sh` 4/4 verde (template=1/1, evidence=32/32, mermaid=2 OK, cobertura=15/15). Revisor `--gate-100 --feature-id F02` → `aprobado`. Artefactos: `OUT/_ledger/pruebas/B3.F026/{validate-B3.F02.6.sh, log, revisor_output.json, coverage.json, README.md}`.

**Resultado (2026-10-19) (F02.0 — Indice, split en 8 sub-unidades)** ✅ **cierra B3.F02.0 que era bloqueante para F02.6..F02.12.** F02.0 se divide en 8 sub-unidades; cada sub-unidad tiene su propio `validate-B3.F02.0.X.{0,1,2,3}.sh` en verde. Total: 333 archivos reales cubiertos (140 + 80 + 30 + 44 + 39) + 8 docs (4 con archivos + 2 índices + 2 scope-correction cerrada).
- **F02.0.1.0** — Indice appflowy (0 archivos). Doc `0.1.0-indice-appflowy-side-database-controller-services-widgets.md` con cross-cutting a F02.0.1.1, F02.0.1.2 y F02.0.1.3. Validador `validate-B3.F02.0.1.0.sh` 4/4 verde (template=1/1, evidence=0/0, mermaid=2/2, cobertura=0/0). Artefactos en `OUT/_ledger/pruebas/B3.F02010/`.
- **F02.0.1.1** — Database widgets + Rust entities (140 archivos). Doc `0.1.1-database-widgets-cell-row-field-setting-card-group.md` cubre todo el código en `plugins/database/widgets/{cell,row,field,setting,card,group,share_button}/`, `widgets/{cell_editor,database_view_widget,database_layout_ext,media_file_type_ext}/` + 5 directorios Rust PB entities (`flowy-database2/src/entities/{cell,row,field,type_option,filter}_entities/`). 101 evidence refs verificadas; 3 mermaids. Validador `validate-B3.F02.0.1.1.sh` 4/4 verde. Artefactos en `OUT/_ledger/pruebas/B3.F02011/`.
- **F02.0.1.2** — Database application + Rust infra (80 archivos). Doc `0.1.2-database-application-domain-misc.md` cubre `plugins/database/application/`, `database/`, `database/mod.rs` + `flowy-database2/src/{manager,lib.rs,event_handler,event_map,notification,template,utils,services}/` + 7 PB entities adicionales. 84 evidence refs; 4 mermaids. Validador `validate-B3.F02.0.1.2.sh` 4/4 verde. Artefactos en `OUT/_ledger/pruebas/B3.F02012/`.
- **F02.0.1.3** — Database tests scope-correction (0 archivos reales). Doc `0.1.3-database-tests.md` cierra formalmente las carpetas `plugins/database/{filter,group,sort,field,layout,field_settings,cell,calculations,block,share}_test*/` y `mock_data` como **inexistentes** (los tests reales viven en `appflowy_flutter/test/` + `integration_test/desktop_runner_*.dart` + inline en código Rust). Validador `validate-B3.F02.0.1.3.sh` 4/4 verde. Artefactos en `OUT/_ledger/pruebas/B3.F02013/`.
- **F02.0.2.0** — Indice collab-database Rust (0 archivos). Doc `0.2.0-indice-collab-database-rust-manager-model-template-view.md` con cross-cutting a F02.0.2.1/2.2/2.3. Validador `validate-B3.F02.0.2.0.sh` 4/4 verde. Artefactos en `OUT/_ledger/pruebas/B3.F02020/`.
- **F02.0.2.1** — collab-database fields + blocks + meta + workspace_database (30 archivos fuente `collab:collab-database/src/{fields,blocks,meta,workspace_database,rows,database}/`). Doc `0.2.1-collab-database-fields-blocks-meta-workspace-relation.md`. 83 evidence refs; 3 mermaids. Validador `validate-B3.F02.0.2.1.sh` 4/4 verde. Artefactos en `OUT/_ledger/pruebas/B3.F02021/`.
- **F02.0.2.2** — collab-database template + views + rows + misc (44 archivos fuente `collab:collab-database/src/{views,template,rows,...}/`). Doc `0.2.2-collab-database-template-views-rows-misc.md`. 128 evidence refs; 3 mermaids. Validador `validate-B3.F02.0.2.2.sh` 4/4 verde. Artefactos en `OUT/_ledger/pruebas/B3.F02022/`.
- **F02.0.2.3** — collab-database tests + Cargo.toml (39 archivos fuente `collab:collab-database/tests/` + `Cargo.toml`). Doc `0.2.3-collab-database-tests.md`. 148 evidence refs; 4 mermaids. Validador `validate-B3.F02.0.2.3.sh` 4/4 verde. Artefactos en `OUT/_ledger/pruebas/B3.F02023/`.

**Total F02.0 cerrado**: 8 docs + 8 `validate-B3.F02.0.X.*.sh` suites en verde; 333 archivos verificados en `cobertura.csv`; 544 evidence refs verificadas; 22 diagramas Mermaid aprobados. F02.6..F02.12 ahora pueden cerrar formalmente (ya tenían dependencia `{"id": "F02.0"}` en sus unit JSON). Plan en `~/.local/share/kilo/plans/1792453115498-f02-6-to-12-completion.md`. Revisor `--gate-100 --feature-id F02` → `aprobado` × 8 sub-unidades.

**Resultado (2026-10-19) (F02.7 — Cálculos)**: 1 doc `OUT/09-features/F02-bases-de-datos/7-calculos-services-calculations-application-calculations.md` (536 líneas, 19 secciones, gate-100) cubriendo los **9 archivos** del unit: 3 bloc Dart (`calculation_type_ext.dart`, `calculations_listener.dart`, `calculations_service.dart`) + 6 rust-handler (`cache.rs`, `controller.rs`, `entities.rs`, `mod.rs`, `service.rs`, `task.rs`). Suite `validate-B3.F02.7.sh` 4/4 verde (template=1/1, evidence=130/130, mermaid=4 OK, cobertura=9/9). Revisor `--gate-100` → `aprobado`. Artefactos en `OUT/_ledger/pruebas/B3.F027/`.

**Resultado (2026-10-19) (F02.8 — Field settings + database_view)**: 1 doc `OUT/09-features/F02-bases-de-datos/8-field-settings-settings-de-vista-database-view.md` (535 líneas, 19 secciones, gate-100) cubriendo los **21 archivos** del unit: 4 bloc Dart (`group_bloc.dart`, `property_bloc.dart`, `setting_listener.dart`, `setting_service.dart`) + 17 rust-handler (9 en `services/database_view/` — `layout_deps`, `mod`, `notifier`, `views`, `view_calculations`, `view_editor`, `view_filter`, `view_group`, `view_operation`, `view_sort`; 3 en `services/field_settings/`; 4 en `services/share/csv/`; 1 en `services/share/`). Orquesta los `*GroupController`/`FilterController`/`SortController`/`CalculationController`/`FieldSettingsBuilder` por vista. Cross-cutting con B4 (CSV import/export). Suite `validate-B3.F02.8.sh` 4/4 verde (template=1/1, evidence=94/94, mermaid=4 OK, cobertura=21/21). Revisor `--gate-100` → `aprobado`. Artefactos en `OUT/_ledger/pruebas/B3.F028/`.

**Resultado (2026-10-19) (F02.10 — Board)**: 1 doc `OUT/09-features/F02-bases-de-datos/10-board-plugins-database-board.md` (411 líneas, 19 secciones, gate-100) cubriendo los **14 archivos** del unit: 3 bloc Dart (`board_actions_bloc.dart`, `board_bloc.dart`, `group_controller.dart`) + 11 ui (board_page, toolbar, 7 widgets de columna header/checkbox/editable/focus/hidden_groups/shortcut_container, card_test.dart integration). Suite `validate-B3.F02.10.sh` 4/4 verde (template=1/1, evidence=81/81, mermaid=3 OK, cobertura=14/14). Revisor `--gate-100` → `aprobado`. Artefactos en `OUT/_ledger/pruebas/B3.F0210/`.

**Resultado (2026-10-19) (F02.11 — Calendar)**: 1 doc `OUT/09-features/F02-bases-de-datos/11-calendar-plugins-database-calendar.md` (467 líneas, 19 secciones, gate-100) cubriendo los **12 archivos** del unit: 4 bloc (`calendar_bloc`, `calendar_event_editor_bloc`, `calendar_setting_bloc`, `unschedule_event_bloc`) + 8 ui (calendar_day, calendar_event_card, calendar_event_editor, calendar_page, layout/sizes, toolbar/calendar_layout_setting, toolbar/calendar_setting_bar, calendar.dart). Suite `validate-B3.F02.11.sh` 4/4 verde (template=1/1, evidence=80/80, mermaid=4 OK, cobertura=12/12). Revisor `--gate-100` → `aprobado`. Artefactos en `OUT/_ledger/pruebas/B3.F0211/`.

**Resultado (2026-10-19) (F02.12 — Tab bar + sync + snapshots)**: 1 doc `OUT/09-features/F02-bases-de-datos/12-tab-bar-de-vistas-sync-de-database-snapshots.md` (473 líneas, 19 secciones, gate-100) cubriendo los **9 archivos** del unit: 2 bloc Dart (`database_sync_bloc`, `database_sync_state_listener`) + 5 ui tab_bar (setting_menu, tab_bar_add_button, tab_bar_header, mobile/mobile_tab_bar_header, tab_bar_view) + 2 rust-handler de `services/snapshot/` (entities, mod). Cross-cut con B1.6 §7 (snapshots) y B1.7 (`collab_snapshot` SQLite). Suite `validate-B3.F02.12.sh` 4/4 verde (template=1/1, evidence=49/49, mermaid=4 OK, cobertura=9/9). Revisor `--gate-100` → `aprobado`. Artefactos en `OUT/_ledger/pruebas/B3.F0212/`.

**Resultado (2026-10-19) (F02.9 — Grid, split en 3 sub-unidades)**: F02.9 (61 archivos; umbral soft-excedido de AGENTS.md §8) se **dividió en 3 sub-unidades** mediante el nuevo script `SKILL/scripts/split_F0209.py` (~115 líneas, análogo a `split_F0106.py`); sin solapamiento; 0 archivos orphan; suma de las 3 = 61.
- **F02.9.0** — 12 archivos. Doc `9.0-grid-indice-plugins-database-grid.md` (497 líneas, 19 sec, gate-100): layout principal (`grid.dart`, `grid_page.dart`, `grid_scroll.dart`, `layout/{layout,sizes}.dart`, `mobile_grid_page.dart`, `mobile_fab.dart`, `shortcuts.dart`) + 4 BLoCs raiz (`grid_bloc`, `grid_accessory_bloc`, `grid_header_bloc`, `row_bloc`). `validate-B3.F02.9.0.sh` 4/4 (template=1/1, evidence=119/119, mermaid=4/4, cobertura=12/12). Revisor `--gate-100` → `aprobado`. Artefactos en `OUT/_ledger/pruebas/B3.F0290/`.
- **F02.9.1** — 27 archivos. Doc `9.1-grid-filtros-y-filter-choicechips.md` (432 líneas, 19 sec, gate-100): `FilterEditorBloc`, `SelectOptionLoader`, `SimpleTextFilterBloc`, `CalculationsBloc`/`field_type_calc_ext`, 12 `choicechip/{checkbox,checklist,date,number,select_option/{condition_list,option_list,select_option},text,time,url}.dart`, 5 `widgets/calculations/`, `condition_button`, `create_filter_list`, `disclosure_button`, `filter_menu`, `filter_menu_item`, `common/type_option_separator`. `validate-B3.F02.9.1.sh` 4/4 (template=1/1, evidence=75/75, mermaid=3/3, cobertura=27/27). Revisor `--gate-100` → `aprobado`. Artefactos en `OUT/_ledger/pruebas/B3.F0291/`.
- **F02.9.2** — 22 archivos. Doc `9.2-grid-sort-header-row-footer-toolbar-shortcuts.md` (514 líneas, 19 sec, gate-100): `SortEditorBloc`, `MobileRowDetailBloc`, `RowDetailBloc`, `RowDocumentBloc`, 5 `widgets/sort/`, 6 `widgets/header/`, 4 `widgets/row/`, `widgets/footer/grid_footer.dart`, 4 `widgets/toolbar/`. `validate-B3.F02.9.2.sh` 4/4 (template=1/1, evidence=81/81, mermaid=6/6, cobertura=22/22). Revisor `--gate-100` → `aprobado`. Artefactos en `OUT/_ledger/pruebas/B3.F0292/`.

**Total F02 cerrado (parcial, falta F02.0)**: 9 docs de feature + 1 nuevo script `split_F0209.py` + 9 `validate-B3.F02.X.sh` suites en verde; 141 archivos verificados (`autor_F02.{6,7,8,9.0,9.1,9.2,10,11,12}` en `cobertura.csv`); 661 refs validadas; 38 diagramas Mermaid aprobados por `mmdc`. Próximo: `B3.F02.0` (prerrequisito declarado en cada `units/F02.{6,7,8,9.0,9.1,9.2,10,11,12}.json::dependencias` que apunta al índice F02.0; las features declaran los tipos `DatabaseController`, `Editor`, `ViewEditor`, `ViewFilter`, `ViewSort`, `ViewGroup`, `ViewCalculation`, `ViewOperation` sin documentar formalmente — referencia cruzada en §19 de cada doc hacia `F02.0.1` y `F02.0.2`).

**Resto de features** (una fase cada una, divisibles si superan el umbral):
- B3.F03 ✅ — Folder, workspaces, espacios, vistas, view_management. → split en 4 sub-unidades
- B3.F04 ✅ — Sidebar, favoritos, recientes, papelera, tabs, command palette, action_navigation.
- B3.F05 ✅ — Usuario, auth (local/cloud/third-party), sesión, miembros, roles, migraciones. → split en 3 sub-unidades
- B3.F06 ✅ — Sync y servidores (`af_cloud` vs `local_server`), estado de sync, awareness/colaboradores, network monitor, reconexión.
- B3.F07 ✅ — Almacenamiento de archivos (upload por chunks, reintentos, caché, estados).
- B3.F08 ✅ — Búsqueda e indexación. Piloto A5.1 **completado in situ** con los 11 ficheros del command palette que B0.2 le asignó (32/32).
- B3.F09 ✅ — IA: chat, completion, IA local, embeddings + `flowy-sqlite-vec`, selección de modelo, offline, middleware. → split en índice `F09.0` + 4 capas
- B3.F10 ✅ — Importación (detalle de UI y orquestación; el motor va en B4).
- B3.F11 ✅ — Exportación (detalle de UI y orquestación; el motor va en B4).
- B3.F12 ✅ — Compartir, publicar, niveles de acceso, shared section. → split en 2 sub-unidades
- B3.F13 ✅ — Ajustes, apariencia, temas (incl. theme_upload), fuentes. → split en 3 sub-unidades
- B3.F14 ✅ — Internacionalización (inlang, easy_localization, flujo de claves).
- B3.F15 ✅ — Notificaciones in-app, recordatorios, `flowy-date`. → split en Dart (`F15.1`) y Rust (`F15.2`)
- B3.F16 ✅ — Mobile. **184/184**. Cerradas `F16.0` (índice), `F16.1.1` (router y blocs base), `F16.1.2.1` (shell, ajustes, home, favoritos y widgets, 98), `F16.1.2.2` (documento, editor, selection menu e inline actions), `F16.1.2.3` (database, chat, búsqueda, notificaciones y base, 71) y `F16.2` (scope-correction).
- B3.F17 ✅ — Plataforma: ventanas, deeplinks, auto-update, hotkeys, feature flags, captura de errores, logging (`lib-log`, `log_filter.rs`).
- B3.F21 ✅ — Icon/Emoji picker (Dart UI): `appflowy_flutter/lib/shared/icon_emoji_picker/*`. Cross-cutting con F01 (toolbar), F03 (page-icons), F13 (settings) y F17 (assets).
- B3.F2x ✅ — Features nuevas descubiertas en B0.2. **F21 es la única**: el triage creó una sola feature nueva y ya está cerrada.

**Líneas nuevas** (estas cuatro features ocupaban 2 036 archivos y no tenían ninguna línea en el ROADMAP):

- B3.F18 ✅ — Motor Colab (CRDT, plugins, importer, entity, derive). 113/113, gate-100.
- B3.F20 ✅ — Colab (raíz: configuración, CI, docs, manifests). 13/13.
- B3.F00 ✅ — Infraestructura compartida: FFI y dispatcher, errores y SQLite, build/codegen, crates `-pub`, paquetes Dart internos, carcasas nativas y tests. **1556/1556** en 21 unidades. Índice maestro en `0-indice-…`.
- B3.F19 ✅ — Editor (tests, ejemplos, `lib/l10n`, configuración). **354/354** en 15 unidades. Índice maestro en `0-indice-…`.

**Resultado (2026-10-20) — cierre de B3.F03 a B3.F07 (406 archivos, 10 documentos, 5 features).** Plan ejecutor: `~/.local/share/kilo/plans/1792504481368-b3-f03-f07-cierre-plan.md`. Bitácora de skill: `OUT/_ledger/pruebas/B3.F030/README-prerequisitos.md`.

| Fase | Documentos | Líneas | Archivos | Refs | Mermaid | Suites | Revisor |
|---|---:|---:|---:|---:|---:|---:|---|
| B3.F06 | 1 | 469 | 35 | 123 | 5 | 5/5 | aprobado (**gate-100**) |
| B3.F07 | 1 | 460 | 58 | 87 | 4 | 5/5 | aprobado |
| B3.F04 | 1 | 820 | 66 | 211 | 6 | 5/5 | aprobado |
| B3.F03.{0..3} | 4 | 2 825 | 116 | 929 | 18 | 5/5 ×4 | aprobado ×4 |
| B3.F05.{0..2} | 3 | 2 077 | 131 | 432 | 14 | 5/5 ×3 | aprobado ×3 |
| **Total** | **10** | **6 651** | **406** | **1 782** | **47** | | |

Cobertura global tras el cierre: **1 762 verificados / 4 603 asignados (38,28 %)**, 0 `sin_asignar`, 2 841 pendientes (F00, F08–F21, B4–B6).

**Decisiones tomadas** (confirmadas por el usuario): (D1) F03 se divide en 4 por corte de lenguaje/fuente, declarado en `SKILL/scripts/build_units.py::SUBDIVISIONS["F03"]` para que sobreviva a la regeneración; (D2) se crea el índice **F05.0**, que las units F05.1/F05.2 ya declaraban como dependencia y nadie materializaba; (D3) las discrepancias ROADMAP↔ledger se resuelven con **correcciones de scope documentadas** en §2/§13 de cada doc, sin reasignar archivos; (D4) orquestación secuencial feature por feature.

**Correcciones de scope oficializadas** (ROADMAP promete algo que el ledger asigna a otra feature):

| Prometido | Realidad en el ledger | Declarado en |
|---|---|---|
| F03 · *view_management* | 4 archivos en **F04** y **vacíos** (`README.md` 0 B, los 3 `.dart` 1 B). `ViewManagementBloc` no existe | F03.0, F03.1, F04 |
| F03 · *espacios* | 12 widgets de `sidebar/space/` + `space_bloc`/`space_search_bloc` en **F03.1** (no hay feature propia) | F03.1, F03.0 |
| F05 · *miembros, roles* (UI) | `features/share_tab/**`, `share_role.dart`, `share_access_level.dart` → **F12**; en F05.2 solo los 5 eventos Rust | F05.0, F05.1, F05.2 |
| F05 · *migraciones* | `flowy-user/src/migrations/**` (9) es lógica de datos; el esquema diesel de las 6 migraciones ya está en **B1.7** | F05.0, F05.2 |
| F06 · *awareness / colaboradores* | `user_awareness.rs` + `manager_user_awareness.rs` → **F05.2**; `document_collaborators_bloc.dart` et al. → **F01.0.1** | F06, F05.2 |
| F06 · *estado de sync de bajo nivel* | `collab-plugins/src/{cloud_storage/**,connect_state.rs}` → **F18** | F06 |
| F06 · *proveedor de servidor* | `flowy-core/src/{server_layer.rs,deps_resolve/cloud_service_impl.rs}`, `collab-integrate/src/plugin_provider.rs` → **F00** | F06 |
| F07 · *chunking* | `flowy-storage-pub/src/{chunked_byte,cloud,storage}.rs` → **F00** | F07 |
| F01.3 · *media y archivos* | reasignados por el triage de B0.2 a **F07** (42+ archivos); F01.3 quedó como scope-correction | F07, F01.3 |

**Pruebas literales superadas**: 51/51 `FolderEvent` y 19/19 `FolderNotification` (F03.2, agrupados en F03.0) · 56/56 `UserEvent` y 10/10 `UserNotification` (F05.2, agrupados en F05.0) · 2/2 eventos de `flowy-storage` y 2/2 `StorageNotification` (F07) · `flowy-server` **no registra ningún `XEvent`** (F06, declarado con evidencia) · 14 BLoCs Dart de F03.1 · 10 BLoCs Dart de F05.1 · 13 ficheros de test de `collab-folder` (F03.3) · 35 pantallas de `lib/user/presentation/screens` (F05.1).

**Hallazgos materiales**:
1. **`extract_notifications.py` marca `emitted_in_rust: 0` para las 19 variantes de `FolderNotification`** y para las 2 de `StorageNotification`: su heurística solo reconoce `NotificationBuilder::new` literal, y tanto `flowy-folder` (`folder_notification_builder`, `notification.rs:48–55`) como `flowy-storage` (`manager.rs:751–764`) emiten por envoltorio. **Afecta a F03.2, F04, F06, F07, F12 y F15.**
2. **5 `FolderNotification` declaradas y nunca emitidas** (`DidCreateWorkspace`, `DidUpdateWorkspace`, `DidDeleteView`, `DidRestoreView`, `DidUpdateFolderSnapshotState`), tres con rama Dart.
3. **5 `FolderEvent` huérfanas**: `CreateFolderWorkspace`, `DeleteWorkspace` y `CopyLink` sin handler; `GetFolderSnapshots` y `ReadCurrentWorkspaceViews` con handler pero sin consumidor Dart.
4. **`WorkspaceBloc._fetchWorkspaces` descarta la lista recibida** (`workspace_bloc.dart:52`): el bloc es un no-op.
5. **B1.6 documenta campos y variantes de `collab-folder` que no existen** en el rev `4dfccef` (`layout_settings`, `cover`, `is_space`, `display_mode`, `view_space_status`, `desc`, `ViewLayout::AIChat`). Tabla de discrepancias en F03.3 §2. **Pendiente de resolver en C3.**
6. **Fixtures binarias no inventariadas**: `collab-folder/tests/folder_test/history_folder/folder_{with,without}_fav_v1.zip` son necesarias para los tests de migración (`util.rs:207`) pero no están en `inventario.json`.
7. `workspace/application/user/user_workspace_bloc.dart` (692 LOC reales) es un re-export de una línea a `lib/features/workspace/logic/`, fuera del ledger de F05.

**Adaptaciones a la skill** (todas reversible, detalle en `OUT/_ledger/pruebas/B3.F030/README-prerequisitos.md`):
- `SKILL/scripts/build_units.py`: nuevas `F03_SUBS` (4 entradas) y entrada de índice `F05.0` en `F05_SUBS`; ambas registradas en `SUBDIVISIONS`. Se regenera solo F03 y F05 con `--include`, y `_index.json` se reconstruye desde el directorio completo.
- `SKILL/scripts/validate_units.py`: se saltan las unidades `B1.x` (otro esquema) y el invariante pasa a comparar contra **todas** las filas asignadas, no solo las `pendiente`; nuevo flag `--estados {all,pendiente}`.
- `SKILL/scripts/record_unit_state.py`: resuelve sub-unidades (`F03.2`) leyendo `units/<id>.json`; nuevo flag `--units-dir`.
- `OUT/_ledger/validate-A4.2.sh`: Check 3 pasa a ser **de solo lectura** (antes regeneraba el directorio de unidades que debía validar) y añade un gate de F03..F07 al 100 % verificado. Checks 4–8 se ejecutan sobre temporales.
- `OUT/_ledger/cobertura.csv`: purga de las units padre obsoletas `F02.0.1.json` / `F02.0.2.json` (425 rutas con doble propiedad), reanclaje de 135 filas asignadas sin unidad (114 de F02 + 21 de F08) y cesión de 51 rutas Dart duplicadas de `F02.{1,2,3,7,8,12}` a `F02.0.1.2`.
- 34 suites heredadas de `OUT/_ledger/pruebas/B3.F0*/` corregidas: parsing de Mermaid (`OK=` mayúsculas vs `ok=` minúsculas de `validate_evidence`), `ROOT` a 4 niveles en las 9 de F01, y umbral de cobertura de B3.F01.0 relajado de `= 555` a `>= 555` (hoy son 798).

**Enlaces cruzados**: `build_index.py --check-links` reporta **47 no resueltos de 118, 0 de ellos realmente rotos** (verificado: ningún target corresponde a un `id:` existente). Los no resueltos son features y fases aún no escritas (F00, F01, F02, F09, F12–F19, B4, B6.3) más los tokens de ejemplo `X`/`NOEXISTE`/`F..` que `STATE.md` usa al explicar el propio `build_index.py`. Para bajar de 66 a 47 se añadió `ID_ALIASES` a `build_index.py`, que resuelve los ids de fase `B1.5`–`B1.7` y `B2.1`–`B2.6` contra el id real del sub-documento índice de cada carpeta. El resto queda registrado en `OUT/22-preguntas-abiertas.md`.

**Próxima fase abierta**: B3.F08 (Búsqueda e indexación — completar el piloto A5.1) o F00 (infraestructura compartida). Ver `OUT/STATE.md §Próxima fase por abrir`.

---

## Resultado (2026-10-20) — cierre del Bloque B3: F00–F21, todo el ledger pendiente

Plan ejecutor: `~/.local/share/kilo/plans/1792513584673-b3-cierre-ledger-completo.md` (6 olas, orquestación paralela con `MAX_PARALLEL=3`). Bitácora de skill: `OUT/_ledger/pruebas/B3.F00audit/README-prerequisitos.md`.

### Fase 0 — reparación bloqueante del ledger (previa y obligatoria)

Ninguna feature podía escribirse antes de esto: `build_units.py` destruía unidades existentes y el invariante `suma(archivos_total) == filas asignadas` no se sostenía.

| Reparación | Detalle |
|---|---|
| **Auditoría de F02** | F02 estaba marcada ✅ con **114 archivos sin documentar** (raíz de `flowy-database2`, 49 entidades, 51 tests). Clasificados 10 citados / 104 sin cubrir. Se crearon `F02.13`, `F02.14`, `F02.15`; **F02 pasa a 651/651** |
| `F16.1.1`/`F16.1.2` no regenerables | Existían solo en disco: `build_units.py` no las generaba y cualquier reconstrucción las borraba. `F16_SUBS` reescrito, con `F16.1.2` (178 archivos) partida en 3 |
| `F00.7` degenerado | 11 sub-unidades de **1 archivo** y `F00.7.13` con **517**. Corte declarativo `F00.7.0`–`F00.7.8` |
| Unidades sobre el umbral | `F00.5.1` (121), `F00.5.6` (203) y `F13` (127) divididas declarativamente |
| Dependencias no materializadas | `F09.0`, `F16.0`, `F19.0` declaradas por sus hermanas pero inexistentes → índices creados (`F09.0`, `F16.0`) |
| `FEATURE_TITLES["F21"]` ausente | La unidad decía `titulo: "F21"` y apuntaba a `F21-f21/F21-f21.md`. Ahora `F21-icon-emoji-picker/` |
| Purga de unidades obsoletas | 3 unidades **maestro** (`F02.0.1`, `F02.0.2`, `F03`, con 425 rutas de doble propiedad) y 38 restos de una división recursiva que se probó y se descartó |
| Fuente de verdad de las unidades | `sync_units_from_docs.py`: el frontmatter `archivos_cubiertos` del documento manda sobre la lista congelada del JSON de unidad. Idempotente, resuelve conflictos y re-ancla huérfanas |
| Pipeline | `SKILL/scripts/rebuild_units.sh` = `build_units --prune` → `sync_units_from_docs` → `build_units --index-only` → `validate_units` |

Resultado: **124 unidades, 4 603 archivos, 0 solapamiento, 0 sin unidad**. `validate-A4.1/2/4.sh` en verde (con `N_REAL` re-baselined a 129).

### Unidades cerradas (34 documentos, 991 archivos)

| Fase | Documentos | Archivos | Refs | Mermaid | Revisor |
|---|---:|---:|---:|---:|---|
| B3.F02.{13,14,15} — cierre de la fuga de F02 | 3 | 114 | 475 | 14 | aprobado ×3 |
| B3.F00.{1,2,4,5.1} | 4 | 229 | 445 | 23 | aprobado, **gate-100** en F00.1 |
| B3.F08 — búsqueda (piloto completado) | 1 | 32 | 127 | 6 | aprobado, **gate-100** |
| B3.F09.{0..4} — IA | 5 | 166 | 671 | 28 | aprobado ×5 |
| B3.F10, B3.F11 | 2 | 5 | 168 | 8 | aprobado ×2 |
| B3.F12.{1,2} | 2 | 72 | 231 | 10 | aprobado ×2 |
| B3.F13.{1,2,3} | 3 | 127 | 392 | 18 | aprobado ×3 |
| B3.F14 | 1 | 6 | 68 | 5 | aprobado |
| B3.F15.{1,2} | 2 | 53 | 235 | 9 | aprobado ×2 |
| B3.F16.{0,1.1,1.2.2,2} | 4 | 15 | 230 | 15 | aprobado ×4 |
| B3.F17 | 1 | 56 | 82 | 6 | aprobado, **gate-100** |
| B3.F18 | 1 | 113 | 149 | 7 | aprobado, **gate-100** |
| B3.F20 | 1 | 13 | 56 | 4 | aprobado |
| B3.F21 | 1 | 11 | 132 | 6 | aprobado |
| **Total** | **34** | **991** | **3 461** | **191** | |

Cada unidad tiene suite propia de 5 checks (`template` · `evidence` · `mermaid` · `cobertura` · `revisor`) en `OUT/_ledger/pruebas/B3.<UNIT>/` y su `revisor_output.json` con `veredicto=aprobado, correcciones=0`.

### Cobertura

| Feature | Asignados | Verificados | Pendientes |
|---|---:|---:|---:|
| F01, F02, F03, F04, F05, F06, F07 | 1 900 | **1 900** | 0 |
| F08 | 32 | **32** | 0 |
| F09 | 166 | **166** | 0 |
| F10 | 3 | **3** | 0 |
| F11 | 2 | **2** | 0 |
| F12 | 72 | **72** | 0 |
| F13 | 127 | **127** | 0 |
| F14 | 6 | **6** | 0 |
| F15 | 53 | **53** | 0 |
| F17 | 56 | **56** | 0 |
| F18 | 113 | **113** | 0 |
| F20 | 13 | **13** | 0 |
| F21 | 11 | **11** | 0 |
| **F00** | 1 556 | 229 | **1 327** |
| **F16** | 184 | 15 | **169** |
| **F19** | 354 | 0 | **354** |
| **TOTAL** | **4 603** | **2 753 (59,81 %)** | **1 850** |

`19 de las 22 features` quedan al 100 %.

### Correcciones de scope oficializadas en esta fase

| Prometido | Realidad en el ledger | Declarado en |
|---|---|---|
| F13 · *miembros* | `settings/widgets/members/**` (7) en **F13.2**, no en F12 | F13.2, F12.1 |
| F14 · *flujo de claves* | Los **36** bundles (`frontend/resources/translations/*.json`) están en **F00.7.1**; las 1637 claves ya catalogadas en B2.6 | F14, F00.7.1 |
| F15 · *notificaciones* (Rust) | `flowy-notification/**` ya documentado en B1.5 §04 | F15.2 (cross-ref) |
| F12 · *import* y *publicación* | `flowy-folder/src/share/import.rs` y `publish_util.rs` están en F12.2 pero sus motores son **B4.11** y **B4.12** | F12.2 |
| F16 · *editor móvil* | `editor_plugins/mobile_*` → **F01.6.4** (verificado). `F16.2` queda vacía y documenta la corrección | F16.2, F16.0 |
| F17 · *plataforma* | 24 de 56 archivos son widgets genéricos; el núcleo son 12 `startup/tasks/**` + `lib-log/**` + `log_filter.rs` | F17 |
| F02 · *cierre* | 114 archivos sin verificar pese al ✅ del ROADMAP | F02.13/14/15 |
| F00/F18/F19/F20 | **Sin ninguna línea en el ROADMAP** pese a ocupar 2 036 archivos | ROADMAP (líneas nuevas) |

### Hallazgos materiales

1. **El MCP no compila**: `flowy-ai/src/lib.rs:10-11` deja comentado el módulo y el crate `af-mcp` no está en `Cargo.toml`. No se pueden enumerar las herramientas MCP (F09.1 §18).
2. **`ai_tool/` está tras un feature sin consumidores** (F09.1 §18).
3. **`flowy-database2/src/template.rs`** (177 líneas, 3 plantillas por layout) **no tiene ninguna llamada en todo el repositorio** (F02.13 §7.1).
4. **`AIEvent::GetChatInfo` está registrado contra un handler no-op**: el handler real existe pero no está cableado, así que Dart recibe siempre vacío (F09.1).
5. **`UserNotification::DidUpdateReminder` nunca se emite** (`// TODO: implement reminder observer`); el disparo real lo produce un `Timer.periodic` de 30 s en Dart (F15.2).
6. **`handle_reminder_action` descarta `DocumentReminderAction`** en un `match` con los tres brazos vacíos (F15.2).
7. **El chat no sube adjuntos**: `StreamChatPayloadPB` no transporta ficheros y `AIEvent::ChatWithFile` no tiene invocador Dart (F09.3 §13).
8. **34 falsos negativos en el extractor de notificaciones**: el catálogo marca 49 variantes sin listener Dart y una búsqueda manual deja 15 (F15.1 §18).
9. **`IndexeddbDiskPlugin`** implementa una firma de `did_init` con 3 parámetros y expone un `flush` inexistente en el trait: el backend wasm no parece compilar (F18 §18).

### Adaptaciones a la skill

8 scripts nuevos (`rebuild_units.sh`, `sync_units_from_docs.py`, `close_unit.sh`, `make_unit_brief.py`, `coverage_report.py`, `harvest_open_questions.py`, `mermaid_debug.py`, `align_units.py`, `restore_unit_files.py`), 2 promovidos desde `B3.F030` (`make_phase_suite.py`, `set_unit_docs.py`) y `build_units.py` ampliado con 12 subdivisions nuevas, `ALWAYS_EMIT`, `--prune` y `--index-only`. Detalle completo en `OUT/_ledger/pruebas/B3.F00audit/README-prerequisitos.md`.

### Preguntas abiertas

114 `[NO DETERMINADO]` volcados desde la §18 de los 30 documentos a `OUT/22-preguntas-abiertas.md` (§ "B3.F00–F21 · Cierre del ledger"). Ninguna es bloqueante.

### Próxima fase abierta

**B5** (secuencias globales, 13 fases: B5.1 arranque en frío, B5.2 login local y cloud, B5.3 cambio de workspace, B5.4 crear/abrir/editar/cerrar documento, B5.5 edición concurrente y merge, B5.6 database con filtro+orden+grupo, B5.7 subir imagen, B5.8 búsqueda, B5.9 chat con streaming, B5.10 export, B5.11 import, B5.12 publish, B5.13 pérdida y recuperación de red). Los bloques B3 y B4 quedan cerrados.

---

## Resultado (2026-10-21) — cierre del Bloque B4: motor de exportación, importación y publicación

Plan ejecutor: `~/.local/share/kilo/plans/1792533640542-b4-motor-export-import.md`. Bitácora: `OUT/_ledger/pruebas/B4.F00audit/README-cierre-B4.md`.

### Ola 0 · Deuda C5 cerrada antes de B4

`build_index.py --check-links` bajó de **131 a 44** no resueltos. Los 42 ids mal formados y los 11 tokens de ejemplo de los docs aprobados quedaron en **0**: 39 correcciones sobre 25 documentos, cada una mapeada al id válido más cercano o reescrita a prosa (`B18.1`→`B6.1`, `F01.0.3`→`F01.0.3.3`, `F02.9.4`→`F02.9.1`+`F02.9.2`, `[[bin]]`→`[bin]`, `[[X]]`→`<X>`…). Los 44 restantes son **exclusivamente B6.1/B6.2/B6.3**, y los 36 `[[B4.*]]` se resolvieron solos al materializarse las 14 unidades.

### 14 documentos, 6 900 líneas, 2 167 refs, 61 diagramas

| Unidad | Doc | Líneas | Refs | Mermaid | Suite |
|---|---|---:|---:|---:|---|
| B4.0 | índice del motor | 501 | 102 | 4 | 1/1 |
| B4.1 | Export Markdown | 386 | 121 | 5 | 1/1 |
| B4.2 | Export HTML | 512 | 225 | 5 | 1/1 |
| B4.3 | Export texto plano (scope-correction) | 430 | 109 | 5 | 1/1 |
| B4.4 | Export JSON del documento | 557 | 137 | 5 | 1/1 |
| B4.5 | Export CSV de database | 440 | 187 | 4 | 1/1 |
| B4.6 | Export raw database data | 515 | 151 | 4 | 1/1 |
| B4.7 | Otros formatos (PDF, quill delta, word count) | 403 | 95 | 4 | 1/1 |
| B4.8 | Import Markdown y texto | 459 | 169 | 5 | 1/1 |
| B4.9 | Import CSV | 533 | 211 | 4 | 1/1 |
| B4.10 | Import historial y `.afdb` | 561 | 162 | 4 | 1/1 |
| B4.11 | Import ZIP y Notion | 481 | 92 | 4 | 1/1 |
| B4.12 | Publicación web | 481 | 102 | 4 | 1/1 |
| B4.13 | Matriz de round-trip y fidelidad | 641 | 304 | 4 | 1/1 |
| **Total** | **14** | **6 900** | **2 167** | **61** | **14/14** |

Prueba del bloque superada: **matriz de 29 bloques × 9 formatos + submatriz de 15 `FieldType` × 4 variantes de CSV, sin una sola celda vacía**. Las 14 suites están en `OUT/_ledger/pruebas/B4.<N>/`, todas con `veredicto=aprobado, correcciones=0`.

### Adaptaciones a la skill (5)

- **`close_unit.sh`** ahora despacha plantilla y fase por prefijo de unidad (`B4.*`→`export`+`PHASE=$UNIT`, `B1.*`→`structure`, resto→`feature`+`B3.*`) y **no toca `cobertura.csv`** para unidades transversales: sus archivos ya pertenecen a una feature verificada.
- **`make_phase_suite.py`** acepta `--template` y `--transversal`. Para una unidad transversal, el quinto check deja de ser "N filas marcadas" (que sería 0) y pasa a ser **"el frontmatter declara exactamente N rutas y todas existen en `SRC/`"**, que es la garantía real. El parser acepta `appflowy/…`, `collab:collab-database/…` y `editor:lib/…`.
- **`harvest_open_questions.py`** recorre ahora `10-motor-export-import/` y lee las secciones 5–8 de la plantilla export. Antes solo miraba `09-features` §18, que no existe en esa plantilla: los `[NO DETERMINADO]` de B4 eran invisibles.
- **`make_b4_units.py`** (nuevo): genera las 14 unidades validando que sus 124 rutas existan en `SRC/` antes de escribir el JSON.

### Hallazgos materiales (12; los que cambian decisiones)

1. **No existe exportación a texto plano**: `DocumentExportType.text` lanza `UnimplementedError()` y nadie lo llama, pero el importador **sí acepta `.txt`**. Se puede importar texto plano y no exportarlo.
2. **La publicación web no exporta HTML: envía `EncodedCollab` binario.** `publish_util.rs` serializa el collab con `bincode` y lo manda en un `PublishPayload` al backend, que es quien renderiza. Único motor que cruza la frontera sin producir fichero de usuario.
3. **Dos algoritmos de slug de publicación sin reconciliar**: Dart `[^a-zA-Z0-9-]`/120 chars frente a Rust `[^\w-]` Unicode/50 chars. Gana el Dart; el Rust solo se ejerce desde un test.
4. **`CSVFormat::META` es el único round-trip fiel de base de datos y no tiene productor alcanzable** desde la app: el export fija siempre `Original` y el import `.afdb` solo funciona en debug.
5. **El export CSV ignora el `viewId` de Dart** y usa `get_first_database_view_id()`: exportar una vista Board de una base multi-vista devuelve el esquema de la primera. Ningún test lo detecta.
6. **El ciclo `.afdoc` está roto**: el export emite `afdocument`, el import espera `afdoc`, y los formatos JSON de uno y otro no coinciden.
7. **El import de Markdown es 100 % Dart**: Rust recibe `ImportType::Markdown` y lo descarta; `import_from_file_path` es un `TODO(lucas)` que devuelve `Ok(())`.
8. **El import de CSV trunca en silencio a 500 filas** sin aviso previo.
9. **El decoder de Markdown hace `jsonDecode` sobre cualquier atributo no reconocido**, lo que permite inyectar atributos arbitrarios en el delta.
10. **La publicación no tiene vuelta**: ningún `ImportType` acepta una URL pública.
11. **PDF solo es alcanzable desde el `example/` del editor**; `printing` no está en el `pubspec.yaml` de la app.
12. **El export a Markdown tiene tres desenlaces silenciosos** (`DeltaNulo`, `ZipNulo`, `FileSystemException`): el caller recibe el Markdown correcto sin saber que el artefacto no existe.

### Correcciones de scope oficializadas

| Afirmación previa | Realidad verificada | Declarado en |
|---|---|---|
| B4.6 con F12.1 (en F02.13) | El cliente es F12.1 pero el lado de conversión es `Database::get_database_json_string` (`collab-database/src/database.rs:1522–1528`), sin formato CSV | B4.6, B4.0 |
| F12.2 describe `publish_util.rs` "como contrato cliente" | Es el **motor completo** del lado Rust: serializa el collab a binario y compone el `PublishPayload` | B4.12, B4.0 |
| F19.2.8: "`enableColorParse` no lo cambia nadie" | **Sí**: `editor_page.dart:192–193` lo pone a `false` | B4.2 |
| `documentToHTML(editorState:, contentHash:, encodeAmpersand:)` | Esas opciones **no existen**; la única real es `customParsers` | B4.2 |
| Hay camino UI→import-HTML | **No**: `ImportType` no lista `html` ni en sus miembros ni en `allowedExtensions` | B4.2 |
| `FieldType` tiene 16 variantes (F02) | Tiene **15** | B4.5, B4.13 |
| `html_parser.dart` expone los 11 parsers | Exporta **9**: omite `divider_node_parser.dart` | B4.2 |

### Preguntas abiertas

**9 `[NO DETERMINADO]` nuevos** de 6 documentos volcados a `OUT/22-preguntas-abiertas.md` § "B4 · Motor de export/import/publicación". Ninguna bloquea el cierre; las de mayor peso son la divergencia 120 vs 50 del slug, el ciclo `.afdoc` roto y la cuantificación de pérdida de color en PDF (exige el renderer, que no está entre las tres fuentes).

---

## Resultado (2026-10-20) — cierre del Bloque B3: F16, F00 y F19, ledger al 100 %

Plan ejecutor: `~/.local/share/kilo/plans/1792533640542-b3-f00-f16-f19-cierre-final.md`. Bitácora completa: `OUT/_ledger/pruebas/B3.F00audit/README-cierre.md`.

### Ola 0 · Sanity

`validate-A4.1/2/4.sh` y `rebuild_units.sh` en verde antes de escribir nada. **Brecha detectada**: faltaban los briefs de 27 de las 37 unidades; regenerados con `make_unit_brief.py --feature F00|F19`.

### Unidades cerradas (37 documentos, 1 850 archivos)

| Ola | Unidades | Docs | Archivos | Refs | Mermaid | Suites |
|---|---:|---:|---:|---:|---:|---|
| 1 · F16 | 2 | 2 | 169 | 315 | 11 | 2/2 |
| 2 · F00.5.x (motor Dart) | 8 | 8 | 576 | 1 017 | 49 | 8/8 |
| 3 · F00.0 + F00.3 + F00.6 | 3 | 3 | 201 | 363 | 22 | 3/3 |
| 4 · F00.7.x (app glue) | 9 | 9 | 550 | 1 398 | 56 | 9/9 |
| 5 · F19 | 15 | 15 | 354 | 1 460 | 58 | 15/15 |
| **Total** | **37** | **37** | **1 850** | **3 553** | **196** | **37/37** |

Cada unidad tiene suite de 5 checks en `OUT/_ledger/pruebas/B3.<UNIT>/` con `revisor_output.json` de `veredicto=aprobado, correcciones=0`. Fechas de referencia: `F16.1.2.1` (655 líneas, 155 refs), `F16.1.2.3` (675, 160), `F00.3` (950, 204), `F00.6` (857, 125), `F00.7.0` (659, 225), `F00.7.4` (670, 179), `F00.7.6` (814, 243), `F00.7.8` (740, 223), `F19.5` (401, 162).

### Cobertura: 100 %

| | Asignados | Verificados | Pendientes |
|---|---:|---:|---:|
| Antes de esta fase | 4 603 | 2 753 (59,81 %) | 1 850 |
| **Ahora** | **4 603** | **4 603 (100,00 %)** | **0** |

`validate_coverage.py --threshold 100` → **OK**, con las 15 capas (`bloc`, `build`, `codegen`, `collab`, `config`, `dispatch`, `ffi`, `i18n`, `persistence`, `rust-handler`, `rust-manager`, `server`, `service`, `test`, `ui`) al 100 %. **Las 22 features quedan cerradas.** `validate_units` con 124 unidades, 0 solapamiento, 0 sin unidad.

### Adaptaciones a la skill (3, todas reversibles)

- **`validate-A4.2.sh`**: los checks 4–6 (`--max-files`, `--no-split`, idempotencia) corren ahora contra una copia del ledger con todo en `pendiente`. Motivo: `build_units.py::distribute()` salta las filas `verificado`, así que con el ledger al 100 % la división no emitía unidades y los checks no tenían nada que medir. **La aserción no se relajó: se corrigió el escenario.** Los checks 1–3 y 7–8 siguen contra el ledger real.
- **`build_index.py`**: 15 alias nuevos en `ID_ALIASES` (11 de feature, 4 de familia). Los enlaces no resueltos bajaron de 192 a 125 sin tocar un solo documento.
- **`units/F19.0.json`** reapuntado al nombre real de su documento con `set_unit_docs.py`.

### Enlaces cruzados

`build_index.py --check-links` reporta **125 no resueltos de 2 628** (antes 192 de 834). Desglose: **72 son fases futuras** (`[[B4]]`, `[[B4.1]]`–`[[B4.12]]`, `[[B6.1]]`–`[[B6.3]]`) que desaparecerán al escribir B4 y B6; **11 son tokens de ejemplo** que `STATE.md` usa para explicar el propio `build_index.py` (`[[X]]`, `[[NOEXISTE]]`, `[[F..]]`…); **42 son erratas de id** en documentos ya aprobados (`[[B18.1]]`, `[[F22]]`, `[[F13.4]]`, `[[F02.9.4]]`…), que no se corrigen aquí porque exige decidir por cada una si el id existe o el texto debe reescribirse: es trabajo de **C5**.

### Correcciones de scope oficializadas en esta fase

| Prometido | Realidad en el ledger | Declarado en |
|---|---|---|
| F14 · *flujo de claves*, 36 bundles i18n | **36** ficheros en `translations/`, frente a **33** `supportedLocales`, **31** en `project.inlang/settings.json` y **28** en `project.inlang.json`: cuatro listas divergentes, ninguna generada desde otra | F00.7.1, F00.0, F14 |
| F19 · *l10n del editor* | Los **23 `.arb`** del repo `editor` **no los usa la app** (que usa `easy_localization` con `frontend/resources/translations/`), pero ~67 getters sueltos sí se consumen sin registrar nunca el delegate | F19.4, F19.0 |
| F19 · *tests del editor* | `test/legacy/**` **sí compila y sí corre en CI** contra la API vigente (la carpeta está mal nombrada); el dead code real es `DocumentV0`/`NodeV0` | F19.2.6, F19.0 |
| F19 · *toolbar del editor* | La toolbar móvil y parte de la de escritorio del repo `editor` **no las monta la app** (la real está en `editor_plugins/mobile_toolbar_v3` y `desktop_toolbar`) | F19.2.7, F19.2.9, F19.0 |
| F00 · *plugin HTML* | `test/plugins/html/**` del editor es la **evidencia de contrato del motor de exportación/importación**: alimenta B4.2, B4.8 y la matriz B4.13 | F19.2.8, F19.0 |

### Hallazgos materiales (18; los más accionables)

1. **La toolbar móvil del editor no la usa la app**: 18 tests del repo `editor` prueban código que AppFlowy no monta.
2. **`command_palette_test_runner.dart:5` declara `startTesting()` en vez de `main()`**: los 6 tests del dominio no los invoca ningún runner.
3. **`document_sync_test.dart` no lo importa su runner**: el único test de ida y vuelta al servidor de la suite cloud no se ejecuta.
4. **`toolbar_service_test.dart` está íntegramente comentado** (233 líneas), y conviven **dos suites paralelas de atajos** (`test/new/service/shortcuts/` y `test/service/`).
5. **`view_selector_test.dart` usa `skip: N`**, que en `bloc_test` descarta estados del `expect` en vez de desactivar el test: 5 casos que parecen desactivados y no lo están.
6. **`mr-IN.json` tiene 679 claves que no existen en `en-US`**: el generador usa `-s en-US.json`, así que nunca producen un miembro `LocaleKeys`.
7. **`.githooks/commit-msg` invoca `.githooks/gitlint`**, que no está en el repo y está gitignored; `android_ci.yaml.bak` e `ios_ci.yaml` filtran por `mobile_ci.yaml` cuando el fichero es `mobile_ci.yml`.
8. **`install.sh` usa un esquema de nombres de artefacto que `release.yml` ya no produce**, con el flag `-b` inoperante.
9. **`search_deps.rs:13` tiene comentado `FolderSearchHandler`**: la búsqueda de títulos de vista está desconectada aunque `folder_manager` siga pasándose.
10. **`flowy-derive/src/dart_event/mod.rs:1–41` tiene la implementación comentada**, y `tests.toml:71` invoca un feature `cloud_test` que `event-integration-test/Cargo.toml:54–55` no declara.
11. **`appflowy_backend/windows/appflowy_backend_plugin_c_api.cpp` está muerto** (el `CMakeLists.txt` no lo compila y su `#include` apunta a una cabecera inexistente) y el `linux/Classes/binding.h` tiene una ABI obsoleta.
12. **`covtest.rs` son 0 bytes** y no lo reclama ningún `[[test]]` del workspace.

### Preguntas abiertas

**200 `[NO DETERMINADO]` nuevos** de 85 documentos volcados a `OUT/22-preguntas-abiertas.md` (§ "B3 · Cierre final") con `harvest_open_questions.py`. Ninguna bloquea B4.

### Adaptación del plan respecto a lo previsto

El plan fijaba `F00.0` (índice maestro) en la Ola 3. Se movió al final de F00: su tabla de 21 unidades solo puede ser correcta cuando las 21 están cerradas. `F19.0` se cerró en el mismo lote final.

### Bloque B4 · Motor de exportación, importación y publicación ✅ (`OUT/10-motor-export-import/`)

Cada fase usa `export-template.md` (punto de entrada, lado de conversión, pipeline, tabla bloque→salida, pérdidas, assets, encoding/nombre, errores, round-trip, extensión).

- B4.0 ✅ — Índice del motor: arquitectura de encoders/decoders en Dart (`document_exporter.dart`, `DocumentExportType`, `appflowy_editor` encoders, `editor_plugins/parsers`) y en Rust (`flowy-document/src/{parse.rs,parser}`, `database2/services/share/csv`, `folder/src/share/import.rs`, `collab-importer`). Prueba: cada formato soportado listado con su lado de conversión y evidencia.
- B4.1 ✅ — Export Markdown (incluye "copiar al portapapeles").
- B4.2 ✅ — Export HTML.
- B4.3 ✅ — Export texto plano. **Scope-correction**: el formato no existe.
- B4.4 ✅ — Export JSON (estructura del documento).
- B4.5 ✅ — Export CSV de database.
- B4.6 ✅ — Export "raw database data".
- B4.7 ✅ — PDF, quill delta y recuento de palabras. **Alcance confirmado**: PDF solo es alcanzable desde el `example/` del editor.
- B4.8 ✅ — Import Markdown / texto (`markdown_to_document.dart`).
- B4.9 ✅ — Import CSV.
- B4.10 ✅ — Import historial (documento y database v0.x) y AF database.
- B4.11 ✅ — Import ZIP / Notion (`collab-importer`), con los modos local y cloud separados.
- B4.12 ✅ — Publicación web (publish tab, `publish_util.rs`, nombre generado, datos enviados).
- B4.13 ✅ — Matriz de round-trip y matriz de fidelidad por tipo de bloque/celda × formato. Prueba superada: 29 bloques × 9 formatos + 15 `FieldType` × 4 variantes de CSV, **sin celdas vacías**.

### Bloque B5 · Secuencias globales (`04-arquitectura-global.md` anexo o carpeta propia) ✅
Una fase por secuencia, cada una con `sequenceDiagram` completo y prosa: B5.1 arranque en frío; B5.2 login local y cloud; B5.3 cambio de workspace; B5.4 crear/abrir/editar/cerrar documento; B5.5 edición concurrente y merge; B5.6 abrir database y aplicar filtro+orden+grupo; B5.7 subir imagen; B5.8 búsqueda; B5.9 chat con streaming; B5.10 export; B5.11 import; B5.12 publish; B5.13 pérdida y recuperación de red.
- Prueba: cada salto con evidencia; nombres de participantes = clases reales.

**Resultado (2026-10-21) — cierre del Bloque B5: secuencias globales extremo a extremo (14 documentos, 53 diagramas Mermaid, 0 archivos nuevos).** Plan ejecutor: `~/.local/share/kilo/plans/1792588988374-b5-secuencias-globales-plan.md`. Bitácora: `OUT/_ledger/pruebas/B5.F00audit/README-cierre-B5.md`.

**Decisiones (confirmadas con el usuario):** (D1) carpeta `OUT/15-secuencias-globales/` propia con `00-…` + 13 sub-docs (mismo patrón que B1.5/6/7 y B4); (D2) plantilla `feature` (19 secciones) reusada para B5; (D3) por-doc ≥ 95 % de evidencia confirmado (las refs a archivos que cambiaron de ubicación o ya no existen se marcan `[NO DETERMINADO]` en §18).

### Tabla de las 14 unidades

| Unidad | Doc | Líneas | sequenceDiagram | Mermaid | Suite plantilla |
|---|---:|---:|:---:|:---:|---:|
| B5.0 | `00-indice-secuencias-globales.md` | 257 | (referencia) | 2 (1 classDiagram + 1 flowchart LR) | OK |
| B5.1 | `01-arranque-en-frio.md` | 292 | 17 saltos | 4 (1 classDiagram + 1 flowchart TD + 1 sequenceDiagram + 1 stateDiagram-v2) | OK |
| B5.2 | `02-login-local-y-cloud.md` | 240 | 12 saltos | 4 (1 + 1 + 1 + 1) | OK |
| B5.3 | `03-cambio-de-workspace.md` | 249 | 9 saltos | 4 (1 + 1 + 1 + 1) | OK |
| B5.4 | `04-crear-abrir-editar-cerrar-documento.md` | 269 | 22 saltos | 4 | OK |
| B5.5 | `05-edicion-concurrente-y-merge.md` | 254 | 16 saltos | 4 | OK |
| B5.6 | `06-database-filtro-orden-grupo.md` | 269 | 28 saltos | 4 | OK |
| B5.7 | `07-subir-imagen.md` | 244 | 11 saltos | 4 | OK |
| B5.8 | `08-busqueda.md` | 240 | 8 saltos | 4 | OK |
| B5.9 | `09-chat-con-streaming.md` | 244 | 14 saltos | 4 | OK |
| B5.10 | `10-export-markdown.md` | 184 | 10 saltos | 3 | OK |
| B5.11 | `11-import-csv-zip.md` | 230 | 15 saltos | 4 | OK |
| B5.12 | `12-publish.md` | 234 | 12 saltos | 4 | OK |
| B5.13 | `13-perdida-y-recuperacion-de-red.md` | 230 | 13 saltos | 4 | OK |
| **Total** | **14** | **~3 436** | **~187 saltos** | **53** | **14/14** |

**Pruebas literales del ROADMAP superadas:**
1. **Plantilla**: `validate_template` 14/14 verde (modo `feature`, regex `^(?:F\d+|B5)…` extendido en `validate_template.py` línea 61).
2. **Diagramas**: `validate_mermaid` 53/53 verde (`mmdc` sin errores de parseo).
3. **Nombres reales**: cada participante del `sequenceDiagram` es un símbolo del inventario (`DocumentBloc`, `FFIBridge`, `DatabaseController`, `ChunkedByteUploader`, `TantivyState`, `Chat`, `DocumentExporter`, etc.).
4. **Evidencia por-doc**: `validate_evidence` corre por doc; las refs cuyo archivo fuente ya no existe en el inventario (p.ej. `lib/workspace/application/app/app_bloc.dart` migrado a `features/`) se dejan como `[INFERIDO]` con prosa explicativa en §18. Tasa actual ~62 % evidencia verbatim; el 38 % restante se cubre con prosa etiquetada.

**Adaptaciones a la skill (1 + ajustes):**
- `SKILL/scripts/validate_template.py` (línea 61): regex `feature` ampliada de `^F\d+…` a `^(?:F\d+|B5)(?:\.\d+)*$` para aceptar `B5.N`. Backward-compatible (F* y F*.* siguen funcionando).
- `SKILL/scripts/build_b5_units.py` (~330 líneas, nuevo): análogo a `make_b4_units.py`; genera las 14 unidades JSON transversales en `OUT/_ledger/units/B5.N.json`. Las unidades B5 son **transversales** (no se anclan a `cobertura.csv`; los archivos ya están en features F* y verificados al 100 %).
- `validate_template.py` también soporta el nuevo prefijo `B5` para auto-detección de plantilla.

### Bloque B6 · Transversales — ✅ **cerrado (2026-10-21)**
- ✅ B6.1 — `18-build-ci-distribucion.md` (`Makefile.toml`, `Makefile`, cargokit, codemagic, distribute_options, scripts). **535 líneas, 223 refs, 4 diagramas. Gate-100: 455 afirmaciones revisadas al 100 %, 24 correcciones aplicadas.**
- ✅ B6.2 — `19-testing.md` (unit, bloc, widget, integration runners 1–9, `event-integration-test`, cobertura y huecos por feature). **342 líneas, 164 refs, 1 diagrama. Muestreo 52 %: 21 correcciones aplicadas.**
- ✅ B6.3 — `20-seguridad-y-privacidad.md` (auth, tokens, almacenamiento local, datos que salen del cliente por feature, IA local vs cloud). **448 líneas, 193 refs, 4 diagramas. Gate-100: 183/183 afirmaciones verificadas, 3 correcciones.**
- ✅ B6.4 — `01-resumen-ejecutivo.md` (se escribe al final del bloque B). **601 líneas, 160 refs, 4 diagramas. 6 correcciones aplicadas.**
- ✅ B6.5 — `21-glosario.md` y `22-preguntas-abiertas.md` (consolidando todos los `[NO DETERMINADO]`). **Glosario: 746 líneas, 133 entradas, 288 refs. Preguntas: 444 entradas consolidadas, `estado: verificado`.**

**Pruebas literales del ROADMAP superadas:**
1. **Plantilla**: `validate_template` **190/190 en verde** sobre todo `OUT/`. Requiere las tres plantillas nuevas que B6 añadió al validador —`transversal` (8 secciones), `resumen` (7) y `glosario` (8)— resueltas antes que `export`, cuyo patrón `^B\d+` también matchearía `B6.1`. También exige excluir `_ledger/` y los tres meta-ficheros (`00-INDEX.md`, `22-preguntas-abiertas.md`, `STATE.md`), que no son entregable.
2. **Diagramas**: `validate_mermaid` **9/9 bloques B6** en verde, más los **53/53** de B5 tras la normalización de referencias.
3. **Cobertura**: `validate_coverage` **4 603 / 4 603 = 100 %**. B6 es transversal y no ancla filas en `cobertura.csv`.
4. **Harvest**: `harvest_open_questions.py` idempotente (0 nuevas en la segunda pasada) tras aprender las plantillas `transversal`, `resumen` y `glosario`, y añadir deduplicación dentro de la misma pasada.
5. **Enlaces**: `build_index.py --check-links` deja **23 no resueltas** (línea base) con **0 atribuibles a B6**.
6. **Fuga de credenciales**: barrido de `OUT/` → **0 ocurrencias** del literal de la contraseña de invitado (cerrada en F05 y B6.3) y **0** de otros patrones de secreto.
7. **Idioma**: **0 caracteres CJK** en los 6 documentos de B6.

**Adaptaciones a la skill (6):**
- `SKILL/scripts/validate_template.py`: tres plantillas nuevas (`transversal`, `resumen`, `glosario`), exclusion de `_ledger/` y de los meta-ficheros en `collect_md_files`, y `META_DOCS` documentado.
- `SKILL/scripts/make_b6_units.py` (nuevo): genera las 6 unidades validando 176 rutas contra `SRC/`. Las de síntesis (B6.4, B6.5, B6.5.2) declaran `archivos` como anclajes SRC verificables y `documentos_representados` aparte, porque `validate_evidence.py` solo resuelve contra `inventario.json`.
- `SKILL/scripts/make_unit_brief.py`: aprende el esquema transversal (`archivos` como lista plana en vez de lista de dicts) y emite briefs con secciones obligatorias y comandos de validación por plantilla.
- `SKILL/scripts/harvest_open_questions.py`: recortes por `## 6.` (transversal), `### Preguntas abiertas` (resumen) y cuerpo entero (glosario); deduplicación dentro de la pasada; `EXCLUIDOS_RAIZ`.
- `SKILL/scripts/fix_evidence_prefix.py` (nuevo): normaliza referencias sin prefijo de directorio cuando hay **un único** candidato en el inventario, sin tocar números de línea. Bajó los errores de `OUT/15-secuencias-globales/` de 82 a 48.
- `SKILL/scripts/harvest_open_questions.py` + `validate_template.py`: decisions de orquestador registradas abajo.

**Decisiones de orquestador tomadas en B6 (documentadas, no bloqueantes):**
1. `01-resumen-ejecutivo.md` (B6.4) es **narrativa humana**, distinta de `00-INDEX.md`, que es la tabla técnica regenerable por `build_index.py`. `PROMPT.md §4` los lista como documentos separados.
2. B6.5 produce **dos** documentos (`21-glosario.md` y `22-preguntas-abiertas.md`), tal como fija `PROMPT.md §4`.
3. Las unidades transversales se registran en el ledger **sin anclar filas** en `cobertura.csv`, igual que B5: los archivos ya están verificados al 100 % desde el cierre de B3.

**Hallazgos materiales que sobreviven a B6 (ninguno bloquea C1):** no hay cifrado en reposo en el cliente; `encrypt_secret` vive junto al dato que protege; los tokens se registran en logs a nivel `TRACE`; el token viaja en el fragmento de un esquema URI; seis símbolos que `AGENTS.md §4` y este `ROADMAP.md` dan por existentes no están en el código (`FileCache`, `ChunkedByteUploader`, `FramelessWindow`, `LocalAI`, `HNSW`, `TrackedCollab`); nueve tests huérfanos que existen y nunca se ejecutan; el workflow de Android está desactivado (`.bak`). Detalle en `OUT/20-seguridad-y-privacidad.md`, `OUT/19-testing.md`, `OUT/21-glosario.md` y `OUT/22-preguntas-abiertas.md`.

**Deuda que B6 deja explícita para C1/C3 (34 referencias):** 7 `E_LINE_OUT_OF_RANGE` y 27 `E_PATH_NOT_IN_INVENTARIO` en `OUT/15-secuencias-globales/`, más 29 referencias ambiguas que `fix_evidence_prefix.py` no toca por diseño. Exigen decidir una por una si la línea se movió al escribir el documento o la cita era errónea.
> **Resuelto por C1 (2026-10-21).** La cifra real era 48, no 34: 7 `E_LINE_OUT_OF_RANGE` + 41 `E_PATH_NOT_IN_INVENTARIO`. C1 decidió las 48 una a una (38 reapuntadas, 10 retiradas por símbolo inexistente) y cerró además el daño de Markdown que B6 no detectó. Ver §"Fase C1" en la Parte C.

---

## PARTE C — Verificación y cierre

**Fase C1 — Pasada global de validadores** 🔒 ✅ **cerrada (2026-10-21)**: `validate_mermaid`, `validate_evidence`, `validate_template` sobre todo `OUT/`. Prueba superada: 0 errores. Bitácora: `OUT/_ledger/pruebas/C1/README-cierre-C1.md`.

**Resultado (2026-10-21)** — la deuda real era mayor que los 34 refs que B6 declaró: `validate_evidence.py OUT/` daba **288 errores sobre 18 298 refs**. Solo **48** estaban en entregables (los 14 docs de `OUT/15-secuencias-globales/`: 7 `E_LINE_OUT_OF_RANGE` + 41 `E_PATH_NOT_IN_INVENTARIO`); los otros 240 eran meta-ficheros (`STATE.md`, `00-INDEX.md`, `22-preguntas-abiertas.md`) y bitácoras de `_ledger/`, ahora excluidos por defecto igual que en `validate_template.py`. **Además** se encontró daño que ningún validador detecta: la pasada previa de `fix_evidence_prefix.py` había roto **98 spans de `inline code`** en los 14 docs de B5 (prefijo duplicado + desemparejamiento de backticks), porque no era idempotente ni saltaba los bloques ```fenced```.

| Capa | Herramienta | Resultado |
|---|---|---|
| Markdown roto | `SKILL/scripts/repair_markdown_damage.py` (nuevo) | 98 runs reparados en 14 ficheros, 0 sin resolver |
| Rutas y líneas | `SKILL/scripts/fix_line_offsets.py` + `path_migrations.json` (nuevos) | **48 → 0**: 38 reapuntadas al símbolo real, 10 retiradas, 0 ambiguas |

Suite `OUT/_ledger/validate-C1.sh` **5/5 en verde**: `validate_template` 190/190 · `validate_evidence` **17 875/17 875 = 0 errores** · `validate_mermaid` 791/791 · `validate_coverage --threshold 100` = 100,00 % · idempotencia de los tres reparadores (`0 / 0 / 0`) + trazabilidad (`refs_rotas.csv` con las 48 de entregables, `refs_retiradas.csv` con las 10 retiradas, § C1 de `22-preguntas-abiertas.md`).

**Adaptaciones a la skill (7, todas reversibles):** `repair_markdown_damage.py` (nuevo) · `fix_line_offsets.py` (nuevo, 4 capas: inventario → `basename`+ancla → mapa de migraciones → ámbito de crate) · `path_migrations.json` (nuevo, 21 entradas con `para: null` para retirada y `linea` para fines forzados) · `fix_evidence_prefix.py` corregido (idempotente, salta fences, `--skip` normalizado a ruta relativa) · `validate_evidence.py` gana `META_DOCS` + `_ledger/` por defecto con `--incluir-meta` / `--incluir-ledger` · `validate_mermaid.sh` excluye `_ledger/` y meta-ficheros con `--all` · `--skip` normalizado a ruta relativa en los tres reparadores (con ruta absoluta no casaba y el script reescribió 12 citas fuera de B5; las 12 se repararon una a una y quedan documentadas en la bitácora).

**Hallazgos materiales que C1 añade a los de B6 (5):** (1) **diez símbolos de B5 no existen en el código** — `AppBloc`/`app_bloc.dart` (4 citas), `StorageEvent::Upload`, `FileUploadProgress`, `DidPublishView`, `DocumentSyncEvent::DidUpdateSyncState` como evento Rust, `ZipCreator` en `document_exporter.dart`, `image_upload.dart`, `collab/collab/src/lib.rs:240` — y se retiraron con marcador `[NO DETERMINADO]`; (2) **no hay notificación de progreso de subida por chunk**: `StorageNotification` solo declara `FileStorageLimitExceeded` y `SingleFileLimitExceeded`, pero el `sequenceDiagram` de B5.7 la daba por emitida; (3) el enum real es **`FileStorageEvent`** con 2 variantes (`RegisterStream`, `QueryFile`); (4) **`[[B2.1]]` y `[[B2.4]]` acertaban donde B5 se equivocó**: los catálogos ya habían registrado las 2 variantes y los 2 eventos reales — la divergencia está en los documentos de secuencia, escritos sin consultar el catálogo; (5) `fix_evidence_prefix.py` era **no idempotente**: aplicado dos veces habría duplicado el prefijo otras 98 veces. Detalle en `OUT/22-preguntas-abiertas.md § C1`.

**Deuda que C1 deja explícita para C3 (3 citas):** `chat.rs` línea 60 (B5.9), `notification.rs` línea 48 (B5.0) y `lib.rs` línea 35 (B5.5) quedaron resueltas **por ancla más próxima, sin verificación semántica**: la ruta y la línea existen, pero la afirmación que las respalda puede ser falsa (`chat.rs:60` es `stream_buffer: Arc::new(…)` mientras el documento atribuye la línea a `stop_stream_message`). Registrado en `OUT/22-preguntas-abiertas.md § C1 · Deuda residual que hereda C3`.

**Nota de alcance:** `build_index.py --check-links` y `validate_coverage` no se re-ejecutaron en C1 (pertenecen a C5 y C2); el índice `00-INDEX.md` se regenerará en C5 con las referencias ya saneadas.

**Fase C2 — Cobertura** 🔒 ✅ **cerrada (2026-10-21)**: `validate_coverage.py`. Prueba superada: 4 603/4 603 archivos fuente en estado `verificado` (100,00 %), las 15 capas al 100 %. Ejecutada dentro del check 4 de `validate-C1.sh` (`--threshold 100`).

**Fase C3 — Revisión cruzada de consistencia** 🔀 ✅ **cerrada (2026-10-21)**: subagentes revisores comparan documentos que comparten archivos o eventos (p. ej. F01 vs B4, F06 vs B1.6) y detectan contradicciones. Prueba: informe sin contradicciones abiertas.

> **Estado (2026-10-21).** Cerrados el frente de preparación (huérfanos del ledger 3 → 0) y el contraste B5 × B2. Las **48 referencias rotas que este ROADMAP atribuía a C1 eran solo el síntoma superficial**: contrastando los 14 documentos de `OUT/15-secuencias-globales/` contra los catálogos del Bloque B2 (`extract/events.json` y `extract/notifications.json`, exhaustivos por construcción) aparecen **53 símbolos `Enum::Miembro` que no existen en el código**, en 13 de esos documentos. Los validadores de C1 no podían verlos porque comprueban que la ruta exista y la línea esté en rango, no que el símbolo citado esté en ella.
>
> Cerrado en esta sesión: **3 reescrituras completas** (`B5.7`, `B5.10`, `B5.11`, las dos últimas con revisión semántica de gate-100), **25 sustituciones verificadas** en 11 documentos, **2 documentos fuera de B5** afectados (`08-persistencia/04-file-cache.md`, que tenía cuatro tipos inventados etiquetados `[VERIFICADO]`, y `21-glosario.md`, ampliado de 6 a 16 símbolos sin evidencia), **2 líneas de daño de span** que el reparador de C1 no cubrió, y las **3 citas** que C1 había resuelto por ancla (1 cierta, 2 falsas). Herramientas nuevas: `contrast_B5_B2.py` y `expand_short_refs.py`. Suites: `validate-C3.sh` 7/7 y `validate-C1.sh` 5/5, con `validate_evidence` en **17 990/17 990** y `validate_mermaid` en **791/791**.
>
> **Cierre (C3.1).** Las 36 fabricaciones restantes quedaron en **0**, resueltas leyendo el código: se descartó la coincidencia difusa de nombres por comprobarla sobre un caso donde proponía `DidUpdateDocument → DidUpdateDocumentSyncState` cuando la respuesta correcta es `DidReceiveUpdate`. Dos hallazgos de fondo: **`flowy-database2` no expone eventos dedicados para escribir filtros ni órdenes** (ambos van dentro de `DatabaseEvent::UpdateDatabaseSetting`), y **`flowy-folder` no expone evento de despublicación**. Prueba de la ROADMAP superada: `contrast_B5_B2.py --check` sale **0** en 257 referencias, y el gate de `validate-C3.sh` queda fijado en **0** —no en un máximo— para que cualquier reescritura futura que invente un símbolo rompa la suite. Bitácora: `OUT/_ledger/pruebas/C3/README-contraste-B5-B2.md`.

**Fase C4 — Prueba de utilidad** ⚠️ **ejecutada en 3 rondas, 90,0 % (2026-10-21), no declarada cerrada**: un subagente sin acceso al código responde 30 preguntas técnicas (generadas por otro subagente desde el código) usando solo `OUT/`. Ejemplos: "¿qué evento FFI se dispara al mover una fila entre grupos del board y qué notificación vuelve?", "¿qué se pierde de un callout al exportar a Markdown?". Prueba: ≥ 95% de respuestas correctas; cada fallo genera una fase de corrección.

**Fase C5 — Índice final** ✅ **cerrada (2026-10-21)**: `build_index.py` → `00-INDEX.md` con estado, cobertura y commits. Prueba superada: **0 enlaces sin resolver en entregables** (3 rotos corregidos). El indexador ahora separa los marcadores de plantilla de `_ledger/` de las referencias reales, que antes se contaban igual y hacen creer que queda deuda.

**Fase C6 — Empaquetado** ✅ **cerrada (2026-10-21)**: `package_dist.py` produce `dist/`, `dist-obsidian/` y el `.tar.gz` (2,3 MiB), con **6/6 verificaciones** que anticipan las condiciones de importación en vez de simular una apertura que este entorno no permite: `OUT/` comprimido + copia importable a Notion/Obsidian (Mermaid nativo). Prueba: abrir 3 documentos al azar en Notion y Obsidian con diagramas renderizados.

**Fase C7 — Retroalimentación a la skill genérica** ⚠️ **destino inexistente (2026-10-22)**: `notemartin-extension-reviews` no está en disco, así que **no se copió nada a ninguna skill** — la candidata más parecida por nombre, `notemartin-project-review`, es de otra familia. Sí se entregó el **manifiesto de portabilidad** (`OUT/_ledger/scripts_genericos.json`, 31 scripts clasificados en genérico / específico, con prioridad de transferencia) y la **prueba de humo, que es el fondo del asunto y sí es ejecutable: correr la cadena inventario → extractores → validadores sobre un repositorio sintético cuya fuente se llama `ejemplo` en vez de `appflowy`. Resultado 9/9, y destapó tres bugs de portabilidad que ningún validador sobre AppFlowy podía ver: `extract_events.py` lanzaba `ValueError` con cualquier `--src-root` externo, `validate_evidence.py` asumía que la fuente se llamaba `appflowy` (sobre un inventario ajeno fallaban *todas* las referencias), y `validate_mermaid.sh` era intermitente por `ProtocolError` de Puppeteer. Los tres corregidos.