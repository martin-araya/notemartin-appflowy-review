#!/usr/bin/env bash
# validate-B1.6.sh — suite de validación de la fase B1.6.
set -uo pipefail

cd "$(dirname "$0")/../.."

FAIL=0

for doc in 00-indice 01-modelo-collab 02-folder 03-documento 04-database 05-user-awareness 06-collab-plugins 07-snapshots-conflict-resolution; do
  echo "─── validate_template (${doc}) ───"
  if SKILL/scripts/validate_template.py "OUT/07-motor-colaborativo-crdt/${doc}.md" --quiet --no-color; then
    echo "OK: template ${doc}"
  else
    echo "FAIL: template ${doc}"; FAIL=1
  fi

  echo "─── validate_evidence (${doc}) ───"
  if SKILL/scripts/validate_evidence.py "OUT/07-motor-colaborativo-crdt/${doc}.md" --quiet --no-color; then
    echo "OK: evidence ${doc}"
  else
    echo "FAIL: evidence ${doc}"; FAIL=1
  fi

  echo "─── validate_mermaid (${doc}) ───"
  if SKILL/scripts/validate_mermaid.sh "OUT/07-motor-colaborativo-crdt/${doc}.md" --quiet; then
    echo "OK: mermaid ${doc}"
  else
    echo "FAIL: mermaid ${doc}"; FAIL=1
  fi
done

echo "─── validate_B1_6_coverage ───"
if OUT/_ledger/pruebas/B1.6/validate_B1_6_coverage.py --quiet; then
  echo "OK: coverage"
else
  echo "FAIL: coverage"; FAIL=1
fi

if [ "$FAIL" -eq 0 ]; then
  echo
  echo "OK: B1.6 (template x8 + evidence x8 + mermaid x8 + coverage, 25/25 checks)"
  exit 0
else
  echo
  echo "FAIL: B1.6"
  exit 1
fi
