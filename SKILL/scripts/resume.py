#!/usr/bin/env python3
"""resume.py — Orquestador determinista de reanudación para A4.4.

Lee OUT/STATE.md + cobertura.csv + units/_index.json + OUT/09-features/
y produce un `resume-plan.{json,md}` con:

- fase siguiente a ejecutar
- totales (verificados, pendientes, in_flight, sin_asignar, huerfanos)
- orden de ejecucion priorizado (in_flight primero, luego prioridad, id)
- unidades verificadas (que se omiten)
- unidades in_flight detectadas por archivos .partial.md en disco
- unidades huerfanas (docs sin unit_id en el ledger)
- decisiones de triage pendientes (sin_asignar.md)

Opcional: --regenerate-state-section reescribe la seccion
"## Como reanudar" de STATE.md con el plan actual (preserva el resto).

Fase A4.4 de la skill notemartin-appflowy-review.
Ver AGENTS.md §8-9 y ROADMAP.md linea 103.

Uso:
  resume.py [--ledger PATH] [--units-index PATH] [--state PATH]
            [--docs-root PATH] [--out-plan PATH] [--out-md PATH]
            [--max-units N] [--json] [--no-color] [--regenerate-state-section]
            [--help]
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_PATH = Path(__file__).resolve()
SKILL_ROOT = SCRIPT_PATH.parent.parent.parent

LEDGER_DEFAULT = SKILL_ROOT / "OUT" / "_ledger" / "cobertura.csv"
UNITS_INDEX_DEFAULT = SKILL_ROOT / "OUT" / "_ledger" / "units" / "_index.json"
STATE_DEFAULT = SKILL_ROOT / "OUT" / "STATE.md"
DOCS_ROOT_DEFAULT = SKILL_ROOT / "OUT" / "09-features"
OUT_PLAN_DEFAULT = SKILL_ROOT / "OUT" / "_ledger" / "resume-plan.json"
OUT_MD_DEFAULT = SKILL_ROOT / "OUT" / "_ledger" / "resume-plan.md"

HEADER_LEDGER = (
    "fuente",
    "ruta",
    "capa",
    "feature_ids",
    "documento",
    "estado",
    "verificado_por",
)

ESTADOS_VALIDOS = {"verificado", "pendiente", "sin_asignar"}
IN_FLIGHT_PREFIX = "in_flight:"

# Regex sobre `id` (Fxx o Fxx.y).
UNIT_ID_RE = re.compile(r"^F(\d{2})(?:\.(\d+))?$")
# Regex para parsear "## Ultima fase cerrada" en STATE.md.
# Acepta tildes (Última/última) y envoltura opcional de asteriscos
# para el id de la fase.
PHASE_RE = re.compile(r"##\s+(?:[Uu]|[Úú])ltima\s+fase\s+cerrada\s*\n+\**\s*([A-Z][A-Z0-9.]*)")
NEXT_PHASE_RE = re.compile(r"##\s+(?:[Uu]|[Úú])ltima\s+fase\s+por\s+abrir\s*\n+\**\s*([A-Z][A-Z0-9.]*)")
# Regex para extraer el unit_id del nombre de archivo .partial.md
#   "01.4-menciones-inline-actions-emoji.md.partial"  → F01.4
#   "F11-exportacion-ui.md.partial"                   → F11
PARTIAL_UNIT_RE = re.compile(r"^(F?\d{2}(?:\.\d+)?)-")

RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BOLD = "\033[1m"
RESET = "\033[0m"


@dataclass
class LedgerRow:
    fuente: str
    ruta: str
    capa: str
    feature_ids: set[str]
    documento: str
    estado: str
    verificado_por: str


@dataclass
class Stats:
    asignados: int = 0
    verificados: int = 0
    pendientes: int = 0
    sin_asignar: int = 0
    in_flight: int = 0
    huerfanos: int = 0
    by_feature: Counter = field(default_factory=Counter)
    by_fuente: Counter = field(default_factory=Counter)


# ---------- IO ------------------------------------------------------------


def load_ledger(path: Path) -> list[LedgerRow]:
    if not path.is_file():
        print(f"ERROR: no existe {path}", file=sys.stderr)
        sys.exit(2)
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames
        if header is None or tuple(header) != HEADER_LEDGER:
            print(
                f"ERROR: cabecera de {path} no coincide.\n"
                f"  esperado: {list(HEADER_LEDGER)}\n"
                f"  encontrado: {header}",
                file=sys.stderr,
            )
            sys.exit(2)
        rows = list(reader)
    out: list[LedgerRow] = []
    for r in rows:
        fids = {f for f in r.get("feature_ids", "").split(";") if f}
        out.append(LedgerRow(
            fuente=r["fuente"],
            ruta=r["ruta"],
            capa=r.get("capa", ""),
            feature_ids=fids,
            documento=r.get("documento", ""),
            estado=r.get("estado", "sin_asignar"),
            verificado_por=r.get("verificado_por", ""),
        ))
    return out


def load_units_index(path: Path) -> dict:
    if not path.is_file():
        return {"total_unidades": 0, "units": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"WARN: {path} no es JSON valido: {e}", file=sys.stderr)
        return {"total_unidades": 0, "units": []}


def load_state_phases(path: Path) -> tuple[str | None, str | None]:
    """Devuelve (ultima_fase_cerrada, ultima_fase_por_abrir)."""
    if not path.is_file():
        return None, None
    text = path.read_text(encoding="utf-8")
    cerrada = None
    abrir = None
    m = PHASE_RE.search(text)
    if m:
        cerrada = m.group(1)
    m = NEXT_PHASE_RE.search(text)
    if m:
        abrir = m.group(1)
    return cerrada, abrir


def scan_partial_docs(docs_root: Path) -> dict[str, list[str]]:
    """Devuelve {unit_id: [paths .partial.md]}.

    Busca recursivamente `*.partial.md` bajo docs_root y mapea cada
    archivo al unit_id inferido del nombre.
    """
    out: dict[str, list[str]] = defaultdict(list)
    if not docs_root.is_dir():
        return out
    for path in docs_root.rglob("*.partial.md"):
        name = path.name.removesuffix(".partial.md").removesuffix(".md")
        m = PARTIAL_UNIT_RE.match(name)
        if not m:
            continue
        unit_id = m.group(1)
        # Normalizar: "01.4" → "F01.4"
        if not unit_id.startswith("F"):
            unit_id = "F" + unit_id
        out[unit_id].append(str(path.relative_to(SKILL_ROOT)))
    return out


def read_frontmatter_id(path: Path) -> str | None:
    """Devuelve el campo `id:` del frontmatter YAML de un .md, o None."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    for line in text[3:end].splitlines():
        m = re.match(r"^id:\s*(\S+)\s*$", line)
        if m:
            return m.group(1).strip("'\"")
    return None


