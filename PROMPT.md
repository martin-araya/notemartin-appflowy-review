# PROMPT — `notemartin-appflowy-review`

> **Documento derivado de `AGENTS.md` + `ROADMAP.md`.** Reconstruido en la fase A0.0 para desbloquear A0.2–A0.4 y A4.1. Si entra en conflicto con los originales, prevalece el original; este fichero debe consolidarse con `AGENTS.md`/`ROADMAP.md` en una fase posterior y toda contradicción detectada durante la ejecución se anota en `OUT/22-preguntas-abiertas.md`.

Encargo detallado de la skill de ingeniería inversa de **AppFlowy**. `AGENTS.md` define el **cómo** se trabaja (reglas, evidencia, patrones, subagentes); este `PROMPT.md` define el **qué** se entrega: etapas 0–7, estructura de salida, mapa de features, plantillas y convenciones transversales.

---

## 1. Encargo

Producir, desde el código fuente, la documentación técnica más completa posible de AppFlowy en Markdown (español técnico): diagrama de flujo global, cada feature con sus diagramas (flujo, secuencia, estados, datos), todos los archivos involucrados, el motor completo (puente Flutter↔Rust, CRDT, persistencia, sync, búsqueda, IA) y el motor de exportación/importación formato por formato.

Salida canónica: `OUT/appflowy-review/`. Idioma: español técnico. Identificadores, rutas, comandos y código en su forma original.

---

## 2. Etapas 0–7

Las 8 etapas agrupan los bloques del `ROADMAP.md`. Cada fase dentro de una etapa termina cuando su **prueba** pasa; una fase puede descubrir trabajo nuevo y dar lugar a fases `N.x` adicionales. No hay estimaciones de tiempo.

| # | Etapa | Bloque ROADMAP | Rango de fases | Qué entrega | Puerta / validación |
|---|---|---|---|---|---|
| 0 | **Esqueleto de la skill** | Bloque A0 | A0.1 → A0.4 | `SKILL/` con `SKILL.md`, `AGENTS.md`, `references/`, `scripts/`, `templates/output-skeleton/`. | `tree SKILL` coincide con `AGENTS.md §2`; el esqueleto de salida produce exactamente la estructura de §3. |
| 1 | **Adquisición e inventario** | Bloque A1 | A1.1 → A1.3 | `SRC/{appflowy,collab,editor}` clonados en los rev correctos; `OUT/_ledger/{inventario.json,assets.json,sources.json,cobertura.csv}`. | `sources.json` con 3 entradas (hash 7+); conteo `.rs`+`.dart` = `find`; ningún archivo con `capa: null`. |
| 2 | **Extractores deterministas** | Bloque A2 | A2.1 → A2.7 | `OUT/_ledger/extract/{events,protobuf,notifications,blocs,deps,misc}.json` + Mermaid crudo de dependencias. | Cada `input`/`output` de eventos existe como entidad protobuf; BLoCs esperados presentes; codegen produce `.proto` o `codegen-fallido.md`. |
| 3 | **Validadores** | Bloque A3 | A3.1 → A3.5 | `SKILL/scripts/validate_{mermaid,evidence,template,coverage}.{sh,py}` y `build_index.py`. | Diagramas rotos, rutas inventadas, secciones obligatorias faltantes y cobertura incompleta fallan con archivo y línea exacta. |
| 4 | **Orquestación de subagentes** | Bloque A4 | A4.1 → A4.4 | `assign_ledger.py`, generador de unidades, prompts autor/revisor, `STATE.md` con reanudación. | ≥ 90% de archivos asignados automáticamente; la suma de archivos por unidad = archivos asignados; reanudación cross-herramienta. |
| 5 | **Piloto end-to-end** | Bloque A5 | A5.1 → A5.2 | Documento aprobado del piloto F08 (búsqueda) y `SKILL/CHANGELOG.md` con diffs de plantillas. | Validadores en verde; revisor aprueba; ≥ 1 flowchart, ≥ 2 sequence, ≥ 1 state. |
| 6 | **Ejecución del análisis** | Parte B | B0 → B6 | Documentos `OUT/01..22-*.md`, `OUT/09-features/Fxx/`, `OUT/10-motor-export-import/`, `OUT/06..08-*/` y catálogo en `OUT/11..16-*.md`. | Cada feature con plantilla completa + validadores en verde + revisor aprueba; ledger de la unidad en `verificado`. |
| 7 | **Verificación y cierre** | Parte C | C1 → C7 | `validate_*` global sin errores, 100% cobertura, índice final, paquete portable. | `validate_coverage` 100%; prueba de utilidad ≥ 95% de respuestas correctas; abrir 3 documentos al azar en Notion y Obsidian con Mermaid renderizado. |

