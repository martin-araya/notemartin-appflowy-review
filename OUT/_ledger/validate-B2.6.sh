#!/usr/bin/env bash
# validate-B2.6.sh — suite de validación de la fase B2.6.
# Ejecuta los 4 validadores A3.x + la prueba literal de cobertura sobre
# `OUT/16-catalogo-flags-rutas-atajos.md` (generado por
# build_catalog_misc.py desde misc.json).
set -uo pipefail

cd "$(dirname "$0")/../.."

FAIL=0

echo "─── validate_template (catalogue) ───"
if SKILL/scripts/validate_template.py OUT/16-catalogo-flags-rutas-atajos.md --quiet --no-color; then
  echo "OK: template"
else
  echo "FAIL: template"; FAIL=1
fi

echo "─── validate_evidence ───"
if SKILL/scripts/validate_evidence.py OUT/16-catalogo-flags-rutas-atajos.md --quiet --no-color; then
  echo "OK: evidence"
else
  echo "FAIL: evidence"; FAIL=1
fi

echo "─── validate_mermaid ───"
if SKILL/scripts/validate_mermaid.sh OUT/16-catalogo-flags-rutas-atajos.md --quiet; then
  echo "OK: mermaid"
else
  echo "FAIL: mermaid"; FAIL=1
fi

echo "─── count_rows_misc (prueba literal del ROADMAP) ───"
if OUT/_ledger/pruebas/B2.6/count_rows_misc.py; then
  echo "OK: count_rows_misc"
else
  echo "FAIL: count_rows_misc"; FAIL=1
fi

if [ "$FAIL" -eq 0 ]; then
  echo
  echo "OK: B2.6 (template + evidence + mermaid + count_rows, 4/4 checks)"
  exit 0
else
  echo
  echo "FAIL: B2.6"
  exit 1
fi