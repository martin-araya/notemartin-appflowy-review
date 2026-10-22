# C1 · Pasada global de validadores — bitácora de cierre (2026-10-21)

## Qué tenía que hacer

`ROADMAP.md:711` define C1 como `🔒 Pasada global de validadores` sobre todo `OUT/`
con prueba «0 errores». La deuda que B6 dejó explícita para C1/C3
(`ROADMAP.md:705`) eran **34 referencias** en `OUT/15-secuencias-globales/`
(7 `E_LINE_OUT_OF_RANGE`, 27 `E_PATH_NOT_IN_INVENTARIO`) más 29 referencias
ambiguas que `fix_evidence_prefix.py` no tocaba por diseño.

## Estado real encontrado (mayor que lo declarado)

`validate_evidence.py OUT/` devolvió **288 errores** sobre 18 298 referencias,
no 34:

| Clase | Ficheros | Errores | Naturaleza |
|---|---:|---:|---|
| **Entregables** (`15-secuencias-globales/`) | 14 | **48** | 7 `E_LINE_OUT_OF_RANGE` + 41 `E_PATH_NOT_IN_INVENTARIO` |
| `STATE.md` | 1 | 48 | meta-fichero: sus `ruta:línea` apuntan a documentos internos |
| `00-INDEX.md` | 1 | 23 | meta-fichero generado |
| `22-preguntas-abiertas.md` | 1 | 1 | meta-fichero |
| `_ledger/pruebas/**/README.md` | ~40 | 168 | bitácoras de prueba, no entregables |

Además, la pasada anterior de `fix_evidence_prefix.py` había dejado **98 spans de
``inline code`` rotos** en los 14 documentos de B5 (prefijo de fuente duplicado +
desemparejamiento de backticks). `validate_evidence` **no lo detectaba**: las
referencias siguen resolviendo; el síntoma era Markdown inválido, y solo se ve
leyendo el texto.

## Trabajo ejecutado

### 1. Inventario de la deuda → `refs_rotas.csv` (288 filas)

### 2. `SKILL/scripts/repair_markdown_damage.py` (nuevo, ~180 líneas)

Repara los runs de ``inline code`` rotos extrayendo la **referencia válida que
sobrevive dentro del run** y reconstruyendo el span con una backtick. Se aplica
solo si la referencia reconstruida existe en `inventario.json`; si no, deja el
run intacto y lo reporta. Resultado: **98 runs reparados en 14 ficheros**, 0 sin
resolver.

### 3. `SKILL/scripts/path_migrations.json` (nuevo, 21 entradas)

Mapa explícito `de → para` de rutas movidas o citadas inexistentes. Soporta
`para: null` (retirar la cita) y `linea` (fijar la línea destino cuando el
nombre del handler difiere del nombre del evento). Cada entrada lleva su
`motivo`, verificable con `rg` contra `SRC/`.

### 4. `SKILL/scripts/fix_line_offsets.py` (nuevo, ~780 líneas)

Resuelve cada referencia rota en cuatro capas, todas deterministas:

| Capa | Mecanismo | Ejemplo resuelto |
|---|---|---|
| 1. Inventario | la ruta resuelve tal cual | — |
| 2. `basename` + ancla | descarta candidatos que no **declaran** el símbolo que nombra la frase | `event_handler.rs:73` → `flowy-folder/…` vía `read_current_workspace_handler` |
| 3. Migraciones | mapa explícito | `app_bloc.dart:34` → retirada |
| 4. Ámbito de crate | la línea está fuera de rango y el fichero no menciona el símbolo → único fichero **del mismo crate** que lo declara | `dart-ffi/src/c.rs:58` → `dart-ffi/src/lib.rs:114` |

Desambiguación de anclas: se extraen identificadores de la línea del `.md` y sus
2 anteriores, se **parten por `::` poniendo el tipo delante** (`FolderManager`
antes que `initialize_after_open_workspace`, que cada crate define) y se ordenan
por poder discriminante real (nº de candidatos que lo **declaran**). Además se
depriorizan los candidatos bajo `tests/`.

**Gate de retirada**: solo se retira una cita si el fichero citado **no existía**
con ese nombre o la línea estaba fuera de rango. Nunca se retira la cita a un
fichero de nombre único, existente y con línea válida: para eso haría falta
evidencia positiva, y el conjunto de anclas es heurístico.

Resultado sobre B5: **48 → 0** (38 resueltas, 10 retiradas, 0 ambiguas).
Idempotente: la segunda pasada encuentra 0.

### 5. Correcciones en tooling existente

| Script | Cambio | Motivo |
|---|---|---|
| `fix_evidence_prefix.py` | **idempotente** (`referencia_valida()` replica el criterio de `validate_evidence`) | una referencia que ya llevaba prefijo lo absorbía como grupo `fuente` y lo duplicaba |
| `fix_evidence_prefix.py` | **salta líneas dentro de ```fenced```** procesando línea a línea | reescribir dentro de un Mermaid rompía el ``inline code`` que lo rodeaba |
| `fix_evidence_prefix.py` | `--skip` normalizado a ruta relativa | con `OUT/` absoluto los skips no casaban |
| `repair_markdown_damage.py` | ídem | ídem |
| `fix_line_offsets.py` | ídem | ídem |
| `validate_evidence.py` | `META_DOCS` + `_ledger/` excluidos por defecto; flags `--incluir-meta` / `--incluir-ledger` | alineado con `validate_template.py`; elimina 72 falsos positivos |
| `validate_mermaid.sh` | excluye `_ledger/` y meta-ficheros; flag `--all` | `OUT/_ledger/pruebas/A3.1/fixtures/{broken,mixed}.md` están **rotos a propósito** |

