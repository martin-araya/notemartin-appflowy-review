#!/usr/bin/env python3
# extract_notifications.py — Recorre
#   SRC/appflowy/frontend/rust-lib/**/notification.rs (y archivos que
#   llamen a `send_notification` o `NotificationBuilder::new`)
# y
#   SRC/appflowy/frontend/appflowy_flutter/lib/core/notification/*.dart
#   y **/*_listener.dart
# y emite OUT/_ledger/extract/notifications.json con:
#   - rust_notifications: enums `*Notification` con sus variantes,
#     observable_source, y todos los emitters que las usan.
#   - dart_listeners: listeners Dart y las variantes que manejan.
#   - variant_usage: cruce por variante (emitida_en_rust, has_dart_listener).
#   - rust_source_mismatches: parsers Dart cuyo _source no encuentra enum.
#
# Ver AGENTS.md §5.1 y ROADMAP.md A2.3.
#
# Uso:
#   extract_notifications.py [--src-root DIR] [--out-dir DIR]
#                            [--fuente NAME]... [--help]

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------- constantes ----------

SCRIPT_PATH = Path(__file__).resolve()
SKILL_ROOT = SCRIPT_PATH.parent.parent.parent
SRC_DEFAULT = SKILL_ROOT / "SRC"
OUT_DIR_DEFAULT = SKILL_ROOT / "OUT" / "_ledger" / "extract"
DEFAULT_FUENTES = ("appflowy",)
RUSTLIB_REL = Path("frontend/rust-lib")
FLUTTER_LIB_REL = Path("frontend/appflowy_flutter/lib")

SCHEMA_VERSION = "1.0"
TOOL_NAME = "extract_notifications.py"
TOOL_VERSION = "1.0"

EXCLUDE_DIRS = {".git", "target", "node_modules", "build", "dist"}


# ---------- regex ----------

# `pub enum XNotification { ... }` con `#[derive(... ProtoBuf_Enum, ...)]`
RE_DERIVE = re.compile(
    r"""
    \#\s*\[\s*derive\s*\(
      (?P<inner>[^)]*)
    \)\s*\]
    """,
    re.VERBOSE | re.DOTALL,
)
# Acepta: `pub enum`, `pub(crate) enum`, `pub(super) enum`, `pub(in path) enum`.
RE_ENUM_DECL = re.compile(
    r"^\s*pub(?:\s*\([^)]*\))?\s+enum\s+(?P<name>[A-Z][A-Za-z0-9_]*Notification)\b\s*(?P<generics><[^>]*>)?",
    re.MULTILINE,
)
# Variante: #[attrs] Name = N ,
RE_VARIANT = re.compile(
    r"""
    (?P<decl>
      (?:(?:\s*\#\s*\[[^\]]*\]\s*)*)?
      \s*
      (?P<name>[A-Z][A-Za-z0-9_]*)\s*=\s*(?P<index>-?\d+)
    )\s*,?
    """,
    re.VERBOSE,
)

# `const X_OBSERVABLE_SOURCE: &str = "Y";` (con/sin visibility, con/sin `pub(crate)`)
# Solo nombres que terminan en `_OBSERVABLE_SOURCE` o son exactamente `OBSERVABLE_SOURCE`.
RE_OBS_SOURCE = re.compile(
    r'^\s*(?:pub(?:\s*\([^)]*\))?\s+)?const\s+(?P<name>(?:[A-Z][A-Z0-9_]*_)?OBSERVABLE_SOURCE)\s*:\s*&str\s*=\s*"(?P<value>[^"]+)"',
    re.MULTILINE,
)

# `send_notification(id, EnumName::Variant)` — multilínea
RE_SEND_NOTIF = re.compile(
    r"""
    send_notification\s*\(
      (?P<args>[^)]+)
    \)
    """,
    re.VERBOSE | re.DOTALL,
)

