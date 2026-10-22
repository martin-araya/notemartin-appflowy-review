#!/usr/bin/env python3
"""validate_template.py — verifica que un `.md` cumple la plantilla
obligatoria (frontmatter con 5 campos + secciones numeradas en
orden).

Fase A3.3 de la skill `notemartin-appflowy-review`.
Spec: ROADMAP.md línea 89 y SKILL/references/{feature,export}-template.md.

Uso: validate_template.py [opciones] PATH [PATH …]

Plantillas soportadas en v1:
  feature    → 19 obligatorias (## 1. … ## 19.) + opcional ## 20.
               id ∈ /^F\d+(\.\d+)?$/  ·  estado ∈ {verificado, pendiente, sin_asignar}
  export     → 11 obligatorias (## 1. … ## 11.).
               id ∈ /^B\d+(\.\d+)?$/  ·  estado ∈ {verificado, pendiente}
  structure  → 11 obligatorias (## 1. … ## 11.).
               id ∈ /^B1\.\d+(-[a-z0-9]+)?$/      ·  estado ∈ {verificado, pendiente}
               (documentos raíz del Bloque B1: estructura del repo, stack,
                arquitectura, arranque, puente, motor collab, persistencia)
bridge     → 11 obligatorias (## 1. … ## 11.).
                id ∈ /^06-\d{2}-[a-z-]+$/  ·  estado ∈ {verificado, pendiente}
                (sub-documentos del Bloque B1.5: puente FFI, con 5+ sub-docs
                 por carpeta: 06-NN-ffi, 06-NN-lib-dispatch, etc.)
catalogue  → 10 obligatorias (## 1. … ## 10.).
                 id ∈ /^1[1-6]-[a-z0-9-]+$/ ·  estado ∈ {verificado, pendiente}
                (catálogos del Bloque B2: 11-eventos-ffi, 12-protobuf,
                 13-blocs, 14-notificaciones, 15-errores, 16-flags-rutas-atajos)
  transversal → 8 obligatorias (## 1. … ## 8.).
                 id ∈ /^B6\.[123]$/  ·  estado ∈ {verificado, pendiente}
                (docs transversales del Bloque B6: 18-build-ci-distribucion,
                 19-testing, 20-seguridad-y-privacidad)
  resumen     → 7 obligatorias (## 1. … ## 7.).
                 id ∈ /^B6\.4$/  ·  estado ∈ {verificado, pendiente}
                (01-resumen-ejecutivo: narrativa, sin sección de pendientes)
  glosario    → 8 obligatorias (## 1. … ## 8.).
                 id ∈ /^B6\.5$/  ·  estado ∈ {verificado, pendiente}
                (21-glosario: entradas término → definición + evidencia)

Auto-detección: si el `id` matchea `^F\d+…` o `^B5…` → feature;
si `^B\d+…` → export.
Si matchea `^B1\.\d+$` específicamente → structure (antes que export).
Si matchea `^0[6-9]-\d{2}-[a-z-]+$` → bridge (antes que export).
Si matchea `^11-[a-z0-9-]+$` → catalogue (antes que export).
Si matchea `^B6\.[123]$` → transversal, `^B6\.4$` → resumen,
`^B6\.5$` → glosario (todos antes que export, que también matchearía `^B\d+`).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
PROJECT_ROOT_DEFAULT = SKILL_DIR.parent
DEFAULT_OUTPUT_SKELETON = PROJECT_ROOT_DEFAULT / "SKILL" / "templates" / "output-skeleton"

RED = "\033[31m"
GREEN = "\033[32m"
DIM = "\033[2m"
RESET = "\033[0m"

REQUIRED_FRONTMATTER_FIELDS = ("id", "titulo", "fuente", "archivos_cubiertos", "estado")

TEMPLATES = {
    "feature": {
        "required_sections": list(range(1, 20)),  # 1..19
        "optional_sections": [20],
        # B5 (secuencias globales) reusa la plantilla feature: 19 secciones +
        # 1 opcional. La plantilla export no admite el grueso de la prosa
        # requerida para una secuencia global.
        "id_pattern": re.compile(r"^(?:F\d+|B5)(?:\.\d+)*$"),
        "estados": {"verificado", "pendiente", "sin_asignar"},
    },
    "export": {
        "required_sections": list(range(1, 12)),  # 1..11
        "optional_sections": [],
        "id_pattern": re.compile(r"^B\d+(\.\d+)?$"),
        "estados": {"verificado", "pendiente"},
    },
    "structure": {
        "required_sections": list(range(1, 12)),  # 1..11
        "optional_sections": [],
        "id_pattern": re.compile(r"^B1\.\d+(-[a-z0-9]+)?$"),
        "estados": {"verificado", "pendiente"},
    },
    "bridge": {
        "required_sections": list(range(1, 12)),  # 1..11
        "optional_sections": [],
        "id_pattern": re.compile(r"^0[6-9]-\d{2}-[a-z-]+$"),
        "estados": {"verificado", "pendiente"},
    },
    "catalogue": {
        "required_sections": list(range(1, 11)),  # 1..10
        "optional_sections": [],
        "id_pattern": re.compile(r"^1[1-6]-[a-z0-9-]+$"),
        "estados": {"verificado", "pendiente"},
    },
    "transversal": {
        "required_sections": list(range(1, 9)),  # 1..8
        "optional_sections": [],
        "id_pattern": re.compile(r"^B6\.[123]$"),
        "estados": {"verificado", "pendiente"},
    },
    "resumen": {
        "required_sections": list(range(1, 8)),  # 1..7
        "optional_sections": [8],
        "id_pattern": re.compile(r"^B6\.4$"),
        "estados": {"verificado", "pendiente"},
    },
    "glosario": {
        "required_sections": list(range(1, 9)),  # 1..8
        "optional_sections": [],
        "id_pattern": re.compile(r"^B6\.5$"),
        "estados": {"verificado", "pendiente"},
    },
}

RE_SECTION = re.compile(r"^##\s+(\d+)\.\s")


# --- YAML minimalista (sin PyYAML) ----------------------------------------


def parse_yaml(lines: list[str]) -> dict:
    """Parser YAML minimal: soporta `key: value`, `key: [a, b, c]` y
    `key:` + lista indentada con `- valor`. No soporta multi-línea con
    `>` o `|`, anclas, aliases, ni tipos explícitos.
    """
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
            # lista en líneas siguientes
            items: list = []
            j = i + 1
            while j < len(lines):
                nxt = lines[j]
                nxt_stripped = nxt.strip()
                if not nxt_stripped:
                    j += 1
                    continue
                if nxt_stripped.startswith("- "):
                    items.append(nxt_stripped[2:].strip())
                    j += 1
                    continue
                # otra `key:` o cualquier otra cosa → fin de la lista
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


def split_frontmatter(text: str) -> tuple[dict | None, str, int]:
    """Divide `text` en (frontmatter_dict, body, fm_end_line_1based).

    Devuelve (None, text, 0) si el archivo no abre con `---`.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text, 0
    for idx, line in enumerate(lines[1:], start=2):
        if line.strip() == "---":
            yaml_text = lines[1 : idx - 1]
            body = "\n".join(lines[idx:])
            return parse_yaml(yaml_text), body, idx
    return None, text, 0


