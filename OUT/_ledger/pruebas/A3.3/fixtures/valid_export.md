---
id: B4.0
titulo: Fixture válido (export)
fuente: appflowy, editor
archivos_cubiertos: [export-template.md]
estado: pendiente
---

# B4.0 — Fixture válido (export)

Documento de prueba con las 11 secciones obligatorias de la plantilla export, en orden, con contenido real.

## 1. Punto de entrada (UI)
Botón "Exportar" en el menú contextual de la vista, con precondición de usuario autenticado.

## 2. Lado de conversión
Dart (`appflowy_editor/plugins/markdown/`) o Rust (`flowy-document/src/parser/`).

## 3. Pipeline
```mermaid
flowchart LR
  Bloque --> Intermedio --> Serializador --> Archivo
```

## 4. Tabla bloque → salida
Por cada bloque del editor (heading, list, todo_list, callout, code_block): cómo se traduce.

## 5. Pérdidas
Información que se descarta en este formato (estilos no soportados, atributos).

## 6. Assets
Imágenes y archivos incrustados: cómo se referencian y dónde se guardan.

## 7. Encoding y nombre de archivo
UTF-8 sin BOM, nombre generado con slug + timestamp.

## 8. Errores
Casos de fallo y notificación al usuario (ErrorCode → mensaje).

## 9. Round-trip
Tabla de equivalencias con la importación del mismo formato.

## 10. Extensión y firma
`.md`, MIME `text/markdown`, magic bytes `0xEF 0xBB 0xBF` (BOM opcional).

## 11. Ejemplos
Antes/después con un documento real, captura o fragmento de ≤ 25 líneas.