# `NotificationBuilder::new(id, ty, source)` (con o sin `&`/`&str`)
RE_BUILDER_NEW = re.compile(
    r"""
    NotificationBuilder\s*::\s*new\s*\(
      (?P<args>[^)]+)
    \)
    """,
    re.VERBOSE | re.DOTALL,
)

# En una lista de argumentos, extraer el tipo (segundo arg) que es un enum path.
RE_ENUM_PATH = re.compile(r'([A-Z][A-Za-z0-9_]*)\s*::\s*([A-Z][A-Za-z0-9_]*)')
RE_BARE_NAME = re.compile(r'^\s*([A-Z][A-Za-z0-9_]*)\s*$')


# ---------- helpers ----------

def find_line_for_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def find_matching_brace(text: str, open_pos: int) -> int:
    """Devuelve la posición del `}` que cierra el `{` en `open_pos`."""
    depth = 0
    i = open_pos
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "/" and i + 1 < n and text[i + 1] == "/":
            j = text.find("\n", i)
            i = n if j == -1 else j + 1
            continue
        if ch == "/" and i + 1 < n and text[i + 1] == "*":
            j = text.find("*/", i + 2)
            i = n if j == -1 else j + 2
            continue
        if ch == '"':
            i += 1
            while i < n and text[i] != '"':
                if text[i] == "\\" and i + 1 < n:
                    i += 2
                else:
                    i += 1
            i += 1
            continue
        if ch == "'":
            i += 1
            while i < n and text[i] != "'":
                if text[i] == "\\" and i + 1 < n:
                    i += 2
                else:
                    i += 1
            i += 1
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return -1


def parse_derives(derive_attr_text: str) -> list:
    cleaned = []
    for line in derive_attr_text.split("\n"):
        in_str = False
        cut = len(line)
        for i, ch in enumerate(line):
            if ch == '"' and (i == 0 or line[i - 1] != "\\"):
                in_str = not in_str
            elif not in_str and ch == "/" and i + 1 < len(line) and line[i + 1] == "/":
                cut = i
                break
        cleaned.append(line[:cut])
    blob = " ".join(cleaned)
    return [d.strip() for d in blob.split(",") if d.strip()]


def split_top_level_args(args: str) -> list:
    """Parte los argumentos de una llamada por comas al nivel top (sin
    contar comas dentro de `<...>` o `()`)."""
    out = []
    depth_paren = 0
    depth_angle = 0
    cur = []
    for ch in args:
        if ch == "(":
            depth_paren += 1
            cur.append(ch)
        elif ch == ")":
            depth_paren -= 1
            cur.append(ch)
        elif ch == "<" and depth_paren == 0:
            depth_angle += 1
            cur.append(ch)
        elif ch == ">" and depth_paren == 0:
            depth_angle -= 1
            cur.append(ch)
        elif ch == "," and depth_paren == 0 and depth_angle == 0:
            out.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
    if cur:
        out.append("".join(cur).strip())
    return out


def extract_variant_from_type(type_expr: str):
    """Extrae (enum_name, variant_name) de una expresión de tipo.
    Acepta `EnumName::Variant` o `EnumName<...>::Variant`. Si no es
    un path de enum, devuelve (None, None).
    """
    s = type_expr.strip()
    # Quitar &, &mut, referencias y sufijos
    s = re.sub(r'^\s*&', '', s)
    s = s.strip()
    m = RE_ENUM_PATH.search(s)
    if m:
        return (m.group(1), m.group(2))
    # Bare name (posiblemente un identificador de tipo local)
    m = RE_BARE_NAME.match(s)
    if m:
        return (None, m.group(1))
    return (None, None)


def find_enum_at_offset(text: str, offset: int) -> tuple:
    """Busca el enum con `ProtoBuf_Enum` anterior a `offset`."""
    best = None
    for dm in RE_DERIVE.finditer(text, 0, offset):
        if "ProtoBuf_Enum" not in parse_derives(dm.group("inner")):
            continue
        # ¿Es el siguiente enum el que aplica?
        next_enum = None
        for cand in RE_ENUM_DECL.finditer(text, dm.end(), offset + 1):
            gap = text[dm.end():cand.start()]
            if re.fullmatch(r"[\s/\-#>!.\n\r,]*", gap):
                next_enum = cand
            else:
                break
        if next_enum is not None:
            best = (next_enum.group("name"), dm.end(), next_enum.start(), next_enum.end())
    return best if best else (None, None, None, None)