Gates 🔒 explícitos: A1.1, A3, A5, B0.2, C1, C2. Ningún gate puede saltarse.

---

## 3. Estructura de salida `appflowy-review/`

Árbol canónico generado por `templates/output-skeleton/` y poblado durante la Parte B y C.

```
appflowy-review/
├── 00-INDEX.md                     # Árbol, estado, cobertura, commits (C5)
├── 01-resumen-ejecutivo.md         # B6.4 (último del bloque B)
├── 02-stack-y-dependencias.md      # B1.2
├── 03-estructura-del-repo.md       # B1.1
├── 04-arquitectura-global.md       # B1.3 (C4 + secuencias globales en anexo)
├── 05-arranque-y-ciclo-de-vida.md  # B1.4
├── 06-puente-flutter-rust/         # B1.5
│   ├── 00-indice.md
│   ├── 01-ffi.md
│   ├── 02-lib-dispatch.md
│   ├── 03-codegen.md
│   ├── 04-notificaciones.md
│   └── 05-ejemplo-traza-opendocument.md
├── 07-motor-colaborativo-crdt/     # B1.6
│   ├── 00-indice.md
│   ├── 01-modelo-collab.md
│   ├── 02-folder.md
│   ├── 03-documento.md
│   ├── 04-database.md
│   ├── 05-user-awareness.md
│   ├── 06-collab-plugins.md
│   └── 07-snapshots-conflict-resolution.md
├── 08-persistencia/                # B1.7
│   ├── 00-indice.md
│   ├── 01-sqlite-schema.md
│   ├── 02-kv.md
│   ├── 03-collab-db.md
│   ├── 04-file-cache.md
│   ├── 05-sqlite-vec.md
│   ├── 06-migraciones.md
│   └── 07-rutas-plataforma.md
├── 09-features/                    # Bloque B3
│   ├── F01-documentos-y-editor/
│   ├── F02-bases-de-datos/
│   ├── F03-folder-workspaces/
│   ├── F04-sidebar-...
│   ├── F05-usuario-auth/
│   ├── F06-sync-servidores/
│   ├── F07-almacenamiento-archivos/
│   ├── F08-busqueda-indexacion/
│   ├── F09-ia/
│   ├── F10-importacion-ui/
│   ├── F11-exportacion-ui/
│   ├── F12-compartir-publicar/
│   ├── F13-ajustes-apariencia/
│   ├── F14-internacionalizacion/
│   ├── F15-notificaciones-recordatorios/
│   ├── F16-mobile/
│   ├── F17-plataforma/
│   └── F2x-descubiertas/
├── 10-motor-export-import/         # Bloque B4
│   ├── 00-indice.md
│   ├── 01-markdown.md
│   ├── 02-html.md
│   ├── 03-texto-plano.md
│   ├── 04-json-documento.md
│   ├── 05-csv-database.md
│   ├── 06-raw-database.md
│   ├── 07-otros-formatos.md
│   ├── 08-import-markdown.md
│   ├── 09-import-csv.md
│   ├── 10-import-historial-afdb.md
│   ├── 11-import-zip-notion.md
│   ├── 12-publicacion-web.md
│   └── 13-matriz-round-trip.md
├── 11-catalogo-eventos-ffi.md      # B2.1
├── 12-catalogo-entidades-protobuf.md  # B2.2
├── 13-catalogo-blocs.md            # B2.3
├── 14-catalogo-notificaciones.md   # B2.4
├── 15-catalogo-errores.md          # B2.5
├── 16-catalogo-flags-rutas-atajos.md  # B2.6
├── 17-grafo-dependencias.md        # B1.2 (anexo)
├── 18-build-ci-distribucion.md     # B6.1
├── 19-testing.md                   # B6.2
├── 20-seguridad-y-privacidad.md    # B6.3
├── 21-glosario.md                  # B6.5
├── 22-preguntas-abiertas.md        # B6.5
├── _ledger/
│   ├── sources.json
│   ├── inventario.json
│   ├── assets.json
│   ├── cobertura.csv
│   ├── extract/
│   │   ├── events.json
│   │   ├── protobuf.json
│   │   ├── notifications.json
│   │   ├── blocs.json
│   │   ├── deps.json
│   │   └── misc.json
│   └── units/
└── STATE.md                        # A4.4 (reanudación)
```

