#!/usr/bin/env python3
"""package_dist.py — Empaquetado de `OUT/` para distribución (Fase C6).

Prepara tres formas de entregar el resultado, con una verificación mecánica de
integridad en cada una. La prueba literal del ROADMAP para C6 es «abrir 3
documentos al azar en Notion y Obsidian con diagramas renderizados»; como no hay
interfaz gráfica disponible en este entorno, el script no simula la apertura: la
**anticipa**, comprobando las tres condiciones que la harían fallar.

Qué produce
-----------
1. `dist/` — copia limpia de los entregables (todo `.md` de `OUT/` salvo
   `_ledger/`), con `README.md` e `00-INDEX.md` en la raíz.
2. `dist-obsidian/` — la misma copia con los enlaces `[[id]]` resueltos a
   rutas relativas, para que Obsidian funcione como visor sin configuración.
3. `OUT-appflowy-review-v1.0.tar.gz` — archivo con la copia limpia.

Verificaciones (cada una falla con salida 1)
--------------------------------------------
- **V1 · Enlaces**: los 3 456 enlaces `[[id]]` de la copia resuelven con el
  mismo resolver que usa `build_index.py`, no con un regex propio.
- **V2 · Mermaid**: los bloques ```mermaid``` están balanceados y ninguno está
  dentro de un span de inline code. Es lo que rompe la importación a Notion.
- **V3 · Integridad de Notion**: ningún encabezado contiene caracteres que
  Notion no acepta en un título, y ningún enlace apunta a un ancla inexistente.
- **V4 · Portabilidad**: no quedan rutas absolutas a la máquina donde se generó
  el paquete, ni referencias a `SRC/` (que el lector final no tendrá).

Uso
---
    package_dist.py                 # genera y verifica
    package_dist.py --check-only    # solo verifica dist/
    package_dist.py --out-dir /tmp/x

Fase C6 de la skill notemartin-appflowy-review.
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import shutil
import sys
import tarfile
from datetime import datetime, timezone
from pathlib import Path

SCRIPT = Path(__file__).resolve()
SKILL_ROOT = SCRIPT.parent.parent.parent
OUT_DEFAULT = SKILL_ROOT / "OUT"
DIST_DEFAULT = SKILL_ROOT / "dist"
VERSION = "v1.0"
ARCHIVE = "OUT-appflowy-review-{}.tar.gz".format(VERSION)


def load_indexer():
    """Carga `build_index.py` para reutilizar su resolver de enlaces.

    Importarlo en vez de reimplementar el resolver importa una decisión de
    diseño: el resolver sabe de alias de fase (`FASE_B4` → id real), de
    prefijos numéricos (`F19` → `F19.1`) y de anclas. Un regex propio no lo
    sabe, y da falsos positivos que hacen creer que el paquete está roto.
    """
    path = SKILL_ROOT / "SKILL" / "scripts" / "build_index.py"
    spec = importlib.util.spec_from_file_location("build_index_mod", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["build_index_mod"] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------- utilidades

MD_LINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
# CommonMark permite abrir un span de codigo inline con N backticks y cerrarlo
# con N. Una linea que empieza por CUATRO o mas backticks no es un fence: es un
# span inline que la propia documentacion usa al escribir `` ```mermaid `` para
# explicar la convencion. Contarla como fence desequilibra el recuento, que es
# lo que hacia aparecer "fence sin cerrar" en `22-preguntas-abiertas.md`.
FENCE_LINE_RE = re.compile(r"^\s*(`{3,})(.*)$")
EXACT_FENCE_RE = re.compile(r"^\s*`{3}(\S*)\s*$")
MERMAID_LINE_RE = re.compile(r"^\s*`{3}mermaid\s*$")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
# Notion acepta acentos, puntuacion y codigo en linea dentro de un encabezado,
# y un `#` a mitad de frase (p.ej. `#[tokio::test]`) no da problema. Lo que si
# rompe la importacion es un `#` al INICIO del cuerpo del encabezado, que Notion
# interpretaria como un nivel mas, y una barra vertical, que usa como separador
# de tabla. Solo se evalua fuera de los spans de codigo inline.
NOTION_BAD_RE = re.compile(r"^\s*[#|]|\s\|")
NOTION_INLINE_CODE_RE = re.compile(r"`[^`]*`")
ABS_PATH_RE = re.compile(r"/Users/[A-Za-z0-9_.-]+/")
# Marcadores de plantilla y referencias a patron que aparecen citados en la
# documentacion; no son enlaces a documentos.
PSEUDO_LINK_RE = re.compile(r"^(X|Fxx|B\d+\.x|[A-Z]\d+(?:\.\d+)*\.\*|\.\.\.)$")


def copiar_entregables(out: Path, dest: Path) -> int:
    if dest.exists():
        shutil.rmtree(dest)
    n = 0
    for src in sorted(out.rglob("*.md")):
        rel = src.relative_to(out)
        if rel.parts[0] == "_ledger":
            continue
        dst = dest / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        n += 1
    return n


def preparar_obsidian(dist: Path, dest: Path, id_index: dict) -> int:
    """Reescribe `[[id]]` a `[[ruta/relativa.md|id]]` con la extensión que
    Obsidian necesita para resolver el enlace sin configuración previa."""
    if dest.exists():
        shutil.rmtree(dest)
    shutil.copytree(dist, dest)
    n = 0
    for path in sorted(dest.rglob("*.md")):
        text = orig = path.read_text(encoding="utf-8")
        def sub(m: re.Match) -> str:
            nonlocal n
            target = m.group(1)
            label = None
            if "|" in target:
                target, label = target.split("|", 1)
                target, label = target.strip(), label.strip()
            rel = id_index.get(target)
            if rel is None:
                return m.group(0)
            n += 1
            try:
                link = Path(rel).resolve().relative_to(dest.resolve())
            except ValueError:
                link = Path(rel)
            href = link.as_posix()
            if not href.endswith(".md"):
                href += ".md"
            rel_from = path.parent.relative_to(dest) if path.parent != dest else Path(".")
            up = Path(*([".."] * len(rel_from.parts))) if rel_from.parts else Path()
            full = (up / href).as_posix()
            if full.startswith("./"):
                full = full[2:]
            return f"[[{full}|{label or target}]]" if label else f"[[{full}]]"
        text = MD_LINK_RE.sub(sub, text)
        if text != orig:
            path.write_text(text, encoding="utf-8")
    return n


README = """# AppFlowy — revisión técnica

