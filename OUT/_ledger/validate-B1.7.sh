#!/usr/bin/env bash
# validate-B1.7.sh — suite de validación de la fase B1.7.
set -uo pipefail

cd "$(dirname "$0")/../.."

FAIL=0

for doc in 00-indice 01-sqlite-schema 02-kv 03-collab-db 04-file-cache 05-sqlite-vec 06-migraciones 07-rutas-plataforma; do
  echo "─── validate_template (${doc}) ───"
  if SKILL/scripts/validate_template.py "OUT/08-persistencia/${doc}.md" --quiet --no-color; then
    echo "OK: template ${doc}"
  else
    echo "FAIL: template ${doc}"; FAIL=1
  fi

  echo "─── validate_evidence (${doc}) ───"
  if SKILL/scripts/validate_evidence.py "OUT/08-persistencia/${doc}.md" --quiet --no-color; then
    echo "OK: evidence ${doc}"
  else
    echo "FAIL: evidence ${doc}"; FAIL=1
  fi

  echo "─── validate_mermaid (${doc}) ───"
  if SKILL/scripts/validate_mermaid.sh "OUT/08-persistencia/${doc}.md" --quiet; then
    echo "OK: mermaid ${doc}"
  else
    echo "FAIL: mermaid ${doc}"; FAIL=1
  fi
done

echo "─── validate_B1_7_coverage ───"
if OUT/_ledger/pruebas/B1.7/validate_B1_7_coverage.py --quiet; then
  echo "OK: coverage"
else
  echo "FAIL: coverage"; FAIL=1
fi

if [ "$FAIL" -eq 0 ]; then
  echo
  echo "OK: B1.7 (template x8 + evidence x8 + mermaid x8 + coverage, 25/25 checks)"
  exit 0
else
  echo
  echo "FAIL: B1.7"
  exit 1
fi
