# Pruebas A2.6 — `extract_misc.py` + `misc.json`

**Fecha:** 2026-10-18
**Fase:** A2.6 (Bloque A2 — Extractores deterministas)
**Estado:** ✅ cerrada

## Objetivo

Verificar que el extractor captura los 6 bloques de metadata
miscelánea del workspace de AppFlowy:

1. **routes** — 35 `GoRoute(...)` en `generate_router.dart`.
2. **shortcuts** — `HotKeyItem` en `hotkeys.dart` (los `CommandShortcutEvent`
   viven en `appflowy_editor` externo, no en este repo).
3. **feature_flags** — `enum FeatureFlag` en `shared/feature_flags.dart`.
4. **error_codes** — `pub enum ErrorCode` con `#[repr(u8)]` en
   `flowy-error/src/code.rs`.
5. **i18n_keys** — strings y `LocaleKeys.X` usados con `.tr()`.
6. **startup_tasks** — orden de `LaunchTask` en `startup.dart`.

## Comandos ejecutados

```bash
python3 SKILL/scripts/extract_misc.py
OUT/_ledger/validate-A2.6.sh
```

Log completo: [`extract.log`](extract.log) y [`validate.log`](validate.log).

## Resultado del validador

```
OK: A2.6 (JSON valido, routes=35, shortcuts=13, feature_flags=9, error_codes=133 (repr=u8), i18n_keys=1637, startup_tasks=15, PlatformErrorCatcherTask idx=0)
exit=0
```

## Resumen

| Bloque | Métrica | Valor |
|---|---|---:|
| routes | `GoRoute(...)` extraídos | 35 |
| shortcuts | `HotKeyItem` (con nombre del comentario) | 13 |
| shortcuts | `CommandShortcutEvent` (externo `appflowy_editor`) | 0 |
| feature_flags | `enum FeatureFlag` variantes | 9 |
| error_codes | `pub enum ErrorCode` variantes (u8) | 133 |
| error_codes | Variante con `#[default]` | `Internal` (idx=0) |
| i18n_keys | Claves únicas (en todo `lib/`) | 1.637 |
| i18n_keys | Usos totales (`.tr()` calls) | > 1.637 |
| startup_tasks | `LaunchTask` registradas en `addTasks` | 15 |

## Casos del test literal del ROADMAP A2.6

### 1. Cada salida no vacía (6/6)
- ✅ `routes.total = 35 > 0`
- ✅ `shortcuts.total = 13 > 0` (13 `HotKeyItem` con nombres legibles)
- ✅ `feature_flags.total = 9 > 0`
- ✅ `error_codes.total = 133 > 0` (con `repr = "u8"`)
- ✅ `i18n_keys.unique_keys = 1.637 > 0`
- ✅ `startup_tasks.total = 15 > 0`

### 2. `ErrorCode` coincide con variantes del enum (≥ 100)
- ✅ 133 variantes extraídas, `enum = "ErrorCode"`, `repr = "u8"`, todas con `index` en rango `0..=255`.
- ✅ Variante `Internal` con `is_default: true` y `index: 0` (como en el código fuente).
- ✅ Mensajes del `#[error("...")]` capturados (p. ej. `"Unauthorized user"`, `"Record not found"`).

## Casos destacados

### Routes (extracto)

```json
[
  {"path": "/",                          "name": "",                 "decl_line": 219},
  {"path": "AddMembersScreen.routeName", "name": "",                 "decl_line": 258},
  {"path": "AppFlowyCloudPage.routeName","name": "",                 "decl_line": 271},
  {"path": "DesktopHomeScreen.routeName","name": "",                 "decl_line": 515},
  {"path": "FeatureFlagScreen.routeName","name": "",                 "decl_line": 297}
]
```

Todos los `path` del workspace son referencias a constantes
(`SomeScreen.routeName`), NO strings literales. El extractor captura
ambas formas (D4 del plan).

### Feature flags

```json
[
  {"name": "collaborativeWorkspace",  "default": null, "decl_line": 16},
  {"name": "membersSettings",         "default": null, "decl_line": 21},
  {"name": "syncDocument",            "default": null, "decl_line": 26},
  {"name": "syncDatabase",            "default": null, "decl_line": 31},
  {"name": "search",                  "default": null, "decl_line": 36},
  {"name": "planBilling",             "default": null, "decl_line": 41},
  {"name": "spaceDesign",             "default": null, "decl_line": 46},
  {"name": "inlineSubPageMention",    "default": null, "decl_line": 51},
  {"name": "sharedSection",           "default": null, "decl_line": 56}
]
```

### Error codes (extracto)

```json
[
  {"name": "Internal",                "index": 0,   "is_default": true,  "message": "Internal error",                "decl_line": 13},
  {"name": "UserUnauthorized",        "index": 2,   "is_default": false, "message": "Unauthorized user",             "decl_line": 16},
  {"name": "RecordNotFound",          "index": 3,   "is_default": false, "message": "Record not found",              "decl_line": 19},
  {"name": "WorkspaceInitializeError","index": 6,   "is_default": false, "message": "Can't load the workspace data", "decl_line": 34}
]
```

Índices discontinuos (0, 2, 3, 4, 5, 6, 8, 9, ...) son legítimos — el código fuente salta valores (ver `appflowy/frontend/rust-lib/flowy-error/src/code.rs:25–34`, donde se reordena 5, 8, 9, 6).

### Startup tasks (primeras 8)