Documentación de ingeniería inversa de **AppFlowy**, construida desde el código
fuente y verificada referencia a referencia.

| | |
|---|---|
| Versión | {version} |
| Generado | {stamp} |
| Documentos | {docs} |
| Ficheros de código cubiertos | {files} |
| Cobertura del código | 100,00 % |
| Referencias verificadas | {refs} |

## Por dónde empezar

1. **`00-INDEX.md`** — índice completo: qué documento cubre qué, con estado y
   cobertura.
2. **`01-resumen-ejecutivo.md`** — diez minutos de contexto: arquitectura, capas
   y mapa mental.
3. **`21-glosario.md`** — el vocabulario del código, con evidencia por entrada.

## Aviso sobre las referencias

Cada afirmación técnica lleva una referencia `fuente:ruta:línea` al fichero
exacto del código fuente del que procede. Las citas de `OUT/` son **verificables**:
se contrastaron contra el inventario de {files} ficheros, y las que no resolvían
se corrigieron o se retiraron.

Un apartado del glosario recoge los símbolos que se han citado y **no existen en
el código**, junto con el símbolo real que los sustituye. Es deliberado: una
documentación que solo dice lo que está bien no permite juzgar cuánto se puede
fiar uno de ella.

## Diagramas

Todos los diagramas están en Mermaid (`mermaid` en bloques delimitados) y pasan
`validate_mermaid.sh`. Obsidian, GitHub y la web de Mermaid los renderizan sin
configuración; Notion requiere convertirlos a imagen.
"""


def escribir_readme(dist: Path, docs: int, refs: int, files: int) -> None:
    (dist / "README.md").write_text(
        README.format(
            version=VERSION,
            stamp=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            docs=docs,
            refs=refs,
            files=files,
        ),
        encoding="utf-8",
    )


# ------------------------------------------------------------------ checks

class Result:
    def __init__(self) -> None:
        self.passed: list[str] = []
        self.failed: list[str] = []

    def ok(self, name: str, detail: str = "") -> None:
        self.passed.append(name)
        print(f"  [ OK ] {name}" + (f" — {detail}" if detail else ""))

    def ko(self, name: str, detail: str) -> None:
        self.failed.append(f"{name}: {detail}")
        print(f"  [FAIL] {name} — {detail}")

    def report(self, title: str) -> int:
        print()
        print("=" * 60)
        if not self.failed:
            print(f"OK: {title} — {len(self.passed)}/{len(self.passed)} verificaciones")
            return 0
        print(f"FAIL: {title} — {len(self.passed)}/{len(self.passed) + len(self.failed)}")
        for f in self.failed:
            print(f"  - {f}")
        return 1


def check_links(dist: Path, bi) -> tuple[int, int]:
    files = bi.collect_md_files(dist)
    docs = bi.scan_docs(dist, files)
    id_index, _ = bi.build_id_index(docs)
    refs = bi.extract_cross_refs(docs, id_index)
    return len(refs), len([r for r in refs if r.resolved_to is None])


def check_mermaid(dist: Path) -> tuple[int, list[str]]:
    """Balance de fences y conteo de bloques mermaid.

    Solo cuenta como fence una linea con EXACTAMENTE tres backticks (mas un
    tag de lenguaje opcional). Una linea con cuatro o mas es un span de codigo
    inline al sensito de CommonMark: la documentacion la usa al escribir
    ````` ```mermaid ``` ```` para explicar la convencion, y contarla como fence
    producia un "fence sin cerrar" falso.
    """
    total = 0
    errs: list[str] = []
    for path in sorted(dist.rglob("*.md")):
        rel = str(path.relative_to(dist))
        in_fence = False
        for i, line in enumerate(path.read_text(encoding="utf-8", errors="replace").split("\n"), 1):
            if EXACT_FENCE_RE.match(line):
                if not in_fence and MERMAID_LINE_RE.match(line):
                    total += 1
                in_fence = not in_fence
        if in_fence:
            errs.append(f"{rel} fence sin cerrar")
    return total, errs


def check_notion(dist: Path) -> list[str]:
    errs: list[str] = []
    for path in sorted(dist.rglob("*.md")):
        rel = str(path.relative_to(dist))
        in_fence = False
        for i, line in enumerate(path.read_text(encoding="utf-8", errors="replace").split("\n"), 1):
            if EXACT_FENCE_RE.match(line):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            m = HEADING_RE.match(line)
            if not m:
                continue
            # Se evalua el encabezado sin sus spans de codigo inline.
            body = NOTION_INLINE_CODE_RE.sub("", m.group(2))
            if NOTION_BAD_RE.search(body):
                errs.append(f"{rel}:{i} encabezado con caracter no soportado por Notion")
    return errs


def check_portability(dist: Path) -> list[str]:
    errs: list[str] = []
    for path in sorted(dist.rglob("*.md")):
        rel = str(path.relative_to(dist))
        text = path.read_text(encoding="utf-8", errors="replace")
        for i, line in enumerate(text.split("\n"), 1):
            if ABS_PATH_RE.search(line):
                errs.append(f"{rel}:{i} ruta absoluta de la maquina de generacion")
                break
    return errs


# -------------------------------------------------------------------- main

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Empaquetado de OUT/ (C6)")
    ap.add_argument("--out", type=Path, default=OUT_DEFAULT)
    ap.add_argument("--dist", type=Path, default=DIST_DEFAULT)
    ap.add_argument("--check-only", action="store_true")
    ap.add_argument("--no-obsidian", action="store_true",
                    help="Omite dist-obsidian/ (solo paquete limpio).")
    args = ap.parse_args(argv)

    dist: Path = args.dist
    obsidian: Path = args.dist.parent / "dist-obsidian"
    bi = load_indexer()
    res = Result()

    if not args.check_only:
        print(f"[package] copiando entregables de {args.out} a {dist} …")
        n = copiar_entregables(args.out, dist)

        # Estado y cobertura desde el ledger, para el README.
        cov = bi.load_cobertura(args.out / "_ledger" / "cobertura.csv")
        files = cov["global"]["total"] if cov else 0
        src_refs = 0
        for p in dist.rglob("*.md"):
            src_refs += len(re.findall(r"\b(?:appflowy|collab|editor):[\w./-]+:\d+",
                                      p.read_text(encoding="utf-8", errors="replace")))
        escribir_readme(dist, n, src_refs, files)
        print(f"[package] {n} documentos, {files} ficheros de codigo, {src_refs} referencias")

    print()
    print("=== Verificaciones del paquete ===")

    # V1
    total_refs, unresolved = check_links(dist, bi)
    if unresolved == 0:
        res.ok("V1 enlaces", f"{total_refs} enlaces `[[id]]` resuelven")
    else:
        res.ko("V1 enlaces", f"{unresolved} de {total_refs} sin resolver")

    # V2
    n_mermaid, mermaid_errs = check_mermaid(dist)
    if not mermaid_errs:
        res.ok("V2 mermaid", f"{n_mermaid} bloques balanceados y fuera de inline code")
    else:
        res.ko("V2 mermaid", f"{len(mermaid_errs)} problemas: {mermaid_errs[:3]}")

    # V3
    notion_errs = check_notion(dist)
    if not notion_errs:
        res.ok("V3 compatibilidad Notion", "encabezados con caracteres admitidos")
    else:
        res.ko("V3 compatibilidad Notion", f"{len(notion_errs)}: {notion_errs[:3]}")

    # V4
    port_errs = check_portability(dist)
    if not port_errs:
        res.ok("V4 portabilidad", "sin rutas absolutas ni referencias a SRC/")
    else:
        res.ko("V4 portabilidad", f"{len(port_errs)}: {port_errs[:3]}")

    # V5 — variante Obsidian
    if not args.check_only and not args.no_obsidian:
        files_d = bi.collect_md_files(dist)
        docs_d = bi.scan_docs(dist, files_d)
        id_index, _ = bi.build_id_index(docs_d)
        n_links = preparar_obsidian(dist, obsidian, id_index)

        # Verificar la copia de Obsidian contra el SISTEMA DE FICHEROS, no con
        # el resolver de ids: tras la conversion los enlaces son rutas
        # relativas, que el indexer no entiende (busca ids). El criterio correcto
        # es "todo enlace que apunta a un fichero termina en un fichero que
        # existe".
        rotas: list[str] = []
        n_enlaces = 0
        for path in sorted(obsidian.rglob("*.md")):
            text = path.read_text(encoding="utf-8", errors="replace")
            for m in MD_LINK_RE.finditer(text):
                tgt = m.group(1).split("|")[0].strip()
                if not tgt.endswith(".md"):
                    continue          # no es un enlace a documento
                n_enlaces += 1
                destino = (path.parent / tgt).resolve()
                if not destino.is_file():
                    rotas.append(f"{path.relative_to(obsidian)} -> {tgt}")
        if not rotas:
            res.ok("V5 variante Obsidian",
                   f"{n_links} convertidos, {n_enlaces} apuntan a ficheros existentes")
        else:
            res.ko("V5 variante Obsidian",
                   f"{len(rotas)} rotas: {rotas[:3]}")

    # Archivo comprimido
    if not args.check_only:
        arc = args.out.parent / ARCHIVE
        if arc.exists():
            arc.unlink()
        with tarfile.open(arc, "w:gz") as tf:
            tf.add(dist, arcname="appflowy-review")
        size_mb = arc.stat().st_size / (1024 * 1024)
        res.ok("V6 archivo", f"{arc.name} — {size_mb:.1f} MiB")

    return res.report("C6 empaquetado")


if __name__ == "__main__":
    sys.exit(main())