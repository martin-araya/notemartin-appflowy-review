#!/usr/bin/env python3
# extract_events.py — Recorre SRC/<fuente>/frontend/rust-lib/**/event_map.rs
#   y emite OUT/_ledger/extract/events.json con:
#     - enums derivados con Flowy_Event (atributos event_err y variantes con
#       #[event(input=.., output=..)] incluyendo formas multilínea y vacías),
#     - registros `.event(EnumName::Variant, handler)` (incluye multilínea)
#       dentro de `pub fn init(...) -> AFPlugin`,
#     - resolución archivo:línea de cada handler dentro del crate.
#
# Ver AGENTS.md §5.1 y ROADMAP.md A2.1.
#
# Uso:
#   extract_events.py [--src-root DIR] [--out-dir DIR] [--fuente NAME]... [--help]
#
# Por defecto procesa solo `appflowy` (el patrón event_map.rs es exclusivo
# del workspace de AppFlowy; collab y editor no lo usan — D1 del plan).

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------- constantes ----------

SCRIPT_PATH = Path(__file__).resolve()
SKILL_ROOT = SCRIPT_PATH.parent.parent.parent  # SKILL/scripts/extract_events.py → skill_root
SRC_DEFAULT = SKILL_ROOT / "SRC"
OUT_DIR_DEFAULT = SKILL_ROOT / "OUT" / "_ledger" / "extract"
DEFAULT_FUENTES = ("appflowy",)
RUSTLIB_REL = Path("frontend/rust-lib")
EVENT_MAP_REL = "src/event_map.rs"

SCHEMA_VERSION = "1.0"
TOOL_NAME = "extract_events.py"
TOOL_VERSION = "1.0"

EXCLUDE_DIRS = {".git", "target", "node_modules", "build", "dist"}

# Regex de cabecera de variante: nombre, =, índice, coma (o sin coma si es la última).
# Comentarios `///` y `//` se ignoran al mapear variante→atributo (D7).
RE_VARIANT = re.compile(
    r"""
    (?:(?P<attrs>(?:\s*\#\[[^\]]*\]\s*)+))?    # atributos #[...] previos (uno o varios)
    \s*
    (?P<name>[A-Z][A-Za-z0-9_]*)\s*=\s*(?P<index>-?\d+)\s*,?
    """,
    re.VERBOSE,
)

# Parser del contenido de un `#[event(...)]` (puede tener comas y saltos de línea).
# Capturas `input` y `output` por separado; si no aparecen → None.
RE_EVENT_ATTR_INNER = re.compile(
    r"""
    input\s*=\s*"(?P<input>[A-Za-z_][A-Za-z0-9_]*)"
    |
    output\s*=\s*"(?P<output>[A-Za-z_][A-Za-z0-9_]*)"
    """,
    re.VERBOSE,
)

# `#[derive(...)]` con derive que contenga Flowy_Event.
RE_DERIVE_LINE = re.compile(r"^\s*#\s*\[\s*derive\s*\((?P<inner>[^)]*)\)\s*\]", re.MULTILINE)
RE_EVENT_ERR = re.compile(r'^\s*#\s*\[\s*event_err\s*=\s*"(?P<err>[A-Za-z_][A-Za-z0-9_]*)"\s*\]',
                          re.MULTILINE)
RE_PUB_ENUM = re.compile(r"^\s*pub\s+enum\s+(?P<name>[A-Z][A-Za-z0-9_]*)\s*\{", re.MULTILINE)

# `pub fn init(...) -> AFPlugin` (puede tener un nombre distinto por crate).
RE_INIT_HEAD = re.compile(
    r"^\s*pub\s+fn\s+(?P<name>init)\s*\([^)]*\)\s*->\s*AFPlugin\s*\{",
    re.MULTILINE,
)

# Llamada `.event(EnumName::Variant, handler)` (atributos/llaves externas
# los delimitamos con el balance de la función init).
# Acepta:
#   - handler seguido de `,` (caso multi-línea: `handler,\n)`) o sin coma
#   - cualquier cantidad de whitespace (incluye \n) entre tokens
RE_EVENT_CALL = re.compile(
    r"""
    \.event\s*\(\s*
      (?P<qual>[A-Z][A-Za-z0-9_]*)\s*::\s*(?P<variant>[A-Z][A-Za-z0-9_]*)\s*,\s*
      (?P<handler>[A-Za-z_][A-Za-z0-9_]*)\s*,?
    \s*\)
    """,
    re.VERBOSE,
)