# --- Extracción de secciones ----------------------------------------------


def extract_section_numbers(body: str) -> list[tuple[int, int]]:
    """Devuelve [(N, line_1based), …] de headings `## N.` (excluyendo
    los que están dentro de bloques ```fenced```).
    """
    out: list[tuple[int, int]] = []
    in_fence = False
    for i, line in enumerate(body.splitlines(), 1):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        m = RE_SECTION.match(line)
        if m:
            out.append((int(m.group(1)), i))
    return out


# --- Auto-detección de plantilla -------------------------------------------


def detect_template(id_value: str | None) -> str | None:
    if not id_value:
        return None
    if TEMPLATES["feature"]["id_pattern"].match(id_value):
        return "feature"
    if TEMPLATES["catalogue"]["id_pattern"].match(id_value):
        return "catalogue"
    if TEMPLATES["structure"]["id_pattern"].match(id_value):
        return "structure"
    if TEMPLATES["bridge"]["id_pattern"].match(id_value):
        return "bridge"
    # Las plantillas del Bloque B6 se resuelven antes que `export`, cuyo patrón
    # `^B\d+(\.\d+)?$` también matchearía `B6.1`, `B6.4` y `B6.5`.
    if TEMPLATES["transversal"]["id_pattern"].match(id_value):
        return "transversal"
    if TEMPLATES["resumen"]["id_pattern"].match(id_value):
        return "resumen"
    if TEMPLATES["glosario"]["id_pattern"].match(id_value):
        return "glosario"
    if TEMPLATES["export"]["id_pattern"].match(id_value):
        return "export"
    return None


