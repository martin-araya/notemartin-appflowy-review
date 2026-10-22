#!/usr/bin/env python3
"""purge_stale.py — borra unidades obsoletas de OUT/_ledger/units/.

Fase 0 del plan de cierre del Bloque B3.这些 ficheros son restos de:

  1. La recursion de `_split_one_level` que se probo y se descarto
     (`F00.5.6.2.*`, `F00.7.1.*`, `F00.7.2.*`): dejaban ~35 unidades de
     1-15 archivos para el andamiaje `example/` y `android/` de los paquetes.
  2. Las units maestro de features que ya estan subdivididas
     (`F02.0.1`, `F02.0.2`, `F03`): duplican la propiedad de sus hijas y ya
     fueron purgadas en B3.F030; reaparecieron al restaurar `.stale-bak`.

No toca `_index.json`, ni las unidades `B1.*`, ni ninguna unidad viva.
Es idempotente. Copia a `.stale-bak/` antes de borrar.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

UNITS = Path(__file__).resolve().parents[4] / "OUT" / "_ledger" / "units"

STALE_EXACT = {
    "F02.0.1.json",  # unit padre obsoleta (purgada en B3.F030)
    "F02.0.2.json",  # unit padre obsoleta (purgada en B3.F030)
    "F03.json",      # unit maestro de F03, duplica F03.0..F03.3
}
STALE_PREFIXES = ("F00.5.6.2.", "F00.7.1.", "F00.7.2.")


def main() -> int:
    backup = UNITS / ".stale-bak"
    backup.mkdir(parents=True, exist_ok=True)
    purged = []
    for path in sorted(UNITS.glob("*.json")):
        name = path.name
        if name == "_index.json":
            continue
        stale = name in STALE_EXACT or name.startswith(STALE_PREFIXES)
        if not stale:
            continue
        shutil.copy2(path, backup / name)
        path.unlink()
        purged.append(name)
    print(f"[purge_stale] purgadas {len(purged)} unidades obsoletas")
    for name in purged:
        print(f"  - {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())