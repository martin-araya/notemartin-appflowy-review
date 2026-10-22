---
id: R-006
titulo: Plantilla de export/import (11 secciones)
fuente: PROMPT.md §6 (líneas 246–294)
archivos_cubiertos: [PROMPT.md]
estado: verificado
---

# R-006 — Plantilla de export/import (11 secciones)

> Plantilla obligatoria para cada `OUT/10-motor-export-import/<formato>.md`. Validada por `validate_template.py` (A3.3). Una instancia por formato (Markdown, HTML, texto plano, JSON, CSV, raw database, ZIP/Notion, etc.). La matriz round-trip de `OUT/10-motor-export-import/13-matriz-round-trip.md` (B4.13) referencia estas instancias celda a celda.

## Bloque de la plantilla (copia 1:1 de `PROMPT.md §6`)

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

## Notas de uso

- **Frontmatter:** `id` con prefijo `B4.N` (no `F`); `estado` ∈ {`verificado`, `pendiente`}; `archivos_cubiertos` con las rutas del motor implicadas (encoders en `appflowy_editor`, parsers en `flowy-document`, `collab-importer`, etc.).
- **Sección 3 (Pipeline):** `flowchart LR` con nodos `Bloque → Intermedio → Serializador → Archivo final`. Si el pipeline tiene más de 6 saltos, partir en dos diagramas enlazados.
- **Sección 4 (Tabla bloque → salida):** la granularidad mínima es 1 fila por tipo de bloque del editor (`heading`, `paragraph`, `bulleted_list`, `numbered_list`, `todo_list`, `quote`, `callout`, `code_block`, `math_equation`, `image`, `video`, `file`, `table`, `simple_table`, `toggle`, `outline`, `page`, `sub_page`, `database`, `columns`).
- **Sección 5 (Pérdidas):** todo lo que se descarta debe etiquetarse `[VERIFICADO]` con `ruta:línea` al encoder que lo descarta. Si no se puede verificar, `[NO DETERMINADO]` y va a `22-preguntas-abiertas.md`.
- **Sección 9 (Round-trip):** enlaza con `OUT/10-motor-export-import/13-matriz-round-trip.md` y, si el formato es importable, con la instancia de import correspondiente (`08-import-markdown.md`, `09-import-csv.md`).
- **Sección 11 (Ejemplos):** fragmentos ≤ 25 líneas, con `ruta:línea` al input real. Captura visual (PNG) cuando el output no es texto plano.

## Conteo de secciones (validación)

`validate_template.py` (A3.3) verificará que el documento final tiene `## 1.` … `## 11.` exactos, en orden, sin huecos.

## Diferencias con la plantilla de feature (R-005)

| Aspecto | R-005 (feature) | R-006 (export/import) |
|---|---|---|
| Nº de secciones | 19 (1–19 + opcional 20) | 11 (1–11) |
| Prefijo de `id` | `Fxx.y` | `B4.N` |
| Diagramas obligatorios | flujo + secuencia + estado | solo flujo (`flowchart LR` de pipeline) |
| Sección de round-trip | no | sí (§9) |
| Sección de pérdidas | no (sustituida por §13 riesgos) | sí (§5) |

## Relacionado con

- `R-003 evidence-rules.md` — cómo etiquetar afirmaciones y bloques.
- `R-004 diagram-conventions.md` — cómo escribir el `flowchart LR` de §3.
- `R-005 feature-template.md` — plantilla análoga para features.
- `PROMPT.md §3` — el árbol `OUT/10-motor-export-import/` y la lista de formatos.
