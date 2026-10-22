#!/usr/bin/env python3
"""set_unit_docs.py — Fija las rutas de documento de las unidades B3.F03..F07 y
regenera `OUT/_ledger/units/_index.json` a partir del directorio completo.

`build_units.py --include F03,F05` regenera `_index.json` solo con las features
incluidas y genera nombres de documento por slug del titulo (demasiado largos).
Este script corrige ambas cosas sin tocar el resto de unidades.

Uso: python3 OUT/_ledger/pruebas/B3.F030/set_unit_docs.py
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
UNITS_DIR = PROJECT_ROOT / "OUT" / "_ledger" / "units"

DOCS = {
    "F03.0": "OUT/09-features/F03-folder-workspaces-vistas/0.0-indice-folder-workspaces-vistas.md",
    "F03.1": "OUT/09-features/F03-folder-workspaces-vistas/0.1-vistas-workspaces-sidebar-dart.md",
    "F03.2": "OUT/09-features/F03-folder-workspaces-vistas/0.2-flowy-folder-rust.md",
    "F03.3": "OUT/09-features/F03-folder-workspaces-vistas/0.3-collab-folder.md",
    "F05.0": "OUT/09-features/F05-usuario-auth-sesion/0.0-indice-usuario-auth-sesion.md",
    "F05.1": "OUT/09-features/F05-usuario-auth-sesion/1-usuario-appflowy-flutter-lib-user-dart.md",
    "F05.2": "OUT/09-features/F05-usuario-auth-sesion/2-usuario-flowy-user-collab-user-rust-collab.md",
}

PRIORIDAD = {"F03": 1, "F04": 1, "F05": 2, "F06": 1, "F07": 2}


def main() -> int:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    units = []
    for p in sorted(UNITS_DIR.glob("[!_]*.json")):
        units.append(json.loads(p.read_text(encoding="utf-8")))

    changed = 0
    for u in units:
        if u["id"] in DOCS and u.get("documento") != DOCS[u["id"]]:
            u["documento"] = DOCS[u["id"]]
            changed += 1
        if u["id"].split(".")[0] in PRIORIDAD:
            u["prioridad"] = PRIORIDAD[u["id"].split(".")[0]]
        (UNITS_DIR / f"{u['id']}.json").write_text(
            json.dumps(u, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )

    # --- _index.json desde el directorio completo (orden estable) ---
    feature_units = [u for u in units if not str(u["id"]).startswith("B")]
    by_feature = defaultdict(list)
    for u in feature_units:
        by_feature[u.get("feature_id", "?")].append(u)

    def sort_key(u: dict) -> tuple:
        parts = str(u["id"]).split(".")
        return (int(parts[0][1:]) if len(parts[0]) > 1 else 0,
                tuple(int(p) for p in parts[1:] if p.isdigit()))

    features_vacias = sorted(
        {f"F{n:02d}" for n in range(0, 22)} - set(by_feature)
    )
    index = {
        "schema_version": 1,
        "generado_en": now,
        "total_unidades": len(feature_units),
        "archivos_total_global": sum(u["archivos_total"] for u in feature_units),
        "units": [
            {
                "id": u["id"],
                "feature_id": u["feature_id"],
                "titulo": u["titulo"],
                "archivos_total": u["archivos_total"],
                "prioridad": u.get("prioridad", 1),
                "concurrencia": u.get("concurrencia", "paralela"),
                "dependencias": u.get("dependencias", []),
                "documento": u["documento"],
            }
            for u in sorted(feature_units, key=sort_key)
        ],
        "features_vacias": features_vacias,
    }
    (UNITS_DIR / "_index.json").write_text(
        json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    capas = Counter()
    for u in feature_units:
        capas[u["feature_id"]] += u["archivos_total"]
    print(f"documentos fijados: {changed}")
    print(f"_index.json: {index['total_unidades']} unidades, "
          f"{index['archivos_total_global']} archivos")
    print("por feature: " + ", ".join(f"{k}={v}" for k, v in sorted(capas.items())))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())