#!/usr/bin/env python3
# extract_deps.py — Recorre el workspace Rust (`Cargo.toml` raíz + cada
#   crate interno) y el workspace Dart (`pubspec.yaml` + `pubspec.lock`
#   + cada `packages/*/pubspec.yaml`) y emite
#   `OUT/_ledger/extract/deps.json` con dos grafos (Rust + Dart) y un
#   bloque Mermaid crudo por cada uno.
#
# Sin cargo. Sin pip (más allá de `tomli` opcional). Solo stdlib.
# Para Python 3.11+ usa `tomllib`; para 3.9/3.10 cae a `tomli` (misma API).
#
# Ver AGENTS.md §5.1 y ROADMAP.md A2.5.
#
# Uso:
#   extract_deps.py [--src-root DIR] [--out-dir DIR]
#                    [--fuente NAME]... [--help]

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------- import toml lib ----------

try:
    import tomllib as toml_lib  # Python 3.11+
except ImportError:  # pragma: no cover
    try:
        import tomli as toml_lib  # type: ignore
    except ImportError:
        print("ERROR: neither `tomllib` (3.11+) nor `tomli` is installed.", file=sys.stderr)
        print("       Install with: pip3 install tomli", file=sys.stderr)
        sys.exit(2)

# ---------- constantes ----------

SCRIPT_PATH = Path(__file__).resolve()
SKILL_ROOT = SCRIPT_PATH.parent.parent.parent
SRC_DEFAULT = SKILL_ROOT / "SRC"
OUT_DIR_DEFAULT = SKILL_ROOT / "OUT" / "_ledger" / "extract"
DEFAULT_FUENTES = ("appflowy",)
RUSTLIB_REL = Path("frontend/rust-lib")
FLUTTER_LIB_REL = Path("frontend/appflowy_flutter")

SCHEMA_VERSION = "1.0"
TOOL_NAME = "extract_deps.py"
TOOL_VERSION = "1.0"


# ---------- helpers ----------

def load_toml(path: Path) -> dict:
    """Carga un archivo TOML."""
    with path.open("rb") as f:
        return toml_lib.load(f)


def parse_pubstyle_path(dep_spec: dict) -> tuple:
    """Devuelve (kind, payload) para un valor del deps map de pubspec.yaml.
    kind ∈ {'path', 'git', 'hosted', 'sdk'}.
    """
    if not isinstance(dep_spec, dict):
        # pubspec: `name: "1.2.3"` (string constraint) o `name: ^1.0` (raw).
        return ("hosted", {"version_constraint": str(dep_spec)})
    if "path" in dep_spec:
        return ("path", {"path": dep_spec["path"]})
    if "git" in dep_spec:
        git = dep_spec["git"]
        if isinstance(git, dict):
            return ("git", {"url": git.get("url", ""), "ref": git.get("ref", "")})
        return ("git", {"url": git, "ref": ""})
    if "sdk" in dep_spec:
        return ("sdk", {"sdk": dep_spec["sdk"]})
    if "version" in dep_spec:
        return ("hosted", {"version_constraint": dep_spec["version"]})
    return ("unknown", {})


# ---------- FASE 1: Rust ----------

