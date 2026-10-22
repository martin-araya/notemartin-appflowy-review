#!/usr/bin/env python3
"""fix_evidence_prefix.py — normaliza referencias `ruta:línea` a las que les
falta el prefijo de directorio de su fuente.

Motivo (hallazgo del cierre de B6, P5.1): varios documentos de `OUT/` citan
`flowy-user/src/notification.rs:18` o `collab:collab/src/lib.rs:1` en vez de
`appflowy/frontend/rust-lib/flowy-user/src/notification.rs:18` o
`collab:collab/collab/src/lib.rs:1`. `validate_evidence.py` las rechaza con
`E_PATH_NOT_IN_INVENTORY` aunque el fichero exista.

La corrección es **determinista y conservative**: solo reescribe una referencia
cuando existe **exactamente un** fichero del inventario cuyo sufijo sea el
ruta citado. Si hay cero candidatos se deja como está (error real); si hay más
de uno se deja como está y se avisa (ambigüedad: decisión de un humano).

NUNCA toca números de línea: solo antepone el prefijo de directorio.

Dos correcciones aplicadas en la Fase C1 (el script había damaged 98 spans de
`OUT/15-secuencias-globales/` antes de que B6 cerrara):

1. **Salta los bloques ```fenced```**. Reescribir dentro de un diagrama Mermaid
   rompía el emparejamiento de backticks del ``inline code`` que lo rodeaba.
2. **Es idempotente**. Antes, una referencia que ya llevaba el prefijo de fuente
   (`appflowy:frontend/rust-lib/...`) lo consumía como grupo `fuente` y la
   reescribía con el prefijo duplicado (`appflowy:appflowy/frontend/...`).
   Ahora una referencia que ya resuelve se deja intacta.

Daño ya producido y reparado por `repair_markdown_damage.py` (C1).

Uso:
  python3 fix_evidence_prefix.py --dry-run            # solo informe
  python3 fix_evidence_prefix.py --apply OUT/15-secuencias-globales/
  python3 fix_evidence_prefix.py --apply OUT/ --skip OUT/_ledger
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
INVENTARIO = PROJECT_ROOT / "OUT" / "_ledger" / "inventario.json"

# Mismo regex que validate_evidence.py: prefijo de fuente opcional, ruta con
# extensión, y línea (con rango opcional).
RE_REF = re.compile(
    r"(?P<full>(?:(?P<fuente>appflowy|collab|editor):)?"
    r"(?P<ruta>[A-Za-z0-9_][A-Za-z0-9_./\-]*\.[A-Za-z0-9]+)"
    r":(?P<linea>\d+)(?:[–\-](?P<fin>\d+))?)"
)

FUENTES = ("appflowy", "collab", "editor")

LINE_CACHE: dict[str, int] = {}


def fuera_de_fences(texto: str) -> str:
    """Deprecated: se conserva por compatibilidad. Sustituía por espacios las
    líneas dentro de bloques ```fenced```, lo que al escribir el resultado de
    vuelta en disco vaciaba los diagramas. El bucle principal procesa ahora
    línea a línea y salta las líneas del fence sin enmascarar el texto."""


def referencia_valida(
    claves_inv: set[tuple[str, str]], fuente: str | None, ruta: str
) -> bool:
    """Replica el criterio de `validate_evidence.py` para una referencia escrita.

    Es lo que hace el script **idempotente** (C1): si la referencia tal y como
    aparece ya resuelve contra el inventario, no se toca. Antes, el grupo
    `fuente` absorbía un prefijo ya presente y la reescritura lo duplicaba
    (`appflowy:appflowy/frontend/…`), rompiendo el ``inline code`` de 98 spans.
    """
    f = fuente or "appflowy"
    ruta_full = ruta if ruta.startswith(f"{f}/") else f"{f}/{ruta}"
    return (f, ruta_full) in claves_inv


def cargar_rutas() -> dict[str, list[str]]:
    """Devuelve {ruta_relativa: [claves_de_inventario]} indexado por sufijo.

    En realidad devuelve un índice de sufijo -> [(fuente, ruta_completa), …]
    para poder resolver por coincidencia de final de ruta.
    """
    data = json.loads(INVENTARIO.read_text(encoding="utf-8"))
    entradas = data["files"] if isinstance(data, dict) and "files" in data else data
    por_sufijo: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for e in entradas:
        if isinstance(e, dict):
            fuente = e.get("fuente") or e.get("source") or "appflowy"
            ruta = e.get("ruta_rel") or e.get("ruta") or e.get("path") or ""
        else:
            fuente, ruta = str(e).split("/", 1)[0], str(e)
        if not ruta:
            continue
        por_sufijo[ruta].append((fuente, ruta))
    return por_sufijo


def cargar_claves() -> set[tuple[str, str]]:
    """Conjunto {(fuente, ruta_rel)} del inventario, para el chequeo de
    idempotencia de `referencia_valida`."""
    data = json.loads(INVENTARIO.read_text(encoding="utf-8"))
    entradas = data["files"] if isinstance(data, dict) and "files" in data else data
    return {
        (e.get("fuente") or "appflowy", e.get("ruta_rel"))
        for e in entradas
        if isinstance(e, dict) and e.get("ruta_rel")
    }


def candidatos(ruta: str, fuente: str | None, por_sufijo) -> list[tuple[str, str]]:
    """Ficheros del inventario cuya ruta termina en `ruta`.

    Si `ruta` ya está indexada, es la coincidencia exacta y gana.
    """
    exactas = por_sufijo.get(ruta, [])
    if exactas:
        return exactas
    sufijo = "/" + ruta
    out = []
    for k, v in por_sufijo.items():
        if k.endswith(sufijo):
            out.extend(v)
    if fuente:
        out = [c for c in out if c[0] == fuente] or out
    return out


RAIZ = Path(__file__).resolve().parents[2]


def _relativo(m: Path) -> str:
    """Ruta relativa al proyecto: `--skip` no debe depender de si el `PATH` de
    la CLI viene en relativo o en absoluto (C1)."""
    try:
        return str(m.resolve().relative_to(RAIZ))
    except ValueError:
        return str(m)


def recolectar(paths: list[str], skip: list[str]) -> list[Path]:
    out: list[Path] = []
    for p in paths or ["OUT/"]:
        pp = Path(p)
        if pp.is_file():
            out.append(pp)
        elif pp.is_dir():
            out += [
                m
                for m in sorted(pp.rglob("*.md"))
                if not any(_relativo(m).startswith(s) for s in skip)
            ]
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="*", default=["OUT/"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--skip", nargs="*", default=["OUT/_ledger", "OUT/STATE.md", "OUT/00-INDEX.md"])
    args = ap.parse_args()

    if not args.dry_run and not args.apply:
        ap.error("usa --dry-run o --apply")

    por_sufijo = cargar_rutas()
    claves_inv = cargar_claves()
    targets = recolectar(args.paths, args.skip)

    reparados = 0
    ambiguos = 0
    sin_match = 0
    ficheros_tocados = 0
    for doc in sorted(set(targets)):
        texto = doc.read_text(encoding="utf-8")
        cambios: dict[str, str] = {}

        def sub(m: re.Match) -> str:
            nonlocal reparados, ambiguos, sin_match
            ruta, fuente = m.group("ruta"), m.group("fuente")
            cands = candidatos(ruta, fuente, por_sufijo)
            # Ya resuelve o ya lleva la ruta completa del inventario: no tocar.
            if len(cands) == 1 and cands[0][1] == ruta:
                return m.group("full")
            # Idempotencia (C1): si la referencia escrita ya resuelve contra el
            # inventario, no se reescribe.
            if referencia_valida(claves_inv, fuente, ruta):
                return m.group("full")
            if len(cands) == 1:
                f_dest, r_dest = cands[0]
                prefijo_fuente = f"{f_dest}:" if f_dest != "appflowy" else ""
                reparados += 1
                return f"{prefijo_fuente}{r_dest}:{m.group('linea')}" + (
                    f"–{m.group('fin')}" if m.group("fin") else ""
                )
            if len(cands) > 1:
                ambiguos += 1
                return m.group("full")
            sin_match += 1
            return m.group("full")

        # Se procesa línea a línea saltando las que están dentro de un bloque
        # ```fenced``` (C1): enmascararlas y escribir el resultado de vuelta
        # vaciaba los diagramas Mermaid.
        lineas = texto.split("\n")
        nuevo_lineas: list[str] = []
        dentro = False
        for ln in lineas:
            if ln.lstrip().startswith("```"):
                dentro = not dentro
                nuevo_lineas.append(ln)
                continue
            nuevo_lineas.append(ln if dentro else RE_REF.sub(sub, ln))
        nuevo = "\n".join(nuevo_lineas)
        if nuevo != texto:
            ficheros_tocados += 1
            print(f"  {doc}")
            if args.apply:
                doc.write_text(nuevo, encoding="utf-8")

    modo = "APLICADO" if args.apply else "DRY-RUN"
    print(f"[{modo}] referencias normalizadas: {reparados} · "
          f"ambiguas sin tocar: {ambiguos} · sin candidato: {sin_match} · "
          f"ficheros afectados: {ficheros_tocados}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())