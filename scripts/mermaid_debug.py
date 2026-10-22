#!/usr/bin/env python3
"""mermaid_debug.py — renderiza cada bloque mermaid de un documento por
separado y muestra el error real del que falle.

Útil cuando `validate_mermaid.sh` solo dice "1 FAIL": mmdc recibe todos los
bloques en un fichero concatenado y el error que reporta no corresponde al
diagrama que falla.
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path

BLOCK = re.compile(r"```mermaid\n(.*?)```", re.S)


def main() -> int:
    path = Path(sys.argv[1])
    blocks = BLOCK.findall(path.read_text(encoding="utf-8"))
    if not blocks:
        print("sin bloques mermaid")
        return 0
    fallos = 0
    with tempfile.TemporaryDirectory() as tmp:
        for i, b in enumerate(blocks, 1):
            src = Path(tmp) / f"b{i}.mmd"
            out = Path(tmp) / f"b{i}.svg"
            src.write_text(b, encoding="utf-8")
            r = subprocess.run(
                ["npx", "-y", "@mermaid-js/mermaid-cli", "-i", str(src), "-o", str(out)],
                capture_output=True, text=True,
            )
            if r.returncode == 0:
                print(f"bloque {i}: OK")
            else:
                fallos += 1
                print(f"bloque {i}: FAIL — primera línea: {b.splitlines()[0]!r}")
                err = (r.stderr or r.stdout).strip().splitlines()
                for line in err[:4]:
                    print(f"    {line}")
    print(f"{len(blocks) - fallos}/{len(blocks)} bloques OK")
    return 1 if fallos else 0


if __name__ == "__main__":
    raise SystemExit(main())