# ---------- extracción de enums Rust ----------

def parse_rust_notification_enum(path: Path, text: str, rel: str) -> dict:
    """Parsea el `*Notification` enum en un archivo de notificación Rust.
    Devuelve un dict con name, variants, observable_source, derives, decl_line.
    """
    # Encontrar la `pub enum XNotification {`.
    enum_match = None
    for em in RE_ENUM_DECL.finditer(text):
        # Verificar que el derive inmediatamente anterior contiene ProtoBuf_Enum.
        enum_name = em.group("name")
        enum_decl_line = find_line_for_offset(text, em.start())
        # Buscar el derive anterior más cercano. El gap entre el derive y el
        # enum puede contener otros atributos (p. ej. `#[repr(i32)]`,
        # `#[serde(...)]`), whitespace y comentarios, pero NO otra
        # declaración significativa (fn, struct, enum, impl, trait, mod, use).
        prev_derive = None
        for dm in RE_DERIVE.finditer(text, 0, em.start()):
            gap = text[dm.end():em.start()]
            # Quitar del gap todos los bloques `#[...]` y comentarios.
            gap_stripped = re.sub(r"#\s*\[[^\]]*\]", "", gap)
            gap_stripped = re.sub(r"//[^\n]*", "", gap_stripped)
            gap_stripped = re.sub(r"/\*.*?\*/", "", gap_stripped, flags=re.DOTALL)
            # Lo que queda debe ser solo whitespace y comas.
            if re.fullmatch(r"[\s,]*", gap_stripped):
                # Tampoco debe haber otro `#[derive(...)]` en el gap.
                if not re.search(r"#\s*\[\s*derive\s*\(", gap):
                    prev_derive = dm
            else:
                break
        if prev_derive is None:
            continue
        if "ProtoBuf_Enum" not in parse_derives(prev_derive.group("inner")):
            continue
        enum_match = (em, prev_derive)
        break
    if enum_match is None:
        return None
    em, dm = enum_match
    enum_name = em.group("name")
    enum_decl_line = find_line_for_offset(text, em.start())
    derives = parse_derives(dm.group("inner"))

    # Parsear variantes
    brace_pos = text.find("{", em.end())
    if brace_pos == -1:
        return None
    end_pos = find_matching_brace(text, brace_pos)
    if end_pos == -1:
        return None
    body = text[brace_pos + 1:end_pos]
    variants = []
    for vm in RE_VARIANT.finditer(body):
        vname = vm.group("name")
        if not vname:
            continue
        try:
            vidx = int(vm.group("index"))
        except (TypeError, ValueError):
            vidx = None
        # Detectar #[default] en los atributos previos
        attrs_text = body[vm.start("decl"):vm.start("name")]
        is_default = "#[default]" in attrs_text
        v_line = find_line_for_offset(text, brace_pos + 1 + vm.start("name"))
        variants.append({
            "name": vname,
            "index": vidx,
            "is_default": is_default,
            "decl_line": v_line,
        })
    variants.sort(key=lambda v: (v["index"] if v["index"] is not None else 9999))

    # observable_source
    obs = None
    for om in RE_OBS_SOURCE.finditer(text):
        # Aceptar el primero que esté antes del enum o en el mismo archivo
        obs = {
            "const_name": om.group("name"),
            "value": om.group("value"),
            "line": find_line_for_offset(text, om.start()),
        }
        break

    return {
        "name": enum_name,
        "file": rel,
        "crate": rel.split("/")[4] if len(rel.split("/")) > 4 else "<unknown>",
        "decl_line": enum_decl_line,
        "derives": derives,
        "observable_source": obs,
        "variants": variants,
    }


