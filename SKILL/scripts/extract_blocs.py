#!/usr/bin/env python3
# extract_blocs.py — Recorre `lib/**/*.dart` bajo appflowy_flutter y
#   emite `OUT/_ledger/extract/blocs.json` con todas las clases
#   `extends Bloc<…>` o `extends Cubit<…>`, sus eventos y estados
#   (freezed), servicios inyectados, archivo:línea.
#
# Ver AGENTS.md §5.1 y ROADMAP.md A2.4.
#
# Uso:
#   extract_blocs.py [--src-root DIR] [--out-dir DIR]
#                     [--fuente NAME]... [--help]

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ---------- constantes ----------

SCRIPT_PATH = Path(__file__).resolve()
SKILL_ROOT = SCRIPT_PATH.parent.parent.parent
SRC_DEFAULT = SKILL_ROOT / "SRC"
OUT_DIR_DEFAULT = SKILL_ROOT / "OUT" / "_ledger" / "extract"
DEFAULT_FUENTES = ("appflowy",)
FLUTTER_LIB_REL = Path("frontend/appflowy_flutter/lib")

SCHEMA_VERSION = "1.0"
TOOL_NAME = "extract_blocs.py"
TOOL_VERSION = "1.0"

EXCLUDE_DIRS = {".git", ".dart_tool", "build", ".idea", ".gradle", "Pods"}
EXCLUDE_FILE_SUFFIXES = (
    ".g.dart",
    ".freezed.dart",
    ".config.dart",
    ".gr.dart",
    ".mocks.dart",
    ".pb.dart",
)


# ---------- regex ----------

# `class XBloc extends Bloc<XEvent, XState> {` (con o sin `with`).
RE_CLASS_DECL = re.compile(
    r"^\s*class\s+(?P<name>[A-Z]\w+)\s+extends\s+(?P<kind>Bloc|Cubit)\s*<\s*(?P<generics>[^>]+?)\s*>",
    re.MULTILINE,
)

# `@freezed class XEvent with _$XEvent {` — NO consume la `{` final
# para que `find("{", fm.end())` apunte a la `{` de apertura del body.
RE_FREEZED_CLASS = re.compile(
    r"@freezed\s+class\s+(?P<name>\w+)\s+with\s+_\$\w+\s*",
    re.MULTILINE,
)

# `const factory XEvent.foo(args) = ConcreteName;` (multilínea, freezed-style).
# `const` opcional para soportar clases sealed sin `const`.
# Usa `[\s\S]*?` para partes que pueden abarcar saltos de línea (p. ej.
# `factory X.setCustomPath(String path) =\n    Concrete;`).
RE_FREEZED_FACTORY = re.compile(
    r"(?:const\s+)?factory\s+(?P<cls>\w+)\s*\.\s*(?P<variant>\w+)\s*\((?P<args>[\s\S]*?)\)\s*=[\s\S]*?(?P<concrete>\w+)\s*;",
)

# `factory XEvent.foo(args) => Concrete(args);` (arrow form, sealed-class style).
RE_SEALED_FACTORY = re.compile(
    r"""
    (?:const\s+)?factory\s+(?P<cls>\w+)\s*\.\s*(?P<variant>\w+)\s*\((?P<args>.*?)\)\s*=>\s*
    (?P<concrete>\w+)\s*\(
    """,
    re.VERBOSE | re.DOTALL,
)

# Campo del state (dentro del factory principal): `required T name,` o `T name,` o `T name = default,`
# Tipo: nombre de clase (`Foo`, `Foo?`, `List<Foo>`, `Foo<T>?`) o primitivo
# Dart (`bool`, `int`, `double`, `num`, `String`, `dynamic`, `void`).
RE_FIELD = re.compile(
    r"""
    (?:(?P<required>required\s+(?:final\s+)?)?)
    (?P<type>(?:[A-Z]\w+|[a-z]+)(?:<[^>]+>)?(?:\??)?)
    \s+
    (?P<name>[a-z_]\w*)
    (?:\s*=\s*(?P<default>[^,]+?))?
    \s*[,}]
    """,
    re.VERBOSE,
)

# Servicio inyectado: `final T _name = T(...);` o `late final T _name = T(...);`
RE_INJECTED = re.compile(
    r"^\s*(?:late\s+)?final\s+(?P<type>\w+(?:<[^>]+>)?)\s+(?P<name>_\w+)\s*=\s*(?P<init>[^;]+);",
    re.MULTILINE,
)


# ---------- helpers ----------

def find_line_for_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def find_matching_brace(text: str, open_pos: int) -> int:
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


