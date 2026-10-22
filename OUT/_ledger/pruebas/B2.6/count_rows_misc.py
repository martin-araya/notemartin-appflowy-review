#!/usr/bin/env python3
"""count_rows_misc.py — cuenta las filas del catálogo misc
(`OUT/16-catalogo-flags-rutas-atajos.md`) y comprueba que sumen
exactamente 1709 (= summary.total_routes + total_shortcuts +
total_feature_flags + total_i18n_keys + total_startup_tasks),
como exige el ROADMAP.

Prerrequisito: el documento ya fue generado por `build_catalog_misc.py`.

Estrategia de conteo:
  - §4 Rutas (35): header `| Path | Name | Archivo |`
  - §5 Hotkeys (13): header `| # | Nombre | Comando | Archivo |`
  - §6 Feature flags (9): header `| # | Variante | Default | decl_line | Archivo |`
  - §7 i18n keys (1637): header `| Key | Usages | Sources |`
  - §8 Startup tasks (15): header `| # | Class | Conditional | Condition |`
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent.parent
DEFAULT_DOC = PROJECT_ROOT / "OUT" / "16-catalogo-flags-rutas-atajos.md"
DEFAULT_MISC = PROJECT_ROOT / "OUT" / "_ledger" / "extract" / "misc.json"

HEADER_S4 = "| Path | Name | Archivo |"
HEADER_S5 = "| # | Nombre | Comando | Archivo |"
HEADER_S6 = "| # | Variante | Default | decl_line | Archivo |"
HEADER_S7 = "| Key | Usages | Sources |"
HEADER_S8 = "| # | Class | Conditional | Condition |"


def extract_table_rows(text: str, header: str) -> list[str]:
    rows: list[str] = []
    in_fence = False
    in_table = False
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not in_table:
            if line.strip() == header:
                in_table = True
            continue
        if not line.startswith("|"):
            in_table = False
            continue
        if re.match(r"^\|\s*-+", line):
            continue
        rows.append(line)
    return rows


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="count_rows_misc.py")
    p.add_argument("--doc", type=Path, default=DEFAULT_DOC)
    p.add_argument("--misc", type=Path, default=DEFAULT_MISC)
    p.add_argument("--quiet", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    if not args.doc.exists():
        print(f"count_rows_misc.py: doc no encontrado: {args.doc}", file=sys.stderr)
        return 2
    if not args.misc.exists():
        print(f"count_rows_misc.py: misc.json no encontrado: {args.misc}", file=sys.stderr)
        return 2

    misc = json.loads(args.misc.read_text(encoding="utf-8"))
    summary = misc["summary"]
    expected_total = (
        summary["total_routes"]
        + summary["total_shortcuts"]
        + summary["total_feature_flags"]
        + summary["total_i18n_keys"]
        + summary["total_startup_tasks"]
    )

    text = args.doc.read_text(encoding="utf-8")
    rows_s4 = extract_table_rows(text, HEADER_S4)
    rows_s5 = extract_table_rows(text, HEADER_S5)
    rows_s6 = extract_table_rows(text, HEADER_S6)
    rows_s7 = extract_table_rows(text, HEADER_S7)
    rows_s8 = extract_table_rows(text, HEADER_S8)

    expected_per_section = {
        "§4 rutas": (summary["total_routes"], len(rows_s4)),
        "§5 atajos": (summary["total_shortcuts"], len(rows_s5)),
        "§6 flags": (summary["total_feature_flags"], len(rows_s6)),
        "§7 i18n keys": (summary["total_i18n_keys"], len(rows_s7)),
        "§8 startup": (summary["total_startup_tasks"], len(rows_s8)),
    }
    rows_total = len(rows_s4) + len(rows_s5) + len(rows_s6) + len(rows_s7) + len(rows_s8)
    all_ok = rows_total == expected_total and all(
        exp == got for exp, got in expected_per_section.values()
    )

    summary_out = {
        "doc": str(args.doc),
        "expected_total": expected_total,
        "rows_total": rows_total,
        "per_section": [
            {"section": k, "expected": exp, "got": got, "ok": exp == got}
            for k, (exp, got) in expected_per_section.items()
        ],
        "ok": all_ok,
    }

    if args.json:
        print(json.dumps(summary_out, indent=2, ensure_ascii=False))
    else:
        for k, (exp, got) in expected_per_section.items():
            print(f"  {k:14s}: {got} filas (esperado {exp}) {'OK' if exp == got else 'FAIL'}")
        print(f"  {'TOTAL':14s}: {rows_total} filas (esperado {expected_total}) {'OK' if all_ok else 'FAIL'}")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())