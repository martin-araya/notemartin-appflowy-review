#!/usr/bin/env python3
"""contrast_B5_B2.py — Contraste automático entre los documentos de secuencia
(B5) y los catálogos exhaustivos (B2.1 eventos FFI / B2.4 notificaciones).

Fase C3 · T1.1 del plan `1792619085358-c3-al-cierre-plan.md`.

Por qué existe
-------------
Los 14 documentos de `OUT/15-secuencias-globales/` se escribieron en el Bloque
B5 **sin consultar los catálogos del Bloque B2**. La Fase C1 (pasada global de
validadores) ya encontró 48 referencias rotas en esos documentos, 10 de ellas
retiradas porque el fichero *y* el símbolo no existen en el código. Ese trabajo
era línea a línea; este script hace el cruce sistemático para que el patrón no
se repita: cualquier símbolo Rust tipo `Enum::Variant` que un documento de
secuencia menciona y que no exista en `extract/events.json` ni en
`extract/notifications.json` se reporta como **fabricación**.

Qué NO hace
-----------
- No valida líneas (eso es `validate_evidence.py`, ya en verde desde C1).
- No valida prosa, solo identificadores Rust cualificados (`Foo::Bar`).
- No reescribe documentos: produce un informe que consume el orquestador y, si
  hace falta, el subagente autor de la unidad B5 correspondiente.

Criterio de clasificación
-------------------------
Para cada referencia `Enum::Variant` hallada en un `.md` de B5:

| Resultado  | Significado |
|------------|-------------|
| `OK`       | El enum existe en el catálogo y la variante es suya. |
| `ENUM_DESCONOCIDO` | El enum no existe en ningún catálogo. Fabricación probable. |
| `VARIANTE_DESCONOCIDA` | El enum existe pero esa variante no (el catálogo es exhaustivo por construcción). Fabricación. |
| `AMBIGUO`  | El identificador no parece un símbolo Rust cualificado; se reporta aparte, sin veredicto. |
| `FUERA_DE_CATALOGO` | Símbolo Rust real pero de una familia que los catálogos no cubren (p. ej. `ErrorCode`, tipos de `collab-*`). No es fabricación; se reporta para revisión. |

Idempotente: leer catálogos y escribir informe, sin tocar `SRC/` ni `OUT/` fuera
del directorio de salida que se le pase.

Uso
---
    contrast_B5_B2.py --out-dir OUT/_ledger/pruebas/C3
    contrast_B5_B2.py --out-dir … --check     # sale 1 si hay fabricariones
    contrast_B5_B2.py --out-dir … --doc OUT/15-secuencias-globales/07-subir-imagen.md

Fase C3 de la skill notemartin-appflowy-review.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve()
SKILL_ROOT = SCRIPT_PATH.parent.parent.parent

EXTRACT_DEFAULT = SKILL_ROOT / "OUT" / "_ledger" / "extract"
B5_DEFAULT = SKILL_ROOT / "OUT" / "15-secuencias-globales"
OUT_DIR_DEFAULT = SKILL_ROOT / "OUT" / "_ledger" / "pruebas" / "C3"

# `Enum::Variant` / `Enum::Variant::Deeper` / `Type::method`.
#
# El miembro DEBE admitir mayúscula inicial: las variantes de los enums Rust de
# AppFlowy (`DidUpdateRow`, `ImportCsvData`) son PascalCase y son justamente lo
# que hay que contrastar contra los catálogos. Una versión anterior de este
# regex exigía minúscula inicial, lo que hacía inalcanzable la rama de
# verificación de variantes y dejó pasar 12 fabricaciones de enum en B5.5.
QUALIFIED_RE = re.compile(
    r"\b([A-Z][A-Za-z0-9_]*)::([A-Za-z_][A-Za-z0-9_]*)"
    r"(?:::[A-Z][A-Za-z0-9_]*)?"
)

# Filtro de bloques donde un identificador no es una referencia de símbolo:
# código fenced, tablas de prosa con `Foo::bar` como ejemplo, etc. No se excluyen
# los bloques: una fabricación dentro de un ```rust también es una fabricación.
# Lo que sí se hace es normalizar los prefijos `SRC/` que algunos docs usan.

# Familias de símbolos Rust que los catálogos B2.1/B2.4 no cubren pero cuya
# existencia en el código sí es verificable. Se marcan FUERA_DE_CATALOGO si el
# símbolo aparece en `SRC/`, y AMBIGUO si no aparece en ninguna parte.
FUERA_DE_CATALOGO_PATRONES = (
    "ErrorCode",           # flowy-error/src/code.rs -> B2.5 (15-catalogo-errores.md)
    "FlowyError",          # flowy-error/src/errors.rs
    "AFPlugin",            # lib-dispatch
    "Collab",              # collab-plugins / collab-integrate
    "CollabType",
    "CollabBuilder",
    "EncoderVersion",
    "ViewLayout",
    "FieldType",
    "LocalStorage",
    "CloudStorage",
    "KVAction",
    "EncodedCollab",
    "Block",               # collab-document
    "DocumentData",
    "Row",
    "Cell",
    "Field",
    "View",
    "Workspace",
    "FolderData",
    "ChatMessage",
    "DocumentAwareness",
    "UserAwareness",
)

# Crates externos cuyo API aparece en los docs de secuencia con la sintaxis
# `crate::Tipo::metodo`. No viven en SRC/, así que no se pueden resolver con
# el índice de declaraciones Rust; se aceptan por nombre. `Doc` y `Duration`
# son los casos reales en B5.4/B5.5 (`yrs::Doc::new`,
# `yrs::Doc::transact_with_remote`, `std::time::Duration::from_secs`).
CRATES_EXTERNOS = {
    "std", "core", "alloc", "yrs", "tokio", "serde", "serde_json",
    "csv", "anyhow", "uuid", "chrono", "log", "liblog", "lazy_static",
    "dashmap", "tracing", "reqwest", "http", "url", "futures", "pin_project",
    "protobuf", "async_trait", "once_cell", "regex", "sha2", "bytes",
}

# Tipos cuya resolución depende de un crate externo: `Doc` es `yrs::Doc` en la
# nomenclatura de AppFlowy-Collab.
EXTERNOS_POR_TIPO = {
    "Doc": "yrs::Doc",
    "TransactionMut": "yrs::TransactionMut",
    "ReadTxn": "yrs::ReadTxn",
    "Origin": "yrs::Origin",
    "Out": "yrs::Out",
    "Updates": "yrs::Updates",
    "StateVector": "yrs::StateVector",
    "Duration": "std::time::Duration",
    "Instant": "std::time::Instant",
    "Utc": "chrono::Utc",
    "Arc": "std::sync::Arc",
    "Mutex": "std::sync::Mutex",
    "RwLock": "std::sync::RwLock",
    "HashMap": "std::collections::HashMap",
    "Uuid": "uuid::Uuid",
    # Constantes de `std`, no metodos. `Ordering::SeqCst` es
    # `std::sync::atomic::Ordering::SeqCst` y aparece en `chat.rs:67` al
    # cancelar el streaming.
    "Ordering": "std::sync::atomic::Ordering",
}

# Nombres que aparecen como `Foo::bar` pero son abreviaturas de un documento o
# una referencia a un fichero, no símbolos Rust.
RUINA_RE = re.compile(
    r"^(README|CHANGELOG|Cargo|LICENSE|Makefile|src|lib|tests|bin|doc|docs|"
    r"appflowy|editor|collab|frontend|rust|pubspec|build|target|examples)$"
)

# Patrón del daño que `repair_markdown_damage.py` de C1 no cubrió: un prefijo de
# fuente duplicado dentro de un span de `inline code`. Ejemplo real en B5.11:
#   ``collab:`collab:`collab:collab/collab-importer/src/zip_tool/async_zip.rs:1`` ``
SPAN_DANADO_RE = re.compile(
    r"`[^`\n]*`"                                  # span de inline code
    r"(?P<cuerpo>[^`\n]*)"
)
PREFIJO_FUENTE_RE = re.compile(r"\b(appflowy|collab|editor)\s*:")

# Firma exacta del daño que dejó `fix_evidence_prefix.py` y que
# `repair_markdown_damage.py` (C1) no cubrió: el prefijo de fuente **duplicado**
# dentro de una misma línea, con un acento grave intercalado entre las dos
# apariciones.
#
# Sano:      `` `appflowy:frontend/rust-lib/flowy-search/src/lib.rs:1` ``
# Sano:      ``con el prefijo `appflowy:` ``   ← prosa legítima, una sola vez
# Dañado A:  ``collab:`collab:`collab:collab/collab-importer/… ``   (B5.11:159)
# Dañado B:  ````editor:`editor:editor/lib/… ````                   (B5.10:133)
#
# La clave discriminante es la **repetición**: `repair_markdown_damage.py`
# absorbió el prefijo y lo duplicó, así que el patrón siempre aparece dos veces
# seguidas. La prosa que menciona un prefijo una vez no se toca.
SPAN_DUPLICADO_RE = re.compile(
    r"`(appflowy|collab|editor)\s*:`\s*`\s*\1\s*:"   # `collab:`collab:
    r"|`+\s*(appflowy|collab|editor)\s*:\s*`{1,2}\s*\2\s*:"  # ``editor:`editor:
)


@dataclass
class Ref:
    doc: str
    linea: int
    simbolo: str          # "Enum::Variant"
    enum_nombre: str
    variante: str
    resultado: str
    detalle: str = ""


@dataclass
class Catalogo:
    """Índices planos que se consultan en O(1) por referencia."""

    enums_evento: dict[str, dict] = field(default_factory=dict)      # Enum -> {crate, variants:set, ...}
    variantes_evento: dict[tuple[str, str], dict] = field(default_factory=dict)
    enums_notif: dict[str, dict] = field(default_factory=dict)
    variantes_notif: dict[tuple[str, str], dict] = field(default_factory=dict)
    eventos_registrados: set[str] = field(default_factory=set)
    eventos_sin_handler: set[str] = field(default_factory=set)
    rust_sym_known: set[str] = field(default_factory=set)            # símbolos Cargo.toml [[bin]]/crates


def load_catalogos(extract_dir: Path) -> Catalogo:
    cat = Catalogo()

    events = json.loads((extract_dir / "events.json").read_text(encoding="utf-8"))
    for cr in events.get("crates", []):
        enum_name = (cr.get("enum") or {}).get("name")
        crate = cr.get("crate")
        if not enum_name:
            continue
        variants = {v["name"]: v for v in cr.get("variants", [])}
        cat.enums_evento[enum_name] = {"crate": crate, "variants": variants}
        for name, v in variants.items():
            cat.variantes_evento[(enum_name, name)] = v
            full = f"{enum_name}::{name}"
            if v.get("sin_handler"):
                cat.eventos_sin_handler.add(full)
            else:
                cat.eventos_registrados.add(full)

    notif = json.loads((extract_dir / "notifications.json").read_text(encoding="utf-8"))
    for en in notif.get("rust_notifications", []):
        name = en.get("name")
        if not name:
            continue
        variants = {v["name"]: v for v in en.get("variants", [])}
        cat.enums_notif[name] = {"crate": en.get("crate"), "variants": variants}
        for vname, v in variants.items():
            cat.variantes_notif[(name, vname)] = v

    return cat


def _build_rust_symbol_index() -> set[str]:
    """Índice de símbolos Rust declarados en SRC/ para clasificar FUERA_DE_CATALOGO.

    Deliberadamente barato: se collects una sola vez y se usa solo para
    desambiguar referencias que los catálogos no cubren. Se limita a nombres de
    tipo (`struct X`, `enum X`, `trait X`, `type X`) y miembros de enum que ya
    estén en los catálogos.
    """
    idx: set[str] = set()
    src = SKILL_ROOT / "SRC"
    if not src.is_dir():
        return idx
    decl = re.compile(r"^\s*(?:pub(?:\([^)]*\))?\s+)?(?:struct|enum|trait|type)\s+([A-Z][A-Za-z0-9_]*)")
    for rs in src.rglob("*.rs"):
        if "/.git" in str(rs):
            continue
        try:
            with rs.open(encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    m = decl.match(line)
                    if m:
                        idx.add(m.group(1))
        except OSError:
            continue
    return idx


def clasificar(ref_enum: str, ref_var: str, cat: Catalogo, rust_idx: set[str]) -> tuple[str, str]:
    """Devuelve (resultado, detalle) para un par Enum::Variant.

    La distinción decisiva es el **miembro**, no el tipo:

    - miembro en PascalCase (`DidUpdateRow`, `ImportZip`) → variante de enum.
      Los catálogos B2.1/B2.4 son exhaustivos por construcción (299 variantes,
      0 empiezan por minúscula), así que un veredicto negativo es una
      fabricación, no un falso negativo del clasificador.
    - miembro en camelCase/snake_case (`new`, `decode`, `from_secs`) → llamada
      a método o función asociada. No es una variante, se resuelve aparte.
    """
    if RUINA_RE.match(ref_enum):
        return "AMBIGUO", "prefijo de ruta, no símbolo Rust"

    # Tipos que resuelven a un crate externo. Se comprueba ANTES que los
    # catálogos porque cubre dos casos con la misma sintaxis: metodos
    # (`Arc::new`) y constantes (`Ordering::SeqCst`), y estas ultimas empiezan
    # por mayuscula igual que una variante de enum.
    if ref_enum in EXTERNOS_POR_TIPO:
        return "EXTERNO", f"`{ref_enum}::{ref_var}` resuelve a {EXTERNOS_POR_TIPO[ref_enum]}"
    if ref_enum in CRATES_EXTERNOS:
        return "EXTERNO", f"crate externo `{ref_enum}` (no está en SRC/)"

    # --- miembro PascalCase: variante de enum, veredicto duro --------------
    if ref_var[0].isupper():
        if ref_enum in cat.enums_evento:
            v = cat.enums_evento[ref_enum]["variants"].get(ref_var)
            if v:
                sin = " (declarada sin handler)" if v.get("sin_handler") else ""
                return "OK", f"evento FFI en {cat.enums_evento[ref_enum]['crate']}{sin}"
            return (
                "VARIANTE_DESCONOCIDA",
                f"{ref_enum} existe ({cat.enums_evento[ref_enum]['crate']}) pero no declara "
                f"la variante `{ref_var}`; variantes reales: "
                f"{sorted(cat.enums_evento[ref_enum]['variants'])[:6]}…",
            )

        if ref_enum in cat.enums_notif:
            v = cat.enums_notif[ref_enum]["variants"].get(ref_var)
            if v:
                return "OK", f"notificación en {cat.enums_notif[ref_enum]['crate']}"
            return (
                "VARIANTE_DESCONOCIDA",
                f"{ref_enum} existe ({cat.enums_notif[ref_enum]['crate']}) pero solo tiene "
                f"{len(cat.enums_notif[ref_enum]['variants'])} variantes: "
                f"{sorted(cat.enums_notif[ref_enum]['variants'])}",
            )

        if ref_enum in rust_idx or ref_enum in FUERA_DE_CATALOGO_PATRONES:
            return "FUERA_DE_CATALOGO", "símbolo Rust real, familia fuera de B2.1/B2.4"

        return (
            "ENUM_DESCONOCIDO",
            f"ni evento FFI ni notificación ni declaración Rust llamada `{ref_enum}`",
        )

    # --- miembro en minúscula: método/función, no variante ------------------
    if ref_enum in cat.enums_evento or ref_enum in cat.enums_notif or ref_enum in rust_idx:
        return "METODO_PROPIO", f"`{ref_enum}` es un tipo del repo; `{ref_var}` es un método suyo"
    return (
        "ENUM_DESCONOCIDO",
        f"ni tipo declarado ni crate externo conocido para `{ref_enum}::{ref_var}`",
    )


def escanear_spans_danados(path: Path, rel: str) -> list[Ref]:
    """Detecta spans de inline code con prefijo de fuente duplicado o anidado.

    `repair_markdown_damage.py` (C1) reparó 98 spans, pero solo cuando el
    síntoma era Markdown inválido. Quedan spans que **resuelven** como ruta y
    por tanto no los ve ningún validador, pero cuyo prefijo o camino está mal.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    out: list[Ref] = []
    for i, line in enumerate(text.splitlines(), start=1):
        if SPAN_DUPLICADO_RE.search(line):
            n_pref = len(PREFIJO_FUENTE_RE.findall(line))
            out.append(Ref(
                doc=rel, linea=i,
                simbolo=line.strip()[:110],
                enum_nombre="(span)", variante="",
                resultado="SPAN_DANADO",
                detalle=f"prefijo de fuente duplicado ({n_pref} apariciones) con un acento "
                        f"grave intercalado. Ningún validador lo ve: el span resuelve como "
                        f"ruta, así que `validate_evidence` lo acepta, y el Markdown lo "
                        f"renderiza como texto plano en vez de código.",
            ))
    return out


