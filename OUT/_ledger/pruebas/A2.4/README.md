# Pruebas A2.4 — `extract_blocs.py` + `blocs.json`

**Fecha:** 2026-10-18
**Fase:** A2.4 (Bloque A2 — Extractores deterministas)
**Estado:** ✅ cerrada

## Objetivo

Verificar que el extractor:

1. Recorre `SRC/appflowy/frontend/appflowy_flutter/lib/**/*.dart` y extrae
   todas las clases `extends Bloc<…>` o `extends Cubit<…>`.
2. Para cada bloc, captura `event_type` y `state_type` de los generics.
3. Vincula los eventos/estados a su `@freezed class` en el mismo archivo, o
   a `sealed class` (con `const factory` o `factory => Concrete(args)`) en
   otros archivos de la nueva arquitectura `features/*/logic/*_event.dart`.
4. Extrae los campos del state principal y los servicios inyectados
   (campos `final T _name = T(...)`).

## Comandos ejecutados

```bash
python3 SKILL/scripts/extract_blocs.py
OUT/_ledger/validate-A2.4.sh
```

Log completo: [`extract.log`](extract.log) y [`validate.log`](validate.log).

## Resultado del validador

```
OK: A2.4 (JSON valido, 142 blocs (125 Bloc + 17 Cubit), DocumentBloc OK con 8 eventos, ShareBloc OK con 9 eventos, 33 blocs en plugins/database/application)
exit=0
```

## Resumen

| Métrica | Valor |
|---|---:|
| Total Blocs + Cubits | **142** |
| Blocs (extiende `Bloc<…>`) | 125 |
| Cubits (extiende `Cubit<…>`) | 17 |
| Blocs con eventos extraídos | 125 |
| BLoCs en `plugins/database/application/` | **33** |
| Archivos `.dart` escaneados | 1.525 |

**Distribución por carpeta de primer nivel:**

| Carpeta | BLoCs |
|---|---:|
| `plugins/` (document, database, shared, etc.) | 72 |
| `workspace/` (settings, view, edit, etc.) | 43 |
| `mobile/` | 9 |
| `user/` | 8 |
| `features/` (nueva arquitectura) | 5 |
| `ai/` | 5 |

## Casos del test literal del ROADMAP A2.4

### `DocumentBloc`

```json
{
  "name": "DocumentBloc",
  "kind": "Bloc",
  "file": "SRC/appflowy/frontend/appflowy_flutter/lib/plugins/document/application/document_bloc.dart",
  "decl_line": 47,
  "event_type": "DocumentEvent",
  "state_type": "DocumentState",
  "events": [
    {"factory": "DocumentEvent.initial",            "class": "Initial",            "decl_line": 455},
    {"factory": "DocumentEvent.moveToTrash",         "class": "MoveToTrash",        "decl_line": 456},
    {"factory": "DocumentEvent.restore",             "class": "Restore",            "decl_line": 457},
    {"factory": "DocumentEvent.restorePage",         "class": "RestorePage",        "decl_line": 458},
    {"factory": "DocumentEvent.deletePermanently",   "class": "DeletePermanently",  "decl_line": 459},
    {"factory": "DocumentEvent.syncStateChanged",    "class": "syncStateChanged",   "decl_line": 460},
    {"factory": "DocumentEvent.syncAwarenessStates", "class": "SyncAwarenessStates","decl_line": 463},
    {"factory": "DocumentEvent.clearAwarenessStates","class": "ClearAwarenessStates","decl_line": 464}
  ],
  "state_fields": [
    {"name": "isDeleted",       "type": "bool",                          "required": true,  "default": null},
    {"name": "forceClose",      "type": "bool",                          "required": true,  "default": null},
    {"name": "isLoading",       "type": "bool",                          "required": true,  "default": null},
    {"name": "syncState",       "type": "DocumentSyncState",             "required": true,  "default": null},
    {"name": "isDocumentEmpty", "type": "bool?",                         "required": false, "default": null},
    {"name": "userProfilePB",   "type": "UserProfilePB?",                "required": false, "default": null},
    {"name": "editorState",     "type": "EditorState?",                  "required": false, "default": null},
    {"name": "error",           "type": "FlowyError?",                   "required": false, "default": null},
    {"name": "awarenessStates", "type": "DocumentAwarenessStatesPB?",    "required": false, "default": null}
  ],
  "injected_services": [
    {"name": "_documentListener", "type": "DocumentListener",         "init": "DocumentListener(id: documentId)"},
    {"name": "_syncStateListener","type": "DocumentSyncStateListener","init": "DocumentSyncStateListener(id: documentId)"},
    {"name": "_documentService", "type": "DocumentService",          "init": "DocumentService()"},
    {"name": "_trashService",    "type": "TrashService",             "init": "TrashService()"}
  ]
}
```

### `ShareBloc`

9 eventos: `initial`, `share`, `publish`, `unPublish`, `updateViewName`,
`updatePublishStatus`, `setPublishStatus`, `updatePathName`,
`clearPathNameResult`.

### BLoCs en `plugins/database/application/`

