#!/usr/bin/env python3
"""make_b6_units.py — crea las 6 unidades del Bloque B6 (transversales de
cierre: build/CI, testing, seguridad, resumen ejecutivo, glosario y
preguntas abiertas).

Las unidades B6 usan el mismo esquema transversal que las de B5:
`archivos` es la lista de ficheros que el documento RE-PRESENTA (no una
partición del ledger) y no tocan `cobertura.csv`, porque esos ficheros ya
pertenecen a features F* y están verificados al 100 % desde el cierre de B3.

Las 6 unidades:
  - B6.1    build, CI y distribución (codegen, Makefile.toml, cargokit,
            codemagic, GitHub Actions, scripts de plataforma, perfiles Cargo)
  - B6.2    testing (unit/bloc/widget Dart, runners de integración 1-9,
            event-integration-test Rust, cobertura y huecos por feature)
  - B6.3    seguridad y privacidad (auth, tokens, almacenamiento local, datos
            que salen del cliente por feature, IA local vs cloud)
  - B6.4    resumen ejecutivo (no lee SRC: re-presenta OUT/)
  - B6.5    glosario (no lee SRC: consolida terminología de OUT/)
  - B6.5.2  preguntas abiertas (no lee SRC: consolidar 22-preguntas-abiertas.md)

Uso:
  python3 make_b6_units.py              # crea/actualiza las 6
  python3 make_b6_units.py --list       # solo lista el plan
  python3 make_b6_units.py --only B6.3  # solo una unidad
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
UNITS = PROJECT_ROOT / "OUT" / "_ledger" / "units"

APP = "appflowy/"
FR = "appflowy/frontend/"
FL = "appflowy/frontend/appflowy_flutter/"
RL = "appflowy/frontend/rust-lib/"

# --- B6.1 · Build, CI y distribución ---------------------------------------

CI_WORKFLOWS = [
    f"{APP}.github/workflows/build_command.yml",
    f"{APP}.github/workflows/flutter_ci.yaml",
    f"{APP}.github/workflows/rust_ci.yaml",
    f"{APP}.github/workflows/rust_coverage.yml",
    f"{APP}.github/workflows/mobile_ci.yml",
    f"{APP}.github/workflows/ios_ci.yaml",
    f"{APP}.github/workflows/android_ci.yaml.bak",
    f"{APP}.github/workflows/docker_ci.yml",
    f"{APP}.github/workflows/release.yml",
    f"{APP}.github/workflows/commit_lint.yml",
    f"{APP}.github/workflows/ninja_i18n.yml",
    f"{APP}.github/workflows/translation_notify.yml",
]

MAKEFRAGMENT = [
    f"{FR}scripts/makefile/flutter.toml",
    f"{FR}scripts/makefile/desktop.toml",
    f"{FR}scripts/makefile/mobile.toml",
    f"{FR}scripts/makefile/tests.toml",
    f"{FR}scripts/makefile/protobuf.toml",
    f"{FR}scripts/makefile/tool.toml",
    f"{FR}scripts/makefile/env.toml",
    f"{FR}scripts/makefile/docker.toml",
    f"{FR}scripts/makefile/tauri.toml",
    f"{FR}scripts/makefile/web.toml",
]

CODEGEN_SCRIPTS = [
    f"{FR}scripts/code_generation/language_files/generate_language_files.sh",
    f"{FR}scripts/code_generation/flowy_icons/generate_flowy_icons.sh",
    f"{FR}scripts/code_generation/flowy_icons/generate_flowy_icons.cmd",
    f"{FR}scripts/code_generation/freezed/generate_freezed.sh",
    f"{FR}scripts/code_generation/freezed/generate_freezed.cmd",
]

PLATFORM_SCRIPTS = [
    f"{FR}scripts/flutter_release_build/build_universal_package_for_macos.sh",
    f"{FR}scripts/flutter_release_build/build_flowy.dart",
    f"{FR}scripts/flutter_release_build/tool.dart",
    f"{FR}scripts/windows_installer/inno_setup_config.iss",
    f"{FR}scripts/linux_distribution/deb/build_deb.sh",
    f"{FR}scripts/linux_distribution/deb/DEBIAN/control",
    f"{FR}scripts/linux_distribution/deb/DEBIAN/postinst",
    f"{FR}scripts/linux_distribution/deb/DEBIAN/postrm",
    f"{FR}scripts/linux_distribution/deb/AppFlowy.desktop",
    f"{FR}scripts/linux_distribution/appimage/build_appimage.sh",
    f"{FR}scripts/linux_distribution/appimage/AppImageBuilder.yml",
    f"{FR}scripts/linux_distribution/appimage/io.appflowy.AppFlowy.desktop",
    f"{FR}scripts/linux_distribution/packaging/launcher.sh",
    f"{FR}scripts/linux_distribution/packaging/io.appflowy.AppFlowy.service",
    f"{FR}scripts/linux_distribution/packaging/io.appflowy.AppFlowy.metainfo.xml",
    f"{FR}scripts/linux_distribution/packaging/io.appflowy.AppFlowy.launcher.desktop",
    f"{FR}scripts/flatpack-buildfiles/io.appflowy.AppFlowy.yml",
    f"{FR}scripts/flatpack-buildfiles/dbus-interface.xml",
    f"{FR}scripts/linux_installer/control",
    f"{FR}scripts/linux_installer/postinst",
    f"{FR}scripts/linux_installer/postrm",
]

TOOL_SCRIPTS = [
    f"{FR}scripts/tool/update_collab_source.sh",
    f"{FR}scripts/tool/update_collab_rev.sh",
    f"{FR}scripts/tool/update_local_ai_rev.sh",
    f"{FR}scripts/tool/update_client_api_rev.sh",
]

DEVENV_SCRIPTS = [
    f"{FR}scripts/install_dev_env/install_linux.sh",
    f"{FR}scripts/install_dev_env/install_macos.sh",
    f"{FR}scripts/install_dev_env/install_windows.sh",
    f"{FR}scripts/install_dev_env/install_ios.sh",
]

WHITE_LABEL = [
    f"{FR}scripts/white_label/white_label.sh",
    f"{FR}scripts/white_label/code_white_label.sh",
    f"{FR}scripts/white_label/icon_white_label.sh",
    f"{FR}scripts/white_label/font_white_label.sh",
    f"{FR}scripts/white_label/i18n_white_label.sh",
    f"{FR}scripts/white_label/windows_white_label.sh",
]

B6_1 = (
    CI_WORKFLOWS
    + MAKEFRAGMENT
    + CODEGEN_SCRIPTS
    + PLATFORM_SCRIPTS
    + TOOL_SCRIPTS
    + DEVENV_SCRIPTS
    + WHITE_LABEL
    + [
        f"{APP}codemagic.yaml",
        f"{APP}commitlint.config.js",
        f"{APP}install.sh",
        f"{APP}project.inlang.json",
        f"{FR}Makefile.toml",
        f"{FR}rust-toolchain.toml",
        f"{FL}Makefile",
        f"{FL}build.yaml",
        f"{FL}cargokit_options.yaml",
        f"{FL}distribute_options.yaml",
        f"{FL}pubspec.yaml",
        f"{FL}analysis_options.yaml",
        f"{FL}dart_dependency_validator.yaml",
        f"{RL}Cargo.toml",
        f"{RL}dart-ffi/Cargo.toml",
        f"{RL}flowy-core/Cargo.toml",
        f"{RL}lib-dispatch/Cargo.toml",
        f"{RL}build-tool/flowy-codegen/Cargo.toml",
        f"{RL}event-integration-test/Cargo.toml",
    ]
)

# --- B6.2 · Testing ---------------------------------------------------------

DART_TESTS = [
    f"{FL}test/util.dart",
    f"{FL}test/bloc_test/view_selector_test.dart",
    f"{FL}test/widget_test/test_material_app.dart",
    f"{FL}test/widget_test/test_asset_bundle.dart",
    f"{FL}test/widget_test/widget_test_wrapper.dart",
    f"{FL}test/widget_test/confirm_dialog_test.dart",
    f"{FL}test/widget_test/date_picker_test.dart",
    f"{FL}test/widget_test/direction_setting_test.dart",
    f"{FL}test/widget_test/select_option_text_field_test.dart",
    f"{FL}test/widget_test/spae_cion_test.dart",
    f"{FL}test/widget_test/theme_font_family_setting_test.dart",
]

INTEGRATION_RUNNERS = [
    f"{FL}integration_test/runner.dart",
    f"{FL}integration_test/mobile_runner_1.dart",
] + [f"{FL}integration_test/desktop_runner_{n}.dart" for n in range(1, 10)]

RUST_EVENT_TESTS = [
    f"{RL}event-integration-test/Cargo.toml",
    f"{RL}event-integration-test/src/lib.rs",
    f"{RL}event-integration-test/src/event_builder.rs",
    f"{RL}event-integration-test/src/chat_event.rs",
    f"{RL}event-integration-test/src/database_event.rs",
    f"{RL}event-integration-test/src/document_event.rs",
    f"{RL}event-integration-test/src/folder_event.rs",
    f"{RL}event-integration-test/src/user_event.rs",
    f"{RL}event-integration-test/tests/main.rs",
    f"{RL}event-integration-test/tests/util.rs",
]

B6_2 = DART_TESTS + INTEGRATION_RUNNERS + RUST_EVENT_TESTS + [
    f"{FR}scripts/makefile/tests.toml",
    f"{FR}Makefile.toml",
    f"{APP}.github/workflows/flutter_ci.yaml",
    f"{APP}.github/workflows/rust_ci.yaml",
    f"{APP}.github/workflows/rust_coverage.yml",
    f"{FL}analysis_options.yaml",
    f"{RL}Cargo.toml",
    f"{RL}flowy-core/Cargo.toml",
    f"{RL}dart-ffi/Cargo.toml",
]

# --- B6.3 · Seguridad y privacidad -----------------------------------------

AUTH_DART = [
    f"{FL}lib/user/application/auth/auth_service.dart",
    f"{FL}lib/user/application/auth/af_cloud_auth_service.dart",
    f"{FL}lib/user/application/auth/af_cloud_mock_auth_service.dart",
    f"{FL}lib/user/application/auth/backend_auth_service.dart",
    f"{FL}lib/user/application/auth/device_id.dart",
    f"{FL}lib/user/application/auth/auth_error.dart",
    f"{FL}lib/user/application/sign_in_bloc.dart",
    f"{FL}lib/user/application/sign_up_bloc.dart",
    f"{FL}lib/user/application/anon_user_bloc.dart",
    f"{FL}lib/user/application/password/password_bloc.dart",
    f"{FL}lib/user/application/password/password_http_service.dart",
    f"{FL}lib/user/application/user_service.dart",
]

SEC_RUST = [
    f"{RL}dart-ffi/src/lib.rs",
    f"{RL}dart-ffi/src/c.rs",
    f"{RL}flowy-user/src/lib.rs",
    f"{RL}flowy-core/src/config.rs",
    f"{RL}flowy-core/src/app_life_cycle.rs",
    f"{RL}flowy-sqlite/src/lib.rs",
    f"{RL}flowy-sqlite/src/schema.rs",
    f"{RL}flowy-sqlite-vec/Cargo.toml",
    f"{RL}flowy-storage/src/file_cache.rs",
    f"{RL}flowy-search/src/services/manager.rs",
    f"{RL}flowy-search/src/document/cloud_search_handler.rs",
    f"{RL}flowy-search/src/document/local_search_handler.rs",
    f"{RL}flowy-ai/src/model_select.rs",
    f"{RL}flowy-ai/src/ai_manager.rs",
    f"{RL}lib-dispatch/src/runtime.rs",
]

B6_3 = AUTH_DART + SEC_RUST + [
    f"{FL}lib/startup/tasks/appflowy_cloud_task.dart",
    f"{FL}lib/core/network_monitor.dart",
    f"{FL}lib/shared/feature_flags.dart",
    f"{FL}lib/shared/permission/permission_checker.dart",
    f"{FL}pubspec.yaml",
    f"{RL}flowy-server/src/af_cloud/mod.rs",
    f"{RL}flowy-server/src/af_cloud/server.rs",
    f"{RL}flowy-server/src/af_cloud/define.rs",
    f"{RL}flowy-server/src/local_server/mod.rs",
    f"{RL}flowy-server/src/local_server/server.rs",
    f"{RL}event-integration-test/src/user_event.rs",
]

# --- B6.4 / B6.5 / B6.5.2 · Documentos que re-presentan OUT/ ----------------
#
# Los documentos de síntesis (B6.4, B6.5, B6.5.2) resumen OUT/ en lugar de
# leer SRC/, pero `validate_evidence.py` sólo resuelve referencias contra
# `inventario.json` (rutas de SRC). Por eso `archivos` sigue siendo la lista
# de anclajes SRC verificables que el autor debe citar, y el conjunto de
# documentos de OUT/ que resume va en `documentos_representados`, que no se
# valida como evidencia.

B6_4_ANCHORS = [
    f"{FL}lib/main.dart",
    f"{FL}lib/startup/startup.dart",
    f"{FL}lib/startup/deps_resolver.dart",
    f"{RL}flowy-core/src/lib.rs",
    f"{RL}dart-ffi/src/lib.rs",
    f"{RL}lib-dispatch/src/dispatcher.rs",
    f"{RL}flowy-sqlite/src/lib.rs",
    f"{RL}flowy-search/src/services/manager.rs",
    f"{RL}flowy-ai/src/ai_manager.rs",
    f"{RL}flowy-document/src/manager.rs",
    f"{RL}flowy-folder/src/manager.rs",
    f"{RL}flowy-database2/src/manager.rs",
    "collab/collab/src/lib.rs",
    "collab/collab-document/src/document.rs",
    "editor/lib/src/editor_state.dart",
]

B6_4_REPRESENTADOS = [
    "OUT/00-INDEX.md",
    "OUT/02-stack-y-dependencias.md",
    "OUT/03-estructura-del-repo.md",
    "OUT/04-arquitectura-global.md",
    "OUT/05-arranque-y-ciclo-de-vida.md",
    "OUT/06-puente-flutter-rust/",
    "OUT/07-motor-colaborativo-crdt/",
    "OUT/08-persistencia/",
    "OUT/09-features/",
    "OUT/10-motor-export-import/",
    "OUT/11-catalogo-eventos-ffi.md",
    "OUT/12-catalogo-entidades-protobuf.md",
    "OUT/13-catalogo-blocs.md",
    "OUT/14-catalogo-notificaciones.md",
    "OUT/15-catalogo-errores.md",
    "OUT/16-catalogo-flags-rutas-atajos.md",
    "OUT/17-grafo-dependencias.md",
    "OUT/18-build-ci-distribucion.md",
    "OUT/19-testing.md",
    "OUT/20-seguridad-y-privacidad.md",
    "OUT/STATE.md",
]

B6_5_ANCHORS = [
    f"{RL}flowy-document/src/event_map.rs",
    f"{RL}flowy-folder/src/event_map.rs",
    f"{RL}flowy-database2/src/event_map.rs",
    f"{RL}flowy-user/src/event_map.rs",
    f"{RL}flowy-search/src/event_handler.rs",
    f"{RL}dart-ffi/src/lib.rs",
    f"{RL}lib-dispatch/src/module/module.rs",
    f"{RL}flowy-notification/src/lib.rs",
    f"{RL}flowy-notification/src/debounce.rs",
    f"{RL}flowy-error/src/code.rs",
    f"{FL}packages/appflowy_backend/lib/rust_stream.dart",
    f"{FL}lib/plugins/shared/share/share_bloc.dart",
    "collab/collab/src/lib.rs",
    "collab/collab-plugins/src/lib.rs",
]

B6_5_REPRESENTADOS = [
    "OUT/05-arranque-y-ciclo-de-vida.md",
    "OUT/06-puente-flutter-rust/",
    "OUT/07-motor-colaborativo-crdt/",
    "OUT/08-persistencia/",
    "OUT/11-catalogo-eventos-ffi.md",
    "OUT/12-catalogo-entidades-protobuf.md",
    "OUT/13-catalogo-blocs.md",
    "OUT/14-catalogo-notificaciones.md",
    "OUT/15-catalogo-errores.md",
    "OUT/16-catalogo-flags-rutas-atajos.md",
    "AGENTS.md",
]

B6_52_ANCHORS = [
    f"{RL}flowy-user/src/event_map.rs",
    f"{RL}flowy-database2/src/event_map.rs",
]

B6_52_REPRESENTADOS = [
    "OUT/09-features/",
    "OUT/10-motor-export-import/",
    "OUT/15-secuencias-globales/",
    "OUT/18-build-ci-distribucion.md",
    "OUT/19-testing.md",
    "OUT/20-seguridad-y-privacidad.md",
]

UNITS_PLAN = [
    {
        "id": "B6.1",
        "titulo": "Build, CI y distribución",
        "documento": "OUT/18-build-ci-distribucion.md",
        "plantilla": "transversal",
        "archivos": B6_1,
        "fuentes": ["appflowy"],
        "evidence_min_pct": 95,
        "gate_100": True,
        "transversal": True,
        "nota": "Transversal. `archivos` es la lista de configs, scripts de build y perfiles Cargo que el documento RE-PRESENTA; no particiona cobertura.csv. Evidencia 100 % verbatim en comandos, flags y nombres de target: son cadenas ejecutables.",
    },
    {
        "id": "B6.2",
        "titulo": "Testing: unit, bloc, widget, integración y event-integration-test",
        "documento": "OUT/19-testing.md",
        "plantilla": "transversal",
        "archivos": B6_2,
        "fuentes": ["appflowy"],
        "evidence_min_pct": 90,
        "gate_100": False,
        "transversal": True,
        "nota": "Transversal. La lista es el esqueleto de runners y suites; el autor debe enumerar el contenido real de cada directorio (los ficheros de test no se inventan, se listan con `find`).",
    },
    {
        "id": "B6.3",
        "titulo": "Seguridad y privacidad",
        "documento": "OUT/20-seguridad-y-privacidad.md",
        "plantilla": "transversal",
        "archivos": B6_3,
        "fuentes": ["appflowy"],
        "evidence_min_pct": 95,
        "gate_100": True,
        "transversal": True,
        "nota": "Transversal. Evidencia 100 % verbatim en tokens, headers, rutas de almacenamiento y endpoints. Cualquier credencial literal encontrada se sustituye por `<REDACTED>` y se registra como pregunta abierta `SEC-n`.",
    },
    {
        "id": "B6.4",
        "titulo": "Resumen ejecutivo",
        "documento": "OUT/01-resumen-ejecutivo.md",
        "plantilla": "resumen",
        "archivos": B6_4_ANCHORS,
        "documentos_representados": B6_4_REPRESENTADOS,
        "fuentes": ["appflowy", "collab", "editor"],
        "evidence_min_pct": 70,
        "gate_100": False,
        "transversal": True,
        "sintesis": True,
        "nota": "Documento de síntesis: lee OUT/ para el relato y SRC/ sólo para anclar cada afirmación. `archivos` son los anclajes verificables contra inventario.json; `documentos_representados` es el conjunto de OUT/ que resume y NO se valida como evidencia. Toda cifra viene de OUT/STATE.md o OUT/00-INDEX.md.",
    },
    {
        "id": "B6.5",
        "titulo": "Glosario consolidado",
        "documento": "OUT/21-glosario.md",
        "plantilla": "glosario",
        "archivos": B6_5_ANCHORS,
        "documentos_representados": B6_5_REPRESENTADOS,
        "fuentes": ["appflowy", "collab"],
        "evidence_min_pct": 90,
        "gate_100": False,
        "transversal": True,
        "sintesis": True,
        "nota": "Documento de síntesis. Cada entrada es término → definición + al menos una evidencia `ruta:línea` de SRC/ + un enlace `[[X]]` al doc de OUT/ que más lo desarrolla.",
    },
    {
        "id": "B6.5.2",
        "titulo": "Preguntas abiertas: consolidación final",
        "documento": "OUT/22-preguntas-abiertas.md",
        "plantilla": "ninguna",
        "archivos": B6_52_ANCHORS,
        "documentos_representados": B6_52_REPRESENTADOS,
        "fuentes": ["appflowy"],
        "evidence_min_pct": 60,
        "gate_100": False,
        "transversal": True,
        "sintesis": True,
        "consolidacion": True,
        "nota": "Documento de consolidación. Se ejecuta `harvest_open_questions.py` dos veces y se cambia `estado: en-construccion` → `verificado`. No se aplica validate_template (su id `22-preguntas-abiertas` no matchea ninguna plantilla y sus secciones son `## Ax.y`, no `## N.`).",
    },
]


def build(unit: dict) -> dict:
    archivos = [a for a in unit["archivos"]]
    out = dict(unit)
    out["archivos"] = archivos
    out["archivos_total"] = len(archivos)
    out["feature_id"] = unit["id"]
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--list", action="store_true", help="solo lista el plan")
    ap.add_argument("--only", help="crea/actualiza solo esa unidad (p.ej. B6.3)")
    args = ap.parse_args()

    selected = [u for u in UNITS_PLAN if args.only is None or u["id"] == args.only]
    if args.only and not selected:
        print(f"ERROR: unidad desconocida: {args.only}")
        return 2

    print(f"Plan B6: {len(UNITS_PLAN)} unidades")
    for u in UNITS_PLAN:
        print(f"  {u['id']:<8} {u['titulo']:<52} -> {u['documento']}  ({len(u['archivos'])} archivos)")

    if args.list:
        return 0

    UNITS.mkdir(parents=True, exist_ok=True)
    for u in selected:
        data = build(u)
        path = UNITS / f"{u['id']}.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"OK  {path.relative_to(PROJECT_ROOT)}  ({data['archivos_total']} archivos)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())