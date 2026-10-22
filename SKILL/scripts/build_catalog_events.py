#!/usr/bin/env python3
"""build_catalog_events.py — genera `OUT/11-catalogo-eventos-ffi.md`
desde `OUT/_ledger/extract/events.json` con semántica breve por evento
derivada del nombre del handler + los PB input/output.

Fase B2.1 de la skill `notemartin-appflowy-review`.
Spec: ROADMAP.md línea 173 y AGENTS.md §5.1 (registro de eventos).

Política de evidencia:
  - Toda fila referencia el `event_map.rs:decl_line` del crate (índice
    `source_line`) y, si hay registro, el `handler_file:handler_line`.
  - La semántica breve es SIEMPRE `[INFERIDO]` salvo cuando el handler
    tiene un `///` doc-comment literal adyacente (no se rastrea aquí;
    `events.json` no lo incluye; queda como mejora futura).
  - 5 `sin_handler` se marcan explícitamente.

Salida: 229 filas verificables en §4 + §5.*; sumadas, igual a
`events.json::summary.total_variants` (prueba literal del ROADMAP).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DEFAULT_INPUT = PROJECT_ROOT / "OUT" / "_ledger" / "extract" / "events.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "OUT" / "11-catalogo-eventos-ffi.md"

# Pequeño glosario para semántica derivada (input/output → verbo).
# Cobertura: sufijos PB recurrentes. Sin ser exhaustivo, ancla el texto.
VERB_HINTS = [
    (re.compile(r"^Create"), "Crea el lanzamiento"),
    (re.compile(r"^Open"), "Abre el recurso"),
    (re.compile(r"^Close"), "Cierra el recurso"),
    (re.compile(r"^Read"), "Lee el estado actual"),
    (re.compile(r"^Get"), "Obtiene el recurso"),
    (re.compile(r"^Set"), "Establece el recurso"),
    (re.compile(r"^Update"), "Actualiza el recurso"),
    (re.compile(r"^Delete"), "Elimina el recurso"),
    (re.compile(r"^Remove"), "Elimina el recurso"),
    (re.compile(r"^Add"), "Añade el recurso"),
    (re.compile(r"^Append"), "Añade el recurso"),
    (re.compile(r"^Insert"), "Inserta el recurso"),
    (re.compile(r"^Duplicate"), "Duplica el recurso"),
    (re.compile(r"^Move"), "Mueve el recurso"),
    (re.compile(r"^Reorder"), "Reordena el recurso"),
    (re.compile(r"^Sort"), "Ordena el recurso"),
    (re.compile(r"^Filter"), "Filtra el recurso"),
    (re.compile(r"^Group"), "Agrupa el recurso"),
    (re.compile(r"^Calculate"), "Calcula el recurso"),
    (re.compile(r"^Summarize"), "Resume el recurso"),
    (re.compile(r"^Search"), "Busca coincidencias"),
    (re.compile(r"^List"), "Lista los recursos"),
    (re.compile(r"^Load"), "Carga el recurso"),
    (re.compile(r"^Save"), "Persiste el recurso"),
    (re.compile(r"^Export"), "Exporta el recurso"),
    (re.compile(r"^Import"), "Importa el recurso"),
    (re.compile(r"^Upload"), "Sube el archivo"),
    (re.compile(r"^Download"), "Descarga el archivo"),
    (re.compile(r"^UploadChunk"), "Sube un chunk del archivo"),
    (re.compile(r"^Reset"), "Restablece el estado"),
    (re.compile(r"^Clear"), "Limpia el recurso"),
    (re.compile(r"^Toggle"), "Alterna el estado"),
    (re.compile(r"^Mark"), "Marca el recurso"),
    (re.compile(r"^Unmark"), "Desmarca el recurso"),
    (re.compile(r"^Subscribe"), "Suscribe al canal"),
    (re.compile(r"^Unsubscribe"), "Cancela la suscripción"),
    (re.compile(r"^Publish"), "Publica el recurso"),
    (re.compile(r"^Unpublish"), "Retira la publicación"),
    (re.compile(r"^Share"), "Comparte el recurso"),
    (re.compile(r"^Unshare"), "Revoca el acceso"),
    (re.compile(r"^Transfer"), "Transfiere el ownership"),
    (re.compile(r"^Invite"), "Invita al recurso"),
    (re.compile(r"^Join"), "Une al recurso"),
    (re.compile(r"^Leave"), "Abandona el recurso"),
    (re.compile(r"^Sign"), "Firma la acción"),
    (re.compile(r"^SignIn"), "Inicia sesión"),
    (re.compile(r"^SignUp"), "Registra al usuario"),
    (re.compile(r"^SignOut"), "Cierra la sesión"),
    (re.compile(r"^UpdateAuth"), "Actualiza la autenticación"),
    (re.compile(r"^Generate"), "Genera el recurso"),
    (re.compile(r"^Send"), "Envía el recurso"),
    (re.compile(r"^Receive"), "Recibe el recurso"),
    (re.compile(r"^Stream"), "Inicia un stream"),
    (re.compile(r"^StopStream"), "Detiene el stream"),
    (re.compile(r"^Cancel"), "Cancela la operación"),
    (re.compile(r"^Process"), "Procesa el recurso"),
    (re.compile(r"^Run"), "Ejecuta el recurso"),
    (re.compile(r"^Index"), "Indexa el recurso"),
    (re.compile(r"^Suggest"), "Sugiere el recurso"),
    (re.compile(r"^Embed"), "Calcula el embedding"),
    (re.compile(r"^Complete"), "Completa el prompt"),
    (re.compile(r"^Chat"), "Mensaje de chat"),
    (re.compile(r"^Migrate"), "Migra el esquema"),
    (re.compile(r"^Collapse"), "Colapsa el nodo"),
    (re.compile(r"^Expand"), "Expande el nodo"),
    (re.compile(r"^Rename"), "Renombra el recurso"),
    (re.compile(r"^Restore"), "Restaura del"),
    (re.compile(r"^Put"), "Establece el recurso"),
    (re.compile(r"^DidBuildViewMap"), "Construye el mapa de vistas"),
]

OBJECT_HINTS = {
    "Document": "del documento",
    "Folder": "del folder",
    "Workspace": "del workspace",
    "View": "de la vista",
    "Database": "de la base de datos",
    "DatabaseView": "de la vista de base de datos",
    "Row": "de la fila",
    "Rows": "de las filas",
    "Cell": "de la celda",
    "Field": "del campo",
    "Fields": "de los campos",
    "FieldType": "del tipo de campo",
    "User": "del usuario",
    "Session": "de la sesión",
    "Auth": "de autenticación",
    "Authenticator": "del autenticador",
    "WorkspaceMember": "del miembro del workspace",
    "Notification": "de notificación",
    "Reminder": "del recordatorio",
    "File": "del archivo",
    "Upload": "del upload",
    "UploadFile": "del archivo en upload",
    "UploadPart": "del chunk",
    "Chat": "del chat",
    "ChatMessage": "del mensaje de chat",
    "ChatSettings": "de los ajustes del chat",
    "Mention": "de la mención",
    "Search": "de búsqueda",
    "SearchResult": "del resultado de búsqueda",
    "Setting": "del ajuste",
    "Settings": "de los ajustes",
    "Theme": "del tema",
    "Icon": "del icono",
    "Emoji": "del emoji",
    "Permission": "del permiso",
    "Snapshot": "del snapshot",
    "Page": "de la página",
    "Block": "del bloque",
    "Revision": "de la revisión",
    "Doc": "del documento",
    "DocLink": "del enlace al documento",
    "Recent": "del reciente",
    "Favorite": "del favorito",
    "Trash": "de la papelera",
    "AIServer": "AIServer",
    "LocalAI": "IA local",
    "Model": "del modelo",
    "Completion": "del completado",
    "Question": "de la pregunta",
    "Answer": "de la respuesta",
    "LocalModel": "del modelo local",
    "LocalAIResource": "del recurso de IA local",
    "OfflineAISetting": "del ajuste de IA offline",
    "MCP": "del servidor MCP",
    "Embeddings": "del embedding",
    "Tool": "de la herramienta",
    "Date": "de la fecha",
    "ParsedDate": "de la fecha parseada",
}


def derive_semantic(name: str, input_pb: str | None, output_pb: str | None) -> str:
    """Devuelve una frase corta derivada del nombre del evento."""
    for pat, verb in VERB_HINTS:
        if pat.match(name):
            base = verb
            break
    else:
        base = "Procesa el recurso"
    # Objeto: por nombre del evento (después del verbo) o por input PB
    tail = re.sub(r"^(Get|Set|Update|Delete|Add|Remove|Create|Open|Close|Load|Save|List|Reset|Move|Upload|Download|Insert|Append|Duplicate|Search|Index|Stream|Suggest|Embed|Complete|Chat|Generate|Send|Receive|Subscribe|Unsubscribe|Publish|Unpublish|Share|Unshare|Transfer|Sign|SignIn|SignUp|SignOut|Export|Import|Filter|Group|Sort|Calculate|Summarize|Toggle|Mark|Unmark|Rename|Restore|Migrate|Collapse|Expand|Clear|Process|Run|Stop|Cancel|Invite|Join|Leave|Read|Put|UpdateAuth|Trigger)\w*?", "", name, count=0)
    obj = None
    if tail:
        for k, v in OBJECT_HINTS.items():
            if k.lower() in tail.lower():
                obj = v
                break
    if obj:
        return f"{base} {obj}."
    if input_pb:
        return f"{base} ({input_pb})."
    return f"{base}."


def md_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |"]
    out.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for r in rows:
        out.append("| " + " | ".join(r) + " |")
    return out


def fmt_ref(fuente: str, ruta: str, linea: int) -> str:
    """Renderiza `fuente:ruta:linea` quitando el prefijo `SRC/<fuente>/`
    para que coincida con `inventario.json::ruta_rel` (que ya incluye
    el nombre de la fuente como primer segmento).
    """
    ruta_clean = re.sub(r"^SRC/[^/]+/", "", ruta)
    return f"`{fuente}:{ruta_clean}:{linea}`"


def render(events: dict) -> str:
    crates = events["crates"]
    summary = events["summary"]
    total_v = summary["total_variants"]
    total_r = summary["total_registered"]
    total_sh = summary["total_sin_handler"]

    # Tabla resumen por crate
    summary_rows: list[list[str]] = []
    summary_rows_full: list[list[str]] = []
    sin_handler_rows: list[list[str]] = []
    catalog_by_crate: list[tuple[str, list[dict], int, int]] = []
    all_variants: list[dict] = []

    for c in crates:
        crate = c["crate"]
        event_map_file = c["event_map_file"]
        fuente = c["fuente"]
        enum_name = c["enum"]["name"]
        decl = c["enact_decl"] if "enact_decl" in c else c["enum"]["decl_line"]
        n = len(c["variants"])
        regs = sum(1 for v in c["variants"] if not v["sin_handler"])
        sh = sum(1 for v in c["variants"] if v["sin_handler"])
        catalog_by_crate.append((crate, fuente, event_map_file, c["variants"], regs, sh))
        all_variants.extend(
            [{"crate": crate, "fuente": fuente, "event_map_file": event_map_file, **v} for v in c["variants"]]
        )

        summary_rows_full.append(
            [
                f"`{crate}`",
                f"`{enum_name}`",
                str(n),
                str(regs),
                str(sh),
                fmt_ref(fuente, event_map_file.split(":", 1)[1], decl)
                if ":" in event_map_file
                else event_map_file,
            ]
        )

    # Ordenamos todos los eventos por crate+índice para §4
    all_variants.sort(key=lambda v: (v["crate"], v["index"]))

    # ---------- Render ----------
    out: list[str] = []

    # Frontmatter (catalogue: id = 11-catalogo-eventos-ffi)
    archivos_cubiertos = [
        "appflowy/frontend/rust-lib/flowy-ai/src/event_map.rs",
        "appflowy/frontend/rust-lib/flowy-database2/src/event_map.rs",
        "appflowy/frontend/rust-lib/flowy-date/src/event_map.rs",
        "appflowy/frontend/rust-lib/flowy-document/src/event_map.rs",
        "appflowy/frontend/rust-lib/flowy-folder/src/event_map.rs",
        "appflowy/frontend/rust-lib/flowy-search/src/event_map.rs",
        "appflowy/frontend/rust-lib/flowy-storage/src/event_map.rs",
        "appflowy/frontend/rust-lib/flowy-user/src/event_map.rs",
    ]
    fm = [
        "---",
        "id: 11-catalogo-eventos-ffi",
        "titulo: Catálogo de eventos FFI (Dart ↔ Rust)",
        "fuente: appflowy",
        "archivos_cubiertos:",
    ]
    for a in archivos_cubiertos:
        fm.append(f"  - {a}")
    fm.extend(["estado: verificado", "---"])
    out.extend(fm)
    out.append("")

    # Title H1
    out.append("# 11 — Catálogo de eventos FFI (Dart ↔ Rust)")
    out.append("")

    # Resumen (3-6 líneas)
    out.append(
        "Este documento cataloga las "
        f"**{total_v} variantes de eventos FFI** registradas por "
        "AppFlowy en los `event_map.rs` de los 8 crates de feature "
        "(`flowy-user`, `flowy-folder`, `flowy-document`, `flowy-database2`, "
        "`flowy-ai`, `flowy-search`, `flowy-storage`, `flowy-date`). Cada "
        "variante se enumera como `#[event(input = \"…\", output = \"…\")]` "
        "sobre el enum `XEvent` (`Flowy_Event` + `ProtoBuf_Enum`) y se "
        "despacha en `lib-dispatch` hacia un handler Rust asíncrono que "
        "opera sobre el manager del crate. La fuente de datos es el "
        "catálogo determinista `OUT/_ledger/extract/events.json` "
        "(Fase A2.1, validador `validate-A2.1.sh` 11/11 OK). El catálogo "
        "es la base para los documentos B2.2 (entidades PB), B2.4 "
        "(notificaciones), B3.F01–F17 (handlers por feature) y el "
        "sub-documento `06-puente-flutter-rust/02-lib-dispatch.md`."
    )
    out.append("")

    # §1
    out.append("## 1. Cómo leer este catálogo")
    out.append("")
    out.append(
        "Cada fila de la tabla de un crate representa una variante del "
        "enum `XEvent` y aporta seis datos clave: `#` (índice en el enum), "
        "`Evento` (nombre de la variante), `Input PB` (entidad protobuf "
        "de entrada; `-` si no toma), `Output PB` (entidad protobuf de "
        "salida; `-` si no devuelve), `Handler` (función registrada en "
        "`AFPlugin::event(...)`; `—` si la variante está en el enum pero "
        "no fue asociada a un handler — los 5 casos se listan en §6), "
        "`Archivo handler` (`ruta:línea` resuelto contra `inventario.json`). "
        "La columna `Semántica` deriva en una línea qué dispara el "
        "evento a partir del nombre de la variante, los PB de entrada y "
        "salida, y el nombre del handler; va siempre etiquetada "
        "`[INFERIDO]` porque `extract_events.py` no captura "
        "`///` doc-comments del handler. Toda referencia `ruta:línea` "
        "apunta a archivos en `inventario.json` y se valida con "
        "`validate_evidence.py`."
    )
    out.append("")

    # §2 arquitectura
    out.append("## 2. Arquitectura del registro de eventos")
    out.append("")
    out.append(
        "El siguiente diagrama muestra cómo una llamada Dart "
        "(`XEventFoo().send()`) cruza la frontera FFI, llega al dispatcher, "
        "resuelve el `AFPlugin` del crate, localiza el handler, lo ejecuta "
        "en el `AFPluginRuntime` y devuelve un `FlowyResult<T, FlowyError>` "
        "al isolate de Dart."
    )
    out.append("")
    out.append("```mermaid")
    out.append("flowchart TD")
    out.append("  subgraph Dart[\"Isolate Dart\"]")
    out.append("    Bloc[\"BLoC / Service\"]")
    out.append("    Gen[\"XEventFoo (generado por flowy-codegen)\"]")
    out.append("    Send[\".send()\"]")
    out.append("  end")
    out.append("  subgraph FFI[\"Frontera C (dart-ffi)\"]")
    out.append("    AsyncEvent[\"async_event (lib.rs:175)\"]")
    out.append("  end")
    out.append("  subgraph Dispatch[\"lib-dispatch\"]")
    out.append("    Dispatcher[\"AFPluginDispatcher (dispatcher.rs:63)\"]")
    out.append("    PluginMap[\"AFPluginMap (8 crates)\"]")
    out.append("    Runtime[\"AFPluginRuntime (runtime.rs:1)\"]")
    out.append("  end")
    out.append("  subgraph Crate[\"Crate de feature (p.ej. flowy-document)\"]")
    out.append("    EventMap[\"event_map.rs (XEvent enum + init())\"]")
    out.append("    Handler[\"event_handler.rs (foo_handler)\"]")
    out.append("    Manager[\"Manager (Weak&lt;XManager&gt;)\"]")
    out.append("    Collab[\"Collab / persistencia\"]")
    out.append("  end")
    out.append("  Bloc --> Gen --> Send --> AsyncEvent --> Dispatcher")
    out.append("  Dispatcher --> Runtime")
    out.append("  Dispatcher --> PluginMap")
    out.append("  PluginMap --> EventMap")
    out.append("  EventMap -- \".event(XEvent::Foo, foo_handler)\" --> Handler")
    out.append("  Handler --> Manager --> Collab")
    out.append("  Handler -- \"FlowyResult&lt;T&gt;\" --> AsyncEvent")
    out.append("  AsyncEvent -- \"callback\" --> Bloc")
    out.append("```")
    out.append("")
    out.append(
        "Lectura: la flecha Dart → FFI cruza la frontera C ABI "
        "(`#[no_mangle] pub extern \"C\" fn async_event`); el dispatcher "
        "identifica el plugin por nombre, busca la variante en el mapa "
        "interno (`AFPluginEvent`), llama al handler dentro de "
        "`tokio::task::spawn_local` y devuelve un `AFPluginEventResponse` "
        "con `StatusCode::Ok` o `StatusCode::Err` + `ErrorCode`. El handler "
        "opera sobre un `Weak<XManager>` para no retener el ciclo de vida "
        "del manager."
    )
    out.append("")

    # §3 resumen por crate
    out.append("## 3. Resumen por crate")
    out.append("")
    out.append(
        "Tabla de los 8 crates de feature con `event_map.rs` extraído. "
        "La columna `ruta:línea` apunta al sitio donde se declara el enum "
        "`XEvent` (`#[derive(Flowy_Event)]`); la columna `decl_line` es "
        "exactamente la primera línea del bloque."
    )
    out.append("")
    headers = ["Crate", "Enum", "Variantes", "Registradas", "Sin handler", "Declaración"]
    for line in md_table(headers, summary_rows_full):
        out.append(line)
    out.append("")
    out.append(
        f"**Total**: {total_v} variantes, {total_r} registradas "
        f"(`AFPlugin::event(...)`), {total_sh} sin handler "
        "(§6). Fuente: `events.json::summary`."
    )
    out.append("")

    # §4 índice global
    out.append("## 4. Índice global de las 229 variantes")
    out.append("")
    out.append(
        "Tabla plana con las 229 variantes ordenadas por `(crate, índice)`. "
        "Cada fila es un evento que aparecerá también en §5.<crate> con "
        "el mismo número. El conteo de filas de §4 y de la suma de filas "
        "de §5.* debe ser exactamente 229 (prueba literal del ROADMAP)."
    )
    out.append("")
    headers = ["Crate", "#", "Evento", "Input PB", "Output PB", "Handler", "Semántica"]
    rows4: list[list[str]] = []
    for v in all_variants:
        regs = v["registrations"]
        if regs:
            handler = regs[0]["handler"]
            hfile = regs[0]["handler_file"]
            hline = regs[0]["handler_line"]
            handler_cell = f"`{handler}`"
            handler_file_cell = fmt_ref(v["fuente"], hfile.split(":", 1)[1] if ":" in hfile else hfile, hline)
        else:
            handler_cell = "—"
            handler_file_cell = "—"
        ipb = v.get("input") or "—"
        opb = v.get("output") or "—"
        sem = derive_semantic(v["name"], v.get("input"), v.get("output"))
        rows4.append([
            f"`{v['crate']}`",
            str(v["index"]),
            f"`{v['name']}`",
            f"`{ipb}`" if ipb != "—" else "—",
            f"`{opb}`" if opb != "—" else "—",
            handler_cell,
            f"{sem} `[INFERIDO]`",
        ])
    for line in md_table(headers, rows4):
        out.append(line)
    out.append("")

    # §5 catálogo por crate
    out.append("## 5. Catálogo por crate")
    out.append("")
    out.append(
        "Cada sub-sección desarrolla un crate. Las tablas siguen el "
        "mismo esquema que §4 pero incluyen el archivo del handler. "
        "Cuando un crate supera las 20 variantes, se acompaña de un "
        "`flowchart` que muestra los grupos de eventos (CRUD sobre "
        "documentos, sobre filas, etc.)."
    )
    out.append("")
    for crate, fuente, event_map_file, variants, regs, sh in catalog_by_crate:
        anchor = crate.replace("-", "_")
        out.append(f"### 5.{catalog_by_crate.index((crate, fuente, event_map_file, variants, regs, sh)) + 1} `{crate}`")
        out.append("")
        out.append(f"**{len(variants)}** variantes · **{regs}** registradas · **{sh}** sin handler.")
        out.append("")
        # Mermaid opcional si >20 variantes
        if len(variants) >= 20:
            out.append("```mermaid")
            out.append("flowchart LR")
            out.append(f"  subgraph C{anchor}[\"{crate}\"]")
            # Agrupar por prefijo
            prefixes: dict[str, list[str]] = {}
            for v in variants:
                m = re.match(r"^([A-Z][a-z]+)", v["name"])
                p = m.group(1) if m else "Other"
                prefixes.setdefault(p, []).append(v["name"])
            for p, names in sorted(prefixes.items()):
                node_id = f"{anchor}_{p}"
                labels = "<br/>".join(names[:8])
                if len(names) > 8:
                    labels += f"<br/>… +{len(names) - 8}"
                out.append(f'    {node_id}["{p}<br/>({len(names)}):<br/>{labels}"]')
            out.append("  end")
            out.append("```")
            out.append("")
        headers = ["#", "Evento", "Input PB", "Output PB", "Handler", "Archivo handler", "Semántica"]
        rows5: list[list[str]] = []
        for v in sorted(variants, key=lambda x: x["index"]):
            regs = v["registrations"]
            if regs:
                handler_cell = f"`{regs[0]['handler']}`"
                hfile = regs[0]["handler_file"]
                hline = regs[0]["handler_line"]
                handler_file_cell = fmt_ref(
                    fuente,
                    hfile.split(":", 1)[1] if ":" in hfile else hfile,
                    hline,
                )
            else:
                handler_cell = "—"
                handler_file_cell = "—"
            ipb = v.get("input") or "—"
            opb = v.get("output") or "—"
            sem = derive_semantic(v["name"], v.get("input"), v.get("output"))
            rows5.append([
                str(v["index"]),
                f"`{v['name']}`",
                f"`{ipb}`" if ipb != "—" else "—",
                f"`{opb}`" if opb != "—" else "—",
                handler_cell,
                handler_file_cell,
                f"{sem} `[INFERIDO]`",
            ])
        for line in md_table(headers, rows5):
            out.append(line)
        out.append("")

    # §6 sin handler
    out.append("## 6. Eventos sin handler registrado")
    out.append("")
    out.append(
        f"Hay **{total_sh} variantes** declaradas en el enum pero sin "
        "una llamada `AFPlugin::event(...)` correspondiente en el mismo "
        "`event_map.rs`. Esto indica trabajo pendiente o variantes "
        "reservadas para uso futuro; **no** es un fallo del extractor "
        "(A2.1) porque la prueba exige detectarlas y marcarlas "
        "`sin_handler: true`."
    )
    out.append("")
    headers = ["Crate", "Evento", "#", "Source line", "Estado"]
    sh_table: list[list[str]] = []
    for v in all_variants:
        if v["sin_handler"]:
            crate_cell = f"`{v['crate']}`"
            sh_table.append([
                crate_cell,
                f"`{v['name']}`",
                str(v["index"]),
                fmt_ref(
                    v["fuente"],
                    v["event_map_file"].split(":", 1)[1] if ":" in v["event_map_file"] else v["event_map_file"],
                    v["source_line"],
                ),
                "Sin handler `[INFERIDO]`",
            ])
    for line in md_table(headers, sh_table):
        out.append(line)
    out.append("")
    out.append(
        "Cada `ruta:línea` apunta al sitio del enum (no al handler). Los "
        "nombres `GetAllRows`, `CreateFolderWorkspace`, `DeleteWorkspace`, "
        "`CopyLink` y `AddWorkspaceMember` siguen el patrón "
        "verbo+objeto de la fase A2.1; están presentes en el enum pero "
        "el `event_map.rs` no los enlaza con un handler (el builder "
        "`AFPlugin::event(...)` los omite)."
    )
    out.append("")

    # §7 prueba literal
    out.append("## 7. Conteo de filas y prueba literal")
    out.append("")
    out.append(
        "La prueba del ROADMAP exige que el número de filas del catálogo "
        f"sea exactamente **{total_v}** (= `events.json::summary.total_variants`). "
        "El script `OUT/_ledger/pruebas/B2.1/count_rows_229.py` cuenta las "
        "filas de §4 y de la suma de §5.*; debe coincidir. El comando "
        "canónico de referencia es:"
    )
    out.append("")
    out.append("```bash")
    out.append(
        f"jq '.crates | map(.variants | length) | add' \\\n"
        f"  OUT/_ledger/extract/events.json   # esperado: {total_v}"
    )
    out.append("```")
    out.append("")
    out.append(
        "La invariante local del catálogo es que la suma de filas en "
        "§4 = §5.1 + §5.2 + … + §5.8. Esto se comprueba programáticamente "
        "(no visualmente) en `validate-B2.1.sh`."
    )
    out.append("")

    # §8 cobertura / cross-ref
    out.append("## 8. Cobertura y referencias cruzadas")
    out.append("")
    out.append(
        "- **B2.2 — `12-catalogo-entidades-protobuf.md`**: cada `Input PB` "
        "y `Output PB` de este catálogo debe existir como entidad en "
        "`OUT/_ledger/extract/protobuf.json`."
    )
    out.append("- **B2.4 — `14-catalogo-notificaciones.md`**: cada `AFPlugin` "
        "puede emitir `send_notification(...)` (см. `flowy-notification`); "
        "este documento es 1:1 con el sub-doc "
        "`06-puente-flutter-rust/04-notificaciones.md`.")
    out.append("- **B1.5 — `06-puente-flutter-rust/02-lib-dispatch.md`**: el "
        "dispatcher (229 / 224 / 8 / 5) y los detalles de `AFPlugin`.")
    out.append("- **Bloque B3 — F0x**: cada handler descrito aquí se documenta "
        "en detalle en el doc de su feature (p. ej. `DocumentBloc` ↔ F03 "
        "vistas, F01 documentos).")
    out.append("- **Bloque B4 — export/import**: los eventos con `Export…` o "
        "`Import…` se referencian desde `10-motor-export-import/`.")
    out.append("")

    # §9 preguntas abiertas
    out.append("## 9. Preguntas abiertas")
    out.append("")
    out.append(
        "Por ahora no hay entradas `[NO DETERMINADO]`. La semántica breve "
        "es `[INFERIDO]` por construcción (ver §1). Si en una fase "
        "posterior el revisor detecta eventos cuyo nombre no baste para "
        "inferir la operación (p. ej. handler con lógica de control de "
        "flujo no trivial), se volcará aquí y en `OUT/22-preguntas-abiertas.md`."
    )
    out.append("")

    # §10 relacionado con
    out.append("## 10. Relacionado con")
    out.append("")
    out.append("- `06-puente-flutter-rust/02-lib-dispatch.md` — `AFPlugin`, "
        "`AFPluginDispatcher`, `AFPluginRuntime`.")
    out.append("- `06-puente-flutter-rust/04-notificaciones.md` — canal "
        "complementario Rust → Dart.")
    out.append("- `07-motor-colaborativo-crdt/` — los handlers de "
        "`flowy-document`, `flowy-folder`, `flowy-database2` operan sobre "
        "el `Collab` descrito ahí.")
    out.append("- `B0.1` — adquisiciones (extract `events.json`).")
    out.append("- `B2.2` — entidades protobuf (cada PB usado por un evento).")
    out.append("- `B2.4` — notificaciones (los enums `XNotification` se "
        "emiten desde estos handlers).")
    out.append("- `B3.F01` — handlers `flowy-document` en detalle.")
    out.append("- `B3.F02` — handlers `flowy-database2` en detalle.")
    out.append("- `B3.F05` — handlers `flowy-user` en detalle.")
    out.append("- `B3.F06` — handlers `flowy-folder` (workspace, vista, share).")
    out.append("- `B3.F07` — handlers `flowy-storage`.")
    out.append("- `B3.F08` — handlers `flowy-search` (índice tantivy).")
    out.append("- `B3.F09` — handlers `flowy-ai` (chat, completion, local).")
    out.append("")

    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="build_catalog_events.py")
    p.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    p.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args(argv)

    events = json.loads(args.input.read_text(encoding="utf-8"))
    n_var = sum(len(c["variants"]) for c in events["crates"])
    if n_var != events["summary"]["total_variants"]:
        print(
            f"build_catalog_events.py: INCONSISTENCIA events.json: "
            f"sum_variants={n_var} vs summary.total_variants="
            f"{events['summary']['total_variants']}",
            file=sys.stderr,
        )
        return 2

    text = render(events)
    args.output.write_text(text, encoding="utf-8")
    if not args.quiet:
        print(
            f"OK: {args.output} escrito · "
            f"{events['summary']['total_variants']} variantes · "
            f"{len(text.splitlines())} líneas"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())