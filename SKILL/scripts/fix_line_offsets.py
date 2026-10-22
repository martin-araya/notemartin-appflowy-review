#!/usr/bin/env python3
"""fix_line_offsets.py — resuelve las referencias de evidencia rotas de `OUT/`
decidiendo, una a una, si la línea se movió al escribir el documento o la cita
era errónea (deuda que B6 dejó explícita para C1, ROADMAP.md:705).

Tres capas, todas deterministas y auditables. Ninguna reescribe una línea sin
poder explicar **por qué** en el CSV de salida.

Capa 1 — `path_migrations.json`
    Mapa explícito `de → para` para rutas que se movieron o que se citaron mal
    (fichero inexistente). Si la ruta citada está en el mapa, se aplica y punto.

Capa 2 — `basename` + ancla de contexto
    Para rutas como `event_handler.rs:147` (sin directorio) hay 8 candidatos en
    el inventario. Se extraen **anclas** (identificadores entre backticks) de la
    línea del `.md` y sus 2 anteriores, y se descartan los candidatos cuyo texto
    no contenga el ancla. Si queda exactamente uno, es la ruta correcta.

Capa 3 — búsqueda global por ancla
    Para citas que apuntan a un fichero que **no existe** pero cuyo símbolo sí
    (`collab/collab/src/lib.rs:240` para `EncodedCollab`), se busca el ancla en
    todo el inventario. Si un único fichero la contiene, se repunta la cita.

Resolución de la línea
    Una vez elegida la ruta, la línea se recalcula localizando el ancla dentro
    del fichero (coincidencia exacta de palabra completa). Si hay varias, se
    elige la más próxima a la línea citada. El rango `inicio–fin` se preserva
    con su amplitud cuando cabe en el fichero.

Salida
    `--csv-dir DIR` escribe tres ficheros:
      `refs_resueltas.csv`  decisiones aplicadas con su justificación
      `refs_ambiguas.csv`    decisiones que requieren humano
      `refs_sin_ancla.csv`   citas cuyo fichero no existe en el snapshot

Idempotente: Applied twice changes nothing (la segunda pasada no encuentra
referencias rotas).

Uso
    python3 fix_line_offsets.py --dry-run --csv-dir OUT/_ledger/pruebas/C1
    python3 fix_line_offsets.py --apply --csv-dir OUT/_ledger/pruebas/C1
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
INVENTARIO = PROJECT_ROOT / "OUT" / "_ledger" / "inventario.json"
MIGRACIONES = SCRIPT_DIR / "path_migrations.json"

VALID_FUENTES = ("appflowy", "collab", "editor")
DEFAULT_FUENTE = "appflowy"

RE_REF = re.compile(
    r"(?P<pre>`+)"
    r"(?:(?P<fuente>appflowy|collab|editor):)?"
    r"(?P<ruta>[A-Za-z0-9_][A-Za-z0-9_./\-]*\.[A-Za-z0-9]+)"
    r":(?P<linea>\d+)"
    r"(?:(?P<sep>[–\-])(?P<fin>\d+))?"
    r"(?P<post>`+)"
)
RE_REF_SIMPLE = re.compile(
    r"(?:(?P<fuente>appflowy|collab|editor):)?"
    r"(?P<ruta>[A-Za-z0-9_][A-Za-z0-9_./\-]*\.[A-Za-z0-9]+)"
    r":(?P<linea>\d+)(?:(?P<sep>[–\-])(?P<fin>\d+))?"
)

# Identificadores utilizables como ancla.
STOPWORDS = {
    "appflowy", "collab", "editor", "rust", "dart", "flutter", "src", "lib",
    "linea", "lineas", "doc", "docs", "ref", "refs", "rust_lib", "flowy_core",
    "self", "super", "crate", "impl", "pub", "fn", "let", "const", "static",
    "class", "enum", "struct", "type", "return", "void", "true", "false", "null",
    "this", "new", "old", "the", "and", "not", "for", "with", "from", "into",
    "get", "set", "add", "remove", "update", "create", "delete", "load", "save",
    "main", "init", "data", "value", "name", "path", "file", "files", "code",
    "text", "line", "note", "none", "some", "all", "any", "one", "two", "usa",
    "usa", "solo", "como", "cada", "este", "esta", "este", "caso", "parte",
}
RE_ANCLA_FN = re.compile(r"\b[a-z][a-z0-9]*(?:_[a-z0-9]+){1,}\b")
RE_ANCLA_TIPO = re.compile(r"\b[A-Z][A-Za-z0-9]*(?:::[A-Za-z0-9_]+)+\b")
RE_ANCLA_CLASE = re.compile(r"\b[A-Z][A-Za-z0-9]{3,}\b")


# --- Inventario -------------------------------------------------------------


class Inventario:
    def __init__(self, path: Path):
        data = json.loads(path.read_text(encoding="utf-8"))
        entradas = data["files"] if isinstance(data, dict) and "files" in data else data
        self.por_clave: dict[tuple[str, str], dict] = {}
        self.por_basename: dict[str, list[tuple[str, str]]] = defaultdict(list)
        self._texto: dict[tuple[str, str], list[str]] = {}
        for e in entradas:
            if not isinstance(e, dict):
                continue
            f, r = e.get("fuente"), e.get("ruta_rel")
            if not f or not r:
                continue
            self.por_clave[(f, r)] = e
            self.por_basename[r.rsplit("/", 1)[-1]].append((f, r))

    def existe(self, fuente: str, ruta_rel: str) -> bool:
        return (fuente, ruta_rel) in self.por_clave

    def texto(self, clave: tuple[str, str]) -> list[str]:
        if clave not in self._texto:
            abs_path = self.por_clave[clave].get("ruta_abs")
            try:
                self._texto[clave] = Path(abs_path).read_text(
                    encoding="utf-8", errors="replace"
                ).splitlines()
            except OSError:
                self._texto[clave] = []
        return self._texto[clave]

    def buscar(self, clave: tuple[str, str], ancla: str) -> list[int]:
        """Líneas (1-based) donde `ancla` aparece como palabra completa."""
        pat = re.compile(rf"\b{re.escape(ancla)}\b")
        return [i for i, ln in enumerate(self.texto(clave), 1) if pat.search(ln)]

    def buscar_todos(self, ancla: str, limite: int = 40) -> list[tuple[str, str]]:
        """Claves del inventario cuyo texto contiene `ancla`."""
        pat = re.compile(rf"\b{re.escape(ancla)}\b")
        out: list[tuple[str, str]] = []
        for clave in self.por_clave:
            if pat.search("\n".join(self.texto(clave))):
                out.append(clave)
                if len(out) >= limite:
                    break
        return out


# --- Migraciones ------------------------------------------------------------


def cargar_migraciones(path: Path) -> tuple[dict[str, str | None], dict[str, int | None]]:
    """Devuelve ({de: para}, {de: linea_forzada}).

    `para: null` significa "retirar la cita": el fichero citado no existe y el
    símbolo tampoco. `linea` fija la línea destino cuando la del documento no
    se puede derivar del código (p. ej. el nombre del handler difiere del
    nombre del evento).
    """
    if not path.exists():
        return {}, {}
    data = json.loads(path.read_text(encoding="utf-8"))
    out: dict[str, str | None] = {}
    lineas: dict[str, int | None] = {}
    for m in data.get("migraciones", []):
        de = m["de"]
        if de.startswith(("appflowy:", "collab:", "editor:")):
            de = de.split(":", 1)[1]
        out[de] = m["para"]
        if m.get("linea") is not None:
            lineas[de] = int(m["linea"])
    return out, lineas


# --- Anchas -----------------------------------------------------------------


def crate_de(ruta_rel: str) -> str:
    """Prefijo del crate/módulo al que pertenece un fichero del inventario.

    `appflowy/frontend/rust-lib/flowy-storage/src/event_handler.rs` →
    `appflowy/frontend/rust-lib/flowy-storage`.
    """
    partes = ruta_rel.split("/")
    for ancla in ("src", "lib", "tests", "test"):
        if ancla in partes:
            return "/".join(partes[: partes.index(ancla)])
    return "/".join(partes[:-1])


def buscar_en_crate(
    inv: Inventario, ruta_rel: str, anclas: list[str]
) -> tuple[tuple[str, str] | None, int | None, str]:
    """Reapunta una cita al único fichero **del mismo crate** que declara el
    símbolo. Es la última red antes de retirar la cita: si la línea está fuera
    de rango y el fichero citado no menciona el símbolo, casi siempre el autor
    apontou al fichero equivocado del crate equivocado."""
    prefijo = crate_de(ruta_rel)
    alcance = [c for c in inv.por_clave if c[1].startswith(prefijo + "/")]
    if not alcance:
        return None, None, "sin_crate"
    for tok in ordenar_tokens(inv, anclas, alcance):
        declaradores = [c for c in alcance if es_declaracion(inv, c, tok)]
        if len(declaradores) == 1:
            clave = declaradores[0]
            hits = inv.buscar(clave, tok)
            if hits:
                return clave, hits[0], f"crate_scope:{tok}"
    return None, None, "sin_declaracion_en_crate"


def tokens_de(ancla: str) -> list[str]:
    """Parte el ancla en los tokens buscables dentro del código fuente.

    `DatabaseEditor::new` → ['DatabaseEditor', 'new']; `publish_view_handler` →
    ['publish_view_handler']. El código fuente no suele escribir la forma
    `Tipo::metodo` (Rust usa `impl` + `fn`), así que se busca por tokens sueltos.
    """
    partes = re.split(r"::|\(|\)|\.|\s+", ancla)
    return [p for p in partes if len(p) >= 4 and p not in STOPWORDS]


def tokens_ordenados(ancla: str) -> list[str]:
    """Tokens en orden de especificidad decreciente: el **tipo** primero.

    Cada crate Rust define su propio `initialize_after_open_workspace`, así que
    ese token no discrimina; el `FolderManager` de `FolderManager::initialize_
    after_open_workspace` sí. Por eso `Tipo::metodo` se parte poniendo la parte
    anterior a `::` delante.
    """
    if "::" in ancla:
        cabeza, _, cola = ancla.partition("::")
        orden = tokens_de(cabeza) + tokens_de(cola)
    else:
        orden = tokens_de(ancla)
    vistos: list[str] = []
    for t in orden:
        if t not in vistos:
            vistos.append(t)
    return vistos


def token_principal(ancla: str) -> str | None:
    toks = tokens_ordenados(ancla)
    return toks[0] if toks else None


def anclas_de_linea(linea: str, excluir: set[str]) -> list[str]:
    """Identificadores candidatos de la línea, del más específico al menos.

    Se recoge primero lo que va entre backticks (que es como el autor nombra
    los símbolos) y después el texto llano. `excluir` contiene los tokens de la
    propia referencia (`ruta:línea`) para no usarlos como ancla.
    """
    fuera: set[str] = set()
    for r in excluir:
        fuera.update(re.findall(r"[A-Za-z_][A-Za-z0-9_:]*", r))

    spans = re.findall(r"`+([^`\n]+)`+", linea)
    candidatos: list[str] = []
    for fuente_texto in (" ".join(spans), re.sub(r"`[^`]*`", " ", linea)):
        for pat in (RE_ANCLA_TIPO, RE_ANCLA_FN, RE_ANCLA_CLASE):
            for tok in pat.findall(fuente_texto):
                base = tok.split("::")[0]
                if tok in fuera or base in fuera:
                    continue
                if base in STOPWORDS or len(base) < 5 or base.isdigit():
                    continue
                if tok not in candidatos:
                    candidatos.append(tok)
        if candidatos:
            break
    return candidatos[:8]


def contexto(lineas: list[str], idx: int, radio: int = 2) -> str:
    lo = max(0, idx - radio)
    hi = min(len(lineas), idx + 1)
    return "\n".join(lineas[lo:hi])


# --- Resolución -------------------------------------------------------------


RE_DECLARACION = {
    "rs": r"\b(?:pub(?:\([^)]*\))?\s+)?(?:async\s+)?(?:fn|struct|enum|trait|impl|type|const|static|mod)\s+{t}\b|\bimpl(?:<[^>]*>)?\s+{t}\b",
    "dart": r"\b(?:abstract\s+)?class\s+{t}\b|\bmixin\s+{t}\b|\bextension\s+{t}\b|\b(?:enum|typedef)\s+{t}\b|{t}\s*(?:\(|\{{)",
}


def es_declaracion(inv: "Inventario", clave: tuple[str, str], tok: str) -> bool:
    """¿`tok` se *declara* en el fichero (no solo se menciona)?

    Un nombre de variable (`folder_manager`) aparece en media docena de crates;
    un nombre de función o tipo (`read_current_workspace_handler`) casi nunca.
    Para desambiguar basenames sólo sirven los segundos.
    """
    ext = Path(inv.por_clave[clave]["ruta_abs"]).suffix.lstrip(".")
    plantilla = RE_DECLARACION.get(ext, RE_DECLARACION["rs"])
    pat = re.compile(plantilla.format(t=re.escape(tok)))
    return any(pat.search(ln) for ln in inv.texto(clave))


def ordenar_tokens(inv: "Inventario", anclas: list[str], candidatos: list[tuple[str, str]]) -> list[str]:
    """Tokens de las anclas, del más discriminante al menos.

    Un token que **declara** algo en exactamente un candidato vale mucho más
    que uno que se menciona en los ocho: `read_current_workspace_handler`
    identifica `flowy-folder/src/event_handler.rs`, mientras que `FlowyError`
    —que el documento menciona en la misma frase— no dice nada.
    """
    puntuaciones: list[tuple[int, int, str]] = []
    vistos: set[str] = set()
    for ancla in anclas:
        for tok in tokens_ordenados(ancla):
            if tok in vistos:
                continue
            vistos.add(tok)
            decl = sum(1 for c in candidatos if es_declaracion(inv, c, tok))
            if decl:
                puntuaciones.append((0, decl, tok))
                continue
            hits = sum(1 for c in candidatos if inv.buscar(c, tok))
            puntuaciones.append((1, hits if hits else 999, tok))
    puntuaciones.sort()
    return [t for _p, _n, t in puntuaciones]


def deprioritar_tests(candidatos: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Quita los candidatos de `tests/` cuando queda alguno de producción.

    `database_editor.rs` existe tanto en `src/services/database/` como en
    `tests/database/`. Cuando el documento describe comportamiento en
    ejecución, el fichero de producción es el correcto.
    """
    prod = [c for c in candidatos if "/tests/" not in c[1] and "/test/" not in c[1]]
    return prod or candidatos


