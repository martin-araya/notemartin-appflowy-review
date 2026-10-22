#!/usr/bin/env bash
# validate-A4.4.sh — Prueba de la Fase A4.4 (resume.py + record_unit_state.py).
# Salida: 0 si OK, 1 si algun check falla.
set -u
fail() { echo "FAIL: $1" >&2; exit 1; }
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
RESUME="$ROOT/SKILL/scripts/resume.py"
RECORD="$ROOT/SKILL/scripts/record_unit_state.py"
FIX="$ROOT/OUT/_ledger/pruebas/A4.4/fixtures"
LEDGER_FIX="$FIX/cut_cobertura.csv"
STATE_FIX="$FIX/cut_STATE.md"
DOCS_FIX="$FIX/docs_root/OUT/09-features"
UNITS_INDEX="$ROOT/OUT/_ledger/units/_index.json"
LEDGER_REAL="$ROOT/OUT/_ledger/cobertura.csv"

[ -f "$RESUME" ] || fail "no existe $RESUME"
[ -x "$RESUME" ] || fail "$RESUME no es ejecutable"
[ -f "$RECORD" ] || fail "no existe $RECORD"
[ -x "$RECORD" ] || fail "$RECORD no es ejecutable"
[ -d "$FIX" ]    || fail "no existe $FIX"
[ -f "$LEDGER_FIX" ] || fail "no existe $LEDGER_FIX"
[ -f "$STATE_FIX" ]  || fail "no existe $STATE_FIX"
[ -d "$DOCS_FIX" ]   || fail "no existe $DOCS_FIX"

# Check 1: --help funciona
python3 "$RESUME" --help >/dev/null 2>&1   || fail "--help de resume fallo"
python3 "$RECORD" --help >/dev/null 2>&1  || fail "--help de record_unit_state fallo"

# Check 2: la fixture tiene 4 verificados + 2 in_flight
python3 - "$LEDGER_FIX" <<'PY' || fail "fixture cut_cobertura.csv no cumple 4 verificados + 2 in_flight"
import csv, sys
verificados = set()
in_flight = set()
with open(sys.argv[1]) as f:
    r = csv.DictReader(f)
    for row in r:
        fids = [x for x in row["feature_ids"].split(";") if x]
        if row["estado"] == "verificado" and fids:
            verificados.add(sorted(fids)[0])
        if "in_flight:" in row.get("verificado_por", "") and fids:
            in_flight.add(sorted(fids)[0])
expected_ver = {"F11", "F14", "F18", "F20"}
assert verificados == expected_ver, f"verificados: {verificados} != {expected_ver}"
print(f"  fixture: {len(verificados)} verificados, {len(in_flight)} con marca in_flight")
PY

# Check 3: resume sobre la fixture produce plan con totales correctos
WORK=$(mktemp -d)
PLAN="$WORK/plan.json"
MD="$WORK/plan.md"

python3 "$RESUME" \
  --ledger "$LEDGER_FIX" \
  --units-index "$UNITS_INDEX" \
  --state "$STATE_FIX" \
  --docs-root "$DOCS_FIX" \
  --out-plan "$PLAN" --out-md "$MD" \
  --no-color 2>&1 || fail "resume sobre fixture fallo"
python3 - "$PLAN" <<'PY' || fail "plan no tiene totales correctos"
import json, sys
d = json.load(open(sys.argv[1]))
t = d["totales"]
assert t["verificados"] == 134, f"verificados: {t['verificados']} != 134"
assert t["in_flight"] == 2, f"in_flight: {t['in_flight']} != 2"
assert t["asignados"] == 4279, f"asignados: {t['asignados']} != 4279"
print(f"  plan: {t['verificados']} verificados, {t['in_flight']} in_flight, {t['pendientes']} pendientes")
PY

# Check 4: orden_ejecucion no incluye los 4 verificados
python3 - "$PLAN" <<'PY' || fail "orden incluye verificados"
import json, sys
d = json.load(open(sys.argv[1]))
orden = {u["unit_id"] for u in d["orden_ejecucion"]}
omitir = set(d["unidades_verificadas_omitir"])
inter = orden & omitir
assert not inter, f"orden intersecta omitir: {inter}"
print(f"  orden: {len(orden)} unidades, 0 en comun con omitir ({len(omitir)})")
PY

