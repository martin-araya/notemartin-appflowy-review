#!/usr/bin/env bash
# validate-A3.5.sh — orquestador de la prueba del ROADMAP A3.5.
# Invoca SKILL/scripts/build_index.py sobre los fixtures y verifica
# el comportamiento exigido por la fase.

set -u
set -o pipefail

ROOT="/Users/martin/Desktop/projects/Skills/notemartin-appflowy-review"
SCRIPT="$ROOT/SKILL/scripts/build_index.py"
FIXDIR="$ROOT/OUT/_ledger/pruebas/A3.5/fixtures"
INDEX="$FIXDIR/00-INDEX.md"
LOG="$ROOT/OUT/_ledger/pruebas/A3.5/validate.log"

mkdir -p "$(dirname "$LOG")"
: > "$LOG"

log() { printf '[%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" | tee -a "$LOG"; }

PASS=0
FAIL=0
checks=0
check() {
  local name="$1" result="$2" detail="${3:-}"
  checks=$(( checks + 1 ))
  if [[ "$result" == "0" ]]; then
    PASS=$(( PASS + 1 ))
    log "  OK  check $checks: $name"
  else
    FAIL=$(( FAIL + 1 ))
    log "  FAIL check $checks: $name — $detail"
  fi
}

# --- check 1: script ejecutable ---
if [[ -x "$SCRIPT" ]]; then
  check "script ejecutable" 0
else
  check "script ejecutable" 1 "no se encuentra o no es ejecutable: $SCRIPT"
  log "abortando: script no disponible"
  exit 1
fi

# --- check 2: --help imprime uso y sale 0 ---
HELP_OUT=$(python3 "$SCRIPT" --help 2>&1)
HELP_RC=$?
if [[ $HELP_RC -eq 0 ]] && printf '%s' "$HELP_OUT" | grep -q "build_index.py"; then
  check "--help imprime uso y sale 0" 0
else
  check "--help imprime uso y sale 0" 1 "rc=$HELP_RC"
fi

# Regenerar el índice antes de los checks siguientes.
python3 "$SCRIPT" --no-color --out-dir "$FIXDIR" --out "$INDEX" >/dev/null 2>&1 || true

# --- check 3: 00-INDEX.md generado contiene 4 ids (A, B, C, 00-INDEX) ---
IDX_HAS_A=$(grep -cE "^\| \`A\.md\` \| A \|" "$INDEX" || true)
IDX_HAS_B=$(grep -cE "^\| \`B\.md\` \| B \|" "$INDEX" || true)
IDX_HAS_C=$(grep -cE "^\| \`C\.md\` \| C \|" "$INDEX" || true)
IDX_HAS_INDEX=$(grep -cE "^\| \`00-INDEX\.md\` \| 00-INDEX \|" "$INDEX" || true)
if [[ "$IDX_HAS_A" -ge 1 && "$IDX_HAS_B" -ge 1 && "$IDX_HAS_C" -ge 1 && "$IDX_HAS_INDEX" -ge 1 ]]; then
  check "00-INDEX.md contiene los 4 ids (A, B, C, 00-INDEX) en la tabla" 0
else
  check "00-INDEX.md contiene los 4 ids (A, B, C, 00-INDEX) en la tabla" 1 "A=$IDX_HAS_A B=$IDX_HAS_B C=$IDX_HAS_C idx=$IDX_HAS_INDEX"
fi

# --- check 4: sección 'no resueltos' contiene NOEXISTE pero NO A ni B ---
NR_HAS_NOEX=$(grep -cE "\[\[NOEXISTE\]\]" "$INDEX" || true)
NR_HAS_A=$(grep -cE "→ \`\[\[A\]\]" "$INDEX" || true)
NR_HAS_B=$(grep -cE "→ \`\[\[B\]\]" "$INDEX" || true)
# Nota: A y B sí aparecen en "mapa de enlaces" como destinos, pero la
# sección 8 "no resueltos" sólo debe listar NOEXISTE.
# Buscamos en la sección 8 con un patrón más específico.
NR_SECTION=$(awk '/^## 8\. Enlaces no resueltos/{f=1; next} /^## 9\./{f=0} f' "$INDEX")
NR_SECTION_NOEX=$(printf '%s' "$NR_SECTION" | grep -c "NOEXISTE" || true)
NR_SECTION_A=$(printf '%s' "$NR_SECTION" | grep -cE "→ \`\[\[A\]\]" || true)
NR_SECTION_B=$(printf '%s' "$NR_SECTION" | grep -cE "→ \`\[\[B\]\]" || true)
if [[ "$NR_SECTION_NOEX" -ge 1 ]] && [[ "$NR_SECTION_A" -eq 0 ]] && [[ "$NR_SECTION_B" -eq 0 ]]; then
  check "sección 8 (no resueltos) contiene sólo NOEXISTE, no A ni B" 0
else
  check "sección 8 (no resueltos) contiene sólo NOEXISTE, no A ni B" 1 "NOEXISTE=$NR_SECTION_NOEX; A_in_8=$NR_SECTION_A; B_in_8=$NR_SECTION_B"
fi

# --- check 5: sección 'Commits' menciona los 3 commit_short ---
COMMIT_5C=$(grep -c "5cf3a36" "$INDEX" || true)
COMMIT_4D=$(grep -c "4dfccef" "$INDEX" || true)
COMMIT_470=$(grep -c "470c4e7" "$INDEX" || true)
if [[ "$COMMIT_5C" -ge 1 && "$COMMIT_4D" -ge 1 && "$COMMIT_470" -ge 1 ]]; then
  check "sección 2 (Commits) menciona los 3 commit_short (5cf3a36, 4dfccef, 470c4e7)" 0
else
  check "sección 2 (Commits) menciona los 3 commit_short" 1 "5c=$COMMIT_5C 4d=$COMMIT_4D 470=$COMMIT_470"
fi

# --- check 6: tabla de cobertura de fuente muestra 2 capas y global 50% ---
COV_HAS_BLOC=$(grep -cE "^\| bloc \|" "$INDEX" || true)
COV_HAS_UI=$(grep -cE "^\| ui \|" "$INDEX" || true)
COV_GLOBAL=$(grep -cE "GLOBAL.*\*\*4\*\*.*\*\*2\*\*" "$INDEX" || true)
COV_GLOBAL_PCT=$(grep -cE "GLOBAL.*\*\*4\*\*.*\*\*2\*\*.*\*\*50\.00%\*\*" "$INDEX" || true)
if [[ "$COV_HAS_BLOC" -ge 1 && "$COV_HAS_UI" -ge 1 && "$COV_GLOBAL_PCT" -ge 1 ]]; then
  check "sección 4 (cobertura fuente) muestra bloc, ui, GLOBAL=4/2=50.00%" 0
else
  check "sección 4 (cobertura fuente) muestra bloc, ui, GLOBAL=4/2=50.00%" 1 "bloc=$COV_HAS_BLOC ui=$COV_HAS_UI global_pct=$COV_GLOBAL_PCT"
fi

# --- check 7: --check-links exit 1 (por [[NOEXISTE]]) ---
CL_OUT=$(python3 "$SCRIPT" --no-color --check-links --out-dir "$FIXDIR" 2>&1)
CL_RC=$?
if [[ $CL_RC -eq 1 ]]; then
  check "--check-links exit 1 por [[NOEXISTE]]" 0
else
  check "--check-links exit 1 por [[NOEXISTE]]" 1 "rc=$CL_RC; out=$CL_OUT"
fi

# --- check 8: --json produce JSON parseable con unresolved_count == 1 ---
JSON_OUT=$(python3 "$SCRIPT" --no-color --json --out-dir "$FIXDIR" 2>/dev/null || true)
if printf '%s' "$JSON_OUT" | python3 -m json.tool >/dev/null 2>&1; then
  UNR_CNT=$(printf '%s' "$JSON_OUT" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(d["summary"]["unresolved_count"])' 2>/dev/null)
  if [[ "$UNR_CNT" == "1" ]]; then
    check "--json produce JSON parseable con unresolved_count == 1" 0
  else
    check "--json produce JSON parseable con unresolved_count == 1" 1 "unresolved_count=$UNR_CNT"
  fi
else
  check "--json produce JSON parseable con unresolved_count == 1" 1 "json inválido"
fi

# --- check 9: modo "todo resuelto" con D.md con id NOEXISTE → exit 0 ---
DMDFILE="$FIXDIR/D.md"
cat > "$DMDFILE" <<'EOF'
---
id: NOEXISTE
titulo: Doc D
estado: verificado
---

# D — Doc D

Este doc tiene id `NOEXISTE` para resolver el enlace roto de C.md.
EOF
CL2_OUT=$(python3 "$SCRIPT" --no-color --check-links --out-dir "$FIXDIR" 2>&1)
CL2_RC=$?
rm -f "$DMDFILE"
# Regenerar el índice sin D.md para que el resto del estado sea
# coherente con los demás checks.
python3 "$SCRIPT" --no-color --out-dir "$FIXDIR" --out "$INDEX" >/dev/null 2>&1 || true
if [[ $CL2_RC -eq 0 ]]; then
  check "modo 'todo resuelto' (con D.md con id NOEXISTE) → --check-links exit 0" 0
else
  check "modo 'todo resuelto' (con D.md con id NOEXISTE) → --check-links exit 0" 1 "rc=$CL2_RC; out=$CL2_OUT"
fi

# --- check 10: el árbol del índice muestra los 4 docs ---
TREE_HAS_A=$(grep -cE "├── A\.md" "$INDEX" || true)
TREE_HAS_B=$(grep -cE "├── B\.md" "$INDEX" || true)
TREE_HAS_C=$(grep -cE "├── C\.md" "$INDEX" || true)
TREE_HAS_INDEX=$(grep -cE "├── 00-INDEX\.md" "$INDEX" || true)
if [[ "$TREE_HAS_A" -ge 1 && "$TREE_HAS_B" -ge 1 && "$TREE_HAS_C" -ge 1 && "$TREE_HAS_INDEX" -ge 1 ]]; then
  check "sección 5 (árbol) muestra los 4 docs" 0
else
  check "sección 5 (árbol) muestra los 4 docs" 1 "A=$TREE_HAS_A B=$TREE_HAS_B C=$TREE_HAS_C idx=$TREE_HAS_INDEX"
fi

# --- summary ---
log "---"
log "resultado: $PASS/$checks checks OK ($FAIL fallidos)"
if [[ $FAIL -eq 0 ]]; then
  log "OK: A3.5 (build_index.py funciona: genera 00-INDEX.md con árbol, estado, cobertura, commits; resuelve [[id]] → rutas reales)"
  exit 0
else
  log "FAIL: A3.5 (revisar logs)"
  exit 1
fi
