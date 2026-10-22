#!/usr/bin/env python3
"""run_subagent.py — Mock determinista del subagente autor/revisor
definido en SKILL/references/subagent-{contract,autor-prompt,revisor-prompt}.md.

Fase A4.3 de la skill notemartin-appflowy-review.
Ver AGENTS.md §8 y ROADMAP.md linea 101.

El mock NO usa un LLM real; produce un documento estructuralmente
valido (pasa validate_template.py) pero semanticamente vacio (citas
placeholder). El modo revisor ejecuta los 3 validadores reales
(validate_evidence, validate_template, validate_mermaid) sobre el
documento creado por el autor y emite un veredicto estricto.

Uso:
  run_subagent.py --rol {autor|revisor}
                  --unit PATH
                  --src-root PATH
                  --inventario PATH
                  --extract-dir PATH
                  --plantilla PATH
                  --out PATH             # JSON de salida
                  [--evidence-min-pct N]
                  [--feature-id ID]
                  [--no-color] [--quiet] [--json]
                  [--help]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_PATH = Path(__file__).resolve()
SKILL_ROOT = SCRIPT_PATH.parent.parent.parent
DEFAULT_TEMPLATE_FEATURE = SKILL_ROOT / "SKILL" / "references" / "feature-template.md"
DEFAULT_TEMPLATE_EXPORT = SKILL_ROOT / "SKILL" / "references" / "export-template.md"
DEFAULT_INVENTARIO = SKILL_ROOT / "OUT" / "_ledger" / "inventario.json"
DEFAULT_EXTRACT_DIR = SKILL_ROOT / "OUT" / "_ledger" / "extract"
DEFAULT_SRC_ROOT = SKILL_ROOT / "SRC"

# Validadores consumidos por el modo revisor.
VALIDATE_EVIDENCE = SKILL_ROOT / "SKILL" / "scripts" / "validate_evidence.py"
VALIDATE_TEMPLATE = SKILL_ROOT / "SKILL" / "scripts" / "validate_template.py"
VALIDATE_MERMAID = SKILL_ROOT / "SKILL" / "scripts" / "validate_mermaid.sh"

CONTRACT_PATH = SKILL_ROOT / "SKILL" / "references" / "subagent-contract.md"
AUTOR_PROMPT_PATH = SKILL_ROOT / "SKILL" / "references" / "subagent-autor-prompt.md"
REVISOR_PROMPT_PATH = SKILL_ROOT / "SKILL" / "references" / "subagent-revisor-prompt.md"

RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BOLD = "\033[1m"
RESET = "\033[0m"


# ---------- carga y utilidades --------------------------------------------


def load_json(path: Path) -> dict:
    if not path.is_file():
        print(f"ERROR: no existe {path}", file=sys.stderr)
        sys.exit(2)
    return json.loads(path.read_text(encoding="utf-8"))


def read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def first_nonblank_line(text: str) -> int:
    """Devuelve el numero de linea (1-based) de la primera linea no vacia."""
    for i, line in enumerate(text.splitlines(), start=1):
        if line.strip():
            return i
    return 1


def slug(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")
    return s[:60]


# ---------- modo autor (mock) ---------------------------------------------


def run_autor(args: argparse.Namespace) -> dict:
    unit = load_json(args.unit)
    unit_id = unit.get("id", "F?")
    titulo = unit.get("titulo", unit_id)
    fuentes = unit.get("fuentes", [])
    archivos = unit.get("archivos", [])
    metricas = unit.get("metricas", {})
    dependencias = unit.get("dependencias", [])
    documento_rel = unit.get("documento")
    if not documento_rel:
        return _fatal("unit.documento no declarado; no se puede escribir el documento.")

    out_root = Path(args.out_root) if args.out_root else SKILL_ROOT / "OUT"
    doc_path = out_root / documento_rel
    doc_path.parent.mkdir(parents=True, exist_ok=True)

    archivos_cubiertos = [{"fuente": f["fuente"], "ruta": f["ruta"]} for f in archivos]

    # Citas reales (primera linea no vacia de cada archivo si existe).
    filas: list[dict] = []
    archivos_extra: list[dict] = []
    src_root = Path(args.src_root)
    for f in archivos:
        # `ruta` ya incluye el prefijo de fuente (e.g.
        # "appflowy/frontend/..."); no se duplica.
        src = src_root / f["ruta"]
        if not src.is_file():
            archivos_extra.append({
                "fuente": f["fuente"],
                "ruta": f["ruta"],
                "motivo": "Archivo declarado en la unidad pero no existe en SRC.",
            })
            continue
        line = first_nonblank_line(read_text(src))
        filas.append({
            "fuente": f["fuente"],
            "ruta": f["ruta"],
            "primera_linea": line,
        })

    # Genera el documento estructuralmente valido.
    frontmatter = _frontmatter(unit_id, titulo, fuentes, archivos, metricas)
    secciones = _sections(unit, filas, archivos_extra, args, dependencias)
    doc = frontmatter + "\n" + "\n".join(secciones) + "\n"
    doc_path.write_text(doc, encoding="utf-8")

    preguntas = [
        f"[NO DETERMINADO] Documento de la unidad {unit_id} generado por mock run_subagent; "
        "pendiente de redaccion humana (autor real en A4.3.x o Parte B).",
    ]
    out: dict = {
        "schema_version": 1,
        "documento": documento_rel,
        "filas_ledger_cubiertas": archivos_cubiertos,
        "archivos_extra_detectados": archivos_extra,
        "preguntas_abiertas": preguntas,
        "metricas": {
            "secciones_rellenas": len(secciones),
            "afirmaciones_verificadas": len(filas),
            "afirmaciones_inferidas": 0,
            "diagramas_mermaid": 0,
        },
    }
    return out


def _frontmatter(unit_id: str, titulo: str, fuentes: list, archivos: list, metricas: dict) -> str:
    archivos_cubiertos_list = [f"{f['fuente']}:{f['ruta']}" for f in archivos]
    fuentes_str = ", ".join(fuentes) if fuentes else "appflowy"
    archivos_yaml = "\n".join(f"  - {a}" for a in archivos_cubiertos_list)
    return (
        "---\n"
        f"id: {unit_id}\n"
        f"titulo: {titulo}\n"
        f"fuente: {fuentes_str}\n"
        f"archivos_cubiertos:\n{archivos_yaml}\n"
        "estado: pendiente\n"
        "---\n\n"
    )


def _sections(unit: dict, filas: list[dict], archivos_extra: list[dict],
              args: argparse.Namespace, dependencias: list) -> list[str]:
    """Genera las 19 secciones de la plantilla feature (o 11 si plantilla=export)."""
    max_secciones = args.max_secciones
    unit_id = unit.get("id", "F?")
    titulo = unit.get("titulo", unit_id)
    metricas = unit.get("metricas", {})
    n_arch = metricas.get("archivos", len(filas))
    por_capa = metricas.get("por_capa", {})
    por_fuente = metricas.get("por_fuente", {})
    secciones: list[str] = []

    secciones.append(f"# {unit_id} — {titulo}\n")
    secciones.append(
        "## 1. Resumen (3–6 líneas)\n\n"
        f"Documento de la unidad `{unit_id}` cubriendo {n_arch} archivo(s) "
        f"de la feature **{titulo}**. Generado por el mock `run_subagent.py` "
        f"para validar el contrato del subagente autor en la fase A4.3; "
        f"queda pendiente de redaccion humana antes de la fase B3. "
        f"Estructura conforme a `SKILL/references/feature-template.md` (19 secciones).\n"
    )
    secciones.append(
        "## 2. Alcance\n\n"
        f"Esta unidad cubre los archivos listados en la seccion 12. "
        f"Quedan fuera los archivos declarados como `archivos_extra_detectados` "
        f"que el autor no encontro en `SRC/`. Las dependencias declaradas en "
        f"`unit.dependencias` se procesan antes que esta unidad.\n"
    )
    secciones.append(
        "## 3. Modelos de datos\n\n"
        "Diagrama `classDiagram` o `erDiagram` (placeholder del mock; "
        "el autor real lo sustituira por el modelo del codigo).\n"
        "```mermaid\n"
        "classDiagram\n"
        "  class Placeholder {\n"
        "    +int id\n"
        "    +string nombre\n"
        "  }\n"
        "```\n"
    )
    secciones.append(
        "## 4. Eventos FFI\n\n"
        "Tabla `evento, input PB, output PB, handler, archivo:línea` extraida "
        "de `OUT/_ledger/extract/events.json` (placeholder).\n\n"
        "| Evento | Input PB | Output PB | Handler | Archivo:línea |\n"
        "|---|---|---|---|---|\n"
        "| — | — | — | — | — |\n"
    )
    secciones.append(
        "## 5. Notificaciones\n\n"
        "Tabla `notificacion, emisor, listener Dart, efecto UI, archivo:línea` "
        "(placeholder).\n"
    )
    secciones.append(
        "## 6. BLoCs / Cubits\n\n"
        "Tabla `clase, eventos, estados, servicios, archivo:línea` (placeholder).\n"
    )
    secciones.append(
        "## 7. Servicios e inyeccion de dependencias\n\n"
        "Dart (`get_it`) y Rust (`flowy-core/deps_resolve`) (placeholder).\n"
    )
    secciones.append(
        "## 8. Persistencia\n\n"
        "Tablas SQLite, KV, archivo de collab en disco (placeholder).\n"
    )
    secciones.append(
        "## 9. Diagramas de flujo\n\n"
        "`flowchart TD` con subgraphs por capa (placeholder; el autor real "
        "lo sustituira por el flujo concreto).\n"
        "```mermaid\n"
        "flowchart TD\n"
        "  UI[UI] --> SVC[Servicio]\n"
        "  SVC --> FFI[FFI]\n"
        "  FFI --> RUST[Rust handler]\n"
        "```\n"
    )
    secciones.append(
        "## 10. Diagramas de secuencia\n\n"
        "`sequenceDiagram` con participantes = clase real (placeholder).\n"
        "```mermaid\n"
        "sequenceDiagram\n"
        "  participant U as Usuario\n"
        "  participant A as Autor\n"
        "  U->>A: ejecutar unidad\n"
        "  A-->>U: AutorOutput\n"
        "```\n"
    )
    secciones.append(
        "## 11. Diagramas de estado\n\n"
        "`stateDiagram-v2` para ciclos de vida relevantes (placeholder).\n"
    )

    # Seccion 12: lista tabular de archivos cubiertos (real).
    rows = []
    for f in filas:
        rows.append(
            f"| `{f['fuente']}` | `{f['ruta']}` | — | `{f['fuente']}:{f['ruta']}:{f['primera_linea']}` |"
        )
    if not rows:
        rows.append("| — | — | — | — |")
    secciones.append(
        "## 12. Archivos cubiertos (del ledger)\n\n"
        "Lista tabular copiada de `_ledger/cobertura.csv` filtrada por esta unidad.\n\n"
        "| Fuente | Ruta | Capa | Evidencia |\n"
        "|---|---|---|---|\n"
        + "\n".join(rows) + "\n"
    )

    secciones.append(
        "## 13. Riesgos y casos limite\n\n"
        "Bullets con que puede fallar y como se mitiga (placeholder del mock).\n"
    )
    secciones.append(
        "## 14. Evidencias y etiquetas\n\n"
        "El mock emite solo `[VERIFICADO]` con evidencia `ruta:línea` de la "
        "primera linea no vacia de cada archivo. El autor real debera "
        "aumentar el muestreo segun las reglas de `evidence-rules.md`.\n"
    )
    secciones.append(
        "## 15. Pruebas\n\n"
        "Tests unitarios, de BLoC, widget e integration que cubren esta feature "
        "(placeholder; el autor real lista los `test/` y `integration_test/` "
        "que correspondan).\n"
    )
    secciones.append(
        "## 16. Metricas\n\n"
        f"- Archivos: **{n_arch}**\n"
        f"- Por capa: `{por_capa}`\n"
        f"- Por fuente: `{por_fuente}`\n"
    )
    secciones.append(
        "## 17. Pendientes\n\n"
        "Tareas que se descubrieron durante la documentacion. (Vacio en el mock.)\n"
    )
    secciones.append(
        "## 18. Preguntas abiertas\n\n"
        "- `[NO DETERMINADO]` Documento generado por `run_subagent.py`; "
        "pendiente de redaccion humana.\n"
    )
    if archivos_extra:
        extras_md = "\n".join(
            f"- `{e['fuente']}` · `{e['ruta']}` — {e['motivo']}" for e in archivos_extra
        )
    else:
        extras_md = "- (vacio)"
    secciones.append(
        f"## 19. Relacionado con\n\n"
        f"Dependencias de la unidad: `{json.dumps(dependencias, ensure_ascii=False)}`.\n\n"
        f"Archivos extra detectados:\n{extras_md}\n"
    )

    if max_secciones < 19:
        secciones = secciones[: max_secciones + 1]  # +1 por el titulo
    return secciones


# ---------- modo revisor --------------------------------------------------


def run_revisor(args: argparse.Namespace) -> dict:
    unit = load_json(args.unit)
    unit_id = unit.get("id", "F?")
    feature_id = args.feature_id or unit.get("feature_id", "F?")

    documento_rel = unit.get("documento")
    if not documento_rel:
        return _fatal("unit.documento no declarado.")
    out_root = Path(args.out_root) if args.out_root else SKILL_ROOT / "OUT"
    doc_path = out_root / documento_rel
    if not doc_path.is_file():
        return _fatal(f"documento {doc_path} no existe; ejecuta primero el modo autor.")

    # Validacion 1: evidence.
    ev = _run_validate_evidence(doc_path, args.inventario)
    # Validacion 2: template.
    tp = _run_validate_template(doc_path)
    # Validacion 3: mermaid.
    mm = _run_validate_mermaid(doc_path)

    correcciones: list[dict] = []
    for err in ev["errores"]:
        correcciones.append({
            "tipo": "evidence",
            "archivo": str(doc_path.relative_to(SKILL_ROOT)),
            "linea": err.get("line", 0),
            "mensaje": err.get("message", str(err)),
        })
    for err in tp["errores"]:
        correcciones.append({
            "tipo": "template",
            "archivo": str(doc_path.relative_to(SKILL_ROOT)),
            "linea": 0,
            "mensaje": err.get("message", str(err)),
        })
    for err in mm["errores"]:
        correcciones.append({
            "tipo": "mermaid",
            "archivo": err.get("archivo", str(doc_path.relative_to(SKILL_ROOT))),
            "linea": err.get("bloque", 0),
            "mensaje": err.get("mensaje", ""),
        })

    # Muestreo: el mock no muestrea realmente; pct=0 con afirmaciones=[].
    muestreo = {
        "pct": 0,
        "total_afirmaciones": 0,
        "verificadas": 0,
        "afirmaciones": [],
    }

    veredicto = "aprobado" if (
        ev["exit"] == 0 and tp["exit"] == 0 and mm["exit"] == 0 and not correcciones
    ) else "rechazado"

    return {
        "schema_version": 1,
        "veredicto": veredicto,
        "correcciones": correcciones,
        "muestreo_verificado": muestreo,
        "validaciones": {
            "evidence": ev,
            "template": tp,
            "mermaid": mm,
        },
    }


def _run_validate_evidence(doc_path: Path, inventario: Path) -> dict:
    cmd = [
        sys.executable, str(VALIDATE_EVIDENCE),
        "--inventario", str(inventario),
        "--json", "--quiet", "--no-color",
        str(doc_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    out = proc.stdout.strip()
    errores: list[dict] = []
    if out:
        try:
            data = json.loads(out)
            for e in data.get("errors", []):
                errores.append(e)
        except json.JSONDecodeError:
            errores.append({"message": f"salida no-JSON de validate_evidence: {out[:200]}"})
    if proc.returncode != 0 and not errores:
        errores.append({"message": f"validate_evidence exit={proc.returncode}: {proc.stderr[:200]}"})
    return {"exit": proc.returncode, "errores": errores}


def _run_validate_template(doc_path: Path) -> dict:
    cmd = [
        sys.executable, str(VALIDATE_TEMPLATE),
        "--json", "--quiet", "--no-color", str(doc_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    out = proc.stdout.strip()
    errores: list[dict] = []
    if out:
        try:
            data = json.loads(out)
            for e in data.get("errors", []):
                errores.append(e)
        except json.JSONDecodeError:
            errores.append({"message": f"salida no-JSON de validate_template: {out[:200]}"})
    if proc.returncode != 0 and not errores:
        errores.append({"message": f"validate_template exit={proc.returncode}: {proc.stderr[:200]}"})
    return {"exit": proc.returncode, "errores": errores}


def _run_validate_mermaid(doc_path: Path) -> dict:
    cmd = [str(VALIDATE_MERMAID), "--quiet", "--no-color", str(doc_path)]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    errores: list[dict] = []
    for line in proc.stdout.splitlines() + proc.stderr.splitlines():
        m = re.match(r"^ERROR\s+(\S+):(\d+):\s*(.*)$", line.strip())
        if m:
            errores.append({
                "archivo": m.group(1),
                "bloque": int(m.group(2)),
                "mensaje": m.group(3),
            })
    bloques_ok = proc.stdout.count("OK:") if proc.returncode == 0 else 0
    bloques_ko = len(errores)
    return {
        "exit": proc.returncode,
        "bloques_ok": bloques_ok,
        "bloques_ko": bloques_ko,
        "errores": errores,
    }


# ---------- utilidades comunes -------------------------------------------


def _fatal(msg: str) -> dict:
    return {"schema_version": 1, "error": "fatal", "mensaje": msg}


# ---------- CLI ----------------------------------------------------------


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Mock determinista del subagente autor/revisor de A4.3. "
            "Ejecuta el contrato definido en SKILL/references/subagent-contract.md."
        )
    )
    p.add_argument("--rol", choices=["autor", "revisor"], required=True)
    p.add_argument("--unit", type=Path, required=True)
    p.add_argument("--src-root", type=Path, default=DEFAULT_SRC_ROOT)
    p.add_argument("--inventario", type=Path, default=DEFAULT_INVENTARIO)
    p.add_argument("--extract-dir", type=Path, default=DEFAULT_EXTRACT_DIR)
    p.add_argument("--plantilla", type=Path, default=DEFAULT_TEMPLATE_FEATURE)
    p.add_argument("--out", type=Path, required=True, help="JSON de salida.")
    p.add_argument("--out-root", type=Path, default=SKILL_ROOT / "OUT")
    p.add_argument("--evidence-min-pct", type=int, default=30)
    p.add_argument("--feature-id", type=str, default=None)
    p.add_argument("--max-secciones", type=int, default=19)
    p.add_argument("--quiet", action="store_true")
    p.add_argument("--no-color", action="store_true")
    p.add_argument("--json", action="store_true", dest="as_json")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    if args.rol == "autor":
        result = run_autor(args)
    else:
        result = run_revisor(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.as_json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif not args.quiet:
        head = f"{BOLD}[run_subagent]{RESET}" if not args.no_color else "[run_subagent]"
        head = head.replace(RESET, "")
        if args.rol == "autor":
            print(f"{head} rol=autor documento={result.get('documento')} "
                  f"filas={len(result.get('filas_ledger_cubiertas', []))} "
                  f"extras={len(result.get('archivos_extra_detectados', []))}",
                  file=sys.stderr)
        else:
            v = result.get("veredicto", "?")
            c = len(result.get("correcciones", []))
            color = GREEN if v == "aprobado" else RED
            print(f"{head} rol=revisor veredicto={color}{v}{RESET} correcciones={c}",
                  file=sys.stderr)
    if "error" in result and result["error"] == "fatal":
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
