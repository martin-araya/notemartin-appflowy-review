#!/usr/bin/env python3
"""validate_evidence.py — encuentra todas las referencias
`[fuente:]ruta:línea[–fin]` en uno o varios `.md` y comprueba, contra
`OUT/_ledger/inventario.json`, que (1) el archivo esté inventariado,
(2) la fuente coincida, (3) la(s) línea(s) exista(n) en el archivo
real, (4) en rangos, `inicio ≤ fin`.

Fase A3.2 de la skill `notemartin-appflowy-review`.
Spec: ROADMAP.md línea 87 y AGENTS.md §6 (reglas 1 y 5).

Prerrequisito: `OUT/_ledger/inventario.json` debe existir
(generado por A1.2 — `SKILL/scripts/inventory.py`).

Uso: validate_evidence.py [opciones] PATH [PATH …]
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import namedtuple
from pathlib import Path
from typing import Iterable

# --- Constantes -------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent  # SKILL/
PROJECT_ROOT_DEFAULT = SKILL_DIR.parent  # notemartin-appflowy-review/
DEFAULT_INVENTARIO = PROJECT_ROOT_DEFAULT / "OUT" / "_ledger" / "inventario.json"

# Fuentes de AppFlowy. No es una lista cerrada: el smoke test de retroalimentacion
# (Fase C7) pasa un inventario de otro repo, cuyo unico prefijo puede ser
# cualquier cosa. `valid_fuentes` se deriva del propio inventario y este conjunto
# solo se usa como lista de sugerencias en el mensaje de error.
VALID_FUENTES = {"appflowy", "collab", "editor"}
DEFAULT_FUENTE = "appflowy"

# Meta-ficheros: no son entregables y sus `ruta:línea` apuntan a documentos
# internos de `OUT/`, no a código fuente. `validate_template.py` ya los excluía
# (su `META_DOCS`); C1 alineó `validate_evidence.py` con el mismo criterio para
# que la pasada global no arrastre falsos positivos (23 en `00-INDEX.md`,
# 48 en `STATE.md`, 1 en `22-preguntas-abiertas.md`).
META_DOCS = {"00-INDEX.md", "22-preguntas-abiertas.md", "STATE.md"}

# Regex principal. Ver plan §3.3 para casos cubiertos / excluidos.
RE_REF = re.compile(
    r"(?:(?P<fuente>appflowy|collab|editor):)?"
    r"(?P<ruta>[A-Za-z0-9_][A-Za-z0-9_./\-]*\.[A-Za-z0-9]+)"
    r":(?P<linea>\d+)"
    r"(?:[–\-](?P<fin>\d+))?"
    r"(?!\d)"
)

# Colores ANSI
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
DIM = "\033[2m"
RESET = "\033[0m"


Ref = namedtuple("Ref", ["doc_line", "text", "fuente", "ruta", "linea", "fin"])


# --- Carga de inventario ---------------------------------------------------


def load_inventario(path: Path) -> dict:
    """Carga inventario.json y devuelve {(fuente, ruta_rel): entry}.

    Lanza SystemExit si el archivo no existe o no parsea.
    """
    if not path.exists():
        print(
            f"validate_evidence.py: inventario no encontrado: {path}\n"
            f"  Ejecuta primero SKILL/scripts/inventory.py (Fase A1.2).",
            file=sys.stderr,
        )
        sys.exit(2)
    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"validate_evidence.py: inventario JSON inválido: {e}", file=sys.stderr)
        sys.exit(2)
    inv = {}
    for entry in data.get("files", []):
        fuente = entry.get("fuente")
        ruta_rel = entry.get("ruta_rel")
        if fuente and ruta_rel:
            inv[(fuente, ruta_rel)] = entry
    return inv


# --- Extracción de referencias ---------------------------------------------


def extract_refs(text: str) -> list[Ref]:
    """Devuelve todas las referencias de evidencia en `text`.

    - Ignora líneas dentro de bloques ```código``` (fenced).
    - Numeración doc_line es 1-based (linea del .md).
    """
    refs: list[Ref] = []
    in_fence = False
    for ln, line in enumerate(text.splitlines(), 1):
        stripped = line.lstrip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for m in RE_REF.finditer(line):
            fuente = m.group("fuente")
            ruta = m.group("ruta")
            linea = int(m.group("linea"))
            fin_str = m.group("fin")
            fin = int(fin_str) if fin_str else None
            # Filtros posteriores al match:
            # 1) una URL tipo https://foo:42 — `https` no es fuente válida,
            #    ya queda fuera por el (?:...)? opcional.
            # 2) Falsos positivos tipo "RFC:4180" — la regex exige un '.'
            #    en la "ruta", ya filtrado.
            # 3) Si la "ruta" es un directorio con sólo dígitos, no es
            #    referencia de código (sin extensión .algo). Filtrado por
            #    \.[A-Za-z0-9]+.
            # 4) "1:2:3" — el (?!\d) final ya excluye concatenaciones.
            refs.append(
                Ref(
                    doc_line=ln,
                    text=m.group(0),
                    fuente=fuente,
                    ruta=ruta,
                    linea=linea,
                    fin=fin,
                )
            )
    return refs


# --- Validación de una referencia -----------------------------------------

ERROR_CODES = {
    "E_PATH_NOT_IN_INVENTORY": "ruta no encontrada en inventario",
    "E_FUENTE_MISMATCH": "fuente no coincide con el prefijo",
    "E_LINE_OUT_OF_RANGE": "línea (o fin de rango) fuera del archivo",
    "E_RANGE_INVERTED": "rango invertido: inicio > fin",
}


def count_lines(path: Path) -> int:
    """Cuenta líneas reales del archivo (no el `loc` del inventario)."""
    try:
        with path.open("rb") as f:
            return sum(1 for _ in f)
    except OSError as e:
        # Si no se puede leer, devolvemos 0; la validación reportará OOR.
        print(f"  (aviso) no se pudo leer {path}: {e}", file=sys.stderr)
        return 0


def validate_ref(
    ref: Ref,
    inv: dict,
    line_cache: dict,
    no_color: bool,
) -> dict | None:
    """Devuelve un dict de error, o None si la referencia es válida.

    El prefijo de fuente se deduce del propio inventario (`inv`), no de una
    lista fija. Antes de la Fase C7 se comparaba contra
    `VALID_FUENTES = {appflowy, collab, editor}` y, si la referencia no llevaba
    prefijo, se asumía `appflowy`. Sobre un repo ajeno eso producía
    `E_PATH_NOT_IN_INVENTORY` para todas las citas, porque el inventario tenía
    `ejemplo/...` y el validador buscaba `appflowy/ejemplo/...`.
    """
    valid_fuentes = {f for (f, _r) in inv} or VALID_FUENTES
    default_fuente = sorted({f for (f, _r) in inv})[0] if inv else DEFAULT_FUENTE
    fuente_raw = ref.fuente
    ruta = ref.ruta
    linea = ref.linea
    fin = ref.fin

    # Prefijo de fuente: si la referencia lo lleva, se respeta siempre. Solo se
    # valida contra la lista de AppFlowy cuando el inventario la contiene, para no
    # rechazar un repo ajeno por usar un prefijo distinto.
    if (fuente_raw is not None and fuente_raw not in VALID_FUENTES
            and valid_fuentes and fuente_raw not in valid_fuentes):
        return {
            "code": "E_FUENTE_MISMATCH",
            "detail": f"fuente desconocida: '{fuente_raw}' "
            f"(esperado: {sorted(valid_fuentes)} o vacío)",
        }

    fuente = fuente_raw or default_fuente
    # Convención del inventario (A1.2): ruta_rel = "<fuente>/<rest>".
    # Las referencias usan la ruta interna (sin el prefijo de fuente),
    # p. ej. "collab:collab-database/src/blocks/block.rs" -> la parte
    # "ruta" es "collab-database/src/blocks/block.rs" y la fuente es
    # "collab". Para hacer lookup, prependemos "<fuente>/" salvo que
    # la ruta ya lo tenga (idempotente).
    if ruta.startswith(f"{fuente}/"):
        ruta_full = ruta
    else:
        ruta_full = f"{fuente}/{ruta}"
    key = (fuente, ruta_full)

    if key not in inv:
        return {
            "code": "E_PATH_NOT_IN_INVENTORY",
            "detail": (
                f"no existe en inventario como "
                f"({fuente!r}, {ruta_full!r}) ({len(inv)} entradas)"
            ),
        }

    # Validar rango invertido antes de contar líneas (atajo)
    if fin is not None and fin < linea:
        return {
            "code": "E_RANGE_INVERTED",
            "detail": f"inicio {linea} > fin {fin}",
        }

    # Validar líneas contra el archivo real
    abs_path_str = inv[key].get("ruta_abs")
    if not abs_path_str:
        return {
            "code": "E_PATH_NOT_IN_INVENTORY",
            "detail": "entrada de inventario sin ruta_abs",
        }
    abs_path = Path(abs_path_str)
    if abs_path_str not in line_cache:
        line_cache[abs_path_str] = count_lines(abs_path)
    total = line_cache[abs_path_str]

    if linea < 1 or linea > total:
        return {
            "code": "E_LINE_OUT_OF_RANGE",
            "detail": f"línea {linea} fuera de rango (archivo tiene {total} líneas)",
        }
    if fin is not None and fin > total:
        return {
            "code": "E_LINE_OUT_OF_RANGE",
            "detail": f"fin {fin} fuera de rango (archivo tiene {total} líneas)",
        }
    return None


# --- Recolección de archivos ----------------------------------------------


def collect_md_files(
    paths: list[Path], incluir_meta: bool = False, incluir_ledger: bool = False
) -> list[Path]:
    """Devuelve la lista de .md a procesar (recursivo si es dir).

    Por defecto excluye los meta-ficheros (`META_DOCS`) y `_ledger/` (el cuaderno
    de trabajo de la skill), igual que `validate_template.py`. Con
    `--incluir-meta` / `--incluir-ledger` se pasan todos.
    """
    out: list[Path] = []
    skip_dirs = {".git", "node_modules", "_wip", "fixtures"}
    if not incluir_ledger:
        skip_dirs = skip_dirs | {"_ledger"}
    for p in paths:
        if p.is_file():
            if p.suffix == ".md":
                out.append(p)
            continue
        if p.is_dir():
            for root, dirs, files in os.walk(p):
                dirs[:] = [d for d in dirs if d not in skip_dirs]
                for name in sorted(files):
                    if not name.endswith(".md"):
                        continue
                    if not incluir_meta and name in META_DOCS:
                        continue
                    out.append(Path(root) / name)
    return sorted(out)


# --- Salida ----------------------------------------------------------------


def c_red(s: str, no_color: bool) -> str:
    return s if no_color else f"{RED}{s}{RESET}"


def c_green(s: str, no_color: bool) -> str:
    return s if no_color else f"{GREEN}{s}{RESET}"


def c_dim(s: str, no_color: bool) -> str:
    return s if no_color else f"{DIM}{s}{RESET}"


def print_error(
    doc: Path, ref_index: int, ref: Ref, err: dict, no_color: bool
) -> None:
    print(
        f"{c_red('ERROR', no_color)} {doc}:{ref_index}: "
        f"{err['code']}: {err['detail']}\n"
        f"    ref: {ref.text} (línea {ref.doc_line} del doc)",
        file=sys.stderr,
    )


# --- Main ------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="validate_evidence.py",
        description=(
            "Encuentra referencias [fuente:]ruta:línea[–fin] en .md y "
            "comprueba que existan en inventario.json y dentro de rango."
        ),
    )
    parser.add_argument(
        "paths",
        nargs="+",
        type=Path,
        help="Archivos .md o directorios (recursivo).",
    )
    parser.add_argument(
        "-i",
        "--inventario",
        type=Path,
        default=DEFAULT_INVENTARIO,
        help=f"Path a inventario.json (default: {DEFAULT_INVENTARIO})",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Salida en JSON estructurado a stdout.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Sólo summary final; oculta líneas por archivo.",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Desactiva códigos ANSI.",
    )
    parser.add_argument(
        "--incluir-meta",
        action="store_true",
        help=(
            "Valida también los meta-ficheros "
            f"({sorted(META_DOCS)}); sus `ruta:línea` apuntan a documentos "
            "internos de OUT/, no a código fuente."
        ),
    )
    parser.add_argument(
        "--incluir-ledger",
        action="store_true",
        help="Valida también OUT/_ledger/ (bitácoras de prueba, no entregables).",
    )
    args = parser.parse_args(argv)

    inv = load_inventario(args.inventario)
    files = collect_md_files(args.paths, args.incluir_meta, args.incluir_ledger)
    if not files:
        print(
            f"validate_evidence.py: no se encontraron .md en {args.paths}",
            file=sys.stderr,
        )
        return 2

    line_cache: dict[str, int] = {}
    summary = {"files": 0, "references": 0, "ok": 0, "errors": 0}
    errors_out: list[dict] = []

    for md in files:
        try:
            text = md.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            print(f"  (aviso) no se pudo leer {md}: {e}", file=sys.stderr)
            continue
        refs = extract_refs(text)
        file_ok = 0
        file_err = 0
        for i, ref in enumerate(refs, 1):
            summary["references"] += 1
            err = validate_ref(ref, inv, line_cache, args.no_color)
            if err is None:
                summary["ok"] += 1
                file_ok += 1
            else:
                summary["errors"] += 1
                file_err += 1
                errors_out.append(
                    {
                        "doc": str(md),
                        "ref_index": i,
                        "doc_line": ref.doc_line,
                        "ref": ref.text,
                        "code": err["code"],
                        "detail": err["detail"],
                    }
                )
                if not args.json:
                    print_error(md, i, ref, err, args.no_color)
        summary["files"] += 1
        if not args.quiet and not args.json:
            if file_err:
                print(
                    f"{md}: {len(refs)} refs "
                    f"({c_green(f'{file_ok} OK', args.no_color)} / "
                    f"{c_red(f'{file_err} FAIL', args.no_color)})",
                    file=sys.stderr,
                )
            else:
                print(
                    f"{md}: {len(refs)} refs "
                    f"({c_green(f'{file_ok} OK', args.no_color)})",
                    file=sys.stderr,
                )

    if args.json:
        out = {"summary": summary, "errors": errors_out, "schema_version": "1.0"}
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        trailer = (
            f"--- summary: refs={summary['references']} "
            f"ok={summary['ok']} errors={summary['errors']} ---"
        )
        print(trailer, file=sys.stderr)

    return 1 if summary["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
