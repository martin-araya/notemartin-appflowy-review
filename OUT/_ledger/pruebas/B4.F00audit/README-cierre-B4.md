# Cierre del Bloque B4 · Motor de exportación, importación y publicación

Ejecutado el 2026-10-21 siguiendo `~/.local/share/kilo/plans/1792533640542-b4-motor-export-import.md`.

## Ola 0 · Deuda C5 cerrada antes de B4

| Qué | Antes | Después |
|---|---:|---:|
| Enlaces no resueltos en `build_index.py --check-links` | 131 | **44** |
| Erratas de id en docs aprobados | 42 | **0** |
| Tokens de ejemplo (`[[X]]`, `[[bin]]`, `[[AGENTS]]`…) | 11 | **0** |
| No resueltos que **no** son fases futuras | 53 | **0** |

Los 50 restantes son **exclusivamente B6.1/B6.2/B6.3** (transversales aún no escritas). En particular, los 36 `[[B4.*]]` del plan se resolvieron solos al materializarse las 14 unidades.

39 correcciones aplicadas sobre 25 documentos, cada una mapeada al id válido más cercano o reescrita a prosa:

| Patrón | Ejemplos | Política |
|---|---|---|
| Id con un nivel de menos | `F01.0.3`→`F01.0.3.3`, `F02.9.4`→`F02.9.1`+`F02.9.2`, `F00.8`→`F00.7.8`, `F00.7.13`→`F00.7.7`, `F02.0.3`→`F02.0.1.3`, `F01.0.5.7`→`F00.5.7`, `F01.7.5`→`F01.4` | mapear al id real |
| Id inexistente con equivalente | `B18.1`→`B6.1`, `F12.3`→`F12.2`, `F13.0`→`F13.1`, `F12.0`→`F12.1`, `F21.icon-emoji-picker`→`F21`, `F04.sidebar`→`F04`, `F09.ia`→`F09.3`, `F08.A`→`B1.7`, `F19.2`→`F19.2.1`–`F19.2.10`, `F02.0`→`F02`, `B1`→`B2.1`+`B2.2`, `F02.6..F02.12`→`F02.6` a `F02.12` | mapear o reescribir el rango como prosa |
| Feature futura inexistente | `F22`, `F13.4`, `F13.5`, `F02.9.7`, `F02.X.1` | reescribir a prosa (son huecos de test, no enlaces) |
| Sintaxis TOML malinterpretada como enlace | `[[bin]]`, `[[test]]` (Cargo), `[[06]]`, `[[08]]`, `[[AGENTS]]`, `[[14-notificaciones]]` | reescribir a `[bin]`, `[test]`, `06-puente-flutter-rust/`… |
| Tokens de ejemplo en prosa que explica el propio validador | `[[X]]`, `[[NOEXISTE]]`, `[[F..]]` (en `STATE.md`, `22-preguntas-abiertas.md`, fixtures de A3.5/A4.4) | `<X>`, `<NOEXISTE>`, `<F..>` |

Las 4 referencias que quedaron en `PROMPT.md`-land se corrigieron también: `B4.6` que `F02.13` atribuía a `F12.1` (publish vive en `F12.2`/`B4.12`).

## Olas 1–5 · 14 documentos, 6 900 líneas

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

Las 14 suites están en `OUT/_ledger/pruebas/B4.<N>/` con `revisor_output.json` en `veredicto=aprobado, correcciones=0`. La prueba del bloque (`B4.13`) pasa: **matriz de 29 bloques × 9 formatos + submatriz de 15 `FieldType` × 4 variantes de CSV, sin una sola celda vacía**.

## Adaptaciones a la skill (4, todas reversibles)

