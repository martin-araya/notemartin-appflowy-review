#!/usr/bin/env python3
# extract_protobuf.py — Recorre SRC/<fuente>/frontend/rust-lib/**/*.rs y
#   emite OUT/_ledger/extract/protobuf.json con todas las entidades
#   derivadas de `ProtoBuf` (structs) y `ProtoBuf_Enum` (enums).
#
# Por cada entidad se extrae:
#   - kind (struct|enum), name, file, decl_line, end_line
#   - derives[], generics
#   - fields[] con name, type (string crudo), pb {index, one_of, extra}, vis
#   - variants[] con name, index, attrs
#   - raw_excerpt (≤ 25 líneas, incluye el `#[derive(...)]`)
#
# Cruza con OUT/_ledger/extract/events.json (A2.1): cada `input`/`output`
# único se marca como `resolved` o se reporta en `missing_event_pbs`.
#
# Ver AGENTS.md §5.1 y ROADMAP.md A2.2.
#
# Uso:
#   extract_protobuf.py [--src-root DIR] [--out-dir DIR]
#                        [--events-json PATH] [--fuente NAME]... [--help]

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
EVENTS_JSON_DEFAULT = SKILL_ROOT / "OUT" / "_ledger" / "extract" / "events.json"
DEFAULT_FUENTES = ("appflowy",)
RUSTLIB_REL = Path("frontend/rust-lib")

SCHEMA_VERSION = "1.0"
TOOL_NAME = "extract_protobuf.py"
TOOL_VERSION = "1.0"

EXCLUDE_DIRS = {".git", "target", "node_modules", "build", "dist"}

# Atributo `#[derive(...)]` (puede ser multilínea y contener `//` comentarios).
RE_DERIVE = re.compile(
    r"""
    \#\s*\[\s*derive\s*\(
      (?P<inner>[^)]*)
    \)\s*\]
    """,
    re.VERBOSE | re.DOTALL,
)

# `pub struct Name<...>` o `pub struct Name` (sin generics en la mayoría de casos).
RE_STRUCT = re.compile(
    r"^\s*pub\s+struct\s+(?P<name>[A-Z][A-Za-z0-9_]*)\b\s*(?P<generics><[^>]*>)?",
    re.MULTILINE,
)

# `pub enum Name<...>`.
RE_ENUM_DECL = re.compile(
    r"^\s*pub\s+enum\s+(?P<name>[A-Z][A-Za-z0-9_]*)\b\s*(?P<generics><[^>]*>)?",
    re.MULTILINE,
)

# Atributo `#[pb(index = N, one_of, type = "...", ...)]` (puede ser multilínea).
RE_PB_ATTR = re.compile(
    r"""
    \#\s*\[\s*pb\s*\(
      (?P<inner>[^)]*)
    \)\s*\]
    """,
    re.VERBOSE | re.DOTALL,
)

# Componentes dentro de un `#[pb(...)]`:
#   index = N   (entero)
#   one_of      (presencia booleana)
#   type = "..." (string)
#   <otra> = "..." o <otra>  (preservar en extra)
RE_PB_INDEX = re.compile(r"\bindex\s*=\s*(?P<index>\d+)")
RE_PB_ONE_OF = re.compile(r"\bone_of\b")
RE_PB_KV = re.compile(r'\b(?P<k>[A-Za-z_][A-Za-z0-9_]*)\s*=\s*"(?P<v>[^"]*)"')
RE_PB_KV_RAW = re.compile(r"\b(?P<k>[A-Za-z_][A-Za-z0-9_]*)\b")

# Campo: REQUIERE al menos un atributo `#[...]` previo + vis opcional + name : type , o ;
# Esto evita falsos positivos cuando un bloque de comentarios `// ...` contiene
# texto que casualmente parece un campo (p. ej. `// - font_layout: "small"`).
# Los campos sin atributo no son protobuf fields: quedan excluidos.
# Los comentarios `//` que aparecen ENTRE `#[pb(...)]` y el campo se
# neutralizan antes de aplicar el regex (ver strip_line_comments_in_place).
RE_FIELD = re.compile(
    r"""
    (?P<decl>
      (?:\s*\#\s*\[[^\]]*\]\s*)+     # uno o más atributos `#[...]` (REQUERIDO)
      \s*
      (?P<vis>(?:pub(?:\s*\([^)]*\))?\s+)?)
      (?P<name>[a-z_][A-Za-z0-9_]*)\s*:\s*
      (?P<type>[^,;\n]+?)
    )\s*[,;]
    """,
    re.VERBOSE,
)