def _buscar_migracion(
    inv: Inventario, migraciones: dict[str, str | None], ruta: str, f: str
) -> tuple[tuple[str, str] | None, str, bool, str | None]:
    """Aplica el mapa de migraciones a `ruta`. Devuelve además la clave usada."""
    clave_mig = ruta.split("/", 1)[1] if ruta.startswith(f"{f}/") else ruta
    if clave_mig not in migraciones:
        return None, "sin_migracion", False, None
    destino = migraciones[clave_mig]
    if destino is None:
        return None, "retirar:simbolo_inexistente", True, clave_mig
    for cand_f in VALID_FUENTES:
        if inv.existe(cand_f, destino):
            return (cand_f, destino), "migracion", False, clave_mig
    return None, f"migracion_destino_ausente:{destino}", False, clave_mig


def _clave_migracion(
    migraciones: dict[str, str | None], ruta: str, f: str
) -> tuple[str | None, str | None]:
    """Devuelve (clave_del_mapa, destino) para `ruta`, o (None, None)."""
    clave_mig = ruta.split("/", 1)[1] if ruta.startswith(f"{f}/") else ruta
    if clave_mig not in migraciones:
        return None, None
    return clave_mig, migraciones[clave_mig]


def resolver_ruta(
    inv: Inventario,
    fuente: str | None,
    ruta: str,
    anclas: list[str],
    migraciones: dict[str, str | None],
) -> tuple[tuple[str, str] | None, str, bool, str | None]:
    """Devuelve ((fuente, ruta_rel), motivo, retirar, clave_migracion).

    `retirar=True` marca las citas que deben desaparecer del documento: el
    fichero y el símbolo citados no existen en el snapshot, y según
    `AGENTS.md §6` está prohibido inventarlos.
    """
    f = fuente or DEFAULT_FUENTE

    # (a) Ya está en el inventario, con o sin prefijo de fuente.
    for cand_f in VALID_FUENTES:
        if cand_f != f:
            continue
        if inv.existe(cand_f, ruta):
            return (cand_f, ruta), "ya_resuelto", False, None
        if inv.existe(cand_f, f"{cand_f}/{ruta}"):
            return (cand_f, f"{cand_f}/{ruta}"), "ya_resuelto", False, None

    base = ruta.rsplit("/", 1)[-1]

    # (b) Basename + anclas de contexto: descarta los candidatos cuyo texto no
    #     contiene el símbolo que el documento nombra en la misma frase.
    candidatos = list(inv.por_basename.get(base, []))
    if not candidatos and "/" in ruta:
        sufijo = ruta.rsplit("/", 1)[-1]
        candidatos = [c for c in inv.por_basename.get(sufijo, []) if "/" + sufijo in c[1]]
    if len(candidatos) > 1:
        candidatos = deprioritar_tests(candidatos)
    if len(candidatos) > 1 and anclas:
        for tok in ordenar_tokens(inv, anclas, candidatos):
            # Un token sólo discrimina si el candidato lo **declara**.
            declaradores = [
                c for c in candidatos if es_declaracion(inv, c, tok)
            ]
            candidatos_fuente = declaradores or candidatos
            filtrados = [c for c in candidatos_fuente if inv.buscar(c, tok)]
            if not filtrados:
                continue
            if len(filtrados) == 1:
                return filtrados[0], f"basename+ancla:{tok}", False, None
            # Se conservan los filtrados y se sigue con el siguiente token:
            # la intersección suele dejar un único candidato.
            candidatos = deprioritar_tests(filtrados)
    if len(candidatos) == 1:
        return candidatos[0], "basename_unico", False, None
    if len(candidatos) > 1:
        # Las anclas no discriminan: antes de declarar ambigüedad se consulta el
        # mapa de migraciones, que puede fijar el destino de un basename común
        # (`notification.rs`, `event_handler.rs`, `document_event.rs`).
        clave, motivo, retirar, kmig = _buscar_migracion(inv, migraciones, ruta, f)
        if kmig:
            return clave, f"{motivo}_tras_ambiguedad", retirar, kmig
        return None, f"ambigua:{len(candidatos)}_candidatos", False, None

    # (c) Mapa explícito de migraciones (rutas movidas o citadas inexistentes).
    clave, motivo, retirar, kmig = _buscar_migracion(inv, migraciones, ruta, f)
    if kmig:
        return clave, motivo, retirar, kmig

    # (d) Búsqueda global por ancla: el fichero citado no existe.
    for ancla in anclas:
        tok = token_principal(ancla)
        if not tok:
            continue
        hits = inv.buscar_todos(tok, limite=8)
        if len(hits) == 1:
            return hits[0], f"ancla_global:{ancla}", False, None
    return None, "sin_candidato", False, None


