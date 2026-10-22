---
id: R-005
titulo: Plantilla de feature (19 secciones)
fuente: PROMPT.md §5 (líneas 166–244)
archivos_cubiertos: [PROMPT.md]
estado: verificado
---

# R-005 — Plantilla de feature (19 secciones)

> Plantilla obligatoria para cada `OUT/09-features/Fxx/<sub>-<nombre>.md` y para los sub-documentos del motor (`OUT/06-…`, `OUT/07-…`, `OUT/08-…`, `OUT/10-…`). Validada por `validate_template.py` (A3.3). **Toda unidad de trabajo abre una copia de esta plantilla y rellena sus 19 secciones en orden**; las secciones 17 y 18 alimentan `OUT/22-preguntas-abiertas.md`.

## Bloque de la plantilla (copia 1:1 de `PROMPT.md §5`)

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

## Notas de uso

- **Frontmatter (líneas 1–7):** los 5 campos (`id, titulo, fuente, archivos_cubiertos, estado`) son obligatorios para `validate_template.py` (A3.3). `archivos_cubiertos` se rellena con la lista de rutas del ledger asignadas a la unidad.
- **Secciones 9–11:** al menos un diagrama de flujo por feature; al menos un diagrama de secuencia para interacciones con FFI/Rust/collab; el de estado solo si la feature tiene ciclo de vida no trivial.
- **Sección 12:** se construye automáticamente con `assign_ledger.py` (A4.1); el autor solo verifica que la lista coincide con su unidad.
- **Sección 18:** cada entrada se copia literalmente en `OUT/22-preguntas-abiertas.md` al cerrar la unidad; el orquestador lo hace, no el autor.
- **Sección 20:** opcional. Usar para notas contextuales que no encajan en otra sección. Máximo 10 líneas para no inflar el documento.

## Conteo de secciones (validación)

`validate_template.py` (A3.3) verificará que el documento final tiene `## 1.` … `## 19.` y, si la sección 20 está presente, que también está bien formada. La numeración debe ser **exactamente** 1–19 (o 1–20 si se incluye la opcional).

## Relacionado con

- `R-003 evidence-rules.md` — cómo etiquetar afirmaciones dentro de cada sección.
- `R-004 diagram-conventions.md` — cómo escribir los diagramas de §9–§11.
- `R-006 export-template.md` — plantilla análoga para el motor de export/import.
- `PROMPT.md §4` — mapa inicial de features → archivos (de dónde salen los `archivos_cubiertos`).