# `fn <name>(` (acepta `pub(crate)`, `async`, generics, lifetimes).
RE_FN_DEF = re.compile(
    r"^\s*(?:pub(?:\s*\([^)]*\))?\s+)?(?:async\s+)?(?:const\s+)?(?:unsafe\s+)?(?:extern\s+\"[^\"]+\"\s+)?fn\s+"
    r"(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*[<\(]",
    re.MULTILINE,
)


# ---------- helpers de parseo ----------

def find_line_for_offset(text: str, offset: int) -> int:
    """Devuelve nº de línea 1-indexed que contiene el offset `offset` en `text`."""
    return text.count("\n", 0, offset) + 1


def strip_line_comments(line: str) -> str:
    """Quita el `//` final de una línea (preserva URLs en strings mejor-esfuerzo)."""
    # No tocamos los strings; basta con cortar el `//` que no esté dentro de `"..."`.
    # Para `#[event(...)]` multilínea, esto se aplica solo a las líneas que
    # llegan como `línea` aislada — los bloques `#[...]` ya están
    # consumidos por el parser de atributos y no se ven aquí.
    in_str = False
    for i, ch in enumerate(line):
        if ch == '"' and (i == 0 or line[i - 1] != "\\"):
            in_str = not in_str
        elif not in_str and ch == "/" and i + 1 < len(line) and line[i + 1] == "/":
            return line[:i]
    return line


def parse_event_attr(attr_inner: str) -> dict:
    """Parsea el interior de un `#[event(...)]` y devuelve {input, output}.

    Si no hay `input=` ni `output=` (forma vacía `#[event()]` o atributo
    sin argumentos relevantes), ambos son None.
    """
    input_pb = None
    output_pb = None
    for m in RE_EVENT_ATTR_INNER.finditer(attr_inner):
        if m.group("input"):
            input_pb = m.group("input")
        elif m.group("output"):
            output_pb = m.group("output")
    return {"input": input_pb, "output": output_pb}


def extract_attr_block(attr_text: str) -> dict:
    """Extrae `input`/`output` de un bloque de atributos `#[event(...)]` previo
    a una variante. Si hay varios `#[...]` previos, se unen y se aplica la
    regex sobre el conjunto (caso típico: `#[event_err=...]` y `#[event(...)]`
    separados). Devuelve {input, output} consolidado del último `#[event]`.
    """
    # Buscar todos los `#[event(...)]` (pueden ser multilínea). El último gana
    # (defensa si una variante tuviese varios, no debería ocurrir).
    last_input = None
    last_output = None
    saw_event_attr = False
    for m in re.finditer(r"#\s*\[\s*event\s*(?P<inner>\([^)]*\))?\s*\]", attr_text, re.DOTALL):
        saw_event_attr = True
        inner = m.group("inner") or "()"
        parsed = parse_event_attr(inner)
        # Solo sobreescribimos si el bloque trae un valor explícito
        if parsed["input"] is not None:
            last_input = parsed["input"]
        if parsed["output"] is not None:
            last_output = parsed["output"]
    if not saw_event_attr:
        return {"input": None, "output": None}
    return {"input": last_input, "output": last_output}


def find_init_block(text: str):
    """Devuelve (start_line, end_line_exclusive, init_name) o None si no hay."""
    m = RE_INIT_HEAD.search(text)
    if not m:
        return None
    body_start_offset = m.end() - 1  # posición del `{`
    # Balance de llaves desde body_start_offset (descartando strings/chars y comentarios).
    depth = 0
    i = body_start_offset
    n = len(text)
    while i < n:
        ch = text[i]
        if ch == "/" and i + 1 < n and text[i + 1] == "/":
            # comentario de línea
            j = text.find("\n", i)
            i = n if j == -1 else j + 1
            continue
        if ch == "/" and i + 1 < n and text[i + 1] == "*":
            j = text.find("*/", i + 2)
            i = n if j == -1 else j + 2
            continue
        if ch == '"':
            # string Rust básico (admite \" y \\)
            i += 1
            while i < n and text[i] != '"':
                if text[i] == "\\" and i + 1 < n:
                    i += 2
                else:
                    i += 1
            i += 1
            continue
        if ch == "'":
            # char Rust: 'x' o '\\'...
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
                end_offset = i + 1
                return (
                    find_line_for_offset(text, body_start_offset),
                    find_line_for_offset(text, end_offset),
                    m.group("name"),
                )
        i += 1
    return None