def resolver_linea(
    inv: Inventario,
    clave: tuple[str, str],
    linea: int,
    anclas: list[str],
    forzada: int | None = None,
) -> tuple[int | None, str]:
    total = len(inv.texto(clave))
    # Gate final: si **ningún** token del ancla aparece en el fichero destino, la
    # cita no describe nada real de ese fichero aunque la línea exista. Es el
    # caso de los símbolos inventados (`FileUploadProgress`, `DidPublishView`):
    # la ruta se resuelve pero el símbolo no existe (AGENTS.md §6).
    if not forzada and not any(
        inv.buscar(clave, tok)
        for ancla in anclas
        for tok in tokens_ordenados(ancla)
    ):
        return None, "simbolo_inexistente_en_el_fichero"
    if 1 <= linea <= total:
        return linea, "en_rango"
    for ancla in anclas:
        for tok in tokens_ordenados(ancla):
            hits = inv.buscar(clave, tok)
            if hits:
                mejor = min(hits, key=lambda h: (abs(h - linea), h))
                sufijo = "" if len(hits) == 1 else f",{len(hits)}_hits"
                return mejor, f"ancla:{tok}{sufijo}"
    return None, "sin_ancla"


# --- Recorrido de un documento ---------------------------------------------


def procesar_documento(
    doc: Path,
    inv: Inventario,
    migraciones: dict[str, str | None],
    lineas_mig: dict[str, int | None],
    dry_run: bool,
) -> list[dict]:
    lineas = doc.read_text(encoding="utf-8").splitlines()
    registros: list[dict] = []
    cambios: list[tuple[int, int, int, str]] = []  # (start, end, doc_line, nuevo)

    for i, linea in enumerate(lineas):
        if linea.lstrip().startswith("```"):
            continue
        for m in RE_REF.finditer(linea):
            fuente, ruta = m.group("fuente"), m.group("ruta")
            linea_citada = int(m.group("linea"))
            fin_citado = int(m.group("fin")) if m.group("fin") else None
            ancho = (fin_citado - linea_citada) if fin_citado else 0

            f = fuente or DEFAULT_FUENTE
            linea_fuera_de_rango = False
            clave_directa = None
            if inv.existe(f, ruta):
                clave_directa = (f, ruta)
            elif inv.existe(f, f"{f}/{ruta}"):
                clave_directa = (f, f"{f}/{ruta}")
            if clave_directa is not None:
                # La ruta existe: solo intervene si la línea citada se sale del
                # fichero (`E_LINE_OUT_OF_RANGE`), nunca para reescribir rutas.
                total = len(inv.texto(clave_directa))
                if 1 <= linea_citada <= total and (
                    fin_citado is None or fin_citado <= total
                ):
                    continue
                linea_fuera_de_rango = True

            ctx = contexto(lineas, i)
            propias = anclas_de_linea(linea, {ruta, m.group(0)})
            anclas = propias + [
                a for a in anclas_de_linea(ctx, {ruta, m.group(0)}) if a not in propias
            ]
            clave, motivo_ruta, retirar, kmig = resolver_ruta(
                inv, fuente, ruta, anclas, migraciones
            )

            base = {
                "doc": str(doc),
                "doc_line": i + 1,
                "ref_original": m.group(0).strip("`"),
                "anclas": ";".join(anclas[:4]),
                "motivo_ruta": motivo_ruta,
            }
            if retirar:
                marca = "`[NO DETERMINADO]` (ver `22-preguntas-abiertas.md § C1`)"
                base.update(
                    decision="retirada",
                    ref_nuevo=marca,
                    motivo_linea="simbolo_inexistente_en_el_snapshot",
                )
                registros.append(base)
                cambios.append((m.start(), m.end(), i + 1, marca))
                continue
            if clave is None:
                base.update(
                    decision="sin_resolver",
                    ref_nuevo="",
                    motivo_linea="",
                )
                registros.append(base)
                continue

            forzada = lineas_mig.get(kmig) if kmig else None
            nueva_linea, motivo_linea = resolver_linea(
                inv, clave, linea_citada, anclas, forzada
            )
            if forzada is not None:
                nueva_linea, motivo_linea = forzada, "linea_fijada_por_migracion"
            if nueva_linea is None:
                # Red 1: el mapa de migraciones. Cubre el caso en que la ruta
                # **existe** pero el autor apuntaba al fichero equivalente de
                # otro módulo (`collab/collab/src/lib.rs` → `src/entity.rs`).
                kmig_alt, destino_alt = _clave_migracion(migraciones, ruta, f)
                if destino_alt is not None and destino_alt != clave:
                    for cf in VALID_FUENTES:
                        if inv.existe(cf, destino_alt):
                            alt = (cf, destino_alt)
                            alt_linea, alt_motivo = resolver_linea(
                                inv, alt, linea_citada, anclas, lineas_mig.get(kmig_alt)
                            )
                            if alt_linea is not None:
                                total_alt = len(inv.texto(alt))
                                ref_nuevo = formatear(
                                    alt,
                                    alt_linea,
                                    min(ancho, max(0, total_alt - alt_linea)),
                                )
                                base.update(
                                    decision="resuelto",
                                    ref_nuevo=ref_nuevo,
                                    motivo_ruta=f"migracion_reintento:{kmig_alt}",
                                    motivo_linea=alt_motivo,
                                )
                                registros.append(base)
                                if ref_nuevo != m.group(0).strip("`"):
                                    cambios.append((m.start(), m.end(), i + 1, ref_nuevo))
                                continue

                # Red 2: el mismo crate. Si la línea está fuera de rango y el
                # fichero citado no menciona el símbolo, se busca el único
                # fichero del crate que lo declara.
                alt, alt_linea, alt_motivo = buscar_en_crate(inv, clave[1], anclas)
                if alt is not None and alt_linea is not None:
                    total_alt = len(inv.texto(alt))
                    ref_nuevo = formatear(
                        alt, alt_linea, min(ancho, max(0, total_alt - alt_linea))
                    )
                    base.update(
                        decision="resuelto",
                        ref_nuevo=ref_nuevo,
                        motivo_ruta="crate_scope",
                        motivo_linea=alt_motivo,
                    )
                    registros.append(base)
                    if ref_nuevo != m.group(0).strip("`"):
                        cambios.append((m.start(), m.end(), i + 1, ref_nuevo))
                    continue

                # Red 3: retirada, solo si la cita no era estructuralmente válida.
                # Criterio (C1): **nunca** se retira una cita cuyo fichero se
                # resolvió por nombre único o ya venía en el inventario con la
                # línea dentro de rango. Para que un fichero de nombre único, que
                # existe, en una línea que existe, sea unaugel fabrication hace
                # falta evidencia positiva, y el conjunto de anclas es
                # heurístico: usarlo como prueba-retirada producía falsos
                # positivos (`sidebar_test_runner.dart:14` y
                # `_page_style_icon_bloc.dart:10` se retiraron sin motivo).
                # La retirada queda para las citas cuyo fichero **no existía**
                # con ese nombre (migración por ambigüedad o `para: null`) o
                # cuya línea estaba fuera de rango.
                retirada_permitida = motivo_ruta.startswith(
                    ("migracion", "ancla_global", "sin_candidato")
                ) or linea_fuera_de_rango
                existe_alguno = any(
                    inv.buscar(clave, tok)
                    for ancla in anclas
                    for tok in tokens_ordenados(ancla)
                )
                if not existe_alguno and retirada_permitida:
                    marca = (
                        "`[NO DETERMINADO]` (ver "
                        "`22-preguntas-abiertas.md § C1`)"
                    )
                    base.update(
                        decision="retirada",
                        ref_nuevo=marca,
                        motivo_linea="simbolo_inexistente_en_el_snapshot",
                    )
                    registros.append(base)
                    cambios.append((m.start(), m.end(), i + 1, marca))
                    continue
                base.update(
                    decision="ruta_ok_linea_intraducible",
                    ref_nuevo=formatear(clave, linea_citada, ancho),
                    motivo_linea=motivo_linea,
                )
                registros.append(base)
                continue

            total = len(inv.texto(clave))
            ref_nuevo = formatear(clave, nueva_linea, min(ancho, max(0, total - nueva_linea)))
            base.update(
                decision="resuelto",
                ref_nuevo=ref_nuevo,
                motivo_linea=motivo_linea,
            )
            registros.append(base)
            if ref_nuevo != m.group(0).strip("`"):
                cambios.append((m.start(), m.end(), i + 1, ref_nuevo))

    if cambios and not dry_run:
        nuevo_texto = lineas[:]
        # Aplicar de derecha a izquierda para no invalidar los offsets.
        for start, end, _dl, nuevo in sorted(cambios, reverse=True):
            nuevo_texto[_dl - 1] = nuevo_texto[_dl - 1][:start] + nuevo + nuevo_texto[_dl - 1][end:]
        doc.write_text("\n".join(nuevo_texto) + "\n", encoding="utf-8")
    return registros