def split_generics(generics: str) -> list:
    """Parte una lista de generics tipo `A, B` por coma top-level."""
    out = []
    depth_paren = 0
    depth_angle = 0
    cur = []
    for ch in generics:
        if ch == "(":
            depth_paren += 1
            cur.append(ch)
        elif ch == ")":
            depth_paren -= 1
            cur.append(ch)
        elif ch == "<":
            depth_angle += 1
            cur.append(ch)
        elif ch == ">":
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


def strip_outer_extends(s: str) -> str:
    """Quita un prefijo `X extends Y` o `extends Y` para dejar solo `Y`."""
    s = s.strip()
    if " extends " in s:
        return s.split(" extends ", 1)[1].strip()
    return s


def parse_freezed_factories(text: str, class_name: str, brace_start: int, brace_end: int) -> list:
    """Devuelve la lista de factories dentro de un bloque freezed o sealed class.
    Acepta tanto `const factory X.foo(args) = Concrete;` (freezed) como
    `factory X.foo(args) => Concrete(args);` (sealed arrow).
    """
    body = text[brace_start + 1:brace_end]
    out = []
    # Patrón freezed: `const factory X.foo(args) = Concrete;`
    for m in RE_FREEZED_FACTORY.finditer(body):
        if m.group("cls") != class_name:
            continue
        line = find_line_for_offset(text, brace_start + 1 + m.start())
        out.append({
            "factory": f"{class_name}.{m.group('variant')}",
            "class": m.group("concrete"),
            "args_raw": m.group("args").strip(),
            "decl_line": line,
        })
    # Patrón sealed-class: `factory X.foo(args) => Concrete(args);`
    for m in RE_SEALED_FACTORY.finditer(body):
        if m.group("cls") != class_name:
            continue
        line = find_line_for_offset(text, brace_start + 1 + m.start())
        out.append({
            "factory": f"{class_name}.{m.group('variant')}",
            "class": m.group("concrete"),
            "args_raw": m.group("args").strip(),
            "decl_line": line,
        })
    return out


def parse_state_fields(text: str, factory_open_pos: int, factory_close_pos: int) -> list:
    """Extrae campos del factory principal de un state (entre `({` y `})`)."""
    body = text[factory_open_pos:factory_close_pos]
    out = []
    for m in RE_FIELD.finditer(body):
        name = m.group("name")
        if not name:
            continue
        # Evitar capturar palabras clave (factory, const)
        if name in ("factory", "const"):
            continue
        out.append({
            "name": name,
            "type": m.group("type").strip(),
            "required": bool(m.group("required")),
            "default": m.group("default").strip() if m.group("default") else None,
            "decl_line": find_line_for_offset(text, factory_open_pos + m.start()),
        })
    return out


# ---------- parseo por archivo ----------

