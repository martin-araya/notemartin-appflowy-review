#!/usr/bin/env bash
# validate-C1.sh — Prueba de la Fase C1 (Pasada global de validadores).
#
# C1 cierra la deuda que B6 dejó explícita para C1/C3 (ROADMAP.md:705):
# 48 referencias rotas en `OUT/15-secuencias-globales/` (7 E_LINE_OUT_OF_RANGE,
# 41 E_PATH_NOT_IN_INVENTARIO) más el daño de Markdown que dejó la pasada
# anterior de `fix_evidence_prefix.py` (98 spans de `inline code` rotos).
#
# Checks (5):
#   1. validate_template  sobre todo OUT/            → 190/190
#   2. validate_evidence  sobre todo OUT/            → 0 errores
#   3. validate_mermaid   sobre todo OUT/            → 0 fallos
#   4. validate_coverage  --threshold 100           → 4 603/4 603
#   5. Idempotencia + residuos de la reparación
#        5a. fix_line_offsets.py 2ª pasada           → 0 refs rotas
#        5b. repair_markdown_damage.py --dry-run     → 0 runs
#        5c. fix_evidence_prefix.py --dry-run        → 0 reparados
#        5d. refs_rotas.csv sin filas de entregables pendientes
#              5e. § C1 de 22-preguntas-abiertas.md con las 10 retiradas
#
# Salida: 0 si OK, 1 si algún check falla.

set -u
set -o pipefail
SCRIPT_NAME=$(basename "$0")
fail() { echo "FAIL: $1" >&2; exit 1; }

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="$ROOT/OUT"
PRUEBAS="$OUT/_ledger/pruebas/C1"
VT="$ROOT/SKILL/scripts/validate_template.py"
VE="$ROOT/SKILL/scripts/validate_evidence.py"
VM="$ROOT/SKILL/scripts/validate_mermaid.sh"
VC="$ROOT/SKILL/scripts/validate_coverage.py"
FLO="$ROOT/SKILL/scripts/fix_line_offsets.py"
RMD="$ROOT/SKILL/scripts/repair_markdown_damage.py"
FEP="$ROOT/SKILL/scripts/fix_evidence_prefix.py"
LEDGER="$OUT/_ledger/cobertura.csv"

for f in "$VT" "$VE" "$VM" "$VC" "$FLO" "$RMD" "$FEP"; do
  [ -f "$f" ] || fail "no existe $f"
done
[ -f "$LEDGER" ] || fail "no existe $LEDGER"
[ -d "$PRUEBAS" ] || fail "no existe $PRUEBAS"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "=== $SCRIPT_NAME — Fase C1 ==="

# --- Check 1: plantilla --------------------------------------------------
echo "--- Check 1: validate_template sobre OUT/"
python3 "$VT" "$OUT" > "$TMP/tpl.log" 2>&1
TPL_RC=$?
tail -1 "$TMP/tpl.log"
TPL_LINE="$(tail -1 "$TMP/tpl.log")"
echo "$TPL_LINE" | grep -q 'errors=0' || fail "check 1: $TPL_LINE"
[ "$TPL_RC" -eq 0 ] || fail "check 1: validate_template devolvió $TPL_RC"

# --- Check 2: evidencia --------------------------------------------------
echo "--- Check 2: validate_evidence sobre OUT/ (sin meta-docs ni _ledger)"
python3 "$VE" "$OUT" --json --quiet > "$TMP/ev.json" 2>/dev/null
EV_RC=$?
python3 - "$TMP/ev.json" <<'PY'
import json, sys
d = json.load(open(sys.argv[1]))
s = d["summary"]
print(f"    refs={s['references']} ok={s['ok']} errors={s['errors']} files={s['files']}")
if s["errors"]:
    for e in d["errors"][:20]:
        print("   ", e["code"], e["doc"], e["doc_line"], e["ref"])
    sys.exit(1)
PY
[ $? -eq 0 ] || fail "check 2: hay referencias de evidencia rotas"
[ "$EV_RC" -eq 0 ] || fail "check 2: validate_evidence devolvió $EV_RC"

# --- Check 3: mermaid ---------------------------------------------------
echo "--- Check 3: validate_mermaid sobre OUT/"
bash "$VM" "$OUT" > "$TMP/mmd.log" 2>&1
MMD_RC=$?
tail -1 "$TMP/mmd.log"
grep -q 'fail=0' "$TMP/mmd.log" || fail "check 3: hay diagramas Mermaid rotos"
[ "$MMD_RC" -eq 0 ] || fail "check 3: validate_mermaid devolvió $MMD_RC"

