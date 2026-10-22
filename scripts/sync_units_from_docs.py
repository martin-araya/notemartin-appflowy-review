#!/usr/bin/env python3
"""sync_units_from_docs.py — reconstruye `archivos` de cada unidad a partir
del frontmatter `archivos_cubiertos` de su documento.

Por que
-------
Las unidades se generan desde las filas **pendientes** del ledger, asi que una
feature cerrada (F01, F03..F07) solo se mantiene mediante reparaciones
manuales. En la Fase 0 del cierre del Bloque B3 un `restore_unit_files.py`
demasiado agresivo metio las 798 filas de F01 dentro de F01.0.1 y F01.0.2 a
la vez. El documento, en cambio, si sabe exactamente que cubre: su
frontmatter `archivos_cubiertos` es la lista canonica.

Este script usa el documento como fuente de verdad de la unidad y deja el
invariante `suma(archivos_total) == filas asignadas` en verde otra vez.

Uso:
  python3 sync_units_from_docs.py            # aplica
  python3 sync_units_from_docs.py --dry-run
  python3 sync_units_from_docs.py --unit F01.0.1   # solo una
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT = PROJECT_ROOT / "OUT"
UNITS = OUT / "_ledger" / "units"
LEDGER = OUT / "_ledger" / "cobertura.csv"

_ITEM = re.compile(r"^\s*-\s+(\S+)\s*$")


def parse_frontmatter(path: Path) -> dict[str, list[str] | str]:
    """Extrae `archivos_cubiertos` (lista YAML simple) del frontmatter.

    No usa PyYAML (el proyecto es Python 3 stdlib puro): los items de la
    lista son lineas `  - ruta` y los comentarios `  # ...` se ignoran."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    block = text[3:end]
    out: dict[str, list[str] | str] = {}
    key = None
    for line in block.splitlines():
        m = _ITEM.match(line)
        if m and key == "archivos_cubiertos":
            out.setdefault("archivos_cubiertos", []).append(m.group(1))  # type: ignore[union-attr]
            continue
        if line.lstrip().startswith("#"):
            continue
        m2 = re.match(r"^([a-z_]+):\s*(.*)$", line)
        if m2:
            key = m2.group(1)
            val = m2.group(2).strip()
            if val.startswith("[") and val.endswith("]"):
                # Lista YAML en linea: `archivos_cubiertos: [a, b, c]`
                inner = val[1:-1].strip()
                items = [x.strip().strip("'\"") for x in inner.split(",")] if inner else []
                out[key] = items
            else:
                out[key] = val if val else []
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--unit", default="", help="restringir a una unidad")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-orphan-fix", action="store_true",
                    help="no reasignar a la unidad mas cercana las filas "
                         "asignadas que ningun documento reclama")
    args = ap.parse_args()

    rows = list(csv.DictReader(LEDGER.open(encoding="utf-8", newline="")))
    by_ruta: dict[str, dict] = {r["ruta"]: r for r in rows}

    # Propiedad previa de cada ruta (antes de este sync). Se usa para
    # desempatar: algunos documentos- indice listan en su frontmatter ficheros
    # que el documento de la sub-unidad tambien reclama (p. ej. el indice
    # F01.0 cita los 555 ficheros que sus 7 sub-documentos reparten). El
    # criterio es "no mover lo que ya estaba bien".
    previo: dict[str, str] = {}
    for path in sorted(UNITS.glob("[!_]*.json")):
        u = json.loads(path.read_text(encoding="utf-8"))
        if u.get("id") and not u["id"].startswith("B"):
            for a in u.get("archivos", []):
                previo.setdefault(a["ruta"], u["id"])

    changed: list[tuple[str, int, int]] = []
    missing: list[tuple[str, str]] = []
    # Collect first, resolve conflicts, then write: writing while collecting
    # made the outcome depend on directory order.
    propuestas: dict[str, list[dict]] = {}
    documentos: dict[str, str] = {}
    for path in sorted(UNITS.glob("[!_]*.json")):
        unit = json.loads(path.read_text(encoding="utf-8"))
        uid = unit.get("id", "")
        if uid.startswith("B"):
            continue
        if args.unit and uid != args.unit:
            continue
        doc_rel = unit.get("documento")
        if not doc_rel:
            continue
        doc_path = PROJECT_ROOT / doc_rel
        tiene_doc = doc_path.is_file()
        if not tiene_doc:
            missing.append((uid, doc_rel))
            antes = len(unit.get("archivos", []))
            # Sin documento la unidad conserva lo que le dio `build_units.py`
            # (filas pendientes), salvo que no tenga ninguna: entonces esta
            # obsoleta (caso F02.0 con 539 rutas de sus sub-unidades).
            unit["__nuevo__"] = list(unit.get("archivos", [])) if antes else []
            unit["__antes__"] = antes
            unit["__doc__"] = False
            propuestas[uid] = unit
            continue
        fm = parse_frontmatter(doc_path)
        covered = fm.get("archivos_cubiertos") or []
        if isinstance(covered, str):
            print(f"  [frontmatter invalido] {uid}: archivos_cubiertos no es lista")
            covered = []
        # Un documento que existe pero no declara `archivos_cubiertos` es un
        # indice (0 archivos por definicion). Se le vacia la lista para que no
        # conserve una lista obsoleta.
        antes = len(unit.get("archivos", []))
        propuestas[uid] = unit
        documentos[uid] = doc_rel
        unit["__doc__"] = True
        nuevos = []
        for ruta in covered:
            row = by_ruta.get(ruta)
            if row is None:
                # Los documentos cita rutas como `fuente:ruta` o `SRC/fuente/ruta`
                # (ver AGENTS.md §6). Se normaliza contra el ledger, que usa
                # siempre `fuente/ruta/...` sin prefijo `SRC/`.
                cand = ruta.split(":", 1)[-1]
                cand = cand[len("SRC/"):] if cand.startswith("SRC/") else cand
                row = by_ruta.get(cand)
            if row is None or row["feature_ids"] != unit["feature_id"]:
                continue
            nuevos.append({
                "fuente": row["fuente"],
                "ruta": row["ruta"],
                "capa": row["capa"],
                "estado": row["estado"],
            })
        unit["__nuevo__"] = nuevos
        unit["__antes__"] = antes

    # --- resolver conflictos de propiedad --------------------------------
    # Doc de cada ruta-> unidades cuyo frontmatter la lista.
    doc_de: dict[str, list[str]] = {}
    for uid, unit in propuestas.items():
        if not unit.get("__doc__"):
            continue
        for a in unit["__nuevo__"]:
            doc_de.setdefault(a["ruta"], []).append(uid)

    # Regla de conservacion: una unidad no pierde un fichero que ya poseia si
    # ningun otro documento lo reclama. Sin ella el sync alternaba entre
    # "27 -> 22 -> +5 -> 27" en cada ejecucion (F01.6.1 lista 22 de los 27
    # ficheros que cubre en §12) y nunca convergia.
    for uid, unit in propuestas.items():
        if not unit.get("__doc__"):
            continue
        actuales = {a["ruta"] for a in unit.get("archivos", [])}
        extras = [
            a for a in unit.get("archivos", [])
            if a["ruta"] not in doc_de and a["ruta"] in actuales
        ]
        rutas_doc = {a["ruta"] for a in unit["__nuevo__"]}
        for a in extras:
            if a["ruta"] not in rutas_doc:
                unit["__nuevo__"].append(a)

    reclamadas: dict[str, list[str]] = {}
    for uid, unit in propuestas.items():
        for a in unit["__nuevo__"]:
            reclamadas.setdefault(a["ruta"], []).append(uid)
    conflictos = 0
    for ruta, uids in reclamadas.items():
        if len(uids) == 1:
            continue
        conflictos += 1
        # Precedencia, de mayor a menor:
        #   1. unidad con documento (su `archivos_cubiertos` es la cobertura
        #      declarada y ya aprobada por el revisor);
        #   2. unidad no-indice mas especifica;
        #   3. propietario previo (no mover lo que ya estaba bien).
        con_doc = [u for u in uids if propuestas[u].get("__doc__")]
        candidatas = con_doc or uids
        especificas = [u for u in candidatas
                       if not re.fullmatch(r"F\d+\.0", u)]
        candidatas = especificas or candidatas
        dueño = previo.get(ruta)
        if dueño not in candidatas:
            dueño = sorted(candidatas)[0]
        for uid in uids:
            if uid != dueño:
                propuestas[uid]["__nuevo__"] = [
                    a for a in propuestas[uid]["__nuevo__"] if a["ruta"] != ruta
                ]

    for uid, unit in propuestas.items():
        nuevos = unit.pop("__nuevo__")
        antes = unit.pop("__antes__")
        unit.pop("__doc__", None)
        if antes == len(nuevos):
            continue
        changed.append((uid, antes, len(nuevos)))
        if args.dry_run:
            continue
        unit["archivos"] = sorted(nuevos, key=lambda a: a["ruta"])
        unit["archivos_total"] = len(unit["archivos"])
        m = unit.setdefault("metricas", {})
        m["archivos"] = len(unit["archivos"])
        capas: dict[str, int] = {}
        fuentes: dict[str, int] = {}
        for a in unit["archivos"]:
            capas[a["capa"]] = capas.get(a["capa"], 0) + 1
            fuentes[a["fuente"]] = fuentes.get(a["fuente"], 0) + 1
        m["por_capa"] = capas
        m["por_fuente"] = fuentes
        (UNITS / f"{uid}.json").write_text(
            json.dumps(unit, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"[sync_units_from_docs] ajustadas={len(changed)} "
          f"conflictos resueltos={conflictos} docs ausentes={len(missing)}"
          f"{' (dry-run)' if args.dry_run else ''}")
    for uid, antes, despues in changed:
        print(f"  {uid}: {antes} -> {despues}")
    for uid, doc in missing:
        print(f"  [doc ausente] {uid} -> {doc}")

    if args.no_orphan_fix:
        return 0

    # --- filas asignadas que ningun documento reclama -----------------------
    # Un documento puede no listar en su frontmatter un fichero que si
    # documenta en §12. Para no romper el invariante "toda fila asignada
    # tiene exactamente una unidad", cada fila huerfana se ancla a la unidad
    # de su misma feature con el prefijo comun mas largo (empate: menor id).
    units = {}
    for path in sorted(UNITS.glob("[!_]*.json")):
        u = json.loads(path.read_text(encoding="utf-8"))
        if u.get("id") and not u["id"].startswith("B"):
            units[u["id"]] = u
    owned: set[str] = set()
    for u in units.values():
        owned.update(a["ruta"] for a in u.get("archivos", []))

    orphans = [r for r in rows
               if r["feature_ids"].strip() and r["ruta"] not in owned]
    if not orphans:
        print("[sync_units_from_docs] 0 filas asignadas sin unidad")
        return 0

    def common_prefix(a: str, b: str) -> int:
        n = 0
        for x, y in zip(a, b):
            if x != y:
                break
            n += 1
        return n

    asignadas: dict[str, list[str]] = {}
    for r in orphans:
        candidatos = [
            (common_prefix(r["ruta"], a["ruta"]), uid)
            for uid, u in units.items()
            if u["feature_id"] == r["feature_ids"]
            for a in u.get("archivos", [])
        ]
        if not candidatos:
            print(f"  [sin unidad posible] {r['ruta']} ({r['feature_ids']})")
            continue
        _, uid = max(candidatos)
        asignadas.setdefault(uid, []).append(r)

    total = 0
    for uid, lst in sorted(asignadas.items()):
        u = units[uid]
        nuevos = [{"fuente": r["fuente"], "ruta": r["ruta"], "capa": r["capa"],
                   "estado": r["estado"]} for r in lst]
        antes = len(u.get("archivos", []))
        u["archivos"].extend(nuevos)
        u["archivos"].sort(key=lambda a: a["ruta"])
        u["archivos_total"] = len(u["archivos"])
        m = u.setdefault("metricas", {})
        m["archivos"] = u["archivos_total"]
        capas: dict[str, int] = {}
        for a in u["archivos"]:
            capas[a["capa"]] = capas.get(a["capa"], 0) + 1
        m["por_capa"] = capas
        fuentes: dict[str, int] = {}
        for a in u["archivos"]:
            fuentes[a["fuente"]] = fuentes.get(a["fuente"], 0) + 1
        m["por_fuente"] = fuentes
        total += len(nuevos)
        print(f"  [huerfanas] {uid}: +{len(nuevos)} ({antes} -> {u['archivos_total']})")
        if not args.dry_run:
            (UNITS / f"{uid}.json").write_text(
                json.dumps(u, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[sync_units_from_docs] reancladas {total} filas huerfanas")
    return 0


if __name__ == "__main__":
    sys.exit(main())