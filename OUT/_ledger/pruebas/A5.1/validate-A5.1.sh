#!/usr/bin/env bash
# validate-A5.1.sh — Smoke ejecutable del gate de la fase A5.1 (Piloto F08).
# Re-ejecuta los 3 validadores reales + el revisor (run_subagent.py) sobre
# el documento F08 y debe salir 0 si todo OK.
#
# Fase A5.1 de la skill `notemartin-appflowy-review`.

set -u
set -o pipefail

SCRIPT_NAME=$(basename "$0")
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
PROJECT_ROOT=$(cd "$SCRIPT_DIR/../../../.." && pwd)
DOC="$PROJECT_ROOT/OUT/09-features/F08-busqueda-e-indexacion/F08-busqueda-e-indexacion.md"
UNIT="$PROJECT_ROOT/OUT/_ledger/units/F08.json"
REVISOR_OUT="$PROJECT_ROOT/OUT/_ledger/revisor_f08_output.json"
INVENTARIO="$PROJECT_ROOT/OUT/_ledger/inventario.json"

# --- 0. prerrequisitos -----------------------------------------------------
fail=0
if [[ ! -f "$DOC" ]]; then
  echo "[$SCRIPT_NAME] FAIL: no existe $DOC" >&2
  exit 2
fi
if [[ ! -f "$UNIT" ]]; then
  echo "[$SCRIPT_NAME] FAIL: no existe $UNIT" >&2
  exit 2
fi
if [[ ! -f "$INVENTARIO" ]]; then
  echo "[$SCRIPT_NAME] FAIL: no existe $INVENTARIO" >&2
  exit 2
fi

# --- 1. validate_template -------------------------------------------------
echo "[$SCRIPT_NAME] check 1: validate_template.py"
if python3 "$PROJECT_ROOT/SKILL/scripts/validate_template.py" "$DOC" >/dev/null 2>&1; then
  echo "  OK"
else
  echo "  FAIL" >&2
  fail=1
fi

# --- 2. validate_evidence -------------------------------------------------
echo "[$SCRIPT_NAME] check 2: validate_evidence.py"
ev_out=$(python3 "$PROJECT_ROOT/SKILL/scripts/validate_evidence.py" "$DOC" 2>&1)
ev_exit=$?
if [[ $ev_exit -eq 0 ]]; then
  echo "  OK ($(echo "$ev_out" | tail -1 | sed 's/.*: //'))"
else
  echo "  FAIL" >&2
  echo "$ev_out" | tail -10 >&2
  fail=1
fi

# --- 3. validate_mermaid --------------------------------------------------
echo "[$SCRIPT_NAME] check 3: validate_mermaid.sh"
mm_out=$(bash "$PROJECT_ROOT/SKILL/scripts/validate_mermaid.sh" "$DOC" 2>&1)
mm_exit=$?
if [[ $mm_exit -eq 0 ]]; then
  echo "  OK ($(echo "$mm_out" | tail -1 | sed 's/.*: //'))"
else
  echo "  FAIL" >&2
  echo "$mm_out" | tail -10 >&2
  fail=1
fi

# --- 4. run_subagent.py --rol revisor ------------------------------------
echo "[$SCRIPT_NAME] check 4: run_subagent.py --rol revisor"
python3 "$PROJECT_ROOT/SKILL/scripts/run_subagent.py" \
  --rol revisor \
  --unit "$UNIT" \
  --out "$REVISOR_OUT" \
  --out-root "$PROJECT_ROOT" \
  --quiet >/dev/null 2>&1
rev_exit=$?
if [[ $rev_exit -eq 0 ]]; then
  veredicto=$(python3 -c "import json; d=json.load(open('$REVISOR_OUT')); print(d.get('veredicto','?'))" 2>/dev/null)
  if [[ "$veredicto" == "aprobado" ]]; then
    echo "  OK (veredicto=aprobado)"
  else
    echo "  FAIL (veredicto=$veredicto)" >&2
    fail=1
  fi
else
  echo "  FAIL (run_subagent.py exit=$rev_exit)" >&2
  fail=1
fi

# --- 5. cobertura F08 100% ------------------------------------------------
echo "[$SCRIPT_NAME] check 5: cobertura F08 100% verificado"
total=$(python3 -c "
import csv
n=0
with open('$PROJECT_ROOT/OUT/_ledger/cobertura.csv') as f:
  for r in csv.DictReader(f):
    if r['feature_ids']=='F08':
      n+=1
print(n)
")
verif=$(python3 -c "
import csv
n=0
with open('$PROJECT_ROOT/OUT/_ledger/cobertura.csv') as f:
  for r in csv.DictReader(f):
    if r['feature_ids']=='F08' and r['estado']=='verificado':
      n+=1
print(n)
")
if [[ "$total" == "21" && "$verif" == "21" ]]; then
  echo "  OK (21/21 verificado)"
else
  echo "  FAIL (total=$total, verificado=$verif)" >&2
  fail=1
fi

# --- 6. ROADMAP.md línea 107 contiene ✅ ---------------------------------
echo "[$SCRIPT_NAME] check 6: ROADMAP.md A5.1 marcado"
if grep -q "Fase A5.1" "$PROJECT_ROOT/ROADMAP.md" && grep -A2 "Fase A5.1" "$PROJECT_ROOT/ROADMAP.md" | grep -q "✅"; then
  echo "  OK"
else
  echo "  FAIL (Fase A5.1 sin ✅ en ROADMAP.md)" >&2
  fail=1
fi

# --- resumen --------------------------------------------------------------
if [[ $fail -eq 0 ]]; then
  echo "---"
  echo "OK: A5.1 — Piloto F08 Búsqueda verificado (6/6 checks)"
  exit 0
else
  echo "---"
  echo "FAIL: A5.1 — uno o más checks fallaron" >&2
  exit 1
fi
