#!/usr/bin/env bash
# validate-B1.2.sh — suite de validación de la fase B1.2.
# Ejecuta los 3 validadores A3.x sobre los 2 docs + la prueba literal de cobertura.
# Salida OK si los 7 checks pasan.
set -uo pipefail

cd "$(dirname "$0")/../.."

FAIL=0

echo "─── validate_template (02) ───"
if SKILL/scripts/validate_template.py OUT/02-stack-y-dependencias.md --quiet --no-color; then
  echo "OK: template 02"
else
  echo "FAIL: template 02"; FAIL=1
fi

echo "─── validate_template (17) ───"
if SKILL/scripts/validate_template.py OUT/17-grafo-dependencias.md --quiet --no-color; then
  echo "OK: template 17"
else
  echo "FAIL: template 17"; FAIL=1
fi

echo "─── validate_evidence (02) ───"
if SKILL/scripts/validate_evidence.py OUT/02-stack-y-dependencias.md --quiet --no-color; then
  echo "OK: evidence 02"
else
  echo "FAIL: evidence 02"; FAIL=1
fi

echo "─── validate_evidence (17) ───"
if SKILL/scripts/validate_evidence.py OUT/17-grafo-dependencias.md --quiet --no-color; then
  echo "OK: evidence 17"
else
  echo "FAIL: evidence 17"; FAIL=1
fi

echo "─── validate_mermaid (02) ───"
if SKILL/scripts/validate_mermaid.sh OUT/02-stack-y-dependencias.md --quiet; then
  echo "OK: mermaid 02"
else
  echo "FAIL: mermaid 02"; FAIL=1
fi

echo "─── validate_mermaid (17) ───"
if SKILL/scripts/validate_mermaid.sh OUT/17-grafo-dependencias.md --quiet; then
  echo "OK: mermaid 17"
else
  echo "FAIL: mermaid 17"; FAIL=1
fi

echo "─── validate_B1_2_coverage (literal) ───"
if OUT/_ledger/pruebas/B1.2/validate_B1_2_coverage.py --quiet; then
  echo "OK: coverage"
else
  echo "FAIL: coverage"; FAIL=1
fi

if [ "$FAIL" -eq 0 ]; then
  echo
  echo "OK: B1.2 (template x2 + evidence x2 + mermaid x2 + coverage, 7/7 checks)"
  exit 0
else
  echo
  echo "FAIL: B1.2"
  exit 1
fi