1. **`close_unit.sh` — dispatch de plantilla y fase por prefijo de unidad.** `B4.*` → plantilla `export` (11 secciones) y `PHASE=$UNIT`; `B1.*` → `structure`; el resto → `feature` y `PHASE=B3.$UNIT` como antes. Antes estaba fijado a `feature`/`B3.` y no habría podido validar ningún doc de B4.
2. **`close_unit.sh` — las unidades `B*` no tocan `cobertura.csv`.** Sus archivos ya pertenecen a una feature F* y están verificados; el ledger se queda en 100 % global.
3. **`make_phase_suite.py` — `--transversal` y `--template`.** Para unidades transversales el quinto check no es "N filas marcadas por `record_unit_state.py`" (que sería 0) sino **"el frontmatter declara exactamente N rutas y todas existen en `SRC/`"**, que es la garantía real que aporta un doc transversal. El parser acepta las tres formas de escribir la fuente: `appflowy/…`, `collab:collab-database/…` y `editor:lib/…`.
4. **`harvest_open_questions.py` — recorre `10-motor-export-import/` y lee secciones 5–8.** Antes solo miraba `09-features` y la sección `## 18.`, que no existe en la plantilla export: los `[NO DETERMINADO]` de B4 eran invisibles.
5. **Script nuevo `make_b4_units.py`** — genera las 14 unidades B4 con su lista real de archivos y valida que las 124 rutas existan en `SRC/` antes de escribir el JSON.

**Bugs encontrados y corregidos durante la fase**: `make_b4_units.py` generaba `B4.3` con un duplicado (y con una lista de 3 rutas en vez de 5); los frontmatter de B4.3/B4.4/B4.6Ampliaban el alcance más allá de la lista inicial del unit, así que se sincronizó cada unit contra el frontmatter real del doc (validando existencia) en vez de recortar los docs.

## Hallazgos materiales del bloque (los que cambian decisiones)

1. **No existe exportación a texto plano.** `DocumentExportType.text` lanza `throw UnimplementedError()` (frontend/appflowy_flutter/lib/workspace/application/export/document_exporter.dart:55–56) y ningún call site lo despacha, pero el importador **sí** acepta `.txt`. La asimetría es real: se puede importar texto plano pero no exportarlo. B4.3 documenta además los tres conversores de texto plano que sí existen en el producto (`GetDocumentText` para el contexto de IA, `ConvertDocument` con `ParseTypePB.text` sin consumidor Dart, y el copiado del editor).
2. **La publicación web no exporta HTML: envía `EncodedCollab` binario.** `publish_util.rs` materializa el collab a disco, lo serializa con `bincode` y lo manda en un `PublishPayload::{Document|Database}` al backend, que es quien renderiza. Es el único motor de export que cruza la frontera sin producir fichero de usuario, y rompe la asimetría que cabía esperar con el export HTML local de B4.2.
3. **El slug de publicación tiene dos algoritmos que no se reconcilian**: Dart `[^a-zA-Z0-9-]` con 120 caracteres (frontend/appflowy_flutter/lib/workspace/application/export/document_exporter.dart:13–18) y Rust `[^\w-]` Unicode-aware con 50 (`appflowy/frontend/rust-lib/flowy-folder/src/publish_util.rs:11–22`). En el camino normal gana el Dart; el Rust solo se ejerce desde un test programático.
4. **`CSVFormat::META` es el único round-trip fiel de base de datos y no tiene productor alcanzable desde la app**: el export CSV fija siempre `Original` (frontend/rust-lib/flowy-database2/src/event_handler.rs:1036) y el import `.afdb` solo es alcanzable en debug (`appflowy/frontend/appflowy_flutter/lib/workspace/presentation/home/menu/sidebar/import/import_type.dart:64–66`).
5. **El export CSV ignora el `viewId` enviado por Dart** y usa `get_first_database_view_id()` (frontend/rust-lib/flowy-database2/src/services/share/csv/export.rs:31–33): exportar una vista Board de una base multi-vista devuelve el esquema de la primera. Ningún test lo detecta porque `share_test` solo usa bases de una vista.
6. **El ciclo `.afdoc` está roto**: el export emite extensión `afdocument` (`appflowy/frontend/appflowy_flutter/lib/workspace/presentation/settings/widgets/files/settings_file_exporter_widget.dart:228–274`) y el import espera `afdoc` (`appflowy/frontend/appflowy_flutter/lib/plugins/document/presentation/editor_plugins/migration/editor_migration.dart:31–38`). Además el export emite JSON actual (raíz `page`) mientras `migrateDocument` espera el `type: editor` de v0.1.0.
7. **El import de Markdown es 100 % Dart**: `ImportType::Markdown` existe en Rust pero `DocumentFolderOperation::import_from_bytes` descarta el discriminante (frontend/rust-lib/flowy-core/src/deps_resolve/folder_deps/folder_deps_doc_impl.rs:159–177) y `import_from_file_path` es un `TODO(lucas)` que devuelve `Ok(())` (`:179–187`).
8. **El import de CSV tiene un límite duro de 500 filas** (frontend/rust-lib/flowy-folder/src/manager.rs:463–468) que trunca en silencio: el único test que lo prueba confirma 492 filas OK y 10 240 → `InvalidParams` (`import_test.rs:8,27`). No hay aviso previo.
9. **El decoder de Markdown intenta `jsonDecode` sobre cualquier atributo** que no reconoce (`editor:lib/src/plugins/markdown/decoder/delta_markdown_decoder.dart:1`), lo que permite inyectar atributos arbitrarios en el delta.
10. **La publicación no tiene vuelta**: ningún `ImportType` acepta una URL pública.
11. **PDF solo es alcanzable desde el `example/` del editor**: `PdfHTMLEncoder` se invoca en editor:editor/example/lib/home_page.dart:416 y `printing` está declarado solo en `example/pubspec.yaml:46`. La app no monta ningún camino a PDF.
12. **El export a Markdown tiene tres desenlaces silenciosos** (`DeltaNulo`, `ZipNulo`, `FileSystemException`): en los tres, el caller recibe `markdown` correcto sin saber que el artefacto no existe.

