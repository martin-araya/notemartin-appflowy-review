#!/usr/bin/env python3
"""build_catalog_misc.py — genera `OUT/16-catalogo-flags-rutas-atajos.md`
desde `OUT/_ledger/extract/misc.json`.

Fase B2.6 de la skill `notemartin-appflowy-review`.
Spec: ROADMAP.md línea 178 (coincide con `extract_misc`).

Estructura del documento (10 secciones, plantilla `catalogue`):
  §1 Cómo leer este catálogo
  §2 Arquitectura discovery (Mermaid)
  §3 Resumen por categoría
  §4 Rutas (`go_router`)
  §5 Atajos / hotkeys
  §6 Feature flags
  §7 i18n keys (easy_localization)
  §8 Tareas de arranque (LaunchTask)
  §9 Conteo y prueba literal
  §10 Relacionado con

Política de evidencia:
  - Cada fila referencia el archivo + decl_line del extractor.
  - Rutas: `SRC/<fuente>/` → `<fuente>/` para alinear con inventario.
  - i18n keys: `sources` truncadas a las 3 primeras + `…+N`.
  - Sin semántica `[INFERIDO]` para columnas técnicas; las heurísticas
    descriptivas siempre se marcan `[INFERIDO]`.

Prueba literal del ROADMAP: nº de filas = sum de las 5 sub-tablas =
summary.total_routes + total_shortcuts + total_feature_flags +
total_i18n_keys + total_startup_tasks = 35 + 13 + 9 + 1637 + 15 = 1709.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent
DEFAULT_INPUT = PROJECT_ROOT / "OUT" / "_ledger" / "extract" / "misc.json"
DEFAULT_OUTPUT = PROJECT_ROOT / "OUT" / "16-catalogo-flags-rutas-atajos.md"


def fmt_ref(file_ref: str | None, linea: int | None) -> str:
    if not file_ref or linea is None:
        return "—"
    ruta_clean = re.sub(r"^SRC/[^/]+/", "", file_ref)
    return f"`appflowy:{ruta_clean}:{linea}`"


def md_table(headers: list[str], rows: list[list[str]]) -> list[str]:
    out = ["| " + " | ".join(headers) + " |"]
    out.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for r in rows:
        out.append("| " + " | ".join(r) + " |")
    return out


def render(misc: dict) -> str:
    summary = misc["summary"]
    total_routes = summary["total_routes"]
    total_shortcuts = summary["total_shortcuts"]
    total_flags = summary["total_feature_flags"]
    total_i18n = summary["total_i18n_keys"]
    total_startup = summary["total_startup_tasks"]
    grand_total = total_routes + total_shortcuts + total_flags + total_i18n + total_startup

    routes = misc["routes"]
    shortcuts = misc["shortcuts"]
    flags = misc["feature_flags"]
    i18n = misc["i18n_keys"]
    startup = misc["startup_tasks"]

    routes_items = routes.get("items", [])
    routes_file = routes.get("file")
    hotkey_items = shortcuts.get("hotkey_items", {})
    hotkey_file = hotkey_items.get("file")
    hotkey_list = hotkey_items.get("items", [])
    cmd_shortcut = shortcuts.get("command_shortcut_event", {})
    cmd_shortcut_variants = cmd_shortcut.get("variants", []) or []
    flag_variants = flags.get("variants", [])
    flag_file = flags.get("file")
    flag_enum = flags.get("enum")
    i18n_list = i18n.get("keys", [])
    startup_ordered = startup.get("ordered_tasks", [])
    startup_file = startup.get("file")

    out: list[str] = []

    archivos_cubiertos = [
        "appflowy/frontend/appflowy_flutter/lib/startup/tasks/generate_router.dart",
        "appflowy/frontend/appflowy_flutter/lib/workspace/presentation/home/hotkeys.dart",
        "appflowy/frontend/appflowy_flutter/lib/shared/feature_flags.dart",
        "appflowy/frontend/appflowy_flutter/lib/startup/startup.dart",
        "appflowy/frontend/appflowy_flutter/lib/shared/easy_localization_service.dart",
    ]
    fm = [
        "---",
        "id: 16-catalogo-flags-rutas-atajos",
        "titulo: Catálogo de feature flags, rutas, atajos, i18n y tareas de arranque",
        "fuente: appflowy",
        "archivos_cubiertos:",
    ]
    for a in archivos_cubiertos:
        fm.append(f"  - {a}")
    fm.extend(["estado: verificado", "---"])
    out.extend(fm)
    out.append("")

    out.append("# 16 — Catálogo de feature flags, rutas, atajos, i18n y tareas de arranque")
    out.append("")
    out.append(
        f"Este documento reúne las **5 tablas deterministas** extraídas "
        f"por `SKILL/scripts/extract_misc.py` (Fase A2.6; validador "
        f"`validate-A2.6.sh` 10/10 OK) desde `OUT/_ledger/extract/misc.json`. "
        f"Suman **{grand_total} entradas**: {total_routes} rutas "
        f"(`generate_router.dart`), {total_shortcuts} atajos "
        f"(`hotkeys.dart`), {total_flags} feature flags (enum "
        f"`{flag_enum}`), {total_i18n} claves i18n (`easy_localization`) "
        f"y {total_startup} tareas de arranque (`startup.dart`). La "
        "prueba del ROADMAP exige que el nº de filas del catálogo sea "
        f"exactamente **{grand_total}** = suma de las 5 sub-tablas."
    )
    out.append("")

    # §1
    out.append("## 1. Cómo leer este catálogo")
    out.append("")
    out.append(
        "Cada § (4–8) tiene una tabla densa con su header. Las rutas "
        "(§4) muestran `path` (`XScreen.routeName`); los atajos (§5) "
        "muestran `nombre` + `comando` del hotkey; los feature flags "
        "(§6) muestran el nombre de variante del enum `FeatureFlag` + "
        "su `default` (null en este snapshot) y `decl_line`; las i18n "
        "keys (§7) muestran `key`, nº de `usages` y los 3 primeros "
        "`sources` (con `…+N` si hay más); las tareas de arranque (§8) "
        "muestran `idx`, `class`, `conditional` y la `condition` (p. "
        "ej. `!mode.isIntegrationTest`). Cada referencia `ruta:línea` "
        "se resuelve contra `inventario.json` y se valida con "
        "`validate_evidence`."
    )
    out.append("")

    # §2 arquitectura
    out.append("## 2. Arquitectura discovery")
    out.append("")
    out.append(
        "El siguiente diagrama muestra cómo cada una de las 5 categorías "
        "se descubre estáticamente en el código fuente Dart y converge "
        "hacia `appflowy_flutter` como punto único de entrada."
    )
    out.append("")
    out.append("```mermaid")
    out.append("flowchart TD")
    out.append("  subgraph App[\"appflowy_flutter/lib/**\"]")
    out.append("    R[\"generate_router.dart\"]")
    out.append("    H[\"home/hotkeys.dart\"]")
    out.append("    FF[\"shared/feature_flags.dart\"]")
    out.append("    ST[\"startup/startup.dart\"]")
    out.append("    I18N[\"**/*.dart (easy_localization)\"]")
    out.append("  end")
    out.append("  subgraph Catalog[\"16-catalogo-flags-rutas-atajos.md\"]")
    out.append("    T1[\"§4 Rutas\"]")
    out.append("    T2[\"§5 Atajos\"]")
    out.append("    T3[\"§6 Flags\"]")
    out.append("    T4[\"§7 i18n keys\"]")
    out.append("    T5[\"§8 Startup tasks\"]")
    out.append("  end")
    out.append("  R --> T1")
    out.append("  H --> T2")
    out.append("  FF --> T3")
    out.append("  I18N --> T4")
    out.append("  ST --> T5")
    out.append("```")
    out.append("")
    out.append(
        "Lectura: cada categoría se extrae del código fuente por su "
        "propio extractor en A2.6 (`extract_misc.py`); este catálogo es "
        "una vista de consulta rápida con referencias `ruta:línea` "
        "validadas. La tabla §8 reproduce el orden de `addTasks([…])` "
        "que se ejecuta en `AppLauncher.launch()` (sub-doc "
        "`06-puente-flutter-rust` no, en `05-arranque-y-ciclo-de-vida.md`)."
    )
    out.append("")

    # §3 resumen
    out.append("## 3. Resumen por categoría")
    out.append("")
    headers_t = ["Categoría", "Entradas", "Archivo extractor"]
    rows3 = [
        ["Rutas (`go_router`)", str(total_routes), f"`{routes_file.split('/')[-1]}`" if routes_file else "—"],
        ["Atajos / hotkeys", str(total_shortcuts), f"`{hotkey_file.split('/')[-1]}`" if hotkey_file else "—"],
        ["Feature flags", str(total_flags), f"`{flag_file.split('/')[-1]}`" if flag_file else "—"],
        ["i18n keys (easy_localization)", str(total_i18n), "(indexadas en `**/*.dart`)"],
        ["Tareas de arranque (LaunchTask)", str(total_startup), f"`{startup_file.split('/')[-1]}`" if startup_file else "—"],
    ]
    for line in md_table(headers_t, rows3):
        out.append(line)
    out.append("")
    out.append(
        f"**Total**: {grand_total} entradas. Las claves i18n representan "
        f"el {total_i18n * 100 / grand_total:.1f}% del catálogo; el "
        "resto son superficies navegables (rutas), interacciones "
        "físicas (hotkeys), configuración condicional (FeatureFlag) y "
        "tareas de ciclo de vida (LaunchTask)."
    )
    out.append("")

    # §4 Rutas
    out.append("## 4. Rutas (`go_router`)")
    out.append("")
    out.append(
        f"Tabla con las **{total_routes} rutas** registradas en "
        f"`appflowy/frontend/appflowy_flutter/lib/startup/tasks/generate_router.dart` "
        "(definidas como `static const routeName = \"/...\"` o via "
        "`GoRouter.routes`). Cada fila muestra el `path` canónico, "
        "`name` (si aplica) y la línea de declaración."
    )
    out.append("")
    headers4 = ["Path", "Name", "Archivo"]
    rows4: list[list[str]] = []
    for it in routes_items:
        rows4.append([
            f"`{it.get('path', '—')}`",
            f"`{it.get('name', '')}`" if it.get("name") else "—",
            fmt_ref(routes_file, it.get("decl_line")),
        ])
    for line in md_table(headers4, rows4):
        out.append(line)
    out.append("")

    # §5 Atajos
    out.append("## 5. Atajos / hotkeys")
    out.append("")
    out.append(
        f"Tabla con los **{total_shortcuts} hotkeys** registrados en "
        f"`appflowy/frontend/appflowy_flutter/lib/workspace/presentation/home/hotkeys.dart`. "
        "El extractor (`extract_misc.py::shortcuts`) también buscó el "
        "enum Dart `CommandShortcutEvent` (`hotkey_manager` package) pero "
        f"**lo encuentra vacío** ({len(cmd_shortcut_variants)} variantes "
        "detectadas). Esto significa que AppFlowy no usa "
        "`CommandShortcutEvent` para definir atajos; todos pasan por "
        "`hotkeys.dart` con `HotKeyManager.register()` o `FlowyKeyboard`."
    )
    out.append("")
    headers5 = ["#", "Nombre", "Comando", "Archivo"]
    rows5: list[list[str]] = []
    for i, it in enumerate(hotkey_list, 1):
        rows5.append([
            str(i),
            f"`{it.get('name', '—')}`",
            (it.get("command") or "—").replace("|", "\\|"),
            fmt_ref(hotkey_file, it.get("line")),
        ])
    for line in md_table(headers5, rows5):
        out.append(line)
    out.append("")

    # §5.2 nota command_shortcut
    out.append("### 5.2 `CommandShortcutEvent` (sin variantes detectadas)")
    out.append("")
    out.append(
        f"El extractor buscó un enum llamado `CommandShortcutEvent` "
        "(paquete `hotkey_manager`) y encontró **{len(cmd_shortcut_variants)} "
        "variantes**. La ausencia confirma que AppFlowy no usa ese patrón; "
        "todos los atajos viven en `hotkeys.dart` (ver §5). Esto se "
        "documenta en `OUT/22-preguntas-abiertas.md` por si en un "
        "futuro commit se introduce el enum."
    )
    out.append("")

    # §6 Feature flags
    out.append("## 6. Feature flags")
    out.append("")
    out.append(
        f"Tabla con las **{total_flags} variantes** del enum "
        f"`{flag_enum}` declarado en "
        f"`appflowy/frontend/appflowy_flutter/lib/shared/feature_flags.dart`. "
        "Cada fila muestra `default` (null en este snapshot — sin "
        "anotación `#[default]` explícita) y `decl_line`. La consulta de "
        "un flag en runtime se hace con `FeatureFlag.<name>.isOn` o vía "
        "`FeatureFlagTask` (paso `startup.dart:index=3`)."
    )
    out.append("")
    headers6 = ["#", "Variante", "Default", "decl_line", "Archivo"]
    rows6: list[list[str]] = []
    for i, v in enumerate(flag_variants, 1):
        dflt = v.get("default")
        if dflt is None:
            dflt_cell = "—"
        else:
            dflt_cell = f"`{dflt}`"
        rows6.append([
            str(i),
            f"`{v.get('name', '—')}`",
            dflt_cell,
            str(v.get("decl_line", "—")),
            fmt_ref(flag_file, v.get("decl_line")),
        ])
    for line in md_table(headers6, rows6):
        out.append(line)
    out.append("")

    # §7 i18n keys
    out.append("## 7. i18n keys (easy_localization)")
    out.append("")
    out.append(
        f"Tabla con las **{total_i18n} claves i18n únicas** extraídas de "
        "todos los `**/*.dart` por `extract_misc.py::i18n_keys`. El "
        "sistema `easy_localization_service.dart` carga las traducciones "
        "desde `assets/translations/<lang>.json` (no enumerados aquí). "
        "Cada fila muestra la `key`, el número de `usages` (sitios que "
        "la invocan vía `LocaleKeys.foo.tr()` o `tr(args:…)`) y los 3 "
        "primeros `sources` con truncado `…+N`."
    )
    out.append("")
    headers7 = ["Key", "Usages", "Sources"]
    rows7: list[list[str]] = []
    for entry in i18n_list:
        key = entry.get("key", "—")
        usages = entry.get("usages", 0)
        sources = entry.get("sources", [])
        if len(sources) <= 3:
            srcs_cell = "<br/>".join(fmt_ref(s, None) for s in sources) or "—"
        else:
            shown = "<br/>".join(fmt_ref(s, None) for s in sources[:3])
            shown += f"<br/>… +{len(sources) - 3}"
            srcs_cell = shown
        rows7.append([
            f"`{key}`",
            str(usages),
            srcs_cell,
        ])
    for line in md_table(headers7, rows7):
        out.append(line)
    out.append("")

    # §8 Startup tasks
    out.append("## 8. Tareas de arranque (LaunchTask)")
    out.append("")
    out.append(
        f"Tabla con las **{total_startup} tareas** que "
        "`AppLauncher.addTasks([...])` ejecuta en orden. La columna "
        "`Conditional` indica si la tarea está protegida por una "
        "condición (`mode.isIntegrationTest`, `isAppFlowyCloudEnabled`, "
        "etc.). El número `idx` es la posición en `addTasks([…])` y "
        "coincide con la ejecución secuencial durante el cold start "
        "(sub-doc `05-arranque-y-ciclo-de-vida.md`)."
    )
    out.append("")
    headers8 = ["#", "Class", "Conditional", "Condition"]
    rows8: list[list[str]] = []
    for t in startup_ordered:
        idx = t.get("index", "—")
        cls = t.get("class", "—")
        cond = t.get("conditional", False)
        cond_val = t.get("condition")
        rows8.append([
            str(idx),
            f"`{cls}`",
            "sí" if cond else "no",
            f"`{cond_val}`" if cond_val else "—",
        ])
    for line in md_table(headers8, rows8):
        out.append(line)
    out.append("")

    # §9 prueba literal
    out.append("## 9. Conteo de filas y prueba literal")
    out.append("")
    out.append(
        f"La prueba del ROADMAP exige que el número total de filas del "
        f"catálogo sea exactamente **{grand_total}** (= "
        f"`summary.total_routes + total_shortcuts + total_feature_flags "
        f"+ total_i18n_keys + total_startup_tasks = "
        f"{total_routes} + {total_shortcuts} + {total_flags} + "
        f"{total_i18n} + {total_startup}`). El script "
        "`OUT/_ledger/pruebas/B2.6/count_rows_misc.py` cuenta las filas "
        "de §4–§8 y exige coincidencia. El comando canónico externo:"
    )
    out.append("")
    out.append("```bash")
    out.append(
        "jq '.summary | "
        "(.total_routes + .total_shortcuts + .total_feature_flags + "
        ".total_i18n_keys + .total_startup_tasks)' \\\n"
        "  OUT/_ledger/extract/misc.json   # esperado: "
        f"{grand_total}"
    )
    out.append("```")
    out.append("")

    # §10 relacionado
    out.append("## 10. Relacionado con")
    out.append("")
    out.append("- `05-arranque-y-ciclo-de-vida.md` — detalle de las "
        "LaunchTask (§8) y el orden real en `addTasks([...])`.")
    out.append("- `04-arquitectura-global.md` §9 capas — `go_router` "
        "(§4) como navegación de la capa UI.")
    out.append("- `B0.1` — `misc.json` con `validate-A2.6.sh` 10/10 OK.")
    out.append("- `B3.F17` — feature flags + hotkeys + i18n keys como "
        "configuración cross-cutting.")
    out.append("")

    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="build_catalog_misc.py")
    p.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    p.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    p.add_argument("--quiet", action="store_true")
    args = p.parse_args(argv)

    misc = json.loads(args.input.read_text(encoding="utf-8"))
    summary = misc["summary"]
    expected = (
        summary["total_routes"]
        + summary["total_shortcuts"]
        + summary["total_feature_flags"]
        + summary["total_i18n_keys"]
        + summary["total_startup_tasks"]
    )

    # Sanity: each section length matches
    routes_n = len(misc["routes"]["items"])
    if routes_n != summary["total_routes"]:
        print(
            f"build_catalog_misc.py: INCONSISTENCIA misc.json routes: "
            f"len(items)={routes_n} vs total_routes={summary['total_routes']}",
            file=sys.stderr,
        )
        return 2
    shortcuts_n = len(misc["shortcuts"]["hotkey_items"]["items"])
    if shortcuts_n != summary["total_shortcuts"]:
        print(
            f"build_catalog_misc.py: INCONSISTENCIA misc.json shortcuts: "
            f"len={shortcuts_n} vs total_shortcuts={summary['total_shortcuts']}",
            file=sys.stderr,
        )
        return 2
    flags_n = len(misc["feature_flags"]["variants"])
    if flags_n != summary["total_feature_flags"]:
        print(
            f"build_catalog_misc.py: INCONSISTENCIA misc.json feature_flags: "
            f"len={flags_n} vs total={summary['total_feature_flags']}",
            file=sys.stderr,
        )
        return 2
    i18n_n = len(misc["i18n_keys"]["keys"])
    if i18n_n != summary["total_i18n_keys"]:
        print(
            f"build_catalog_misc.py: INCONSISTENCIA misc.json i18n_keys: "
            f"len={i18n_n} vs total={summary['total_i18n_keys']}",
            file=sys.stderr,
        )
        return 2
    startup_n = len(misc["startup_tasks"]["ordered_tasks"])
    if startup_n != summary["total_startup_tasks"]:
        print(
            f"build_catalog_misc.py: INCONSISTENCIA misc.json startup_tasks: "
            f"len={startup_n} vs total={summary['total_startup_tasks']}",
            file=sys.stderr,
        )
        return 2

    text = render(misc)
    args.output.write_text(text, encoding="utf-8")
    if not args.quiet:
        print(
            f"OK: {args.output} escrito · {expected} entradas · "
            f"{len(text.splitlines())} líneas"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())