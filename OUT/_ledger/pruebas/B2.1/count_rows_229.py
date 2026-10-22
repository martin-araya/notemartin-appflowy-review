#!/usr/bin/env python3
"""count_rows_229.py — cuenta las filas de variantes en
`OUT/11-catalogo-eventos-ffi.md` y comprueba que sean exactamente 229
(= `events.json::summary.total_variants`), como exige el ROADMAP.

Prerrequisito: el documento ya fue generado por `build_catalog_events.py`.

Estrategia de conteo:
  - §4 índice global: tabla con encabezado `| Crate | # | Evento | …`.
  - §5.<crate>: 8 tablas con encabezado `| # | Evento | …`.
  - §6 sin_handler: tabla con encabezado `| Crate | Evento | …`.

Cada variante del catálogo aparece exactamente 2 veces (una en §4, una
en §5). La prueba exige contar las filas de §5 (sumadas) y comprobar
= 229. Las filas de §4 deben ser también 229. §6 son 5.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent.parent
DEFAULT_DOC = PROJECT_ROOT / "OUT" / "11-catalogo-eventos-ffi.md"
DEFAULT_EVENTS = PROJECT_ROOT / "OUT" / "_ledger" / "extract" / "events.json"

RE_ROW = re.compile(r"^\| .+\|.+\|$")

# Encabezados de tablas que SÍ cuentan como filas de variantes.
# §4: "| Crate | # | Evento | Input PB | Output PB | Handler | Semántica |"
# §5.*: "| # | Evento | Input PB | Output PB | Handler | Archivo handler | Semántica |"
HEADER_S4 = "| Crate | # | Evento | Input PB | Output PB | Handler | Semántica |"
HEADER_S5 = "| # | Evento | Input PB | Output PB | Handler | Archivo handler | Semántica |"


def extract_table_rows(text: str, header: str) -> list[str]:
    """Devuelve filas que siguen al header `header` hasta el siguiente
    header (de tabla) o fin de §. Ignora filas dentro de bloques
    fenced.
    """
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
        # En tabla. Una fila de tabla inicia con `|` y no es el separador `|---|`.
        if not line.startswith("|"):
            in_table = False
            continue
        if re.match(r"^\|\s*-+", line):
            continue
        rows.append(line)
    return rows


def extract_s6_sin_handler_rows(text: str) -> list[str]:
    header = "| Crate | Evento | # | Source line | Estado |"
    return extract_table_rows(text, header)


def count_section_5(text: str) -> int:
    """Cuenta todas las filas de variantes en §5.* (sumadas)."""
    pattern = re.compile(r"^### 5\.\d+\s+", re.M)
    starts = [m.start() for m in pattern.finditer(text)]
    total = 0
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(text)
        section_text = text[start:end]
        total += len(extract_table_rows(section_text, HEADER_S5))
    return total


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="count_rows_229.py")
    p.add_argument("--doc", type=Path, default=DEFAULT_DOC)
    p.add_argument("--events", type=Path, default=DEFAULT_EVENTS)
    p.add_argument("--expected", type=int, default=None,
                   help="Override del valor esperado (default: events.json).")
    p.add_argument("--quiet", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args(argv)

    if not args.doc.exists():
        print(f"count_rows_229.py: doc no encontrado: {args.doc}", file=sys.stderr)
        return 2
    if not args.events.exists():
        print(f"count_rows_229.py: events.json no encontrado: {args.events}", file=sys.stderr)
        return 2

    events = json.loads(args.events.read_text(encoding="utf-8"))
    expected = args.expected if args.expected is not None else events["summary"]["total_variants"]

    text = args.doc.read_text(encoding="utf-8")
    rows_s4 = extract_table_rows(text, HEADER_S4)
    rows_s5_total = count_section_5(text)
    rows_s6 = extract_s6_sin_handler_rows(text)

    ok_s4 = len(rows_s4) == expected
    ok_s5 = rows_s5_total == expected
    expected_s6 = events["summary"]["total_sin_handler"]
    ok_s6 = len(rows_s6) == expected_s6

    summary = {
        "doc": str(args.doc),
        "expected_total": expected,
        "rows_section_4": len(rows_s4),
        "rows_section_5_total": rows_s5_total,
        "expected_sin_handler": expected_s6,
        "rows_section_6_sin_handler": len(rows_s6),
        "ok": ok_s4 and ok_s5 and ok_s6,
    }

    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print(f"  §4 índice global        : {len(rows_s4)} filas (esperado {expected}) {'OK' if ok_s4 else 'FAIL'}")
        print(f"  §5.* suma               : {rows_s5_total} filas (esperado {expected}) {'OK' if ok_s5 else 'FAIL'}")
        print(f"  §6 sin handler          : {len(rows_s6)} filas (esperado {expected_s6}) {'OK' if ok_s6 else 'FAIL'}")

    return 0 if summary["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())