def scan_orphan_docs(docs_root: Path, valid_unit_ids: set[str], all_feature_ids: set[str]) -> list[dict]:
    """Busca .md (no .partial) bajo docs_root cuyo unit_id no este en
    units_index ni como feature_id en cobertura.csv.

    El id se lee del FRONTMATTER `id:` del documento (fuente de verdad), no
    del nombre de archivo: la convencion `12-tab-bar-…md` dentro de
    `F02-bases-de-datos/` NO codifica el id real (`F02.12`). Sin esto, tres
    documentos de F02 se reportaban como huerfanos aunque sus unidades
    `F02.12/F02.13/F02.15` existen en `_index.json` y los apuntan.
    Se cae al nombre solo si el doc no tiene frontmatter legible.
    """
    orphans: list[dict] = []
    if not docs_root.is_dir():
        return orphans
    for path in docs_root.rglob("*.md"):
        if path.name.endswith(".partial.md"):
            continue
        unit_id = read_frontmatter_id(path)
        origin = "frontmatter"
        if unit_id is None:
            name = path.name.removesuffix(".md")
            m = PARTIAL_UNIT_RE.match(name)
            if not m:
                continue
            unit_id = m.group(1)
            if not unit_id.startswith("F"):
                unit_id = "F" + unit_id
            origin = "nombre_archivo"
        if unit_id in valid_unit_ids:
            continue
        # Un doc puede no ser una unidad (indice de feature, doc B*, etc.).
        # Solo es huerfano si ademas no es un feature_id conocido del ledger.
        if unit_id in all_feature_ids:
            continue
        orphans.append({
            "ruta": str(path.relative_to(SKILL_ROOT)),
            "unit_id_inferido": unit_id,
            "motivo": f"Sin unit_id asociado en units/_index.json (id leido de {origin})",
        })
    return orphans


