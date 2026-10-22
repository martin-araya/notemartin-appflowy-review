#!/usr/bin/env python3
"""harvest_open_questions.py — vuelca las `[NO DETERMINADO]` de la sección 18
de los documentos de `OUT/09-features/` a `OUT/22-preguntas-abiertas.md`.

Por qué existe: el cierre de fase exige que ninguna pregunta quede solo en su
documento. La sección 18 de la plantilla es la lista literal, pero está en
Markdown natural (viñetas, párrafos, tablas), no en un formato parseable de
forma fiable. Este extractor se queda con las viñetas y los párrafos que
contienen la etiqueta, conserva el `origen` (id del documento) y **no toca las
entradas que ya están** en el fichero (idempotente por el prefijo `- **<id>**`).

Uso:
  python3 harvest_open_questions.py --dry-run
  python3 harvest_open_questions.py --desde B3.F08     # solo esas unidades
"""
from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
# El bloque B4 (OUT/10-motor-export-import/) usa la plantilla `export-template.md`
# (11 secciones) en lugar de la de feature, y sus [NO DETERMINADO] viven en las
# secciones de perdidas/errores (5 y 8) en vez de en la seccion 18. Se recorren
# ambos arboles y se corta por la ultima seccion numerada de cada plantilla.
SCAN_DIRS = [
    PROJECT_ROOT / "OUT" / "09-features",
    PROJECT_ROOT / "OUT" / "10-motor-export-import",
    PROJECT_ROOT / "OUT" / "15-secuencias-globales",
    # Bloque B6: los documentos transversales cuelgan de la raíz de OUT/
    # (18-build-ci-distribucion.md, 19-testing.md, 20-seguridad-y-privacidad.md).
    # Se recorre el directorio, no los ficheros sueltos, para no arrastrar
    # STATE.md ni 00-INDEX.md, que se regeneran.
    PROJECT_ROOT / "OUT",
]
# Ficheros de la raíz de OUT/ que nunca son fuente de preguntas: son
# artefactos generados o el propio destino del harvest.
EXCLUIDOS_RAIZ = {"22-preguntas-abiertas.md", "STATE.md", "00-INDEX.md"}

DEST = PROJECT_ROOT / "OUT" / "22-preguntas-abiertas.md"

SECCION = re.compile(r"^##\s*18\.", re.M)
SIGUIENTE = re.compile(r"^##\s*19\.", re.M)
# Plantilla export/import: se toman las secciones 5..8 (perdidas, assets,
# encoding, errores) porque ahi es donde se registran los [NO DETERMINADO].
SECCION_EXPORT = re.compile(r"^##\s*5\.", re.M)
SIGUIENTE_EXPORT = re.compile(r"^##\s*9\.", re.M)
# Plantilla transversal (Bloque B6): los [NO DETERMINADO] viven en la
# seccion 6 ("Riesgos, huecos y decisiones de diseno pendientes") y la
# seccion 7 es "Relacionado con".
SECCION_TRANSVERSAL = re.compile(r"^##\s*6\.", re.M)
SIGUIENTE_TRANSVERSAL = re.compile(r"^##\s*7\.", re.M)
# Plantilla `resumen` (B6.4): no tiene sección de riesgos; sus preguntas
# openness están bajo `### Preguntas abiertas`, dentro de la sección 7.
SECCION_RESUMEN = re.compile(r"^###\s*Preguntas abiertas", re.M)
# Plantilla `glosario` (B6.5): las entradas sin determinar están intercaladas
# en las secciones 4..7 como ítems de lista, así que se recorre el cuerpo
# entero en lugar de recortar una sección.
SIN_RECORTE = re.compile(r"^(?!x)x")  # nunca casa: marca "todo el cuerpo"
ID_DOC = re.compile(r"^id:\s*(\S+)", re.M)
ETIQUETA = "[NO DETERMINADO]"

# Plantillas cuyo bloque de preguntas se recorta por secciones numeradas.
# Cada entrada es (regex_de_inicio, regex_de_fin, predicado_de_id). El orden
# importa: el primer predicado que casa gana.
RECORTES = [
    (SECCION, SIGUIENTE, lambda i: not i.startswith(("B4.", "B6."))),
    (SECCION_EXPORT, SIGUIENTE_EXPORT, lambda i: i.startswith("B4.")),
    (SECCION_RESUMEN, SIN_RECORTE, lambda i: i == "B6.4"),
    (SIN_RECORTE, SIN_RECORTE, lambda i: i == "B6.5"),
    (SECCION_TRANSVERSAL, SIGUIENTE_TRANSVERSAL, lambda i: i.startswith("B6.")),
]