def strip_line_comments_in_place(s: str) -> str:
    """Reemplaza cada `// ...` (comentario de línea) por espacios del mismo
    largo. Conserva la longitud exacta y los `\n`, así las posiciones siguen
    siendo válidas en el string original. NO toca strings Rust (`"..."`).
    """
    out = list(s)
    i = 0
    n = len(s)
    while i < n:
        ch = s[i]
        if ch == "/" and i + 1 < n and s[i + 1] == "/":
            # Comentario de línea: reemplazar hasta el próximo \n o fin.
            j = i
            while j < n and s[j] != "\n":
                out[j] = " "
                j += 1
            i = j
            continue
        if ch == '"':
            # String Rust: saltar sin tocar.
            i += 1
            while i < n and s[i] != '"':
                if s[i] == "\\" and i + 1 < n:
                    i += 2
                else:
                    i += 1
            i += 1
            continue
        i += 1
    return "".join(out)

# Variante de enum: cero o más atributos previos + Name = N , o ;
RE_VARIANT = re.compile(
    r"""
    (?P<decl>
      (?:(?:\#\s*\[[^\]]*\]\s*|//[^\n]*\n)+)?
      \s*
      (?P<name>[A-Z][A-Za-z0-9_]*)\s*=\s*(?P<index>-?\d+)
    )\s*,?
    """,
    re.VERBOSE,
)

# Atributos de variante de enum (sin #[pb(...)], que no aplica a variantes).
# Captura: #[default] → {"default": true}; #[serde(...)] → {"serde": "..."}
RE_VARIANT_ATTR = re.compile(r'\#\s*\[\s*(?P<inner>[^\]]*)\s*\]')


# ---------- helpers de parseo ----------