# ---------- extracción de emitters ----------

def find_emitters_in_rust_file(path: Path, text: str, rel: str, enum_by_source: dict, const_to_value: dict) -> list:
    """Encuentra todos los call sites de `send_notification(...)` y
    `NotificationBuilder::new(...)` y los asocia a un enum por la
    OBSERVABLE_SOURCE que aparezca en el cuerpo del builder (o por el
    source string en send_notification directa).
    """
    emitters = []

    # 1) `NotificationBuilder::new(id, ty, source)` — source es el tercer arg.
    for m in RE_BUILDER_NEW.finditer(text):
        args = split_top_level_args(m.group("args"))
        if len(args) < 3:
            continue
        type_arg = args[1]
        source_arg = args[2]
        enum_name, variant = extract_variant_from_type(type_arg)
        # Normalizar source: quitar &, comillas, espacios.
        source_clean = re.sub(r'^\s*&', '', source_arg).strip().strip('"')
        # Si source es un identificador (referencia a const), resolver.
        if source_clean in const_to_value:
            source_clean = const_to_value[source_clean]
        line = find_line_for_offset(text, m.start())
        emitters.append({
            "file": rel,
            "line": line,
            "kind": "NotificationBuilder::new",
            "source": source_clean,
            "enum_name": enum_name,
            "variant": variant,
            "raw": m.group(0)[:200],
        })

    # 2) `send_notification(id, ty)` — el source lo deducimos del enum_name.
    for m in RE_SEND_NOTIF.finditer(text):
        args = split_top_level_args(m.group("args"))
        if len(args) < 2:
            continue
        type_arg = args[1]
        enum_name, variant = extract_variant_from_type(type_arg)
        line = find_line_for_offset(text, m.start())
        emitters.append({
            "file": rel,
            "line": line,
            "kind": "send_notification",
            "source": None,  # se resuelve después por enum_name
            "enum_name": enum_name,
            "variant": variant,
            "raw": m.group(0)[:200],
        })

    return emitters


# ---------- extracción Dart ----------

RE_DART_SOURCE = re.compile(
    r"^\s*const\s+String\s+_source\s*=\s*['\"]([^'\"]+)['\"]",
    re.MULTILINE,
)
RE_DART_PARSER_CLASS = re.compile(
    r"^\s*class\s+(?P<name>[A-Z][A-Za-z0-9_]*NotificationParser)\b",
    re.MULTILINE,
)
RE_DART_VALUE_OF = re.compile(
    r"valueOf",
)
RE_DART_SWITCH = re.compile(
    r"switch\s*\(\s*ty\s*\)\s*\{(?P<body>[^}]*)\}",
    re.DOTALL,
)
RE_DART_CASE = re.compile(
    r"case\s+(?:[a-z_][A-Za-z0-9_]*\.)?(?P<enum>[A-Z][A-Za-z0-9_]*)\s*\.\s*(?P<variant>[A-Z][A-Za-z0-9_]*)\s*:"
)


def parse_dart_parser_file(path: Path, text: str, rel: str) -> dict:
    """Parsea un archivo `*_notification.dart` (parser)."""
    source_match = RE_DART_SOURCE.search(text)
    parser_match = RE_DART_PARSER_CLASS.search(text)
    return {
        "file": rel,
        "name": parser_match.group("name") if parser_match else None,
        "source": source_match.group(1) if source_match else None,
        "uses_valueOf": bool(RE_DART_VALUE_OF.search(text)),
    }