# --- Check 4: cobertura -------------------------------------------------
echo "--- Check 4: validate_coverage --threshold 100"
python3 "$VC" --threshold 100 > "$TMP/cov.log" 2>&1
COV_RC=$?
tail -2 "$TMP/cov.log"
[ "$COV_RC" -eq 0 ] || fail "check 4: cobertura por debajo del 100 %"

# --- Check 5: idempotencia y residuos -----------------------------------
echo "--- Check 5a: fix_line_offsets.py idempotente"
# `--csv-dir` apunta a un temporal: los CSV de `$PRUEBAS` son el **registro de
# auditoría de C1** (lo que había antes y lo que se retiró) y una ejecución en
# vivo no debe sobrescribirlos con cero filas.
python3 "$FLO" --apply --csv-dir "$TMP" "$OUT" > "$TMP/flo.log" 2>&1
grep -q 'refs rotas detectadas: 0' "$TMP/flo.log" \
  || fail "check 5a: fix_line_offsets todavía encuentra refs rotas"
tail -1 "$TMP/flo.log"

echo "--- Check 5b: repair_markdown_damage.py sin runs pendientes"
python3 "$RMD" --dry-run "$OUT" > "$TMP/rmd.log" 2>&1
grep -q 'runs reparados: 0' "$TMP/rmd.log" \
  || fail "check 5b: quedan spans de inline code rotos"
tail -1 "$TMP/rmd.log"

echo "--- Check 5c: fix_evidence_prefix.py sin reescrituras pendientes"
python3 "$FEP" --dry-run "$OUT" > "$TMP/fep.log" 2>&1
grep -q 'referencias normalizadas: 0' "$TMP/fep.log" \
  || fail "check 5c: fix_evidence_prefix todavía reescribiría referencias"
tail -1 "$TMP/fep.log"

echo "--- Check 5d: refs_rotas.csv = inventario de la deuda que C1 cerró"
# `refs_rotas.csv` es el inventario **previo** a la reparación (trazabilidad):
# deben estar las 48 referencias rotas de los entregables que B5 dejó, y cada
# una debe seguir cerrada —lo garantiza el Check 2, que exige 0 errores—.
[ -f "$PRUEBAS/refs_rotas.csv" ] || fail "check 5d: falta refs_rotas.csv"
N_ENT="$(tail -n +2 "$PRUEBAS/refs_rotas.csv" | grep -c ',entregable,' || true)"
echo "    refs rotas de entregables inventariadas antes de C1: $N_ENT"
[ "$N_ENT" -eq 48 ] || fail "check 5d: se esperaban 48 refs de entregables, hay $N_ENT"
N_TOT="$(tail -n +2 "$PRUEBAS/refs_rotas.csv" | wc -l | tr -d ' ')"
echo "    refs rotas totales inventariadas (incl. meta y _ledger): $N_TOT"

echo "--- Check 5e: § C1 de 22-preguntas-abiertas.md con las 10 retiradas"
[ -f "$PRUEBAS/refs_retiradas.csv" ] || fail "check 5e: falta refs_retiradas.csv"
N_RET="$(tail -n +2 "$PRUEBAS/refs_retiradas.csv" | wc -l | tr -d ' ')"
echo "    citas retiradas registradas: $N_RET"
[ "$N_RET" -eq 10 ] || fail "check 5e: se esperaban 10 citas retiradas, hay $N_RET"
grep -q '## C1 · Pasada global de validadores' "$OUT/22-preguntas-abiertas.md" \
  || fail "check 5e: 22-preguntas-abiertas.md no tiene la sección § C1"
# Los documentos de B5 no deben conservar marcas de retirada por encima de las
# 10 que C1 inventarió. La cifra solo puede BAJAR: cada vez que una marca
# desaparece es porque el documento se ha reescrito con el símbolo real, que es
# lo que hizo la Fase C3 al resolver 4 de las 10marks con una reescritura
# (B5.7, B5.10 y B5.11). Lo que NO se admite es que aparezcan marcas nuevas.
if grep -rq 'NO DETERMINADO.*22-preguntas-abiertas.md § C1' "$OUT/15-secuencias-globales"; then
  n=$(grep -rc 'NO DETERMINADO.*22-preguntas-abiertas.md § C1' "$OUT/15-secuencias-globales" | awk -F: '{s+=$2} END {print s}')
  [ "$n" -le 10 ] || fail "check 5e: B5 tiene $n marcas de retirada, más que las 10 de C1"
  echo "    marcas de retirada en B5: $n (de un máximo de 10; las $((10 - n)) restantes resueltas en C3)"
else
  echo "    marcas de retirada en B5: 0 (las 10 de C1 resueltas)"
fi

echo
echo "=== $SCRIPT_NAME: checks en verde ==="
exit 0