# --- Validación ----------------------------------------------------------


@dataclass
class Error:
    code: str
    detail: str
    line: int = 0

    def to_dict(self) -> dict:
        return {"code": self.code, "detail": self.detail, "line": self.line}


def validate_document(
    md: Path,
    text: str,
    template_override: str | None,
    allow_extra: bool,
) -> list[Error]:
    errors: list[Error] = []
    fm, body, fm_end = split_frontmatter(text)
    if fm is None:
        errors.append(
            Error("E_NO_FRONTMATTER", "archivo no abre con '---' (frontmatter ausente)", 1)
        )
        return errors

    # Campos obligatorios
    for field_name in REQUIRED_FRONTMATTER_FIELDS:
        if field_name not in fm:
            errors.append(
                Error(
                    "E_MISSING_FRONTMATTER_FIELD",
                    f"falta campo obligatorio '{field_name}'",
                    fm_end,
                )
            )

    # Validación de tipo: archivos_cubiertos debe ser lista
    if "archivos_cubiertos" in fm and not isinstance(fm["archivos_cubiertos"], list):
        errors.append(
            Error(
                "E_BAD_FRONTMATTER_TYPE",
                f"'archivos_cubiertos' debe ser lista (got {type(fm['archivos_cubiertos']).__name__})",
                fm_end,
            )
        )

    # fuente puede ser string o lista
    if "fuente" in fm and not isinstance(fm["fuente"], (str, list)):
        errors.append(
            Error(
                "E_BAD_FRONTMATTER_TYPE",
                f"'fuente' debe ser string o lista (got {type(fm['fuente']).__name__})",
                fm_end,
            )
        )

    # titulo debe ser string
    if "titulo" in fm and not isinstance(fm["titulo"], str):
        errors.append(
            Error(
                "E_BAD_FRONTMATTER_TYPE",
                f"'titulo' debe ser string (got {type(fm['titulo']).__name__})",
                fm_end,
            )
        )

    # Determinar plantilla
    id_value = fm.get("id") if isinstance(fm, dict) else None
    if template_override:
        template = template_override
    else:
        template = detect_template(id_value) or ""

    if not template:
        errors.append(
            Error(
                "E_UNKNOWN_TEMPLATE",
                f"no se pudo inferir plantilla del id='{id_value}' (use --template)",
                fm_end,
            )
        )
        return errors

    tpl = TEMPLATES[template]

    # Validar id matchea el patrón de la plantilla
    if id_value and not tpl["id_pattern"].match(id_value):
        errors.append(
            Error(
                "E_ID_MISMATCH",
                f"id='{id_value}' no matchea el patrón de '{template}' "
                f"({tpl['id_pattern'].pattern})",
                fm_end,
            )
        )

    # Validar estado
    estado = fm.get("estado")
    if estado is not None and estado not in tpl["estados"]:
        errors.append(
            Error(
                "E_BAD_ESTADO",
                f"estado='{estado}' no está en {sorted(tpl['estados'])} para '{template}'",
                fm_end,
            )
        )

    # Validar secciones
    sections = extract_section_numbers(body)
    nums = [n for n, _ in sections]

    # E_OUT_OF_ORDER
    if nums != sorted(nums):
        # Encontrar la primera inversión
        first_bad = next(
            (i for i in range(1, len(nums)) if nums[i] < nums[i - 1]), 0
        )
        bad_n = nums[first_bad] if first_bad < len(nums) else -1
        line_n = (
            next((l for n, l in sections if n == bad_n), 0) if bad_n > 0 else 0
        )
        errors.append(
            Error(
                "E_OUT_OF_ORDER",
                f"sección {bad_n} (línea {line_n}) está fuera de orden "
                f"(anterior: {nums[first_bad - 1] if first_bad > 0 else 'N/A'})",
                line_n,
            )
        )

    # E_DUPLICATE_SECTION
    seen: set = set()
    duplicates: list[int] = []
    for n, line in sections:
        if n in seen and n not in duplicates:
            duplicates.append(n)
        seen.add(n)
    if duplicates:
        errors.append(
            Error(
                "E_DUPLICATE_SECTION",
                f"secciones duplicadas: {duplicates}",
                0,
            )
        )

    # E_MISSING_SECTION
    required = set(tpl["required_sections"])
    present = set(nums)
    missing = sorted(required - present)
    if missing:
        errors.append(
            Error(
                "E_MISSING_SECTION",
                f"faltan secciones: {missing}",
                0,
            )
        )

    # E_EXTRA_SECTION
    allowed = required | set(tpl["optional_sections"])
    extras = sorted(set(nums) - allowed)
    if extras:
        severity = "warn" if allow_extra else "fail"
        errors.append(
            Error(
                "E_EXTRA_SECTION",
                f"secciones fuera del rango permitido: {extras} (severity={severity})",
                0,
            )
        )

    # E_EMPTY_SECTION: una sección sin contenido (sólo la siguiente o
    # sólo líneas en blanco) antes de la próxima `## N.`
    body_lines = body.splitlines()
    for idx, (n, line) in enumerate(sections):
        next_line = sections[idx + 1][1] if idx + 1 < len(sections) else len(body_lines) + 1
        # Contar líneas con contenido real entre `line` (exclusive) y
        # `next_line` (exclusive).
        has_content = False
        for j in range(line, next_line - 1):
            if j - 1 < len(body_lines):
                candidate = body_lines[j].strip()
                if candidate and not candidate.startswith("#"):
                    has_content = True
                    break
        if not has_content:
            errors.append(
                Error(
                    "E_EMPTY_SECTION",
                    f"sección {n} sin contenido (línea {line})",
                    line,
                )
            )

    return errors


