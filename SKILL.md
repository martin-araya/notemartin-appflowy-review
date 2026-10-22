---
name: notemartin-appflowy-review
description: Ingeniería inversa completa y exhaustiva del código fuente de AppFlowy (Flutter + Rust + CRDT sobre yrs). Úsala cuando el usuario pida "revisa AppFlowy completo", "documenta AppFlowy", "auditoría técnica de AppFlowy", "análisis técnico de AppFlowy", "mapea AppFlowy", "ingeniería inversa de AppFlowy", "informe técnico de AppFlowy", o entregue el repo de AppFlowy (o su monorepo) y pida un informe exhaustivo en español sobre arquitectura, features, motor colaborativo, persistencia, búsqueda, IA, exportación e importación. Produce OUT/appflowy-review/ con diagramas Mermaid, evidencia ruta:línea y cobertura por ledger. No dispara para: resúmenes cortos, preguntas puntuales sueltas,改修 de código, explicar una API concreta sin intención de análisis exhaustivo, o tareas que no sean AppFlowy.
---

# `notemartin-appflowy-review` — SKILL.md

> Router de la skill. Lo único que el agente lee cuando la skill se dispara. Solo enruta; cero plantillas embebidas, cero detalle de fases, cero gramática Mermaid. Toda regla de detalle vive en `SKILL/AGENTS.md`, `PROMPT.md` y `SKILL/references/`. Límite duro: **≤ 500 líneas**.

## §1 · Cuándo se dispara

Dispara cuando el usuario entrega el código de AppFlowy (o su monorepo `AppFlowy-IO/AppFlowy` más dependencias) y pide —o implica— producir **documentación técnica exhaustiva y trazable** en español sobre su arquitectura, motor, features y estado del proyecto.

| Dispara | No dispara |
|---|---|
| "revisa AppFlowy completo", "documenta AppFlowy", "audita AppFlowy" | Resúmenes de un párrafo o de una sola feature |
| "ingeniería inversa de AppFlowy", "mapa de AppFlowy", "informe técnico" | Responder una duda puntual de uso de la app |
| "analiza el código de AppFlowy", "auditoría técnica exhaustiva" | Hacer cambios al repo o ejecutar la app |
| "produce documentación por feature" | Documentar AppFlowy-Cloud por dentro (fuera de alcance) |
| Pega URL/ruta del repo de AppFlowy y pide documentación | Tareas que no tengan AppFlowy como objeto |

## §2 · Invariantes y reglas bloqueantes

Subconjunto de `AGENTS.md §2, §6, §10, §11` que aplica a toda invocación. El detalle completo vive en `SKILL/AGENTS.md`.

| # | Regla | Si se omite |
|---|---|---|
| R1 | Toda afirmación lleva `ruta:línea` o `ruta:inicio–fin` (`AGENTS.md §6`). | El revisor rechaza el documento entero. |
| R2 | Etiquetas `[VERIFICADO]` / `[INFERIDO]` / `[NO DETERMINADO]`. `[NO DETERMINADO]` va a `OUT/22-preguntas-abiertas.md`. | Sin trazabilidad ni separación de incertidumbres. |
| R3 | Prohibido inventar clases, eventos, archivos, campos. Si dudas, `rg` antes. | Documentación plausible pero falsa. |
| R4 | Fragmentos de código ≤ 25 líneas, siempre con referencia. | Citas que no caben en el contexto del revisor. |
| R5 | Nunca citar archivos fuera de `_ledger/inventario.json`. | Cobertura imposible de verificar. |
| R6 | Mermaid: IDs sin espacios, etiquetas literales, ≤ ~60 nodos por diagrama, validado por `validate_mermaid.sh` (`AGENTS.md §7`). | Diagramas rotos o ilegibles. |
| R7 | Español técnico; identificadores, rutas y código en original; párrafos completos; cada doc abre con 3–6 líneas y cierra con "Relacionado con" (`AGENTS.md §10`). | Estilo inconsistente. |
| R8 | Gates 🔒 no se saltan: A1.1, A3, A5, B0.2, C1, C2. | Fases downstream construidas sobre cimientos sin verificar. |
| R9 | `SKILL.md` ≤ 500 líneas y solo enruta. | Contexto saturado en cada disparo. |

## §3 · Las 8 etapas (resumen)

El detalle de cada fase vive en `ROADMAP.md`. Este router solo nombra cada etapa y su puerta.

