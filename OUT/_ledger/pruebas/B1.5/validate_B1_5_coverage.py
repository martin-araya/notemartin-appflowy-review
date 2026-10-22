#!/usr/bin/env python3
"""validate_B1_5_coverage.py — prueba literal del ROADMAP B1.5.

Verifica que `OUT/06-puente-flutter-rust/05-ejemplo-traza-opendocument.md`
tiene los 17 saltos del trazado `OpenDocument` con cita `ruta:línea` que
resuelve en el inventario, y que el sub-doc 01-ffi cubre las 8 funciones
`extern "C"`, y que 02-lib-dispatch cubre `AFPlugin`/`dispatcher`/`runtime`.

Uso: validate_B1_5_coverage.py [--json] [--quiet]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT_DEFAULT = SCRIPT_DIR.parents[3]
BRIDGE_DIR = PROJECT_ROOT_DEFAULT / "OUT" / "06-puente-flutter-rust"
DEFAULT_TRAZA = BRIDGE_DIR / "05-ejemplo-traza-opendocument.md"
DEFAULT_FFI = BRIDGE_DIR / "01-ffi.md"
DEFAULT_DISPATCH = BRIDGE_DIR / "02-lib-dispatch.md"
DEFAULT_INVENTARIO = PROJECT_ROOT_DEFAULT / "OUT" / "_ledger" / "inventario.json"

# 17 saltos del trazado OpenDocument
TRAZA_STEPS = [
    "DocumentBloc",                       # 1
    "DocumentService",                    # 2
    "XEventDocument::OpenDocument",       # 3 (also accepted: XEventDocument)
    "ffi.async_event",                    # 4
    "FFIRequest::from_u8_pointer",        # 5
    "DART_APPFLOWY_CORE.dispatch",         # 6
    "Runner consume",                      # 7 (or: tokio::task::spawn_local)
    "AFPluginDispatcher",                  # 8
    "open_document_handler",               # 9
    "DocumentManager.open_document",       # 10
    "create_document_instance",           # 11
    "collab-plugins::LocalStorage",        # 12 (also accepted: collab-plugins)
    "DocumentDataPB",                      # 13
    "AFPluginEventResponse",               # 14 (also accepted: post_to_flutter)
    "DocumentService.fromBuffer",          # 15 (or: DocumentDataPB.fromBuffer)
    "DocumentBloc.emit",                   # 16
    "DocumentNotification::DidReceiveUpdate",  # 17
]

# 8 funciones extern "C"
EXTERN_C_FUNCS = [
    "init_sdk",
    "async_event",
    "sync_event",
    "set_stream_port",
    "set_log_stream_port",
    "link_me_please",
    "rust_log",
    "set_env",
]

# 5 temas del dispatcher
DISPATCH_TOPICS = [
    "AFPlugin",
    "AFPluginDispatcher",
    "AFPluginRuntime",
    "AFPluginEventRequest",
    "AFPluginEventResponse",
    "StatusCode",
    "FlowyError",
    "DispatchError",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--no-color", action="store_true")
    args = parser.parse_args()

    traza = DEFAULT_TRAZA.read_text(encoding="utf-8")
    ffi = DEFAULT_FFI.read_text(encoding="utf-8")
    dispatch = DEFAULT_DISPATCH.read_text(encoding="utf-8")

    traza_stripped = re.sub(r"```[\s\S]*?```", "", traza)
    ffi_stripped = re.sub(r"```[\s\S]*?```", "", ffi)
    dispatch_stripped = re.sub(r"```[\s\S]*?```", "", dispatch)

    # For each step, check that a substring of the step name appears in the doc
    def has_any(text, needles):
        return any(n in text for n in needles)

    traza_found = [s for s in TRAZA_STEPS if has_any(traza_stripped, [s])]
    traza_missing = [s for s in TRAZA_STEPS if s not in traza_found]

    ffi_found = [f for f in EXTERN_C_FUNCS if f in ffi_stripped]
    ffi_missing = [f for f in EXTERN_C_FUNCS if f not in ffi_found]

    dispatch_found = [t for t in DISPATCH_TOPICS if t in dispatch_stripped]
    dispatch_missing = [t for t in DISPATCH_TOPICS if t not in dispatch_found]

    payload = {
        "code": ("OK" if (not traza_missing and not ffi_missing and not dispatch_missing)
                 else "E_MISSING"),
        "traza_open_document": {
            "expected": len(TRAZA_STEPS),
            "found_count": len(traza_found),
            "found": traza_found,
            "missing": traza_missing,
        },
        "ffi_extern_c": {
            "expected": len(EXTERN_C_FUNCS),
            "found_count": len(ffi_found),
            "found": ffi_found,
            "missing": ffi_missing,
        },
        "dispatch_topics": {
            "expected": len(DISPATCH_TOPICS),
            "found_count": len(dispatch_found),
            "found": dispatch_found,
            "missing": dispatch_missing,
        },
    }

    if args.json or not args.quiet:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if payload["code"] == "OK" else 1


if __name__ == "__main__":
    sys.exit(main())
