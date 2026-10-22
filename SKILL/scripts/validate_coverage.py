#!/usr/bin/env python3
"""validate_coverage.py — cruza el ledger (cobertura.csv) consigo mismo
y reporta % global y por capa, más la lista de archivos sin asignar /
pendientes por capa.

Fase A3.4 de la skill `notemartin-appflowy-review`.
Spec: ROADMAP.md línea 91 y AGENTS.md §1 (métrica: archivos
fuente en estado "verificado", gate de C2).

Uso: validate_coverage.py [opciones]
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
PROJECT_ROOT_DEFAULT = SKILL_DIR.parent
DEFAULT_LEDGER = PROJECT_ROOT_DEFAULT / "OUT" / "_ledger" / "cobertura.csv"

EXPECTED_HEADER = (
    "fuente",
    "ruta",
    "capa",
    "feature_ids",
    "documento",
    "estado",
    "verificado_por",
)
KNOWN_ESTADOS = {"verificado", "pendiente", "sin_asignar"}
UNCLASSIFIED = "__unclassified__"
UNKNOWN_ESTADO = "__unknown_estado__"

RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


# --- Carga del CSV --------------------------------------------------------


def load_ledger(path: Path) -> list[dict]:
    """Carga el CSV. Valida el header. Devuelve lista de filas (dict).

    Lanza SystemExit(2) si el archivo no existe o el header no matchea.
    """
    if not path.exists():
        print(
            f"validate_coverage.py: ledger no encontrado: {path}\n"
            f"  Ejecuta primero SKILL/scripts/init_ledger.py (Fase A1.3).",
            file=sys.stderr,
        )
        sys.exit(2)
    try:
        with path.open(encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if header is None:
                print(
                    f"validate_coverage.py: ledger vacío: {path}",
                    file=sys.stderr,
                )
                sys.exit(2)
            if tuple(header) != EXPECTED_HEADER:
                print(
                    f"validate_coverage.py: E_BAD_CSV: header no matchea\n"
                    f"  esperado: {list(EXPECTED_HEADER)}\n"
                    f"  encontrado: {header}\n"
                    f"  en: {path}",
                    file=sys.stderr,
                )
                sys.exit(2)
            rows = [dict(zip(EXPECTED_HEADER, r)) for r in reader]
    except (OSError, csv.Error) as e:
        print(
            f"validate_coverage.py: E_BAD_CSV: no se pudo leer {path}: {e}",
            file=sys.stderr,
        )
        sys.exit(2)
    return rows


# --- Cómputo de cobertura --------------------------------------------------


def compute_coverage(rows: list[dict]) -> dict:
    """Devuelve {global: {counters, pct}, by_capa: {capa: {counters, pct}}}."""
    by_capa: dict[str, dict] = defaultdict(
        lambda: {"total": 0, "verificado": 0, "pendiente": 0, "sin_asignar": 0, "__other__": 0}
    )
    glob = {"total": 0, "verificado": 0, "pendiente": 0, "sin_asignar": 0, "__other__": 0}

    for r in rows:
        capa = (r.get("capa") or "").strip() or UNCLASSIFIED
        estado = (r.get("estado") or "").strip()
        by_capa[capa]["total"] += 1
        glob["total"] += 1
        if estado in KNOWN_ESTADOS:
            by_capa[capa][estado] += 1
            glob[estado] += 1
        else:
            by_capa[capa]["__other__"] += 1
            glob["__other__"] += 1

    def _pct(d: dict) -> float:
        if d["total"] == 0:
            return 0.0
        return 100.0 * d["verificado"] / d["total"]

    glob["pct"] = _pct(glob)
    for capa, d in by_capa.items():
        d["pct"] = _pct(d)

    return {
        "global": dict(glob),
        "by_capa": dict(by_capa),
    }


def collect_faltantes(rows: list[dict], by_capa: dict, limit: int) -> dict:
    """Para cada capa con pct < 100, recoge las primeras `limit` filas
    en `sin_asignar` y `pendiente` (formato: '<fuente>/<ruta>').
    """
    capas_con_faltantes = {c for c, d in by_capa.items() if d["pct"] < 100.0}
    out: dict = {}
    for r in rows:
        capa = (r.get("capa") or "").strip() or UNCLASSIFIED
        if capa not in capas_con_faltantes:
            continue
        estado = (r.get("estado") or "").strip()
        if estado not in {"sin_asignar", "pendiente"}:
            continue
        bucket = out.setdefault(capa, {"sin_asignar": [], "pendiente": []})
        if len(bucket[estado]) < limit:
            bucket[estado].append(f"{r['fuente']}/{r['ruta']}")
    return out


# --- Salida --------------------------------------------------------------


def c_red(s: str, no_color: bool) -> str:
    return s if no_color else f"{RED}{s}{RESET}"


def c_green(s: str, no_color: bool) -> str:
    return s if no_color else f"{GREEN}{s}{RESET}"


def c_yellow(s: str, no_color: bool) -> str:
    return s if no_color else f"{YELLOW}{s}{RESET}"


def c_bold(s: str, no_color: bool) -> str:
    return s if no_color else f"{BOLD}{s}{RESET}"


def c_dim(s: str, no_color: bool) -> str:
    return s if no_color else f"{DIM}{s}{RESET}"


def fmt_pct(pct: float, no_color: bool) -> str:
    s = f"{pct:.2f}%"
    if pct >= 100.0:
        return c_green(s, no_color)
    if pct >= 50.0:
        return c_yellow(s, no_color)
    return c_red(s, no_color)


def print_table(by_capa: dict, glob: dict, no_color: bool) -> None:
    headers = ("capa", "total", "verificado", "pendiente", "sin_asignar", "%")
    rows = []
    for capa in sorted(by_capa):
        d = by_capa[capa]
        rows.append((
            capa,
            d["total"],
            d["verificado"],
            d["pendiente"],
            d["sin_asignar"],
            fmt_pct(d["pct"], no_color),
        ))
    rows.append((
        c_bold("GLOBAL", no_color),
        c_bold(glob["total"], no_color),
        c_bold(glob["verificado"], no_color),
        c_bold(glob["pendiente"], no_color),
        c_bold(glob["sin_asignar"], no_color),
        c_bold(fmt_pct(glob["pct"], no_color), no_color),
    ))

    widths = [max(len(str(r[i])) for r in [headers, *rows]) for i in range(len(headers))]

    def _fmt_row(r):
        out = []
        for i, cell in enumerate(r):
            if i == 0:
                out.append(str(cell).ljust(widths[i]))
            else:
                out.append(str(cell).rjust(widths[i]))
        return " | ".join(out)

    sep = "-+-".join("-" * w for w in widths)
    print(_fmt_row(headers), file=sys.stdout)
    print(sep, file=sys.stdout)
    for r in rows:
        print(_fmt_row(r), file=sys.stdout)


def print_faltantes(
    faltantes: dict,
    by_capa: dict,
    limit: int,
    no_color: bool,
) -> None:
    if not faltantes:
        print(
            c_green("Sin faltantes: todas las capas tienen 100% verificado.", no_color),
            file=sys.stdout,
        )
        return
    print("", file=sys.stdout)
    print(
        c_bold(f"Faltantes (estado != verificado), top {limit} por capa:", no_color),
        file=sys.stdout,
    )
    for capa in sorted(faltantes):
        d = by_capa[capa]
        pct = fmt_pct(d["pct"], no_color)
        print("", file=sys.stdout)
        print(f"  capa={capa} ({pct}):", file=sys.stdout)
        for estado in ("sin_asignar", "pendiente"):
            items = faltantes[capa].get(estado, [])
            if not items:
                continue
            label = f"  {estado} ({len(items)}"
            if len(items) >= limit and d[estado] > limit:
                label += f" de {d[estado]}"
            label += "):"
            print(c_yellow(label, no_color), file=sys.stdout)
            for it in items:
                print(f"    - {it}", file=sys.stdout)


# --- Main ----------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="validate_coverage.py",
        description=(
            "Cruza el ledger (cobertura.csv) y reporta el % global y por "
            "capa de archivos en estado 'verificado', más listas de "
            "faltantes por capa."
        ),
    )
    parser.add_argument(
        "-l",
        "--ledger",
        type=Path,
        default=DEFAULT_LEDGER,
        help=f"Path a cobertura.csv (default: {DEFAULT_LEDGER})",
    )
    parser.add_argument(
        "-t",
        "--threshold",
        type=float,
        default=100.0,
        help="Porcentaje mínimo de cobertura global para exit 0 (default: 100).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Tamaño máximo de la lista de faltantes por capa (default: 50).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Salida en JSON estructurado a stdout.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Sólo summary final; oculta la tabla Markdown.",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Desactiva códigos ANSI.",
    )
    args = parser.parse_args(argv)

    rows = load_ledger(args.ledger)
    coverage = compute_coverage(rows)
    glob = coverage["global"]
    by_capa = coverage["by_capa"]
    faltantes = collect_faltantes(rows, by_capa, args.limit)

    if args.json:
        out = {
            "schema_version": "1.0",
            "ledger": str(args.ledger),
            "threshold": args.threshold,
            "limit": args.limit,
            "global": {
                "total": glob["total"],
                "verificado": glob["verificado"],
                "pendiente": glob["pendiente"],
                "sin_asignar": glob["sin_asignar"],
                "pct": round(glob["pct"], 4),
            },
            "by_capa": {
                capa: {
                    "total": d["total"],
                    "verificado": d["verificado"],
                    "pendiente": d["pendiente"],
                    "sin_asignar": d["sin_asignar"],
                    "pct": round(d["pct"], 4),
                }
                for capa, d in sorted(by_capa.items())
            },
            "faltantes": faltantes,
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        if not args.quiet:
            print_table(by_capa, glob, args.no_color)
            print_faltantes(faltantes, by_capa, args.limit, args.no_color)
        # Summary
        msg = f"Cobertura global: {glob['pct']:.2f}% (threshold: {args.threshold:.2f}%)"
        if glob["pct"] >= args.threshold:
            print(c_green(msg, args.no_color), file=sys.stdout)
        else:
            print(c_red(msg, args.no_color), file=sys.stdout)

    return 0 if glob["pct"] >= args.threshold else 1


if __name__ == "__main__":
    sys.exit(main())