| # | Etapa | Bloque ROADMAP | Qué entrega | Puerta |
|---|---|---|---|---|
| 0 | Esqueleto de la skill | A0 | `SKILL/` con `SKILL.md`, `AGENTS.md`, `references/`, `scripts/`, `templates/output-skeleton/` | árbol coincide con `AGENTS.md §2` |
| 1 | Adquisición e inventario | A1 | clones en `SRC/{appflowy,collab,editor}` + `_ledger/{inventario,sources,assets,cobertura}` | `sources.json` con 3 entradas (hash 7+); `inventario.json` con conteos `find` coincidentes y `capa` siempre presente; `cobertura.csv` con 4.603 filas y todas en `sin_asignar` |
| 2 | Extractores deterministas | A2 | `_ledger/extract/{events,protobuf,notifications,blocs,deps,misc}.json` | cada `input`/`output` existe como PB |
| 3 | Validadores | A3 | `validate_{mermaid,evidence,template,coverage}.{sh,py}` + `build_index.py` | 🔒 toda ruta:línea y todo bloque Mermaid verificado |
| 4 | Orquestación de subagentes | A4 | `assign_ledger.py`, prompts autor/revisor, `STATE.md` | ≥ 90% asignado automáticamente; reanuda cross-herramienta |
| 5 | Piloto end-to-end | A5 | F08 (búsqueda) aprobada + `SKILL/CHANGELOG.md` | 🔒 revisor aprueba con 100% de archivos cubiertos |
| 6 | Ejecución del análisis | B | `OUT/01..22-*.md`, `09-features/Fxx/`, `10-motor-export-import/`, `06..08-*/` | cada feature pasa plantilla + validadores + revisor |
| 7 | Verificación y cierre | C | cobertura 100%, `00-INDEX.md`, paquete portable | 🔒 C1, C2 verdes; prueba de utilidad ≥ 95% |

## §4 · Reglas de orquestación

(Resumen de `AGENTS.md §8`. Detalle y contrato completo en `references/subagent-autor-prompt.md` y `references/subagent-revisor-prompt.md` cuando se creen en A4.3.)

- **Orquestador** = este agente. Ejecuta scripts, mantiene el ledger, divide en unidades, asigna, integra, dispara verificación. No escribe documentos de feature.
- **Unidad de trabajo** = `{id, título, archivos[] del ledger, catálogos relevantes, plantilla, documentos dependientes}`. Si la unidad supera ~120 archivos se divide (ej. F01 → un documento por grupo de bloques).
- **Subagente autor**: lee todos sus archivos, escribe el documento con la plantilla, devuelve `{documento, filas_ledger_cubiertas, archivos_extra_detectados, preguntas_abiertas}`.
- **Subagente revisor**: distinto del autor, contexto limpio. Corre `validate_evidence`, `validate_template`, `validate_mermaid` y verifica semánticamente ≥ 30% de afirmaciones (100% en F01, F02, F06 y motor export/import). Devuelve `aprobado | rechazado + correcciones`.
- **Concurrencia**: configurable por plataforma (`MAX_PARALLEL`). Catálogos y arquitectura global van primero porque alimentan a las features.

## §5 · Reanudar desde `STATE.md`

Pasos numerados para retomar la skill en cualquier sesión o herramienta (Hermes ↔ Cline ↔ Kilo Code):

1. Leer `OUT/STATE.md` y localizar la última fase con `estado: completada`.
2. Cargar `OUT/_ledger/cobertura.csv` para ver qué archivos están en `verificado`, `pendiente` o `sin_asignar`.
3. Cargar las salidas del extractor correspondiente a la fase actual (`_ledger/extract/*.json`).
4. Saltar a la siguiente fase del `ROADMAP.md` cuya puerta esté en verde.
5. Al cerrar la fase, actualizar `OUT/STATE.md` con `{fase, estado, fecha, notas}` antes de devolver el control.
6. Si la fase tiene gate 🔒, no avanzar hasta que el validador correspondiente devuelva 0 errores.

`STATE.md` se actualiza al cerrar **cada** fase (A4.4). Sin `STATE.md` actualizado, la reanudación es inválida.

## §6 · Gates (puertas bloqueantes)

Lista de gates 🔒 del `ROADMAP.md`. Cada uno se valida con un script de `SKILL/scripts/`.

| Gate | Fase | Script | Estado |
|---|---|---|---|
| A1.1 | fuentes correctas en `SRC/` | `OUT/_ledger/validate-A1.1.sh` (lee `OUT/_ledger/sources.json`) | ✅ verificado 2026-10-18 (appflowy `5cf3a36`, collab `4dfccef`, editor `470c4e7`) |
| A3 | validadores listos | smoke test de los 4 scripts sobre fixtures | pendiente |
| A5 | piloto F08 aprobado | revisor + validadores en verde | pendiente |
| B0.2 | 0 archivos `sin_asignar` | `validate_coverage` post-triage | pendiente |
| C1 | pasada global sin errores | `validate_*` sobre todo `OUT/` | pendiente |
| C2 | 100% cobertura | `validate_coverage.py` | pendiente |

> A1.2 complementa A1.1 con el inventario detallado (`inventario.json` 4.603 archivos, `assets.json` 1.186 binarios); no es gate formal pero es prerrequisito de A1.3 (`cobertura.csv`) y de A4.1 (`assign_ledger.py`). Su validador es `OUT/_ledger/validate-A1.2.sh` y se ejecutó OK el 2026-10-18.
> A1.3 cierra el Bloque A1 inicializando `cobertura.csv` (4.603 filas, 7 columnas, todas `estado=sin_asignar`); validador `OUT/_ledger/validate-A1.3.sh` OK el 2026-10-18. A4.1 (`assign_ledger.py`) mutará este CSV rellenando `feature_ids`.

