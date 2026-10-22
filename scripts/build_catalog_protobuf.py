#!/usr/bin/env python3
"""build_catalog_protobuf.py — genera `OUT/12-catalogo-entidades-protobuf.md`
desde `OUT/_ledger/extract/protobuf.json`.

Fase B2.2 de la skill `notemartin-appflowy-review`.
Spec: ROADMAP.md línea 174 y AGENTS.md §5.1 (codegen + entidades PB).

Estructura del documento (10 secciones, plantilla `catalogue`):
  §1 Cómo leer este catálogo
  §2 Arquitectura del codegen
  §3 Resumen por crate
  §4 Índice global de las 439 entidades
  §5 Catálogo por crate (10 sub-secciones)
  §6 Entidades sin uso en eventos (huérfanas)
  §7 Conteo de filas y prueba literal
  §8 Cobertura y referencias cruzadas
  §9 Preguntas abiertas
  §10 Relacionado con

Política de evidencia:
  - Cada fila referencia el `file:decl_line` del extractor.
  - Rutas normalizadas: `SRC/<fuente>/` → `<fuente>/` para alinear con
    `inventario.json::ruta_rel`.
  - Semántica SIEMPRE `[INFERIDO]` porque `extract_protobuf.py` no
    captura `///` doc-comments. Sólo se basa en nombre + fields + derives.

Prueba literal del ROADMAP: nº de filas = `summary.total_entities = 439`.
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
DEFAULT_INPUT = PROJECT_ROOT / "OUT" / "_ledger" / "extract" / "protobuf.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "OUT" / "12-catalogo-entidades-protobuf.md"

# Heurísticas para semántica derivada de nombre (struct).
STRUCT_HINTS = [
    (re.compile(r"^(\w+Id)$"), "Identificador de {0}."),
    (re.compile(r"^(\w+)(IdPB)$"), "Identificador de {0}."),
    (re.compile(r"^(\w+)Settings$"), "Ajustes de {0}."),
    (re.compile(r"^(\w+)SettingsPB$"), "Ajustes de {0}."),
    (re.compile(r"^(\w+)Configuration$"), "Configuración de {0}."),
    (re.compile(r"^(\w+)ConfigurationPB$"), "Configuración de {0}."),
    (re.compile(r"^(\w+)Config$"), "Configuración de {0}."),
    (re.compile(r"^(\w+)ConfigPB$"), "Configuración de {0}."),
    (re.compile(r"^(\w+)PayloadPB$"), "Payload de {0}."),
    (re.compile(r"^(\w+)Payload$"), "Payload de {0}."),
    (re.compile(r"^(\w+)ChangesetPB$"), "Cambios (changeset) sobre {0}."),
    (re.compile(r"^(\w+)Changeset$"), "Cambios (changeset) sobre {0}."),
    (re.compile(r"^(\w+)CellDataChangesetPB$"), "Cambios de datos de celda {0}."),
    (re.compile(r"^(\w+)CellDataPB$"), "Datos de celda de {0}."),
    (re.compile(r"^(\w+)DataPB$"), "Datos de {0}."),
    (re.compile(r"^(\w+)Data$"), "Datos de {0}."),
    (re.compile(r"^(\w+)RequestPB$"), "Petición de {0}."),
    (re.compile(r"^(\w+)ResponsePB$"), "Respuesta de {0}."),
    (re.compile(r"^(\w+)ResultPB$"), "Resultado de {0}."),
    (re.compile(r"^(\w+)SummaryPB$"), "Resumen de {0}."),
    (re.compile(r"^(\w+)InfoPB$"), "Información de {0}."),
    (re.compile(r"^(\w+)MetaPB$"), "Metadatos de {0}."),
    (re.compile(r"^(\w+)ListPB$"), "Lista de {0}."),
    (re.compile(r"^(\w+)ArrayPB$"), "Arreglo de {0}."),
    (re.compile(r"^(\w+)MapPB$"), "Mapa de {0}."),
    (re.compile(r"^Create(\w+)PayloadPB$"), "Payload de creación de {0}."),
    (re.compile(r"^Update(\w+)PayloadPB$"), "Payload de actualización de {0}."),
    (re.compile(r"^Delete(\w+)PayloadPB$"), "Payload de borrado de {0}."),
    (re.compile(r"^Get(\w+)PB$"), "Lectura de {0}."),
    (re.compile(r"^Open(\w+)PayloadPB$"), "Payload de apertura de {0}."),
    (re.compile(r"^Close(\w+)PayloadPB$"), "Payload de cierre de {0}."),
    (re.compile(r"^ConvertData(\w+)PayloadPB$"), "Payload de conversión de datos {0}."),
    (re.compile(r"^ConvertDocument(\w+)PayloadPB$"), "Payload de conversión de documento {0}."),
    (re.compile(r"^Import(\w+)PB$"), "Importación de {0}."),
    (re.compile(r"^Export(\w+)PB$"), "Exportación de {0}."),
    (re.compile(r"^Upload(\w+)PB$"), "Subida de {0}."),
    (re.compile(r"^Stream(\w+)PayloadPB$"), "Payload de stream de {0}."),
    (re.compile(r"^(\w+)SnapshotPB$"), "Snapshot serializado de {0}."),
    (re.compile(r"^(\w+)NotificationPB$"), "Payload de notificación de {0}."),
]

ENUM_HINTS = [
    (re.compile(r"^FFIStatusCode$"), "Códigos de estado de la FFI (Ok / Err / Internal)."),
    (re.compile(r"^StatusCode$"), "Códigos de estado genéricos."),
    (re.compile(r"^(\w+)TypePB$"), "tipo / categoría {0}."),
    (re.compile(r"^(\w+)Status$"), "estado {0}."),
    (re.compile(r"^(\w+)Layout$"), "layout {0}."),
    (re.compile(r"^(\w+)LayoutPB$"), "layout {0}."),
    (re.compile(r"^(\w+)Mode$"), "modo {0}."),
    (re.compile(r"^(\w+)Level$"), "nivel {0}."),
    (re.compile(r"^(\w+)Scope$"), "alcance {0}."),
    (re.compile(r"^(\w+)Source$"), "origen {0}."),
    (re.compile(r"^(\w+)Role$"), "rol {0}."),
    (re.compile(r"^(\w+)Action$"), "acción {0}."),
    (re.compile(r"^(\w+)Format$"), "formato {0}."),
    (re.compile(r"^(\w+)Order$"), "orden {0}."),
    (re.compile(r"^(\w+)Direction$"), "dirección {0}."),
    (re.compile(r"^(\w+)Visibility$"), "visibilidad {0}."),
    (re.compile(r"^(\w+)Condition$"), "condición {0}."),
    (re.compile(r"^(\w+)Filter$"), "filtro {0}."),
]


def derive_struct_semantic(name: str) -> str:
    for pat, template in STRUCT_HINTS:
        m = pat.match(name)
        if m:
            word = m.group(1)
            # Camel → snake-ish
            spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", word).strip()
            return template.format(spaced.lower())
    return f"Estructura protobuf ({name})."


def derive_enum_semantic(name: str) -> str:
    for pat, template in ENUM_HINTS:
        m = pat.match(name)
        if m:
            if m.lastindex and m.group(1):
                word = m.group(1)
                spaced = re.sub(r"([a-z])([A-Z])", r"\1 \2", word).strip()
                return template.format(spaced.lower())
            return template
    return f"Enumeración protobuf {name}."


def fmt_ref(file_ref: str, linea: int) -> str:
    """Renderiza `fuente:ruta:linea` (sin prefijo `SRC/`)."""
    parts = file_ref.split(":", 1)
    if len(parts) == 2:
        fuente = "src"
        ruta = parts[1]
    else:
        fuente = "appflowy"
        ruta = file_ref
    ruta_clean = re.sub(r"^SRC/[^/]+/", "", ruta)
    fuente_clean = "appflowy"
    return f"`{fuente_clean}:{ruta_clean}:{linea}`"


def crate_of(entity: dict) -> str:
    """Devuelve el nombre del crate (parte `frontend/rust-lib/<crate>/src/...`)."""
    file_ref = entity.get("file", "")
    m = re.search(r"rust-lib/([^/]+)/src/", file_ref)
    if m:
        return m.group(1)
    m = re.search(r"rust-lib/([^/]+)/", file_ref)
    if m:
        return m.group(1)
    return "?"


def md_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |"]
    out.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for r in rows:
        out.append("| " + " | ".join(r) + " |")
    return out


def render(pb: dict) -> str:
    entities = pb["entities"]
    summary = pb["summary"]
    cross_ref = pb.get("cross_ref", {})

    total = summary["total_entities"]
    n_structs = summary["total_structs"]
    n_enums = summary["total_enums"]
    n_resolved_in = len(cross_ref.get("resolved_inputs", []))
    n_resolved_out = len(cross_ref.get("resolved_outputs", []))
    n_missing = len(cross_ref.get("missing_event_pbs", []))
    n_unique_in = len(cross_ref.get("unique_event_inputs", []))
    n_unique_out = len(cross_ref.get("unique_event_outputs", []))

    # Group entities by crate
    by_crate: dict[str, list[dict]] = defaultdict(list)
    for e in entities:
        by_crate[crate_of(e)].append(e)

    # Crates ordered by n entities desc
    crate_order = sorted(by_crate.keys(), key=lambda k: (-len(by_crate[k]), k))

    # Huérfanas: ni input_of ni output_of
    huerfanas = [
        e for e in entities
        if not (e.get("is_input_of") or []) and not (e.get("is_output_of") or [])
    ]
    n_huerfanas = len(huerfanas)

    out: list[str] = []

    # Frontmatter
    archivos_cubiertos = []
    for c in crate_order:
        archivos_cubiertos.append(
            f"appflowy/frontend/rust-lib/{c}/src/**/*.rs"
        )
    archivos_cubiertos.append(
        "appflowy/frontend/rust-lib/build-tool/flowy-derive/src/lib.rs"
    )
    fm = [
        "---",
        "id: 12-catalogo-entidades-protobuf",
        "titulo: Catálogo de entidades protobuf",
        "fuente: appflowy",
        "archivos_cubiertos:",
    ]
    for a in archivos_cubiertos:
        fm.append(f"  - {a}")
    fm.extend(["estado: verificado", "---"])
    out.extend(fm)
    out.append("")

    out.append("# 12 — Catálogo de entidades protobuf (struct + enum)")
    out.append("")
    out.append(
        f"Este documento cataloga las **{total} entidades protobuf** "
        f"({n_structs} structs + {n_enums} enums) extraídas por "
        "`SKILL/scripts/extract_protobuf.py` (Fase A2.2; validador "
        "`validate-A2.2.sh` 8/8 OK). Cada entidad se declara en un "
        "`frontend/rust-lib/<crate>/src/**/*.rs` con `#[derive(ProtoBuf)]` "
        "(struct) o `#[derive(ProtoBuf_Enum)]` (enum) y se codifica en "
        "tiempo de compilación por `flowy-derive` "
        "(`build-tool/flowy-derive/src/lib.rs`) hacia bincode que cruza "
        "la frontera FFI dentro de `FFIRequest.payload` o se devuelve en "
        "`FFIResponse.payload`. La fuente de datos es "
        "`OUT/_ledger/extract/protobuf.json` y la prueba del ROADMAP "
        "exige que el nº de filas de este catálogo sea exactamente "
        f"**{total}**. **Cross-ref**: "
        f"{n_resolved_in} inputs + {n_resolved_out} outputs = "
        f"{n_resolved_in + n_resolved_out} entidades referenciadas "
        "por eventos FFI (B2.1); las **" + str(n_huerfanas) + " restantes** "
        "se documentan como payload interno, notificaciones (B2.4) o "
        "serialización."
    )
    out.append("")

    # §1
    out.append("## 1. Cómo leer este catálogo")
    out.append("")
    out.append(
        "Cada fila representa una entidad `#[derive(ProtoBuf)]` o "
        "`#[derive(ProtoBuf_Enum)]`. Las columnas son: "
        "`#` (ordinal dentro del crate), `Entidad` (nombre en "
        "`UpperCamelCase`), `Tipo` (`struct` / `enum`), `Campos` "
        "(nº de fields; en `enum` es nº de variantes), `Inputs de` "
        "(lista de nombres de eventos FFI cuya firma la consume como "
        "input — `—` si ninguno), `Outputs de` (idem como output), "
        "`Archivo` (`ruta:línea` resuelto contra `inventario.json`). "
        "La semántica breve se deriva siempre del nombre + los "
        "fields/variants + los derives; va etiquetada `[INFERIDO]` "
        "porque `extract_protobuf.py` no captura `///` doc-comments. "
        "Las entidades que no son ni input ni output de un evento "
        "(`huérfanas`) se enumeran en §6 con su `Crate` para "
        "clasificarlas como payload de notificación, payload de "
        "export/import, struct interno del manager, etc."
    )
    out.append("")

    # §2 arquitectura del codegen
    out.append("## 2. Arquitectura del codegen")
    out.append("")
    out.append(
        "El siguiente diagrama muestra cómo una struct `#[derive(ProtoBuf)]` "
        "se transforma en binario binario cruzando la FFI: `flowy-derive` "
        "expande el `derive` en `impl ProtoBuf for X { fn write_to_bytes() … }` "
        "y `impl TryFrom<&[u8]> for X { fn from_bytes() … }`; el código "
        "Dart se genera en build a partir de los mismos derives vía "
        "`flowy-codegen` (sub-doc `06-puente-flutter-rust/03-codegen.md`)."
    )
    out.append("")
    out.append("```mermaid")
    out.append("flowchart LR")
    out.append("  subgraph Rust[\"Rust (rust-lib)\"]")
    out.append("    S[\"struct X { #[pb(index=N)] field: T }\"]")
    out.append("    Derive[\"#[derive(ProtoBuf)]\"]")
    out.append("    Expand[\"flowy-derive expand\"]")
    out.append("    Bincode[\"X → Vec&lt;u8&gt;\"]")
    out.append("    Req[\"FFIRequest{ event, payload: Vec&lt;u8&gt; }\"]")
    out.append("  end")
    out.append("  subgraph FFI[\"Frontera C (dart-ffi)\"]")
    out.append("    AsyncEv[\"async_event(lib.rs:175)\"]")
    out.append("    Dispatch[\"AFPluginDispatcher\"]")
    out.append("    Handler[\"handler.rs → FlowyResult&lt;Y&gt;\"]")
    out.append("    Resp[\"FFIResponse{ payload: Vec&lt;u8&gt; }\"]")
    out.append("  end")
    out.append("  subgraph Dart[\"Dart (packages/appflowy_backend)\"]")
    out.append("    XGen[\"class XPB { factory XPB.fromBuffer(Uint8List) }\"]")
    out.append("    Bloc[\"BLoC consumidor\"]")
    out.append("  end")
    out.append("  S --> Derive --> Expand --> Bincode")
    out.append("  Bincode --> Req --> AsyncEv --> Dispatch --> Handler --> Resp")
    out.append("  Resp --> XGen --> Bloc")
    out.append("```")
    out.append("")
    out.append(
        "Lectura: el derive `ProtoBuf` se expande en tiempo de compilación "
        "en `lib_bincode` (`protobuf-rust`) y se serializa con un esquema "
        "fijo (tag + longitud + valor para cada `#[pb(index=N)]`). El "
        "byte-array resultante se embebe en `FFIRequest.payload` y cruza "
        "la frontera vía `async_event`. El handler Rust deserializa con "
        "`X::try_from(bytes)`, ejecuta su lógica y devuelve otra entidad "
        "(`Y`) en `FFIResponse.payload`. En Dart, el código generado por "
        "`flowy-codegen` reconstruye la clase con `fromBuffer(Uint8List)`."
    )
    out.append("")

    # §3 resumen por crate
    out.append("## 3. Resumen por crate")
    out.append("")
    headers_t = ["Crate", "Structs", "Enums", "Total", "Inputs de eventos", "Outputs de eventos", "Huérfanas"]
    rows3: list[list[str]] = []
    for c in crate_order:
        ents = by_crate[c]
        n_s = sum(1 for e in ents if e.get("kind") == "struct")
        n_e = sum(1 for e in ents if e.get("kind") == "enum")
        in_ev = sum(1 for e in ents if (e.get("is_input_of") or []))
        out_ev = sum(1 for e in ents if (e.get("is_output_of") or []))
        h = sum(
            1 for e in ents
            if not (e.get("is_input_of") or []) and not (e.get("is_output_of") or [])
        )
        rows3.append([
            f"`{c}`",
            str(n_s),
            str(n_e),
            str(n_s + n_e),
            str(in_ev),
            str(out_ev),
            str(h),
        ])
    for line in md_table(headers_t, rows3):
        out.append(line)
    out.append("")
    out.append(
        f"**Total**: {total} entidades en {len(by_crate)} crates. "
        f"**{n_resolved_in + n_resolved_out}** están en `is_input_of`/"
        "`is_output_of` de al menos un evento (B2.1); **" + str(n_huerfanas) +
        f"** son `huérfanas` (sin uso directo en eventos). Cobertura "
        f"cross-ref con B2.1: `{n_missing}` `missing_event_pbs` (esperado 0)."
    )
    out.append("")

    # §4 índice global
    out.append(f"## 4. Índice global de las {total} entidades")
    out.append("")
    out.append(
        "Tabla plana con las 439 entidades ordenadas por `(crate, nombre)`. "
        "Cada fila es una entidad que también aparecerá en §5.<crate>. El "
        "conteo de filas de §4 y de la suma de filas de §5.* debe ser "
        f"exactamente **{total}** (prueba literal del ROADMAP). Las "
        f"entidades con campos vacíos en `Inputs de` y `Outputs de` son "
        "`huérfanas` (se enumeran en §6)."
    )
    out.append("")
    headers4 = ["Crate", "#", "Entidad", "Tipo", "Campos", "Inputs de", "Outputs de", "Archivo"]
    rows4: list[list[str]] = []
    sorted_entities = []
    for c in crate_order:
        ents = sorted(by_crate[c], key=lambda e: e["name"])
        sorted_entities.extend((c, idx, e) for idx, e in enumerate(ents, 1))

    for c, idx, e in sorted_entities:
        n_fields = (
            len(e.get("fields") or [])
            if e.get("kind") == "struct"
            else len(e.get("variants") or [])
        )
        in_of = e.get("is_input_of") or []
        out_of = e.get("is_output_of") or []
        in_cell = "<br/>".join(f"`{x}`" for x in in_of[:3])
        if len(in_of) > 3:
            in_cell += f"<br/>… +{len(in_of) - 3}"
        out_cell = "<br/>".join(f"`{x}`" for x in out_of[:3])
        if len(out_of) > 3:
            out_cell += f"<br/>… +{len(out_of) - 3}"
        rows4.append([
            f"`{c}`",
            str(idx),
            f"`{e['name']}`",
            e["kind"],
            str(n_fields),
            in_cell or "—",
            out_cell or "—",
            fmt_ref(e["file"], e["decl_line"]),
        ])
    for line in md_table(headers4, rows4):
        out.append(line)
    out.append("")

    # §5 catálogo por crate
    out.append("## 5. Catálogo por crate")
    out.append("")
    out.append(
        "Cada sub-sección desarrolla un crate. Las tablas siguen el "
        "mismo esquema que §4 (sin la columna `Crate` redundante). "
        "Cuando un crate supera las 20 entidades, se acompaña de un "
        "`flowchart LR` que agrupa los nombres por prefijo."
    )
    out.append("")
    for idx, c in enumerate(crate_order, 1):
        ents = sorted(by_crate[c], key=lambda e: e["name"])
        anchor = c.replace("-", "_")
        out.append(f"### 5.{idx} `{c}`")
        out.append("")
        n_s = sum(1 for e in ents if e.get("kind") == "struct")
        n_e = sum(1 for e in ents if e.get("kind") == "enum")
        out.append(f"**{len(ents)} entidades** ({n_s} structs + {n_e} enums).")
        out.append("")
        if len(ents) >= 20:
            out.append("```mermaid")
            out.append("flowchart LR")
            out.append(f"  subgraph C{anchor}[\"{c}\"]")
            prefixes: dict[str, list[str]] = {}
            for e in ents:
                m = re.match(r"^([A-Z][a-z]+)", e["name"])
                p = m.group(1) if m else "Other"
                prefixes.setdefault(p, []).append(e["name"])
            for p, names in sorted(prefixes.items()):
                node_id = f"{anchor}_{p}"
                labels = "<br/>".join(names[:8])
                if len(names) > 8:
                    labels += f"<br/>… +{len(names) - 8}"
                out.append(f'    {node_id}["{p}<br/>({len(names)}):<br/>{labels}"]')
            out.append("  end")
            out.append("```")
            out.append("")
        headers5 = ["#", "Entidad", "Tipo", "Campos", "Inputs de", "Outputs de", "Archivo", "Semántica"]
        rows5: list[list[str]] = []
        for i, e in enumerate(ents, 1):
            n_fields = (
                len(e.get("fields") or [])
                if e.get("kind") == "struct"
                else len(e.get("variants") or [])
            )
            in_of = e.get("is_input_of") or []
            out_of = e.get("is_output_of") or []
            in_cell = "<br/>".join(f"`{x}`" for x in in_of[:3])
            if len(in_of) > 3:
                in_cell += f"<br/>… +{len(in_of) - 3}"
            out_cell = "<br/>".join(f"`{x}`" for x in out_of[:3])
            if len(out_of) > 3:
                out_cell += f"<br/>… +{len(out_of) - 3}"
            sem = (
                derive_struct_semantic(e["name"])
                if e.get("kind") == "struct"
                else derive_enum_semantic(e["name"])
            )
            rows5.append([
                str(i),
                f"`{e['name']}`",
                e["kind"],
                str(n_fields),
                in_cell or "—",
                out_cell or "—",
                fmt_ref(e["file"], e["decl_line"]),
                f"{sem} `[INFERIDO]`",
            ])
        for line in md_table(headers5, rows5):
            out.append(line)
        out.append("")

    # §6 huérfanas
    out.append("## 6. Entidades sin uso en eventos (huérfanas)")
    out.append("")
    out.append(
        f"Hay **{n_huerfanas} entidades** que no aparecen en `is_input_of` "
        "ni en `is_output_of` de ningún evento FFI de B2.1. Esto puede "
        "deberse a: payload de notificación (`flowy-notification`, "
        "B2.4), payload de export/import (`filter`/`type_control`/etc., "
        "Bloque B4), struct interno de un manager, o entidad pendiente "
        "de uso. El muestreo en auditoría debe verificar ≥ 30 % de "
        "esta lista para descartar errores del extractor."
    )
    out.append("")
    headers6 = ["#", "Entidad", "Tipo", "Campos", "Crate", "Archivo", "Estado"]
    rows6: list[list[str]] = []
    h_sorted = sorted(huerfanas, key=lambda e: (crate_of(e), e["name"]))
    for i, e in enumerate(h_sorted, 1):
        n_fields = (
            len(e.get("fields") or [])
            if e.get("kind") == "struct"
            else len(e.get("variants") or [])
        )
        rows6.append([
            str(i),
            f"`{e['name']}`",
            e["kind"],
            str(n_fields),
            f"`{crate_of(e)}`",
            fmt_ref(e["file"], e["decl_line"]),
            "Huérfana `[INFERIDO]`",
        ])
    for line in md_table(headers6, rows6):
        out.append(line)
    out.append("")
    out.append(
        "Cada entidad va con su `ruta:línea` resuelta en `inventario.json` "
        "(el test `validate_evidence` falla si falta). El campo `Crate` "
        "permite triage por origen (p. ej. `flowy-search` probablemente "
        "tiene entidades internas del índice tantivy; `flowy-notification` "
        "tiene el payload de `NotificationBuilder`)."
    )
    out.append("")

    # §7 prueba literal
    out.append("## 7. Conteo de filas y prueba literal")
    out.append("")
    out.append(
        f"La prueba del ROADMAP exige que el número de filas del catálogo "
        f"sea exactamente **{total}** (= `protobuf.json::summary.total_entities`). "
        "El script `OUT/_ledger/pruebas/B2.2/count_rows_439.py` cuenta las "
        "filas de §4 y de la suma de §5.*; debe coincidir. Las filas de §6 "
        f"deben sumar {n_huerfanas}. El comando canónico externo:"
    )
    out.append("")
    out.append("```bash")
    out.append(
        f"jq '.summary.total_entities' \\\n"
        f"  OUT/_ledger/extract/protobuf.json   # esperado: {total}"
    )
    out.append("```")
    out.append("")

    # §8 cobertura
    out.append("## 8. Cobertura y referencias cruzadas")
    out.append("")
    out.append(
        f"- **B2.1 — `11-catalogo-eventos-ffi.md`**: cada `Input PB` / "
        "`Output PB` de las 229 variantes debe existir aquí. "
        f"`cross_ref.missing_event_pbs` está en **{n_missing}** "
        "(esperado 0; la validación A2.2 lo verifica)."
    )
    out.append("- **B1.5 — `06-puente-flutter-rust/03-codegen.md`**: "
        "los macros `ProtoBuf`, `ProtoBuf_Enum`, `Flowy_Event` y el "
        "generador `flowy-codegen`.")
    out.append("- **B2.4 — `14-catalogo-notificaciones.md`**: cada "
        "`NotificationBuilder.send_notification(<PB>)` referencia una "
        "entidad de este catálogo (probablemente la mayoría de las "
        f"{n_huerfanas} huérfanas).")
    out.append("- **Bloque B4 — export/import**: entidades con sufijo "
        "`Export*PB` o `Import*PB` se referencian desde "
        "`10-motor-export-import/`.")
    out.append("- **Bloque B3 — F01–F17**: cada feature documenta las "
        "entidades que manipula en su(s) sección(es) `Payloads` / "
        "`Entidades`.")
    out.append("")

    # §9 preguntas abiertas
    out.append("## 9. Preguntas abiertas")
    out.append("")
    out.append(
        "Sin entradas por ahora. Si el revisor detecta entidades cuya "
        "semántica no sea derivable (p. ej. `TypeOptionData` con 30+ "
        "fields, structs `DB` con un solo `value: String`), se volcará "
        "una entrada `[NO DETERMINADO]` aquí y en `OUT/22-preguntas-abiertas.md`."
    )
    out.append("")

    # §10 relacionado con
    out.append("## 10. Relacionado con")
    out.append("")
    out.append("- `06-puente-flutter-rust/03-codegen.md` — `flowy-derive`, "
        "`flowy-codegen`, macros `ProtoBuf*`.")
    out.append("- `06-puente-flutter-rust/01-ffi.md` — `FFIRequest`, "
        "`FFIResponse`, `FFIStatusCode`.")
    out.append("- `11-catalogo-eventos-ffi.md` — 229 eventos FFI que "
        "consumen estas entidades.")
    out.append("- `B0.1` — `protobuf.json` con `validate-A2.2.sh` 8/8 OK.")
    out.append("- `B2.4` — entidades emitidas vía `send_notification`.")
    out.append("- `B4` — entidades `Export*PB` / `Import*PB`.")
    out.append("")

    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="build_catalog_protobuf.py")
    p.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    p.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args(argv)

    pb = json.loads(args.input.read_text(encoding="utf-8"))
    if len(pb["entities"]) != pb["summary"]["total_entities"]:
        print(
            f"build_catalog_protobuf.py: INCONSISTENCIA protobuf.json: "
            f"len(entities)={len(pb['entities'])} vs summary.total_entities="
            f"{pb['summary']['total_entities']}",
            file=sys.stderr,
        )
        return 2

    text = render(pb)
    args.output.write_text(text, encoding="utf-8")
    if not args.quiet:
        print(
            f"OK: {args.output} escrito · "
            f"{pb['summary']['total_entities']} entidades · "
            f"{len(text.splitlines())} líneas"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())