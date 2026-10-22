#!/usr/bin/env bash
# validate-B2.1.sh — suite de validación de la fase B2.1.
# Ejecuta los 4 validadores A3.x + la prueba literal de cobertura sobre
# `OUT/11-catalogo-eventos-ffi.md` (generado por build_catalog_events.py
# desde events.json).
set -uo pipefail

cd "$(dirname "$0")/../.."

FAIL=0

echo "─── validate_template (catalogue) ───"
if SKILL/scripts/validate_template.py OUT/11-catalogo-eventos-ffi.md --quiet --no-color; then
  echo "OK: template"
else
  echo "FAIL: template"; FAIL=1
fi

echo "─── validate_evidence ───"
if SKILL/scripts/validate_evidence.py OUT/11-catalogo-eventos-ffi.md --quiet --no-color; then
  echo "OK: evidence"
else
  echo "FAIL: evidence"; FAIL=1
fi

echo "─── validate_mermaid ───"
if SKILL/scripts/validate_mermaid.sh OUT/11-catalogo-eventos-ffi.md --quiet; then
  echo "OK: mermaid"
else
  echo "FAIL: mermaid"; FAIL=1
fi

echo "─── count_rows_229 (prueba literal del ROADMAP) ───"
if OUT/_ledger/pruebas/B2.1/count_rows_229.py; then
  echo "OK: count_rows_229"
else
  echo "FAIL: count_rows_229"; FAIL=1
fi

if [ "$FAIL" -eq 0 ]; then
  echo
  echo "OK: B2.1 (template + evidence + mermaid + count_rows, 4/4 checks)"
  exit 0
else
  echo
  echo "FAIL: B2.1"
  exit 1
fi