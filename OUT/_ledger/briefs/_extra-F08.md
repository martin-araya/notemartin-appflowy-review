## Foco de esta unidad — COMPLETAR el piloto A5.1

Este documento **ya existe** y cubre 21 de los 32 archivos (la parte Rust:
`flowy-search/**` + los tres ficheros de indexación de `flowy-core`). Tu trabajo
es **ampliarlo**, no reescribirlo.

Faltan **11 archivos Dart** del command palette, asignados a F08 por el triage
de B0.2 (antes vivían en `sin_asignar`):

```
workspace/presentation/command_palette/command_palette.dart
workspace/presentation/command_palette/navigation_bloc_extension.dart
workspace/presentation/command_palette/widgets/page_preview.dart
workspace/presentation/command_palette/widgets/recent_views_list.dart
workspace/presentation/command_palette/widgets/search_ask_ai_entrance.dart
workspace/presentation/command_palette/widgets/search_field.dart
workspace/presentation/command_palette/widgets/search_icon.dart
workspace/presentation/command_palette/widgets/search_recent_view_cell.dart
workspace/presentation/command_palette/widgets/search_result_cell.dart
workspace/presentation/command_palette/widgets/search_results_list.dart
workspace/presentation/command_palette/widgets/search_summary_cell.dart
```

Qué debes hacer, en este orden:

1. **Lee el documento completo** y su frontmatter. Respeta su estilo, su prosa y
   las secciones que ya tiene: no las borres ni las reescribas desde cero.
2. **Añade el frontmatter `archivos_cubiertos`** con los 11 ficheros nuevos, para
   que la lista pase a los 32. `estado:` debe quedar en `verificado`.
3. **Incorpora la capa UI** en las secciones que correspondan, sin romper el
   orden de las 19 secciones:
   - §3 (modelo de datos) o §6 (BLoCs): cómo entra una consulta de búsqueda
     desde el command palette y cómo vuelve a la lista de resultados.
   - §9/§10: **un `sequenceDiagram` nuevo** de una búsqueda completa: usuario
     escribe → `SearchField` → `search` → FFI (`SearchDocument`/`SearchLatest`
     o los eventos reales que verifiques) → `SearchManager` (tantivy) →
     `SearchResponse` → `SearchResultsList` + `SearchResultCell`.
   - §10 o §11: máquina de estados o diagrama de flujo de la UI del palette
     (debounce, foco, navegación con teclado, vista de recientes vs resultados).
   - §12: añade las 11 filas nuevas a la tabla de archivos cubiertos.
   - §13/§2: **corrección de scope**: el piloto A5.1 declaró el command palette
     como "referenciado sin reclamar sus archivos"; el triage de B0.2 lo
     asignó a F08. Consigna esa decisión.
4. Actualiza §14 (recuento de etiquetas) y §18 si añades `[NO DETERMINADO]`.
5. En §19 añade los cruces nuevos que correspondan (`[[F04]]` por la navegación,
   `[[F09.3]]` por `search_ask_ai_entrance.dart`, `[[F03.1]]` por los widgets de
   vistas/recientes).

Pruebas literales: los 11 widgets con su fichero y su línea; el flujo completo de
búsqueda; la tabla de los 32 archivos.