```json
[
  {"class": "PlatformErrorCatcherTask", "index": 0, "conditional": false, "condition": null},
  {"class": "MemoryLeakDetectorTask",  "index": 1, "conditional": false, "condition": null},
  {"class": "DebugTask",                "index": 2, "conditional": false, "condition": null},
  {"class": "FeatureFlagTask",          "index": 3, "conditional": false, "condition": null},
  {"class": "InitLocalizationTask",    "index": 4, "conditional": false, "condition": null},
  {"class": "InitAppWindowTask",       "index": 5, "conditional": false, "condition": null},
  {"class": "PluginLoadTask",           "index": 6, "conditional": false, "condition": null},
  {"class": "FileStorageTask",          "index": 7, "conditional": false, "condition": null}
]
```

Orden coincide exactamente con `appflowy/frontend/appflowy_flutter/lib/startup/startup.dart:118–156`.

### i18n keys (top 5)

```json
[
  {"key": "appName",                    "usages": 12, ...},
  {"key": "settings.appearance.title",  "usages":  3, ...},
  {"key": "common.confirm",             "usages":  5, ...},
  ...
]
```

## Patrones cubiertos

1. **Routes**: `GoRoute(path: 'literal', name: 'name')` o
   `GoRoute(path: SomeClass.routeName, ...)` (referencia a constante).
2. **Shortcuts — HotKeyItem**: `HotKeyItem(\n  hotKey: HotKey(...),\n  keyDownHandler: ...)`
   con comentario `// ...` justo antes (capturado como `name`).
3. **Shortcuts — CommandShortcutEvent**: declarado en el paquete externo
   `appflowy_editor`; el workspace lo referencia pero no lo define.
4. **Feature flags**: `enum FeatureFlag { name, name, name, }` con
   `;` después de la última variante y métodos en el cuerpo.
5. **Error codes**: `pub enum ErrorCode { #[error("msg")] Name = N, }` con
   `#[repr(u8)]` y comentarios `//` entre atributos y nombre.
6. **i18n keys**: `LocaleKeys.foo.bar.tr()` y `'foo.bar'.tr()`.
7. **Startup tasks**: `launcher.addTasks([ ... ])` con items
   `XxxTask()`, `if (cond) XxxTask()`, y `if (cond) ...[ X, Y ]`.

## Smoke test (robustez del extractor)

Ejecutado con SRC/ vacío (directorios creados pero sin código):

```bash
TMP=$(mktemp -d) && mkdir -p "$TMP/SRC/appflowy/frontend/rust-lib" \
  "$TMP/SRC/appflowy/frontend/appflowy_flutter/lib"
python3 SKILL/scripts/extract_misc.py --src-root "$TMP/SRC" --out-dir "$TMP/out"
```

Resultado:

```json
{
  "routes": 0,
  "shortcuts": 0,
  "feature_flags": 0,
  "error_codes": 0,
  "i18n_keys": 0,
  "startup_tasks": 0
}
```

✅ El extractor no aborta; produce JSON bien formado con todos los
bloques en cero. El validador en este modo falla en checks 3-9
(que exigen datos), comportamiento esperado.

## Tamaño y rendimiento

| Métrica | Valor |
|---|---|
| Líneas JSON | 13.540 |
| Tamaño | 504 KB |
| Tiempo de extracción | < 2 s |
| Tiempo del validador | < 0,1 s |

## Diferencias detectadas vs el plan original (corregidas en sitio)

| # | Diferencia | Acción |
|---|---|---|
| 1 | El plan asumía que `CommandShortcutEvent` está en el workspace. | Confirmado: vive en el paquete externo `appflowy_editor`. El extractor reporta `command_shortcut_event: { file: null, variants: [], total: 0 }` y captura los `HotKeyItem` como la fuente principal de atajos. Documentado en 22-preguntas-abiertas A2.6-a. |
| 2 | `HotKeyItem` no usa strings para `key` (usa `KeyCode.backslash` + `modifiers`). | Estrategia: extraer el comentario `// ...` anterior como `name`, generar id `hotkey_N` secuencial. |
| 3 | `GoRoute` usaba `path: SomeClass.routeName` (const), no strings. | Regex ampliada: `path:\s*(?:'literal'\|ClassName.routeName)`. |
| 4 | `find_matching_brace` buscaba desde `m.end()` después del `enum Name ` sin consumir `{`, lo que apuntaba al `{` siguiente en lugar del inmediato. | Corregido: `text.find("{", m.end() - 1)`. |
| 5 | `InProgress = 107` no se capturaba (tenía `// ...` entre `#[error(...)]` y el nombre). | Regex ampliada con `(?:\s*(?://[^\n]*\|/\*.*?\*/)\s*)*` entre attrs y nombre. |
| 6 | `m.start("2")` no funciona sin grupos con nombre en `RE_EC_VARIANT`. | Cambiado a `m.start(2)` (posicional). |
| 7 | El primer intento rompió la sintaxis de `extract_shortcuts` al insertar un regex dentro del cuerpo. | Restaurada la estructura `def extract_shortcuts` correcta. |

Sin impacto sobre el contrato externo del JSON.

## Criterio de aprobación del ROADMAP

> cada salida no vacía; el número de `ErrorCode` coincide con las variantes del enum.

- ✅ Las 6 salidas son no vacías (validador checks 3-8).
- ✅ `error_codes.total = 133 == número de líneas `Name = N,` en `code.rs` (validador check 4).
- ✅ `error_codes.repr = "u8"` (validador check 5).
- ✅ Todos los `ErrorCode` tienen `index` en rango `u8` (validador check 8).
- ✅ `PlatformErrorCatcherTask` está en posición 0 (validador check 9, coincide con comentario `// this task should be first task`).