---

## 4. Mapa inicial de features → archivos

Tabla consumida por `assign_ledger.py` (A4.1) para reparto automático. Las celdas son **patrones de ruta** en `SRC/appflowy` (prefijo `appflowy:`) o rutas literales de Rust (sin prefijo). Lo que no case queda como `sin_asignar` para triage en B0.2.

| Feature | Patrones de ruta (match por prefijo) |
|---|---|
| F01 — Documentos y editor | `appflowy:frontend/appflowy_flutter/lib/plugins/document/`, `appflowy:frontend/appflowy_flutter/lib/shared/markdown_to_document.dart`, `editor:lib/src/`, `collab:collab-document/` |
| F02 — Bases de datos | `appflowy:frontend/appflowy_flutter/lib/plugins/database/`, `frontend/rust-lib/flowy-database2/`, `collab:collab-database/` |
| F03 — Folder, workspaces, vistas | `appflowy:frontend/appflowy_flutter/lib/workspace/application/{home,view,view_info,view_title,workspace,menu,sidebar}`, `frontend/rust-lib/flowy-folder/`, `collab:collab-folder/` |
| F04 — Sidebar, favoritos, recientes, papelera, tabs, command palette | `appflowy:frontend/appflowy_flutter/lib/workspace/application/{favorite,recent,tabs,command_palette,action_navigation,edit_panel}`, `appflowy:frontend/appflowy_flutter/lib/plugins/trash/`, `appflowy:frontend/appflowy_flutter/lib/features/view_management/` |
| F05 — Usuario, auth, sesión | `appflowy:frontend/appflowy_flutter/lib/user/`, `frontend/rust-lib/flowy-user/`, `collab:collab-user/` |
| F06 — Sync y servidores | `frontend/rust-lib/flowy-server/`, `appflowy:frontend/appflowy_flutter/lib/core/network_monitor.dart`, `appflowy:frontend/appflowy_flutter/lib/plugins/document/application/doc_sync_state_listener.dart` |
| F07 — Almacenamiento de archivos | `frontend/rust-lib/flowy-storage/`, `appflowy:frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/{file,image,video,cover,link_preview,link_embed}/` |
| F08 — Búsqueda e indexación | `frontend/rust-lib/flowy-search/`, `frontend/rust-lib/flowy-core/src/indexing_data_runner.rs`, `frontend/rust-lib/flowy-core/src/full_indexed_data_provider.rs`, `frontend/rust-lib/flowy-core/src/indexed_data_consumer.rs`, `appflowy:frontend/appflowy_flutter/lib/workspace/application/command_palette/` |
| F09 — IA | `frontend/rust-lib/flowy-ai/`, `frontend/rust-lib/flowy-sqlite-vec/`, `appflowy:frontend/appflowy_flutter/lib/ai/`, `appflowy:frontend/appflowy_flutter/lib/plugins/ai_chat/`, `appflowy:frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/ai/` |
| F10 — Importación (UI) | `appflowy:frontend/appflowy_flutter/lib/workspace/presentation/home/import/`, `appflowy:frontend/appflowy_flutter/lib/plugins/database/application/import*` |
| F11 — Exportación (UI) | `appflowy:frontend/appflowy_flutter/lib/workspace/application/export/`, `appflowy:frontend/appflowy_flutter/lib/plugins/shared/share/export_tab.dart` |
| F12 — Compartir, publicar, niveles de acceso | `appflowy:frontend/appflowy_flutter/lib/plugins/shared/share/`, `appflowy:frontend/appflowy_flutter/lib/features/{page_access_level,share_tab,shared_section}/`, `frontend/rust-lib/flowy-folder/src/{share/import.rs,publish_util.rs}` |
| F13 — Ajustes, apariencia, temas, fuentes | `appflowy:frontend/appflowy_flutter/lib/workspace/application/settings/`, `appflowy:frontend/appflowy_flutter/lib/workspace/presentation/settings/widgets/`, `appflowy:frontend/appflowy_flutter/lib/features/settings/` |
| F14 — Internacionalización | `appflowy:project.inlang*`, `appflowy:frontend/appflowy_flutter/lib/shared/easy_localiation_service.dart`, `appflowy:frontend/appflowy_flutter/lib/startup/tasks/localization.dart`, `appflowy:frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/i18n/` |
| F15 — Notificaciones in-app y recordatorios | `appflowy:frontend/appflowy_flutter/lib/workspace/application/notification/`, `appflowy:frontend/appflowy_flutter/lib/workspace/presentation/notifications/`, `appflowy:frontend/appflowy_flutter/lib/core/notification/`, `frontend/rust-lib/flowy-notification/`, `frontend/rust-lib/flowy-document/src/reminder.rs`, `frontend/rust-lib/flowy-date/` |
| F16 — Mobile | `appflowy:frontend/appflowy_flutter/lib/mobile/`, `appflowy:frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/mobile_*/` |
| F17 — Plataforma (ventanas, deeplinks, auto-update, hotkeys, feature flags, errores, logging) | `appflowy:frontend/appflowy_flutter/lib/startup/tasks/{windows,deeplink,auto_update_task,hot_key,platform_error_catcher,memory_leak_detector,feature_flag_task}.dart`, `appflowy:frontend/appflowy_flutter/lib/shared/feature_flags.dart`, `appflowy:frontend/appflowy_flutter/lib/core/frameless_window.dart`, `frontend/rust-lib/lib-log/`, `frontend/rust-lib/flowy-core/src/log_filter.rs` |
| F2x — Descubiertas | triage manual de B0.2 (carpetas sin patrón asignado) |

