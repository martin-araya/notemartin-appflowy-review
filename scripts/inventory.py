#!/usr/bin/env python3
# inventory.py — Recorre SRC/{appflowy,collab,editor} y emite
#   OUT/_ledger/inventario.json (archivos fuente) y
#   OUT/_ledger/assets.json (binarios y recursos no-fuente).
# Ver AGENTS.md §9 y ROADMAP.md A1.2.
#
# Uso:
#   inventory.py [--src-root DIR] [--out-dir DIR] [--include LIST] [--help]
#
# Por defecto procesa las 3 fuentes clonadas por fetch_sources.sh
# (appflowy, collab, editor) y escribe los JSON en <skill_root>/OUT/_ledger/.

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from fnmatch import fnmatch
from pathlib import Path

# ---------- constantes (D1, D2, D5, D11, D12) ----------

SCRIPT_PATH = Path(__file__).resolve()
SKILL_ROOT = SCRIPT_PATH.parent.parent.parent  # SKILL/scripts/inventory.py → skill_root
SRC_DEFAULT = SKILL_ROOT / "SRC"
OUT_DIR_DEFAULT = SKILL_ROOT / "OUT" / "_ledger"
DEFAULT_FUENTES = ("appflowy", "collab", "editor")

# Lenguaje por extensión
LANG_BY_EXT = {
    ".dart": "dart",
    ".rs": "rust",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".swift": "swift",
    ".m": "objc",
    ".h": "objc-header",
    ".mm": "objc++",
    ".java": "java",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".json": "json",
    ".md": "markdown",
    ".markdown": "markdown",
    ".sh": "bash",
    ".bash": "bash",
    ".zsh": "bash",
    ".cmake": "cmake",
    ".gradle": "groovy",
    ".proto": "protobuf",
    ".xml": "xml",
    ".plist": "xml",
    ".lock": "toml",
    ".gitignore": "text",
    ".gitattributes": "text",
    ".editorconfig": "text",
    ".arb": "json",
    ".css": "css",
    ".scss": "scss",
    ".html": "html",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".py": "python",
    ".inlang": "json",
}

# Directorios excluidos (D11)
EXCLUDE_DIRS = {
    ".git", "node_modules", "build", "dist", ".dart_tool", ".idea",
    ".gradle", ".vscode", "target", ".symlinks", ".pub-cache",
    "Pods", "ephemeral", ".kotlin",
}

# Patrones de archivo excluidos (D11)
EXCLUDE_FILE_PATTERNS = (
    "Cargo.lock",
    "pubspec.lock",
    "package_config.json",
    "package-lock.json",
    ".DS_Store",
)

# Extensiones de archivos generados (D11)
EXCLUDE_FILE_EXTS = {
    ".pb.dart",        # marcador (se checa con suffix compuesto más abajo)
    ".g.dart",
    ".freezed.dart",
    ".mocks.dart",
    ".gr.dart",
    ".config.dart",
}

# Extensiones binarias (D12)
BINARY_EXTS = {
    "png", "jpg", "jpeg", "gif", "webp", "bmp", "ico", "tif", "tiff",
    "ttf", "otf", "woff", "woff2", "eot",
    "mp3", "mp4", "wav", "ogg", "mov", "webm", "m4a", "flac", "aac",
    "zip", "tar", "gz", "tgz", "7z", "rar", "bz2", "xz", "zst",
    "pb", "bin", "exe", "dll", "so", "dylib", "a", "o", "obj",
    "pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx",
    "class", "jar", "war", "ear", "deb", "rpm", "dmg", "iso",
    "apk", "ipa", "aab", "app", "arsc",
}

# SVG es texto pero va a assets (D12)
ASSET_ALWAYS_EXTS = {"svg"}

