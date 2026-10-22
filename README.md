# `notemartin-appflowy-review` — README

Documentación de la skill portable que produce la ingeniería inversa completa de
**AppFlowy** (Flutter + Rust + CRDT sobre `yrs`) desde el código fuente, en
español, con evidencia `ruta:línea` y cobertura verificable por ledger. Este
fichero explica qué es la skill, cómo se instala, cómo se dispara, qué contiene
cada pieza y en qué estado está. El flujo paso a paso vive en
[`flow.md`](./flow.md); las reglas de trabajo, en [`AGENTS.md`](./AGENTS.md); el
encargo original y las 8 etapas, en [`PROMPT.md`](./PROMPT.md); y el detalle de
cada fase con su prueba y sus gates, en [`CHANGELOG.md`](./CHANGELOG.md).

---

## 1 · Qué es y qué no es

La skill es un **procedimiento ejecutable**, no un documento. Dado el código de
AppFlowy, produce `OUT/appflowy-review/` (en este proyecto, `OUT/`) con la
arquitectura global, las 22 features documentadas una a una, el puente
Flutter↔Rust, el motor colaborativo sobre CRDT, la persistencia, la búsqueda, la
IA, y el motor de exportación/importación formato por formato.

Lo que la hace distinguishable de un "análisis con un LLM" son tres cosas
concretas: **evidencia obligatoria** (toda afirmación lleva `ruta:línea`, y un
validador comprueba que esa ruta exista en el inventario y que la línea esté en
rango), **cobertura cerrada** (4 603 archivos fuente inventariados y
`100 %` verificados antes de declarar el trabajo terminado), y **revisión
separada** (el documento lo escribe un subagente y lo juzga otro con contexto
limpio).

No es un resumen, ni una auditoría de seguridad, ni una guía de uso. No
documenta AppFlowy-Cloud por dentro —solo su contrato cliente desde
`flowy-server/src/af_cloud`—, no modifica el repo analizado y no ejecuta la app.

---

## 2 · Requisitos

| Requisito | Para qué | Notas |
|---|---|---|
| Python 3 (solo stdlib) | los 39 scripts `.py` | no hay `pip install`: cero dependencias Python |
| `ripgrep` (`rg`) | los extractores y varios validadores | búsqueda sobre `SRC/` |
| `git` | `fetch_sources.sh` y `sources.json` | clonar los tres repos en su rev |
| Node + `mermaid-cli` (`mmdc`) | `validate_mermaid.sh` | `npm i -g @mermaid-js/mermaid-cli`; sin él, solo se salta ese validador |
| Red (solo fase A1) | `fetch_sources.sh` | después, todo el trabajo es local |
| Subagentes (opcional) | autor y revisor por unidad | si la plataforma no los tiene, las unidades se ejecutan en serie con el mismo contrato (`AGENTS.md §9`) |

Discriminación útil: la parte cara es la fase A1 (clonar tres repos, uno de
ellos con historial completo) y la fase B (165 unidades de trabajo). Las fases
A2–A4 sonbaratas y deterministas; C6–C7 necesitan red solo para publicar.

---

## 3 · Instalación

La skill es una carpeta. Para que un agente la descubra, la carpeta debe llamarse
como el campo `name` del frontmatter (`notemartin-appflowy-review`) y vivir en
un directorio de skills del agente:

```bash
# instalación por enlace, si se quiere conservar el repositorio como fuente
ln -s /ruta/al/proyecto/SKILL ~/.agents/skills/notemartin-appflowy-review
```

La raíz del repositorio **es** la carpeta de la skill: todo lo que hay en ella es
portable, y `SKILL.md` está en la raíz porque es donde el descubrimiento de
skills.sh lo busca. `OUT/`, `SRC/` y `dist/` no viajan: los crea la skill al
ejecutarse. `SKILL.md` §7–§11 explica esa frontera.

---

## 4 · Cómo se dispara

Prompt canónico (copiar y pegar):

```
Revisa AppFlowy completo. Quiero OUT/appflowy-review/ con la
arquitectura global, todas las features documentadas con diagramas
Mermaid, el motor colaborativo, la persistencia, la búsqueda, la IA
y el motor de exportación/importación. Idioma español, evidencia
ruta:línea, cobertura verificable por ledger.
```

