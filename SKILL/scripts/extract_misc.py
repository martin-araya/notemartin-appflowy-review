#!/usr/bin/env python3
# extract_misc.py — Extrae 6 bloques independientes de metadata miscelánea
#   del workspace de AppFlowy:
#     1. routes (GoRoute)
#     2. shortcuts (CommandShortcutEvent + HotKeyItem)
#     3. feature_flags (enum FeatureFlag)
#     4. error_codes (pub enum ErrorCode en Rust)
#     5. i18n_keys (claves usadas con .tr())
#     6. startup_tasks (orden de LaunchTask en startup.dart)
#
# Ver AGENTS.md §5.1 y ROADMAP.md A2.6.
#
# Uso:
#   extract_misc.py [--src-root DIR] [--out-dir DIR]
#                    [--fuente NAME]... [--help]

import argparse
import json
import re
import sys
from collections import defaultdict
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
TOOL_NAME = "extract_misc.py"
TOOL_VERSION = "1.0"

EXCLUDE_FILE_SUFFIXES = (
    ".g.dart", ".freezed.dart", ".config.dart", ".gr.dart",
    ".mocks.dart", ".pb.dart", ".pbenum.dart",
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


def split_top_level_args(args: str) -> list:
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


# ---------- FASE 1: Routes ----------

# `path: 'literal'` o `path: SomeClass.routeName,`
# El body de GoRoute contiene `pageBuilder: (context, state) { ... }` con
# bloques anidados — usar `re.DOTALL` y capturar solo el path; el cierre
# de `)` se hace con balanceo manual si fuera necesario. Aquí usamos una
# regex no-balanceada hasta el primer `,\n` o `)` top-level.
RE_GOROUTE_PATH = re.compile(
    r"GoRoute\([^)]*?path:\s*"
    r"(?:['\"]([^'\"]+)['\"]|([A-Z][\w.]*(?:\.[a-z]\w*)*))",
    re.DOTALL,
)
# `name: 'literal'` (opcional)
RE_GOROUTE_NAME = re.compile(r"\bname:\s*['\"]([^'\"]+)['\"]")


def extract_routes(src_root: Path, fuente: str) -> dict:
    flutterlib = src_root / fuente / FLUTTER_LIB_REL
    if not flutterlib.is_dir():
        return None
    router_path = flutterlib / "startup" / "tasks" / "generate_router.dart"
    if not router_path.is_file():
        return {"file": None, "total": 0, "items": []}
    text = router_path.read_text(encoding="utf-8")
    rel = str(router_path.relative_to(SKILL_ROOT))
    items = []
    for m in RE_GOROUTE_PATH.finditer(text):
        path = m.group(1) or m.group(2) or ""
        line = find_line_for_offset(text, m.start())
        # Buscar el `name:` más cercano DESPUÉS del path (dentro de la
        # misma GoRoute — buscar hasta el próximo `,` o `)`).
        # Para simplificar, buscamos el siguiente `name:` global.
        # Es una heurística aceptable para GoRoute.
        tail = text[m.end():m.end() + 2000]  # ventana
        nm = RE_GOROUTE_NAME.search(tail)
        name = nm.group(1) if nm else ""
        items.append({"path": path, "name": name, "decl_line": line})
    items.sort(key=lambda x: x["path"])
    return {"file": rel, "total": len(items), "items": items}


# ---------- FASE 2: Shortcuts ----------

RE_COMMAND_SHORTCUT_ENUM = re.compile(r"enum\s+CommandShortcutEvent\s*")
RE_CS_VARIANT = re.compile(r"^\s*(\w+)\s*,\s*$", re.MULTILINE)

# Lista de `CommandShortcutEvent` con `command:` (el archivo command_shortcuts.dart
# contiene una lista grande; contamos y capturamos los nombres).
RE_COMMAND_SHORTCUT_DEF = re.compile(
    r"^(\s*)([a-z][A-Za-z0-9_]*)\s*=\s*const\s+CommandShortcutEvent\s*\(",
    re.MULTILINE,
)

# HotKeyItem: contar ocurrencias con un patrón de "HotKeyItem(\n  hotKey: HotKey(...)"
RE_HOTKEY_ITEM_INSTANCE = re.compile(r"HotKeyItem\s*\(")


def extract_shortcuts(src_root: Path, fuente: str) -> dict:
    flutterlib = src_root / fuente / FLUTTER_LIB_REL
    if not flutterlib.is_dir():
        return None

    # 1) enum CommandShortcutEvent: buscar en cualquier archivo que lo defina.
    cs_enum_path = None
    cs_variants = []
    for dart in flutterlib.rglob("*.dart"):
        if dart.name.endswith(EXCLUDE_FILE_SUFFIXES):
            continue
        if "shortcut" not in dart.name.lower() and "command_shortcuts" not in dart.name.lower():
            continue
        try:
            text = dart.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        m = RE_COMMAND_SHORTCUT_ENUM.search(text)
        if not m:
            continue
        brace_pos = text.find("{", m.end() - 1)
        if brace_pos == -1:
            continue
        close_pos = find_matching_brace(text, brace_pos)
        if close_pos == -1:
            continue
        body = text[brace_pos + 1:close_pos]
        for vm in RE_CS_VARIANT.finditer(body):
            vname = vm.group(1)
            line = find_line_for_offset(text, brace_pos + 1 + vm.start())
            cs_variants.append({
                "name": vname,
                "command": vname,
                "line": line,
            })
        if cs_variants:
            cs_enum_path = str(dart.relative_to(SKILL_ROOT))
            break

    # 2) HotKeyItem en home/hotkeys.dart.
    hotkey_path = None
    hotkey_count = 0
    for cand in [
        flutterlib / "workspace" / "presentation" / "home" / "hotkeys.dart",
    ]:
        if cand.is_file():
            hotkey_path = cand
            break
    if hotkey_path is not None:
        try:
            text = hotkey_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            text = ""
        # Capturar comentarios descriptivos como "name" para cada HotKeyItem.
        # Estrategia: encontrar `HotKeyItem(` y leer el siguiente comentario `//`.
        for m in RE_HOTKEY_ITEM_INSTANCE.finditer(text):
            # Buscar el comentario más reciente antes de m.start().
            preceding = text[:m.start()]
            comment_lines = [
                ln.strip() for ln in preceding.splitlines()[-3:]
                if ln.strip().startswith("//")
            ]
            name = comment_lines[-1].lstrip("/ ").strip() if comment_lines else ""
            line = find_line_for_offset(text, m.start())
            hotkey_count += 1
            cs_variants.append({
                "name": f"hotkey_{hotkey_count}: {name or '(unnamed)'}",
                "command": name,
                "line": line,
            })

    return {
        "command_shortcut_event": {
            "file": cs_enum_path,
            "variants": [v for v in cs_variants if not v["name"].startswith("hotkey_")],
            "total": sum(1 for v in cs_variants if not v["name"].startswith("hotkey_")),
        },
        "hotkey_items": {
            "file": str(hotkey_path.relative_to(SKILL_ROOT)) if hotkey_path else None,
            "items": [v for v in cs_variants if v["name"].startswith("hotkey_")],
            "total": hotkey_count,
        },
        "total": len(cs_variants),
    }


# ---------- FASE 3: Feature flags ----------

RE_FF_ENUM = re.compile(r"enum\s+FeatureFlag\s*\{")
RE_FF_VARIANT = re.compile(r"^\s*(\w+)\s*,?\s*(?://.*)?$", re.MULTILINE)


def extract_feature_flags(src_root: Path, fuente: str) -> dict:
    flutterlib = src_root / fuente / FLUTTER_LIB_REL
    if not flutterlib.is_dir():
        return None
    flags_path = flutterlib / "shared" / "feature_flags.dart"
    if not flags_path.is_file():
        return {"file": None, "enum": "FeatureFlag", "total": 0, "variants": []}
    text = flags_path.read_text(encoding="utf-8")
    rel = str(flags_path.relative_to(SKILL_ROOT))

    em = RE_FF_ENUM.search(text)
    if em is None:
        return {"file": rel, "enum": "FeatureFlag", "total": 0, "variants": []}
    brace_pos = text.find("{", em.end() - 1)
    if brace_pos == -1:
        return {"file": rel, "enum": "FeatureFlag", "total": 0, "variants": []}
    close_pos = find_matching_brace(text, brace_pos)
    if close_pos == -1:
        return {"file": rel, "enum": "FeatureFlag", "total": 0, "variants": []}
    body = text[brace_pos + 1:close_pos]

    variants = []
    for vm in RE_FF_VARIANT.finditer(body):
        vname = vm.group(1)
        # Saltar palabras clave del enum (private, etc.).
        if vname in ("private", "var", "final", "const"):
            continue
        line = find_line_for_offset(text, brace_pos + 1 + vm.start())
        variants.append({"name": vname, "default": None, "decl_line": line})
    return {"file": rel, "enum": "FeatureFlag", "total": len(variants), "variants": variants}


# ---------- FASE 4: Error codes ----------

RE_EC_ENUM = re.compile(r"pub\s+enum\s+ErrorCode\s*")
RE_EC_REPR = re.compile(r'#\s*\[\s*repr\s*\(\s*(\w+)\s*\)\s*\]')
# Variante Rust con #[attrs] Name = N,
# Variante Rust con #[attrs] (opcional) + comentarios + Name = N, [coma]
# Permite comentarios `// ...` o `/* ... */` entre los atributos y el nombre.
RE_EC_VARIANT = re.compile(
    r"((?:\s*#\s*\[[^\]]*\]\s*)*)"   # attrs (0 o más)
    r"(?:\s*(?://[^\n]*|/\*.*?\*/)\s*)*"   # comentarios
    r"(\w+)\s*=\s*(\d+)\s*,",
    re.DOTALL,
)
RE_EC_DEFAULT = re.compile(r"#\s*\[\s*default\s*\]")
RE_EC_ERROR = re.compile(r'#\s*\[\s*error\s*\(\s*"([^"]+)"\s*\)\s*\]')


def extract_error_codes(src_root: Path, fuente: str) -> dict:
    code_path = src_root / fuente / RUSTLIB_REL / "flowy-error" / "src" / "code.rs"
    if not code_path.is_file():
        return {"file": None, "enum": "ErrorCode", "repr": None, "total": 0, "variants": []}
    text = code_path.read_text(encoding="utf-8")
    rel = str(code_path.relative_to(SKILL_ROOT))

    # Detectar `#[repr(u8)]` (o similar) antes del enum.
    em = RE_EC_ENUM.search(text)
    if em is None:
        return {"file": rel, "enum": "ErrorCode", "repr": None, "total": 0, "variants": []}
    repr_match = None
    for m in RE_EC_REPR.finditer(text, 0, em.start()):
        repr_match = m.group(1)  # tomar la última coincidencia
    repr_value = repr_match if repr_match else None

    brace_pos = text.find("{", em.end() - 1)
    if brace_pos == -1:
        return {"file": rel, "enum": "ErrorCode", "repr": repr_value, "total": 0, "variants": []}
    close_pos = find_matching_brace(text, brace_pos)
    if close_pos == -1:
        return {"file": rel, "enum": "ErrorCode", "repr": repr_value, "total": 0, "variants": []}
    body = text[brace_pos + 1:close_pos]

    variants = []
    for vm in RE_EC_VARIANT.finditer(body):
        attrs_block = vm.group(1) or ""
        name = vm.group(2)
        try:
            index = int(vm.group(3))
        except (TypeError, ValueError):
            index = None
        is_default = bool(RE_EC_DEFAULT.search(attrs_block))
        msg_match = RE_EC_ERROR.search(attrs_block)
        message = msg_match.group(1) if msg_match else None
        line = find_line_for_offset(text, brace_pos + 1 + vm.start(2))
        variants.append({
            "name": name,
            "index": index,
            "is_default": is_default,
            "message": message,
            "decl_line": line,
        })
    return {
        "file": rel,
        "enum": "ErrorCode",
        "repr": repr_value,
        "total": len(variants),
        "variants": variants,
    }


# ---------- FASE 5: i18n keys ----------

# `LocaleKeys.foo.bar.tr()` o `LocaleKeys.X.tr()`.
RE_I18N_LOCALES = re.compile(r"LocaleKeys\.([\w.]+)\.tr\(\)")
# `'foo.bar'.tr()` o `"foo.bar".tr()`.
RE_I18N_STRING = re.compile(r"""['"]([\w.]+)['"]\.tr\(\)""")


def extract_i18n_keys(src_root: Path, fuente: str) -> dict:
    flutterlib = src_root / fuente / FLUTTER_LIB_REL
    if not flutterlib.is_dir():
        return None
    keys: dict = defaultdict(lambda: {"usages": 0, "sources": set()})

    for dart in flutterlib.rglob("*.dart"):
        if dart.name.endswith(EXCLUDE_FILE_SUFFIXES):
            continue
        try:
            text = dart.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        rel = str(dart.relative_to(SKILL_ROOT))
        for m in RE_I18N_LOCALES.finditer(text):
            key = m.group(1)
            keys[key]["usages"] += 1
            keys[key]["sources"].add(rel)
        for m in RE_I18N_STRING.finditer(text):
            key = m.group(1)
            keys[key]["usages"] += 1
            keys[key]["sources"].add(rel)

    items = []
    for key in sorted(keys.keys()):
        items.append({
            "key": key,
            "usages": keys[key]["usages"],
            "sources": sorted(keys[key]["sources"]),
        })
    return {
        "total": sum(k["usages"] for k in items),
        "unique_keys": len(items),
        "keys": items,
    }


# ---------- FASE 6: Startup tasks ----------

# `launcher.addTasks([...])` con items tipo `const XxxTask()` o
# `if (...) XxxTask()` o `if (...) ...[X, Y]`.
RE_ADD_TASKS = re.compile(r"launcher\.addTasks\s*\(\s*\[", re.DOTALL)
# Item simple: opcional `if (cond)` + class name + `()`.
RE_TASK_ITEM = re.compile(
    r"(?P<cond>if\s*\([^)]+\)\s+)?(?P<cls>\w+)\(\)\s*,?",
)


def extract_startup_tasks(src_root: Path, fuente: str) -> dict:
    flutterlib = src_root / fuente / FLUTTER_LIB_REL
    if not flutterlib.is_dir():
        return None
    startup_path = flutterlib / "startup" / "startup.dart"
    if not startup_path.is_file():
        return {"file": None, "ordered_tasks": [], "total": 0}
    text = startup_path.read_text(encoding="utf-8")
    rel = str(startup_path.relative_to(SKILL_ROOT))

    m = RE_ADD_TASKS.search(text)
    if m is None:
        return {"file": rel, "ordered_tasks": [], "total": 0}
    open_bracket = m.end() - 1  # posición de `[`
    # Balancear los corchetes para encontrar el cierre.
    depth = 0
    i = open_bracket
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
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                body = text[open_bracket + 1:i]
                break
        i += 1
    else:
        body = ""

    # Iterar items. Manejar:
    #  - `XxxTask(),`
    #  - `if (...) XxxTask(),`
    #  - `if (...) ...[ X, Y ],` (spread)
    tasks = []
    idx = 0
    i = 0
    while i < len(body):
        # Saltar whitespace y comentarios.
        while i < len(body) and body[i] in " \t\n\r":
            i += 1
        if i >= len(body):
            break
        # Comentario de línea.
        if body[i] == "/" and i + 1 < len(body) and body[i + 1] == "/":
            j = body.find("\n", i)
            i = len(body) if j == -1 else j + 1
            continue
        # Comentario de bloque.
        if body[i] == "/" and i + 1 < len(body) and body[i + 1] == "*":
            j = body.find("*/", i + 2)
            i = len(body) if j == -1 else j + 2
            continue
        # `if (cond) XxxTask(),`
        m = re.match(r"if\s*\((?P<cond>[^)]+)\)\s+(?P<rest>.+)", body[i:])
        if m:
            cond = m.group("cond").strip()
            rest = m.group("rest")
            # Verificar si rest es `...[ X, Y ]` (spread).
            sp = re.match(r"\.\.\.\s*\[(?P<inner>[^\]]*)\]", rest, re.DOTALL)
            if sp:
                inner = sp.group("inner")
                for itm in split_top_level_args(inner):
                    itm = itm.strip()
                    if not itm:
                        continue
                    cls_m = re.match(r"(\w+)\(\)", itm)
                    if cls_m:
                        tasks.append({
                            "class": cls_m.group(1),
                            "index": idx,
                            "conditional": True,
                            "condition": cond,
                            "decl_line": find_line_for_offset(body, i) + body[:i].count("\n"),
                        })
                        idx += 1
                i += m.end()
                # Avanzar después de la `,` si la hay.
                while i < len(body) and body[i] in " \t\n\r,":
                    i += 1
                continue
            cls_m = re.match(r"(\w+)\(\)", rest)
            if cls_m:
                tasks.append({
                    "class": cls_m.group(1),
                    "index": idx,
                    "conditional": True,
                    "condition": cond,
                })
                idx += 1
                i += m.end()
                while i < len(body) and body[i] in " \t\n\r,":
                    i += 1
                continue
        # `XxxTask(),` simple.
        cls_m = re.match(r"(\w+)\(\)\s*,?", body[i:])
        if cls_m:
            tasks.append({
                "class": cls_m.group(1),
                "index": idx,
                "conditional": False,
                "condition": None,
            })
            idx += 1
            i += cls_m.end()
            while i < len(body) and body[i] in " \t\n\r,":
                i += 1
            continue
        # Si no matchea nada, saltar un carácter para evitar bucle infinito.
        i += 1

    return {"file": rel, "ordered_tasks": tasks, "total": len(tasks)}


# ---------- CLI ----------

def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description=(
            "Extrae 6 bloques misceláneos (routes, shortcuts, feature_flags, "
            "error_codes, i18n_keys, startup_tasks) del workspace AppFlowy. "
            "Ver AGENTS.md §5.1 / ROADMAP.md A2.6."
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
    out_path = out_dir / "misc.json"

    routes = None
    shortcuts = None
    feature_flags = None
    error_codes = None
    i18n_keys = None
    startup_tasks = None

    for fuente in fuentes:
        if routes is None:
            routes = extract_routes(src_root, fuente)
        if shortcuts is None:
            shortcuts = extract_shortcuts(src_root, fuente)
        if feature_flags is None:
            feature_flags = extract_feature_flags(src_root, fuente)
        if error_codes is None:
            error_codes = extract_error_codes(src_root, fuente)
        if i18n_keys is None:
            i18n_keys = extract_i18n_keys(src_root, fuente)
        if startup_tasks is None:
            startup_tasks = extract_startup_tasks(src_root, fuente)

    summary = {
        "total_routes": (routes or {}).get("total", 0),
        "total_shortcuts": (shortcuts or {}).get("total", 0),
        "total_feature_flags": (feature_flags or {}).get("total", 0),
        "total_error_codes": (error_codes or {}).get("total", 0),
        "total_i18n_keys": (i18n_keys or {}).get("unique_keys", 0),
        "total_startup_tasks": (startup_tasks or {}).get("total", 0),
    }

    out_obj = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tool": {"name": TOOL_NAME, "version": TOOL_VERSION},
        "fuentes": sorted(set(fuentes)),
        "routes": routes,
        "shortcuts": shortcuts,
        "feature_flags": feature_flags,
        "error_codes": error_codes,
        "i18n_keys": i18n_keys,
        "startup_tasks": startup_tasks,
        "summary": summary,
    }
    out_path.write_text(json.dumps(out_obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Resumen a stderr
    print(f"  escrito:               {out_path}", file=sys.stderr)
    print(f"  routes:                {summary['total_routes']}", file=sys.stderr)
    print(f"  shortcuts:             {summary['total_shortcuts']} ({shortcuts or {}})", file=sys.stderr)
    print(f"  feature_flags:         {summary['total_feature_flags']}", file=sys.stderr)
    print(f"  error_codes:           {summary['total_error_codes']} (ErrorCode)", file=sys.stderr)
    print(f"  i18n_keys (unique):    {summary['total_i18n_keys']}", file=sys.stderr)
    print(f"  startup_tasks:         {summary['total_startup_tasks']}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