## §7 · Mapa del repositorio de la skill

```
notemartin-appflowy-review/
├── SKILL.md                        # este fichero (router, ≤ 500 líneas)
├── AGENTS.md                       # reglas, patrones, subagentes
├── references/                     # detalle por tema (A0.3)
│   ├── repo-map.md
│   ├── patterns.md
│   ├── evidence-rules.md
│   ├── diagram-conventions.md
│   ├── feature-template.md
│   ├── export-template.md
│   ├── subagent-autor-prompt.md    # A4.3
│   └── subagent-revisor-prompt.md  # A4.3
├── scripts/                        # extractores y validadores (A2, A3)
│   ├── fetch_sources.sh
│   ├── inventory.py
│   ├── extract_events.py
│   ├── extract_protobuf.py
│   ├── extract_notifications.py
│   ├── extract_blocs.py
│   ├── extract_deps.py
│   ├── extract_misc.py
│   ├── assign_ledger.py
│   ├── validate_mermaid.sh
│   ├── validate_evidence.py
│   ├── validate_template.py
│   ├── validate_coverage.py
│   └── build_index.py
├── templates/
│   └── output-skeleton/            # árbol vacío de appflowy-review/
└── CHANGELOG.md                    # diffs de la skill entre versiones
```

En la raíz del proyecto (fuera de `SKILL/`) viven los documentos no portables: `PROMPT.md` (encargo + 8 etapas + plantillas + mapa inicial), `ROADMAP.md` (fases granulares con prueba) y `OUT/` (salida de la ejecución).

## §8 · Punteros a `references/`

Tabla de documentos de referencia. **No enlazar** hasta que la fase indicada los haya creado; mientras tanto, el campo `estado` es `pendiente` y el agente los lee directamente desde `PROMPT.md` o `AGENTS.md`.

| Referencia | Cubre | Fase que la crea | Estado actual |
|---|---|---|---|
| `repo-map.md` | árbol de carpetas de AppFlowy con propósito | A0.3 | ✅ disponible |
| `patterns.md` | 7 patrones de arquitectura (`AGENTS.md §5`) ampliados con ejemplos | A0.3 | ✅ disponible |
| `evidence-rules.md` | reglas de evidencia `ruta:línea` y etiquetas | A0.3 | ✅ disponible |
| `diagram-conventions.md` | Mermaid: tipos, IDs, etiquetas, fragmentación | A0.3 | ✅ disponible |
| `feature-template.md` | plantilla de 19 secciones para `09-features/` | A0.3 | ✅ disponible (también en `PROMPT.md §5`) |
| `export-template.md` | plantilla de 11 secciones para `10-motor-export-import/` | A0.3 | ✅ disponible (también en `PROMPT.md §6`) |
| `subagent-autor-prompt.md` | prompt y contrato del subagente autor | A4.3 | pendiente |
| `subagent-revisor-prompt.md` | prompt y contrato del subagente revisor | A4.3 | pendiente |

## §9 · Prompt de prueba canónico

Bloque copy-paste para validar que la skill se dispara en el agente receptor:

```
Revisa AppFlowy completo. Quiero OUT/appflowy-review/ con la
arquitectura global, todas las features documentadas con diagramas
Mermaid, el motor colaborativo, la persistencia, la búsqueda, la IA
y el motor de exportación/importación. Idioma español, evidencia
ruta:línea, cobertura verificable por ledger.
```

Variantes que también deben disparar la skill (cubiertas en el `description` del frontmatter): `"documenta AppFlowy"`, `"auditoría técnica de AppFlowy"`, `"mapea AppFlowy"`, `"ingeniería inversa de AppFlowy"`, `"informe técnico de AppFlowy"`, `"analiza el código de AppFlowy"`.

## §10 · Glosario mínimo

(Tomado de `AGENTS.md §12`. El glosario completo con ejemplos se publica en `OUT/21-glosario.md` al final del bloque B.)

| Término | Significado |
|---|---|
| Collab | Objeto colaborativo de AppFlowy-Collab sobre un doc `yrs` |
| View | Nodo del árbol del folder (documento, grid, board, calendar, chat…) |
| Space | Agrupación de vistas en el sidebar |
| AFPlugin | Módulo registrado en `lib-dispatch` con sus eventos |
| PB | Sufijo de entidades protobuf (`ViewPB`, `DocumentDataPB`) |
| Awareness | Presencia/cursores de colaboradores en tiempo real |
| Snapshot | Estado serializado de un collab para historial/recuperación |
| Publish | Publicación web de una vista |

## §11 · Documentos primarios del proyecto (no son parte de la skill portable)

Estos viven en la raíz del proyecto y la skill los lee en cada invocación:

- `PROMPT.md` — encargo, 8 etapas, estructura de salida, plantillas, mapa de features, glosario, lo que no se hace.
- `ROADMAP.md` — fases granulares con su prueba, gates 🔒 y símbolos 🔀.
- `OUT/STATE.md` — estado actual de cada fase para reanudar.
- `OUT/_ledger/` — inventario, cobertura, extractos y unidades.