También dispara: "documenta AppFlowy", "auditoría técnica de AppFlowy", "mapea
AppFlowy", "ingeniería inversa de AppFlowy", "informe técnico de AppFlowy",
"analiza el código de AppFlowy", o pegar la URL del repo y pedir un informe
exhaustivo.

No dispara: resúmenes de un párrafo, responder una duda puntual de uso, hacer
cambios en el repo, ejecutar la app, o cualquier tarea que no tenga AppFlowy
como objeto. `SKILL.md §1` tiene la tabla completa de disparo y no-disparo.

---

## 5 · Arquitectura de la skill

```
notemartin-appflowy-review/          # esta carpeta ES la skill
├── SKILL.md                      # router (≤ 500 líneas, solo enruta) ·REQUIRED
├── PROMPT.md                     # encargo, 8 etapas, plantillas y mapa de features
├── AGENTS.md                     # reglas, patrones y protocolo de subagentes
├── README.md                     # este documento
├── flow.md                       # el flujo paso a paso, con diagramas
├── CHANGELOG.md                  # historial semver: una entrada por fase cerrada
├── references/                   # 9 documentos de referencia
│   ├── repo-map.md               # árbol de AppFlowy con propósito por carpeta
│   ├── patterns.md               # los 7 patrones de arquitectura, con ejemplos
│   ├── evidence-rules.md         # reglas de evidencia y etiquetas
│   ├── diagram-conventions.md    # Mermaid: tipos, IDs, etiquetas, fragmentación
│   ├── feature-template.md       # plantilla de 19 secciones para 09-features/
│   ├── export-template.md        # plantilla de 11 secciones para 10-motor-export-import/
│   ├── subagent-contract.md      # contrato común de autor y revisor
│   ├── subagent-autor-prompt.md  # prompt literal del subagente autor
│   └── subagent-revisor-prompt.md# prompt literal del subagente revisor
├── scripts/                      # 45 scripts (39 .py + 6 .sh)
└── templates/output-skeleton/    # árbol vacío de la salida, 25 entradas
```

`SKILL.md` está en la raíz a propósito: es la única posición que el
descubrimiento de skills.sh reconoce por defecto (raíz del repo con `SKILL.md`,
o `skills/<nombre>/SKILL.md`). Frontmatter con `name` y `description`, y ambos
valores deben parsear como YAML: un `": "` suelto dentro de un valor sin comillas
hace que el frontmatter entero sea inválido y la skill no aparezca en el índice.

Fuera de la skill, en el proyecto donde se ejecute: `OUT/` (la salida del análisis),
`SRC/` (los tres repos clonados) y `dist/` (el paquete de entrega). Los crea la
skill; ninguno se publica.

---

## 6 · Los documentos primarios

| Fichero | Contenido | ¿Portable? |
|---|---|---|
| `PROMPT.md` | encargo, 8 etapas, estructura de salida, plantillas, mapa de features, glosario, lo que no se hace | sí |
| `CHANGELOG.md` | una entrada por fase cerrada, con sus gates, sus resultados y las adaptaciones de la skill | sí |

`SKILL.md` los lee en cada invocación (`§11`). Las rutas que aparecen en el resto
de este documento (`OUT/`, `SRC/`, `dist/`) son las que la skill crea en el
proyecto donde se ejecuta, no ficheros del repo publicado.

---

## 7 · Los 45 scripts

Agrupados por lo que hacen, que es como se piensa en ellos durante una fase.

### 7.1 · Adquisición e inventario (fase A1)

| Script | Qué produce |
|---|---|
| `fetch_sources.sh` | `SRC/{appflowy,collab,editor}` en los rev correctos: el `rev` de `[patch.crates-io]` en `Cargo.toml` para Collab y `dependency_overrides.appflowy_editor.git.ref` en `pubspec.yaml` para el editor |
| `inventory.py` | `_ledger/inventario.json` (4 603 archivos fuente) y `_ledger/assets.json` (1 186 binarios y recursos) |
| `init_ledger.py` | `_ledger/cobertura.csv` con las 4 603 filas en `sin_asignar` (7 columnas) |

