#!/usr/bin/env python3
"""audit_f02_leak.py — Fase 0.1 del plan de cierre del Bloque B3.

Audita los N archivos con `feature_ids=F02` que siguen en estado `pendiente`
tras el cierre de F02, y los clasifica en tres categorías:

  (a) citados literalmente en algún documento de F02  -> marcar `verificado`
  (b) cubiertos de facto pero sin cita                -> anadir cita y marcar
  (c) no cubiertos                                    -> nuevo documento

Uso:
  python3 audit_f02_leak.py [--dry-run] [--json OUT.json]

Salida:
  - tabla por grupo (raiz / entities / services-utils / tests)
  - `README-audit.md` con el detalle ruta a ruta
  - exit 0 si no hay categoria (c); exit 1 si la hay (requiere doc nuevo)
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT_ROOT / "SKILL" / "scripts"))

from validate_evidence import extract_refs  # noqa: E402

LEDGER = PROJECT_ROOT / "OUT" / "_ledger" / "cobertura.csv"
INVENTARIO = PROJECT_ROOT / "OUT" / "_ledger" / "inventario.json"
DOCS_DIR = PROJECT_ROOT / "OUT" / "09-features" / "F02-bases-de-datos"
OUT_DIR = PROJECT_ROOT / "OUT" / "_ledger" / "pruebas" / "B3.F02audit"

PREFIX = "appflowy/frontend/rust-lib/flowy-database2/"


def group_of(ruta: str) -> str:
    rel = ruta[len(PREFIX):] if ruta.startswith(PREFIX) else ruta
    if rel.startswith("tests/"):
        return "tests/database/**"
    if rel.startswith("src/entities/"):
        return "src/entities/**"
    if rel.startswith("src/services/") or rel.startswith("src/utils/"):
        return "src/{services,utils}"
    return "raiz de flowy-database2"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--json", type=Path, default=OUT_DIR / "audit.json")
    args = ap.parse_args()

    rows = list(csv.DictReader(LEDGER.open(encoding="utf-8")))
    leaked = [r for r in rows if r["feature_ids"] == "F02" and r["estado"] == "pendiente"]
    leaked.sort(key=lambda r: r["ruta"])

    # Rutas citadas por cualquier documento de F02.
    cited: dict[str, list[str]] = defaultdict(list)
    docs = sorted(DOCS_DIR.glob("*.md"))
    for doc in docs:
        text = doc.read_text(encoding="utf-8")
        for ref in extract_refs(text):
            cited[ref.ruta].append(f"{doc.name}:{ref.doc_line}")

    # inventario.json: `ruta_rel` ya incluye el prefijo de fuente
    # (p. ej. "appflowy/frontend/..."), que es la forma en que las citas
    # aparecen en los documentos.
    inv = json.loads(INVENTARIO.read_text(encoding="utf-8"))
    ruta_rel = {e["ruta_rel"]: e for e in inv.get("files", []) if e.get("ruta_rel")}

    a, b, c = [], [], []
    for r in leaked:
        rel = r["ruta"]
        hits = cited.get(rel, [])
        item = {
            "ruta": r["ruta"],
            "ruta_rel": rel,
            "loc": ruta_rel.get(rel, {}).get("loc"),
            "grupo": group_of(r["ruta"]),
            "citas": hits,
        }
        if hits:
            a.append(item)
        else:
            # (b)vs(c): ¿el path aparece en la tabla de archivos cubiertos (§12)
            # o en el frontmatter `archivos_cubiertos` del algún doc?
            covered_in_front = False
            for doc in docs:
                if r["ruta"] in doc.read_text(encoding="utf-8") or (rel and rel in doc.read_text(encoding="utf-8")):
                    covered_in_front = True
                    break
            item["mencionada"] = covered_in_front
            (b if covered_in_front else c).append(item)

    by_group: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for item in a:
        by_group[item["grupo"]]["a"] += 1
    for item in b:
        by_group[item["grupo"]]["b"] += 1
    for item in c:
        by_group[item["grupo"]]["c"] += 1

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "total_leak": len(leaked),
        "docs_analizados": [d.name for d in docs],
        "categorias": {"a_citado": len(a), "b_mencionado_sin_cita": len(b), "c_sin_cubrir": len(c)},
        "por_grupo": {k: dict(v) for k, v in sorted(by_group.items())},
        "detalle": {"a": a, "b": b, "c": c},
    }
    args.json.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Auditoría de la fuga de F02 (Fase 0.1)",
        "",
        "Audita los archivos con `feature_ids=F02` que siguen en `pendiente` tras el",
        "cierre de F02 declarado en el ROADMAP. Cada ruta se clasifica comparándola con",
        "las referencias `[fuente:]ruta:línea` extraídas por `validate_evidence.extract_refs`",
        "de los 21 documentos de `OUT/09-features/F02-bases-de-datos/`.",
        "",
        "## Resultado",
        "",
        f"- Fugas detectadas: **{len(leaked)}**",
        f"- (a) citadas literalmente en algún doc: **{len(a)}** → marcables como `verificado` con `verificado_por=autor_<doc>`",
        f"- (b) mencionadas (frontmatter o §12) pero sin cita `ruta:línea`: **{len(b)}** → hay que **añadir la cita** al doc y re-validar antes de marcar",
        f"- (c) sin cobertura en ningún doc: **{len(c)}** → requieren documento nuevo",
        "",
        "## Distribución por grupo",
        "",
        "| Grupo | (a) citado | (b) mencionado sin cita | (c) sin cubrir | Total |",
        "|---|---:|---:|---:|---:|",
    ]
    for grupo in sorted(by_group):
        g = by_group[grupo]
        tot = g["a"] + g["b"] + g["c"]
        lines.append(f"| `{grupo}` | {g['a']} | {g['b']} | {g['c']} | {tot} |")
    lines.append(f"| **Total** | **{len(a)}** | **{len(b)}** | **{len(c)}** | **{len(leaked)}** |")
    lines += ["", "## Detalle (a) — citadas literalmente", "", "| Ruta | Cita |", "|---|---|"]
    for item in a:
        lines.append(f"| `{item['ruta_rel']}` | {', '.join(item['citas'])} |")
    lines += ["", "## Detalle (b) — mencionadas sin cita", "", "| Ruta | Grupo |", "|---|---|"]
    for item in b:
        lines.append(f"| `{item['ruta_rel']}` | `{item['grupo']}` |")
    lines += ["", "## Detalle (c) — sin cubrir", "", "| Ruta | Grupo |", "|---|---|"]
    for item in c:
        lines.append(f"| `{item['ruta_rel']}` | `{item['grupo']}` |")
    lines.append("")
    (OUT_DIR / "README-audit.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"[audit_f02_leak] fugas={len(leaked)} a={len(a)} b={len(b)} c={len(c)}")
    for grupo in sorted(by_group):
        g = by_group[grupo]
        print(f"  {grupo:32s} a={g['a']:3d} b={g['b']:3d} c={g['c']:3d}")
    print(f"[audit_f02_leak] detalle en {OUT_DIR / 'README-audit.md'}")
    return 0 if not c else 1


if __name__ == "__main__":
    raise SystemExit(main())