## Correcciones de scope oficializadas

| Afirmación previa | Realidad verificada | Declarado en |
|---|---|---|
| B4.6 = "raw database data" con F12.1 (en F02.13) | Es el evento `ExportRawDatabaseData = 178` y el cliente es `F12.1`, pero el **lado de conversión** es `Database::get_database_json_string` (`collab-database/src/database.rs:1522–1528`), sin formato CSV | B4.6, B4.0 |
| `F12.2` describe `publish_util.rs` "como contrato cliente" | Es el **motor completo** del lado Rust: serializa el collab a binario y compone el `PublishPayload` | B4.12, B4.0 |
| `F19.2.8`: "`DocumentHTMLDecoder.enableColorParse` no lo cambia nadie" | **Sí lo cambia**: frontend/appflowy_flutter/lib/plugins/document/presentation/editor_page.dart:192–193 lo pone a `false` en la app | B4.2 |
| B4.2 con `documentToHTML(editorState:, contentHash:, encodeAmpersand:)` | Esas opciones **no existen**; la única opción real es `customParsers` (editor:editor/lib/src/plugins/html/html_document.dart:20) | B4.2 |
| Hay camino UI→import-HTML | **No**: `ImportType` no lista `html` ni en sus 5 miembros ni en `allowedExtensions` (`import_type.dart:7–12, 60–72`); los únicos consumidores de `htmlToDocument` son el portapapeles y la app de ejemplo del editor | B4.2 |
| `FieldType` tiene 16 variantes (F02) | Tiene **15** (frontend/rust-lib/flowy-database2/src/entities/field_entities.rs:427–444) | B4.5, B4.13 |
| El barrel `html_parser.dart` expone los 11 parsers | Exporta **9**: omite `divider_node_parser.dart` | B4.2 |

## Enlaces cruzados

`build_index.py --check-links`: **44 no resueltos de 3 025**, todos `[[B6.1]]`, `[[B6.2]]` y `[[B6.3]]`. Cero erratas, cero tokens de ejemplo, cero ids de B4 sin resolver: los 36 `[[B4.*]]` heredados se resolvieron solos al materializarse las 14 unidades, y se añadió el alias de bloque `B4` → `B4.0` para los 5 documentos que enlazan al motor entero.

## Preguntas abiertas

**9 `[NO DETERMINADO]` nuevos** de 6 documentos volcados a `OUT/22-preguntas-abiertas.md` § "B4 · Motor de export/import/publicación". Ninguna bloquea el cierre del bloque; las de mayor peso son la divergencia 120 vs 50 del slug, el ciclo `.afdoc` roto y la cuantificación de pérdida de color en PDF (esta última exige acceso al renderer, no está en las tres fuentes).

## Siguiente bloque

**B5 · Secuencias globales** (13 fases, `sequenceDiagram` completo + prosa). Con B4 cerrado, las tres que dependían del motor tienen su materia prima: B5.10 (export), B5.11 (import) y B5.12 (publish) se construyen directamente sobre `OUT/10-motor-export-import/`.
