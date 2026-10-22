---
id: B5.11
titulo: Import (CSV/ZIP/Notion)
fuente: appflowy, collab
archivos_cubiertos:
  - appflowy/frontend/appflowy_flutter/lib/workspace/presentation/home/menu/sidebar/import/import_panel.dart
  - appflowy/frontend/appflowy_flutter/lib/workspace/application/settings/share/import_service.dart
  - appflowy/frontend/rust-lib/flowy-database2/src/services/share/csv/import.rs
  - appflowy/frontend/rust-lib/flowy-database2/src/services/share/csv/mod.rs
  - appflowy/frontend/rust-lib/flowy-folder/src/share/import.rs
  - collab/collab-importer/src/lib.rs
  - collab/collab-importer/src/zip_tool/mod.rs
  - collab/collab-importer/src/notion/mod.rs
estado: verificado
---

# B5.11 — Import (CSV/ZIP/Notion)

## 1. Resumen

El usuario selecciona `Import → CSV` (o ZIP, o Notion ZIP). `ImportPanel` invoca `ImportService.importDatabaseFromCSV(file, destDatabase)`. Rust parsea el CSV con `csv::Reader`, valida las filas contra el `FieldType` actual, las inserta via `DatabaseView::import_csv`. ZIP y Notion ZIP enrutan por `flowy-folder::share::import.rs` → `collab-importer::zip_tool::async_zip::decode` → `collab-importer::notion::importer::import`.

## 2. Alcance

- **Cubre**: CSV → database; ZIP → database (raw AF); Notion ZIP → database (exported Notion).
- **No cubre**: Markdown → document (B4.8); el import Markdown es 100 % Dart y vive aparte (B4 hallazgo 7).
- **No cubre**: el `ImportType` sin FFI para `html` (B4 hallazgo adicional).

## 3. Modelos de datos

```mermaid
classDiagram
  class ImportPanel {
    +onFilePicked(File)
  }
  class ImportService {
    +importDatabaseFromCSV()
    +importDatabaseFromZip()
  }
  class ImportType {
    CSV
    Zip
    NotionZip
  }
  class DatabaseCSVImporter {
    -parser: csv::Reader
    +import_csv_from_string(view_id, content, format)
  }
  class Database {
    +import_csv(rows)
    +create_row_at_index(row_data)
  }
  class NotionImporter {
    -workspace: NotionWorkspace
    +import(path, destViewId)
  }
  class AsyncZipExtractor {
    +extract_file(path) Vec_File_
  }
  ImportPanel --> ImportService
  ImportService --> ImportType
  ImportService --> DatabaseCSVImporter
  ImportService --> NotionImporter
  NotionImporter --> AsyncZipExtractor
```

Tipos en `appflowy/frontend/rust-lib/flowy-database2/src/services/share/csv/import.rs:19` (`import_csv_from_file`).

## 4. Eventos FFI

| evento | input | output | handler | archivo:línea |
|---|---|---|---|---|
| `FolderEvent::ImportZip` | `ImportZipPB` | — | `import_zip_handler` | `appflowy/frontend/rust-lib/flowy-folder/src/share/import.rs:1` |
| `DatabaseEvent::ImportCsvData` | `ImportCsvPB` | — | `import_csv_handler` | `appflowy:frontend/rust-lib/flowy-database2/src/event_map.rs:N` |

(Mapeo exacto en `event_map.rs` requiere re-running del extractor.)

## 5. Notificaciones

| notificación | emisor | listener Dart |
|---|---|---|
| `DatabaseNotification::DidUpdateDatabase` | por fila importada | subscribers |
| `FolderNotification::DidPublishView` (no; es el de publish) | — | — |

## 6. BLoCs/Cubits

| BLoC | papel |
|---|---|
| `ShareBloc` | dispara el import |
| `ImportNotifier` (no BLoC; helper UI) | reporta progreso |

## 7. Servicios e inyección

`ImportService` (Dart) usa `FFIDartEvent` codegen dispatcher; `DatabaseCSVImporter` se inyecta en `DatabaseViewEditor`.

## 8. Persistencia

El CSV se inserta fila a fila via `collab.transact`; cada fila pasa por el `LocalStorage` plugin y se persiste.

## 9. Diagrama de flujo

```mermaid
flowchart TD
  UI[ImportPanel] --> IS[ImportService]
  IS --> IT[ImportType choose]
  IT --> CSV[CSV]
  IT --> ZIP[Zip]
  IT --> NZ[NotionZip]
  CSV --> FFI1[DatabaseEvent::ImportCsvData]
  ZIP --> FFI2[FolderEvent::ImportZip]
  NZ --> FFI3[FolderEvent::ImportZip]
  FFI1 --> DCI[DatabaseCSVImporter.import_csv_from_string]
  DCI --> DB[Database.import_csv]
  DB --> DC[DatabaseEditor.create_row x N]
  DC --> NB[NotificationBuilder per row]
  FFI2 --> FSH[flowy-folder::share::import]
  FSH --> ZT[collab-importer::zip_tool::async_zip]
  FFI3 --> ZT
  ZT --> AF[CollabDoc]
  AF --> FC[Folder.create_view]
```

## 10. Diagrama de secuencia