def parse_dart_file(path: Path, text: str, rel: str, cross_file_event_index: Optional[dict] = None) -> dict:
    """Devuelve un dict con todos los blocs/cubits del archivo, sus eventos,
    estados y servicios inyectados. Si `cross_file_event_index` está dado
    (mapa `name -> (file_rel, brace_open, brace_close)`), se usa para resolver
    eventos definidos en otros archivos (caso de la arquitectura
    `features/*/logic/*_event.dart` con `sealed class`).
    """
    file_result = {
        "file": rel,
        "blocs": [],
    }

    # 1) Localizar todas las declaraciones `class X extends Bloc/Cubit<…>`.
    class_spans = []  # lista de (name, kind, generics, decl_line, open_brace, close_brace)
    for cm in RE_CLASS_DECL.finditer(text):
        name = cm.group("name")
        kind = cm.group("kind")
        generics = cm.group("generics")
        decl_line = find_line_for_offset(text, cm.start())
        # Encontrar la `{` de la clase (puede haber `with` después)
        brace_pos = text.find("{", cm.end())
        if brace_pos == -1:
            continue
        close_pos = find_matching_brace(text, brace_pos)
        if close_pos == -1:
            continue
        # Parsear generics → event_type, state_type
        params = split_generics(generics)
        event_type = None
        state_type = None
        if kind == "Bloc" and len(params) >= 2:
            event_type = strip_outer_extends(params[0])
            state_type = strip_outer_extends(params[1])
        elif kind == "Cubit" and len(params) >= 1:
            state_type = strip_outer_extends(params[0])
        class_spans.append({
            "name": name,
            "kind": kind,
            "event_type": event_type,
            "state_type": state_type,
            "decl_line": decl_line,
            "open_brace": brace_pos,
            "close_brace": close_pos,
        })

    # 2) Localizar todos los `@freezed class` para vincularlos.
    freezed = {}  # name → (open_brace, close_brace)
    for fm in RE_FREEZED_CLASS.finditer(text):
        name = fm.group("name")
        brace_pos = text.find("{", fm.end())
        if brace_pos == -1:
            continue
        close_pos = find_matching_brace(text, brace_pos)
        if close_pos == -1:
            continue
        freezed[name] = (brace_pos, close_pos)

    # 2b) Localizar `sealed class XEvent` (nueva arquitectura features/).
    # Captura `const factory XEvent.foo(args) = ConcreteName;` dentro del sealed.
    # NO consume la `{` final para que `find("{", end)` apunte a la `{` correcta.
    sealed_events = {}  # name → list of factories
    RE_SEALED_CLASS = re.compile(
        r"^\s*sealed\s+class\s+(?P<name>\w+)\s*(?:<[^>]+>)?\s*",
        re.MULTILINE,
    )
    for sm in RE_SEALED_CLASS.finditer(text):
        name = sm.group("name")
        brace_pos = text.find("{", sm.end())
        if brace_pos == -1:
            continue
        close_pos = find_matching_brace(text, brace_pos)
        if close_pos == -1:
            continue
        body = text[brace_pos + 1:close_pos]
        factories = []
        # Patrón freezed: `const factory X.foo(args) = Concrete;`
        for fm in RE_FREEZED_FACTORY.finditer(body):
            if fm.group("cls") != name:
                continue
            line = find_line_for_offset(text, brace_pos + 1 + fm.start())
            factories.append({
                "factory": f"{name}.{fm.group('variant')}",
                "class": fm.group("concrete"),
                "args_raw": fm.group("args").strip(),
                "decl_line": line,
            })
        # Patrón sealed-class: `factory X.foo(args) => Concrete(args);`
        for fm in RE_SEALED_FACTORY.finditer(body):
            if fm.group("cls") != name:
                continue
            line = find_line_for_offset(text, brace_pos + 1 + fm.start())
            factories.append({
                "factory": f"{name}.{fm.group('variant')}",
                "class": fm.group("concrete"),
                "args_raw": fm.group("args").strip(),
                "decl_line": line,
            })
        if factories:
            sealed_events[name] = (brace_pos, close_pos, factories)

    # 3) Para cada bloc, extraer eventos/estados y servicios inyectados.
    for cs in class_spans:
        events = []
        state_fields = []
        state_factory_initial = None
        events_source = None
        if cs["event_type"] and cs["event_type"] in freezed:
            ob, cb = freezed[cs["event_type"]]
            events = parse_freezed_factories(text, cs["event_type"], ob, cb)
            events_source = "freezed (same file)"
        elif cs["event_type"] and cs["event_type"] in sealed_events:
            events = sealed_events[cs["event_type"]][2]
            events_source = "sealed (same file)"
        elif cs["event_type"] and cross_file_event_index and cs["event_type"] in cross_file_event_index:
            cf_file, cf_text, cf_brace = cross_file_event_index[cs["event_type"]]
            events = parse_freezed_factories(cf_text, cs["event_type"], cf_brace[0], cf_brace[1])
            events_source = f"sealed/factory (cross-file: {cf_file})"
        if cs["state_type"] and cs["state_type"] in freezed:
            ob, cb = freezed[cs["state_type"]]
            body = text[ob + 1:cb]
            main_factory = re.search(
                r"const\s+factory\s+" + re.escape(cs["state_type"]) +
                r"\s*\(\s*\{(?P<inner>.*?)\}\s*\)\s*=\s*_\w+\s*;",
                body, re.DOTALL,
            )
            if main_factory:
                inner_open = ob + 1 + main_factory.start("inner")
                state_fields = parse_state_fields(text, inner_open, inner_open + len(main_factory.group("inner")))
            initial_factory = re.search(
                r"factory\s+" + re.escape(cs["state_type"]) + r"\s*\.\s*(\w+)\s*\(",
                body,
            )
            if initial_factory:
                state_factory_initial = {
                    "name": f"{cs['state_type']}.{initial_factory.group(1)}",
                    "decl_line": find_line_for_offset(text, ob + 1 + initial_factory.start()),
                }

        # Injected services en el cuerpo del bloc.
        bloc_body = text[cs["open_brace"] + 1:cs["close_brace"]]
        injected = []
        for im in RE_INJECTED.finditer(bloc_body):
            injected.append({
                "name": im.group("name"),
                "type": im.group("type"),
                "is_late": "late" in im.group(0).split("final", 1)[0],
                "init": im.group("init").strip(),
                "decl_line": find_line_for_offset(text, cs["open_brace"] + 1 + im.start()),
            })

        file_result["blocs"].append({
            "name": cs["name"],
            "kind": cs["kind"],
            "file": rel,
            "decl_line": cs["decl_line"],
            "event_type": cs["event_type"],
            "state_type": cs["state_type"],
            "events": events,
            "events_source": events_source,
            "state_fields": state_fields,
            "state_factory_initial": state_factory_initial,
            "injected_services": injected,
        })

    return file_result