def parse_enum_decl(text: str):
    """Devuelve {name, decl_line, derives[], event_err} del primer enum con
    `Flowy_Event` en su derive, o None si no hay.
    """
    # Iteramos los derives en orden, agrupando los que estén contiguos.
    derives_by_line = list(RE_DERIVE_LINE.finditer(text))
    event_err_by_line = list(RE_EVENT_ERR.finditer(text))
    enums_by_line = list(RE_PUB_ENUM.finditer(text))

    for em in enums_by_line:
        enum_name = em.group("name")
        enum_decl_line = find_line_for_offset(text, em.start())
        # El `#[derive(...)]` que aplica a este enum es el inmediatamente
        # anterior sin líneas de por medio (permitimos comentarios `///`/`//`).
        prev_derive = None
        for dm in derives_by_line:
            if dm.end() >= em.start():
                break
            # ¿hay solo whitespace/comentarios entre el fin del derive y el enum?
            gap = text[dm.end():em.start()]
            if re.fullmatch(r"[\s/\-#>!.\n\r]*", gap):
                prev_derive = dm
            else:
                # Reiniciamos (otro derive más reciente es candidato)
                prev_derive = dm
        if prev_derive is None:
            continue
        derives_str = prev_derive.group("inner")
        derives = [d.strip() for d in derives_str.split(",") if d.strip()]
        if "Flowy_Event" not in derives:
            continue
        # Buscar `event_err` entre el derive y el enum (sin líneas significativas).
        event_err = None
        for em_err in event_err_by_line:
            if prev_derive.end() <= em_err.start() < em.start():
                event_err = em_err.group("err")
                break
        return {
            "name": enum_name,
            "decl_line": enum_decl_line,
            "derives": derives,
            "event_err": event_err,
        }
    return None


def parse_variants(text: str, enum_decl_line: int, enum_name: str) -> list:
    """Devuelve lista ordenada por índice con todas las variantes del enum.

    Para el rango del cuerpo del enum, escaneamos desde la línea de apertura
    hasta el cierre balanceado. Si el parseo falla, lista vacía (no abortamos).
    """
    # Encontrar la `{` del enum.
    em = None
    for m in RE_PUB_ENUM.finditer(text):
        if m.group("name") == enum_name and find_line_for_offset(text, m.start()) == enum_decl_line:
            em = m
            break
    if em is None:
        return []
    # Balance de llaves desde la `{` del enum.
    i = em.end() - 1
    n = len(text)
    depth = 0
    end_offset = None
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
                end_offset = i
                break
        i += 1
    if end_offset is None:
        return []

    body = text[em.end():end_offset]
    variants = []
    for vm in RE_VARIANT.finditer(body):
        name = vm.group("name")
        if not name:
            continue
        try:
            index = int(vm.group("index"))
        except (TypeError, ValueError):
            continue
        attrs_text = vm.group("attrs") or ""
        attr_parsed = extract_attr_block(attrs_text)
        # source_line apunta a la línea del NOMBRE de la variante (no del
        # primer atributo `#[event(...)]` previo), para que coincida con el
        # código fuente real que el lector verá en su editor.
        name_start_in_body = vm.start("name")
        source_line = find_line_for_offset(text, em.end() + name_start_in_body)
        variants.append({
            "name": name,
            "index": index,
            "input": attr_parsed["input"],
            "output": attr_parsed["output"],
            "source_line": source_line,
            "registrations": [],
            "sin_handler": False,
        })

    # Orden estable por índice ascendente; si hay duplicados de índice,
    # añadimos warning más adelante (aquí solo emitimos en el orden del
    # código fuente, no es nuestro problema resolverlo).
    variants.sort(key=lambda v: v["index"])
    return variants


def parse_event_calls(text: str, init_start_line: int, init_end_line: int, enum_hint: str) -> list:
    """Devuelve lista de {qual, variant, handler, line} para las llamadas
    `.event(X, h)` dentro del cuerpo de `init`. Soporta multilínea.
    """
    # Extraer el rango de texto correspondiente a las líneas [init_start_line, init_end_line).
    lines = text.splitlines(keepends=True)
    # Las líneas en `lines` están 0-indexed; las nuestras 1-indexed.
    start = max(0, init_start_line - 1)
    end = min(len(lines), init_end_line - 1)
    body = "".join(lines[start:end])
    body_offset_in_text = sum(len(l) for l in lines[:start])
    out = []
    for m in RE_EVENT_CALL.finditer(body):
        qual = m.group("qual")
        variant = m.group("variant")
        handler = m.group("handler")
        line = find_line_for_offset(text, body_offset_in_text + m.start())
        if enum_hint and qual != enum_hint:
            # Defensa: descartar registros que apunten a otro enum.
            continue
        out.append({
            "qual": qual,
            "variant": variant,
            "handler": handler,
            "line": line,
        })
    return out


