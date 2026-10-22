#!/usr/bin/env python3
"""validate_B1_7_coverage.py — prueba literal del ROADMAP B1.7.

Verifica que el `erDiagram` de `OUT/08-persistencia/01-sqlite-schema.md`
contiene todas las 16 tablas de `appflowy/frontend/rust-lib/flowy-sqlite/src/schema.rs`.

Uso: validate_B1_7_coverage.py [--json] [--quiet]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT_DEFAULT = SCRIPT_DIR.parents[3]
SCHEMA = PROJECT_ROOT_DEFAULT / "SRC" / "appflowy" / "frontend" / "rust-lib" / "flowy-sqlite" / "src" / "schema.rs"
DOC = PROJECT_ROOT_DEFAULT / "OUT" / "08-persistencia" / "01-sqlite-schema.md"


def extract_tables_from_schema() -> set[str]:
    """Lee schema.rs y extrae los nombres de tabla de los `diesel::table! { name (pk) { ... } }`."""
    text = SCHEMA.read_text(encoding="utf-8")
    # Pattern: `diesel::table! { name (pk) {` (or `diesel::table! { name {` if no PK columns)
    matches = re.findall(r"diesel::table!\s*\{\s*([a-z_][a-z0-9_]*)\s*\(", text)
    return set(matches)


def extract_tables_from_doc(doc_text: str) -> set[str]:
    """Lee el `erDiagram` del doc y extrae los nombres de entidad."""
    # Find the erDiagram block
    m = re.search(r"```mermaid\n\s*erDiagram.*?```", doc_text, re.DOTALL)
    if not m:
        return set()
    block = m.group(0)
    # Pattern: each entity is a line like "  table_name {" or "  af_collab_metadata {"
    tables = re.findall(r"^\s*([a-z_][a-z0-9_]*)\s*\{", block, re.MULTILINE)
    return set(tables)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    schema_tables = extract_tables_from_schema()
    doc_text = DOC.read_text(encoding="utf-8")
    doc_tables = extract_tables_from_doc(doc_text)

    missing_in_doc = sorted(schema_tables - doc_tables)
    extra_in_doc = sorted(doc_tables - schema_tables)
    ok = not missing_in_doc

    payload = {
        "code": "OK" if ok else "E_MISSING_TABLE",
        "schema_total": len(schema_tables),
        "doc_total": len(doc_tables),
        "schema_tables": sorted(schema_tables),
        "doc_tables": sorted(doc_tables),
        "missing_in_doc": missing_in_doc,
        "extra_in_doc": extra_in_doc,
        "ok": ok,
    }
    if args.json or not args.quiet:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
