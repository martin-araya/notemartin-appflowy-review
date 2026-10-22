#!/usr/bin/env python3
"""make_unit_brief.py — genera el brief de una unidad de trabajo para el
subagente autor.

El brief es un `.md` autocontenido con: la unidad (ids, rutas, documento),
la lista completa de archivos, el foco heredado del ROADMAP para esa feature,
las correcciones de scope aplicables y las pruebas literales. Evita reescribir
un prompt largo en cada llamada y garantiza que el subagente y el orquestador
vean exactamente los mismos datos.

Uso:
  python3 make_unit_brief.py --unit F00.1
  python3 make_unit_brief.py --unit F09.1 --foco extra           # añade §Foco
  python3 make_unit_brief.py --feature F00          # todas las de la feature
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
UNITS = PROJECT_ROOT / "OUT" / "_ledger" / "units"
BRIEFS = PROJECT_ROOT / "OUT" / "_ledger" / "briefs"

# Foco por feature, heredado del ROADMAP (Bloque B3).
FOCO: dict[str, str] = {
    "F00": "Infraestructura compartida: FFI y dispatcher, errores y SQLite, "
           "build/codegen, crates -pub y paquetes Dart internos.",
    "F02": "Bases de datos. Ya documentadas F02.0-F02.12; esta unidad cubre "
           "lo que quedaba sin verificar.",
    "F08": "Búsqueda e indexación: `flowy-search` (tantivy), indexación en "
           "`flowy-core` y la UI del command palette.",
    "F09": "IA: chat (streaming, mensajes, adjuntos, miembros), completion, IA "
           "local (`local_ai/*`), MCP, embeddings + `flowy-sqlite-vec`, "
           "selección de modelo, offline, edición de documento desde chat, "
           "middleware y `ai_tool`.",
    "F10": "Importación: detalle de UI y orquestación. El motor va en B4.",
    "F11": "Exportación: detalle de UI y orquestación. El motor va en B4.",
    "F12": "Compartir, publicar, niveles de acceso y shared section.",
    "F13": "Ajustes, apariencia, temas (incl. `theme_upload`) y fuentes.",
    "F14": "Internacionalización: inlang, `easy_localization`, flujo de claves.",
    "F15": "Notificaciones in-app, recordatorios y `flowy-date`.",
    "F16": "Mobile: shell de la app y editor móvil.",
    "F17": "Plataforma: ventanas, deeplinks, auto-update, hotkeys, feature "
           "flags, captura de errores y logging (`lib-log`, `log_filter.rs`).",
    "F18": "Motor Collab: `collab-plugins`, `collab-importer`, "
           "`collab-entity` y `collab-derive`.",
    "F19": "Repo del editor: tests, ejemplos, `lib/l10n` y configuración.",
    "F20": "Raíz de AppFlowy-Collab: configuración, CI, docs y manifests.",
    "F21": "Icon/Emoji picker (Dart UI) en `shared/icon_emoji_picker/`.",
}

SCOPE: dict[str, str] = {
    "F13": "El ROADMAP atribuía los widgets de miembros ("
           "`settings/widgets/members/**`) a F12; el triage de B0.2 los dejó "
           "en **F13**. Decláralo en §2 y §13. El emoji picker de Ajustes "
           "(`settings/widgets/emoji_picker/`) es distinto del de F21.",
    "F14": "**El único bundle de traducciones del repo es "
           "`appflowy/frontend/resources/translations/*.json` (32 ficheros) y "
           "está asignado a F00.7.1**, no a F14; decláralo en §2 y §13 y "
           "referencia `[[F00.7.1]]`. Las 1637 claves ya están catalogadas en "
           "`16-catalogo-flags-rutas-atajos.md §7` (B2.6).",
    "F15": "`flowy-notification/**` ya está documentado en "
           "`06-puente-flutter-rust/04-notificaciones.md` (B1.5 §04): "
           "cross-ref, no re-verifiques.",
    "F12": "`flowy-folder/src/share/import.rs` (motor de importación, B4.11) y "
           "`publish_util.rs` (publicación web, B4.12) están en esta unidad "
           "pero el ROADMAP los sitúa en B4: decláralo en §2 y §13.",
    "F10": "El motor de importación (markdown, CSV, Notion/ZIP) está en B4 y "
           "en F18.2 (`collab-importer`). Esta unidad es solo UI+orquestación.",
    "F11": "El motor de exportación está en B4.0–B4.7 y en F01.0.3.3 "
           "(encoders del editor). Esta unidad es solo UI+orquestación.",
    "F16": "`editor_plugins/{mobile_toolbar_v3,mobile_floating_toolbar}` "
           "están asignados a **F01.6.4** (ya verificado), no a F16: es la "
           "corrección de scope que da sentido a la unidad `F16.2`.",
    "F18": "`collab-plugins/src/{cloud_storage/**,connect_state.rs}` estaba "
           "redirigida desde F06 hacia F18 en el cierre de B3.F03..F07: "
           "declara esa redirección en §2 y §13.",
    "F00": "F00 es la feature con más superficie: documenta qué **añade** "
           "respecto de `06-puente-flutter-rust/` (B1.5), `08-persistencia/` "
           "(B1.7) y `17-grafo-dependencias.md` (B1.2), y no repitas su "
           "contenido: cross-ref explícito en §2 y §19.",
    "F21": "F21 se creó en el triage de B0.2 sin título (la unidad decía "
           "`titulo: \"F21\"` y apuntaba a `F21-f21/`); el título canónico es "
           "**Icon/Emoji picker** y el directorio `F21-icon-emoji-picker/`.",
}

GATE_100 = {"F00.1", "F18.1", "F18.2", "F17", "B6.1", "B6.3"}

# Foco heredado del ROADMAP para los bloques transversales B4/B5/B6.
FOCO_BLOQUES: dict[str, str] = {
    "B6.1": "Build, CI y distribución: `codemagic.yaml`, los 12 workflows de "
            "`.github/workflows/`, los 10 fragmentos de `frontend/scripts/makefile/` "
            "que `frontend/Makefile.toml` incluye, los scripts de codegen, los "
            "de empaquetado por plataforma (deb, AppImage, Flatpak, Inno Setup, "
            "DMG universal), los de white-label, los de entorno de desarrollo y "
            "los `tool/update_*.sh` que fijan las revisiones de las fuentes "
            "externas; más `cargokit_options.yaml`, `distribute_options.yaml`, "
            "`build.yaml` y los perfiles `[profile.*]` de los `Cargo.toml`.",
    "B6.2": "Testing: `test/{bloc_test,unit_test,widget_test}` en Dart, los 9 "
            "`integration_test/desktop_runner_*.dart` más `mobile_runner_1.dart`, "
            "los subdirectorios `integration_test/{desktop,mobile,shared}` y el "
            "crate Rust `event-integration-test` con sus `src/*_event.rs` y "
            "`tests/{chat,database,document,folder,search,sql_test,user,asset}`.",
    "B6.3": "Seguridad y privacidad: servicios de auth de Dart y Rust, ciclo "
            "del token de sesión, almacenamiento en reposo (SQLite, KV, cachés, "
            "vectores), qué datos salen del cliente y con qué encabezado, y el "
            "corte IA local frente a IA cloud.",
    "B6.4": "Resumen ejecutivo: síntesis narrativa de todo `OUT/`. Distinto de "
            "`00-INDEX.md`, que es la tabla técnica regenerable.",
    "B6.5": "Glosario: consolidación terminológica de todo `OUT/`, con al menos "
            "una evidencia `ruta:línea` por entrada.",
    "B6.5.2": "Preguntas abiertas: consolidación final de todos los "
               "`[NO DETERMINADO]` de `OUT/` vía `harvest_open_questions.py`.",
}

# Instrucciones de plantilla por bloque transversal.
PLANTILLA_BLOQUE: dict[str, tuple[str, str, str]] = {
    # id -> (plantilla validate_template, nº de secciones, ruta de la referencia)
    "B6.1": ("transversal", "8", "SKILL/references/feature-template.md §5.7"),
    "B6.2": ("transversal", "8", "SKILL/references/feature-template.md §5.7"),
    "B6.3": ("transversal", "8", "SKILL/references/feature-template.md §5.7"),
    "B6.4": ("resumen", "7", "SKILL/references/feature-template.md §5.7"),
    "B6.5": ("glosario", "8", "SKILL/references/feature-template.md §5.7"),
}


def es_transversal(u: dict) -> bool:
    """Una unidad es transversal si su `archivos` es una lista de cadenas
    (esquema B4/B5/B6) en vez de una lista de dicts `{ruta, capa, fuente}`
    (esquema de features F*)."""
    arch = u.get("archivos") or []
    return bool(arch) and isinstance(arch[0], str)


def fuente_de(ruta: str) -> str:
    return ruta.split("/", 1)[0] if "/" in ruta else "appflowy"


SECCIONES_TRANSVERSAL = {
    "transversal": [
        "Resumen (3–6 líneas)",
        "Alcance (qué entra y qué queda fuera, con enlaces a los docs ya "
        "escritos que covers lo mismo)",
        "Mapa de fuentes (tabla de archivos con `ruta:línea`)",
        "Diagramas (Mermaid opcional; cada uno precedido de la frase que dice "
        "qué muestra y seguido de su lectura en prosa)",
        "Hallazgos clave (párrafos o tabla, con evidencia `ruta:línea` verbatim)",
        "Riesgos, huecos y decisiones de diseño pendientes "
        "(aquí van los `[NO DETERMINADO]`)",
        "Relacionado con (enlaces `[[X]]` a features, bloques y catálogos)",
        "Evidencias y etiquetas (conteo `[VERIFICADO]` / `[INFERIDO]` / "
        "`[NO DETERMINADO]`)",
    ],
    "resumen": [
        "Resumen ejecutivo (3–6 líneas)",
        "Qué es AppFlowy y qué resuelve",
        "Arquitectura en una página (capas y contenedor C4 nivel 1)",
        "Mapa de features (un párrafo por F01–F21 con enlace `[[Fxx]]`)",
        "Los motores (CRDT, persistencia, búsqueda, IA, export/import)",
        "Métricas del proyecto y guía de navegación de `OUT/`",
        "Relacionado con",
    ],
    "glosario": [
        "Resumen (3–6 líneas)",
        "Alcance y criterio de inclusión de términos",
        "Convenciones de lectura (formato de entrada y de evidencia)",
        "Glosario A–F",
        "Glosario G–M",
        "Glosario N–S",
        "Glosario T–Z",
        "Relacionado con",
    ],
}


def _brief_transversal(u: dict, uid: str) -> int:
    """Genera el brief de una unidad transversal (esquema B4/B5/B6, donde
    `archivos` es una lista de rutas planas)."""
    tpl, nsec, _ref = PLANTILLA_BLOQUE.get(uid, ("transversal", "8", ""))
    tpl = u.get("plantilla", tpl)
    secciones = SECCIONES_TRANSVERSAL.get(tpl, SECCIONES_TRANSVERSAL["transversal"])
    rutas = u["archivos"]
    fuentes = sorted({fuente_de(r) for r in rutas})
    sintesis = bool(u.get("sintesis"))

    lines = [
        f"# Brief de unidad {uid} — {u['titulo']}",
        "",
        f"- **Unidad**: `{uid}` (`OUT/_ledger/units/{uid}.json`)",
        f"- **Bloque**: transversal (no ancla archivos a `cobertura.csv`; los "
        f"ficheros ya pertenecen a features F* y están verificados al 100 %)",
        f"- **Documento a escribir**: `{u['documento']}`",
        f"- **Archivos fuente**: {u['archivos_total']}",
        f"- **Fuentes**: {', '.join(fuentes)}",
        f"- **Plantilla**: `{tpl}` — {nsec} secciones obligatorias",
        f"- **Evidencia mínima**: {u.get('evidence_min_pct', 90)} % verbatim",
    ]
    if uid in GATE_100:
        lines.append("- **Revisión gate-100**: el revisor verificará el 100 % de "
                     "las afirmaciones, no una muestra.")
    if sintesis:
        lines.append(
            "- **Documento de síntesis**: su relato sale de `OUT/`, pero toda "
            "afirmación técnica se ancla en un fichero de `SRC/` para que "
            "`validate_evidence.py` pueda resolverla. Los documentos de `OUT/` "
            "citados no son evidencia validable."
        )
    if u.get("consolidacion"):
        lines.append(
            "- **Documento de consolidación**: se ejecuta "
            "`python3 SKILL/scripts/harvest_open_questions.py --dry-run` y "
            "después sin `--dry-run`; no se reescribe prosa previa."
        )
    if u.get("documentos_representados"):
        lines += ["", "## Documentos de `OUT/` que resume (no son evidencia)", ""]
        lines += [f"- `{d}`" for d in u["documentos_representados"]]

    lines += ["", "## Foco de esta unidad", "", FOCO_BLOQUES.get(uid, "(sin foco declarado)"), ""]
    if u.get("nota"):
        lines += ["## Nota de la unidad", "", u["nota"], ""]

    lines += ["## Secciones obligatorias del documento", ""]
    for i, s in enumerate(secciones, start=1):
        lines.append(f"{i}. **{s}**")
    lines += [
        "",
        "## Archivos de la unidad (rutas relativas a `SRC/<fuente>/`)",
        "",
    ]
    lines += [f"- `{r}`" for r in rutas]

    valida = [
        "```sh",
        f'python3 SKILL/scripts/validate_template.py "{u["documento"]}" --quiet',
        f'python3 SKILL/scripts/validate_evidence.py --inventario '
        f'OUT/_ledger/inventario.json "{u["documento"]}"',
    ]
    if tpl == "transversal":
        valida.append(
            f'bash SKILL/scripts/validate_mermaid.sh "{u["documento"]}"'
        )
    valida += [
        "python3 SKILL/scripts/harvest_open_questions.py --dry-run",
        "```",
    ]

    lines += [
        "",
        "## Cómo trabajar",
        "",
        "1. Lee `AGENTS.md` (§6 reglas de evidencia), "
        "`SKILL/references/evidence-rules.md` y "
        "`SKILL/references/diagram-conventions.md`.",
        "2. Lee **todos** los archivos de la unidad desde `SRC/`. Para listar el "
        "contenido real de un directorio usa `find` o `ls -R`: los ficheros de "
        "test y de workflow no se inventan, se enumeran.",
        "3. Si un documento de `OUT/` ya cubre parte de tu materia, **cruza** en "
        "lugar de repetir: cita `[[Fxx]]` o `[[B4.x]]` y explica en §2 qué "
        "añades.",
        "4. Escribe el documento en la ruta indicada, con las secciones obligatorias "
        "en orden y sin secciones numeradas extra.",
        "5. Valida con los comandos de abajo y corrige hasta que pasen.",
        "6. Registra cada `[NO DETERMINADO]` en la sección de riesgos para que "
        "`harvest_open_questions.py` lo volque en `22-preguntas-abiertas.md`.",
        "",
        *valida,
        "",
        "Devuelve **solo** el JSON `AutorOutput` del contrato, con "
        "`metricas.validaciones` incluyendo los resultados.",
    ]

    BRIEFS.mkdir(parents=True, exist_ok=True)
    path = BRIEFS / f"{uid}.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"OK {path}  ({u['archivos_total']} archivos, plantilla={tpl})")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--unit", default="")
    ap.add_argument("--feature", default="")
    ap.add_argument("--foco", default="", help="foco extra a_append")
    ap.add_argument("--pruebas", default="", help="pruebas literales extra")
    ap.add_argument("--extra", type=Path,
                    help="fichero Markdown con secciones extra (## Foco de esta "
                         "unidad / ## Pruebas literales adicionales) para evitar "
                         "problemas de escapado en la linea de comandos")
    args = ap.parse_args()

    ids = []
    if args.unit:
        ids = [args.unit]
    elif args.feature:
        for p in sorted(UNITS.glob("*.json")):
            u = json.loads(p.read_text(encoding="utf-8"))
            if u.get("feature_id") == args.feature:
                ids.append(u["id"])
    else:
        ap.error("usa --unit o --feature")

    BRIEFS.mkdir(parents=True, exist_ok=True)
    for uid in ids:
        u = json.loads((UNITS / f"{uid}.json").read_text(encoding="utf-8"))
        feature = u["feature_id"]
        if es_transversal(u):
            if _brief_transversal(u, uid) != 0:
                return 2
            continue
        lines = [
            f"# Brief de unidad {uid} — {u['titulo']}",
            "",
            f"- **Unidad**: `{uid}` (`OUT/_ledger/units/{uid}.json`)",
            f"- **Feature**: `{feature}` — {FOCO.get(feature, '(sin foco declarado)')}",
            f"- **Documento a escribir**: `{u['documento']}`",
            f"- **Archivos**: {u['archivos_total']}",
            f"- **Fuentes**: {', '.join(u.get('fuentes', []))}",
            f"- **Catálogos disponibles**: {', '.join(u.get('catalogos', []))}",
            f"- **Dependencias**: "
            f"{', '.join(d.get('id', '') for d in u.get('dependencias', [])) or '(ninguna)'}",
        ]
        if uid in GATE_100:
            lines.append("- **Revisión gate-100**: el revisor verificará el 100 % "
                         "de las afirmaciones, no una muestra.")
        if feature in SCOPE:
            lines += ["", "## Corrección de scope que debes declarar (en §2 y §13)", "", SCOPE[feature]]
        if args.foco:
            lines += ["", "## Foco de esta unidad", "", args.foco]
        if args.extra:
            lines += ["", args.extra.read_text(encoding="utf-8").rstrip()]
        if args.pruebas:
            lines += ["", "## Pruebas literales adicionales", "", args.pruebas]
        lines += ["", "## Archivos de la unidad", ""]
        for a in u["archivos"]:
            lines.append(f"- `{a['ruta']}` ({a['capa']})")
        lines += [
            "",
            "## Cómo trabajar",
            "",
            "1. Lee `AGENTS.md` (§6 reglas de evidencia) y "
            "`SKILL/references/subagent-autor-prompt.md` (tu contrato).",
            "2. Lee `SKILL/references/feature-template.md` (19 secciones) y "
            "`SKILL/references/evidence-rules.md` + `diagram-conventions.md`.",
            "3. Lee **todos** los archivos de la unidad desde "
            f"`SRC/<fuente>/<ruta>`. Los files están en `SRC/{'/'.join(sorted(set(a['fuente'] for a in u['archivos']))) or 'appflowy'}/...`.",
            "4. Filtra los catálogos de `OUT/_ledger/extract/` a tus archivos.",
            "5. Escribe el documento en la ruta indicada, con las 19 secciones.",
            "6. Valida con los tres comandos y corrige hasta que pasen.",
            "",
            "```sh",
            f'python3 SKILL/scripts/validate_template.py -t feature "{u["documento"]}" --quiet',
            f'python3 SKILL/scripts/validate_evidence.py --inventario OUT/_ledger/inventario.json "{u["documento"]}"',
            f'bash SKILL/scripts/validate_mermaid.sh "{u["documento"]}"',
            "```",
            "",
            "Devuelve **solo** el JSON `AutorOutput` del contrato, con "
            "`metricas.validaciones` incluyendo los tres resultados.",
        ]
        path = BRIEFS / f"{uid}.md"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"OK {path}  ({u['archivos_total']} archivos)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())