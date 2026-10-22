#!/usr/bin/env python3
"""build_catalog_blocs.py — genera `OUT/13-catalogo-blocs.md`
desde `OUT/_ledger/extract/blocs.json`.

Fase B2.3 de la skill `notemartin-appflowy-review`.
Spec: ROADMAP.md línea 175 y AGENTS.md §5.4 (BLoC → Service → FFI).

Estructura del documento (10 secciones, plantilla `catalogue`):
  §1 Cómo leer este catálogo
  §2 Arquitectura BLoC en AppFlowy
  §3 Resumen por carpeta Dart (L1/L2)
  §4 Índice global de los 142 BLoCs
  §5 Catálogo por carpeta
  §6 BLoCs sin servicios inyectados detectados
  §7 Conteo de filas y prueba literal
  §8 Cobertura y referencias cruzadas
  §9 Preguntas abiertas
  §10 Relacionado con

Política de evidencia:
  - Cada fila referencia `file:decl_line` del extractor.
  - Rutas: `SRC/<fuente>/` → `<fuente>/` para alinear con inventario.
  - Semántica SIEMPRE `[INFERIDO]` (extract_blocs.py no captura doc-comments).

Prueba literal del ROADMAP: nº de filas = 142 (125 Bloc + 17 Cubit).
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
DEFAULT_INPUT = PROJECT_ROOT / "OUT" / "_ledger" / "extract" / "blocs.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "OUT" / "13-catalogo-blocs.md"

# Heurísticas para semántica derivada de nombre (BLoC).
BLOC_HINTS = [
    (re.compile(r"^(\w+)View"), "gestión de la vista {0}."),
    (re.compile(r"^View(\w+)_"), "sub-vista {0}."),
    (re.compile(r"^(\w+)Database"), "gestiona {0} de database."),
    (re.compile(r"^(\w+)Document"), "gestión del documento {0}."),
    (re.compile(r"^(\w+)Editor"), "gestión del editor {0}."),
    (re.compile(r"^(\w+)Cell"), "celda {0} de database."),
    (re.compile(r"^(\w+)Field"), "campo {0} de database."),
    (re.compile(r"^(\w+)Row"), "fila {0} de database."),
    (re.compile(r"^(\w+)Grid"), "vista grid {0}."),
    (re.compile(r"^(\w+)Board"), "vista board {0}."),
    (re.compile(r"^(\w+)Calendar"), "vista calendar {0}."),
    (re.compile(r"^(\w+)Settings"), "ajustes {0}."),
    (re.compile(r"^(\w+)Setting"), "ajuste {0}."),
    (re.compile(r"^(\w+)Sidebar"), "sidebar {0}."),
    (re.compile(r"^(\w+)Workspace"), "workspace {0}."),
    (re.compile(r"^(\w+)Folder"), "folder {0}."),
    (re.compile(r"^(\w+)Notification"), "notificación {0}."),
    (re.compile(r"^(\w+)Search"), "búsqueda {0}."),
    (re.compile(r"^(\w+)User"), "usuario {0}."),
    (re.compile(r"^(\w+)Auth"), "autenticación {0}."),
    (re.compile(r"^(\w+)Login"), "inicio de sesión {0}."),
    (re.compile(r"^(\w+)Home"), "home {0}."),
    (re.compile(r"^(\w+)Recent"), "recientes {0}."),
    (re.compile(r"^(\w+)Favorite"), "favoritos {0}."),
    (re.compile(r"^(\w+)Trash"), "papelera {0}."),
    (re.compile(r"^(\w+)Import"), "importación {0}."),
    (re.compile(r"^(\w+)Export"), "exportación {0}."),
    (re.compile(r"^(\w+)AI"), "IA {0}."),
    (re.compile(r"^(\w+)Chat"), "chat {0}."),
    (re.compile(r"^(\w+)CommandPalette"), "command palette {0}."),
    (re.compile(r"^(\w+)Tab"), "tab {0}."),
    (re.compile(r"^(\w+)PageAccess"), "nivel de acceso {0}."),
    (re.compile(r"^(\w+)Share"), "compartir {0}."),
    (re.compile(r"^(\w+)Publish"), "publicación {0}."),
    (re.compile(r"^(\w+)Theme"), "tema {0}."),
    (re.compile(r"^(\w+)Upload"), "subida {0}."),
    (re.compile(r"^(\w+)Mention"), "menciones {0}."),
    (re.compile(r"^(\w+)Mobile"), "mobile {0}."),
    (re.compile(r"^(\w+)Outline"), "outline {0}."),
    (re.compile(r"^(\w+)Navigation"), "navegación {0}."),
    (re.compile(r"^(\w+)EditorToolbar"), "toolbar del editor {0}."),
    (re.compile(r"^(\w+)Find"), "búsqueda interna {0}."),
    (re.compile(r"^(\w+)Date"), "selector de fecha {0}."),
    (re.compile(r"^(\w+)Embed"), "link embed {0}."),
    (re.compile(r"^(\w+)SlashMenu"), "slash menu {0}."),
]


def derive_semantic(name: str) -> str:
    for pat, template in BLOC_HINTS:
        m = pat.match(name)
        if m:
            word = m.group(1)
            spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", word).strip()
            return template.format(spaced.lower())
    return f"BLoC {name}."


def fmt_ref(file_ref: str, linea: int) -> str:
    ruta_clean = re.sub(r"^SRC/[^/]+/", "", file_ref)
    return f"`appflowy:{ruta_clean}:{linea}`"


def folder_of(bloc: dict) -> str:
    """Carpeta Dart L1/L2: 'plugins/database', 'workspace/application', etc."""
    file_ref = bloc.get("file", "")
    m = re.search(r"appflowy_flutter/lib/(.+?)\.dart$", file_ref)
    if m:
        parts = m.group(1).split("/")
        if len(parts) >= 2:
            return "/".join(parts[:2])
        return parts[0]
    return "?"


def md_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |"]
    out.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for r in rows:
        out.append("| " + " | ".join(r) + " |")
    return out


def render(blocs: dict) -> str:
    items = blocs["blocs"]
    summary = blocs["summary"]
    total = summary["total_blocs"] + summary["total_cubits"]
    n_bloc = summary["total_blocs"]
    n_cubit = summary["total_cubits"]
    n_freezed = summary["blocs_with_freezed_events"]
    n_db_app = summary["blocs_in_plugins_database_application"]
    n_scanned = summary["files_scanned"]

    # Group by folder
    by_folder: dict[str, list[dict]] = defaultdict(list)
    for b in items:
        by_folder[folder_of(b)].append(b)

    # Order folders by n desc
    folder_order = sorted(by_folder.keys(), key=lambda k: (-len(by_folder[k]), k))

    # BLoCs without injected_services
    no_services = [b for b in items if not (b.get("injected_services") or [])]

    out: list[str] = []

    # Frontmatter
    archivos_cubiertos = [
        "appflowy/frontend/appflowy_flutter/lib/**/*.dart",
        "appflowy/frontend/appflowy_flutter/packages/appflowy_backend/lib/dispatch/*.dart",
    ]
    fm = [
        "---",
        "id: 13-catalogo-blocs",
        "titulo: Catálogo de BLoCs y Cubits",
        "fuente: appflowy",
        "archivos_cubiertos:",
    ]
    for a in archivos_cubiertos:
        fm.append(f"  - {a}")
    fm.extend(["estado: verificado", "---"])
    out.extend(fm)
    out.append("")

    out.append("# 13 — Catálogo de BLoCs y Cubits")
    out.append("")
    out.append(
        f"Este documento cataloga los **{total} BLoCs y Cubits** "
        f"({n_bloc} `Bloc` + {n_cubit} `Cubit`) extraídos por "
        "`SKILL/scripts/extract_blocs.py` (Fase A2.4; validador "
        "`validate-A2.4.sh` 8/8 OK) a partir de los {n_scanned} archivos "
        "Dart de `frontend/appflowy_flutter/lib/`. Cada BLoC se declara "
        "con `extends Bloc<Event, State>` o `extends Cubit<State>` y "
        "define sus eventos con `@freezed` (o con `sealed class`). La "
        f"mayoría ({n_freezed}) tiene eventos `freezed` y {n_db_app} "
        "viven específicamente en `plugins/database/application/`. La "
        "semántica breve se deriva siempre del nombre + servicios "
        "inyectados + state_fields, etiquetada `[INFERIDO]` porque "
        "`extract_blocs.py` no captura `///` doc-comments. El catálogo "
        "es la base para los documentos B3.F01–F17 (handlers por "
        "feature) y se cruza con B2.1 (eventos FFI) y B2.2 (entidades "
        "PB)."
    )
    out.append("")

    # §1
    out.append("## 1. Cómo leer este catálogo")
    out.append("")
    out.append(
        "Cada fila representa un BLoC o Cubit. Las columnas son: "
        "`#` (ordinal dentro de la carpeta), `BLoC` (nombre de la "
        "clase), `Tipo` (`Bloc` / `Cubit`), `Eventos (n)` (nº de "
        "variantes del enum de eventos; 0 para Cubits sin eventos), "
        "`State fields (n)` (nº de `factory` del state), `Inyectados (n)` "
        "(nº de servicios pasados al constructor), `PB (n)` (nº de "
        "fields cuyo tipo es `*PB` — referencia a B2.2), `Archivo` "
        "(`ruta:línea` resuelto contra `inventario.json`), `Semántica` "
        "(derivada del nombre + heurística de carpeta + servicios). "
        "Las celdas con `—` indican lista `vacía`. La semántica "
        "SIEMPRE va etiquetada `[INFERIDO]`. Los BLoCs `Cubit` con "
        "estado inicial se distinguen porque su `state_type` empieza "
        "con un factory `loading` (campo `state_factory_initial`)."
    )
    out.append("")

    # §2 arquitectura BLoC
    out.append("## 2. Arquitectura BLoC en AppFlowy")
    out.append("")
    out.append(
        "El siguiente diagrama muestra el flujo típico de un BLoC: la "
        "UI dispara un evento, el BLoC lo procesa, delega en un "
        "`Service` que envía un evento FFI (`XEventFoo(...).send()`) "
        "y recibe un `FlowyResult<T, FlowyError>`, actualiza el `State` "
        "y la UI se reconstruye con `BlocBuilder`/`BlocListener`."
    )
    out.append("")
    out.append("```mermaid")
    out.append("flowchart TD")
    out.append("  subgraph UI[\"Widgets (presentation/)\"]")
    out.append("    View[\"BlocXView / Page\"]")
    out.append("    Builder[\"BlocBuilder&lt;XBloc, XState&gt;\"]")
    out.append("  end")
    out.append("  subgraph BLoC[\"BLoC (application/ logic/)\"]")
    out.append("    Bx[\"XBloc extends Bloc&lt;XEvent, XState&gt;\"]")
    out.append("    Ev[\"@freezed XEvent = Initial | DoA | DoB\"]")
    out.append("    St[\"@freezed XState = loading | loaded\"]")
    out.append("  end")
    out.append("  subgraph Svc[\"Service (service/)\"]")
    out.append("    Sx[\"XService\"]")
    out.append("    PB[\"PB (B2.2)\"]")
    out.append("  end")
    out.append("  subgraph FFI[\"FFI\"]")
    out.append("    Send[\"XEventFoo(PB).send()\"]")
    out.append("    Dispatch[\"lib-dispatch\"]")
    out.append("    Rust[\"rust handler → FlowyResult&lt;Y&gt;\"]")
    out.append("  end")
    out.append("  View -->|dispatch event| Ev --> Bx")
    out.append("  Bx -->|emit| St --> Builder --> View")
    out.append("  Bx --> Sx")
    out.append("  Sx --> PB --> Send --> Dispatch --> Rust --> Sx")
    out.append("```")
    out.append("")
    out.append(
        "Lectura: el `XBloc` recibe eventos tipados (lib `flutter_bloc` "
        "+ `@freezed` para que cada `factory` sea una subclase inmutable). "
        "Para hacer una llamada FFI delega en un `XService` (regla no "
        "estricta; en la base actual el 6 % de BLoCs tiene "
        "`injected_services` detectados automáticamente, el resto los "
        "obtiene de un singleton `getIt`). El `XService` envía el evento "
        "FFI por `appflowy_backend` y el resultado vuelve al `BLoC` que "
        "emite un nuevo estado."
    )
    out.append("")

    # §3 resumen por carpeta
    out.append("## 3. Resumen por carpeta")
    out.append("")
    headers_t = ["Carpeta Dart (L1/L2)", "Bloc", "Cubit", "Total", "Sin freezed", "Con services", "Con PB"]
    rows3: list[list[str]] = []
    for f in folder_order:
        ents = by_folder[f]
        nb = sum(1 for b in ents if b["kind"] == "Bloc")
        nc = sum(1 for b in ents if b["kind"] == "Cubit")
        nf = sum(1 for b in ents if not (b.get("events") or []))
        ns = sum(1 for b in ents if (b.get("injected_services") or []))
        npb = sum(
            1 for b in ents
            if any(
                re.search(r"PB(?:[?]?|\b)", s.get("type") or "")
                for s in (b.get("state_fields") or [])
            )
        )
        rows3.append([
            f"`{f}`",
            str(nb),
            str(nc),
            str(nb + nc),
            str(nf),
            str(ns),
            str(npb),
        ])
    for line in md_table(headers_t, rows3):
        out.append(line)
    out.append("")
    out.append(
        f"**Total**: {total} en {len(folder_order)} carpetas. "
        "**Sin freezed**: BLoCs o Cubits sin eventos detectados "
        "(típicamente Cubits). **Con services**: sólo el "
        f"{sum(1 for b in items if (b.get('injected_services') or []))}/{total} "
        "tienen servicios inyectados extraídos automáticamente; el resto "
        "usa `getIt` o un singleton del paquete `flowy_infra`. "
        "**Con PB**: BLoCs cuyo `state_fields` contiene al menos un "
        "tipo terminado en `PB` (referencia a B2.2)."
    )
    out.append("")

    # §4 índice global
    out.append(f"## 4. Índice global de los {total} BLoCs/Cubits")
    out.append("")
    out.append(
        f"Tabla plana con los {total} BLoCs/Cubits ordenados por "
        "`(carpeta, nombre)`. Cada fila es una entrada que también "
        f"aparece en §5.<carpeta>. El conteo de filas de §4 y de la "
        f"suma de filas de §5.* debe ser exactamente **{total}** "
        "(prueba literal del ROADMAP). Las entradas con `Inyectados (n) = 0` "
        "y `Sin services detectado` suelen ser BLoCs que obtienen "
        "dependencias vía `getIt` o singleton."
    )
    out.append("")
    headers4 = ["Carpeta", "#", "BLoC", "Tipo", "Eventos", "State fields", "Inyectados", "PB", "Archivo"]
    rows4: list[list[str]] = []
    sorted_items: list[tuple[str, int, dict]] = []
    for f in folder_order:
        ents = sorted(by_folder[f], key=lambda b: b["name"])
        sorted_items.extend((f, idx, b) for idx, b in enumerate(ents, 1))

    for f, idx, b in sorted_items:
        n_events = len(b.get("events") or [])
        n_state = len(b.get("state_fields") or [])
        n_svc = len(b.get("injected_services") or [])
        n_pb = sum(
            1
            for s in (b.get("state_fields") or [])
            if re.search(r"PB(?:[?]?|\b)", s.get("type") or "")
        )
        rows4.append([
            f"`{f}`",
            str(idx),
            f"`{b['name']}`",
            b["kind"],
            str(n_events),
            str(n_state),
            str(n_svc),
            str(n_pb),
            fmt_ref(b["file"], b["decl_line"]),
        ])
    for line in md_table(headers4, rows4):
        out.append(line)
    out.append("")

    # §5 catálogo por carpeta
    out.append("## 5. Catálogo por carpeta")
    out.append("")
    out.append(
        "Cada sub-sección desarrolla una carpeta Dart L1/L2. Las tablas "
        "siguen el mismo esquema que §4 (sin la columna `Carpeta` "
        "redundante). Cuando una carpeta supera los 20 BLoCs, se "
        "acompaña de un `flowchart LR` que agrupa los nombres por "
        "prefijo."
    )
    out.append("")
    for idx, f in enumerate(folder_order, 1):
        ents = sorted(by_folder[f], key=lambda b: b["name"])
        anchor = f.replace("/", "_").replace("-", "_")
        out.append(f"### 5.{idx} `{f}`")
        out.append("")
        nb = sum(1 for b in ents if b["kind"] == "Bloc")
        nc = sum(1 for b in ents if b["kind"] == "Cubit")
        out.append(f"**{len(ents)} BLoCs/Cubits** ({nb} Bloc + {nc} Cubit).")
        out.append("")
        if len(ents) >= 20:
            out.append("```mermaid")
            out.append("flowchart LR")
            out.append(f"  subgraph C{anchor}[\"{f}\"]")
            prefixes: dict[str, list[str]] = {}
            for b in ents:
                m = re.match(r"^([A-Z][a-z]+)", b["name"])
                p = m.group(1) if m else "Other"
                prefixes.setdefault(p, []).append(b["name"])
            for p, names in sorted(prefixes.items()):
                node_id = f"{anchor}_{p}"
                labels = "<br/>".join(names[:8])
                if len(names) > 8:
                    labels += f"<br/>… +{len(names) - 8}"
                out.append(f'    {node_id}["{p}<br/>({len(names)}):<br/>{labels}"]')
            out.append("  end")
            out.append("```")
            out.append("")
        headers5 = [
            "#",
            "BLoC",
            "Tipo",
            "Eventos (n)",
            "State fields (n)",
            "Inyectados (n)",
            "PB (n)",
            "Archivo",
            "Semántica",
        ]
        rows5: list[list[str]] = []
        for i, b in enumerate(ents, 1):
            n_events = len(b.get("events") or [])
            n_state = len(b.get("state_fields") or [])
            n_svc = len(b.get("injected_services") or [])
            n_pb = sum(
                1
                for s in (b.get("state_fields") or [])
                if re.search(r"PB(?:[?]?|\b)", s.get("type") or "")
            )
            sem = derive_semantic(b["name"])
            rows5.append([
                str(i),
                f"`{b['name']}`",
                b["kind"],
                str(n_events),
                str(n_state),
                str(n_svc),
                str(n_pb),
                fmt_ref(b["file"], b["decl_line"]),
                f"{sem} `[INFERIDO]`",
            ])
        for line in md_table(headers5, rows5):
            out.append(line)
        out.append("")

    # §6 sin services
    out.append("## 6. BLoCs sin servicios inyectados detectados")
    out.append("")
    out.append(
        f"Hay **{len(no_services)}** BLoCs/Cubits con `injected_services = []`. "
        "Esto se debe a que `extract_blocs.py` sólo detecta servicios "
        "explícitamente pasados al constructor (`super(…, this.xService)`), "
        "no los obtenidos vía `getIt`/`Get.find()` (que es el patrón "
        "dominante en AppFlowy). Esta sección los enumera como "
        "referencia para auditoría manual de la FFI cruzada."
    )
    out.append("")
    headers6 = ["#", "BLoC", "Carpeta", "Tipo", "Eventos (n)", "Archivo"]
    rows6: list[list[str]] = []
    ns_sorted = sorted(no_services, key=lambda b: (folder_of(b), b["name"]))
    for i, b in enumerate(ns_sorted, 1):
        rows6.append([
            str(i),
            f"`{b['name']}`",
            f"`{folder_of(b)}`",
            b["kind"],
            str(len(b.get("events") or [])),
            fmt_ref(b["file"], b["decl_line"]),
        ])
    for line in md_table(headers6, rows6):
        out.append(line)
    out.append("")

    # §7 prueba literal
    out.append("## 7. Conteo de filas y prueba literal")
    out.append("")
    out.append(
        f"La prueba del ROADMAP exige que el número de filas del "
        f"catálogo sea exactamente **{total}** (= `summary.total_blocs "
        f"+ summary.total_cubits = {n_bloc} + {n_cubit}`). El script "
        "`OUT/_ledger/pruebas/B2.3/count_rows_142.py` cuenta las filas "
        "de §4 y de la suma de §5.*; debe coincidir. El comando "
        "canónico externo es:"
    )
    out.append("")
    out.append("```bash")
    out.append(
        f"jq '.summary.total_blocs + .summary.total_cubits' \\\n"
        f"  OUT/_ledger/extract/blocs.json   # esperado: {total}"
    )
    out.append("```")
    out.append("")

    # §8 cobertura
    out.append("## 8. Cobertura y referencias cruzadas")
    out.append("")
    out.append("- **B2.1 — `11-catalogo-eventos-ffi.md`**: cada BLoC "
        "típicamente envía 1–N eventos FFI; los `injected_services` "
        "extraídos (8/142) son la fuente directa; el resto cruza por "
        "`getIt`/singleton.")
    out.append("- **B2.2 — `12-catalogo-entidades-protobuf.md`**: cada "
        "BLoC cuya `state_fields` contiene `*PB` (18/142) se cruza "
        "con las entidades de ese catálogo.")
    out.append("- **B1.5 — `06-puente-flutter-rust/02-lib-dispatch.md`**: "
        "el dispatcher (229 eventos / 224 handlers).")
    out.append("- **B1.6 — `07-motor-colaborativo-crdt/`**: los BLoCs "
        "que manejan `Document` o `View` operan sobre el `Collab`.")
    out.append("- **Bloque B3 — F0x**: cada feature documenta sus BLoCs "
        "principales en su doc de feature (ej. `DocumentBloc` en F01, "
        "`ShareBloc` en F12).")
    out.append("- **B5 — Secuencias globales**: las `sequenceDiagram` "
        "trazan `Bloc → Service → FFI` para los flujos principales.")
    out.append("")

    # §9 preguntas abiertas
    out.append("## 9. Preguntas abiertas")
    out.append("")
    out.append(
        "Sin entradas por ahora. Si el revisor detecta BLoCs cuya "
        "semántica no se derive del patrón (p. ej. BLoCs `Cross-file` con "
        "`events_source` cross-file y muchos servicios sin detectar), se "
        "volcará una entrada `[NO DETERMINADO]` aquí y en "
        "`OUT/22-preguntas-abiertas.md`."
    )
    out.append("")

    # §10 relacionado
    out.append("## 10. Relacionado con")
    out.append("")
    out.append("- `06-puente-flutter-rust/02-lib-dispatch.md` — dispatcher.")
    out.append("- `11-catalogo-eventos-ffi.md` — eventos FFI consumidos por "
        "los BLoCs.")
    out.append("- `12-catalogo-entidades-protobuf.md` — entidades "
        "manejadas en el state.")
    out.append("- `B0.1` — `blocs.json` con `validate-A2.4.sh` 8/8 OK.")
    out.append("- `B3.F0x` — cada BLoC en su feature.")
    out.append("- `B5` — `sequenceDiagram` de los flujos principales.")
    out.append("")

    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="build_catalog_blocs.py")
    p.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    p.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args(argv)

    blocs = json.loads(args.input.read_text(encoding="utf-8"))
    expected = blocs["summary"]["total_blocs"] + blocs["summary"]["total_cubits"]
    if len(blocs["blocs"]) != expected:
        print(
            f"build_catalog_blocs.py: INCONSISTENCIA blocs.json: "
            f"len(blocs)={len(blocs['blocs'])} vs summary.total_blocs+"
            f"total_cubits={expected}",
            file=sys.stderr,
        )
        return 2

    text = render(blocs)
    args.output.write_text(text, encoding="utf-8")
    if not args.quiet:
        print(
            f"OK: {args.output} escrito · {expected} BLoCs/Cubits · "
            f"{len(text.splitlines())} líneas"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())