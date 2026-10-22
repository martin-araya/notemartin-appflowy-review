#!/usr/bin/env bash
# validate-B1.3.sh — suite de validación de la fase B1.3.
# Ejecuta los 3 validadores A3.x + la prueba de cobertura de contenedores/componentes.
# Salida OK si los 4 checks pasan.
set -uo pipefail

cd "$(dirname "$0")/../.."

FAIL=0

echo "─── validate_template ───"
if SKILL/scripts/validate_template.py OUT/04-arquitectura-global.md --quiet --no-color; then
  echo "OK: template"
else
  echo "FAIL: template"; FAIL=1
fi

echo "─── validate_evidence ───"
if SKILL/scripts/validate_evidence.py OUT/04-arquitectura-global.md --quiet --no-color; then
  echo "OK: evidence"
else
  echo "FAIL: evidence"; FAIL=1
fi

echo "─── validate_mermaid ───"
if SKILL/scripts/validate_mermaid.sh OUT/04-arquitectura-global.md --quiet; then
  echo "OK: mermaid"
else
  echo "FAIL: mermaid"; FAIL=1
fi

echo "─── validate_B1_3_coverage ───"
if OUT/_ledger/pruebas/B1.3/validate_B1_3_coverage.py --quiet; then
  echo "OK: coverage"
else
  echo "FAIL: coverage"; FAIL=1
fi

if [ "$FAIL" -eq 0 ]; then
  echo
  echo "OK: B1.3 (template+evidence+mermaid+coverage, 4/4 checks)"
  exit 0
else
  echo
  echo "FAIL: B1.3"
  exit 1
fi