def extract_rust(src_root: Path, fuente: str) -> dict:
    """Procesa el workspace Rust y cada crate interno."""
    rustlib = src_root / fuente / RUSTLIB_REL
    if not rustlib.is_dir():
        return None
    root_toml = rustlib / "Cargo.toml"
    if not root_toml.is_file():
        return None
    workspace = load_toml(root_toml)

    workspace_deps_raw = workspace.get("workspace", {}).get("dependencies", {})
    members_raw = workspace.get("workspace", {}).get("members", [])
    # `members` puede ser lista de strings o lista de dicts (`{ path = "..." }`).
    member_paths = []
    for m in members_raw:
        if isinstance(m, str):
            member_paths.append((m, m))
        elif isinstance(m, dict) and "path" in m:
            member_paths.append((m.get("name") or Path(m["path"]).name, m["path"]))

    # Catalogar workspace_dependencies: name -> {path|version|git|..., kind}
    workspace_deps = {}
    for name, spec in workspace_deps_raw.items():
        if not isinstance(spec, dict):
            workspace_deps[name] = {
                "version": str(spec),
                "kind": "external_registry",
            }
            continue
        if "path" in spec:
            workspace_deps[name] = {
                "path": spec["path"],
                "kind": "internal_workspace",
            }
        elif "git" in spec:
            git = spec["git"]
            if isinstance(git, dict):
                workspace_deps[name] = {
                    "git": git.get("url", ""),
                    "rev": git.get("rev", ""),
                    "kind": "external_git",
                }
            else:
                workspace_deps[name] = {"git": git, "kind": "external_git"}
        else:
            # version-only o version+features
            workspace_deps[name] = {
                "version": spec.get("version", ""),
                "kind": "external_registry",
            }
            if "features" in spec:
                workspace_deps[name]["features"] = spec["features"]
            if "default-features" in spec:
                workspace_deps[name]["default_features"] = spec["default-features"]

    # Procesar cada crate interno.
    crates = []
    internal_edges = set()
    for crate_name, member_path in member_paths:
        crate_toml_path = rustlib / member_path / "Cargo.toml"
        if not crate_toml_path.is_file():
            continue
        try:
            crate_toml = load_toml(crate_toml_path)
        except Exception as e:
            print(f"  WARN: no se pudo parsear {crate_toml_path}: {e}", file=sys.stderr)
            continue
        pkg = crate_toml.get("package", {})
        deps = crate_toml.get("dependencies", {})

        internal = []
        external = []
        for dep_name, dep_spec in deps.items():
            if not isinstance(dep_spec, dict):
                # Forma corta: `dep_name = "1.0"` o `dep_name.workspace = true`.
                if isinstance(dep_spec, str) and "." in dep_spec and "workspace" in dep_spec:
                    # `something.workspace = true`
                    if dep_spec.split(".", 1)[0] in workspace_deps:
                        actual = dep_spec.split(".", 1)[0]
                        if workspace_deps.get(actual, {}).get("kind") == "internal_workspace":
                            internal.append(actual)
                            internal_edges.add((crate_name, actual))
                        else:
                            external.append({
                                "name": actual,
                                "version_constraint": workspace_deps[actual].get("version", ""),
                                "kind": workspace_deps[actual].get("kind", "external_registry"),
                            })
                continue
            # Si tiene `workspace = true`, viene de workspace.dependencies.
            if dep_spec.get("workspace"):
                # Resolver el nombre real (puede ser `flowy_user.workspace = true`
                # donde la clave del workspace es `flowy-user`).
                ws_key = dep_name.replace("_", "-")
                # Búsqueda fuzzy: el workspace.dependencies puede usar
                # guiones o subrayes; probar ambos.
                if ws_key not in workspace_deps:
                    for k in workspace_deps:
                        if k.replace("-", "_") == dep_name.replace("-", "_"):
                            ws_key = k
                            break
                if ws_key in workspace_deps:
                    if workspace_deps[ws_key].get("kind") == "internal_workspace":
                        internal.append(ws_key)
                        internal_edges.add((crate_name, ws_key))
                    else:
                        external.append({
                            "name": ws_key,
                            "version_constraint": workspace_deps[ws_key].get("version", ""),
                            "kind": workspace_deps[ws_key].get("kind", "external_registry"),
                        })
                continue
            # Si tiene `path = "..."`, es interno (externo al workspace pero path).
            if "path" in dep_spec:
                external.append({
                    "name": dep_name,
                    "path": dep_spec["path"],
                    "kind": "external_path",
                })
                continue
            # Si tiene `git`, externo.
            if "git" in dep_spec:
                git = dep_spec["git"]
                if isinstance(git, dict):
                    external.append({
                        "name": dep_name,
                        "git": git.get("url", ""),
                        "rev": git.get("rev", ""),
                        "kind": "external_git",
                    })
                else:
                    external.append({"name": dep_name, "git": git, "kind": "external_git"})
                continue
            # version o sin nada.
            external.append({
                "name": dep_name,
                "version_constraint": dep_spec.get("version", ""),
                "kind": "external_registry",
            })
            if "features" in dep_spec:
                external[-1]["features"] = dep_spec["features"]

        internal.sort()
        external.sort(key=lambda e: e["name"])
        crates.append({
            "name": crate_name,
            "path": str((rustlib / member_path).relative_to(SKILL_ROOT)),
            "version": pkg.get("version", ""),
            "edition": pkg.get("edition", ""),
            "internal_dependencies": internal,
            "external_dependencies": external,
        })

    crates.sort(key=lambda c: c["name"])

    # Construir Mermaid.
    mermaid_lines = ["flowchart LR"]
    # Agrupar por crate
    for c in crates:
        for dep in c["internal_dependencies"]:
            mermaid_lines.append(f"  {c['name']} --> {dep}")
    mermaid = "\n".join(mermaid_lines) + "\n"

    return {
        "workspace_root": str(rustlib.relative_to(SKILL_ROOT)),
        "workspace_dependencies": workspace_deps,
        "crates": crates,
        "summary": {
            "total_crates": len(crates),
            "total_internal_edges": len(internal_edges),
            "total_external_deps": sum(len(c["external_dependencies"]) for c in crates),
        },
        "mermaid": mermaid,
    }