Reglas de precedencia para `assign_ledger.py`: (1) match más largo gana; (2) F01 y F02 son los matchers más específicos; (3) F17 absorbe los `startup/tasks/*`; (4) F14 absorbe `easy_localiation_service.dart` y `localization.dart` antes que cualquier otra.

---

## 5. Plantilla de feature (19 secciones)

Plantilla obligatoria para cada `OUT/09-features/Fxx/<sub>-<nombre>.md` y para los sub-documentos del motor (`06-…`, `07-…`, `08-…`, `10-…`). Validada por `validate_template.py` (A3.3).

```markdown
---
id: F01.0
titulo: Índice de documentos y editor
fuente: appflowy, editor, collab
archivos_cubiertos: <lista de rutas del ledger>
estado: verificado | pendiente | sin_asignar
---

# F01.0 — Índice de documentos y editor

## 1. Resumen (3–6 líneas)
Qué es, para qué sirve, dónde encaja.

## 2. Alcance
Qué incluye este documento y qué queda fuera (enlaces a F01.1..F01.9).

## 3. Modelos de datos
Diagrama `classDiagram` o `erDiagram` con los tipos reales del código (con `ruta:línea`).

## 4. Eventos FFI
Tabla `evento, input PB, output PB, handler, archivo:línea` extraída de `events.json`.

## 5. Notificaciones
Tabla `notificación, emisor, listener Dart, efecto UI, archivo:línea`.

## 6. BLoCs / Cubits
Tabla `clase, eventos, estados, servicios, archivo:línea`.

## 7. Servicios e inyección de dependencias
Dart (`get_it`) y Rust (`flowy-core/deps_resolve`).

## 8. Persistencia
Tablas SQLite, KV, archivo de collab en disco.

## 9. Diagramas de flujo
`flowchart TD` con subgraphs por capa (UI, BLoC, Servicio, FFI, Rust, Collab, Persistencia, Cloud).

## 10. Diagramas de secuencia
`sequenceDiagram` con participantes = clase real.

## 11. Diagramas de estado
`stateDiagram-v2` para ciclos de vida relevantes.

## 12. Archivos cubiertos (del ledger)
Lista tabular copiada de `_ledger/cobertura.csv` filtrada por esta unidad.

## 13. Riesgos y casos límite
Bullets con qué puede fallar y cómo se mitiga.

## 14. Evidencias y etiquetas
Resumen de cuántas afirmaciones `[VERIFICADO]`, `[INFERIDO]`, `[NO DETERMINADO]`.

## 15. Pruebas
Tests unitarios, de BLoC, widget e integration que cubren esta feature.

## 16. Métricas
LOC, nº de eventos, nº de BLoCs, nº de archivos, etc.

## 17. Pendientes
Tareas que se descubrieron durante la documentación.

## 18. Preguntas abiertas
Lo marcado como `[NO DETERMINADO]` que va a `22-preguntas-abiertas.md`.

## 19. Relacionado con
Enlaces cruzados `[[F01.1]]`, `[[B1.5]]`, `[[F02]]`, etc.

## 20. Notas
Pie de página libre (opcional, ≤ 10 líneas).
```