33 BLoCs (umbral ≥ 5; valor real mucho mayor). Ejemplos: `ShareBloc`,
`DatabaseTabBarBloc`, `DatabasePropertyBloc`, `DatabaseGroupBloc`,
`DatabaseShareBloc`, `RowBloc`, `RowMetaBloc`, `CellBloc`, `FieldBloc`,
`SortBloc`, `FilterBloc`, `FieldSettingsBloc`, `LayoutSettingBloc`,
`CalculationsBloc`, `ViewBloc`, etc.

## Patrones cubiertos

**Lado Dart (arquitectura legada — `plugins/`, `workspace/`):**

1. `class XBloc extends Bloc<XEvent, XState> { ... }` con `@freezed class XEvent with _$XEvent { const factory XEvent.foo(args) = Concrete; }` en el mismo archivo.
2. `const factory X.foo({args}) = Concrete;` con named args (multi-línea).
3. `class XCubit extends Cubit<XState>` sin eventos.
4. Argumentos genéricos `Bloc<BlocEvent<X>, BlocState<X>>` se parsean
   correctamente (caso complejo).

**Lado Dart (nueva arquitectura — `features/`):**

1. `sealed class XEvent { ... }` con `const factory X.foo(args) = Concrete;`.
2. `sealed class XEvent { ... }` con `factory X.foo(args) => Concrete(args);` (arrow form).
3. Multi-línea: `factory X.setCustomPath(String path) =\n      Concrete;`.
4. Eventos definidos en archivo separado: `logic/X_event.dart`, resueltos
   vía `cross_file_event_index`.

**Injected services:**

1. `final T _name = T();` (constructor simple).
2. `final T _name = T(arg: value);` (constructor con args).
3. `late final T _name = T();` (late).
4. `late final T _name;` (late sin inicialización) — **no se captura** (limitación conocida).
5. Argumentos del constructor: `DocumentBloc({required this.documentId, ...})`
   no se extraen (no son servicios inyectados en sí mismos).

## Smoke test (robustez del extractor)

Ejecutado con `SRC/` vacío (directorios creados pero sin clones):

```bash
TMP=$(mktemp -d) && mkdir -p "$TMP/SRC/appflowy/frontend/appflowy_flutter/lib"
python3 SKILL/scripts/extract_blocs.py --src-root "$TMP/SRC" --out-dir "$TMP/out"
```

Resultado:

```json
{
  "total_blocs": 0,
  "total_cubits": 0,
  "blocs_with_freezed_events": 0,
  "blocs_in_plugins_database_application": 0,
  "files_scanned": 0
}
```

✅ El extractor no aborta; produce JSON bien formado con listas vacías.
El validador en este modo falla en check 4 (que exige `DocumentBloc`),
comportamiento esperado.

## Tamaño y rendimiento

| Métrica | Valor |
|---|---|
| Líneas JSON | 9.369 |
| Tamaño | 268 KB |
| Tiempo de extracción | < 5 s |
| Tiempo del validador | < 0,1 s |

## Diferencias detectadas vs el plan original (corregidas en sitio)

| # | Diferencia | Acción |
|---|---|---|
| 1 | `RE_FREEZED_CLASS` consumía la `{` final, lo que hacía que `find("{", end)` saltara al siguiente `{` | Corregido: regex ya no consume la `{` final. |
| 2 | `RE_FIELD` no aceptaba tipos primitivos Dart (`bool`, `int`, `String`, `double`) | Corregido: regex ampliado con `[a-z]+` para primitivos. |
| 3 | Los BLoCs de la nueva arquitectura (`features/`) declaran sus eventos en archivos separados con `sealed class` + `factory =>` (arrow) o `factory =` (freezed) | Añadido: resolución cross-file mediante `cross_file_event_index`, regex `RE_SEALED_FACTORY` para arrow form, soporte de multi-línea con `[\s\S]*?`. |
| 4 | `RE_SEALED_FACTORY` requería `const\s+factory`; los `factory` simples sin `const` no se capturaban | Corregido: `const` ahora opcional en ambos regex. |
| 5 | Inicialmente, 6 BLoCs (DataLocation, ShareTab, UserWorkspace, etc.) declaraban `event_type` pero `events[]` quedaba vacío | Resuelto al añadir cross-file resolution (D13 modificado a "sí implementar"). |
| 6 | Los servicios `late final T _name;` SIN inicialización (5 casos observados) no se capturan | Documentado como limitación; requiere análisis de asignación en el constructor. |

Sin impacto sobre el contrato externo del JSON.

## Criterio de aprobación del ROADMAP

> `DocumentBloc`, `ShareBloc` y los BLoCs de `plugins/database/application` aparecen con sus eventos.

- ✅ `DocumentBloc` con 8 eventos (`DocumentEvent`).
- ✅ `ShareBloc` con 9 eventos (`ShareEvent`).
- ✅ 33 BLoCs en `plugins/database/application/` (umbral ≥ 5 ampliamente superado).
- ✅ Todos los BLoCs con `event_type` declarado tienen al menos 1 evento extraído (125/125).
- ✅ Conteos internos coherentes (validador checks 1–8).