# Reglas de capa (D10 + §2 del plan).
# (regex_ext, regex_ruta, capa). Primera coincidencia gana.
# ruta_rel tiene prefijo "<fuente>/" (sin SRC/).
CAPA_RULES = [
    # --- AppFlowy Dart (orden específico → general) ---
    (r"\.dart$", r"^appflowy/frontend/appflowy_flutter/lib/plugins/.*/application/.*_bloc\.dart$", "bloc"),
    (r"\.dart$", r"^appflowy/frontend/appflowy_flutter/lib/workspace/application/.*_bloc\.dart$", "bloc"),
    (r"\.dart$", r"^appflowy/frontend/appflowy_flutter/lib/[^/]+/application/.*_bloc\.dart$", "bloc"),
    (r"\.dart$", r"^appflowy/frontend/appflowy_flutter/lib/.*_bloc\.dart$", "bloc"),
    (r"\.dart$", r"^appflowy/frontend/appflowy_flutter/lib/plugins/.*/application/", "bloc"),
    (r"\.dart$", r"^appflowy/frontend/appflowy_flutter/lib/workspace/application/", "bloc"),
    (r"\.dart$", r"^appflowy/frontend/appflowy_flutter/lib/ai/", "service"),
    (r"\.dart$", r"^appflowy/frontend/appflowy_flutter/lib/user/application/", "bloc"),
    (r"\.dart$", r"^appflowy/frontend/appflowy_flutter/lib/user/", "bloc"),
    (r"\.dart$", r"^appflowy/frontend/appflowy_flutter/lib/startup/", "service"),
    (r"\.dart$", r"^appflowy/frontend/appflowy_flutter/lib/shared/", "service"),
    (r"\.dart$", r"^appflowy/frontend/appflowy_flutter/lib/core/", "service"),
    (r"\.dart$", r"^appflowy/frontend/appflowy_flutter/lib/mobile/application/", "bloc"),
    (r"\.dart$", r"^appflowy/frontend/appflowy_flutter/lib/mobile/", "ui"),
    (r"\.dart$", r"^appflowy/frontend/appflowy_flutter/lib/features/[^/]+/(data|logic)/", "bloc"),
    (r"\.dart$", r"^appflowy/frontend/appflowy_flutter/lib/features/.*/presentation/", "ui"),
    (r"\.dart$", r"^appflowy/frontend/appflowy_flutter/lib/features/.*/domain/", "service"),
    (r"\.dart$", r"^appflowy/frontend/appflowy_flutter/lib/features/", "ui"),
    (r"\.dart$", r"^appflowy/frontend/appflowy_flutter/lib/plugins/.*/presentation/", "ui"),
    (r"\.dart$", r"^appflowy/frontend/appflowy_flutter/lib/plugins/.*/shared/", "ui"),
    (r"\.dart$", r"^appflowy/frontend/appflowy_flutter/lib/plugins/.*/", "ui"),
    (r"\.dart$", r"^appflowy/frontend/appflowy_flutter/lib/workspace/presentation/", "ui"),
    (r"\.dart$", r"^appflowy/frontend/appflowy_flutter/lib/workspace/", "ui"),
    (r"\.dart$", r"^appflowy/frontend/appflowy_flutter/lib/packages/[^/]+/", "ui"),
    (r"\.dart$", r"^appflowy/frontend/appflowy_flutter/lib/", "ui"),
    (r"\.dart$", r"^appflowy/frontend/appflowy_flutter/test/", "test"),
    (r"\.dart$", r"^appflowy/frontend/appflowy_flutter/integration_test/", "test"),
    (r"\.dart$", r"^appflowy/frontend/appflowy_flutter/", "ui"),
    # --- AppFlowy Rust (orden específico → general) ---
    (r"\.rs$", r"^appflowy/frontend/rust-lib/dart-ffi/", "ffi"),
    (r"\.rs$", r"^appflowy/frontend/rust-lib/lib-dispatch/", "dispatch"),
    (r"\.rs$", r"^appflowy/frontend/rust-lib/build-tool/", "codegen"),
    (r"\.rs$", r"^appflowy/frontend/rust-lib/flowy-server/", "server"),
    (r"\.rs$", r"^appflowy/frontend/rust-lib/flowy-sqlite/", "persistence"),
    (r"\.rs$", r"^appflowy/frontend/rust-lib/flowy-sqlite-vec/", "persistence"),
    (r"\.rs$", r"^appflowy/frontend/rust-lib/flowy-storage/", "service"),
    (r"\.rs$", r"^appflowy/frontend/rust-lib/event-integration-test/", "test"),
    (r"\.rs$", r"^appflowy/frontend/rust-lib/.*/event_handler\.rs$", "rust-handler"),
    (r"\.rs$", r"^appflowy/frontend/rust-lib/.*/notification\.rs$", "service"),
    (r"\.rs$", r"^appflowy/frontend/rust-lib/.*/(manager|module)\.rs$", "rust-manager"),
    (r"\.rs$", r"^appflowy/frontend/rust-lib/flowy-[^/]+/src/", "rust-handler"),
    (r"\.rs$", r"^appflowy/frontend/rust-lib/collab-integrate/", "rust-manager"),
    (r"\.rs$", r"^appflowy/frontend/rust-lib/lib-infra/", "service"),
    (r"\.rs$", r"^appflowy/frontend/rust-lib/lib-log/", "service"),
    (r"\.rs$", r"^appflowy/frontend/rust-lib/", "rust-handler"),
    (r"\.rs$", r"^appflowy/frontend/", "rust-handler"),
    # --- AppFlowy-Collab ---
    (r"\.rs$", r"^collab/", "collab"),
    # --- appflowy-editor ---
    (r"\.dart$", r"^editor/lib/src/", "ui"),
    (r"\.dart$", r"^editor/test/", "test"),
    (r"\.dart$", r"^editor/", "ui"),
    # --- Configs y miscelánea ---
    (r"\.proto$", r".*", "config"),
    (r"\.ya?ml$", r".*", "config"),
    (r"\.toml$", r".*", "config"),
    (r"\.json$", r".*", "config"),
    (r"\.md$", r".*", "config"),
    (r"\.arb$", r".*", "i18n"),
    (r"\.inlang$", r".*", "config"),
    (r"\.sh$", r".*", "build"),
    (r"\.gradle$", r".*", "build"),
    (r"\.cmake$", r".*", "build"),
    (r"\.gitignore$", r".*", "config"),
    (r"\.gitattributes$", r".*", "config"),
    # Catch-all defensivo (la prueba exige no-null, así que nunca cae aquí)
    (r".*", r".*", "ui"),
]

