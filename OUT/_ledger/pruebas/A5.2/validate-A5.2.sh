#!/usr/bin/env bash
# validate-A5.2.sh — Smoke ejecutable del gate de la fase A5.2 (Ajuste de la skill).
# Re-ejecuta 5 checks sobre los entregables de A5.2 y debe salir 0 si todo OK.

set -u
set -o pipefail

SCRIPT_NAME=$(basename "$0")
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
PROJECT_ROOT=$(cd "$SCRIPT_DIR/../../../.." && pwd)

CHANGELOG="$PROJECT_ROOT/SKILL/CHANGELOG.md"
RUN_REVISOR="$PROJECT_ROOT/SKILL/scripts/run_subagent.py"
RUN_PLACEHOLDER="$PROJECT_ROOT/SKILL/scripts/run_subagent_placeholder.py"
RUN_AUTHOR="$PROJECT_ROOT/SKILL/scripts/run_subagent_author.sh"
UNIT_F08="$PROJECT_ROOT/OUT/_ledger/units/F08.json"
INVENTARIO="$PROJECT_ROOT/OUT/_ledger/inventario.json"
PREGUNTAS="$PROJECT_ROOT/OUT/22-preguntas-abiertas.md"
ROADMAP="$PROJECT_ROOT/ROADMAP.md"
REVISOR_OUT="/tmp/a52_revisor_f08.json"

fail=0

# --- 0. prerrequisitos -----------------------------------------------------
for p in "$CHANGELOG" "$RUN_REVISOR" "$RUN_PLACEHOLDER" "$RUN_AUTHOR" "$UNIT_F08" "$INVENTARIO" "$PREGUNTAS" "$ROADMAP"; do
  if [[ ! -e "$p" ]]; then
    echo "[$SCRIPT_NAME] FAIL: falta $p" >&2
    exit 2
  fi
done

# --- 1. CHANGELOG.md presente y con entrada 0.2.0 -----------------------
echo "[$SCRIPT_NAME] check 1: SKILL/CHANGELOG.md con entrada 0.2.0"
if grep -q "^## \[0\.2\.0\]" "$CHANGELOG"; then
  added=$(grep -c "^### Added" "$CHANGELOG" || true)
  changed=$(grep -c "^### Changed" "$CHANGELOG" || true)
  fixed=$(grep -c "^### Fixed" "$CHANGELOG" || true)
  total=$((added + changed + fixed))
  if [[ $total -ge 3 ]]; then
    echo "  OK (Added=$added, Changed=$changed, Fixed=$fixed, total=$total)"
  else
    echo "  FAIL (total=$total, esperado >= 3)" >&2
    fail=1
  fi
else
  echo "  FAIL (no hay entrada 0.2.0)" >&2
  fail=1
fi

# --- 2. run_subagent.py sin modo autor -----------------------------------
echo "[$SCRIPT_NAME] check 2: run_subagent.py rechaza --rol autor"
out=$(python3 "$RUN_REVISOR" --rol autor --unit "$UNIT_F08" 2>&1 || true)
if echo "$out" | grep -q "invalid choice: 'autor'"; then
  echo "  OK"
else
  echo "  FAIL (no rechazó --rol autor)" >&2
  fail=1
fi

# --- 3. run_subagent_placeholder.py disponible y produce doc placeholder --
echo "[$SCRIPT_NAME] check 3: run_subagent_placeholder.py produce doc"
ph_out=$(python3 "$RUN_PLACEHOLDER" --rol autor --unit "$UNIT_F08" --out /tmp/a52_placeholder.json --out-root "$PROJECT_ROOT" 2>&1)
if [[ -f /tmp/a52_placeholder.json ]]; then
  has_doc=$(python3 -c "import json; d=json.load(open('/tmp/a52_placeholder.json')); print('OK' if d.get('documento') else 'FAIL')" 2>/dev/null)
  if [[ "$has_doc" == "OK" ]]; then
    echo "  OK (AutorOutput con campo documento)"
  else
    echo "  FAIL (placeholder no produjo AutorOutput válido)" >&2
    fail=1
  fi
else
  echo "  FAIL (placeholder no escribió JSON)" >&2
  echo "$ph_out" | tail -3 >&2
  fail=1
fi

# --- 4. run_subagent.py --rol revisor aprueba F08 -------------------------
echo "[$SCRIPT_NAME] check 4: run_subagent.py --rol revisor aprueba F08"
python3 "$RUN_REVISOR" --rol revisor --unit "$UNIT_F08" --out "$REVISOR_OUT" --out-root "$PROJECT_ROOT" --quiet >/dev/null 2>&1
if [[ $? -eq 0 ]]; then
  veredicto=$(python3 -c "import json; d=json.load(open('$REVISOR_OUT')); print(d.get('veredicto','?'))" 2>/dev/null)
  if [[ "$veredicto" == "aprobado" ]]; then
    echo "  OK (veredicto=aprobado)"
  else
    echo "  FAIL (veredicto=$veredicto)" >&2
    fail=1
  fi
else
  echo "  FAIL (run_subagent.py exit=$?)" >&2
  fail=1
fi

# --- 5. 4 preguntas abiertas de F08 en 22-preguntas-abiertas.md ---------
echo "[$SCRIPT_NAME] check 5: 4 preguntas abiertas de F08 volcadas"
n_f08=$(awk 'BEGIN{c=0; f=0} /^## De F08/{f=1; next} /^## /{if(f)f=0} {if(f && /\[NO DETERMINADO\]/)c++} END{print c+0}' "$PREGUNTAS")
if [[ "$n_f08" -ge 4 ]]; then
  echo "  OK ($n_f08 entradas)"
else
  echo "  FAIL (encontradas $n_f08, esperadas >= 4)" >&2
  fail=1
fi

# --- resumen --------------------------------------------------------------
if [[ $fail -eq 0 ]]; then
  echo "---"
  echo "OK: A5.2 — Ajuste de la skill verificado (5/5 checks)"
  exit 0
else
  echo "---"
  echo "FAIL: A5.2 — uno o más checks fallaron" >&2
  exit 1
fi