def parse_dart_listener_file(path: Path, text: str, rel: str) -> dict:
    """Parsea un `*_listener.dart`: encuentra el `switch (ty) { ... }`
    y extrae las variantes manejadas."""
    handled = []
    has_switch = False
    parser_name = None
    # Detectar parser (instanciación): `DocumentNotificationParser(...)` o
    # `_parser = DocumentNotificationParser(`
    m = re.search(r'(\b[A-Z][A-Za-z0-9]*NotificationParser)\s*\(', text)
    if m:
        parser_name = m.group(1)
    # Encontrar todos los `switch (ty) {` y balancear las llaves para
    # capturar el cuerpo completo (puede contener closures con `{}`).
    for sm in re.finditer(r"switch\s*\(\s*ty\s*\)\s*\{", text):
        start = sm.end() - 1  # posición de `{`
        # Balancear llaves a partir de `{` en `start`.
        depth = 0
        i = start
        n = len(text)
        in_str = None  # tipo de string actual
        while i < n:
            ch = text[i]
            if in_str:
                if ch == "\\" and i + 1 < n:
                    i += 2
                    continue
                if ch == in_str:
                    in_str = None
                i += 1
                continue
            if ch in ('"', "'"):
                in_str = ch
                i += 1
                continue
            if ch == "/" and i + 1 < n and text[i + 1] == "/":
                j = text.find("\n", i)
                i = n if j == -1 else j + 1
                continue
            if ch == "/" and i + 1 < n and text[i + 1] == "*":
                j = text.find("*/", i + 2)
                i = n if j == -1 else j + 2
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    body = text[start + 1:i]
                    has_switch = True
                    for cm in RE_DART_CASE.finditer(body):
                        handled.append({
                            "enum": cm.group("enum"),
                            "variant": cm.group("variant"),
                        })
                    break
            i += 1
    return {
        "file": rel,
        "name": path.stem.replace("_listener", "").replace("Listener", "Listener"),
        "parser": parser_name,
        "has_switch": has_switch,
        "handled_variants": handled,
    }


# ---------- CLI ----------