# ---------- FASE 2: Dart ----------

def parse_pubspec_yaml(path: Path) -> dict:
    """Carga un pubspec.yaml como TOML. Como YAML, `tomli` no lo parsea
    directamente. Usamos un mini-parser YAML limitado.
    """
    text = path.read_text(encoding="utf-8")
    return parse_simple_yaml(text)


def parse_simple_yaml(text: str) -> dict:
    """Mini-parser YAML para pubspec.yaml. Soporta:
    - Maps anidados con indentación de 2 espacios.
    - Scalars: strings, integers, floats, booleans, null.
    - Listas de scalars.
    """
    lines = text.splitlines()
    # Tokenize: para cada línea, calcular indent y tipo.
    tokens = []
    for ln in lines:
        if not ln.strip() or ln.strip().startswith("#"):
            continue
        indent = len(ln) - len(ln.lstrip(" "))
        tokens.append((indent, ln.strip()))
    # Parse recursivo.
    pos = [0]

    def parse_block(min_indent):
        out = {}
        while pos[0] < len(tokens):
            indent, content = tokens[pos[0]]
            if indent < min_indent:
                break
            if indent > min_indent:
                pos[0] += 1
                continue
            if ":" not in content:
                pos[0] += 1
                continue
            key, _, val = content.partition(":")
            key = key.strip()
            val = val.strip()
            if val == "":
                # Es un bloque anidado.
                pos[0] += 1
                if pos[0] < len(tokens) and tokens[pos[0]][0] > indent:
                    out[key] = parse_block(tokens[pos[0]][0])
                else:
                    out[key] = None
            elif val == "|" or val == ">":
                pos[0] += 1
                block_lines = []
                while pos[0] < len(tokens) and tokens[pos[0]][0] > indent:
                    block_lines.append(tokens[pos[0]][1])
                    pos[0] += 1
                out[key] = "\n".join(block_lines)
            elif val.startswith("[") and val.endswith("]"):
                # Inline list.
                inner = val[1:-1]
                items = [parse_scalar(s.strip()) for s in split_top_level(inner)]
                out[key] = items
                pos[0] += 1
            else:
                out[key] = parse_scalar(val)
                pos[0] += 1
        return out

    def split_top_level(s: str):
        out, depth, cur = [], 0, []
        for ch in s:
            if ch in "[{(":
                depth += 1
                cur.append(ch)
            elif ch in "]})":
                depth -= 1
                cur.append(ch)
            elif ch == "," and depth == 0:
                out.append("".join(cur).strip())
                cur = []
            else:
                cur.append(ch)
        if cur:
            out.append("".join(cur).strip())
        return out

    def parse_scalar(s: str):
        if s.startswith('"') and s.endswith('"'):
            return s[1:-1]
        if s.startswith("'") and s.endswith("'"):
            return s[1:-1]
        if s in ("true", "True"):
            return True
        if s in ("false", "False"):
            return False
        if s in ("null", "~"):
            return None
        try:
            return int(s)
        except ValueError:
            pass
        try:
            return float(s)
        except ValueError:
            pass
        return s

    return parse_block(0)