### 7.2 · Extractores deterministas (fase A2)

Cada extractor recorre `SRC/` con expresiones regulares y escribe un JSON en
`_ledger/extract/`. Son la parte que hace que el análisis no dependa de que el
modelo se acuerde: los catálogos y las unidades se construyen sobre estos
ficheros, no sobre lo que el agente recuerde.

| Script | Qué extrae |
|---|---|
| `extract_events.py` | enums con `Flowy_Event` y sus `.event(Variante, handler)` en `event_map.rs`, con los PB de entrada y salida |
| `extract_protobuf.py` | todo lo derivado de `ProtoBuf` (structs) y `ProtoBuf_Enum` (enums) |
| `extract_notifications.py` | notificaciones Rust→Dart: `notification.rs`, `send_notification`, `NotificationBuilder` y los `*_listener.dart` |
| `extract_blocs.py` | clases `extends Bloc<…>` / `extends Cubit<…>`, sus eventos y estados, y servicios inyectados |
| `extract_deps.py` | dos grafos de dependencias (Rust y Dart) y sus bloques Mermaid |
| `extract_misc.py` | seis bloques: rutas `GoRoute`, atajos, feature flags, claves i18n, códigos de error, tareas de arranque |
| `extract_codegen.sh` | orquesta el codegen de `flowy-codegen` en un directorio aparte (el repo no trae `.proto` ni el Dart de eventos: se generan en build) |

### 7.3 · Catálogos (bloque B2)

Seis generadores que renderizan los catálogos del entregable desde los
extractores. `extract_*` produce el dato; `build_catalog_*` produce el
documento.

| Script | Documento que genera |
|---|---|
| `build_catalog_events.py` | `OUT/11-catalogo-eventos-ffi.md` |
| `build_catalog_protobuf.py` | `OUT/12-catalogo-entidades-protobuf.md` |
| `build_catalog_blocs.py` | `OUT/13-catalogo-blocs.md` |
| `build_catalog_notifications.py` | `OUT/14-catalogo-notificaciones.md` |
| `build_catalog_errors.py` | `OUT/15-catalogo-errores.md` |
| `build_catalog_misc.py` | `OUT/16-catalogo-flags-rutas-atajos.md` |

### 7.4 · Ledger, unidades y asignaciones (fases A4, B0)

Aquí vive el trabajo que hace que 4 603 archivos acaben documentados sin que
nadie tenga que llevar la cuenta a mano.

| Script | Qué hace |
|---|---|
| `assign_ledger.py` | reparte los archivos del inventario entre las features F01–F17 rellenando `feature_ids` |
| `build_units.py` | genera `_ledger/units/<id>.json` desde las features y los documentos |
| `validate_units.py` | comprueba esquema y coherencia de las unidades |
| `align_units.py` | elimina la doble propiedad después de regenerar unidades |
| `sync_units_from_docs.py` | reconstruye el campo `archivos` de cada unidad a partir de los documentos ya escritos (reconcilia lo que se dijo con lo que se escribió) |
| `rebuild_units.sh` | pipeline canónico de reconstrucción de unidades |
| `restore_unit_files.py` | reinyecta en una unidad las filas que se le habían asignado |
| `set_unit_docs.py` | fija a mano la ruta de documento de unidades concretas |
| `record_unit_state.py` | marca el estado de las unidades (abierta / en curso / cerrada) |
| `close_unit.sh` | cierra una unidad de B3: valida, genera la suite de 5 comprobaciones y actualiza el ledger |
| `make_unit_brief.py` | genera el brief de una unidad para dárselo al subagente autor |
| `make_phase_suite.py` | genera `validate-<FASE>.sh` para una unidad |
| `coverage_report.py` | estado de cobertura por feature y por unidad |
| `resume.py` | orquestador determinista de reanudación desde `STATE.md` |
| `harvest_open_questions.py` | vuelca los `[NO DETERMINADO]` dispersos a `22-preguntas-abiertas.md` |

### 7.5 · Subagentes