def ruta_relativa(abs_path: Path, src_root: Path) -> str:
    """Ruta legible de un fichero, valida tanto dentro como fuera de la skill.

    Antes de C7 esto era `abs_path.relative_to(SKILL_ROOT)`, que lanza
    `ValueError` si se pasa un `--src-root` fuera del proyecto. El smoke test de
    retroalimentacion lo reproduce con un repo sintetico en `/tmp`: el extractor
    se caia antes de escribir nada. Ahora la ruta es relativa a la raiz del
    proyecto cuando el fichero esta dentro, y relativa a `SRC/` (con el prefijo
    de fuente) cuando no, que es la forma que `validate_evidence.py` reconoce.
    """
    try:
        return str(abs_path.relative_to(SKILL_ROOT))
    except ValueError:
        return str(abs_path.relative_to(src_root))


def find_handler_in_crate(crate_root: Path, handler_name: str, rel_base: Path,
                         src_root: Path) -> tuple:
    """Busca `fn <handler_name>` en los .rs del crate (excluyendo target/.git).
    Devuelve (ruta_relativa_al_skill_root, línea 1-indexed) de la primera
    coincidencia estable, o (None, None) si no encuentra.
    """
    candidates = []
    for p in crate_root.rglob("*.rs"):
        # Excluir subárboles prohibidos.
        if any(part in EXCLUDE_DIRS for part in p.parts):
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for m in RE_FN_DEF.finditer(text):
            if m.group("name") == handler_name:
                line = text.count("\n", 0, m.start()) + 1
                candidates.append((p, line))
                break  # una por archivo es suficiente
    if not candidates:
        return (None, None)
    # Orden estable por (ruta_relativa).
    candidates.sort(key=lambda t: str(t[0]))
    p, line = candidates[0]
    rel = ruta_relativa((rel_base / p).resolve(), src_root)
    return (rel, line)


# ---------- orquestación por crate ----------

def process_event_map(event_map_abs: Path, src_root: Path) -> dict:
    rel_to_skill = ruta_relativa(event_map_abs, src_root)
    rel_to_src = str(event_map_abs.relative_to(src_root))
    parts = rel_to_src.split("/")
    # Estructura: <fuente>/frontend/rust-lib/<crate>/src/event_map.rs
    fuente = parts[0]
    crate_name = parts[3]
    crate_root = event_map_abs.parent.parent  # <crate>/
    warnings = []

    text = event_map_abs.read_text(encoding="utf-8")
    lines = text.splitlines()

    init = find_init_block(text)
    enum_decl = parse_enum_decl(text)

    if init is None:
        warnings.append(f"no se encontró `pub fn init(...) -> AFPlugin`")
    if enum_decl is None:
        warnings.append(f"no se encontró enum con `#[derive(... Flowy_Event ...)]`")

    variants = []
    if enum_decl is not None:
        variants = parse_variants(text, enum_decl["decl_line"], enum_decl["name"])

    # Mapeo rápido de variantes por nombre.
    variants_by_name = {v["name"]: v for v in variants}

    # Procesar registros `.event(...)`.
    registrations_by_variant: dict = {}
    if init is not None:
        calls = parse_event_calls(text, init[0], init[1],
                                  enum_decl["name"] if enum_decl else "")
        for c in calls:
            vname = c["variant"]
            registrations_by_variant.setdefault(vname, []).append({
                "handler": c["handler"],
                "registered_in": rel_to_skill,
                "registered_line": c["line"],
                "handler_file": None,
                "handler_line": None,
            })

    # Resolver cada handler y asociar a su variante.
    for vname, regs in registrations_by_variant.items():
        if vname not in variants_by_name:
            warnings.append(f"registro `.event({enum_decl['name']}::{vname}, ...)` sin variante en el enum")
            continue
        for reg in regs:
            handler_name = reg["handler"]
            hf, hl = find_handler_in_crate(crate_root, handler_name, event_map_abs.parent, src_root)
            if hf is None:
                warnings.append(f"handler '{handler_name}' no encontrado en el crate '{crate_name}'")
            reg["handler_file"] = hf
            reg["handler_line"] = hl
        variants_by_name[vname]["registrations"] = regs

    # Marcar sin_handler y resumen.
    registered = 0
    sin_handler = 0
    for v in variants:
        v["sin_handler"] = (len(v["registrations"]) == 0)
        if v["sin_handler"]:
            sin_handler += 1
        else:
            registered += 1

    crate_obj = {
        "fuente": fuente,
        "crate": crate_name,
        "crate_root": ruta_relativa(crate_root, src_root),
        "event_map_file": rel_to_skill,
        "init_function": {
            "name": init[2] if init else None,
            "line": init[0] if init else None,
            "end_line": init[1] if init else None,
        },
        "enum": {
            "name": enum_decl["name"] if enum_decl else None,
            "decl_line": enum_decl["decl_line"] if enum_decl else None,
            "derives": enum_decl["derives"] if enum_decl else [],
            "event_err": enum_decl["event_err"] if enum_decl else None,
        },
        "variants": variants,
        "summary": {
            "total_variants": len(variants),
            "registered": registered,
            "sin_handler": sin_handler,
        },
        "warnings": warnings,
    }
    return crate_obj