def parse_pubspec_lock(path: Path) -> dict:
    """Parser minimalista de `pubspec.lock` (formato pseudo-YAML con map
    de paquetes). Devuelve {name: {version, source, ...}}.
    """
    if not path.is_file():
        return {}
    text = path.read_text(encoding="utf-8")
    result = {}
    lines = text.splitlines()
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i].rstrip()
        if not line or line.startswith("#"):
            i += 1
            continue
        # Cabecera `packages:` → saltar.
        if line == "packages:":
            i += 1
            continue
        # Nombre del paquete: `  nombre:` con indent 2.
        stripped = line.lstrip(" ")
        indent = len(line) - len(stripped)
        if indent == 2 and stripped.endswith(":"):
            name = stripped[:-1]
            entry = {"dependency": None, "version": None, "source": None,
                     "path": None, "url": None, "ref": None}
            i += 1
            while i < n:
                sub = lines[i]
                if not sub.strip() or sub.strip().startswith("#"):
                    i += 1
                    continue
                sub_indent = len(sub) - len(sub.lstrip(" "))
                if sub_indent <= 2:
                    break
                sub_stripped = sub.strip()
                if sub_stripped.startswith("dependency:"):
                    val = sub_stripped.split(":", 1)[1].strip().strip('"')
                    entry["dependency"] = val
                elif sub_stripped.startswith("source:"):
                    val = sub_stripped.split(":", 1)[1].strip()
                    entry["source"] = val
                elif sub_stripped.startswith("version:"):
                    val = sub_stripped.split(":", 1)[1].strip().strip('"')
                    entry["version"] = val
                elif sub_stripped.startswith("path:"):
                    val = sub_stripped.split(":", 1)[1].strip().strip('"')
                    entry["path"] = val
                elif sub_stripped.startswith("url:"):
                    val = sub_stripped.split(":", 1)[1].strip().strip('"')
                    entry["url"] = val
                elif sub_stripped.startswith("ref:"):
                    val = sub_stripped.split(":", 1)[1].strip().strip('"')
                    entry["ref"] = val
                # `description:` puede ser multilínea; consolidar hasta el próximo campo.
                elif sub_stripped.startswith("description:"):
                    val = sub_stripped.split(":", 1)[1].strip()
                    entry["description"] = val
                i += 1
            result[name] = entry
            continue
        i += 1
    return result


def extract_dart(src_root: Path, fuente: str) -> dict:
    """Procesa el app Flutter: pubspec.yaml, pubspec.lock, packages/*."""
    app_root = src_root / fuente / FLUTTER_LIB_REL
    if not app_root.is_dir():
        return None

    pubspec_path = app_root / "pubspec.yaml"
    pubspec_lock_path = app_root / "pubspec.lock"
    if not pubspec_path.is_file():
        return None
    app_yaml = parse_pubspec_yaml(pubspec_path)
    lock_data = parse_pubspec_lock(pubspec_lock_path)

    app_name = app_yaml.get("name", "appflowy")
    app_version = app_yaml.get("version", "")
    deps = app_yaml.get("dependencies", {})
    dev_deps = app_yaml.get("dev_dependencies", {})

    def classify_deps(dep_map: dict) -> tuple:
        internal = []
        external = []
        for dep_name, dep_spec in dep_map.items():
            if not isinstance(dep_spec, dict):
                external.append({"name": dep_name, "version_constraint": str(dep_spec),
                                 "kind": "external_registry"})
                continue
            kind, payload = parse_pubstyle_path(dep_spec)
            # Mapear kind crudo ("path"/"git"/"hosted"/"sdk"/"unknown") a
            # `internal_*` o `external_*` para consistencia con el plan.
            if kind == "path":
                kind_out = "internal_path"
                entry = {"name": dep_name, **payload, "kind": kind_out}
                internal.append(entry)
            else:
                entry = {"name": dep_name, **payload, "kind": f"external_{kind}" if kind != "unknown" else "external_unknown"}
                if "git" in dep_spec and isinstance(dep_spec["git"], dict):
                    entry["git_url"] = dep_spec["git"].get("url", "")
                    entry["git_ref"] = dep_spec["git"].get("ref", "")
                # Buscar versión resuelta en pubspec.lock
                lock_entry = lock_data.get(dep_name, {})
                if lock_entry.get("version"):
                    entry["resolved"] = lock_entry["version"]
                external.append(entry)
        return internal, external

    main_internal, main_external = classify_deps(deps)
    dev_internal, dev_external = classify_deps(dev_deps)

    # Packages internos en packages/*.
    packages_dir = app_root / "packages"
    internal_packages = []
    if packages_dir.is_dir():
        for pkg_yaml_path in sorted(packages_dir.glob("*/pubspec.yaml")):
            try:
                pkg_yaml = parse_pubspec_yaml(pkg_yaml_path)
            except Exception as e:
                print(f"  WARN: no se pudo parsear {pkg_yaml_path}: {e}", file=sys.stderr)
                continue
            pkg_name = pkg_yaml.get("name", pkg_yaml_path.parent.name)
            pkg_version = pkg_yaml.get("version", "")
            pkg_deps = pkg_yaml.get("dependencies", {})
            pkg_int, pkg_ext = classify_deps(pkg_deps)
            # Enriquecer con versión resuelta.
            for ext in pkg_ext:
                lock_entry = lock_data.get(ext["name"], {})
                if lock_entry.get("version"):
                    ext["resolved"] = lock_entry["version"]
            internal_packages.append({
                "name": pkg_name,
                "version": pkg_version,
                "path": str(pkg_yaml_path.relative_to(SKILL_ROOT)),
                "internal_dependencies": pkg_int,
                "external_dependencies": pkg_ext,
            })

    # Mermaid.
    mermaid_lines = ["flowchart LR"]
    for d in main_internal:
        mermaid_lines.append(f"  {app_name} --> {d['name']}")
    for ip in internal_packages:
        # Edges: app -> internal package
        # Buscar si el internal package está en main_internal
        names = {d["name"] for d in main_internal}
        if ip["name"] in names:
            mermaid_lines.append(f"  {app_name} --> {ip['name']}")
    mermaid = "\n".join(mermaid_lines) + "\n"

    return {
        "app_root": str(app_root.relative_to(SKILL_ROOT)),
        "packages": [{
            "name": app_name,
            "version": app_version,
            "path": str(app_root.relative_to(SKILL_ROOT)),
            "internal_dependencies": main_internal,
            "external_dependencies": main_external,
        }],
        "dev_dependencies": {
            "internal": dev_internal,
            "external": dev_external,
        },
        "internal_packages": internal_packages,
        "summary": {
            "total_packages": 1 + len(internal_packages),
            "total_internal_packages": len(internal_packages),
            "total_internal_edges": len(main_internal) + sum(len(p["internal_dependencies"]) for p in internal_packages),
            "total_external_deps": len(main_external) + sum(len(p["external_dependencies"]) for p in internal_packages),
            "total_resolved_packages": len(lock_data),
        },
        "mermaid": mermaid,
    }


