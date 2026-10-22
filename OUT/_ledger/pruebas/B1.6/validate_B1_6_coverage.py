#!/usr/bin/env python3
"""validate_B1_6_coverage.py — prueba literal del ROADMAP B1.6.

Verifica que los 4 sub-docs de tipos de Collab (`02-folder`,
`03-documento`, `04-database`, `05-user-awareness`) tienen
`classDiagram` con clases reales del código de `collab/`.

Uso: validate_B1_6_coverage.py [--json] [--quiet]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT_DEFAULT = SCRIPT_DIR.parents[3]
BRIDGE_DIR = PROJECT_ROOT_DEFAULT / "OUT" / "07-motor-colaborativo-crdt"


def get_class_diagram(doc: Path) -> str:
    text = doc.read_text(encoding="utf-8")
    # Extract the first classDiagram block
    m = re.search(r"```mermaid\n\s*classDiagram.*?```", text, re.DOTALL)
    return m.group(0) if m else ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    targets = {
        "02-folder": {
            "doc": BRIDGE_DIR / "02-folder.md",
            "required_classes": ["View", "Workspace", "FolderData", "ViewLayout", "ViewIdentifier"],
        },
        "03-documento": {
            "doc": BRIDGE_DIR / "03-documento.md",
            "required_classes": ["DocumentData", "Block", "CollabDocument", "DocumentAwareness"],
        },
        "04-database": {
            "doc": BRIDGE_DIR / "04-database.md",
            "required_classes": ["Field", "Row", "Cell", "View", "DatabaseState", "FieldType"],
        },
        "05-user-awareness": {
            "doc": BRIDGE_DIR / "05-user-awareness.md",
            "required_classes": ["UserAwareness", "UserAwarenessState", "UserMetadata", "Selection", "Cursor"],
        },
    }

    results = {}
    for key, info in targets.items():
        doc = info["doc"]
        diag = get_class_diagram(doc)
        found = []
        missing = []
        for cls in info["required_classes"]:
            # Match as a class name in classDiagram
            if re.search(rf"\bclass\s+{re.escape(cls)}\b|\b{re.escape(cls)}\b", diag):
                found.append(cls)
            else:
                missing.append(cls)
        results[key] = {
            "doc": str(doc),
            "required": info["required_classes"],
            "found": found,
            "missing": missing,
            "ok": not missing,
        }

    all_ok = all(r["ok"] for r in results.values())
    payload = {
        "code": "OK" if all_ok else "E_MISSING",
        "results": results,
    }
    if args.json or not args.quiet:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
