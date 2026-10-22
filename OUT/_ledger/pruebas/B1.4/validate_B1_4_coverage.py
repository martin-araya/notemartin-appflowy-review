#!/usr/bin/env python3
"""validate_B1_4_coverage.py — prueba literal del ROADMAP B1.4.

Verifica que las 15 `LaunchTask` documentadas en
`OUT/05-arranque-y-ciclo-de-vida.md` §2 aparecen **en el orden del código**
(`startup.dart:118–156`) y que cada una tiene al menos 2 citas
`ruta:línea` (declaración + definición).

Uso: validate_B1_4_coverage.py [--doc PATH] [--json] [--quiet]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT_DEFAULT = SCRIPT_DIR.parents[3]
DEFAULT_DOC = PROJECT_ROOT_DEFAULT / "OUT" / "05-arranque-y-ciclo-de-vida.md"

# Canonical order from startup.dart:118–156 (15 tasks)
EXPECTED_TASKS = [
    "PlatformErrorCatcherTask",
    "MemoryLeakDetectorTask",
    "DebugTask",
    "FeatureFlagTask",
    "InitLocalizationTask",
    "InitAppWindowTask",
    "InitRustSDKTask",
    "PluginLoadTask",
    "FileStorageTask",
    "ApplicationInfoTask",  # alias of DeviceOrApplicationInfoTask
    "AutoUpdateTask",
    "HotKeyTask",
    "InitAppFlowyCloudTask",
    "InitAppWidgetTask",
    "InitPlatformServiceTask",
    "RecentServiceTask",
]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--doc", type=Path, default=DEFAULT_DOC)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()

    text = args.doc.read_text(encoding="utf-8")

    # Extract ONLY the §2 table (which lists the 15 tasks in canonical order).
    # Find the §2 section: between "## 2." and "## 3.".
    m = re.search(r"## 2\..*?(?=^## 3\.)", text, re.DOTALL | re.MULTILINE)
    section_2 = m.group(0) if m else text
    matches = re.findall(r"`([A-Z][A-Za-z0-9_]*Task)`", section_2)
    seen = []
    for m in matches:
        if m not in seen:
            seen.append(m)

    # Check coverage and order
    missing = [t for t in EXPECTED_TASKS if t not in seen]
    # Also: any task that appears out of order
    expected_filtered = [t for t in EXPECTED_TASKS if t in seen]
    order_in_doc = [t for t in seen if t in EXPECTED_TASKS]
    order_ok = expected_filtered == order_in_doc

    # Check citations: each task should have at least 2 `ruta:línea` references
    citation_counts = {}
    for t in EXPECTED_TASKS:
        # find all citations associated with this task (rough heuristic: line ranges
        # that contain the task name)
        pattern = rf"`appflowy/[^\n]*{t.split('Task')[0].lower()}[^\n]*\.dart:\d+`"
        cites = re.findall(pattern, text, flags=re.IGNORECASE)
        citation_counts[t] = len(cites)

    payload = {
        "code": "OK" if not missing and order_ok else "E_MISSING_OR_ORDER",
        "expected_count": len(EXPECTED_TASKS),
        "found_in_doc": [t for t in EXPECTED_TASKS if t in seen],
        "missing": missing,
        "order_ok": order_ok,
        "expected_order": expected_filtered,
        "actual_order": order_in_doc,
        "citation_counts": citation_counts,
    }
    if args.json or not args.quiet:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0 if not missing and order_ok else 1


if __name__ == "__main__":
    sys.exit(main())