# ---------- CLI ----------

def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description=(
            "Extrae grafos de dependencias Rust (Cargo workspace) y Dart "
            "(pubspec workspace) y los serializa a "
            "OUT/_ledger/extract/deps.json con bloques Mermaid. "
            "Ver AGENTS.md §5.1 / ROADMAP.md A2.5."
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
    out_path = out_dir / "deps.json"

    rust_data = None
    dart_data = None
    for fuente in fuentes:
        if rust_data is None:
            rust_data = extract_rust(src_root, fuente)
        if dart_data is None:
            dart_data = extract_dart(src_root, fuente)

    # Validaciones internas.
    if rust_data is not None:
        assert rust_data["summary"]["total_crates"] == len(rust_data["crates"]), \
            "rust.summary.total_crates inconsistente"
    if dart_data is not None:
        assert dart_data["summary"]["total_packages"] == 1 + len(dart_data["internal_packages"]), \
            "dart.summary.total_packages inconsistente"

    out_obj = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "tool": {"name": TOOL_NAME, "version": TOOL_VERSION},
        "fuentes": sorted(set(fuentes)),
        "rust": rust_data,
        "dart": dart_data,
    }
    out_path.write_text(json.dumps(out_obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    # Resumen a stderr
    print(f"  escrito: {out_path}", file=sys.stderr)
    if rust_data is not None:
        s = rust_data["summary"]
        print(f"  rust: {s['total_crates']} crates, {s['total_internal_edges']} internal edges, {s['total_external_deps']} external deps", file=sys.stderr)
        # Quick check: flowy-core deps
        fc = next((c for c in rust_data["crates"] if c["name"] == "flowy-core"), None)
        if fc:
            flowy_features = [d for d in fc["internal_dependencies"] if d.startswith("flowy-")]
            print(f"  flowy-core.internal_dependencies: {len(fc['internal_dependencies'])} ({len(flowy_features)} flowy-*)", file=sys.stderr)
        dffi = next((c for c in rust_data["crates"] if c["name"] == "dart-ffi"), None)
        if dffi:
            print(f"  dart-ffi.internal_dependencies: {dffi['internal_dependencies']}", file=sys.stderr)
    if dart_data is not None:
        s = dart_data["summary"]
        print(f"  dart: {s['total_packages']} packages ({s['total_internal_packages']} internal), {s['total_internal_edges']} internal edges, {s['total_external_deps']} external deps, {s['total_resolved_packages']} resolved in lock", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