def formatear(clave: tuple[str, str], linea: int, ancho: int) -> str:
    """Referencia en la forma que espera `validate_evidence.py`.

    Convención del inventario: `ruta_rel` = `<fuente>/<resto>`, y
    `validate_evidence.py` solo antepone `<fuente>/` cuando la ruta citada no
    empieza ya por `<fuente>/`. Para `appflowy` (fuente implícita) se quita el
    prefijo; para `collab` y `editor` se conserva `ruta_rel` **entero** y se
    añade `fuente:`, porque el resto ya puede empezar por el nombre del repo
    (`collab/collab/src/entity.rs`).
    """
    fuente, ruta_rel = clave
    if fuente == DEFAULT_FUENTE:
        cuerpo = ruta_rel[len(fuente) + 1:] if ruta_rel.startswith(f"{fuente}/") else ruta_rel
        prefijo = ""
    else:
        cuerpo = ruta_rel
        prefijo = f"{fuente}:"
    if ancho > 0:
        return f"{prefijo}{cuerpo}:{linea}–{linea + ancho}"
    return f"{prefijo}{cuerpo}:{linea}"


# --- Main -------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="*", default=["OUT/"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--inventario", type=Path, default=INVENTARIO)
    ap.add_argument("--migraciones", type=Path, default=MIGRACIONES)
    ap.add_argument("--csv-dir", type=Path, default=None)
    ap.add_argument(
        "--skip",
        nargs="*",
        # Coherente con `validate_evidence.py::META_DOCS`: los meta-ficheros
        # no son entregables y `22-preguntas-abiertas.md` **cita** referencias
        # rotas a propósito (registro de C1), no las afirma.
        default=[
            "OUT/_ledger",
            "OUT/STATE.md",
            "OUT/00-INDEX.md",
            "OUT/22-preguntas-abiertas.md",
        ],
    )
    args = ap.parse_args()
    if not args.dry_run and not args.apply:
        ap.error("usa --dry-run o --apply")

    inv = Inventario(args.inventario)
    migraciones, lineas_mig = cargar_migraciones(args.migraciones)

    targets: list[Path] = []
    raiz = PROJECT_ROOT.resolve()

    def relativo(m: Path) -> str:
        """Ruta relativa al proyecto: `--skip` no debe depender de si el `PATH`
        de la CLI viene en relativo o en absoluto (C1: con `OUT/` absoluto los
        skips no casaban y el script acabó reescribiendo `STATE.md` y las
        bitácoras de `_ledger/`)."""
        try:
            return str(m.resolve().relative_to(raiz))
        except ValueError:
            return str(m)

    for p in args.paths or ["OUT/"]:
        pp = Path(p)
        if pp.is_file():
            targets.append(pp)
        elif pp.is_dir():
            targets += [
                m
                for m in sorted(pp.rglob("*.md"))
                if not any(relativo(m).startswith(s) for s in args.skip)
            ]

    todos: list[dict] = []
    for doc in sorted(set(targets)):
        regs = procesar_documento(doc, inv, migraciones, lineas_mig, args.dry_run)
        if regs:
            print(f"  {doc}: {len(regs)} ref(s) rota(s)")
            todos += regs

    campos = ["doc", "doc_line", "ref_original", "ref_nuevo", "decision",
              "motivo_ruta", "motivo_linea", "anclas"]
    resueltos = [r for r in todos if r["decision"] == "resuelto"]
    retiradas = [r for r in todos if r["decision"] == "retirada"]
    sin_resolver = [r for r in todos if r["decision"] == "sin_resolver"]
    intraducible = [r for r in todos if r["decision"] == "ruta_ok_linea_intraducible"]

    if args.csv_dir:
        args.csv_dir.mkdir(parents=True, exist_ok=True)
        for nombre, filas in (
            ("refs_resueltas.csv", resueltos),
            ("refs_retiradas.csv", retiradas),
            ("refs_ambiguas.csv", sin_resolver),
            ("refs_sin_ancla.csv", intraducible),
        ):
            with (args.csv_dir / nombre).open("w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=campos)
                w.writeheader()
                for fila in filas:
                    w.writerow({k: fila.get(k, "") for k in campos})

    modo = "APLICADO" if args.apply else "DRY-RUN"
    print(
        f"[{modo}] refs rotas detectadas: {len(todos)} · resueltas: "
        f"{len(resueltos)} · retiradas (símbolo inexistente): {len(retiradas)} · "
        f"ambiguas (humano): {len(sin_resolver)} · "
        f"ruta ok pero línea intraducible: {len(intraducible)}"
    )
    for r in sin_resolver:
        print(f"  AMBIGUA {r['doc']}:{r['doc_line']} {r['ref_original']} ({r['motivo_ruta']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())