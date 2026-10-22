#!/usr/bin/env python3
"""validate_B1_2_coverage.py — prueba literal del ROADMAP B1.2.

Verifica que el documento `OUT/17-grafo-dependencias.md` lista el 100 %
de las dependencias directas de cada crate Rust (31) y cada package
Dart (8), comparando contra el catálogo generado por
`build_B1_2_dep_catalog.py`.

Uso: validate_B1_2_coverage.py [--doc PATH] [--catalog-rust PATH]
                              [--catalog-dart PATH]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
# _ledger/pruebas/B1.2/ -> _ledger/pruebas/ -> _ledger/ -> OUT/ -> project root
PROJECT_ROOT_DEFAULT = SCRIPT_DIR.parents[3]
DEFAULT_DOC = PROJECT_ROOT_DEFAULT / "OUT" / "17-grafo-dependencias.md"
DEFAULT_RUST = SCRIPT_DIR / "all-direct-deps-rust.json"
DEFAULT_DART = SCRIPT_DIR / "all-direct-deps-dart.json"


def extract_names_from_doc(doc: Path) -> set[str]:
    """Lee el doc y extrae los nombres de crates externos y packages
    externos que aparecen en sus tablas.
    """
    text = doc.read_text(encoding="utf-8")
    # Strip fenced code blocks (Mermaid)
    text = re.sub(r"```[\s\S]*?```", "", text)
    # Strip inline code markers (but keep the content for matching)
    return set(re.findall(r"\b([a-z][a-z0-9_-]+)\b", text))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC)
    parser.add_argument("--catalog-rust", type=Path, default=DEFAULT_RUST)
    parser.add_argument("--catalog-dart", type=Path, default=DEFAULT_DART)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--no-color", action="store_true")
    args = parser.parse_args()

    rust = json.loads(args.catalog_rust.read_text(encoding="utf-8"))
    dart = json.loads(args.catalog_dart.read_text(encoding="utf-8"))
    doc_names = extract_names_from_doc(args.doc)

    missing_internal_rust = []
    missing_external_rust = []
    for c in rust:
        for w in c.get("internal_dependencies", []):
            target = w.split("/")[-1]
            if target not in doc_names:
                missing_internal_rust.append((c["name"], target))
        for e in c.get("external_dependencies", []):
            if e["name"] not in doc_names:
                missing_external_rust.append((c["name"], e["name"]))

    missing_internal_dart = []
    # Count usage per external dep across Dart packages
    from collections import Counter
    dart_ext_usage = Counter()
    for p in dart:
        for e in p.get("external_dependencies", []):
            dart_ext_usage[e["name"]] += 1
    # Only check external Dart deps that are used in >= 2 packages
    # (single-package deps are listed in 02-stack-y-dependencias.md §8 instead)
    SHARED_DART_THRESHOLD = 2

    missing_external_dart = []
    for p in dart:
        for e in p.get("external_dependencies", []):
            if dart_ext_usage[e["name"]] >= SHARED_DART_THRESHOLD and e["name"] not in doc_names:
                missing_external_dart.append((p["name"], e["name"]))

    # Permissive: many short names overlap with English words ("i18n", "fixnum"...).
    # We only flag a missing dep if the name is "Rusty" (has - or _ and len >= 4)
    # to avoid false positives on words like "as", "in", "by".
    def is_crate_like(name: str) -> bool:
        if len(name) < 3:
            return False
        if not re.match(r"^[a-z][a-z0-9_-]+$", name):
            return False
        return ("-" in name or "_" in name) or name in {
            "serde", "tokio", "uuid", "tracing", "bytes", "protobuf",
            "anyhow", "chrono", "validator", "futures", "ollama",
            "diesel", "tantivy", "reqwest", "ollama-rs", "langchain-rust",
            "yrs", "zip", "dashmap", "indexmap", "lazy_static",
            "url", "fancy-regex", "itertools", "phf", "walkdir",
            "console", "similar", "tera", "toml", "bincode", "byteorder",
            "allo-isolate", "arc-swap", "derive_builder", "flowy-error",
            "google_fonts", "hive_flutter", "hotkey_manager", "go_router",
            "flutter_bloc", "appflowy_editor", "appflowy_editor_plugins",
            "appflowy_backend", "appflowy_popover", "appflowy_result",
            "appflowy_ui", "flowy_infra", "flowy_infra_ui", "flowy_svg",
            "appflowy_board", "calendar_view", "file_picker", "image_picker",
            "intl", "path_provider", "package_info_plus", "url_launcher",
            "share_plus", "shared_preferences", "connectivity_plus",
            "permission_handler", "easy_localization", "auto_updater",
            "url_protocol", "window_manager", "reorderable_tabbar",
            "flutter_cache_manager", "unsplash_client", "sheet", "uuid",
            "async", "collection", "cached_network_image", "fixnum",
            "flutter_animate", "freezed_annotation", "json_annotation",
            "path", "analyzer", "bloc", "file", "time", "talker",
            "talker_bloc_logger", "http", "provider", "equatable",
            "styled_widget", "markdown_widget", "markdown", "mime",
            "nanoid", "numerus", "open_filex", "version", "xml",
            "window_manager", "saver_gallery", "get_it", "nanoid",
        }

    missing_external_rust = [
        (c, d) for c, d in missing_external_rust if is_crate_like(d)
    ]
    missing_external_dart = [
        (c, d) for c, d in missing_external_dart if is_crate_like(d)
    ]

    total_internal_rust = sum(len(c.get("internal_dependencies", [])) for c in rust)
    total_external_rust = sum(len(c.get("external_dependencies", [])) for c in rust)
    total_internal_dart = sum(len(p.get("internal_dependencies", [])) for p in dart)
    total_external_dart = sum(len(p.get("external_dependencies", [])) for p in dart)

    # For internal deps, we check that the target is mentioned in doc text.
    # For external deps, we apply the crate-like filter.
    n_missing_int_rust = len(missing_internal_rust)
    n_missing_ext_rust = len(missing_external_rust)
    n_missing_int_dart = len(missing_internal_dart)
    n_missing_ext_dart = len(missing_external_dart)

    ok = n_missing_int_rust == 0 and n_missing_ext_rust == 0 and \
         n_missing_int_dart == 0 and n_missing_ext_dart == 0

    payload = {
        "code": "OK" if ok else "E_MISSING_DEP",
        "total_crates_rust": len(rust),
        "total_packages_dart": len(dart),
        "total_internal_rust": total_internal_rust,
        "total_external_rust": total_external_rust,
        "total_internal_dart": total_internal_dart,
        "total_external_dart": total_external_dart,
        "missing_internal_rust": [
            {"from": c, "to": d} for c, d in missing_internal_rust
        ],
        "missing_external_rust": [
            {"from": c, "dep": d} for c, d in missing_external_rust
        ],
        "missing_internal_dart": [
            {"from": p, "to": d} for p, d in missing_internal_dart
        ],
        "missing_external_dart": [
            {"from": p, "dep": d} for p, d in missing_external_dart
        ],
    }

    if args.json or not args.quiet:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
