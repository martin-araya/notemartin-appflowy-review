#!/usr/bin/env python3
"""build_index.py — genera `00-INDEX.md` de la skill
`notemartin-appflowy-review` con árbol, estado de cada doc, cobertura
de fuente y commits; resuelve los enlaces cruzados `[[id]]` → rutas
reales.

Fase A3.5 de la skill. Spec: ROADMAP.md línea 93 y
SKILL/references/{evidence-rules,feature-template,export-template}.md.

Uso: build_index.py [opciones]
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
PROJECT_ROOT_DEFAULT = SKILL_DIR.parent
DEFAULT_OUT_DIR = PROJECT_ROOT_DEFAULT / "OUT"
DEFAULT_OUT = DEFAULT_OUT_DIR / "00-INDEX.md"

EXPECTED_HEADER = (
    "fuente",
    "ruta",
    "capa",
    "feature_ids",
    "documento",
    "estado",
    "verificado_por",
)
KNOWN_ESTADOS = {"verificado", "pendiente", "sin_asignar"}
UNCLASSIFIED = "__unclassified__"

RE_CROSSREF = re.compile(r"\[\[([A-Za-z0-9_.\-]+)(?:\|[^\]]*)?\]\]")
RE_SECTION = re.compile(r"^##\s+(\d+)\.\s")
RE_FRONT = re.compile(r"^---\s*$")

RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


# --- YAML minimalista (mismo parser que A3.3) ----------------------------


def parse_yaml(lines: list[str]) -> dict:
    out: dict = {}
    i = 0
    while i < len(lines):
        raw = lines[i]
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            i += 1
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(.*)$", line)
        if not m:
            i += 1
            continue
        key, value = m.group(1), m.group(2).strip()
        if value == "":
            items: list = []
            j = i + 1
            while j < len(lines):
                nxt_stripped = lines[j].strip()
                if not nxt_stripped:
                    j += 1
                    continue
                if nxt_stripped.startswith("- "):
                    items.append(nxt_stripped[2:].strip())
                    j += 1
                    continue
                break
            out[key] = items
            i = j
        elif value.startswith("[") and value.endswith("]"):
            inner = value[1:-1].strip()
            out[key] = [] if not inner else [x.strip() for x in inner.split(",")]
            i += 1
        else:
            out[key] = value
            i += 1
    return out


def split_frontmatter(text: str) -> tuple[dict, str]:
    """Devuelve (fm_dict, body). fm_dict es {} si no hay frontmatter."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    for idx, line in enumerate(lines[1:], start=2):
        if line.strip() == "---":
            return parse_yaml(lines[1 : idx - 1]), "\n".join(lines[idx:])
    return {}, text


# --- Carga de sources y cobertura -----------------------------------------


def load_sources(path: Path) -> list[dict] | None:
    if not path.exists():
        return None
    try:
        with path.open(encoding="utf-8") as f:
            data = json.load(f)
        sources = data.get("sources", [])
        return sources
    except (OSError, json.JSONDecodeError) as e:
        print(f"build_index.py: sources.json inválido: {e}", file=sys.stderr)
        return None