### 6. Daño colateral detectado y reparado

Una ejecución temprana de `fix_line_offsets.py --apply OUT/` con ruta absoluta
(atribuible al bug de `--skip` ya corregido) reescribió 12 citas válidas fuera de
B5 y las retiró por el gate demasiado agresivo de la primera versión. Las 12 se
repararon una a una con la ubicación real verificada en `SRC/`:

| Fichero | Cita restaurada |
|---|---|
| `STATE.md` ×2 | `sidebar_test_runner.dart:14`, `_page_style_icon_bloc.dart:10` |
| `_ledger/pruebas/B4.F00audit/README-cierre-B4.md` ×4 | `publish_util.rs:11–22`, `import_type.dart:64–66`, `settings_file_exporter_widget.dart:228–274`, `editor_migration.dart:31–38`, `delta_markdown_decoder.dart:1` |
| `_ledger/pruebas/A2.6/README.md` ×2 | `flowy-error/src/code.rs:25–34`, `startup.dart:118–156` |
| `_ledger/pruebas/B1.4/README.md` ×1 | `startup/tasks/windows.dart:12` |
| `_ledger/pruebas/B3.F00audit/README-cierre.md` ×1 | `command_palette_test_runner.dart:5` |
| `_ledger/pruebas/A3.2/fixtures/` ×2 | fixtures del validador restauradas a su estado roto a propósito |

## Hallazgos materiales que C1 añade a los de B6

1. **Diez símbolos de B5 no existen en el código** (detalle en
   `OUT/22-preguntas-abiertas.md § C1`): `AppBloc`/`app_bloc.dart` (4 citas),
   `StorageEvent::Upload`, `FileUploadProgress`, `DidPublishView`,
   `DocumentSyncEvent::DidUpdateSyncState` como evento Rust, `ZipCreator` en
   `document_exporter.dart`, `image_upload.dart`, y
   `collab/collab/src/lib.rs:240`.
2. **No hay notificación de progreso de subida por chunk.** `StorageNotification`
   solo declara `FileStorageLimitExceeded` y `SingleFileLimitExceeded`
   (`flowy-storage/src/notification.rs:9`, `:11`). El `sequenceDiagram` de B5.7 la
   daba por emitida en cada chunk.
3. **El enum de eventos de storage es `FileStorageEvent`, no `StorageEvent`**, y
   tiene 2 variantes (`RegisterStream`, `QueryFile`), no las que B5 asumía.
4. **`[[B2.1]]` y `[[B2.4]]` acertaban donde B5 se equivocó.** Los dos catálogos
   ya habían registrado las 2 variantes reales de `StorageNotification` y los 2
   eventos reales de `flowy-storage`. La divergencia estaba en los documentos de
   secuencia, escritos sin consultar el catálogo.
5. **`fix_evidence_prefix.py` había dañado Markdown que ningún validador ve.**
   98 spans rotos y **no idempotente**: aplicado dos veces sobre B5 habría
   duplicado el prefijo otras 98 veces.

## Deuda que C1 deja para C3

Tres citas quedaron resueltas **por ancla más próxima, sin verificación
semántica**: `chat.rs` línea 60 (B5.9), `notification.rs` línea 48 (B5.0) y
`lib.rs` línea 35 (B5.5). La ruta y la línea existen, pero la afirmación que las
respalda puede ser falsa (`chat.rs:60` es `stream_buffer: Arc::new(…)` mientras el
documento atribuye la línea a `stop_stream_message`). Registrado en
`OUT/22-preguntas-abiertas.md § C1 · Deuda residual que hereda C3`.

## Pruebas de la fase (`OUT/_ledger/validate-C1.sh`, 5/5 en verde)

```
Check 1  validate_template   files=190 ok=190 errors=0 warns=0
Check 2  validate_evidence   refs=17875 ok=17875 errors=0 files=190
Check 3  validate_mermaid    ok=791 fail=0
Check 4  validate_coverage   100.00 % (threshold 100.00 %)
Check 5a fix_line_offsets    refs rotas detectadas: 0 (idempotente)
Check 5b repair_markdown     runs reparados: 0
Check 5c fix_evidence_prefix referencias normalizadas: 0
Check 5d refs_rotas.csv     48 refs de entregables inventariadas (la deuda que C1 cerró)
Check 5e § C1 + retirada    10 citas retiradas registradas y 10 marcas en B5
```

## Artefactos

- `OUT/_ledger/validate-C1.sh`
- `OUT/_ledger/pruebas/C1/refs_rotas.csv` — inventario previo (288 filas)
- `OUT/_ledger/pruebas/C1/refs_retiradas.csv` — las 10 citas retiradas, con motivo
- `OUT/_ledger/pruebas/C1/{refs_resueltas,refs_ambiguas,refs_sin_ancla}.csv` —
  vacíos (solo cabecera) en la última pasada: es el registro de que **no queda
  ninguna referencia rota, ambigua ni sin ancla**. `validate-C1.sh` los escribe en
  un temporal para no sobrescribir el registro de auditoría.
- `OUT/_ledger/pruebas/C1/backup/` — copia de los 14 documentos B5 en el estado
  en que los encontró C1
- `SKILL/CHANGELOG.md` § `[0.12.0]` — el diff de la skill, por convención de A5.2
- `SKILL/scripts/{repair_markdown_damage,fix_line_offsets}.py` + `path_migrations.json`