# Check 5: in_flight primeros
python3 - "$PLAN" <<'PY' || fail "in_flight no primero en orden"
import json, sys
d = json.load(open(sys.argv[1]))
orden = d["orden_ejecucion"]
assert len(orden) >= 2
assert orden[0]["estado"] == "in_flight", f"orden[0]: {orden[0]}"
assert orden[1]["estado"] == "in_flight", f"orden[1]: {orden[1]}"
ids = {orden[0]["unit_id"], orden[1]["unit_id"]}
assert ids == {"F01.1", "F01.4"}, f"in_flight esperados: {{F01.1, F01.4}}, hay {ids}"
print(f"  orden: F01.1 + F01.4 primeros, ambos in_flight")
PY

# Check 6: --json produce JSON parseable en stdout
python3 "$RESUME" \
  --ledger "$LEDGER_FIX" --units-index "$UNITS_INDEX" \
  --state "$STATE_FIX" --docs-root "$DOCS_FIX" \
  --json --no-color --quiet 2>/dev/null \
  | python3 -c "import json, sys; d=json.load(sys.stdin); assert d['schema_version']==1" \
  || fail "--json stdout no parseable"

# Check 7: record_unit_state --verificar muta el CSV (usar F03 que esta pendiente)
WORK2=$(mktemp -d)
cp "$LEDGER_FIX" "$WORK2/ledger.csv"
ANTES=$(awk -F, '$6=="verificado"' "$WORK2/ledger.csv" | wc -l | tr -d ' ')
python3 "$RECORD" \
  --unit F03 --accion verificar --verificado-por "test_validate" \
  --ledger "$WORK2/ledger.csv" --no-color 2>&1 \
  || fail "record --verificar fallo"
DESPUES=$(awk -F, '$6=="verificado"' "$WORK2/ledger.csv" | wc -l | tr -d ' ')
[ "$DESPUES" -gt "$ANTES" ] || fail "verificados no aumento: $ANTES -> $DESPUES"
echo "  record --verificar: $ANTES -> $DESPUES verificados"

# Check 8: record_unit_state --marcar_in_flight deja marca en verificado_por
python3 "$RECORD" \
  --unit F06 --accion marcar_in_flight \
  --ledger "$WORK2/ledger.csv" --no-color 2>&1 \
  || fail "record --marcar_in_flight fallo"
grep -q "in_flight:" "$WORK2/ledger.csv" || fail "no aparece marca in_flight:"
python3 "$RECORD" \
  --unit F06 --accion desmarcar_in_flight \
  --ledger "$WORK2/ledger.csv" --no-color 2>&1 \
  || fail "record --desmarcar_in_flight fallo"
grep -q "in_flight:" "$WORK2/ledger.csv" \
  && fail "marca in_flight no se elimino" \
  || echo "  record: marcar/desmarcar in_flight OK"

# Check 9: --regenerate-state-section reescribe "## Como reanudar" sin tocar el resto
STATE_TMP="$WORK2/state.md"
cp "$STATE_FIX" "$STATE_TMP"
ANTES_HASH=$(shasum "$STATE_TMP" 2>/dev/null | awk '{print $1}' || sha1sum "$STATE_TMP" | awk '{print $1}')
python3 "$RESUME" \
  --ledger "$LEDGER_FIX" --units-index "$UNITS_INDEX" \
  --state "$STATE_TMP" --docs-root "$DOCS_FIX" \
  --regenerate-state-section --no-color 2>&1 \
  || fail "regen fallo"
grep -q "## Cómo reanudar" "$STATE_TMP" || fail "seccion '## Como reanudar' no presente tras regen"
grep -q "Plan regenerado por" "$STATE_TMP" || fail "marca 'Plan regenerado por' no presente"
# Comprobar que otra seccion sigue presente
grep -q "## Índice de fases" "$STATE_TMP" || fail "otra seccion (Indice de fases) se perdio"
echo "  regen: '## Como reanudar' actualizada, resto intacto"

# Check 10: resume sobre el real (sin docs partial) devuelve plan no vacio
python3 "$RESUME" \
  --ledger "$LEDGER_REAL" --units-index "$UNITS_INDEX" \
  --state "$ROOT/OUT/STATE.md" --docs-root "$ROOT/OUT/09-features" \
  --no-color 2>&1 || fail "resume sobre real fallo"
python3 - "$ROOT/OUT/_ledger/resume-plan.json" <<'PY' || fail "plan real sin datos"
import json, sys
d = json.load(open(sys.argv[1]))
assert d["totales"]["asignados"] == 4603
assert d["totales"]["sin_asignar"] == 0
print(f"  real: {d['totales']}")
PY

rm -rf "$WORK" "$WORK2"

echo "OK: A4.4 (resume.py + record_unit_state.py: fixture 134v/2if, plan ordenado, verificados omitidos, in_flight primero, regen STATE OK, real 4603 asignados, 0 sin_asignar post-B0.2)"