# ---------- CLI ----------

def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description=(
            "Extrae enums/registros de eventos FFI desde "
            "SRC/<fuente>/frontend/rust-lib/**/event_map.rs y los serializa a "
            "OUT/_ledger/extract/events.json. Ver AGENTS.md §5.1 / ROADMAP.md A2.1."
        ),
    )
    p.add_argument("--src-root", type=Path, default=SRC_DEFAULT,
                   help=f"Raíz con SRC/<fuente> (default: {SRC_DEFAULT})")
    p.add_argument("--out-dir", type=Path, default=OUT_DIR_DEFAULT,
                   help=f"Directorio de salida (default: {OUT_DIR_DEFAULT})")
    p.add_argument("--fuente", action="append", default=None,
                   help=f"Fuente(s) a procesar (default: {list(DEFAULT_FUENTES)}). Admite múltiples.")
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
    out_path = out_dir / "events.json"

    crates = []
    for fuente in fuentes:
        rustlib = src_root / fuente / RUSTLIB_REL
        if not rustlib.is_dir():
            if args.verbose:
                print(f"  [skip] no existe {rustlib}", file=sys.stderr)
            continue
        event_maps = sorted(p for p in rustlib.rglob(EVENT_MAP_REL))
        if args.verbose:
            print(f"  [{fuente}] {len(event_maps)} event_map.rs", file=sys.stderr)
        for em in event_maps:
            if args.verbose:
                print(f"    - {ruta_relativa(em, src_root)}", file=sys.stderr)
            crates.append(process_event_map(em, src_root))

    # Orden estable por (fuente, crate) para diffs legibles (D8).
    crates.sort(key=lambda c: (c["fuente"], c["crate"]))

    # Validaciones internas antes de escribir (D-§4.4).
    total_variants = sum(c["summary"]["total_variants"] for c in crates)
    total_registered = sum(c["summary"]["registered"] for c in crates)
    total_sin_handler = sum(c["summary"]["sin_handler"] for c in crates)
    for c in crates:
        assert sum(len(v["registrations"]) > 0 for v in c["variants"]) == c["summary"]["registered"], \
            f"summary.registered inconsistente en crate {c['crate']}"
        assert sum(1 for v in c["variants"] if v["sin_handler"]) == c["summary"]["sin_handler"], \
            f"summary.sin_handler inconsistente en crate {c['crate']}"
        # registros no debe coexistir con sin_handler
        for v in c["variants"]:
            if v["sin_handler"]:
                assert len(v["registrations"]) == 0, f"{c['crate']}.{v['name']} sin_handler=True con regs"
            else:
                assert len(v["registrations"]) > 0, f"{c['crate']}.{v['name']} sin_handler=False sin regs"

    out_obj = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tool": {"name": TOOL_NAME, "version": TOOL_VERSION},
        "fuentes": sorted(set(fuentes)),
        "crates": crates,
        "summary": {
            "crates_with_event_map": len(crates),
            "total_variants": total_variants,
            "total_registered": total_registered,
            "total_sin_handler": total_sin_handler,
        },
    }
    out_path.write_text(json.dumps(out_obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Resumen a stderr.
    print(f"  crates_with_event_map: {len(crates)}", file=sys.stderr)
    print(f"  total_variants:        {total_variants}", file=sys.stderr)
    print(f"  total_registered:      {total_registered}", file=sys.stderr)
    print(f"  total_sin_handler:     {total_sin_handler}", file=sys.stderr)
    print(f"  escrito:               {out_path}", file=sys.stderr)
    for c in crates:
        if c["warnings"]:
            print(f"  warnings ({c['crate']}):", file=sys.stderr)
            for w in c["warnings"]:
                print(f"    - {w}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