# --- Recolección de archivos ----------------------------------------------


# Ficheros de `OUT/` que no son documentos de plantilla por diseño:
#   - `00-INDEX.md` lo regenera `build_index.py` y su frontmatter lo escribe el
#     propio script, no una plantilla de feature;
#   - `22-preguntas-abiertas.md` se organiza en secciones `## Ax.x · …` (registro
#     cronológico), no en secciones numeradas;
#   - `STATE.md` es el cuaderno de estado entre sesiones, no un documento.
META_DOCS = {"00-INDEX.md", "22-preguntas-abiertas.md", "STATE.md"}


def collect_md_files(paths: list[Path]) -> list[Path]:
    out: list[Path] = []
    for p in paths:
        if p.is_file():
            if p.suffix == ".md":
                out.append(p)
            continue
        if p.is_dir():
            for root, dirs, files in os.walk(p):
                dirs[:] = [
                    d
                    # `_ledger/` es el cuaderno de trabajo de la skill (inventario,
                    # briefs, artefactos de prueba de subagentes), no un árbol de
                    # entregable: sus `.md` no llevan frontmatter por diseño y no
                    # se validan contra ninguna plantilla.
                    for d in dirs
                    if d not in (".git", "node_modules", "_wip", "fixtures", "_ledger")
                ]
                for name in sorted(files):
                    if name.endswith(".md") and name not in META_DOCS:
                        out.append(Path(root) / name)
    return sorted(out)