# ---------- calculos ------------------------------------------------------


def compute_stats(
    rows: list[LedgerRow],
    units_index: dict,
    partials: dict[str, list[str]],
    orphans: list[dict],
) -> Stats:
    s = Stats()
    valid_unit_ids: set[str] = set()
    for u in units_index.get("units", []):
        valid_unit_ids.add(u["id"])

    for r in rows:
        if r.estado == "verificado":
            s.verificados += 1
        elif r.estado == "pendiente" and r.feature_ids:
            s.pendientes += 1
        elif r.estado == "sin_asignar" or not r.feature_ids:
            s.sin_asignar += 1
        if r.feature_ids:
            s.asignados += 1
            for fid in r.feature_ids:
                s.by_feature[fid] += 1
        s.by_fuente[r.fuente] += 1

    # in_flight = unidades con .partial.md que NO estan todas verificadas.
    s.in_flight = 0
    for unit_id in partials:
        if unit_id in valid_unit_ids:
            s.in_flight += 1
    s.huerfanos = len(orphans)
    return s


def compute_order(
    units_index: dict,
    rows: list[LedgerRow],
    partials: dict[str, list[str]],
) -> list[dict]:
    """Orden de ejecucion: in_flight primero, luego por prioridad ASC,
    luego por id ASC. Excluye unidades con todas sus filas en verificado.

    Las unidades detectadas como in_flight (por partials o por la
    marca `in_flight:` en `verificado_por`) se incluyen aunque no
    aparezcan en cobertura.csv (caso sub-unidades como F01.1 cuyo
    padre es F01)."""
    by_unit: dict[str, list[LedgerRow]] = defaultdict(list)
    for r in rows:
        for fid in r.feature_ids:
            by_unit[fid].append(r)

    out: list[dict] = []
    seen: set[str] = set()
    # 1) Unidades con .partial.md (pueden no estar en cobertura.csv).
    for uid in partials:
        if uid in seen:
            continue
        seen.add(uid)
        # Buscar la unidad en el index; si no esta, anadirla como "huérfana
        # documentada" con prioridad 2.
        u_meta = next((u for u in units_index.get("units", []) if u["id"] == uid), None)
        if u_meta is None:
            out.append({
                "unit_id": uid,
                "prioridad": 2,
                "estado": "in_flight",
                "concurrencia": "paralela",
                "archivos_total": 0,
                "dependencias": [],
            })
            continue
        out.append({
            "unit_id": uid,
            "prioridad": u_meta.get("prioridad", 2),
            "estado": "in_flight",
            "concurrencia": u_meta.get("concurrencia", "paralela"),
            "archivos_total": u_meta.get("archivos_total", 0),
            "dependencias": u_meta.get("dependencias", []),
        })
    # 2) Unidades del index que no estan ya en `seen` y no estan verificadas.
    for u in units_index.get("units", []):
        uid = u["id"]
        if uid in seen:
            continue
        unit_rows = by_unit.get(uid, [])
        if not unit_rows:
            continue
        if all(r.estado == "verificado" for r in unit_rows):
            continue
        if any(IN_FLIGHT_PREFIX in (r.verificado_por or "") for r in unit_rows):
            in_flight = True
        else:
            in_flight = uid in partials
        out.append({
            "unit_id": uid,
            "prioridad": u.get("prioridad", 2),
            "estado": "in_flight" if in_flight else "pendiente",
            "concurrencia": u.get("concurrencia", "paralela"),
            "archivos_total": u.get("archivos_total", 0),
            "dependencias": u.get("dependencias", []),
        })
        seen.add(uid)
    # Orden: in_flight primero, prioridad ASC, id ASC.
    out.sort(key=lambda x: (
        0 if x["estado"] == "in_flight" else 1,
        x["prioridad"],
        x["unit_id"],
    ))
    return out


