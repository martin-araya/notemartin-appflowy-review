#!/usr/bin/env python3
"""set_unit_docs.py — Fija a mano la ruta de documento de unidades concretas y
reconstruye `OUT/_ledger/units/_index.json` desde el directorio completo.

Hace falta cuando el slug que genera `build_units.py` no coincide con el
nombre que acabo escribiendo a mano (asi ocurrio con F03/F05 en B3.F030, y con
F21, que quedo como `F21-f21/F21-f21.md` porque `FEATURE_TITLES` no tenia
entrada).

Uso:
  python3 SKILL/scripts/set_unit_docs.py                 # solo reconstruye el indice
  python3 SKILL/scripts/set_unit_docs.py F16.2=OUT/09-features/F16-mobile/2-....md
  python3 SKILL/scripts/set_unit_docs.py --listar
"""
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
UNITS_DIR = PROJECT_ROOT / "OUT" / "_ledger" / "units"

# Rutas fijadas a mano en B3.F030 (F03 y F05). El resto se deduce del slug.
DOCS: dict[str, str] = {
    "F03.0": "OUT/09-features/F03-folder-workspaces-vistas/0.0-indice-folder-workspaces-vistas.md",
    "F03.1": "OUT/09-features/F03-folder-workspaces-vistas/0.1-vistas-workspaces-sidebar-dart.md",
    "F03.2": "OUT/09-features/F03-folder-workspaces-vistas/0.2-flowy-folder-rust.md",
    "F03.3": "OUT/09-features/F03-folder-workspaces-vistas/0.3-collab-folder.md",
    "F05.0": "OUT/09-features/F05-usuario-auth-sesion/0.0-indice-usuario-auth-sesion.md",
    "F05.1": "OUT/09-features/F05-usuario-auth-sesion/1-usuario-appflowy-flutter-lib-user-dart.md",
    "F05.2": "OUT/09-features/F05-usuario-auth-sesion/2-usuario-flowy-user-collab-user-rust-collab.md",
    # B3.F01: el indice real se llamo `0.0-indice-documentos-y-editor.md`,
    # no `0-indice-de-documentos-y-editor-...`.
    "F01.0": "OUT/09-features/F01-documentos-y-editor/0.0-indice-documentos-y-editor.md",
}


def main() -> int:
    args = sys.argv[1:]
    docs = dict(DOCS)
    if args and args[0] == "--listar":
        for p in sorted(UNITS_DIR.glob("[!_]*.json")):
            u = json.loads(p.read_text(encoding="utf-8"))
            existe = "OK " if (PROJECT_ROOT / str(u.get("documento", ""))).is_file() else "FALTA"
            print(f"{existe}  {u['id']:12} {u.get('documento')}")
        return 0
    for arg in args:
        if "=" not in arg:
            print(f"argumento invalido: {arg} (se espera UNIDAD=RUTA.md)")
            return 2
        uid, ruta = arg.split("=", 1)
        docs[uid.strip()] = ruta.strip()

    units = []
    for p in sorted(UNITS_DIR.glob("[!_]*.json")):
        units.append(json.loads(p.read_text(encoding="utf-8")))

    changed = 0
    for u in units:
        if u["id"] in docs and u.get("documento") != docs[u["id"]]:
            u["documento"] = docs[u["id"]]
            changed += 1
        (UNITS_DIR / f"{u['id']}.json").write_text(
            json.dumps(u, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

    # El indice lo reconstruye `build_units.py --index-only`, que ya lee el
    # directorio completo. Aqui solo se avisa del resumen.
    capas = Counter()
    for u in units:
        if not str(u["id"]).startswith("B"):
            capas[u["feature_id"]] += u["archivos_total"]
    print(f"documentos fijados: {changed}")
    print("por feature: " + ", ".join(f"{k}={v}" for k, v in sorted(capas.items())))
    print("ejecuta `build_units.py --index-only` para reindexar")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())