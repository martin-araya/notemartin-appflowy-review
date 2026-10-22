#!/usr/bin/env python3
"""count_rows_70.py — cuenta las filas de variantes en
`OUT/14-catalogo-notificaciones.md` y comprueba que sean exactamente 70
(= suma de variantes en los 6 enums), como exige el ROADMAP.

Prerrequisito: el documento ya fue generado por
`build_catalog_notifications.py`.

Estrategia de conteo:
  - §4 índice global: tabla con encabezado `| Enum | # | Variante | …`.
  - §5.<enum>: 6 tablas con encabezado `| # | Variante | …`.
  - §6 sin uso: tabla con encabezado `| # | Enum | Variante | …`.

Cada variante aparece exactamente 2 veces (una en §4, una en §5). §6 son
las variantes con `status ∈ {unused, emitted_only}` (47 unused + 2
emitted_only = 49).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent.parent
DEFAULT_DOC = PROJECT_ROOT / "OUT" / "14-catalogo-notificaciones.md"
DEFAULT_NOTIF = PROJECT_ROOT / "OUT" / "_ledger" / "extract" / "notifications.json"

HEADER_S4 = "| Enum | # | Variante | Índice | Default | Status | Emisor (Rust) | Listener Dart | Efecto UI |"
HEADER_S5 = "| # | Variante | Índice | Default | Status | Emisor (Rust) | Listener Dart | Archivo variante | Efecto UI |"
HEADER_S6 = "| # | Enum | Variante | Status | Archivo |"


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


def count_section_5(text: str) -> int:
    pattern = re.compile(r"^### 5\.\d+\s+", re.M)
    starts = [m.start() for m in pattern.finditer(text)]
    total = 0
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(text)
        section_text = text[start:end]
        total += len(extract_table_rows(section_text, HEADER_S5))
    return total


def count_sin_uso(notif: dict) -> int:
    n = 0
    for enum_obj in notif["rust_notifications"]:
        vu = enum_obj.get("variant_usage", {})
        for st in vu.values():
            if st.get("status") in ("unused", "emitted_only"):
                n += 1
    return n


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="count_rows_70.py")
    p.add_argument("--doc", type=Path, default=DEFAULT_DOC)
    p.add_argument("--notif", type=Path, default=DEFAULT_NOTIF)
    p.add_argument("--quiet", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    if not args.doc.exists():
        print(f"count_rows_70.py: doc no encontrado: {args.doc}", file=sys.stderr)
        return 2
    if not args.notif.exists():
        print(f"count_rows_70.py: notifications.json no encontrado: {args.notif}", file=sys.stderr)
        return 2

    notif = json.loads(args.notif.read_text(encoding="utf-8"))
    expected = sum(len(e["variants"]) for e in notif["rust_notifications"])
    expected_sin_uso = count_sin_uso(notif)

    text = args.doc.read_text(encoding="utf-8")
    rows_s4 = extract_table_rows(text, HEADER_S4)
    rows_s5_total = count_section_5(text)
    rows_s6 = extract_table_rows(text, HEADER_S6)

    ok_s4 = len(rows_s4) == expected
    ok_s5 = rows_s5_total == expected
    ok_s6 = len(rows_s6) == expected_sin_uso

    summary = {
        "doc": str(args.doc),
        "expected_total": expected,
        "rows_section_4": len(rows_s4),
        "rows_section_5_total": rows_s5_total,
        "expected_sin_uso": expected_sin_uso,
        "rows_section_6_sin_uso": len(rows_s6),
        "ok": ok_s4 and ok_s5 and ok_s6,
    }

    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print(f"  §4 índice global        : {len(rows_s4)} filas (esperado {expected}) {'OK' if ok_s4 else 'FAIL'}")
        print(f"  §5.* suma               : {rows_s5_total} filas (esperado {expected}) {'OK' if ok_s5 else 'FAIL'}")
        print(f"  §6 sin uso en Dart      : {len(rows_s6)} filas (esperado {expected_sin_uso}) {'OK' if ok_s6 else 'FAIL'}")

    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())