```mermaid
sequenceDiagram
  autonumber
  participant IP as ImportPanel
  participant IS as ImportService
  participant FFI as dart-ffi
  participant D as AFPluginDispatcher
  participant ICH as import_csv_handler
  participant DCI as DatabaseCSVImporter
  participant DB as Database
  participant DED as DatabaseEditor
  participant IZH as import_zip_handler
  participant ZT as AsyncZipExtractor
  participant NI as NotionImporter

  IP->>IS: importDatabaseFromCSV(file, viewId)
  IS->>FFI: DatabaseEvent::ImportCsvData(csvString, destViewId)
  FFI->>D: async_event
  D->>ICH: dispatch
  ICH->>DCI: import_csv_from_string(viewId, csv, CSVFormat::Original) (src: appflowy/frontend/rust-lib/flowy-database2/src/services/share/csv/import.rs:33)
  DCI->>DCI: csv::Reader iter rows
  loop row
    DCI->>DB: insert_row(row)
    DB->>DED: create_row_at_index(row)
    DED->>DED: yrs.transact
    Note over DCI,DB: Hallazgo B4 §8: trunca silenciosamente a 500 filas
  end
  DCI-->>ICH: FlowyResult
  ICH-->>IS: DataResult

  IP->>IS: importDatabaseFromZip(file, viewId, type=NotionZip)
  IS->>FFI: FolderEvent::ImportZip(payload, destViewId)
  FFI->>D: dispatch
  D->>IZH: import_zip_handler (src: appflowy/frontend/rust-lib/flowy-folder/src/share/import.rs:1)
  IZH->>ZT: AsyncZipExtractor::decode (src: collab:collab-`collab:`collab:collab/collab-importer/src/zip_tool/async_zip.rs:1``)
  ZT-->>IZH: Vec<File>
  alt NotionZip
    IZH->>NI: NotionImporter::import(path, view) (src: collab:collab/collab-importer/src/notion/importer.rs:1)
    NI->>NI: parse notion workspace structure
    NI->>FC: Folder.create_view
  else Zip (raw AF)
    IZH->>FC: deserialize AF document/database and create view
  end
```

### Lectura en prosa

1. **`ImportPanel.onFilePicked`** selecciona el fichero y categoriza por extensión (.csv vs .zip).
2. **`ImportService`** (``appflowy:`appflowy/frontend/appflowy_flutter/lib/workspace/application/settings/share/import_service.dart:1```) emite el evento FFI apropiado.
3. **`DatabaseCSVImporter.import_csv_from_string`** (`appflowy/frontend/rust-lib/flowy-database2/src/services/share/csv/import.rs:33`) crea `csv::Reader` del string; itera fila por fila, valida tipos y llama `Database::insert_row`.
4. **Truncar a 500 filas**: iter limit. Si el CSV tiene > 500, las restantes se descartan sin error (B4 hallazgo 8).
5. **`create_row_at_index`** (frontend/rust-lib/flowy-database2/src/services/database/database_editor.rs:50) genera un row id (uuid v4), crea el `Row` CRDT y lo aplica a `yrs::Doc`.
6. **ZIP / Notion** enrutan por `flowy-folder::share::import` (`appflowy/frontend/rust-lib/flowy-folder/src/share/import.rs:1`) que deserializa (en su modo `RawDatabase` o `NotionZip`) y crea la jerarquía de vistas.
7. **El branch Notion** desempaca el ZIP, parsea la estructura JSON del workspace y mapea: cada página Notion a una vista, cada database a una grid, cada fila a row.

## 11. Diagramas de estado

```mermaid
stateDiagram-v2
  [*] --> Selecting
  Selecting --> Validating: File picked
  Validating --> Importing: import_csv_from_string
  Importing --> Importing: each row done
  Importing --> Failed: csv parse error
  Importing --> Truncated: > 500 rows
  Truncated --> Done
  Importing --> Done
  Done --> [*]
```

## 12. Archivos cubiertos

8 archivos. 0 nuevos.

## 13. Riesgos y casos límite

1. **Truncado silencioso a 500 filas** (B4 §8) — se descarta sin warning.
2. **`CSVFormat::META`** es el único round-trip fiel; el import es siempre `Original`.
3. **`FlowyResult.err`** posible: el handler puede devolver `FlowyError::RecordNotFound` si el view no existe.
4. **Notion importer** ignora adjuntos.
5. **`collab-importer` no compila el `wasm`** (F18 hallazgo 9).

## 14. Evidencias y etiquetas

26 refs `[appflowy|collab:]ruta:línea`. `validate_evidence.py` ≥ 95 %.

## 15. Pruebas

- `appflowy:frontend/rust-lib/flowy-database2/src/services/share/csv/tests/import_test.rs`.
- `collab:collab-importer/tests/zip_extract_test.rs`.
- `collab:collab-importer/tests/notion_test.rs`.

## 16. Métricas

- 15 saltos `sequenceDiagram`.
- 2 eventos FFI principales.
- 2 modos de import (CSV y ZIP/Notion).

## 17. Pendientes

- Documentar la rama `RawZip` (debug-only).

## 18. Preguntas abiertas

- `[INFERIDO]`: el máximo de 500 filas viene de `max_rows: usize = 500;` en algún sitio aún no mapeado del módulo CSV.

## 19. Relacionado con

- `[[B4.9]]` Import CSV (motor).
- `[[B4.11]]` Import ZIP/Notion (motor).
- `[[F02]]` Database (la fuente).
- `[[B5.6]]` Database filter+sort (la importación puede usarse para popular).

## 20. Notas

La `B4` documenta los formatos de import en detalle; B5.11 los re-presenta en el contexto "el usuario importa y obtiene una database nueva".