# ---------- CLI ----------

def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description=(
            "Extrae clases `extends Bloc<…>` o `extends Cubit<…>` desde "
            "SRC/<fuente>/frontend/appflowy_flutter/lib/**/*.dart, con sus "
            "eventos/estados freezed y servicios inyectados. "
            "Ver AGENTS.md §5.1 / ROADMAP.md A2.4."
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
    out_path = out_dir / "blocs.json"

    all_blocs = []
    files_scanned = 0
    cross_file_event_index = {}  # event_name -> (file_rel, text, (brace_open, brace_close))

    for fuente in fuentes:
        flutterlib = src_root / fuente / FLUTTER_LIB_REL
        if not flutterlib.is_dir():
            if args.verbose:
                print(f"  [skip] no existe {flutterlib}", file=sys.stderr)
            continue
        dart_files = sorted(p for p in flutterlib.rglob("*.dart")
                            if not any(part in EXCLUDE_DIRS for part in p.parts)
                            and not p.name.endswith(EXCLUDE_FILE_SUFFIXES)
                            and "test/" not in str(p.relative_to(flutterlib))
                            and "integration_test/" not in str(p.relative_to(flutterlib)))
        if args.verbose:
            print(f"  [{fuente}] {len(dart_files)} .dart", file=sys.stderr)
        files_scanned = len(dart_files)

        # FASE 1: poblar cross_file_event_index buscando `sealed class XEvent` en todo el lib.
        RE_SEALED_CLASS = re.compile(
            r"^\s*sealed\s+class\s+(?P<name>\w+)\s*(?:<[^>]+>)?\s*",
            re.MULTILINE,
        )
        for df in dart_files:
            rel = str(df.relative_to(SKILL_ROOT))
            try:
                text = df.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            for sm in RE_SEALED_CLASS.finditer(text):
                name = sm.group("name")
                brace_pos = text.find("{", sm.end())
                if brace_pos == -1:
                    continue
                close_pos = find_matching_brace(text, brace_pos)
                if close_pos == -1:
                    continue
                # Solo indexar clases con al menos un `factory` (es un evento/sealed class real).
                body = text[brace_pos + 1:close_pos]
                if "factory " in body or "factory(" in body:
                    cross_file_event_index[name] = (rel, text, (brace_pos, close_pos))

        # FASE 2: parsear blocs con el índice de eventos cross-file.
        for df in dart_files:
            rel = str(df.relative_to(SKILL_ROOT))
            try:
                text = df.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            parsed = parse_dart_file(df, text, rel, cross_file_event_index)
            all_blocs.extend(parsed["blocs"])

    # Orden estable por (file, decl_line, name)
    all_blocs.sort(key=lambda b: (b["file"], b["decl_line"], b["name"]))

    # Calcular resumen
    n_blocs = sum(1 for b in all_blocs if b["kind"] == "Bloc")
    n_cubits = sum(1 for b in all_blocs if b["kind"] == "Cubit")
    n_with_freezed = sum(1 for b in all_blocs if b["events"])
    db_app = sum(
        1 for b in all_blocs
        if "/plugins/database/application/" in b["file"]
    )

    out_obj = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tool": {"name": TOOL_NAME, "version": TOOL_VERSION},
        "fuentes": sorted(set(fuentes)),
        "blocs": all_blocs,
        "summary": {
            "total_blocs": n_blocs,
            "total_cubits": n_cubits,
            "blocs_with_freezed_events": n_with_freezed,
            "blocs_in_plugins_database_application": db_app,
            "files_scanned": files_scanned,
        },
    }
    out_path.write_text(json.dumps(out_obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Resumen a stderr
    print(f"  total_blocs:                {n_blocs}", file=sys.stderr)
    print(f"  total_cubits:               {n_cubits}", file=sys.stderr)
    print(f"  blocs_with_freezed_events:  {n_with_freezed}", file=sys.stderr)
    print(f"  blocs_in_database_app:      {db_app}", file=sys.stderr)
    print(f"  files_scanned:              {files_scanned}", file=sys.stderr)
    print(f"  escrito:                    {out_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