def preguntas_de(doc: Path) -> tuple[str, list[str]]:
    text = doc.read_text(encoding="utf-8")
    m_id = ID_DOC.search(text)
    doc_id = m_id.group(1) if m_id else doc.stem
    m_ini = None
    m_fin = None
    cuerpo_integro = False
    for re_ini, re_fin, aplica in RECORTES:
        if not aplica(doc_id):
            continue
        if re_ini is SIN_RECORTE:
            cuerpo_integro = True
            break
        m_ini = re_ini.search(text)
        if not m_ini:
            return doc_id, []
        m_fin = re_fin.search(text, m_ini.end())
        break
    if not cuerpo_integro and m_ini is None:
        return doc_id, []
    bloque = (
        text
        if cuerpo_integro
        else text[m_ini.end(): m_fin.start() if m_fin else len(text)]
    )
    out: list[str] = []
    # Regla 1: la propia línea contiene la etiqueta (viñeta o párrafo suelto).
    # Regla 2: la etiqueta está en un heading `###`/`####` y las preguntas son
    # sus elementos de lista. Algunos autores (B6.3) titulan la subsección
    # `### 6.2 \`[NO DETERMINADO]\` — huecos reales` y no repiten la etiqueta en
    # cada ítem; sin esta regla esas preguntas nunca llegarían al fichero.
    sub_bajo_etiqueta = False
    for linea in bloque.splitlines():
        s = linea.strip()
        if not s:
            continue
        if s.startswith("#"):
            sub_bajo_etiqueta = ETIQUETA in s
            continue
        es_item = bool(re.match(r"^([-*]|\d+\.)\s+", s))
        if ETIQUETA not in s and not (sub_bajo_etiqueta and es_item):
            continue
        if es_item or ETIQUETA in s:
            s = re.sub(r"^[-*]\s*", "", s)
            s = re.sub(r"^\d+\.\s*", "", s)
            out.append(s)
    return doc_id, out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--desde", default="", help="solo ids >= este prefijo (p. ej. B3.F08)")
    ap.add_argument("--solo", default="",
                    help="lista separada por comas de ids exactos (F08,F09.1,…)")
    ap.add_argument("--verbose", action="store_true",
                    help="lista el texto completo de cada pregunta nueva")
    args = ap.parse_args()

    hoy = date.today().isoformat()
    ya_vistas: set[str] = set()

    solo = {s.strip() for s in args.solo.split(",") if s.strip()}
    actuales = DEST.read_text(encoding="utf-8") if DEST.is_file() else ""
    nuevas: list[tuple[str, str]] = []
    docs = [
        d for base in SCAN_DIRS if base.is_dir()
        for d in base.rglob("*.md")
        if not (d.parent == base and d.name in EXCLUIDOS_RAIZ)
    ]
    for doc in sorted(docs):
        doc_id, qs = preguntas_de(doc)
        if solo and doc_id not in solo:
            continue
        if args.desde and doc_id < args.desde:
            continue
        for q in qs:
            # Normaliza el id: F09.1 -> B3.F09.1
            origen = doc_id if doc_id.startswith("B") else f"B3.{doc_id}"
            # Idempotencia estricta: la entrada completa debe estar ya escrita.
            # Se compara contra el fichero Y contra lo recogido en esta misma
            # pasada, para no duplicar cuando el mismo `[NO DETERMINADO]`
            # aparece dos veces en el documento origen.
            completa = f"- **{origen}** — {q}"
            if completa in actuales or completa in ya_vistas:
                continue
            ya_vistas.add(completa)
            nuevas.append((origen, q))

    por_doc = {}
    for origen, q in nuevas:
        por_doc.setdefault(origen, []).append(q)
    print(f"[harvest] {len(nuevas)} preguntas nuevas de {len(por_doc)} documentos")
    for origen in sorted(por_doc):
        print(f"  {origen}: {len(por_doc[origen])}")
    if args.verbose:
        for origen in sorted(por_doc):
            for q in por_doc[origen]:
                print(f"    {origen}: {q[:160]}")
    if args.dry_run or not nuevas:
        return 0

    bloque = ["", f"## Harvest automático · {hoy} · {len(nuevas)} preguntas", "",
              "Preguntas recogidas automáticamente de las secciones de "
              "`[NO DETERMINADO]` de los documentos de `OUT/`. Recogidas por "
              "`SKILL/scripts/harvest_open_questions.py`; el bloque es "
              "idempotente (una entrada ya escrita no se vuelve a copiar).", ""]
    for origen in sorted(por_doc):
        bloque.append(f"### {origen} ({len(por_doc[origen])})")
        bloque.append("")
        for q in por_doc[origen]:
            bloque.append(f"- **{origen}** — {q}")
        bloque.append("")
    DEST.write_text(actuales.rstrip("\n") + "\n" + "\n".join(bloque) + "\n",
                    encoding="utf-8")
    print(f"[harvest] escritas en {DEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())