def compute_next_action(cerrada: str | None, abrir: str | None,
                        stats: Stats) -> str:
    if stats.in_flight > 0:
        return (f"Recuperar {stats.in_flight} unidad(es) in_flight antes de "
                f"continuar. Ejecuta `run_subagent.py --rol autor` para cada "
                f"unidad in_flight en el orden de ejecucion.")
    if stats.sin_asignar > 0:
        return (f"Triage manual de {stats.sin_asignar} archivos sin_asignar "
                f"(ver OUT/_ledger/sin_asignar.md) antes de continuar "
                f"(fase B0.2).")
    if abrir:
        return f"Continuar con la fase {abrir} (siguiente del ROADMAP)."
    if cerrada:
        return f"Continuar con la fase siguiente a {cerrada} (consultar ROADMAP.md)."
    return "Sin fase siguiente detectada; revisar OUT/STATE.md manualmente."


# ---------- salida --------------------------------------------------------


def build_plan(
    rows: list[LedgerRow],
    units_index: dict,
    partials: dict[str, list[str]],
    orphans: list[dict],
    cerrada: str | None,
    abrir: str | None,
    fase_actual: str | None,
) -> dict:
    stats = compute_stats(rows, units_index, partials, orphans)
    orden = compute_order(units_index, rows, partials)
    verificados_ids = sorted({
        uid for uid, urs in _group_by_unit(rows).items()
        if urs and all(r.estado == "verificado" for r in urs)
    })
    next_action = compute_next_action(cerrada, abrir, stats)
    if fase_actual:
        next_action = f"Reanudar en fase {fase_actual}. " + next_action

    return {
        "schema_version": 1,
        "generado_en": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "fase_actual": fase_actual,
        "ultima_fase_cerrada": cerrada,
        "ultima_fase_por_abrir": abrir,
        "totales": {
            "asignados": stats.asignados,
            "verificados": stats.verificados,
            "pendientes": stats.pendientes,
            "in_flight": stats.in_flight,
            "sin_asignar": stats.sin_asignar,
            "huerfanos": stats.huerfanos,
        },
        "siguiente_accion": next_action,
        "orden_ejecucion": orden,
        "unidades_in_flight": [
            {"unit_id": uid, "partial_docs": docs}
            for uid, docs in sorted(partials.items())
            if uid in {u["id"] for u in units_index.get("units", [])}
        ],
        "unidades_verificadas_omitir": verificados_ids,
        "unidades_huerfanas": orphans,
        "decisiones_triage_pendientes": {
            "sin_asignar_count": stats.sin_asignar,
            "sin_asignar_doc": "OUT/_ledger/sin_asignar.md",
        },
    }


def _group_by_unit(rows: list[LedgerRow]) -> dict[str, list[LedgerRow]]:
    g: dict[str, list[LedgerRow]] = defaultdict(list)
    for r in rows:
        for fid in r.feature_ids:
            g[fid].append(r)
    return g