def load_cobertura(path: Path) -> dict | None:
    """Carga cobertura.csv y devuelve {global, by_capa, total}. None si ausente."""
    if not path.exists():
        return None
    try:
        with path.open(encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            if header is None or tuple(header) != EXPECTED_HEADER:
                print(
                    f"build_index.py: cobertura.csv header no matchea (en {path})",
                    file=sys.stderr,
                )
                return None
            rows = list(reader)
    except (OSError, csv.Error) as e:
        print(f"build_index.py: cobertura.csv inválido: {e}", file=sys.stderr)
        return None

    by_capa: dict[str, dict] = defaultdict(
        lambda: {"total": 0, "verificado": 0, "pendiente": 0, "sin_asignar": 0}
    )
    glob = {"total": 0, "verificado": 0, "pendiente": 0, "sin_asignar": 0}
    for r in rows:
        if len(r) < len(EXPECTED_HEADER):
            continue
        capa = r[2].strip() or UNCLASSIFIED
        estado = r[5].strip()
        by_capa[capa]["total"] += 1
        glob["total"] += 1
        if estado in KNOWN_ESTADOS:
            by_capa[capa][estado] += 1
            glob[estado] += 1

    def _pct(d: dict) -> float:
        return 100.0 * d["verificado"] / d["total"] if d["total"] else 0.0

    glob["pct"] = _pct(glob)
    for d in by_capa.values():
        d["pct"] = _pct(d)

    return {"global": dict(glob), "by_capa": dict(by_capa)}


# --- Walk de docs ---------------------------------------------------------


def collect_md_files(out_dir: Path) -> list[Path]:
    """Devuelve la lista de .md bajo out_dir, excluyendo directorios
    no-docs. Orden estable por (ruta_rel).
    """
    out: list[Path] = []
    for root, dirs, files in os.walk(out_dir):
        dirs[:] = [
            d
            for d in dirs
            if d not in (".git", "node_modules", "_wip", "fixtures", "pruebas")
        ]
        for name in sorted(files):
            if name.endswith(".md"):
                out.append(Path(root) / name)
    return sorted(out, key=lambda p: p.relative_to(out_dir).as_posix())


def scan_docs(out_dir: Path, files: list[Path]) -> list[dict]:
    """Devuelve lista de dicts por .md con metadatos extraídos."""
    docs: list[dict] = []
    for f in files:
        rel = f.relative_to(out_dir).as_posix()
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            print(f"build_index.py: no se pudo leer {f}: {e}", file=sys.stderr)
            continue
        fm, body = split_frontmatter(text)
        n_sections = sum(
            1
            for line in body.splitlines()
            if RE_SECTION.match(line) and not line.lstrip().startswith("```")
        )
        docs.append(
            {
                "rel_path": rel,
                "abs_path": f,
                "id": str(fm.get("id", "")).strip() or None,
                "titulo": str(fm.get("titulo", "")).strip() or None,
                "estado": str(fm.get("estado", "")).strip() or None,
                "n_sections": n_sections,
                "body": body,
                "frontmatter": fm,
            }
        )
    return docs


# --- Índice de ids + cross-refs ------------------------------------------


# Alias de id de FASE -> id real del documento.
#
# B3.F030: los docs de `OUT/06-puente-flutter-rust/`, `OUT/08-persistencia/` y
# los catalogos `11-…`/`12-…` declaran ids como `01-ffi`, `01-modelo-collab` o
# `11-catalogo-eventos-ffi`, que no coinciden con el id de FASE (`B1.5`, `B1.6`,
# `B2.1`…). Los documentos de features enlazan a la FASE, no al sub-documento,
# asi que sin esta tabla esos `[[B1.7]]` salian como "no resueltos" aunque el
# contenido este escrito. Se resuelve el alias al sub-documento INDICE de cada
# carpeta multi-doc, que es el que hace de entrada.
ID_ALIASES: dict[str, str] = {
    "B1.5": "06-00-indice",
    "B1.6": "07-00-indice",
    "B1.7": "08-00-indice",
    "B2.1": "11-catalogo-eventos-ffi",
    "B2.2": "12-catalogo-entidades-protobuf",
    "B2.3": "13-catalogo-blocs",
    "B2.4": "14-catalogo-notificaciones",
    "B2.5": "15-catalogo-errores",
    "B2.6": "16-catalogo-flags-rutas-atajos",
    # Alias de id de FEATURE -> doc maestro de la feature. Los documentos
    # enlazan a la feature completa (`[[F01]]`) mientras que el id real del
    # sub-documento indice es `F01.0`, o el nombre del propio fichero cuando
    # la feature es de un solo documento. Sin esta tabla esos enlaces salen
    # como "no resueltos" aunque la feature entera este escrita.
    "F00": "F00.0",
    "F01": "F01.0",
    "F02": "F02.0.1.0",
    "F03": "F03.0",
    "F05": "F05.0",
    "F09": "F09.0",
    "F12": "F12.1",
    "F13": "F13.1",
    "F15": "F15.1",
    "F16": "F16.0",
    "F19": "F19.0",
    # Alias de id de BLOQUE -> doc maestro del bloque. Los documentos
    # enlazan al bloque entero (`[[B4]]`) mientras que los docs reales
    # declaran `B4.0`, `B4.1`… La presencia del doc indice permite
    # resolverlo sin tocar los documentos que ya estaban aprobados.
    "B4": "B4.0",
    # Alias de id de FAMILIA de sub-unidades (`[[F02.9]]` apunta a la familia,
    # no a una unidad concreta). Resolven al primer sub-documento indice.
    "F00.5": "F00.5.1",
    "F00.7": "F00.7.0",
    "F01.6": "F01.6.0",
    "F02.9": "F02.9.0",
    "F18.2": "F18",
}


# Documentos que no son entregable: briefs de unidad, notas del ledger y
# pruebas. Sus `[[X]]` son marcadores de plantilla.
META_PREFIXES = ("_ledger/",)


def _is_meta(ref) -> bool:
    doc = getattr(ref, "doc_rel", None) or getattr(ref, "doc", "") or ""
    return str(doc).startswith(META_PREFIXES)


def build_id_index(docs: list[dict]) -> tuple[dict, list[str]]:
    """Devuelve ({id: rel_path}, [warnings]). Si hay duplicados, gana
    el último y se emite warning.
    """
    index: dict[str, str] = {}
    warnings: list[str] = []
    for d in docs:
        if not d["id"]:
            continue
        if d["id"] in index:
            warnings.append(
                f"id '{d['id']}' duplicado: {index[d['id']]} y {d['rel_path']} (gana este último)"
            )
        index[d["id"]] = d["rel_path"]
    for alias, target in ID_ALIASES.items():
        if alias in index:
            warnings.append(f"alias '{alias}' choca con un id real; se ignora")
        elif target in index:
            index[alias] = index[target]
        else:
            warnings.append(f"alias '{alias}' -> '{target}' no encontrado entre los ids")
    return index, warnings


CrossRef = namedtuple_CrossRef = type(
    "CrossRef",
    (),
    {"__slots__": ("doc_rel", "line", "target", "resolved_to")},
)


def _make_xref(doc_rel, line, target, resolved_to):
    o = CrossRef()
    o.doc_rel = doc_rel
    o.line = line
    o.target = target
    o.resolved_to = resolved_to
    return o


def extract_cross_refs(docs: list[dict], id_index: dict) -> list:
    """Devuelve lista de CrossRef para todas las refs `[[X]]`.

    Excluye el 00-INDEX.md (que es el artefacto que este script
    genera; las refs en su "no resueltos" son metadatos, no enlaces
    del producto).
    """
    out: list = []
    for d in docs:
        if d["rel_path"] == "00-INDEX.md":
            continue
        in_fence = False
        for line_no, line in enumerate(d["body"].splitlines(), 1):
            if line.lstrip().startswith("```"):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            for m in RE_CROSSREF.finditer(line):
                target = m.group(1)
                resolved_to = id_index.get(target)
                out.append(
                    _make_xref(d["rel_path"], line_no, target, resolved_to)
                )
    return out


# --- Cobertura de docs ---------------------------------------------------


def compute_doc_coverage(docs: list[dict]) -> dict:
    """Cuenta estados en frontmatter de los docs."""
    counts = {"verificado": 0, "pendiente": 0, "sin_asignar": 0, "__other__": 0}
    for d in docs:
        e = d["estado"] or ""
        if e in KNOWN_ESTADOS:
            counts[e] += 1
        else:
            counts["__other__"] += 1
    total = sum(counts.values())
    pct = 100.0 * counts["verificado"] / total if total else 0.0
    return {"counts": counts, "total": total, "pct": pct}


# --- Render --------------------------------------------------------------


def c_red(s, no_color):
    return s if no_color else f"{RED}{s}{RESET}"


def c_green(s, no_color):
    return s if no_color else f"{GREEN}{s}{RESET}"


def c_yellow(s, no_color):
    return s if no_color else f"{YELLOW}{s}{RESET}"


def c_bold(s, no_color):
    return s if no_color else f"{BOLD}{s}{RESET}"


def c_dim(s, no_color):
    return s if no_color else f"{DIM}{s}{RESET}"


def render_index(ctx: dict, no_color: bool) -> str:
    """ctx = {generated_at, docs, id_index, cross_refs, unresolved,
    coverage_docs, coverage_fuente, sources, n_commits}."""
    docs = ctx["docs"]
    id_index = ctx["id_index"]
    cross_refs = ctx["cross_refs"]
    unresolved = ctx["unresolved"]
    cov_docs = ctx["coverage_docs"]
    cov_fuente = ctx["coverage_fuente"]
    sources = ctx["sources"]
    n_total = len(docs)
    n_with_id = sum(1 for d in docs if d["id"])
    n_refs = len(cross_refs)
    # Los enlaces sin resolver se separan entre entregables y material de
    # trabajo. En `_ledger/briefs/` los `[[X]]`, `[[Fxx]]` y `[[B4.x]]` son
    # marcadores de plantilla de un brief, no referencias rotas: contarlos
    # mezclaba documentación real con huecos de plantilla y hacia creer que
    # quedaban enlaces pendientes en el entregable. La cifra que decide el
    # criterio de cierre del ROADMAP ("todos los enlaces resuelven") es la de
    # entregables.
    unresolved_entregables = [r for r in unresolved if not _is_meta(r)]
    n_unresolved = len(unresolved_entregables)
    n_unresolved_meta = len(unresolved) - n_unresolved
    n_commits = len(sources) if sources else 0

    out: list[str] = []
    a = out.append

    # 1. Frontmatter
    a("---")
    a("id: 00-INDEX")
    a("titulo: Índice de la skill `notemartin-appflowy-review`")
    a("estado: verificado")
    a(f"generado: {ctx['generated_at']}")
    a("---")
    a("")
    a("# 00 — Índice de la skill")
    a("")
    a(
        "> Regenerar con: `python3 SKILL/scripts/build_index.py --out-dir OUT/`."
    )
    a("")

    # 2. Resumen
    a("## 1. Resumen")
    a("")
    a("| Métrica | Valor |")
    a("|---|---|")
    a(f"| Documentos `.md` en `OUT/` | {n_total} |")
    a(f"| Documentos con `id` en frontmatter | {n_with_id} |")
    a(f"| Commits de fuentes | {n_commits} |")
    a(
        f"| Cobertura de fuente (verificado) | "
        f"{cov_fuente['global']['pct']:.2f}% |"
        if cov_fuente
        else "| Cobertura de fuente | (cobertura.csv ausente) |"
    )
    a(
        f"| Cobertura de docs (verificado) | {cov_docs['pct']:.2f}% |"
    )
    a(f"| Enlaces cruzados totales | {n_refs} |")
    if n_unresolved_meta:
        a(
            f"| Enlaces no resueltos en entregables | "
            f"{c_green('0', no_color)} {c_green('✓', no_color)} |"
            if n_unresolved == 0
            else f"| Enlaces no resueltos en entregables | "
            f"{c_red(str(n_unresolved), no_color)} |"
        )
        a(
            f"| Marcadores de plantilla en material de trabajo | "
            f"{n_unresolved_meta} (en `_ledger/`, no son entregable) |"
        )
    if not n_unresolved_meta:
        if n_unresolved == 0:
            a(
                f"| Enlaces no resueltos | "
                f"{c_green('0', no_color)} {c_green('✓', no_color)} |"
            )
        else:
            a(
                f"| Enlaces no resueltos | "
                f"{c_red(str(n_unresolved), no_color)} |"
        )
    a("")

    # 3. Commits
    a("## 2. Commits de fuentes")
    a("")
    if sources:
        a("| Fuente | Commit | URL |")
        a("|---|---|---|")
        for s in sources:
            name = s.get("name", "?")
            cs = s.get("commit_short", s.get("commit", "?")[:7])
            url = s.get("url", "")
            a(f"| {name} | `{cs}` | {url} |")
    else:
        a(c_dim("(sources.json ausente o malformado)", no_color))
    a("")

    # 4. Cobertura de docs
    a("## 3. Cobertura de docs en `OUT/`")
    a("")
    a("| estado | total | % |")
    a("|---|---:|---:|")
    for est in ("verificado", "pendiente", "sin_asignar"):
        c = cov_docs["counts"][est]
        pct = 100.0 * c / cov_docs["total"] if cov_docs["total"] else 0.0
        a(f"| {est} | {c} | {pct:.2f}% |")
    if cov_docs["counts"]["__other__"] > 0:
        a(
            f"| (otro / sin estado) | {cov_docs['counts']['__other__']} | "
            f"{100.0 * cov_docs['counts']['__other__'] / cov_docs['total']:.2f}% |"
        )
    a(
        f"| **GLOBAL** | **{cov_docs['total']}** | "
        f"**{cov_docs['pct']:.2f}%** |"
    )
    a("")

    # 5. Cobertura de fuente
    a("## 4. Cobertura de fuente (`cobertura.csv`)")
    a("")
    if cov_fuente:
        a("| capa | total | verificado | % |")
        a("|---|---:|---:|---:|")
        for capa in sorted(cov_fuente["by_capa"]):
            d = cov_fuente["by_capa"][capa]
            pct = d["pct"] if "pct" in d else 100.0 * d["verificado"] / max(1, d["total"])
            a(f"| {capa} | {d['total']} | {d['verificado']} | {pct:.2f}% |")
        g = cov_fuente["global"]
        a(
            f"| **GLOBAL** | **{g['total']}** | **{g['verificado']}** | "
            f"**{g['pct']:.2f}%** |"
        )
    else:
        a(c_dim("(cobertura.csv ausente o malformado)", no_color))
    a("")

    # 6. Árbol
    a("## 5. Árbol de documentos")
    a("")
    a("```")
    a(f"{ctx['out_dir_name']}/")
    for d in docs:
        size_kb = d["abs_path"].stat().st_size / 1024.0
        a(
            f"├── {d['rel_path']}  "
            f"({d['n_sections']} secciones, {size_kb:.1f} KB)"
        )
    a("```")
    a("")

    # 7. Tabla de docs
    a("## 6. Tabla de documentos")
    a("")
    a("| ruta | id | título | estado |")
    a("|---|---|---|---|")
    for d in docs:
        rid = d["id"] if d["id"] else "—"
        tit = d["titulo"] if d["titulo"] else "—"
        est = d["estado"] if d["estado"] else "—"
        a(f"| `{d['rel_path']}` | {rid} | {tit} | {est} |")
    a("")

    # 8. Mapa de enlaces
    a("## 7. Mapa de enlaces cruzados")
    a("")
    if cross_refs:
        a("| origen | → | destino |")
        a("|---|---|---|")
        # agrupar por origen
        by_origin: dict = defaultdict(list)
        for r in cross_refs:
            by_origin[r.doc_rel].append(r)
        for origin in sorted(by_origin):
            for r in by_origin[origin]:
                if r.resolved_to:
                    a(
                        f"| `{origin}` (línea {r.line}) | → | "
                        f"`{r.resolved_to}` (id `{r.target}`) |"
                    )
                else:
                    a(
                        f"| `{origin}` (línea {r.line}) | → | "
                        f"`{c_red('✗ no resuelto', no_color)}` (`{r.target}`) |"
                    )
    else:
        a(c_dim("(sin enlaces cruzados)", no_color))
    a("")

    # 9. No resueltos
    a("## 8. Enlaces no resueltos")
    a("")
    if not unresolved_entregables:
        a(c_green("✓ Todos los enlaces del índice resuelven.", no_color))
        if n_unresolved_meta:
            a("")
            a(
                f"Se ignoran {n_unresolved_meta} enlaces sin resolver en "
                f"`_ledger/briefs/`: son marcadores de plantilla (`[[X]]`, "
                f"`[[Fxx]]`, `[[B4.x]]`) de los briefs de unidad, no referencias "
                f"a documentos de `OUT/`."
            )
    else:
        for r in unresolved_entregables:
            a(
                f"- `{r.doc_rel}:{r.line}` → `[[{r.target}]]` "
                f"{c_red('(id no encontrado en el out-dir)', no_color)}"
            )
    a("")

    # 10. Cómo regenerar
    a("## 9. Cómo regenerar")
    a("")
    a("```bash")
    a("cd /path/to/notemartin-appflowy-review")
    a("python3 SKILL/scripts/build_index.py --out-dir OUT/")
    a("```")
    a("")

    return "\n".join(out)


# --- Main ----------------------------------------------------------------


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="build_index.py",
        description=(
            "Genera 00-INDEX.md de la skill con árbol, estado de cada "
            "doc, cobertura, commits y resolución de enlaces cruzados."
        ),
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=DEFAULT_OUT_DIR,
        help=f"Directorio raíz a indexar (default: {DEFAULT_OUT_DIR})",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Ruta del 00-INDEX.md a generar (default: <out-dir>/00-INDEX.md)",
    )
    parser.add_argument(
        "--check-links",
        action="store_true",
        help="No escribe; sólo verifica que no haya [[X]] no resueltos.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Salida en JSON estructurado a stdout.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Sólo summary final; oculta la tabla de docs.",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Desactiva códigos ANSI.",
    )
    args = parser.parse_args(argv)

    out_dir = args.out_dir
    if not out_dir.is_dir():
        print(
            f"build_index.py: out-dir no existe: {out_dir}",
            file=sys.stderr,
        )
        return 2

    out_path = args.out if args.out else (out_dir / "00-INDEX.md")

    # Cargar metadatos
    sources = load_sources(out_dir / "_ledger" / "sources.json")
    cov_fuente = load_cobertura(out_dir / "_ledger" / "cobertura.csv")

    # Walk docs
    files = collect_md_files(out_dir)
    docs = scan_docs(out_dir, files)

    # Id index
    id_index, id_warnings = build_id_index(docs)
    for w in id_warnings:
        print(f"WARN: {w}", file=sys.stderr)

    # Cross-refs
    cross_refs = extract_cross_refs(docs, id_index)
    unresolved = [r for r in cross_refs if r.resolved_to is None]

    # Cobertura docs
    cov_docs = compute_doc_coverage(docs)

    if args.json:
        out = {
            "schema_version": "1.0",
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "out_dir": str(out_dir),
            "out_path": str(out_path),
            "summary": {
                "docs_total": len(docs),
                "docs_with_id": sum(1 for d in docs if d["id"]),
                "commits": len(sources) if sources else 0,
                "refs_total": len(cross_refs),
                "unresolved_count": len([r for r in unresolved if not _is_meta(r)]),
                "unresolved_template_placeholders": len([r for r in unresolved if _is_meta(r)]),
                "doc_coverage_pct": round(cov_docs["pct"], 4),
            },
            "unresolved": [
                {"doc": r.doc_rel, "line": r.line, "target": r.target}
                for r in unresolved if not _is_meta(r)
            ],
            "unresolved_template_placeholders": [
                {"doc": r.doc_rel, "line": r.line, "target": r.target}
                for r in unresolved if _is_meta(r)
            ],
        }
        if cov_fuente:
            out["fuente_coverage_pct"] = round(cov_fuente["global"]["pct"], 4)
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        ctx = {
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "out_dir_name": out_dir.name,
            "docs": docs,
            "id_index": id_index,
            "cross_refs": cross_refs,
            "unresolved": unresolved,
            "coverage_docs": cov_docs,
            "coverage_fuente": cov_fuente,
            "sources": sources or [],
        }
        text = render_index(ctx, args.no_color)
        if args.check_links:
            n_unresolved = len(unresolved)
            msg = (
                f"Enlaces no resueltos: {n_unresolved} "
                f"(cross-refs totales: {len(cross_refs)})"
            )
            if n_unresolved == 0:
                print(c_green(msg, args.no_color))
            else:
                print(c_red(msg, args.no_color))
            return 0 if n_unresolved == 0 else 1
        try:
            out_path.write_text(text, encoding="utf-8")
        except OSError as e:
            print(f"build_index.py: no se pudo escribir {out_path}: {e}", file=sys.stderr)
            return 2
        n_unresolved = len([r for r in unresolved if not _is_meta(r)])
        n_meta = len(unresolved) - n_unresolved
        msg = (
            f"Generado {out_path}: {len(docs)} docs, "
            f"{len(cross_refs)} refs, {n_unresolved} enlaces sin resolver"
            + (f" en entregables ({n_meta} marcadores de plantilla en _ledger/)."
               if n_meta else ".")
        )
        if n_unresolved == 0:
            print(c_green(msg, args.no_color))
        else:
            print(c_yellow(msg, args.no_color))

    return 0 if not unresolved else 1


if __name__ == "__main__":
    sys.exit(main())
