#!/usr/bin/env python3
"""repair_markdown_damage.py — repara referencias de evidencia a las que una
pasada anterior de `fix_evidence_prefix.py` partió el ``inline code`` y dejó
Markdown inválido.

Origen del daño (hallazgo de la Fase C1)
-----------------------------------------
`fix_evidence_prefix.py` (cerrado en B6) anteponía el prefijo de directorio
**sin saltarse los bloques ```fenced```** y **sin ser idempotente**: si una
referencia ya llevaba el prefijo de fuente, `RE_REF` lo consumía como grupo
`fuente` y reescribía la misma referencia con el prefijo duplicado. Al escribir
dentro de un `` `…` `` ya abierto, el resultado rompe el emparejamiento de
backticks:

    Original   `appflowy/frontend/appflowy_flutter/lib/startup/startup.dart:1`
    Dañado     `appflowy:frontend/`appflowy:`appflowy/frontend/.../startup.dart:1```
                ``appflowy:`appflowy/.../splash_bloc.dart:1```
                (src: appflowy:lib/`appflowy:`appflowy/.../startup.dart:97``-156)

La **referencia válida sí sobrevive intacta** dentro del run (es el prefijo
`<fuente>/` que coincide con `inventario.json::ruta_rel`). Este script la
extracción, se queda con ella y reconstruye el span como un único
``inline code`` de una backtick, que siempre es Markdown válido.

Qué NO hace
-----------
- No toca números de línea.
- No inventa referencias: si un run no contiene ninguna referencia resoluble
  contra el inventario, lo deja intacto y lo reporta.
- No toca ficheros sin run corrupto.

Uso
---
    python3 repair_markdown_damage.py --dry-run OUT/15-secuencias-globales/
    python3 repair_markdown_damage.py --apply OUT/
    python3 repair_markdown_damage.py --apply OUT/ --skip OUT/_ledger
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
INVENTARIO = PROJECT_ROOT / "OUT" / "_ledger" / "inventario.json"

# Referencia válida: prefijo de fuente + ruta con extensión + línea (+ rango).
REF_CORE = (
    r"(?:appflowy|collab|editor)/"
    r"[A-Za-z0-9_][A-Za-z0-9_./\-]*\.[A-Za-z0-9]+"
    r":\d+(?:[–-]\d+)?"
)

# Run corrupto completo. El grupo opcional inicial absorbe el "prefijo
# fantasma" (`appflowy:frontend/`) y el `appflowy:` inyectado que lo precede;
# el resto captura la referencia válida y las backticks sobrantes.
RE_CORRUPT = re.compile(
    r"(?:`+appflowy:[^`\n]*`)?`+appflowy:`+"
    rf"(?P<ref>{REF_CORE})`+"
)

# Run alternativo: doble backtick de apertura con `appflowy:` inyectado dentro
# y rango partido fuera del span (``…:118``-156`).
RE_CORRUPT_ALT = re.compile(
    r"`{2}appflowy:`+(?P<ref>" + REF_CORE + r")`{2}(?P<tail>[–-]\d+)`"
)

# Prefolio fantasma que sobrevive a RE_CORRUPT: el script original antepuso el
# prefijo de directorio (`appflowy:frontend/`) *antes* de reescribir la
# referencia, así que queda un `` `appflowy:frontend/` `` suelto delante de la
# referencia ya válida. El lookahead negativo `(?!(?:collab|editor)/)` protege
# los prefijos de fuente legítimos (`collab:collab/collab/src/lib.rs:1`).
_LA = r"(?=`?" + REF_CORE + r")"
RE_FANTASMA_BT = re.compile(
    r"`appflowy:(?!(?:collab|editor)/)[A-Za-z0-9_./\-]*`" + _LA
)
RE_FANTASMA_NB = re.compile(
    r"appflowy:(?!(?:collab|editor)/)[A-Za-z0-9_./\-]*" + _LA
)


def cargar_inventario() -> set[tuple[str, str]]:
    """Devuelve el conjunto {(fuente, ruta_rel)} del inventario."""
    if not INVENTARIO.exists():
        print(f"repair_markdown_damage: falta {INVENTARIO}", file=sys.stderr)
        raise SystemExit(2)
    data = json.loads(INVENTARIO.read_text(encoding="utf-8"))
    entradas = data["files"] if isinstance(data, dict) and "files" in data else data
    out: set[tuple[str, str]] = set()
    for e in entradas:
        if isinstance(e, dict) and e.get("fuente") and e.get("ruta_rel"):
            out.add((e["fuente"], e["ruta_rel"]))
    return out


def es_resoluble(ref: str, inventario: set[tuple[str, str]]) -> bool:
    """¿La referencia existe en el inventario como (fuente, ruta_rel)?

    Acepta tanto `collab:collab/collab/src/lib.rs:1` como
    `appflowy/frontend/rust-lib/flowy-core/src/lib.rs:61`: el segundo caso
    lleva el nombre de la fuente dentro de la ruta, que es la convención de
    `ruta_rel`.
    """
    cuerpo = ref.rsplit(":", 1)[0]
    cuerpo = re.sub(r"[–-]\d+$", "", cuerpo)
    if ":" in cuerpo:
        fuente, ruta = cuerpo.split(":", 1)
        return (fuente, ruta) in inventario
    for fuente in ("appflowy", "collab", "editor"):
        if (fuente, cuerpo) in inventario:
            return True
    return False


def reparar_texto(
    texto: str, inventario: set[tuple[str, str]]
) -> tuple[str, int, list[str]]:
    """Reparar los runs corruptos. Devuelve (texto, n_reparados, refs_vistas)."""
    refs: list[str] = []
    n = 0

    def sub_alt(m: re.Match) -> str:
        nonlocal n
        ref = m.group("ref")
        if not es_resoluble(ref, inventario):
            return m.group(0)
        n += 1
        refs.append(ref)
        return f"`{ref}{m.group('tail')}`"

    texto = RE_CORRUPT_ALT.sub(sub_alt, texto)

    def sub(m: re.Match) -> str:
        nonlocal n
        ref = m.group("ref")
        if not es_resoluble(ref, inventario):
            return m.group(0)
        n += 1
        refs.append(ref)
        return f"`{ref}`"

    texto = RE_CORRUPT.sub(sub, texto)
    texto = RE_FANTASMA_BT.sub("`", texto)
    texto = RE_FANTASMA_NB.sub("", texto)
    return texto, n, refs


def recolectar(paths: list[str], skip: list[str]) -> list[Path]:
    """Lista de `.md` a procesar.

    `--skip` acepta prefijos relativos al proyecto (`OUT/_ledger`) o absolutos;
    se comparan contra la ruta **relativa al proyecto**, igual que en
    `fix_line_offsets.py` (C1). Sin esta normalización, pasar `OUT/` en absoluto
    desde `validate-C1.sh` hacía que los skips no casaran y el script acababa
    "reparando" también las bitácoras de `_ledger/`.
    """
    raiz = PROJECT_ROOT.resolve()
    out: list[Path] = []
    for p in paths or ["OUT/"]:
        pp = Path(p)
        if pp.is_file():
            out.append(pp)
        elif pp.is_dir():
            out += [
                m
                for m in sorted(pp.rglob("*.md"))
                if not _relativo(m, raiz).startswith(tuple(skip))
            ]
    return out


def _relativo(m: Path, raiz: Path) -> str:
    try:
        return str(m.resolve().relative_to(raiz))
    except ValueError:
        return str(m)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="*", default=["OUT/"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument(
        "--skip",
        nargs="*",
        # Coherente con `validate_evidence.py::META_DOCS` y con
        # `fix_line_offsets.py`: los meta-ficheros no son entregables y
        # `_ledger/` es el cuaderno de trabajo de la skill.
        default=[
            "OUT/_ledger",
            "OUT/STATE.md",
            "OUT/00-INDEX.md",
            "OUT/22-preguntas-abiertas.md",
        ],
    )
    args = ap.parse_args()
    if not args.dry_run and not args.apply:
        ap.error("usa --dry-run o --apply")

    inventario = cargar_inventario()
    total = 0
    tocados = 0
    pendientes = 0
    for doc in recolectar(args.paths, args.skip):
        texto = doc.read_text(encoding="utf-8")
        nuevo, n, _ = reparar_texto(texto, inventario)
        if not n:
            continue
        # Runs que siguen corruptos tras la pasada (sin ref resoluble).
        if "`appflowy:`" in nuevo or re.search(r"appflowy:[^`\n]*`appflowy:`", nuevo):
            pendientes += nuevo.count("`appflowy:`")
        tocados += 1
        total += n
        print(f"  {doc}: {n} run(s) reparado(s)")
        if args.apply:
            doc.write_text(nuevo, encoding="utf-8")

    modo = "APLICADO" if args.apply else "DRY-RUN"
    print(
        f"[{modo}] runs reparados: {total} · ficheros afectados: {tocados} · "
        f"runs sin referencia resoluble (intactos): {pendientes}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())