| Script | Qué hace |
|---|---|
| `run_subagent.py` | modo **revisor** del subagente definido en `references/subagent-revisor-prompt.md`: corre los validadores y devuelve `aprobado` o `rechazado + correcciones` |
| `run_subagent_author.sh` | wrapper que invoca un LLM externo para el subagente autor, con el prompt y el contrato de `references/subagent-autor-prompt.md` |
| `run_subagent_placeholder.py` | mock determinista del autor/revisor, para probar la cadena sin gastar un modelo |

### 7.6 · Validadores y reparación de daño

| Script | Qué comprueba o arregla |
|---|---|
| `validate_evidence.py` | extrae cada `ruta:línea` de un documento y verifica que la ruta exista en el inventario y que la línea esté en rango |
| `validate_mermaid.sh` | renderiza cada bloque ` ```mermaid ` con `mmdc` y falla con `archivo:bloque_nº` |
| `validate_template.py` | que un `.md` tenga todas las secciones obligatorias de su plantilla |
| `validate_coverage.py` | cruza `cobertura.csv` consigo mismo: cobertura global, por feature y por capa |
| `repair_markdown_damage.py` | repara spans de código inline rotos por Reparaciones anteriores |
| `fix_line_offsets.py` | reapunta referencias que ya no cuadran con el fichero real, en cuatro capas (inventario → `basename` + ancla → mapa de migraciones → ámbito de crate) |
| `fix_evidence_prefix.py` | normaliza referencias `ruta:línea` al prefijo de fuente; idempotente, salta bloques fenced |
| `expand_short_refs.py` | expande referencias cortas `archivo.ext:N` a la ruta completa |
| `mermaid_debug.py` | renderiza bloque a bloque para depurar un diagrama que no parsea |

Los cinco scripts de reparación no son opcionales: el estado real del proyecto
demostró que el daño documentado se acumula justo ahí. La bitácora de C1 recounts
98 spans rotos y 48 referencias malClaireadas encontrados por ellos.

### 7.7 · Índice y paquete (fases C5, C6)

| Script | Qué hace |
|---|---|
| `build_index.py` | genera `OUT/00-INDEX.md` con estado, cobertura y commits; `--check-links` separa enlaces reales rotos de marcadores de plantilla |
| `package_dist.py` | produce `dist/`, `dist-obsidian/` (enlaces convertidos a rutas relativas) y `OUT-appflowy-review-v1.0.tar.gz`, con 6 verificaciones que anticipan las condiciones de importación |

---

## 8 · Los 9 documentos de `references/`

| Referencia | Para qué se lee |
|---|---|
| `repo-map.md` | qué hay en cada carpeta de AppFlowy antes de abrir un archivo |
| `patterns.md` | los 7 patrones (registro de eventos, notificaciones, llamada Dart→Rust, DI, collab/CRDT, capas `*-pub`, arquitectura dual) con ejemplos reales |
| `evidence-rules.md` | cómo se cita y qué significan `[VERIFICADO]`, `[INFERIDO]`, `[NO DETERMINADO]` |
| `diagram-conventions.md` | qué tipo de diagrama para qué propósito, y cómo partir uno que crece |
| `feature-template.md` | las 19 secciones obligatorias de un documento de feature |
| `export-template.md` | las 11 secciones obligatorias de un formato de exportación |
| `subagent-contract.md` | el contrato común que comparten autor y revisor: qué reciben, qué devuelven, qué no pueden hacer |
| `subagent-autor-prompt.md` | el prompt literal del subagente autor |
| `subagent-revisor-prompt.md` | el prompt literal del subagente revisor |

---

## 9 · Las cuatro validaciones y las 46 suites

Los cuatro validadores son la puerta objetiva. Ninguna puerta se declara verde
porque "se ha revisado a ojo": se declara verde porque un script salió con 0.

| Validador | Pregunta que responde |
|---|---|
| `validate_evidence.py` | ¿toda cita apunta a algo que existe? |
| `validate_mermaid.sh` | ¿parsea cada diagrama? |
| `validate_template.py` | ¿el documento tiene todas las secciones? |
| `validate_coverage.py` | ¿está todo el inventario verificado? |

Además hay **46 suites** generadas en `OUT/_ledger/validate-<FASE>.sh`, una por
fase y por unidad cerrada, que encadenan varios validadores con umbrales fijos.
Son la memoria ejecutable del proceso: cada suite es la prueba de salida de su
fase, y volver a ejecutarlas es la forma barata de detectar regresiones tras
cualquier cambio.

---

## 10 · Protocolo de subagentes

El orquestador (el agente principal) **no escribe documentos de feature**.
Ejecuta scripts, mantiene el ledger, divide el trabajo, asigna, integra y
dispara la verificación. El trabajo de escritura y el de juicio van separados:

- **Unidad de trabajo**: `{id, título, archivos[], catálogos relevantes, plantilla, documentos dependientes}`. Si supera ~120 archivos se divide en sub-unidades, como se hizo con F01 durante esta ejecución.
- **Subagente autor**: lee **todos** sus archivos (no extractos), escribe el documento con la plantilla y devuelve `{documento, filas_ledger_cubiertas, archivos_extra_detectados, preguntas_abiertas}`. Si necesita un archivo que no le dieron, lo declara en vez de improvisar.
- **Subagente revisor**: distinto del autor, con contexto limpio. Corre los tres validadores de documento y además verifica semánticamente ≥ 30 % de las afirmaciones (100 % en F01, F02, F06 y en el motor de exportación/importación). Devuelve `aprobado` o `rechazado` con la lista de correcciones.
- **Concurrencia**: `MAX_PARALLEL` configurable. Los catálogos y la arquitectura global van primero porque alimentan a las features.

---

## 11 · El ledger

`OUT/_ledger/` es la memoria del proceso, y hay cinco cosas distintas dentro:

| Artefacto | Contenido |
|---|---|
| `sources.json` | los tres repos con commit, método de clonación y la evidencia de por qué ese commit |
| `inventario.json` / `assets.json` | 4 603 archivos fuente y 1 186 binarios, con su capa |
| `cobertura.csv` | 7 columnas por archivo: fuente, ruta, capa, features, documento, estado, verificado_por |
| `extract/*.json` | los seis catálogos deterministas que alimentan documentos y unidades |
| `units/*.json` | 165 unidades de trabajo con sus archivos y su documento |

La columna `verificado_por` no es decorativa: dice qué subagente verificó cada
archivo y cuándo (`autor_F00.5.1.2 @ 2026-10-20T22:56:14Z`). Es lo que permite
auditar quién escribió qué.

---

## 12 · Estado actual (a fecha de 2026-10-22)

| Bloque | Estado | Nota |
|---|---|---|
| A0–A5 | cerrado | incluye el piloto de F08 |
| B0–B6 | cerrado | 272 documentos en `OUT/`, de los cuales 193 entran en el paquete de C6; ledger al 100 % |
| C1 pasada global | cerrado | 5/5 en verde; 17 990/17 990 citas válidas; 791/791 diagramas |
| C2 cobertura | cerrado | 4 603/4 603 archivos verificados |
| C3 contraste cruzado | cerrado | 36 símbolos inventados llevados a 0; el contraste contra los catálogos sale en 0 |
| C4 utilidad | **no cerrada** | 90,0 % en 3 rondas, por debajo del umbral de 95 % |
| C5 índice | cerrado | 272 documentos, 3 483 enlaces, 0 sin resolver en entregables |
| C6 empaquetado | cerrado | `dist/`, `dist-obsidian/` y tar.gz de 2,3 MiB, 6/6 verificaciones |
| C7 retroalimentación | **bloqueada** | `notemartin-extension-reviews` no existe en disco |

Tres cosas que conviene saber antes de tocar nada:

1. **La skill se podó para publicarse.** Se retiraron 12 ficheros: `references/debt.md` (pertenecía a otra skill y esta no lo cableaba) y 10 scripts atados a una ejecución concreta —divisiones de unidades con ID fijo, generadores de planes de fase, el contraste de una ola y su mapa de reapuntamientos—. Quedan los 45 scripts genéricos, más `PROMPT.md` y este README.
2. **`CHANGELOG.md` va por detrás de `STATE.md`.** La última versión registrada es `0.12.0` (2026-10-21), mientras que C5–C7 se cerraron el 2026-10-22. `STATE.md` es la autoridad.
3. **C4 sigue abierta por métrica, no por desconocimiento.** 90 % de aciertos en 30 preguntas es un número alto, pero el umbral del ROADMAP es 95 % y no se rebajó. Cerrarla exige acertar el 5 % restante.

---

## 13 · Reanudar una ejecución

`SKILL.md §5` tiene los seis pasos; en resumen: leer `OUT/STATE.md`, localizar
la última fase cerrada, cargar `cobertura.csv` y los extractos de la fase
actual, saltar a la siguiente fase cuya puerta esté verde, y actualizar
`STATE.md` antes de devolver el control. Sin `STATE.md` al día, la reanudación
no es válida — y `resume.py` hace los primeros pasos de forma determinista.

---

## 14 · Gates

| Gate | Qué bloquea si falla |
|---|---|
| A1.1 | fuentes en el commit correcto (verificado: appflowy `5cf3a36`, collab `4dfccef`, editor `470c4e7`) |
| A3 | los cuatro validadores existen y pasan su smoke test |
| A5 | el piloto de F08 pasa revisión con 100 % de archivos cubiertos |
| B0.2 | queda algún archivo `sin_asignar` |
| C1 | una pasada global de validadores con errores |
| C2 | cobertura por debajo del 100 % |

---

## 15 · Convenciones que se aplican a todo lo escrito

- **Evidencia**: `ruta:línea` o `ruta:inicio–fin`, con prefijo de fuente cuando no es el repo principal (`collab:collab-document/src/document.rs:120`). Tres etiquetas: `[VERIFICADO]`, `[INFERIDO]`, `[NO DETERMINADO]`, y lo no determinado va a `22-preguntas-abiertas.md`.
- **Código**: fragmentos de ≤ 25 líneas, siempre con referencia.
- **Diagramas**: Mermaid según `references/diagram-conventions.md`, IDs sin espacios, ≤ ~60 nodos, y validados por `validate_mermaid.sh`.
- **Estilo**: español técnico; identificadores, rutas y comandos en original; párrafos completos (qué, cómo, por qué, dónde); cada documento abre con 3–6 líneas de resumen y cierra con "Relacionado con".

---

## 16 · Relación con otras skills

`AGENTS.md §2` la define como un **perfil especializado** de
`notemartin-extension-reviews`: los scripts genéricos (inventario, ledger,
validadores) deberían ser reutilizables, y lo específico de AppFlowy vive en
`references/` y en los extractores. En la práctica esa skill genérica no existe
en disco, así que la fase C7 —que era la prueba de que el perfil se puede portar
a otro repo sin cambios— no se pudo ejecutar. Está documentado como bloqueada,
no como superada.

---

## 17 · Mantenimiento de la skill

1. Cambiar algo obliga a bump en `CHANGELOG.md` (semver) y a una entrada en la fase correspondiente si afecta a una puerta.
2. Un validador nuevo se añade junto a los otros tres y genera su suite con `make_phase_suite.py`.
3. Un script que muta `cobertura.csv` o `units/` necesita su script inverso o una nota explícita de irreversibilidad: el ledger es la memoria y perderla cuesta rehacer la fase.
4. `SKILL.md` no crece: si una regla nueva no cabe, va a `references/` y `SKILL.md` la apunta.
5. Al final de cada fase, `STATE.md` se actualiza y el `CHANGELOG` recibe su versión.

---

## Relacionado con

- [`flow.md`](./flow.md) — el flujo paso a paso con sus diagramas y sus puntos de fallo.
- [`SKILL.md`](./SKILL.md) — el router que el agente lee al dispararse.
- [`AGENTS.md`](./AGENTS.md) — reglas de trabajo, patrones de AppFlowy y protocolo de subagentes.
- `PROMPT.md` — el encargo original y las 8 etapas.
- `CHANGELOG.md` — el detalle de cada fase, sus gates y sus resultados.
- `~/.agents/skills/notemartin-code-review/` — skill hermana: revisión de código en dos ejes con registro de deuda propia.