def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description=(
            "Extrae enums Rust `*Notification` + constantes "
            "`*_OBSERVABLE_SOURCE` + emitters `send_notification`/"
            "`NotificationBuilder::new`, y los listeners Dart que los "
            "manejan. Ver AGENTS.md §5.1 / ROADMAP.md A2.3."
        ),
    )
    p.add_argument("--src-root", type=Path, default=SRC_DEFAULT,
                   help=f"Raíz con SRC/<fuente> (default: {SRC_DEFAULT})")
    p.add_argument("--out-dir", type=Path, default=OUT_DIR_DEFAULT,
                   help=f"Directorio de salida (default: {OUT_DIR_DEFAULT})")
    p.add_argument("--fuente", action="append", default=None,
                   help=f"Fuente(s) a procesar (default: {list(DEFAULT_FUENTES)})")
    p.add_argument("-v", "--verbose", action="store_true", help="Log detallado a stderr")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    src_root: Path = args.src_root.resolve()
    out_dir: Path = args.out_dir.resolve()
    fuentes = args.fuente if args.fuente else list(DEFAULT_FUENTES)

    if not src_root.is_dir():
        print(f"ERROR: --src-root no es directorio: {src_root}", file=sys.stderr)
        return 2

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "notifications.json"

    rust_notifications = []
    all_emitters = []
    source_to_enum = {}   # source_value -> enum_name
    enum_to_source = {}   # enum_name -> source_value
    const_to_value = {}   # CONST_NAME -> "value" (para resolver referencias)

    for fuente in fuentes:
        rustlib = src_root / fuente / RUSTLIB_REL
        flutterlib = src_root / fuente / FLUTTER_LIB_REL
        if not rustlib.is_dir():
            if args.verbose:
                print(f"  [skip] no existe {rustlib}", file=sys.stderr)
            continue

        # FASE 1: parsear enums en archivos notification.rs
        notif_files = sorted(p for p in rustlib.rglob("notification.rs")
                             if not any(part in EXCLUDE_DIRS for part in p.parts))
        for nf in notif_files:
            rel = str(nf.relative_to(SKILL_ROOT))
            try:
                text = nf.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            # Recolectar TODOS los const *_OBSERVABLE_SOURCE del archivo
            for om in RE_OBS_SOURCE.finditer(text):
                const_to_value[om.group("name")] = om.group("value")
            enum_obj = parse_rust_notification_enum(nf, text, rel)
            if enum_obj is None:
                if args.verbose:
                    print(f"    [skip] {rel}: no enum ProtoBuf_Enum", file=sys.stderr)
                continue
            rust_notifications.append(enum_obj)
            if enum_obj["observable_source"]:
                source_to_enum[enum_obj["observable_source"]["value"]] = enum_obj["name"]
                enum_to_source[enum_obj["name"]] = enum_obj["observable_source"]["value"]

        # FASE 2: encontrar emitters en TODOS los .rs del rustlib
        all_rs = sorted(p for p in rustlib.rglob("*.rs")
                        if not any(part in EXCLUDE_DIRS for part in p.parts))
        for rs in all_rs:
            rel = str(rs.relative_to(SKILL_ROOT))
            try:
                text = rs.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            # Recolectar consts también en otros archivos del crate
            for om in RE_OBS_SOURCE.finditer(text):
                if om.group("name") not in const_to_value:
                    const_to_value[om.group("name")] = om.group("value")
            emitters = find_emitters_in_rust_file(rs, text, rel, source_to_enum, const_to_value)
            for e in emitters:
                # Resolver source si está en None (caso send_notification
                # con enum_name conocido): usar la source del enum.
                if e["source"] is None and e["enum_name"] in enum_to_source:
                    e["source"] = enum_to_source[e["enum_name"]]
                # Vincular al enum del crate si no se pudo inferir
                if e["enum_name"] is None and e["source"] in source_to_enum:
                    e["enum_name"] = source_to_enum[e["source"]]
            all_emitters.extend(emitters)

    # Asociar emitters a sus enums
    emitters_by_enum = {}
    for e in all_emitters:
        key = e["enum_name"] or "<unknown>"
        emitters_by_enum.setdefault(key, []).append(e)

    for enum_obj in rust_notifications:
        enum_obj["emitters"] = emitters_by_enum.get(enum_obj["name"], [])

    # FASE 3: parsers y listeners Dart
    dart_parsers = []
    dart_listeners = []
    if flutterlib.is_dir():
        # Parsers
        for f in sorted((flutterlib / "core" / "notification").glob("*_notification.dart")):
            rel = str(f.relative_to(SKILL_ROOT))
            try:
                text = f.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            p = parse_dart_parser_file(f, text, rel)
            if p.get("name") or p.get("source"):
                dart_parsers.append(p)
        # Listeners (en todo el lib, recursivo)
        for f in sorted(flutterlib.rglob("*_listener.dart")):
            if not f.is_file():
                continue
            rel = str(f.relative_to(SKILL_ROOT))
            try:
                text = f.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            l = parse_dart_listener_file(f, text, rel)
            if l["has_switch"] or l["parser"]:
                dart_listeners.append(l)

    # FASE 4: cruzar Rust↔Dart
    # Map source (Dart) -> enum name (Rust)
    # Y variantes manejadas por listener.
    variant_usage_by_enum = {}  # enum_name -> {variant -> usage dict}
    for enum_obj in rust_notifications:
        enum_name = enum_obj["name"]
        usage = {}
        for v in enum_obj["variants"]:
            usage[v["name"]] = {
                "emitted_in_rust": sum(
                    1 for e in enum_obj["emitters"]
                    if e.get("variant") == v["name"]
                ),
                "has_dart_listener": False,
                "status": "unused",
            }
        variant_usage_by_enum[enum_name] = usage

    # Mapear listener -> parser -> source -> enum.
    # Para cada listener, inferir su enum por el parser que usa.
    parser_to_source = {p["name"]: p["source"] for p in dart_parsers if p.get("name") and p.get("source")}
    for listener in dart_listeners:
        parser_name = listener["parser"]
        if not parser_name or parser_name not in parser_to_source:
            continue
        source = parser_to_source[parser_name]
        enum_name = source_to_enum.get(source)
        if not enum_name or enum_name not in variant_usage_by_enum:
            continue
        for handled in listener["handled_variants"]:
            vname = handled["variant"]
            if vname in variant_usage_by_enum[enum_name]:
                variant_usage_by_enum[enum_name][vname]["has_dart_listener"] = True

    # Calcular status
    for enum_name, usage in variant_usage_by_enum.items():
        for vname, u in usage.items():
            if u["emitted_in_rust"] > 0 and u["has_dart_listener"]:
                u["status"] = "ok"
            elif u["emitted_in_rust"] > 0 and not u["has_dart_listener"]:
                u["status"] = "emitted_only"
            elif u["emitted_in_rust"] == 0 and u["has_dart_listener"]:
                u["status"] = "declared_only"
            else:
                u["status"] = "unused"

    for enum_obj in rust_notifications:
        enum_obj["variant_usage"] = variant_usage_by_enum[enum_obj["name"]]

    # FASE 5: rust_source_mismatches (parsers Dart sin enum Rust)
    source_mismatches = []
    for p in dart_parsers:
        if p["source"] and p["source"] not in source_to_enum:
            source_mismatches.append({
                "parser": p["name"],
                "source": p["source"],
                "file": p["file"],
            })

    # Variantes sin listener Dart (resumen)
    variants_without_dart_listener = []
    for enum_obj in rust_notifications:
        for vname, u in enum_obj["variant_usage"].items():
            if not u["has_dart_listener"]:
                variants_without_dart_listener.append(f"{enum_obj['name']}::{vname}")

    # Validaciones internas
    for enum_obj in rust_notifications:
        for v in enum_obj["variants"]:
            assert v["name"] in enum_obj["variant_usage"], \
                f"variant {v['name']} missing from variant_usage"
    assert len(rust_notifications) > 0 or True  # aceptamos 0 (no abortar)

    out_obj = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tool": {"name": TOOL_NAME, "version": TOOL_VERSION},
        "fuentes": sorted(set(fuentes)),
        "rust_notifications": rust_notifications,
        "dart_parsers": dart_parsers,
        "dart_listeners": dart_listeners,
        "summary": {
            "total_rust_notifications": len(rust_notifications),
            "total_emitters": sum(len(e["emitters"]) for e in rust_notifications),
            "total_dart_parsers": len(dart_parsers),
            "total_dart_listeners": len(dart_listeners),
            "rust_source_mismatches": len(source_mismatches),
            "rust_source_mismatches_detail": source_mismatches,
            "variants_without_dart_listener": variants_without_dart_listener,
        },
    }
    out_path.write_text(json.dumps(out_obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Resumen a stderr
    print(f"  rust_notifications:    {len(rust_notifications)}", file=sys.stderr)
    print(f"  total_emitters:        {sum(len(e['emitters']) for e in rust_notifications)}", file=sys.stderr)
    print(f"  dart_parsers:          {len(dart_parsers)}", file=sys.stderr)
    print(f"  dart_listeners:        {len(dart_listeners)}", file=sys.stderr)
    print(f"  rust_source_mismatches:{len(source_mismatches)}", file=sys.stderr)
    print(f"  variants sin listener: {len(variants_without_dart_listener)}", file=sys.stderr)
    for enum_obj in rust_notifications:
        n_with_dart = sum(1 for u in enum_obj["variant_usage"].values() if u["has_dart_listener"])
        n_total = len(enum_obj["variants"])
        print(f"    {enum_obj['name']:35s} {n_with_dart}/{n_total} variants con listener Dart, "
              f"{len(enum_obj['emitters'])} emitters", file=sys.stderr)
    print(f"  escrito:               {out_path}", file=sys.stderr)
    if source_mismatches:
        print(f"  source_mismatches (parsers Dart sin enum Rust):", file=sys.stderr)
        for m in source_mismatches:
            print(f"    - {m['parser']}: _source='{m['source']}' en {m['file']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
