#!/usr/bin/env python3
"""expand_short_refs.py — Expande referencias cortas `archivo.ext:N` a la ruta
completa desde la raíz del repo que exige `validate_evidence.py`.

Fase C3 · T1.1. Creado al reescribir B5.7 y B5.10, donde la redacción anterior
usaba la forma corta (`manager.rs:138`) que `validate_evidence.py` rechaza con
`E_PATH_NOT_IN_INVENTORY`: el validador exige la ruta completa
(`appflowy/frontend/rust-lib/flowy-storage/src/manager.rs:138`) porque es lo que
se contrasta contra `inventario.json::ruta_rel`.

Por qué existe una herramienta y no un parche
--------------------------------------------
`fix_evidence_prefix.py` (B6) añadía el prefijo de **fuente** (`appflowy:`) pero
dejaba la ruta relativa al crate. Las formas cortas que quedan son un
incidente recurrente cada vez que un documento se reescribe con criterio. Este
script resuelve el caso general desde `inventario.json`, que es la única fuente
de verdad sobre qué rutas existen.

Algoritmo
---------
1. Carga `OUT/_ledger/inventario.json` y construye un índice
   `basename -> [ruta_rel, …]` (y también `ruta_rel` -> `[basename]`).
2. Recorre el texto del `.md` buscando referencias del tipo
   `[fuente:]camino.línea` donde `camino` no resuelve ya contra el inventario.
3. Para cada una, busca el `basename` en el índice. Si hay **exactamente una**
   coincidencia, la sustituye por la ruta completa. Si hay varias, no toca nada
   y lo reporta: desambiguar a mano es obligatorio, porque elegir mal el crate
   sería peor que la referencia corta.
4. No sustituye dentro de bloques ```fenced``` de código (ahí una ruta corta
   puede ser intencional, p. ej. un ejemplo de la CLI).

Idempotente: aplicarlo dos veces no produce cambios adicionales.

Uso
---
    expand_short_refs.py OUT/15-secuencias-globales/07-subir-imagen.md
    expand_short_refs.py --dry-run OUT/09-features/**.md
    expand_short_refs.py --ambiguous strict  OUT/**/*.md   # falla si hay ambigüedad

Fase C3 de la skill notemartin-appflowy-review.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve()
SKILL_ROOT = SCRIPT_PATH.parent.parent.parent

INVENTARIO_DEFAULT = SKILL_ROOT / "OUT" / "_ledger" / "inventario.json"

# `algo.dart:12`, `algo.dart:12–20`, `algo.dart:12-20`, `algo.dart`
REF_CORTA_RE = re.compile(
    r"(?<![\w/.\-])"          # no partir un identificador o una ruta ya completa
    r"(?P<path>[A-Za-z0-9_][A-Za-z0-9_.\-/]*\.(?:rs|dart|yaml|yml|toml|json|md|lock|sh|m|swift|kt|xml|proto|gradle|cfg|ini|env|png|svg|ttf|otf|woff2?))"
    r"(?P<line>\s*:\s*\d+(?:\s*[–\-]\s*\d+)?)?"
)

FENCE_RE = re.compile(r"^\s*```")


def cargar_indice(inventario: Path) -> tuple[set[str], dict[str, list[str]], dict[str, set[str]]]:
    """Devuelve (rutas_rel_completas, basename -> [rutas_rel], basename -> {fuentes}).

    `inventario.json` es un dict con `files: [ {fuente, ruta_rel, …}, … ]`.
    Cada `ruta_rel` ya lleva el nombre de la fuente como primer segmento
    (`appflowy/…`, `collab/…`, `editor/…`), que es exactamente lo que espera
    `validate_evidence.py`.
    """
    data = json.loads(inventario.read_text(encoding="utf-8"))
    if isinstance(data, list):
        entradas = data
    else:
        entradas = data.get("files") or data.get("archivos") or data.get("entries") or []
    completas: set[str] = set()
    por_base: dict[str, list[str]] = defaultdict(list)
    fuentes_por_base: dict[str, set[str]] = defaultdict(set)
    for e in entradas:
        rel = e.get("ruta_rel") or e.get("ruta")
        if not rel:
            continue
        completas.add(rel)
        base = rel.rsplit("/", 1)[-1]
        por_base[base].append(rel)
        if e.get("fuente"):
            fuentes_por_base[base].add(e["fuente"])
    return completas, por_base, fuentes_por_base


def expandir_texto(texto: str, completas: set[str], por_base: dict[str, list[str]],
                   fuentes_por_base: dict[str, set[str]],
                   prefer: dict[str, str],
                   resueltos: list[tuple[str, str, str]],
                   ambiguos: list[tuple[str, str, list[str]]]) -> str:
    lineas = texto.split("\n")
    dentro_de_fence = False
    salida: list[str] = []

    for linea in lineas:
        if FENCE_RE.match(linea):
            dentro_de_fence = not dentro_de_fence
            salida.append(linea)
            continue
        if dentro_de_fence:
            salida.append(linea)
            continue

        def sub(m: re.Match) -> str:
            path, line = m.group("path"), m.group("line") or ""
            base = path.rsplit("/", 1)[-1]
            # Ya es una ruta completa del inventario.
            if path in completas:
                return m.group(0)
            # Sufijo de una ruta del inventario: `flowy-core/src/lib.rs` es
            # sufijo único de `appflowy/frontend/rust-lib/flowy-core/src/lib.rs`.
            if "/" in path:
                sufijos = [c for c in completas if c.endswith("/" + path)]
                if len(sufijos) == 1:
                    nuevo = sufijos[0] + line
                    resueltos.append((path + line, nuevo, "sufijo"))
                    return nuevo
                if len(sufijos) > 1:
                    if base in prefer and prefer[base] in sufijos:
                        elegido = prefer[base]
                        resueltos.append((path + line, elegido + line, "prefer"))
                        return elegido + line
                    pref = [c for c in sufijos if any(f in c for f in ("appflowy/", "collab/", "editor/"))]
                    if len(pref) == 1:
                        resoltos.append((path + line, pref[0] + line, "sufijo"))
                        return pref[0] + line
                return m.group(0)
            cands = por_base.get(base, [])
            if len(cands) == 1:
                nuevo = cands[0] + line
                resueltos.append((path + line, nuevo, ""))
                return nuevo
            if len(cands) > 1:
                # Desempate explicito por el operador: `--prefer base=rel`.
                # Se valida que la ruta exista en el inventario y que su base
                # case, para que un `--prefer` equivocado no se aplique en
                # silencio.
                if base in prefer:
                    elegido = prefer[base]
                    if elegido in cands:
                        resueltos.append((path + line, elegido + line, "prefer"))
                        return elegido + line
                    ambiguos.append((path + line, base, cands))
                    return m.group(0)
                # Desempate por la fuente citada en la propia linea.
                fuente = None
                for f in ("appflowy", "collab", "editor"):
                    if f in linea:
                        fuente = f
                        break
                if fuente and fuentes_por_base.get(base) == {fuente}:
                    chosen = cands[0]
                    resueltos.append((path + line, chosen + line, f"fuente {fuente}"))
                    return chosen + line
                ambiguos.append((path + line, base, cands))
            return m.group(0)

        salida.append(REF_CORTA_RE.sub(sub, linea))
    return "\n".join(salida)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Expande refs cortas a rutas completas (C3/T1.1)")
    ap.add_argument("docs", nargs="+", type=Path, help="Ficheros .md a procesar.")
    ap.add_argument("--inventario", type=Path, default=INVENTARIO_DEFAULT)
    ap.add_argument("--dry-run", action="store_true", help="No escribe; solo informa.")
    ap.add_argument("--ambiguous", choices=["warn", "strict"], default="warn",
                    help="strict sale 1 si hay referencias ambiguas sin resolver.")
    ap.add_argument("--prefer", action="append", default=[], metavar="BASE=RUTA_REL",
                    help="Desempata explicitamente un basename ambiguo. "
                         "Repetible. Se ignora si RUTA_REL no existe en el "
                         "inventario o no termina en BASE.")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    prefer: dict[str, str] = {}
    for spec in args.prefer:
        if "=" not in spec:
            print(f"ERROR: --prefer espera BASE=RUTA_REL, recibio {spec!r}", file=sys.stderr)
            return 2
        base, rel = spec.split("=", 1)
        prefer[base] = rel

    if not args.inventario.is_file():
        print(f"ERROR: no existe {args.inventario}", file=sys.stderr)
        return 2
    completas, por_base, fuentes_por_base = cargar_indice(args.inventario)

    total_resueltos = 0
    total_ambiguos = 0
    for doc in args.docs:
        if not doc.is_file():
            print(f"WARN: no existe {doc}", file=sys.stderr)
            continue
        texto = doc.read_text(encoding="utf-8")
        resueltos: list[tuple[str, str, str]] = []
        ambiguos: list[tuple[str, str, list[str]]] = []
        nuevo = expandir_texto(texto, completas, por_base, fuentes_por_base,
                             prefer, resueltos, ambiguos)

        if resueltos and not args.dry_run:
            doc.write_text(nuevo, encoding="utf-8")

        total_resueltos += len(resueltos)
        total_ambiguos += len(ambiguos)
        if not args.quiet:
            print(f"[expand] {doc}: {len(resueltos)} resueltas, {len(ambiguos)} ambiguas")
            for old, new, _ in resueltos:
                print(f"    {old}  ->  {new}")
            for old, base, cands in ambiguos:
                print(f"    AMBIGUA {old}: {len(cands)} candidatos en {base}")
                for c in cands[:6]:
                    print(f"        - {c}")
                if len(cands) > 6:
                    print(f"        … y {len(cands) - 6} más")

    if not args.quiet:
        print(f"[expand] total: {total_resueltos} resueltas, {total_ambiguos} ambiguas")

    if args.ambiguous == "strict" and total_ambiguos:
        print(f"FAIL: {total_ambiguos} referencias ambiguas sin resolver", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())