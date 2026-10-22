#!/usr/bin/env python3
"""run_subagent.py — Modo **revisor** del subagente definido en
SKILL/references/subagent-{contract,revisor-prompt}.md.

**A partir de A5.2** este script expone **solo** el rol `revisor`.
El antiguo rol `autor` (que era un mock generador de placeholders para
validar el contrato JSON de A4.3) vive ahora en
`run_subagent_placeholder.py` y NO debe usarse para producir documentos
reales de Parte B. Para producir documentos reales, usa el wrapper
`run_subagent_author.sh` (que delega a un LLM externo) o escribe
directamente con el contenido del código + los catálogos A2.x.

Uso:
  run_subagent.py --rol revisor --unit UNIT --out OUT_JSON \\
                  --out-root PROJECT_ROOT [--evidence-min-pct N] \\
                  [--gate-100] [--quiet] [--no-color] [--json]

Notas operativas (lecciones del piloto A5.1):
- `--out-root` debe ser la **raíz del proyecto** (no `OUT/`), porque
  `unit.documento` ya incluye el prefijo `OUT/...` y el script concatena
  `out_root / documento`. Si pasas `--out-root OUT/`, el script busca
  el documento en `OUT/OUT/...` y devuelve `error: fatal`.
- `--gate-100` (o el mapeo automático por `feature_id`) eleva el
  `evidencia_minima_pct` al 100 % para las features 🔒 (F01, F02, F06
  y cualquier unidad del motor B4). El muestreo semántico real sigue
  siendo manual (lo ejecuta el LLM revisor); el script deja el pct
  explícito en el JSON para que el orquestador lo exija.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve()
SKILL_ROOT = SCRIPT_PATH.parent.parent.parent
DEFAULT_INVENTARIO = SKILL_ROOT / "OUT" / "_ledger" / "inventario.json"
DEFAULT_OUT_ROOT = SKILL_ROOT

# Validadores consumidos por el modo revisor.
VALIDATE_EVIDENCE = SKILL_ROOT / "SKILL" / "scripts" / "validate_evidence.py"
VALIDATE_TEMPLATE = SKILL_ROOT / "SKILL" / "scripts" / "validate_template.py"
VALIDATE_MERMAID = SKILL_ROOT / "SKILL" / "scripts" / "validate_mermaid.sh"

CONTRACT_PATH = SKILL_ROOT / "SKILL" / "references" / "subagent-contract.md"
REVISOR_PROMPT_PATH = SKILL_ROOT / "SKILL" / "references" / "subagent-revisor-prompt.md"

# Features 🔒 que exigen muestreo 100% según AGENTS.md §8.
GATE_100_FEATURES: frozenset[str] = frozenset({"F01", "F02", "F06"})

RED = "\033[31m"
GREEN = "\033[32m"
BOLD = "\033[1m"
RESET = "\033[0m"


def load_json(path: Path) -> dict:
    if not path.is_file():
        print(f"ERROR: no existe {path}", file=sys.stderr)
        sys.exit(2)
    return json.loads(path.read_text(encoding="utf-8"))


def _effective_pct(unit: dict, cli_pct: int, gate_100: bool) -> int:
    """Aplica el mapeo de auto-elevación del pct (AGENTS.md §8 +
    subagent-contract.md §4)."""
    if gate_100 or cli_pct >= 100:
        return 100
    feature_id = unit.get("feature_id", "")
    if feature_id in GATE_100_FEATURES:
        return 100
    for dep in unit.get("dependencias", []) or []:
        dep_id = dep.get("id", "") if isinstance(dep, dict) else str(dep)
        if dep_id.startswith("B4."):
            return 100
    return cli_pct


def run_revisor(args: argparse.Namespace) -> dict:
    unit = load_json(args.unit)
    unit_id = unit.get("id", "F?")
    feature_id = args.feature_id or unit.get("feature_id", "F?")

    documento_rel = unit.get("documento")
    if not documento_rel:
        return _fatal("unit.documento no declarado.")
    out_root = Path(args.out_root) if args.out_root else DEFAULT_OUT_ROOT
    doc_path = out_root / documento_rel
    if not doc_path.is_file():
        return _fatal(
            f"documento {doc_path} no existe; ejecuta primero el modo autor "
            f"(mock: run_subagent_placeholder.py; real: run_subagent_author.sh)."
        )

    # Validacion 1: evidence.
    ev = _run_validate_evidence(doc_path, args.inventario)
    # Validacion 2: template.
    tp = _run_validate_template(doc_path)
    # Validacion 3: mermaid.
    mm = _run_validate_mermaid(doc_path)

    correcciones: list[dict] = []
    for err in ev.get("errors", []) or ev.get("errores", []):
        correcciones.append({
            "tipo": "evidence",
            "archivo": str(doc_path.relative_to(SKILL_ROOT)),
            "linea": err.get("line", err.get("linea", 0)),
            "mensaje": err.get("message", err.get("mensaje", str(err))),
        })
    for err in tp.get("errors", []) or tp.get("errores", []):
        correcciones.append({
            "tipo": "template",
            "archivo": str(doc_path.relative_to(SKILL_ROOT)),
            "linea": 0,
            "mensaje": err.get("message", err.get("mensaje", str(err))),
        })
    for err in mm["errores"]:
        correcciones.append({
            "tipo": "mermaid",
            "archivo": err.get("archivo", str(doc_path.relative_to(SKILL_ROOT))),
            "linea": err.get("bloque", 0),
            "mensaje": err.get("mensaje", ""),
        })

    pct = _effective_pct(unit, args.evidence_min_pct, args.gate_100)

    # El muestreo semántico real lo hace el LLM revisor (no este script);
    # este campo documenta el umbral efectivo que el orquestador debe exigir.
    muestreo = {
        "pct": pct,
        "gate_100_explicit": bool(args.gate_100),
        "gate_100_auto": pct == 100 and not args.gate_100,
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
    try:
        data = json.loads(out) if out else {"errors": [], "ok": 0, "refs": 0, "exit": proc.returncode}
    except json.JSONDecodeError:
        data = {"errors": [{"message": out[:200]}], "ok": 0, "refs": 0, "exit": proc.returncode}
    data["exit"] = proc.returncode
    return data


def _run_validate_template(doc_path: Path) -> dict:
    cmd = [
        sys.executable, str(VALIDATE_TEMPLATE),
        "--json", "--quiet", "--no-color",
        str(doc_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    out = proc.stdout.strip()
    try:
        data = json.loads(out) if out else {"errors": [], "exit": proc.returncode}
    except json.JSONDecodeError:
        data = {"errors": [{"message": out[:200]}], "exit": proc.returncode}
    data["exit"] = proc.returncode
    return data


def _run_validate_mermaid(doc_path: Path) -> dict:
    cmd = [
        "bash", str(VALIDATE_MERMAID),
        "--quiet", "--no-color",
        str(doc_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    out = (proc.stdout or "") + (proc.stderr or "")
    errores: list[dict] = []
    for line in out.splitlines():
        if "ERROR" in line and ":" in line:
            # formato: "ERROR <ruta>:<n>: <msg>"
            try:
                _, payload = line.split("ERROR", 1)
                payload = payload.strip()
                ruta_bloque, _, mensaje = payload.partition(":")
                ruta, _, bloque = ruta_bloque.rpartition(":")
                errores.append({
                    "archivo": ruta.strip(),
                    "bloque": int(bloque.strip() or 0),
                    "mensaje": mensaje.strip(),
                })
            except (ValueError, IndexError):
                errores.append({"mensaje": line.strip()})
    bloques_ok = 0
    bloques_ko = len(errores)
    # Resumen tipo "5 bloques (5 OK)" / "5 bloques (4 OK / 1 FAIL)"
    for line in out.splitlines():
        if "bloques" in line and ("OK" in line or "FAIL" in line):
            import re as _re
            m = _re.search(r"(\d+)\s+bloques", line)
            if m:
                total = int(m.group(1))
                bloques_ko_match = _re.search(r"(\d+)\s+FAIL", line)
                if bloques_ko_match:
                    bloques_ko = int(bloques_ko_match.group(1))
                bloques_ok = total - bloques_ko
            break
    return {
        "exit": proc.returncode,
        "bloques_ok": bloques_ok,
        "bloques_ko": bloques_ko,
        "errores": errores,
    }


def _fatal(msg: str) -> dict:
    return {
        "schema_version": 1,
        "error": "fatal",
        "mensaje": msg,
    }


def parse_args(argv=None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Modo revisor del subagente de A5.2. Ejecuta los 3 validadores "
            "reales (evidence, template, mermaid) sobre el documento de la "
            "unidad y emite un veredicto estricto. El muestreo semántico "
            "lo hace el LLM externo; este script deja el umbral efectivo "
            "(con auto-elevación para features 🔒) en el JSON de salida."
        )
    )
    p.add_argument("--rol", choices=["revisor"], required=True,
                   help="(A5.2+) Solo se admite 'revisor'. El antiguo modo "
                        "'autor' está en run_subagent_placeholder.py.")
    p.add_argument("--unit", type=Path, required=True)
    p.add_argument("--src-root", type=Path, default=SKILL_ROOT / "SRC")
    p.add_argument("--inventario", type=Path, default=DEFAULT_INVENTARIO)
    p.add_argument("--extract-dir", type=Path,
                   default=SKILL_ROOT / "OUT" / "_ledger" / "extract")
    p.add_argument("--plantilla", type=Path,
                   default=SKILL_ROOT / "SKILL" / "references" / "feature-template.md")
    p.add_argument("--out", type=Path, required=True, help="JSON de salida.")
    p.add_argument("--out-root", type=Path, default=DEFAULT_OUT_ROOT,
                   help="Raíz del PROYECTO (no OUT/). El script concatena "
                        "out_root / unit.documento; unit.documento ya "
                        "empieza por 'OUT/...'.")
    p.add_argument("--evidence-min-pct", type=int, default=30,
                   help="Umbral de muestreo semántico (0-100). Default 30. "
                        "Se eleva automáticamente a 100 para F01/F02/F06 "
                        "y unidades del motor B4 (ver AGENTS.md §8).")
    p.add_argument("--gate-100", action="store_true",
                   help="Fuerza evidencia_min_pct=100 sin importar la "
                        "feature_id (útil para 🔒 fuera de la lista "
                        "anterior o para re-verificaciones forzadas).")
    p.add_argument("--feature-id", type=str, default=None)
    p.add_argument("--max-secciones", type=int, default=19)
    p.add_argument("--quiet", action="store_true")
    p.add_argument("--no-color", action="store_true")
    p.add_argument("--json", action="store_true", dest="as_json")
    return p.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    if args.rol != "revisor":
        return _fatal_mensaje(
            f"--rol '{args.rol}' ya no se admite. Use 'revisor' (este "
            f"script) o invoque run_subagent_placeholder.py para el mock "
            f"de A4.3."
        )
    result = run_revisor(args)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if args.as_json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif not args.quiet:
        head = f"{BOLD}[run_subagent]{RESET}" if not args.no_color else "[run_subagent]"
        head = head.replace(RESET, "")
        v = result.get("veredicto", "?")
        c = len(result.get("correcciones", []))
        pct = result.get("muestreo_verificado", {}).get("pct", "?")
        color = GREEN if v == "aprobado" else RED
        print(f"{head} rol=revisor veredicto={color}{v}{RESET} "
              f"correcciones={c} pct_efectivo={pct}",
              file=sys.stderr)
    if "error" in result and result["error"] == "fatal":
        return 2
    return 0


def _fatal_mensaje(mensaje: str) -> int:
    print(f"ERROR: {mensaje}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
