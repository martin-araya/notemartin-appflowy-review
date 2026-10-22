#!/usr/bin/env python3
"""validate_B1_1_coverage.py — prueba literal del ROADMAP B1.1.

Verifica que cada carpeta de primer y segundo nivel de las 3 fuentes
(excluyendo `.git*`) aparece en `OUT/03-estructura-del-repo.md`. Forma
parte de la suite `validate-B*.sh` que la fase C1 ejecutará.

Uso: validate_B1_1_coverage.py [--doc PATH] [--src-root DIR]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
# Subimos 4 niveles para llegar a la raíz del proyecto:
# _ledger/pruebas/B1.1/ -> _ledger/pruebas/ -> _ledger/ -> OUT/ -> notemartin-appflowy-review/
PROJECT_ROOT_DEFAULT = SCRIPT_DIR.parents[3]
DEFAULT_DOC = PROJECT_ROOT_DEFAULT / "OUT" / "03-estructura-del-repo.md"
DEFAULT_SRC = PROJECT_ROOT_DEFAULT / "SRC"

FUENTES = ("appflowy", "collab", "editor")
EXCLUDE_TOP = (".git", ".github")  # excluded (no se enumeran sub-carpetas)


def collect_real_folders(src_root: Path) -> dict[str, set[str]]:
    real: dict[str, set[str]] = {}
    for fuente in FUENTES:
        base = src_root / fuente
        if not base.is_dir():
            continue
        real[fuente] = set()
        for root, _dirs, _files in os.walk(base):
            rel = str(root[len(str(base)) + 1:]) if root != str(base) else ""
            if any(rel == e or rel.startswith(e + "/") for e in EXCLUDE_TOP):
                continue
            parts = [p for p in rel.split("/") if p]
            if len(parts) <= 2:
                real[fuente].add(rel)
    return real


def doc_text(doc: Path) -> str:
    txt = doc.read_text(encoding="utf-8")
    # strip fenced code blocks (Mermaid)
    return re.sub(r"```[\s\S]*?```", "", txt)


def is_mentioned(folder: str, text: str) -> bool:
    forms = {folder, folder.rstrip("/"), folder.split("/")[-1]}
    return any(f in text for f in forms)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC)
    parser.add_argument("--src-root", type=Path, default=DEFAULT_SRC)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--no-color", action="store_true")
    args = parser.parse_args()

    real = collect_real_folders(args.src_root)
    text = doc_text(args.doc)
    total = sum(len(v) for v in real.values())
    missing: list[tuple[str, str]] = []
    for fuente, folders in real.items():
        for folder in sorted(folders):
            if not folder:
                continue
            if not is_mentioned(folder, text):
                missing.append((fuente, folder))

    ok = len(missing) == 0
    payload = {
        "code": "OK" if ok else "E_MISSING_FOLDER",
        "total_real_folders_l1_l2": total,
        "missing_count": len(missing),
        "missing": [{"fuente": f, "folder": d} for f, d in missing],
        "doc": str(args.doc),
        "src_root": str(args.src_root),
    }
    if args.json or not args.quiet:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