# Pre-compila las regex
COMPILED_CAPA = [
    (re.compile(ext), re.compile(ruta), capa)
    for ext, ruta, capa in CAPA_RULES
]


# ---------- helpers ----------

def is_excluded_dir(name: str) -> bool:
    return name in EXCLUDE_DIRS


def is_excluded_file(path: Path) -> bool:
    if path.name in EXCLUDE_FILE_PATTERNS:
        return True
    # extensiones generadas
    name = path.name
    for suf in EXCLUDE_FILE_EXTS:
        if name.endswith(suf):
            return True
    return False


def is_binary(path: Path) -> bool:
    ext = path.suffix.lstrip(".").lower()
    if ext in BINARY_EXTS:
        return True
    if ext in ASSET_ALWAYS_EXTS:
        return True
    return False


def git_hash_or_sha1(path: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "hash-object", str(path)],
            capture_output=True, text=True, check=True, timeout=10,
        ).stdout.strip()
        if len(out) == 40 and all(c in "0123456789abcdef" for c in out):
            return out
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired,
            FileNotFoundError, OSError):
        pass
    try:
        return hashlib.sha1(path.read_bytes()).hexdigest()
    except OSError:
        return ""


def wc_l(path: Path) -> int:
    try:
        out = subprocess.run(
            ["wc", "-l", str(path)],
            capture_output=True, text=True, check=True, timeout=10,
        ).stdout.strip()
        # "      123 path" o "123 path"
        tokens = out.split()
        if tokens:
            return int(tokens[0])
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired,
            FileNotFoundError, OSError, ValueError):
        pass
    try:
        return path.read_bytes().count(b"\n")
    except OSError:
        return 0


def capa_for(ruta_rel: str) -> str:
    ext = Path(ruta_rel).suffix.lower()
    for ext_re, path_re, capa in COMPILED_CAPA:
        if ext_re.fullmatch(ext) and path_re.search(ruta_rel):
            return capa
    return "ui"


def walk_source(fuente: str, src_root: Path):
    base = src_root / fuente
    if not base.is_dir():
        return
    for path in base.rglob("*"):
        if path.is_symlink() and not path.exists():
            continue
        if path.is_dir():
            continue
        # excluir si alguna parte del path es un dir excluido
        rel = path.relative_to(src_root).as_posix()
        parts = rel.split("/")
        if any(is_excluded_dir(p) for p in parts[:-1]):
            continue
        if is_excluded_file(path):
            continue
        yield rel, str(path.resolve())


# ---------- CLI ----------