Nota: la plantilla tiene 19 secciones numeradas (1–19) más el frontmatter y una sección 20 opcional, lo que da el conteo de "19 secciones" que la prueba de A0.3 valida.

---

## 6. Plantilla de export/import (11 secciones)

Plantilla para cada `OUT/10-motor-export-import/<formato>.md`. Validada por `validate_template.py`.

```markdown
---
id: B4.1
titulo: Export Markdown
fuente: appflowy, editor
archivos_cubiertos: <rutas>
estado: verificado | pendiente
---

# B4.1 — Export Markdown

## 1. Punto de entrada (UI)
Quién dispara el export, dónde está el botón, con qué precondiciones.

## 2. Lado de conversión
Dart (`appflowy_editor/plugins/markdown/`) o Rust (`flowy-document/src/parser/`).

## 3. Pipeline
Diagrama `flowchart LR` paso a paso: bloque del documento → serializador intermedio → formato final.

## 4. Tabla bloque → salida
Por cada bloque del editor (heading, list, todo_list, callout, code_block, math_equation, table, …): cómo se traduce a Markdown.

## 5. Pérdidas
Información que se descarta en este formato (estilos no soportados, atributos, metadatos).

## 6. Assets
Imágenes, archivos incrustados: cómo se referencian y dónde se guardan.

## 7. Encoding y nombre de archivo
UTF-8, BOM, nombre generado (slug, timestamp, colisión).

## 8. Errores
Casos de fallo y notificación al usuario (ErrorCode → mensaje).

## 9. Round-trip
¿`import` recupera el mismo documento? Tabla de equivalencias.

## 10. Extensión y firma
`.md`, MIME type, magic bytes.

## 11. Ejemplos
Antes/después con un documento real, captura o fragmento ≤ 25 líneas.
```

---

## 7. Convenciones transversales

- **Idioma**: español técnico. Identificadores, rutas, comandos y código en su forma original.
- **Párrafos**: completos (qué, cómo, por qué, dónde). Nada de bullets vacíos.
- **Apertura y cierre**: cada documento abre con 3–6 líneas de resumen y cierra con "Relacionado con".
- **Evidencia** (`AGENTS.md §6`): toda afirmación lleva `ruta:línea` o `ruta:inicio–fin`; ruta relativa a la raíz de su repo, con prefijo de fuente si no es el principal (`collab:collab-document/src/document.rs:120`, `editor:lib/src/plugins/html/html_document_encoder.dart:40`).
- **Etiquetas**: `[VERIFICADO]` (por defecto, con evidencia), `[INFERIDO]` (razonamiento explícito), `[NO DETERMINADO]` (va a `22-preguntas-abiertas.md`).
- **Fragmentos de código**: ≤ 25 líneas, siempre con referencia.
- **Inventario**: nunca citar un archivo que no esté en `_ledger/inventario.json`.
- **Mermaid** (`AGENTS.md §7`): IDs de nodo sin espacios; etiquetas con literales entre comillas si llevan símbolos; ≤ ~60 nodos por diagrama; cada diagrama con frase introductoria + lectura en prosa; validado por `validate_mermaid.sh`.
- **Pruebas de carga**: al disparar, la skill se carga en Hermes, Cline y Kilo Code con `"revisa AppFlowy completo"` y responde un plan que arranca por la Etapa 0.

---

## 8. Glosario mínimo

(Tomado de `AGENTS.md §12`.)

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

---

## 9. Lo que NO se hace

(Tomado de `AGENTS.md §11`.)

- No documentar AppFlowy-Cloud por dentro (solo su contrato cliente desde `flowy-server/src/af_cloud`).
- No ejecutar la app ni hacer cambios al repo analizado (lectura y build de codegen permitidos en un directorio aparte).
- No reducir alcance por tamaño: la extensión no es un criterio.
- No reemplazar análisis por lectura de README o docs oficiales; esos solo sirven como pista y se contrastan con código.

---

## 10. Cierre

El estado de cada fase del `ROADMAP.md` se refleja en `OUT/STATE.md` (A4.4). La reanudación cross-herramienta (Hermes ↔ Cline ↔ Kilo Code) funciona leyendo ese fichero más el `_ledger/cobertura.csv`. Cualquier desviación detectada entre este `PROMPT.md` y los originales se anota en `OUT/22-preguntas-abiertas.md` para una fase de consolidación posterior.
