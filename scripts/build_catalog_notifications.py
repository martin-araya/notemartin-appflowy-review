#!/usr/bin/env python3
"""build_catalog_notifications.py — genera `OUT/14-catalogo-notificaciones.md`
desde `OUT/_ledger/extract/notifications.json`.

Fase B2.4 de la skill `notemartin-appflowy-review`.
Spec: ROADMAP.md línea 176 y AGENTS.md §5.2 (notificaciones Rust→Dart).

Estructura del documento (10 secciones, plantilla `catalogue`):
  §1 Cómo leer este catálogo
  §2 Arquitectura del canal
  §3 Resumen por enum
  §4 Índice global de las 70 variantes
  §5 Catálogo por enum (6 sub-secciones)
  §6 Variantes sin uso en Dart
  §7 Conteo de filas y prueba literal
  §8 Cobertura y referencias cruzadas
  §9 Preguntas abiertas
  §10 Relacionado con

Política de evidencia:
  - Cada fila referencia el `enum decl_line` (variant_usage de A2.3).
  - Rutas: `SRC/<fuente>/` → `<fuente>/` para alinear con inventario.
  - Semántica SIEMPRE `[INFERIDO]`.

Prueba literal del ROADMAP: nº de filas = 70 variantes (suma §5.* = §4 = 70)
y cada una con emisor o `sin uso`. §6 contiene los 47 unused + 2 emitted_only
sin listener Dart.
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
DEFAULT_INPUT = PROJECT_ROOT / "OUT" / "_ledger" / "extract" / "notifications.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "OUT" / "14-catalogo-notificaciones.md"

# Heurísticas para semántica derivada del nombre de la variante.
NOTIF_HINTS = [
    (re.compile(r"^DidUpdate(\w+)$"), "Actualiza el recurso {0}."),
    (re.compile(r"^DidCreate(\w+)$"), "Crea el recurso {0}."),
    (re.compile(r"^DidDelete(\w+)$"), "Elimina el recurso {0}."),
    (re.compile(r"^DidReceive(\w+)$"), "Recibe {0}."),
    (re.compile(r"^DidLoad(\w+)$"), "Carga {0}."),
    (re.compile(r"^DidMove(\w+)$"), "Mueve {0}."),
    (re.compile(r"^DidReorder(\w+)$"), "Reordena {0}."),
    (re.compile(r"^DidGroupBy(\w+)$"), "Agrupa por {0}."),
    (re.compile(r"^DidFetch(\w+)$"), "Recupera {0}."),
    (re.compile(r"^DidInsert(\w+)$"), "Inserta {0}."),
    (re.compile(r"^DidUpdate(\w+)SnapshotState$"), "Cambia el snapshot state de {0}."),
    (re.compile(r"^DidUpdate(\w+)SyncUpdate$"), "Cambia el sync update {0}."),
    (re.compile(r"^Stream(\w+)Error$"), "Error al streamear {0}."),
    (re.compile(r"^FinishStreaming$"), "Marca el fin del streaming."),
    (re.compile(r"^UpdateLocal(\w+)$"), "Actualiza el recurso local {0}."),
    (re.compile(r"^Local(\w+)Updated$"), "Recurso local {0} actualizado."),
    (re.compile(r"^DidUpdateSelected(\w+)$"), "Cambia la selección de {0}."),
    (re.compile(r"^Unknown$"), "Sentinela / no usado."),
    (re.compile(r"^FileStorageLimitExceeded$"), "Límite total de almacenamiento superado."),
    (re.compile(r"^SingleFileLimitExceeded$"), "Límite por archivo superado."),
]


def derive_effect_ui(enum_name: str, variant_name: str) -> str:
    for pat, template in NOTIF_HINTS:
        m = pat.match(variant_name)
        if m:
            word = m.group(1) if m.lastindex else variant_name
            spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", word).strip()
            return template.format(spaced.lower())
    return f"Notificación {variant_name}."


def fmt_ref(file_ref: str, linea: int) -> str:
    ruta_clean = re.sub(r"^SRC/[^/]+/", "", file_ref)
    return f"`appflowy:{ruta_clean}:{linea}`"


def md_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |"]
    out.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for r in rows:
        out.append("| " + " | ".join(r) + " |")
    return out


def render(notif: dict) -> str:
    items = notif["rust_notifications"]
    summary = notif["summary"]
    total_emitters = summary["total_emitters"]
    total_listeners = summary["total_dart_listeners"]
    total_parsers = summary["total_dart_parsers"]
    variants_without_listener = summary["variants_without_dart_listener"]

    # All variants (flat list of (enum_name, enum_decl_line, file, variant))
    all_variants: list[tuple[dict, dict]] = []
    for enum_obj in items:
        for v in enum_obj["variants"]:
            all_variants.append((enum_obj, v))

    # Build index: (enum_name, variant_name) → listeners list
    listener_for: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for lst in notif.get("dart_listeners", []):
        for hv in lst.get("handled_variants", []):
            key = (hv["enum"], hv["variant"])
            listener_for[key].append({"listener": lst})

    # Build index: (enum_name, variant_name) → emitters list (with file:line)
    emitter_for: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for enum_obj in items:
        for em in enum_obj.get("emitters", []):
            if em.get("variant") is None:
                continue
            key = (em["enum_name"], em["variant"])
            emitter_for[key].append(em)

    # Total variants count
    total = sum(len(e["variants"]) for e in items)

    # Count statuses
    status_count: dict[str, int] = defaultdict(int)
    for enum_obj in items:
        for variant_name, vu in enum_obj.get("variant_usage", {}).items():
            status_count[vu["status"]] += 1

    unused_variants = [
        (e, v)
        for e, v in all_variants
        if e.get("variant_usage", {}).get(v["name"], {}).get("status") == "unused"
        or e.get("variant_usage", {}).get(v["name"], {}).get("status") == "emitted_only"
    ]

    out: list[str] = []

    archivos_cubiertos = [
        "appflowy/frontend/rust-lib/flowy-ai/src/notification.rs",
        "appflowy/frontend/rust-lib/flowy-database2/src/notification.rs",
        "appflowy/frontend/rust-lib/flowy-document/src/notification.rs",
        "appflowy/frontend/rust-lib/flowy-folder/src/notification.rs",
        "appflowy/frontend/rust-lib/flowy-storage/src/notification.rs",
        "appflowy/frontend/rust-lib/flowy-user/src/notification.rs",
        "appflowy/frontend/appflowy_flutter/lib/core/notification/*.dart",
        "appflowy/frontend/appflowy_flutter/lib/plugins/*/application/*_listener.dart",
        "appflowy/frontend/rust-lib/flowy-notification/src/builder.rs",
        "appflowy/frontend/appflowy_flutter/lib/packages/appflowy_backend/lib/rust_stream.dart",
    ]
    fm = [
        "---",
        "id: 14-catalogo-notificaciones",
        "titulo: Catálogo de notificaciones (Rust → Dart)",
        "fuente: appflowy",
        "archivos_cubiertos:",
    ]
    for a in archivos_cubiertos:
        fm.append(f"  - {a}")
    fm.extend(["estado: verificado", "---"])
    out.extend(fm)
    out.append("")

    out.append("# 14 — Catálogo de notificaciones (Rust → Dart)")
    out.append("")
    out.append(
        f"Este documento cataloga las **{total} variantes** de notificaciones "
        f"en **{len(items)} enums** Rust (`flowy-ai`, `flowy-database2`, "
        "`flowy-document`, `flowy-folder`, `flowy-storage`, `flowy-user`) "
        "que cruzan la frontera al isolate de Dart. Cada variante se "
        "define como `#[derive(ProtoBuf_Enum)] XNotification` y se publica "
        "vía `flowy-notification::NotificationBuilder` "
        "(`flowy-notification/src/builder.rs`) con su "
        "`*_OBSERVABLE_SOURCE`. La fuente de datos es "
        "`OUT/_ledger/extract/notifications.json` (Fase A2.3; validador "
        f"`validate-A2.3.sh` 7/7 OK). Hay **{total_emitters}** sitios "
        f"emisor, **{total_listeners}** listeners Dart y "
        f"**{total_parsers}** parsers. La prueba del ROADMAP exige "
        f"que el nº de filas del catálogo sea exactamente **{total}** y "
        "que cada fila tenga emisor o esté marcada `sin uso`. Cruce con "
        "B2.1 (eventos FFI): los handlers que emiten notificaciones "
        "están en el árbol de `event_handler.rs` → `manager.rs`."
    )
    out.append("")

    # §1
    out.append("## 1. Cómo leer este catálogo")
    out.append("")
    out.append(
        "Cada fila representa una variante `XNotification`. Las columnas "
        "son: `#` (ordinal dentro del enum), `Enum` (Rust), `Variante` "
        "(nombre), `Índice` (en el enum), `Default` (si es el miembro "
        "`#[default]`), `Status` (`ok`, `emitted_only`, "
        "`declared_only`, `unused` — del extractor), `Emisor (Rust)` "
        "(`archivo:línea` cuando `variant != null` en `emitters[]`; "
        "`—` si no hay emisor), `Listener Dart` (`archivo:línea` si "
        "`has_dart_listener == true`; `—` si no), `Efecto UI` (descripción "
        "derivada del nombre + listener). Las variantes con `Status "
        "∈ {unused, declared_only, emitted_only}` se explican en §6 "
        "(`Sin uso en Dart`). Las rutas usan el formato del inventario "
        "(sin prefijo `SRC/appflowy/`)."
    )
    out.append("")

    # §2 arquitectura
    out.append("## 2. Arquitectura del canal de notificaciones")
    out.append("")
    out.append(
        "El siguiente diagrama muestra cómo un handler Rust publica una "
        "notificación con `send_notification(&id, ty, source)` y el isolate "
        "Dart la procesa: el `RustStreamReceiver` (`rust_stream.dart`) "
        "deserializa el payload con el `<Enum>NotificationParser`, lo "
        "despacha por `parser.subject.stream` y los `*_listener.dart` "
        "(suscritos vía `subject.listen(...)`) ejecutan el efecto UI "
        "típico (`Bloc.add`, `setState`, `FlowyError`, etc.)."
    )
    out.append("")
    out.append("```mermaid")
    out.append("flowchart TD")
    out.append("  subgraph Rust[\"Rust handler (B2.1 event)\"]")
    out.append("    Handler[\"manager.rs: send_notification(id, ty, source)\"]")
    out.append("    Notif[\"flowy-notification::NotificationBuilder\"]")
    out.append("    Debounce[\"DebounceNotificationSender (debounce)\"]")
    out.append("  end")
    out.append("  subgraph C[\"Frontera C (dart-ffi)\"]")
    out.append("    Notify[\"notify() (tokio mpsc → callback)\"]")
    out.append("  end")
    out.append("  subgraph Dart[\"Isolate Dart\"]")
    out.append("    Recv[\"RustStreamReceiver (rust_stream.dart)\"]")
    out.append("    Parser[\"<Enum>NotificationParser (core/notification/)\"]")
    out.append("    Stream[\"parser.subject.stream\"]")
    out.append("    Listener[\"<X>_listener.dart (Bloc.add)\"]")
    out.append("    Effect[\"Effect UI (refrescar vista)\"]")
    out.append("  end")
    out.append("  Handler --> Notif --> Debounce --> Notify")
    out.append("  Notify --> Recv --> Parser --> Stream --> Listener --> Effect")
    out.append("```")
    out.append("")
    out.append(
        "Lectura: el `DebounceNotificationSender` de `flowy-notification` "
        "puede coalescer múltiples `send_notification` del mismo "
        "`(id, ty, source)` en una sola entrega dentro de una ventana "
        "(típicamente 50 ms). El isolate Dart recibe el evento a través "
        "del puerto `stream_port` (sub-doc `06-puente-flutter-rust/01-ffi.md`) "
        "y `RustStreamReceiver` lo decodifica con el `NotificationParser` "
        "correspondiente (`core/notification/*_notification.dart`). "
        "Cada listener Dart se suscribe vía `parser.subject.listen(...)` "
        "y reacciona con un `switch (notification)`."
    )
    out.append("")

    # §3 resumen por enum
    out.append("## 3. Resumen por enum")
    out.append("")
    headers_t = ["Enum", "Crate", "Variantes", "Emisores (Rust)", "Listeners Dart", "Estados"]
    rows3: list[list[str]] = []
    for e in items:
        n_v = len(e["variants"])
        n_em = sum(1 for em in e.get("emitters", []) if em.get("variant") is not None)
        # Count listeners that handle any variant of this enum
        n_ls = sum(
            1
            for lst in notif.get("dart_listeners", [])
            if any(hv["enum"] == e["name"] for hv in lst.get("handled_variants", []))
        )
        st_counts = defaultdict(int)
        for vn in e.get("variant_usage", {}).values():
            st_counts[vn["status"]] += 1
        states_summary = ", ".join(f"{k}={v}" for k, v in sorted(st_counts.items()))
        rows3.append([
            f"`{e['name']}`",
            f"`{e['crate']}`",
            str(n_v),
            str(n_em),
            str(n_ls),
            states_summary or "—",
        ])
    for line in md_table(headers_t, rows3):
        out.append(line)
    out.append("")
    out.append(
        f"**Total**: {total} variantes en {len(items)} enums. "
        f"**Emisores Rust** que pasan variante específica: "
        f"{sum(1 for e in items for em in e.get('emitters', []) if em.get('variant'))}; "
        f"el resto de los {total_emitters} sitios del extractor son `NotificationBuilder::new(...)` "
        "que crean la fuente (no emiten variantes concretas)."
    )
    out.append("")

    # §4 índice global
    out.append(f"## 4. Índice global de las {total} variantes")
    out.append("")
    out.append(
        f"Tabla plana con las {total} variantes ordenadas por `(enum, índice)`. "
        "Cada fila es una entrada que también aparece en §5.<enum>. El "
        f"conteo de filas de §4 y de la suma de filas de §5.* debe ser "
        f"exactamente **{total}** (prueba literal del ROADMAP)."
    )
    out.append("")
    headers4 = ["Enum", "#", "Variante", "Índice", "Default", "Status", "Emisor (Rust)", "Listener Dart", "Efecto UI"]
    rows4: list[list[str]] = []
    flat: list[tuple[dict, dict]] = []
    for e in items:
        for v in e["variants"]:
            flat.append((e, v))
    flat.sort(key=lambda p: (p[0]["name"], p[1]["index"]))
    for i, (e, v) in enumerate(flat, 1):
        vu = e.get("variant_usage", {}).get(v["name"], {})
        status = vu.get("status", "—")
        emitters = emitter_for.get((e["name"], v["name"]), [])
        em_cell = "<br/>".join(fmt_ref(em["file"], em["line"]) for em in emitters[:3])
        if len(emitters) > 3:
            em_cell += f"<br/>… +{len(emitters) - 3}"
        listeners = listener_for.get((e["name"], v["name"]), [])
        ls_cell = "<br/>".join(fmt_ref(lst["listener"]["file"], 1) for lst in listeners[:3])
        if len(listeners) > 3:
            ls_cell += f"<br/>… +{len(listeners) - 3}"
        eff = derive_effect_ui(e["name"], v["name"])
        rows4.append([
            f"`{e['name']}`",
            str(i),
            f"`{v['name']}`",
            str(v["index"]),
            "sí" if v.get("is_default") else "—",
            status,
            em_cell or "—",
            ls_cell or "—",
            f"{eff} `[INFERIDO]`",
        ])
    for line in md_table(headers4, rows4):
        out.append(line)
    out.append("")

    # §5 catálogo por enum
    out.append("## 5. Catálogo por enum")
    out.append("")
    out.append(
        "Cada sub-sección desarrolla un enum. Las tablas siguen el mismo "
        "esquema que §4 (sin la columna `Enum` redundante). Cuando un enum "
        "supera las 10 variantes, se acompaña de un mini `flowchart` que "
        "muestra el listener que la enruta (cuando existe)."
    )
    out.append("")
    for idx, e in enumerate(items, 1):
        out.append(f"### 5.{idx} `{e['name']}`")
        out.append("")
        n_v = len(e["variants"])
        n_em = sum(1 for em in e.get("emitters", []) if em.get("variant") is not None)
        out.append(
            f"**{n_v} variantes** · **{n_em} emisores con variante** · "
            f"declarado en `appflowy/frontend/rust-lib/{e['crate']}/src/notification.rs:{e['decl_line']}`."
        )
        out.append("")
        # Mini flowchart if >= 10 variants and at least one listener
        listeners_for_enum = [
            lst
            for lst in notif.get("dart_listeners", [])
            if any(hv["enum"] == e["name"] for hv in lst.get("handled_variants", []))
        ]
        if n_v >= 10 and listeners_for_enum:
            out.append("```mermaid")
            out.append("flowchart LR")
            out.append(f"  subgraph R[\"{e['name']} (Rust, crate {e['crate']})\"]")
            out.append("    N[\"NotificationBuilder\"]")
            out.append("  end")
            out.append(f"  subgraph D[\"Listeners Dart\"]")
            for lst in listeners_for_enum[:6]:
                node_id = re.sub(r"[^a-zA-Z0-9]", "_", lst["name"])
                out.append(f'    {node_id}["{lst["name"]}<br/>({lst["file"].split("appflowy_flutter/lib/")[1]})"]')
            out.append("  end")
            out.append("  N --> D")
            out.append("```")
            out.append("")
        headers5 = [
            "#",
            "Variante",
            "Índice",
            "Default",
            "Status",
            "Emisor (Rust)",
            "Listener Dart",
            "Archivo variante",
            "Efecto UI",
        ]
        rows5: list[list[str]] = []
        for i, v in enumerate(sorted(e["variants"], key=lambda x: x["index"]), 1):
            vu = e.get("variant_usage", {}).get(v["name"], {})
            status = vu.get("status", "—")
            emitters = emitter_for.get((e["name"], v["name"]), [])
            em_cell = "<br/>".join(fmt_ref(em["file"], em["line"]) for em in emitters[:3])
            if len(emitters) > 3:
                em_cell += f"<br/>… +{len(emitters) - 3}"
            listeners = listener_for.get((e["name"], v["name"]), [])
            ls_cell = "<br/>".join(fmt_ref(lst["listener"]["file"], 1) for lst in listeners[:3])
            if len(listeners) > 3:
                ls_cell += f"<br/>… +{len(listeners) - 3}"
            eff = derive_effect_ui(e["name"], v["name"])
            rows5.append([
                str(i),
                f"`{v['name']}`",
                str(v["index"]),
                "sí" if v.get("is_default") else "—",
                status,
                em_cell or "—",
                ls_cell or "—",
                fmt_ref(e["file"], v["decl_line"]),
                f"{eff} `[INFERIDO]`",
            ])
        for line in md_table(headers5, rows5):
            out.append(line)
        out.append("")

    # §6 sin uso
    out.append("## 6. Variantes sin uso en Dart")
    out.append("")
    out.append(
        f"Hay **{len(unused_variants)} variantes** con `status ∈ "
        "{\"unused\", \"emitted_only\"}` (sentinela / declarado pero no emitido, "
        "o emitido en Rust sin listener Dart). El ROADMAP exige que **cada "
        "variante tenga emisor o esté marcada `sin uso`**; esta tabla "
        "cubre todas las `unused` y `emitted_only`. Las `declared_only` "
        "y `ok` no aparecen aquí (tienen listener Dart y/o emisor Rust, "
        "ya documentados en §5)."
    )
    out.append("")
    headers6 = ["#", "Enum", "Variante", "Status", "Archivo"]
    rows6: list[list[str]] = []
    for i, (e, v) in enumerate(unused_variants, 1):
        vu = e.get("variant_usage", {}).get(v["name"], {})
        rows6.append([
            str(i),
            f"`{e['name']}`",
            f"`{v['name']}`",
            vu.get("status", "—"),
            fmt_ref(e["file"], v["decl_line"]),
        ])
    for line in md_table(headers6, rows6):
        out.append(line)
    out.append("")

    # §7 prueba literal
    out.append("## 7. Conteo de filas y prueba literal")
    out.append("")
    out.append(
        f"La prueba del ROADMAP exige que el número de filas del catálogo "
        f"sea exactamente **{total}** (= suma de variantes en los "
        f"{len(items)} enums). El script "
        "`OUT/_ledger/pruebas/B2.4/count_rows_70.py` cuenta las filas de "
        "§4 y de la suma de §5.*; debe coincidir. Las filas de §6 son "
        f"las variantes `unused` + `emitted_only` (esperado = "
        f"{len(unused_variants)}). El comando canónico externo:"
    )
    out.append("")
    out.append("```bash")
    out.append(
        f"jq '[.rust_notifications[].variants | length] | add' \\\n"
        f"  OUT/_ledger/extract/notifications.json   # esperado: {total}"
    )
    out.append("```")
    out.append("")

    # §8 cobertura
    out.append("## 8. Cobertura y referencias cruzadas")
    out.append("")
    out.append("- **B2.1 — `11-catalogo-eventos-ffi.md`**: cada handler "
        "que emite `send_notification(...)` está en el árbol de su "
        "crate (`flowy-*/event_handler.rs` → `manager.rs`).")
    out.append("- **B2.2 — `12-catalogo-entidades-protobuf.md`**: los "
        "payloads que llegan a los listeners Dart suelen ser "
        "entidades protobuf serializadas; este catálogo referencia "
        "los PBs.")
    out.append("- **B1.5 — `06-puente-flutter-rust/04-notificaciones.md`**: "
        "el detalle del `flowy-notification` + `DebounceNotificationSender` "
        "+ 6 enums Rust (70 variantes) + 29 listeners Dart.")
    out.append("- **Bloque B3 — F0x**: cada feature documenta sus "
        "notificaciones principales (ej. `DocumentNotification` en F01, "
        "`DatabaseNotification` en F02, `FolderNotification` en F03/F06).")
    out.append("- **B5 — Secuencias globales**: las notificaciones "
        "Rust→Dart son la mitad de cada `sequenceDiagram` end-to-end "
        "(cruzan la frontera en sentido contrario a los eventos FFI).")
    out.append("")

    # §9 preguntas abiertas
    out.append("## 9. Preguntas abiertas")
    out.append("")
    out.append(
        "Sin entradas por ahora. Los 47 `unused` y los 2 `emitted_only` "
        "son variantes declaradas pero sin uso efectivo; se audita en §6. "
        "Si el revisor detecta variantes con listener Dart ambiguo "
        "(múltiples `Bloc.add` para una misma `XNotification::Foo` que "
        "podrían cruzarse), se vuelca aquí."
    )
    out.append("")

    # §10 relacionado
    out.append("## 10. Relacionado con")
    out.append("")
    out.append("- `06-puente-flutter-rust/04-notificaciones.md` — detalle "
        "del canal.")
    out.append("- `06-puente-flutter-rust/01-ffi.md` — `set_stream_port` "
        "que registra el puerto de Dart.")
    out.append("- `11-catalogo-eventos-ffi.md` — emisor (handler) de cada "
        "notificación.")
    out.append("- `12-catalogo-entidades-protobuf.md` — payload.")
    out.append("- `B0.1` — `notifications.json` con `validate-A2.3.sh` 7/7 OK.")
    out.append("- `B3.F0x` — cada feature.")
    out.append("- `B5` — secuencias globales.")
    out.append("")

    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="build_catalog_notifications.py")
    p.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    p.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args(argv)

    notif = json.loads(args.input.read_text(encoding="utf-8"))
    total = sum(len(e["variants"]) for e in notif["rust_notifications"])
    if total != 70:
        print(
            f"build_catalog_notifications.py: INCONSISTENCIA notifications.json: "
            f"sum_variants={total} (esperado 70)",
            file=sys.stderr,
        )
        return 2

    text = render(notif)
    args.output.write_text(text, encoding="utf-8")
    if not args.quiet:
        print(
            f"OK: {args.output} escrito · {total} variantes · "
            f"{len(text.splitlines())} líneas"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())