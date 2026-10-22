#!/usr/bin/env bash
# validate-A4.1.sh — Prueba de la Fase A4.1 (assign_ledger.py).
# Salida: 0 si OK, 1 si algun check falla (imprime el check fallido).
# Misma convencion que validate-A1.3.sh / validate-A3.4.sh.
set -u
fail() { echo "FAIL: $1" >&2; exit 1; }
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
SCRIPT="$ROOT/SKILL/scripts/assign_ledger.py"
FIX="$ROOT/OUT/_ledger/pruebas/A4.1/fixtures"

[ -f "$SCRIPT" ] || fail "no existe $SCRIPT"
[ -x "$SCRIPT" ] || fail "$SCRIPT no es ejecutable"
[ -d "$FIX" ]    || fail "no existe $FIX (debe contener toy_inventario.json y friends)"

# Check 1: --help funciona
python3 "$SCRIPT" --help >/dev/null 2>&1 \
  || fail "--help fallo"
python3 "$SCRIPT" --help 2>&1 | grep -q "min-coverage" \
  || fail "--help no documenta --min-coverage"

# Check 2: dry-run no toca cobertura.csv real
LEDGER="$ROOT/OUT/_ledger/cobertura.csv"
M1=$(stat -f %m "$LEDGER" 2>/dev/null || stat -c %Y "$LEDGER")
python3 "$SCRIPT" --dry-run --no-color >/dev/null 2>&1 \
  || fail "dry-run fallo"
M2=$(stat -f %m "$LEDGER" 2>/dev/null || stat -c %Y "$LEDGER")
[ "$M1" = "$M2" ] || fail "dry-run modifico mtime de $LEDGER ($M1 -> $M2)"

# Check 3: toy -> diff contra expected_ledger.csv
WORK=$(mktemp -d)
cp "$FIX/toy_ledger.csv" "$WORK/ledger.csv"
python3 "$SCRIPT" \
  --inventario "$FIX/toy_inventario.json" \
  --ledger "$WORK/ledger.csv" \
  --sin-asignar "$WORK/sin_asignar.md" \
  --sin-asignar-json "$WORK/sin_asignar.json" \
  --no-color >/dev/null 2>&1 \
  || fail "asignacion toy fallo"
diff -q "$FIX/expected_ledger.csv" "$WORK/ledger.csv" >/dev/null \
  || { diff "$FIX/expected_ledger.csv" "$WORK/ledger.csv" | head -20; fail "toy ledger != expected_ledger"; }
# Verificar que el archivo unassigned coincide
python3 - "$WORK/sin_asignar.json" "$FIX/toy_inventario.json" <<'PY' || fail "sin_asignar.json no contiene el archivo esperado"
import json, sys
un = json.load(open(sys.argv[1]))
inv = json.load(open(sys.argv[2]))
assert len(un) == 1, f"esperaba 1 sin asignar, hay {len(un)}"
assert un[0]["ruta"] == "appflowy/sin_match/archivo_aislado.dart", un[0]
print(f"  sin_asignar.json OK: 1 fila -> {un[0]['ruta']}")
PY

# Check 4: idempotencia — re-ejecutar no cambia el CSV
SHA1=$(shasum "$WORK/ledger.csv" 2>/dev/null | awk '{print $1}' || sha1sum "$WORK/ledger.csv" | awk '{print $1}')
python3 "$SCRIPT" \
  --inventario "$FIX/toy_inventario.json" \
  --ledger "$WORK/ledger.csv" \
  --sin-asignar "$WORK/sin_asignar.md" \
  --sin-asignar-json "$WORK/sin_asignar.json" \
  --no-color >/dev/null 2>&1 \
  || fail "segunda corrida fallo"
SHA2=$(shasum "$WORK/ledger.csv" 2>/dev/null | awk '{print $1}' || sha1sum "$WORK/ledger.csv" | awk '{print $1}')
[ "$SHA1" = "$SHA2" ] || fail "idempotencia rota: $SHA1 != $SHA2"

# Check 5: --min-coverage 100 sobre el real debe fallar
if python3 "$SCRIPT" --dry-run --min-coverage 100 --no-color >/dev/null 2>&1; then
  fail "--min-coverage 100 deberia fallar en real (hay ~7% unassigned)"
fi

# Check 6: inventario inexistente -> exit 2
if python3 "$SCRIPT" --inventario /no/existe.json --dry-run --no-color >/dev/null 2>&1; then
  fail "inventario inexistente deberia fallar con exit 2"
fi
python3 "$SCRIPT" --inventario /no/existe.json --dry-run --no-color 2>/dev/null
EC=$?
[ "$EC" = "2" ] || fail "inventario inexistente: exit code = $EC (esperaba 2)"

# Check 7: preservacion de estado 'verificado'
cp "$FIX/verified_ledger.csv" "$WORK/vledger.csv"
python3 "$SCRIPT" \
  --inventario "$FIX/toy_inventario.json" \
  --ledger "$WORK/vledger.csv" \
  --sin-asignar "$WORK/vsin.md" \
  --sin-asignar-json "$WORK/vsin.json" \
  --no-color >/dev/null 2>&1 \
  || fail "corrida verified fallo"
diff -q "$FIX/expected_verified_ledger.csv" "$WORK/vledger.csv" >/dev/null \
  || { diff "$FIX/expected_verified_ledger.csv" "$WORK/vledger.csv" | head; fail "verified_ledger no preservo estado"; }

# Check 8: el run real genero sin_asignar.md y este bajo el umbral real
[ -f "$ROOT/OUT/_ledger/sin_asignar.md" ] || fail "no se genero OUT/_ledger/sin_asignar.md"
[ -f "$ROOT/OUT/_ledger/sin_asignar.json" ] || fail "no se genero OUT/_ledger/sin_asignar.json"
[ -f "$ROOT/OUT/_ledger/cobertura.csv" ] || fail "no existe OUT/_ledger/cobertura.csv"
# Cobertura real >= 90%
COV=$(python3 - "$ROOT/OUT/_ledger/cobertura.csv" <<'PY'
import csv, sys
total=asig=0
with open(sys.argv[1], encoding='utf-8', newline='') as f:
    r = csv.DictReader(f)
    for row in r:
        total += 1
        if row['feature_ids'].strip():
            asig += 1
print(f"{asig/total*100:.2f}")
PY
)
python3 -c "v=$COV; assert v >= 90, f'cobertura real {v} < 90%'" \
  || fail "cobertura real $COV% < 90%"

rm -rf "$WORK"

echo "OK: A4.1 (assign_ledger.py funciona: toy 100%, real ${COV}% >= 90%, --help, --dry-run no escribe, idempotente, --min-coverage falla con <umbral, inventario inexistente -> exit 2, verificado preservado, sin_asignar.md/json generados)"