# --- Salida --------------------------------------------------------------


def c_red(s: str, no_color: bool) -> str:
    return s if no_color else f"{RED}{s}{RESET}"


def c_green(s: str, no_color: bool) -> str:
    return s if no_color else f"{GREEN}{s}{RESET}"


def c_dim(s: str, no_color: bool) -> str:
    return s if no_color else f"{DIM}{s}{RESET}"


def print_error(doc: Path, err: Error, no_color: bool) -> None:
    line_part = f" (línea {err.line})" if err.line else ""
    print(
        f"{c_red('ERROR', no_color)} {doc}: {err.code}: {err.detail}{line_part}",
        file=sys.stderr,
    )


# --- Main ----------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="validate_template.py",
        description=(
            "Verifica que un .md cumple la plantilla obligatoria "
            "(frontmatter + secciones numeradas en orden)."
        ),
    )
    parser.add_argument("paths", nargs="+", type=Path, help="Archivos .md o directorios.")
    parser.add_argument(
        "-t",
        "--template",
        choices=sorted(TEMPLATES.keys()),
        help="Plantilla a aplicar (auto-detect por id si ausente).",
    )
    parser.add_argument("--json", action="store_true", help="Salida JSON estructurado.")
    parser.add_argument("--quiet", action="store_true", help="Sólo summary final.")
    parser.add_argument("--no-color", action="store_true", help="Desactiva ANSI.")
    parser.add_argument(
        "--allow-extra-sections",
        action="store_true",
        help="E_EXTRA_SECTION se reporta como warn, no como fail.",
    )
    args = parser.parse_args(argv)

    files = collect_md_files(args.paths)
    if not files:
        print(
            f"validate_template.py: no se encontraron .md en {args.paths}",
            file=sys.stderr,
        )
        return 2

    summary = {"files": 0, "ok": 0, "errors": 0, "warns": 0}
    errors_out: list[dict] = []

    extra_is_warn = args.allow_extra_sections

    for md in files:
        try:
            text = md.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            print(f"  (aviso) no se pudo leer {md}: {e}", file=sys.stderr)
            continue
        summary["files"] += 1
        doc_errors = validate_document(md, text, args.template, extra_is_warn)

        # Filtrar E_EXTRA_SECTION si allow_extra_sections
        filtered: list[Error] = []
        for e in doc_errors:
            if e.code == "E_EXTRA_SECTION" and extra_is_warn:
                summary["warns"] += 1
                # reportar como warn
                if not args.json:
                    print(
                        f"{c_dim('WARN', args.no_color)} {md}: {e.code}: {e.detail}",
                        file=sys.stderr,
                    )
            else:
                filtered.append(e)

        if not filtered:
            summary["ok"] += 1
            if not args.quiet and not args.json:
                print(
                    f"{md}: {c_green('OK', args.no_color)}",
                    file=sys.stderr,
                )
        else:
            summary["errors"] += len(filtered)
            for e in filtered:
                errors_out.append(
                    {"doc": str(md), **e.to_dict()}
                )
                if not args.json:
                    print_error(md, e, args.no_color)
            if not args.quiet and not args.json:
                print(
                    f"{md}: {len(filtered)} error(es)",
                    file=sys.stderr,
                )

    if args.json:
        out = {
            "summary": summary,
            "errors": errors_out,
            "schema_version": "1.0",
        }
        print(json.dumps(out, indent=2, ensure_ascii=False))
    else:
        trailer = (
            f"--- summary: files={summary['files']} "
            f"ok={summary['ok']} errors={summary['errors']} "
            f"warns={summary['warns']} ---"
        )
        print(trailer, file=sys.stderr)

    return 1 if summary["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