def render_markdown(plan: dict, max_units: int) -> str:
    t = plan["totales"]
    lines = [
        "# Plan de reanudación — A4.4",
        "",
        f"Generado: `{plan['generado_en']}`",
        "",
        "## Totales",
        "",
        f"- Asignados: **{t['asignados']}**",
        f"- Verificados: **{t['verificados']}**",
        f"- Pendientes: **{t['pendientes']}**",
        f"- In-flight: **{t['in_flight']}**",
        f"- Sin asignar: **{t['sin_asignar']}**",
        f"- Huérfanos: **{t['huerfanos']}**",
        "",
        "## Fase",
        "",
        f"- Última cerrada: `{plan['ultima_fase_cerrada']}`",
        f"- Por abrir: `{plan['ultima_fase_por_abrir']}`",
        f"- Fase actual (override): `{plan['fase_actual']}`",
        "",
        "## Siguiente acción",
        "",
        plan["siguiente_accion"],
        "",
        f"## Orden de ejecución (top {max_units})",
        "",
        "| # | unit_id | prioridad | estado | concurrencia | archivos |",
        "|---|---|---:|---|---|---:|",
    ]
    for i, u in enumerate(plan["orden_ejecucion"][:max_units], start=1):
        lines.append(
            f"| {i} | `{u['unit_id']}` | {u['prioridad']} | {u['estado']} | "
            f"{u['concurrencia']} | {u['archivos_total']} |"
        )
    lines.append("")

    lines.append("## Unidades verificadas (omitir)")
    lines.append("")
    if plan["unidades_verificadas_omitir"]:
        for uid in plan["unidades_verificadas_omitir"]:
            lines.append(f"- `{uid}`")
    else:
        lines.append("- (ninguna)")
    lines.append("")

    lines.append("## In-flight (recuperar)")
    lines.append("")
    if plan["unidades_in_flight"]:
        for inf in plan["unidades_in_flight"]:
            docs = ", ".join(f"`{d}`" for d in inf["partial_docs"])
            lines.append(f"- `{inf['unit_id']}` → {docs}")
    else:
        lines.append("- (ninguna)")
    lines.append("")

    lines.append("## Huérfanas")
    lines.append("")
    if plan["unidades_huerfanas"]:
        for o in plan["unidades_huerfanas"]:
            lines.append(f"- `{o['ruta']}` (id inferido `{o['unit_id_inferido']}`) — {o['motivo']}")
    else:
        lines.append("- (ninguna)")
    lines.append("")

    lines.append("## Decisiones de triage pendientes")
    lines.append("")
    t = plan["decisiones_triage_pendientes"]
    lines.append(f"- `sin_asignar`: {t['sin_asignar_count']} (ver `{t['sin_asignar_doc']}`)")
    lines.append("")
    return "\n".join(lines) + "\n"


def regenerate_state_section(state_path: Path, plan: dict) -> bool:
    """Reescribe la seccion `## Como reanudar` de STATE.md preservando
    el resto. Devuelve True si modifico algo."""
    if not state_path.is_file():
        return False
    text = state_path.read_text(encoding="utf-8")
    # Buscar el inicio de la seccion "## Como reanudar" o "## Cómo reanudar".
    m = re.search(r"^##\s+C[oó]mo\s+reanudar\s*$", text, re.MULTILINE)
    if not m:
        return False
    start = m.start()
    # El final es el siguiente `## ` o el final del archivo.
    rest = text[m.end():]
    n = re.search(r"^##\s+", rest, re.MULTILINE)
    end = m.end() + (n.start() if n else len(rest))

    new_section = _build_state_section(plan)
    new_text = text[:start] + new_section + text[end:]
    state_path.write_text(new_text, encoding="utf-8")
    return True