def parse_args(argv=None):
    p = argparse.ArgumentParser(
        description="Recorre SRC/<fuente> y emite inventario.json + assets.json.",
    )
    p.add_argument("--src-root", type=Path, default=SRC_DEFAULT,
                   help=f"Raíz de los clones (default: {SRC_DEFAULT})")
    p.add_argument("--out-dir", type=Path, default=OUT_DIR_DEFAULT,
                   help=f"Directorio de salida (default: {OUT_DIR_DEFAULT})")
    p.add_argument("--include", type=str, default=",".join(DEFAULT_FUENTES),
                   help=f"Fuentes csv (default: {','.join(DEFAULT_FUENTES)})")
    return p.parse_args(argv)


# ---------- main ----------

def main(argv=None):
    args = parse_args(argv)
    src_root: Path = args.src_root
    out_dir: Path = args.out_dir
    fuentes = [f.strip() for f in args.include.split(",") if f.strip()]

    if not src_root.is_dir():
        print(f"ERROR: src_root no existe: {src_root}", file=sys.stderr)
        return 1
    out_dir.mkdir(parents=True, exist_ok=True)

    inventario = []
    assets = []
    by_fuente = {}
    by_capa = {}
    by_lenguaje = {}
    total_bytes = 0
    total_loc = 0

    for fuente in fuentes:
        count = 0
        for ruta_rel, ruta_abs in walk_source(fuente, src_root):
            p = Path(ruta_abs)
            try:
                stat = p.stat()
            except OSError:
                continue

            if is_binary(p):
                assets.append({
                    "fuente": fuente,
                    "ruta_rel": ruta_rel,
                    "ruta_abs": ruta_abs,
                    "formato": p.suffix.lstrip(".").lower(),
                    "bytes": stat.st_size,
                    "sha1": git_hash_or_sha1(p),
                })
                continue

            ext = p.suffix.lower()
            lenguaje = LANG_BY_EXT.get(ext, "text")
            loc = wc_l(p)
            sha1 = git_hash_or_sha1(p)
            capa = capa_for(ruta_rel)
            inventario.append({
                "fuente": fuente,
                "ruta_rel": ruta_rel,
                "ruta_abs": ruta_abs,
                "lenguaje": lenguaje,
                "loc": loc,
                "sha1": sha1,
                "bytes": stat.st_size,
                "capa": capa,
            })
            count += 1
            total_bytes += stat.st_size
            total_loc += loc
            by_capa[capa] = by_capa.get(capa, 0) + 1
            by_lenguaje[lenguaje] = by_lenguaje.get(lenguaje, 0) + 1
        by_fuente[fuente] = count

    # Orden estable
    inventario.sort(key=lambda e: (e["fuente"], e["ruta_rel"]))
    assets.sort(key=lambda e: (e["fuente"], e["ruta_rel"]))

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    inv_doc = {
        "schema_version": 1,
        "generated_at": ts,
        "src_root": str(src_root.resolve()),
        "fuentes": fuentes,
        "counts": {
            "files": len(inventario),
            "assets": len(assets),
            "by_fuente": by_fuente,
            "by_capa": by_capa,
            "by_lenguaje": by_lenguaje,
            "total_bytes": total_bytes,
            "total_loc": total_loc,
        },
        "files": inventario,
    }
    assets_doc = {
        "schema_version": 1,
        "generated_at": ts,
        "src_root": str(src_root.resolve()),
        "fuentes": fuentes,
        "counts": {"assets": len(assets)},
        "assets": assets,
    }

    inv_path = out_dir / "inventario.json"
    ast_path = out_dir / "assets.json"
    inv_path.write_text(json.dumps(inv_doc, indent=2, sort_keys=False) + "\n")
    ast_path.write_text(json.dumps(assets_doc, indent=2, sort_keys=False) + "\n")

    # Resumen a stderr
    print(f"  files:   {len(inventario)}  (loc: {total_loc:,}, bytes: {total_bytes:,})",
          file=sys.stderr)
    print(f"  assets:  {len(assets)}", file=sys.stderr)
    for f in fuentes:
        print(f"    {f:10} {by_fuente.get(f, 0)} files", file=sys.stderr)
    print(f"  by_capa:      {dict(sorted(by_capa.items()))}", file=sys.stderr)
    print(f"  by_lenguaje:  {dict(sorted(by_lenguaje.items()))}", file=sys.stderr)
    print(f"  escrito: {inv_path}", file=sys.stderr)
    print(f"  escrito: {ast_path}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