def escanear_doc(path: Path, cat: Catalogo, rust_idx: set[str], rel: str) -> list[Ref]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    refs: list[Ref] = []
    for i, line in enumerate(text.splitlines(), start=1):
        for m in QUALIFIED_RE.finditer(line):
            enum_nombre, variante = m.group(1), m.group(2)
            if enum_nombre == variante:
                continue
            res, det = clasificar(enum_nombre, variante, cat, rust_idx)
            refs.append(
                Ref(
                    doc=rel,
                    linea=i,
                    simbolo=f"{enum_nombre}::{variante}",
                    enum_nombre=enum_nombre,
                    variante=variante,
                    resultado=res,
                    detalle=det,
                )
            )
    return refs


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Contraste B5 × B2 (C3/T1.1)")
    ap.add_argument("--extract-dir", type=Path, default=EXTRACT_DEFAULT)
    ap.add_argument("--b5-dir", type=Path, default=B5_DEFAULT)
    ap.add_argument("--out-dir", type=Path, default=OUT_DIR_DEFAULT)
    ap.add_argument("--doc", type=Path, action="append", default=[],
                    help="Restringe el escaneo a estos .md (repetible).")
    ap.add_argument("--sweep-root", type=Path, default=None,
                    help="En vez de escanear B5, barre todos los .md bajo esta raíz "
                         "buscando solo daño de span. Sirve para medir precisión del "
                         "detector sobre documentos sanos (debe dar 0 falsos positivos).")
    ap.add_argument("--check", action="store_true",
                    help="Sale 1 si hay fabricariones (ENUM/VARIANTE_DESCONOCIDA).")
    ap.add_argument("--json", action="store_true", dest="as_json")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    if not args.extract_dir.is_dir():
        print(f"ERROR: no existe {args.extract_dir}", file=sys.stderr)
        return 2

    cat = load_catalogos(args.extract_dir)
    rust_idx = _build_rust_symbol_index()

    docs = args.doc or sorted(args.b5_dir.glob("*.md"))
    solo_spans = args.sweep_root is not None
    if solo_spans:
        docs = sorted(args.sweep_root.rglob("*.md"))
    all_refs: list[Ref] = []
    for d in docs:
        p = Path(d)
        if not p.is_absolute():
            p = (args.b5_dir / p.name) if not p.exists() else p
        rel = str(p.relative_to(SKILL_ROOT)) if str(p).startswith(str(SKILL_ROOT)) else str(p)
        if not solo_spans:
            all_refs.extend(escanear_doc(p, cat, rust_idx, rel))
        all_refs.extend(escanear_spans_danados(p, rel))

    # Filas del CSV: todo lo que tenga veredicto negativo o que merezca revisión.
    filas = [r for r in all_refs if r.resultado in
             ("ENUM_DESCONOCIDO", "VARIANTE_DESCONOCIDA", "FUERA_DE_CATALOGO", "SPAN_DANADO")]

    conteo = Counter(r.resultado for r in all_refs)
    fabricar = [r for r in all_refs
                if r.resultado in ("ENUM_DESCONOCIDO", "VARIANTE_DESCONOCIDA", "SPAN_DANADO")]

    # Un enum desconocido se cuenta una sola vez por (doc, simbolo) para el
    # informe; el CSV sí conserva cada ocurrencia con su línea.
    unicos = {}
    for r in fabricar:
        unicos.setdefault((r.doc, r.simbolo), r)

    por_doc = defaultdict(list)
    for r in fabricar:
        por_doc[r.doc].append(r.simbolo)

    args.out_dir.mkdir(parents=True, exist_ok=True)

    csv_path = args.out_dir / "contrast_B5_B2.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["documento", "linea", "simbolo", "enum", "variante", "resultado", "detalle"])
        for r in sorted(filas, key=lambda x: (x.doc, x.linea)):
            w.writerow([r.doc, r.linea, r.simbolo, r.enum_nombre, r.variante, r.resultado, r.detalle])

    resumen = {
        "schema_version": 1,
        "generado_en": __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
                       .strftime("%Y-%m-%dT%H:%M:%SZ"),
        "docs_escaneados": len(docs),
        "referencias_totales": len(all_refs),
        "por_resultado": dict(conteo),
        "fabricaciones_total": len(fabricar),
        "fabricaciones_unicas": len(unicos),
        "enums_desconocidos_unicos": sorted({r.enum_nombre for r in fabricar
                                             if r.resultado == "ENUM_DESCONOCIDO"}),
        "por_doc": {doc: sorted(set(syms)) for doc, syms in sorted(por_doc.items())},
        "detalle": [{"doc": r.doc, "linea": r.linea, "simbolo": r.simbolo,
                     "resultado": r.resultado, "detalle": r.detalle}
                    for r in sorted(fabricar, key=lambda x: (x.doc, x.linea, x.simbolo))],
    }
    json_path = args.out_dir / "contrast_B5_B2.json"
    json_path.write_text(json.dumps(resumen, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if not args.quiet:
        print(f"[contrast] docs={len(docs)} refs={len(all_refs)} "
              f"fabricaciones={len(fabricar)} (unicas={len(unicos)})")
        for k, v in sorted(conteo.items(), key=lambda x: -x[1]):
            print(f"  {k:22} {v}")
        if fabricar:
            print("[contrast] fabricaciones por doc:")
            for doc, syms in sorted(por_doc.items()):
                print(f"  {doc}")
                for s in sorted(set(syms)):
                    print(f"    - {s}")
        print(f"[contrast] csv={csv_path}")
        print(f"[contrast] json={json_path}")

    if args.check and fabricar:
        print(f"FAIL: {len(fabricar)} fabricacion(es) B5 x B2", file=sys.stderr)
        return 1
    if args.as_json:
        print(json.dumps(resumen, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())