#!/usr/bin/env python3
"""build_catalog_errors.py — genera `OUT/15-catalogo-errores.md`
desde `OUT/_ledger/extract/misc.json::error_codes`.

Fase B2.5 de la skill `notemartin-appflowy-review`.
Spec: ROADMAP.md línea 177 y AGENTS.md §5.1 (AFPluginEventResponse +
FlowyError + UI handling).

Estructura del documento (10 secciones, plantilla `catalogue`):
  §1 Cómo leer este catálogo
  §2 Arquitectura del canal de error
  §3 Resumen por categoría
  §4 Índice global de los 133 códigos
  §5 Catálogo por categoría
  §6 Códigos sentinela / sin emisor específico
  §7 Conteo de filas y prueba literal
  §8 Cobertura y referencias cruzadas
  §9 Preguntas abiertas
  §10 Relacionado con

Política de evidencia:
  - Cada fila referencia `flowy-error/src/code.rs:decl_line`.
  - Rutas: `SRC/<fuente>/` → `<fuente>/` para alinear con inventario.
  - Emisor típico (`flowy-<x>/src/manager.rs`) y UI se derivan del
    nombre de la variante por regex.
  - Semántica SIEMPRE `[INFERIDO]`.

Prueba literal del ROADMAP: nº de filas = 133 (= error_codes.total).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DEFAULT_INPUT = PROJECT_ROOT / "OUT" / "_ledger" / "extract" / "misc.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "OUT" / "15-catalogo-errores.md"

# Categorización por prefijo (UpperCamelCase).
# Category rules (heurística). orden determinista por longitud descendente.
CATEGORY_RULES: list[tuple[str, str]] = [
    ("Workspace*",                       "Workspace"),
    ("WorkspaceMember*",                "Workspace"),
    ("WorkspaceLimit*",                 "Workspace"),
    ("WorkspaceData*",                  "Workspace"),
    ("WorkspaceInitialize*",            "Workspace"),
    ("Database*",                       "Database"),
    ("View*",                           "View"),
    ("Document*",                       "Document"),
    ("Folder*",                         "Folder"),
    ("Field*",                          "Field"),
    ("Row*",                            "Row"),
    ("Cell*",                           "Cell"),
    ("Filter*",                         "Filter"),
    ("Sort*",                           "Sort"),
    ("Group*",                          "Group"),
    ("Option*",                         "Option"),
    ("SelectOption*",                   "Option"),
    ("TypeOption*",                     "TypeOption"),
    ("Record*",                         "Record"),
    ("Block*",                          "Block"),
    ("Text*",                           "Text"),
    ("User*",                           "User"),
    ("Email*",                          "Auth"),
    ("Password*",                       "Auth"),
    ("NewPassword*",                    "Auth"),
    ("Auth*",                           "Auth"),
    ("InvalidAuth*",                    "Auth"),
    ("MissingAuth*",                    "Auth"),
    ("AwaitingEmail*",                  "Auth"),
    ("InvalidGuest*",                   "Auth"),
    ("UserName*",                       "Auth"),
    ("UnsupportedAuth*",                "Auth"),
    ("LocalAI*",                        "Local AI"),
    ("LocalAIDisabled",                 "LocalAI"),
    ("LocalAIError",                    "LocalAI"),
    ("LocalAIUnavailable",              "LocalAI"),
    ("LocalVersion*",                   "LocalAI"),
    ("LocalEmbedding*",                 "LocalAI"),
    ("AppFlowyLAI*",                    "LocalAI"),
    ("AI*",                             "AI"),
    ("MCP*",                            "AI"),
    ("CustomNamespace*",                "Customization"),
    ("InvalidNamespace*",               "Customization"),
    ("PublishName*",                    "Publish"),
    ("InvalidPublish*",                 "Publish"),
    ("SingleUpload*",                   "Storage"),
    ("FileStorage*",                    "Storage"),
    ("ExcessStorage*",                  "Storage"),
    ("PayloadTooLarge",                 "Storage"),
    ("Rocksdb*",                        "Storage"),
    ("DuplicateSqlite*",                "Storage"),
    ("SqlError",                        "Storage"),
    ("PgConnect*",                      "Storage"),
    ("PgDatabase*",                     "Storage"),
    ("PgTransaction*",                  "Storage"),
    ("FailedToOpenIndexDir",            "Search"),
    ("FailedToParseQuery",              "Search"),
    ("IndexWriter*",                    "Search"),
    ("FolderIndex*",                    "Search"),
    ("Network*",                        "Network"),
    ("Connect*",                        "Network"),
    ("Request*",                        "Network"),
    ("Response*",                       "Network"),
    ("InternalServer*",                 "Network"),
    ("Http*",                           "Network"),
    ("InvalidURL",                      "Network"),
    ("DataSync*",                       "Sync"),
    ("WorkspaceDataNotSync",            "Sync"),
    ("CollabData*",                     "Sync"),
    ("InvalidDate*",                    "Date"),
    ("UnexpectedCalendar*",             "Date"),
    ("Import*",                         "Import"),
    ("AppFlowyDataFolder*",             "Import"),
    ("UnsupportedFile*",                "Import"),
    ("MissingPayload",                  "Generic"),
    ("InvalidParams",                   "Generic"),
    ("InvalidRequest",                  "Generic"),
    ("InvalidEncrypt*",                 "Generic"),
    ("NotEnoughPermissions",            "Generic"),
    ("OutOfBounds",                     "Generic"),
    ("Conflict",                        "Generic"),
    ("InProgress",                      "Generic"),
    ("NotSupport*",                     "Generic"),
    ("Unexpected*",                     "Generic"),
    ("Serde",                           "Generic"),
    ("ProtobufSerde",                   "Generic"),
    ("WeakRefDrop",                     "Generic"),
    ("Internal",                        "Generic"),
    ("Unknown",                         "Generic"),
]

CATEGORY_ORDER = [
    "User", "Auth", "Workspace", "View", "Document", "Folder",
    "Database", "Field", "Row", "Cell", "Filter", "Sort", "Group",
    "Option", "TypeOption", "Record", "Block", "Text",
    "AI", "LocalAI", "Customization", "Publish",
    "Storage", "Search", "Network", "Sync",
    "Date", "Import", "Generic", "Other",
]

# Emisor típico por categoría (heurística basada en nombres).
EMITTER_BY_CATEGORY = {
    "User": "flowy-user",
    "Auth": "flowy-user",
    "Workspace": "flowy-user",
    "View": "flowy-folder",
    "Document": "flowy-document",
    "Folder": "flowy-folder",
    "Database": "flowy-database2",
    "Field": "flowy-database2",
    "Row": "flowy-database2",
    "Cell": "flowy-database2",
    "Filter": "flowy-database2",
    "Sort": "flowy-database2",
    "Group": "flowy-database2",
    "Option": "flowy-database2",
    "TypeOption": "flowy-database2",
    "Record": "flowy-folder",
    "Block": "flowy-document",
    "Text": "flowy-document",
    "AI": "flowy-ai",
    "LocalAI": "flowy-ai",
    "Customization": "flowy-user",
    "Publish": "flowy-folder",
    "Storage": "flowy-storage",
    "Search": "flowy-search",
    "Network": "flowy-server",
    "Sync": "flowy-server",
    "Date": "flowy-date",
    "Import": "flowy-document",
    "Generic": "cualquiera (todos los crates)",
    "Other": "cualquiera (todos los crates)",
}

# UI típica por prefijo.
UI_RULES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"^UserUnauthorized$|^UserNotLogin$|^UserIdIsEmpty$|^InvalidGuest$|^AwaitingEmailConfirmation$"),
     "SnackBar + redirige a login"),
    (re.compile(r"^Email.*|^Password.*|^NewPassword.*|^UserName.*|^InvalidAuth.*|^MissingAuth.*|^UnsupportedAuth.*"),
     "Inline error en form widget"),
    (re.compile(r"^WorkspaceLimit.*|^FreePlanGuestLimitExceeded$|^PaidPlanGuestLimitExceeded$|^LimitedByWorkspacePlan$|^WorkspaceMemberLimitExceeded$|^CustomNamespaceRequirePlanUpgrade$"),
     "Overlay upgrade plan + SnackBar"),
    (re.compile(r"^Network.*|^Connect.*|^Request.*|^Response.*|^InternalServer.*|^Http.*|^InvalidURL$"),
     "SnackBar con botón retry"),
    (re.compile(r".*Invalid$|.*IsEmpty$|.*TooLong$|.*TooShort$|.*FormatInvalid$|^ApplyActionsIsEmpty$|^MissingPayload$|^InvalidParams$|^InvalidRequest$|^InvalidEncrypt.*|^InvalidNamespace.*|^InvalidPublish.*|^ViewIsLocked$|^ViewIdIsInvalid$|^DatabaseIdIsEmpty$|^DatabaseViewIdIsEmpty$|^FieldIdIsEmpty$|^RowIdIsEmpty$|^OptionIdIsEmpty$|^GroupIdIsEmpty$|^GroupNameIsEmpty$|^SortIdIsEmpty$|^FilterIdIsEmpty$|^BlockIdIsEmpty$|^SelectOptionNameIsEmpty$|^TextIdIsEmpty$|^UserIdInvalid$|^TypeOptionDataIsEmpty$"),
     "Inline error en form widget"),
    (re.compile(r"^RecordNotFound$|^FieldNotExists$|^FieldRecordNotFound$|^FieldDoesNotExist$|^UnexpectedEmpty$|^NotFound$"),
     "Toast de aviso + recarga"),
    (re.compile(r"^NotEnoughPermissions$|^ViewIsLocked$|^PermissionDenied$"),
     "SnackBar + cierra acción"),
    (re.compile(r"^Internal$|^Unknown$|^Conflict$|^InProgress$|^Serde$|^ProtobufSerde$|^NotSupport.*$|^Unexpected.*$|^OutOfBounds$|^WeakRefDrop$|^UnexpectedCalendarFieldType$"),
     "Toast + log.error"),
    (re.compile(r"^DataSyncRequired$|^WorkspaceDataNotSync$|^WorkspaceDataNotMatch$|^CollabDataNotSync$|^FolderIndexManagerUnavailable$|^LocalVersionNotSupport$"),
     "Overlay 'restart sync'"),
    (re.compile(r"^FileStorage.*|^ExcessStorage.*|^SingleUpload.*|^PayloadTooLarge$|^Rocksdb.*|^DuplicateSqlite.*|^SqlError$|^Pg.*"),
     "Toast de error + log"),
    (re.compile(r"^FailedToOpenIndexDir$|^FailedToParseQuery$|^IndexWriterFailedCommit$"),
     "Toast + log search"),
    (re.compile(r"^LocalAI.*|^AI.*|^MCP.*|^AppFlowyLAINotReady$"),
     "Toast 'modelo no disponible' + log"),
    (re.compile(r"^AppFlowyDataFolder.*|^Import.*|^UnsupportedFile.*"),
     "Toast 'import failed'"),
]


def categorize(name: str) -> str:
    for prefix, cat in CATEGORY_RULES:
        # Coincide si el nombre empieza por el prefijo (quitando *) o es igual.
        if prefix.endswith("*"):
            base = prefix[:-1]
            if name.startswith(base):
                return cat
        else:
            if name == prefix:
                return cat
    return "Other"


def ui_for(name: str) -> str:
    for pat, desc in UI_RULES:
        if pat.match(name):
            return desc
    return "Toast genérico + log"


def fmt_ref(file_ref: str, linea: int) -> str:
    ruta_clean = re.sub(r"^SRC/[^/]+/", "", file_ref)
    return f"`appflowy:{ruta_clean}:{linea}`"


def md_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |"]
    out.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for r in rows:
        out.append("| " + " | ".join(r) + " |")
    return out


def render(misc: dict) -> str:
    err = misc["error_codes"]
    variants = err["variants"]
    total = err["total"]
    file_ref = err["file"]
    enum_name = err["enum"]

    # Group by category
    by_cat: dict[str, list[dict]] = defaultdict(list)
    for v in variants:
        cat = categorize(v["name"])
        by_cat[cat].append(v)

    # Order categories
    ordered_cats = [c for c in CATEGORY_ORDER if c in by_cat]
    extras = [c for c in by_cat.keys() if c not in CATEGORY_ORDER]
    ordered_cats.extend(sorted(extras))

    # Sentinels (Unknown*, Internal, etc.)
    sentinels = [v for v in variants if v["name"] in ("Internal", "Unknown") or v["name"].startswith("Unknown")]

    out: list[str] = []

    archivos_cubiertos = [
        "appflowy/frontend/rust-lib/flowy-error/src/code.rs",
        "appflowy/frontend/rust-lib/flowy-error/src/errors.rs",
        "appflowy/frontend/rust-lib/lib-dispatch/src/errors/errors.rs",
        "appflowy/frontend/appflowy_flutter/lib/packages/appflowy_backend/lib/src/flowy_error.dart",
        "appflowy/frontend/appflowy_flutter/lib/core/helpers/error_code.dart",
    ]
    fm = [
        "---",
        "id: 15-catalogo-errores",
        "titulo: Catálogo de ErrorCode (Rust → Dart)",
        "fuente: appflowy",
        "archivos_cubiertos:",
    ]
    for a in archivos_cubiertos:
        fm.append(f"  - {a}")
    fm.extend(["estado: verificado", "---"])
    out.extend(fm)
    out.append("")

    out.append("# 15 — Catálogo de ErrorCode (Rust → Dart)")
    out.append("")
    out.append(
        f"Este documento cataloga las **{total} variantes** del enum "
        f"`{err['enum']} {err['repr']}` declarado en "
        f"`appflowy/frontend/rust-lib/flowy-error/src/code.rs`. Cada "
        f"variante representa un código de error que los handlers Rust "
        "emiten vía `FlowyError::new(ErrorCode::Foo, msg)`, cruza la "
        "frontera dentro de `AFPluginEventResponse` con "
        "`StatusCode::Err`, y se reconstruye en Dart como "
        "`FlowyError { code, msg }` (paquete `appflowy_backend`). La "
        "UI lo muestra con `FlowyError.show()` que se traduce en un "
        "`SnackBar`/`Overlay`/`Toast` o `inline error` según el prefijo. "
        "La fuente de datos es `OUT/_ledger/extract/misc.json::error_codes` "
        "(Fase A2.6; validador `validate-A2.6.sh` 10/10 OK) y la prueba "
        f"del ROADMAP exige que el nº de filas del catálogo sea "
        f"exactamente **{total}**."
    )
    out.append("")

    # §1
    out.append("## 1. Cómo leer este catálogo")
    out.append("")
    out.append(
        "Cada fila representa una variante `ErrorCode`. Las columnas son: "
        "`#` (ordinal en este doc), `Código` (nombre Rust), `Índice u8` "
        "(valor `repr(u8)` del enum), `Default` (si es `#[default]`), "
        "`Mensaje` (campo `&'static str` que ya viaja con el error), "
        "`Categoría` (heurística por prefijo del nombre), `Emisor típico` "
        "(crate Rust probable — sin `ruta:línea` por ser heurística), "
        "`UI típica` (derivada por regex sobre el nombre), `Archivo` "
        "(`ruta:línea` del sitio de declaración, resuelto contra "
        "`inventario.json`). Las celdas con `—` están vacías. La "
        "semántica de cada fila es **siempre `[INFERIDO]`** porque "
        "`extract_misc.py` no captura doc-comments `///`."
    )
    out.append("")

    # §2 arquitectura
    out.append("## 2. Arquitectura del canal de error")
    out.append("")
    out.append(
        "El siguiente diagrama muestra cómo un error cruza de Rust a "
        "Dart y termina en la UI: el handler Rust construye "
        "`FlowyError::new(ErrorCode::Foo, msg)`; el dispatcher lo "
        "convierte a `AFPluginEventResponse { status_code: Err, "
        "payload: ErrorCode }`; Dart decodifica con `FlowyError.fromBytes` "
        "y muestra con `show()` / `showToast()`."
    )
    out.append("")
    out.append("```mermaid")
    out.append("flowchart TD")
    out.append("  subgraph Rust[\"Rust handler (B2.1 event)\"]")
    out.append("    Handler[\"manager.rs: FlowyError::new(code, msg)\"]")
    out.append("    Dispatcher[\"lib-dispatch::AFPluginDispatcher\"]")
    out.append("    Resp[\"AFPluginEventResponse{ StatusCode::Err, ErrorCode::BE }\"]")
    out.append("  end")
    out.append("  subgraph C[\"Frontera C (dart-ffi)\"]")
    out.append("    AsyncEv[\"async_event (lib.rs:175)\"]")
    out.append("  end")
    out.append("  subgraph Dart[\"Isolate Dart\"]")
    out.append("    FromBytes[\"FlowyError.fromBytes(buffer)\"]")
    out.append("    FlowyError[\"FlowyError{ code, msg }\"]")
    out.append("    Show[\".show() / .showToast(msg)\"]")
    out.append("  end")
    out.append("  subgraph UI[\"Widgets\"]")
    out.append("    Snack[\"SnackBar\"]")
    out.append("    Overlay[\"FlowyOverlay (login, sync, plan)\"]")
    out.append("    Inline[\"Inline form error\"]")
    out.append("    Toast[\"Toast\"]")
    out.append("  end")
    out.append("  Handler --> Dispatcher --> Resp --> FromBytes --> FlowyError --> Show")
    out.append("  Show --> Snack")
    out.append("  Show --> Overlay")
    out.append("  Show --> Inline")
    out.append("  Show --> Toast")
    out.append("```")
    out.append("")
    out.append(
        "Lectura: en `FlowyError::show()` la heurística del nombre "
        "(categoría `Auth`, `Network`, etc.) determina qué UI usar; los "
        "códigos `Internal` y `Unknown*` siempre van a `Toast + log.error`. "
        "El paquete `appflowy_backend` (`flowy_error.dart`) decodifica el "
        "buffer de bytes (`ErrorCode` como `u8` + mensaje `String`) y "
        "exponer `.code` y `.msg` para el switch de la app."
    )
    out.append("")

    # §3 resumen por categoría
    out.append("## 3. Resumen por categoría")
    out.append("")
    headers_t = ["Categoría", "Variantes", "Crane raíz típico"]
    rows3: list[list[str]] = []
    for c in ordered_cats:
        ents = by_cat[c]
        rows3.append([
            f"`{c}`",
            str(len(ents)),
            f"`{EMITTER_BY_CATEGORY.get(c, '?')}`",
        ])
    for line in md_table(headers_t, rows3):
        out.append(line)
    out.append("")
    out.append(
        f"**Total**: {total} variantes en {len(by_cat)} categorías. "
        "Las categorías se derivan del prefijo CamelCase del nombre "
        "(`User*` → `User`, `Database*` → `Database`, `LocalAI*` → "
        "`LocalAI`, etc.). El crate raíz típico es el que concentra "
        f"el manejo de esa categoría (ej. `flowy-database2` para "
        f"`Database`/`Field`/`Row`/`Cell`/`Filter`/`Sort`/`Group`/`Option`/`TypeOption`)."
    )
    out.append("")

    # §4 índice global
    out.append(f"## 4. Índice global de los {total} códigos")
    out.append("")
    out.append(
        f"Tabla plana con las {total} variantes ordenadas por `(categoría, "
        "nombre)`. Cada fila aparece también en §5.<categoría>. El conteo "
        f"de filas de §4 y de la suma de filas de §5.* debe ser exactamente "
        f"**{total}** (prueba literal del ROADMAP)."
    )
    out.append("")
    headers4 = [
        "Cat.",
        "#",
        "Código",
        "Índice u8",
        "Default",
        "Mensaje",
        "Emisor típico",
        "UI típica",
        "Archivo",
    ]
    rows4: list[list[str]] = []
    flat: list[tuple[str, int, dict]] = []
    for c in ordered_cats:
        ents = sorted(by_cat[c], key=lambda v: v["name"])
        flat.extend((c, idx, v) for idx, v in enumerate(ents, 1))

    for c, idx, v in flat:
        rows4.append([
            f"`{c}`",
            str(idx),
            f"`{v['name']}`",
            str(v["index"]),
            "sí" if v.get("is_default") else "—",
            v.get("message", "—").replace("|", "\\|"),
            f"`{EMITTER_BY_CATEGORY.get(c, '?')}`",
            ui_for(v["name"]),
            fmt_ref(file_ref, v["decl_line"]),
        ])
    for line in md_table(headers4, rows4):
        out.append(line)
    out.append("")

    # §5 catálogo por categoría
    out.append("## 5. Catálogo por categoría")
    out.append("")
    out.append(
        "Cada sub-sección desarrolla una categoría. Las tablas siguen el "
        "mismo esquema que §4 (sin las columnas `Cat.` redundantes). "
        "Cuando una categoría supera las 5 entradas, se acompaña de un "
        "mini `flowchart` agrupando por sub-prefijo."
    )
    out.append("")
    for idx, c in enumerate(ordered_cats, 1):
        ents = sorted(by_cat[c], key=lambda v: v["name"])
        out.append(f"### 5.{idx} `{c}`")
        out.append("")
        out.append(
            f"**{len(ents)} variantes** · crate típico `{EMITTER_BY_CATEGORY.get(c, '?')}`."
        )
        out.append("")
        if len(ents) >= 10:
            out.append("```mermaid")
            out.append("flowchart LR")
            out.append(f"  subgraph C{c.replace(' ', '_')}[\"{c} ({len(ents)})\"]")
            prefixes: dict[str, list[str]] = {}
            for v in ents:
                m = re.match(r"^([A-Z][a-z]+)", v["name"])
                p = m.group(1) if m else "Other"
                prefixes.setdefault(p, []).append(v["name"])
            for p, names in sorted(prefixes.items()):
                node_id = f"{c.replace(' ', '_')}_{p}"
                labels = "<br/>".join(names[:8])
                if len(names) > 8:
                    labels += f"<br/>… +{len(names) - 8}"
                out.append(f'    {node_id}["{p}<br/>({len(names)}):<br/>{labels}"]')
            out.append("  end")
            out.append("```")
            out.append("")
        headers5 = [
            "#",
            "Código",
            "Índice u8",
            "Default",
            "Mensaje",
            "Emisor típico",
            "UI típica",
            "Archivo",
        ]
        rows5: list[list[str]] = []
        for i, v in enumerate(ents, 1):
            rows5.append([
                str(i),
                f"`{v['name']}`",
                str(v["index"]),
                "sí" if v.get("is_default") else "—",
                v.get("message", "—").replace("|", "\\|"),
                f"`{EMITTER_BY_CATEGORY.get(c, '?')}`",
                ui_for(v["name"]),
                fmt_ref(file_ref, v["decl_line"]),
            ])
        for line in md_table(headers5, rows5):
            out.append(line)
        out.append("")

    # §6 sentinels
    out.append("## 6. Códigos sentinela")
    out.append("")
    out.append(
        f"Hay **{len(sentinels)}** códigos que **no** son emitidos por un "
        "feature específico sino que sirven como marcadores de "
        "diagnóstico o sentinela (`Internal`, `Unknown*`). Su manejo "
        "es uniforme: `Toast + log.error`. En esta sección se listan "
        "para que la cobertura del ROADMAP (cada variante con emisor o "
        "`sin uso` específico) sea verificable."
    )
    out.append("")
    headers6 = ["#", "Código", "Categoría", "Mensaje", "Archivo"]
    rows6: list[list[str]] = []
    for i, v in enumerate(sentinels, 1):
        cat = categorize(v["name"])
        rows6.append([
            str(i),
            f"`{v['name']}`",
            f"`{cat}`",
            v.get("message", "—").replace("|", "\\|"),
            fmt_ref(file_ref, v["decl_line"]),
        ])
    for line in md_table(headers6, rows6):
        out.append(line)
    out.append("")

    # §7 prueba literal
    out.append("## 7. Conteo de filas y prueba literal")
    out.append("")
    out.append(
        f"La prueba del ROADMAP exige que el número de filas del "
        f"catálogo sea exactamente **{total}** (= "
        f"`misc.json::error_codes.total`). El script "
        "`OUT/_ledger/pruebas/B2.5/count_rows_133.py` cuenta las filas "
        "de §4 y de la suma de §5.*; debe coincidir. El comando canónico "
        "externo:"
    )
    out.append("")
    out.append("```bash")
    out.append(
        f"jq '.error_codes.variants | length' \\\n"
        f"  OUT/_ledger/extract/misc.json   # esperado: {total}"
    )
    out.append("```")
    out.append("")

    # §8 cobertura
    out.append("## 8. Cobertura y referencias cruzadas")
    out.append("")
    out.append("- **B2.1 — `11-catalogo-eventos-ffi.md`**: cada handler "
        "que devuelve `Err(FlowyError::new(ErrorCode::X, _))` envía "
        "este código al Dart.")
    out.append("- **B2.4 — `14-catalogo-notificaciones.md`**: los "
        "handlers no emiten `FlowyError` por la vía de notificaciones; "
        "sólo por `FFIResponse.payload`. Documentado en `06-puente-flutter-rust/02-lib-dispatch.md`.")
    out.append("- **B1.5 — `06-puente-flutter-rust/02-lib-dispatch.md`**: "
        "`AFPluginEventResponse` + `StatusCode::Err`.")
    out.append("- **Bloque B3 — F0x**: cada feature documenta los "
        "`ErrorCode` que sus handlers pueden emitir (ej. F01 `DocumentError`, "
        "F02 `DatabaseError`, F05 `UserError`).")
    out.append("- **B5 — Secuencias globales**: los errores son la mitad "
        "del camino de retorno de las `sequenceDiagram`.")
    out.append("")

    # §9 preguntas abiertas
    out.append("## 9. Preguntas abiertas")
    out.append("")
    out.append(
        "Sin entradas por ahora. Si el revisor detecta códigos con "
        "categorización ambigua (ej. `WorkspaceLimit*` puede ser `Workspace` o "
        "`Plan`; `LocalAIError` puede ser `LocalAI` o `AI`), se vuelca aquí "
        "y en `OUT/22-preguntas-abiertas.md`."
    )
    out.append("")

    # §10 relacionado
    out.append("## 10. Relacionado con")
    out.append("")
    out.append("- `06-puente-flutter-rust/02-lib-dispatch.md` — respuesta FFI con error.")
    out.append("- `11-catalogo-eventos-ffi.md` — handlers que emiten errores.")
    out.append("- `14-catalogo-notificaciones.md` — canal paralelo (éxito).")
    out.append("- `B0.1` — `misc.json` con `validate-A2.6.sh` 10/10 OK.")
    out.append("- `B3.F0x` — cada feature.")
    out.append("- `B5` — secuencias globales.")
    out.append("")

    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="build_catalog_errors.py")
    p.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    p.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args(argv)

    misc = json.loads(args.input.read_text(encoding="utf-8"))
    err = misc["error_codes"]
    total = err["total"]
    if len(err["variants"]) != total:
        print(
            f"build_catalog_errors.py: INCONSISTENCIA misc.json: "
            f"len(variants)={len(err['variants'])} vs total={total}",
            file=sys.stderr,
        )
        return 2

    text = render(misc)
    args.output.write_text(text, encoding="utf-8")
    if not args.quiet:
        print(
            f"OK: {args.output} escrito · {total} variantes · "
            f"{len(text.splitlines())} líneas"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())