def _build_state_section(plan: dict) -> str:
    t = plan["totales"]
    lines = [
        "## Cómo reanudar",
        "",
        f"Plan regenerado por `resume.py` el `{plan['generado_en']}`.",
        "",
        f"- Última fase cerrada: **{plan['ultima_fase_cerrada']}**",
        f"- Última fase por abrir: **{plan['ultima_fase_por_abrir']}**",
        f"- Totales: asignados={t['asignados']} verificados={t['verificados']} "
        f"pendientes={t['pendientes']} in_flight={t['in_flight']} "
        f"sin_asignar={t['sin_asignar']} huérfanos={t['huerfanos']}",
        "",
        f"**Siguiente acción**: {plan['siguiente_accion']}",
        "",
        "Pasos (resumidos de `SKILL/SKILL.md §5`):",
        "",
        f"1. Leer este `STATE.md` → última fase cerrada: **{plan['ultima_fase_cerrada']}**.",
        "2. Cargar el ledger (`OUT/_ledger/...`) y el `units/_index.json`.",
        f"3. Ejecutar las unidades en el orden de `resume-plan.md` "
        f"({len(plan['orden_ejecucion'])} en total).",
        "4. Marcar `verificado` con `record_unit_state.py --verificar <unit>`.",
        "5. Al cerrar la fase, regenerar este bloque con `resume.py --regenerate-state-section`.",
        "",  # separador en blanco antes de la siguiente seccion
        "",
    ]
    return "\n".join(lines)


# ---------- CLI -----------------------------------------------------------


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Genera un plan de reanudacion a partir de STATE.md + ledger + "
            "units/_index.json + docs .partial.md (A4.4)."
        )
    )
    p.add_argument("--ledger", type=Path, default=LEDGER_DEFAULT)
    p.add_argument("--units-index", type=Path, default=UNITS_INDEX_DEFAULT)
    p.add_argument("--state", type=Path, default=STATE_DEFAULT)
    p.add_argument("--docs-root", type=Path, default=DOCS_ROOT_DEFAULT)
    p.add_argument("--out-plan", type=Path, default=OUT_PLAN_DEFAULT)
    p.add_argument("--out-md", type=Path, default=OUT_MD_DEFAULT)
    p.add_argument("--max-units", type=int, default=20)
    p.add_argument("--fase-actual", type=str, default=None,
                   help="Override manual de la fase actual.")
    p.add_argument("--regenerate-state-section", action="store_true",
                   dest="regen_state",
                   help="Reescribe la seccion '## Como reanudar' de STATE.md.")
    p.add_argument("--json", action="store_true", dest="as_json",
                   help="Plan a stdout en JSON.")
    p.add_argument("--quiet", action="store_true",
                   help="Suprime el resumen a stderr (no afecta a --json).")
    p.add_argument("--no-color", action="store_true")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    rows = load_ledger(args.ledger)
    units_index = load_units_index(args.units_index)
    cerrada, abrir = load_state_phases(args.state)
    partials = scan_partial_docs(args.docs_root)
    valid_unit_ids = {u["id"] for u in units_index.get("units", [])}
    all_feature_ids = {fid for r in rows for fid in r.feature_ids}
    orphans = scan_orphan_docs(args.docs_root, valid_unit_ids, all_feature_ids)

    plan = build_plan(
        rows, units_index, partials, orphans,
        cerrada, abrir, args.fase_actual,
    )

    args.out_plan.parent.mkdir(parents=True, exist_ok=True)
    args.out_plan.write_text(json.dumps(plan, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    args.out_md.write_text(render_markdown(plan, args.max_units), encoding="utf-8")

    if args.regen_state:
        if regenerate_state_section(args.state, plan):
            print(f"[resume] seccion '## Como reanudar' regenerada en {args.state}", file=sys.stderr)
        else:
            print(f"WARN: no se encontro '## Como reanudar' en {args.state}", file=sys.stderr)

    if args.as_json:
        print(json.dumps(plan, indent=2, ensure_ascii=False))
    else:
        t = plan["totales"]
        print(f"[resume] asignados={t['asignados']} verificados={t['verificados']} "
              f"pendientes={t['pendientes']} in_flight={t['in_flight']} "
              f"sin_asignar={t['sin_asignar']} huerfanos={t['huerfanos']}",
              file=sys.stderr)
        print(f"[resume] plan={args.out_plan}", file=sys.stderr)
        print(f"[resume] md={args.out_md}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
