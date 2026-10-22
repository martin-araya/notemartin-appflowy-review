#!/usr/bin/env bash
# validate-B1.5.sh — suite de validación de la fase B1.5.
# Ejecuta los 4 validadores A3.x sobre los 6 sub-docs + la prueba literal
# de cobertura (validate_B1_5_coverage.py).
set -uo pipefail

cd "$(dirname "$0")/../.."

FAIL=0

for doc in 00-indice 01-ffi 02-lib-dispatch 03-codegen 04-notificaciones 05-ejemplo-traza-opendocument; do
  echo "─── validate_template (${doc}) ───"
  if SKILL/scripts/validate_template.py "OUT/06-puente-flutter-rust/${doc}.md" --quiet --no-color; then
    echo "OK: template ${doc}"
  else
    echo "FAIL: template ${doc}"; FAIL=1
  fi

  echo "─── validate_evidence (${doc}) ───"
  if SKILL/scripts/validate_evidence.py "OUT/06-puente-flutter-rust/${doc}.md" --quiet --no-color; then
    echo "OK: evidence ${doc}"
  else
    echo "FAIL: evidence ${doc}"; FAIL=1
  fi

  echo "─── validate_mermaid (${doc}) ───"
  if SKILL/scripts/validate_mermaid.sh "OUT/06-puente-flutter-rust/${doc}.md" --quiet; then
    echo "OK: mermaid ${doc}"
  else
    echo "FAIL: mermaid ${doc}"; FAIL=1
  fi
done

echo "─── validate_B1_5_coverage ───"
if OUT/_ledger/pruebas/B1.5/validate_B1_5_coverage.py --quiet; then
  echo "OK: coverage"
else
  echo "FAIL: coverage"; FAIL=1
fi

if [ "$FAIL" -eq 0 ]; then
  echo
  echo "OK: B1.5 (template x6 + evidence x6 + mermaid x6 + coverage, 19/19 checks)"
  exit 0
else
  echo
  echo "FAIL: B1.5"
  exit 1
fi
