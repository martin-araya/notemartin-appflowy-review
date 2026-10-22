#!/usr/bin/env bash
# validate-B2.2.sh — suite de validación de la fase B2.2.
# Ejecuta los 4 validadores A3.x + la prueba literal de cobertura sobre
# `OUT/12-catalogo-entidades-protobuf.md` (generado por
# build_catalog_protobuf.py desde protobuf.json).
set -uo pipefail

cd "$(dirname "$0")/../.."

FAIL=0

echo "─── validate_template (catalogue) ───"
if SKILL/scripts/validate_template.py OUT/12-catalogo-entidades-protobuf.md --quiet --no-color; then
  echo "OK: template"
else
  echo "FAIL: template"; FAIL=1
fi

echo "─── validate_evidence ───"
if SKILL/scripts/validate_evidence.py OUT/12-catalogo-entidades-protobuf.md --quiet --no-color; then
  echo "OK: evidence"
else
  echo "FAIL: evidence"; FAIL=1
fi

echo "─── validate_mermaid ───"
if SKILL/scripts/validate_mermaid.sh OUT/12-catalogo-entidades-protobuf.md --quiet; then
  echo "OK: mermaid"
else
  echo "FAIL: mermaid"; FAIL=1
fi

echo "─── count_rows_439 (prueba literal del ROADMAP) ───"
if OUT/_ledger/pruebas/B2.2/count_rows_439.py; then
  echo "OK: count_rows_439"
else
  echo "FAIL: count_rows_439"; FAIL=1
fi

if [ "$FAIL" -eq 0 ]; then
  echo
  echo "OK: B2.2 (template + evidence + mermaid + count_rows, 4/4 checks)"
  exit 0
else
  echo
  echo "FAIL: B2.2"
  exit 1
fi