def find_line_for_offset(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def find_matching_brace(text: str, open_pos: int) -> int:
    """Devuelve la posición del `}` que cierra el `{` en `open_pos`,
    o -1 si no se encuentra. Respeta strings, chars y comentarios.
    """
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
    """Devuelve la lista de derives (strings) a partir del contenido del
    `#[derive(...)]`. Quita comentarios de línea antes de partir.
    """
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


def parse_pb_attr(attr_text: str) -> dict:
    """Parsea un `#[pb(...)]` y devuelve {index, one_of, extra}."""
    out = {"index": None, "one_of": False, "extra": {}}
    m_index = RE_PB_INDEX.search(attr_text)
    if m_index:
        out["index"] = int(m_index.group("index"))
    out["one_of"] = bool(RE_PB_ONE_OF.search(attr_text))
    for m in RE_PB_KV.finditer(attr_text):
        k = m.group("k")
        if k in ("index",):
            continue
        out["extra"][k] = m.group("v")
    return out


def parse_variant_attrs(attr_text: str) -> dict:
    """Parsea atributos previos a una variante de enum (sin #[pb(...)]).
    Devuelve dict: `default` → True si aparece `#[default]`; otros como
    `serde` se preservan en su string.
    """
    out = {}
    for m in RE_VARIANT_ATTR.finditer(attr_text):
        inner = m.group("inner").strip()
        if inner == "default":
            out["default"] = True
        else:
            out[inner.split("(")[0]] = inner
    return out


def field_pb_from_attrs(attr_text: str) -> dict:
    """Extrae {index, one_of, extra} de los atributos previos a un campo.
    Busca el primer `#[pb(...)]`; si hay varios, el último gana.
    """
    last_pb = None
    for m in RE_PB_ATTR.finditer(attr_text):
        last_pb = m.group("inner")
    if last_pb is None:
        return None
    return parse_pb_attr(last_pb)


def build_excerpt(text: str, decl_line: int, end_line: int) -> str:
    """Devuelve hasta 25 líneas que cubran `#[derive(...)]` + cuerpo."""
    lines = text.splitlines()
    if not lines:
        return ""
    # El decl_line apunta al `pub struct`/`pub enum`; el derive está justo antes.
    # Subimos hasta 5 líneas para incluirlo.
    start = max(0, decl_line - 6)
    end = min(len(lines), end_line)
    excerpt = "\n".join(lines[start:end])
    if len(excerpt.splitlines()) > 25:
        excerpt = "\n".join(excerpt.splitlines()[:25]) + "\n... (truncated)"
    return excerpt


# ---------- parseo por archivo ----------

def parse_protobuf_entities_in_file(path: Path, text: str, rel_to_skill: str) -> tuple:
    """Devuelve (structs, enums) parseados de un archivo."""
    structs = []
    enums = []

    # 1) Encontrar todos los `#[derive(...)]` que mencionan ProtoBuf o ProtoBuf_Enum.
    for dm in RE_DERIVE.finditer(text):
        derives = parse_derives(dm.group("inner"))
        if "ProtoBuf" not in derives and "ProtoBuf_Enum" not in derives:
            continue
        is_proto_enum = "ProtoBuf_Enum" in derives
        # El `pub struct`/`pub enum` posterior inmediato (sin otra declaración
        # significativa de por medio).
        pattern = RE_ENUM_DECL if is_proto_enum else RE_STRUCT
        decl_match = None
        for cand in pattern.finditer(text, dm.end()):
            # ¿Entre el fin del derive y el decl hay solo whitespace + comentarios?
            gap = text[dm.end():cand.start()]
            if re.fullmatch(r"[\s/\-#>!.\n\r,]*", gap):
                decl_match = cand
            else:
                break
        if decl_match is None:
            continue
        decl_name = decl_match.group("name")
        decl_line = find_line_for_offset(text, decl_match.start())
        generics = (decl_match.group("generics") or "").strip()

        # Encontrar la `{` y su cierre.
        brace_pos = text.find("{", decl_match.end())
        if brace_pos == -1:
            continue
        end_pos = find_matching_brace(text, brace_pos)
        if end_pos == -1:
            continue
        end_line = find_line_for_offset(text, end_pos)

        body = text[brace_pos + 1:end_pos]

        if is_proto_enum:
            variants = []
            for vm in RE_VARIANT.finditer(body):
                vname = vm.group("name")
                if not vname:
                    continue
                try:
                    vidx = int(vm.group("index"))
                except (TypeError, ValueError):
                    vidx = None
                attrs_text = text[brace_pos + 1 + vm.start("decl"):brace_pos + 1 + vm.start("name")]
                vattrs = parse_variant_attrs(attrs_text)
                v_line = find_line_for_offset(text, brace_pos + 1 + vm.start("name"))
                variants.append({
                    "name": vname,
                    "index": vidx,
                    "attrs": vattrs,
                    "decl_line": v_line,
                })
            enums.append({
                "name": decl_name,
                "kind": "enum",
                "file": rel_to_skill,
                "decl_line": decl_line,
                "end_line": end_line,
                "derives": derives,
                "generics": generics,
                "variants": variants,
                "raw_excerpt": build_excerpt(text, decl_line, end_line),
            })
        else:
            fields = []
            # Neutralizar comentarios `// ...` para que el regex RE_FIELD
            # no caiga en falsos matches por texto tipo `// - key: value`.
            # Las posiciones se conservan, así que attrs_text se extrae del
            # ORIGINAL `body` (que tiene los `#[pb(...)]` intactos).
            body_clean = strip_line_comments_in_place(body)
            for fm in RE_FIELD.finditer(body_clean):
                fname = fm.group("name")
                if not fname:
                    continue
                ftype = fm.group("type").strip()
                fvis = (fm.group("vis") or "").strip() or "private"
                # Atributos previos al campo (slice sobre body ORIGINAL:
                # `#[pb(...)]` y `#[serde(...)]` están intactos ahí).
                attrs_text = body[fm.start("decl"):fm.start("name")]
                pb = field_pb_from_attrs(attrs_text)
                f_line = find_line_for_offset(text, brace_pos + 1 + fm.start("name"))
                fields.append({
                    "name": fname,
                    "type": ftype,
                    "pb": pb,
                    "vis": fvis,
                    "decl_line": f_line,
                })
            structs.append({
                "name": decl_name,
                "kind": "struct",
                "file": rel_to_skill,
                "decl_line": decl_line,
                "end_line": end_line,
                "derives": derives,
                "generics": generics,
                "fields": fields,
                "raw_excerpt": build_excerpt(text, decl_line, end_line),
            })

    return structs, enums


# ---------- cruce con events.json ----------

def load_events(path: Path) -> dict:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def build_cross_ref(events: dict, entities: list) -> dict:
    """Devuelve el bloque cross_ref: unique_inputs, unique_outputs, resolved,
    missing_event_pbs."""
    if not events:
        return {
            "events_json": None,
            "unique_event_inputs": [],
            "unique_event_outputs": [],
            "resolved_inputs": [],
            "resolved_outputs": [],
            "missing_event_pbs": [],
        }
    unique_inputs = set()
    unique_outputs = set()
    for c in events.get("crates", []):
        for v in c.get("variants", []):
            if v.get("input"):
                unique_inputs.add(v["input"])
            if v.get("output"):
                unique_outputs.add(v["output"])
    entity_names = {e["name"] for e in entities}

    resolved_inputs = sorted(x for x in unique_inputs if x in entity_names)
    resolved_outputs = sorted(x for x in unique_outputs if x in entity_names)
    missing_inputs = sorted(x for x in unique_inputs if x not in entity_names)
    missing_outputs = sorted(x for x in unique_outputs if x not in entity_names)

    # Para cada missing, encontrar el primer evento que lo usa (para contexto).
    first_using = {}
    for c in events.get("crates", []):
        for v in c.get("variants", []):
            for kind, val in (("input", v.get("input")), ("output", v.get("output"))):
                if val and val not in entity_names and val not in first_using:
                    first_using[val] = (kind, f"{c['crate']}::{v['name']}")

    missing_event_pbs = []
    for name in missing_inputs + missing_outputs:
        if name in first_using:
            kind, src = first_using[name]
        else:
            kind, src = ("input" if name in unique_inputs else "output", "<unknown>")
        missing_event_pbs.append({
            "name": name,
            "used_as": kind,
            "from_event": src,
            "reason_hint": ("no definido en SRC/appflowy/frontend/rust-lib/**/*.rs "
                            "con derive ProtoBuf/ProtoBuf_Enum"),
        })

    return {
        "events_json": events.get("_source_path") if events else None,
        "unique_event_inputs": sorted(unique_inputs),
        "unique_event_outputs": sorted(unique_outputs),
        "resolved_inputs": resolved_inputs,
        "resolved_outputs": resolved_outputs,
        "missing_event_pbs": missing_event_pbs,
    }


# ---------- CLI ----------

def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description=(
            "Extrae entidades protobuf (structs con #[derive(ProtoBuf)] y "
            "enums con #[derive(ProtoBuf_Enum)]) desde "
            "SRC/<fuente>/frontend/rust-lib/**/*.rs y las cruza con events.json. "
            "Ver AGENTS.md §5.1 / ROADMAP.md A2.2."
        ),
    )
    p.add_argument("--src-root", type=Path, default=SRC_DEFAULT,
                   help=f"Raíz con SRC/<fuente> (default: {SRC_DEFAULT})")
    p.add_argument("--out-dir", type=Path, default=OUT_DIR_DEFAULT,
                   help=f"Directorio de salida (default: {OUT_DIR_DEFAULT})")
    p.add_argument("--events-json", type=Path, default=EVENTS_JSON_DEFAULT,
                   help=f"events.json para cruce (default: {EVENTS_JSON_DEFAULT})")
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
    out_path = out_dir / "protobuf.json"

    entities = []
    crates_stats = {}
    files_scanned_total = 0

    for fuente in fuentes:
        rustlib = src_root / fuente / RUSTLIB_REL
        if not rustlib.is_dir():
            if args.verbose:
                print(f"  [skip] no existe {rustlib}", file=sys.stderr)
            continue
        rs_files = sorted(p for p in rustlib.rglob("*.rs")
                          if not any(part in EXCLUDE_DIRS for part in p.parts))
        if args.verbose:
            print(f"  [{fuente}] {len(rs_files)} .rs", file=sys.stderr)
        files_scanned_total += len(rs_files)
        for rs in rs_files:
            rel = str(rs.relative_to(SKILL_ROOT))
            try:
                text = rs.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            structs, enums = parse_protobuf_entities_in_file(rs, text, rel)
            entities.extend(structs)
            entities.extend(enums)
            if structs or enums:
                # Determinar crate.
                # Estructura del rel: SRC/<fuente>/frontend/rust-lib/<crate>/...
                parts = rel.split("/")
                crate_name = parts[4] if len(parts) > 4 else "<unknown>"
                st = crates_stats.setdefault(crate_name, {
                    "fuente": fuente,
                    "crate": crate_name,
                    "crate_root": str((src_root / fuente / RUSTLIB_REL / crate_name).relative_to(SKILL_ROOT)),
                    "files_scanned": 0,
                    "entity_count": 0,
                    "struct_count": 0,
                    "enum_count": 0,
                })
                st["files_scanned"] += 1
                st["entity_count"] += len(structs) + len(enums)
                st["struct_count"] += len(structs)
                st["enum_count"] += len(enums)

    # Cargar events.json y construir cross_ref.
    events = load_events(args.events_json)
    if events is not None:
        events["_source_path"] = str(args.events_json)
    cross_ref = build_cross_ref(events, entities)

    # Anotar is_input_of / is_output_of en cada entity.
    if events:
        for entity in entities:
            entity["is_input_of"] = []
            entity["is_output_of"] = []
        for c in events.get("crates", []):
            for v in c.get("variants", []):
                ref = f"{c['crate']}::{v['name']}"
                if v.get("input"):
                    for e in entities:
                        if e["name"] == v["input"]:
                            e["is_input_of"].append(ref)
                if v.get("output"):
                    for e in entities:
                        if e["name"] == v["output"]:
                            e["is_output_of"].append(ref)
    else:
        for entity in entities:
            entity["is_input_of"] = []
            entity["is_output_of"] = []

    # Orden estable por (crate, file, decl_line, name).
    def sort_key(e):
        parts = e["file"].split("/")
        crate_name = parts[3] if len(parts) > 3 else "<unknown>"
        return (crate_name, e["file"], e["decl_line"], e["name"])
    entities.sort(key=sort_key)

    # Validaciones internas.
    total_entities = len(entities)
    total_structs = sum(1 for e in entities if e["kind"] == "struct")
    total_enums = sum(1 for e in entities if e["kind"] == "enum")
    assert total_entities == total_structs + total_enums, \
        f"struct+enum != total: {total_structs}+{total_enums} != {total_entities}"
    # Sanity: todos los unique_inputs/outputs de events.json deben estar
    # en entity_names ∪ missing_event_pbs.
    entity_names = {e["name"] for e in entities}
    missing_names = {m["name"] for m in cross_ref["missing_event_pbs"]}
    for x in cross_ref["unique_event_inputs"] + cross_ref["unique_event_outputs"]:
        assert x in entity_names or x in missing_names, \
            f"{x} no resuelto ni reportado como faltante"

    out_obj = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tool": {"name": TOOL_NAME, "version": TOOL_VERSION},
        "fuentes": sorted(set(fuentes)),
        "crates": sorted(crates_stats.values(), key=lambda s: s["crate"]),
        "entities": entities,
        "summary": {
            "total_entities": total_entities,
            "total_structs": total_structs,
            "total_enums": total_enums,
            "files_scanned": files_scanned_total,
            "crates_with_entities": len(crates_stats),
        },
        "cross_ref": cross_ref,
    }
    out_path.write_text(json.dumps(out_obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Resumen a stderr.
    print(f"  total_entities:    {total_entities}", file=sys.stderr)
    print(f"  total_structs:     {total_structs}", file=sys.stderr)
    print(f"  total_enums:       {total_enums}", file=sys.stderr)
    print(f"  files_scanned:     {files_scanned_total}", file=sys.stderr)
    print(f"  crates:            {len(crates_stats)}", file=sys.stderr)
    print(f"  unique_event_inputs:  {len(cross_ref['unique_event_inputs'])}", file=sys.stderr)
    print(f"    resolved: {len(cross_ref['resolved_inputs'])}, missing: {sum(1 for m in cross_ref['missing_event_pbs'] if m['used_as'] == 'input')}", file=sys.stderr)
    print(f"  unique_event_outputs: {len(cross_ref['unique_event_outputs'])}", file=sys.stderr)
    print(f"    resolved: {len(cross_ref['resolved_outputs'])}, missing: {sum(1 for m in cross_ref['missing_event_pbs'] if m['used_as'] == 'output')}", file=sys.stderr)
    print(f"  escrito:           {out_path}", file=sys.stderr)
    if cross_ref["missing_event_pbs"]:
        print(f"  missing_event_pbs ({len(cross_ref['missing_event_pbs'])}):", file=sys.stderr)
        for m in cross_ref["missing_event_pbs"][:20]:
            print(f"    - {m['name']:40s} ({m['used_as']} of {m['from_event']})", file=sys.stderr)
        if len(cross_ref["missing_event_pbs"]) > 20:
            print(f"    ... y {len(cross_ref['missing_event_pbs']) - 20} más", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
