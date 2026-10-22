#!/usr/bin/env python3
"""validate_B1_3_coverage.py — prueba de cobertura de la fase B1.3.

Verifica que el documento `OUT/04-arquitectura-global.md` cubre los
elementos clave de la arquitectura:
  - 5 contenedores C4 (App Flutter, SDK Rust, Workspace Colab, Librería
    Editor, Backend opcional).
  - 30 crates Rust (uno por sección §T5.2 o §T7.1).
  - 17 features Dart del ROADMAP (F01-F17) + F21.
  - 9 capas (§T6.10).

Uso: validate_B1_3_coverage.py [--doc PATH] [--json] [--quiet]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
# _ledger/pruebas/B1.3/ -> _ledger/pruebas/ -> _ledger/ -> OUT/ -> project root
PROJECT_ROOT_DEFAULT = SCRIPT_DIR.parents[3]
DEFAULT_DOC = PROJECT_ROOT_DEFAULT / "OUT" / "04-arquitectura-global.md"

CONTAINERS = [
    "App Flutter", "SDK Rust", "Workspace Colab", "Librería Editor",
    "Backend opcional",
]

# 30 crates Rust del workspace
RUST_CRATES = [
    "dart-ffi", "flowy-core", "collab-integrate",
    "flowy-user", "flowy-user-pub",
    "flowy-folder", "flowy-folder-pub",
    "flowy-document", "flowy-document-pub",
    "flowy-database2", "flowy-database-pub",
    "flowy-ai", "flowy-ai-pub",
    "flowy-search", "flowy-search-pub",
    "flowy-storage", "flowy-storage-pub",
    "flowy-server", "flowy-server-pub",
    "flowy-error", "flowy-notification", "flowy-date",
    "flowy-sqlite", "flowy-sqlite-vec",
    "lib-dispatch", "lib-infra", "lib-log",
    "flowy-ast", "flowy-codegen", "flowy-derive",
    "event-integration-test",
]

DART_FEATURES = [
    "F01", "F02", "F03", "F04", "F05", "F06", "F07", "F08", "F09",
    "F10", "F11", "F12", "F13", "F14", "F15", "F16", "F17", "F21",
]

LAYERS = [
    "Capa 1", "Capa 2", "Capa 3", "Capa 4", "Capa 5",
    "Capa 6", "Capa 7", "Capa 8", "Capa 9",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--no-color", action="store_true")
    args = parser.parse_args()

    text = args.doc.read_text(encoding="utf-8")
    # Strip fenced code blocks (Mermaid) — coverage checks against prose only
    text_prose = re.sub(r"```[\s\S]*?```", "", text)

    missing_containers = [c for c in CONTAINERS if c not in text_prose]
    missing_crates = [c for c in RUST_CRATES if c not in text_prose]
    missing_features = [f for f in DART_FEATURES if f not in text_prose]
    missing_layers = [l for l in LAYERS if l not in text_prose]

    payload = {
        "code": "OK" if not (missing_containers or missing_crates or
                              missing_features or missing_layers) else "E_MISSING",
        "containers": {
            "expected": len(CONTAINERS),
            "present": len(CONTAINERS) - len(missing_containers),
            "missing": missing_containers,
        },
        "rust_crates": {
            "expected": len(RUST_CRATES),
            "present": len(RUST_CRATES) - len(missing_crates),
            "missing": missing_crates,
        },
        "dart_features": {
            "expected": len(DART_FEATURES),
            "present": len(DART_FEATURES) - len(missing_features),
            "missing": missing_features,
        },
        "layers": {
            "expected": len(LAYERS),
            "present": len(LAYERS) - len(missing_layers),
            "missing": missing_layers,
        },
    }

    if args.json or not args.quiet:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    ok = not (missing_containers or missing_crates or
              missing_features or missing_layers)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
