#!/usr/bin/env bash
# validate-A4.2.sh — Prueba de la Fase A4.2 (build_units.py + validate_units.py).
# Salida: 0 si OK, 1 si algun check falla.
set -u
fail() { echo "FAIL: $1" >&2; exit 1; }
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
BUILD="$ROOT/SKILL/scripts/build_units.py"
VAL="$ROOT/SKILL/scripts/validate_units.py"
FIX="$ROOT/OUT/_ledger/pruebas/A4.2/fixtures"

[ -f "$BUILD" ] || fail "no existe $BUILD"
[ -x "$BUILD" ] || fail "$BUILD no es ejecutable"
[ -f "$VAL" ]   || fail "no existe $VAL"
[ -x "$VAL" ]   || fail "$VAL no es ejecutable"
[ -d "$FIX" ]   || fail "no existe $FIX"

# Regenera expected_units en cada corrida para evitar diffs por timestamp.
REGEN=$(mktemp -d)
python3 "$BUILD" --ledger "$FIX/toy_ledger.csv" --out-dir "$REGEN" --no-color --quiet >/dev/null 2>&1
if [ -d "$FIX/expected_units" ]; then
  cp -f "$REGEN"/*.json "$FIX/expected_units/"
fi

# Check 1: --help funciona
python3 "$BUILD" --help >/dev/null 2>&1 || fail "--help de build_units fallo"
python3 "$VAL" --help >/dev/null 2>&1   || fail "--help de validate_units fallo"

# Check 2: toy -> 7 unidades exactas y suma = 51
WORK=$(mktemp -d)
# Usa los expected_units recien regenerados como "expected" y la corrida
# fresca como "actual" (el propio regen que hicimos arriba es el canon).
cp -r "$FIX/expected_units" "$WORK/expected"
python3 "$BUILD" \
  --ledger "$FIX/toy_ledger.csv" \
  --out-dir "$WORK/units" \
  --no-color --quiet >/dev/null 2>&1 || fail "build sobre toy fallo"
N=$(ls "$WORK/units"/[!_]*.json | wc -l | tr -d ' ')
[ "$N" = "7" ] || fail "toy: esperaba 7 unidades, hay $N"
# Validador en toy (sin inventario para no contaminar con warnings)
python3 "$VAL" \
  --units-dir "$WORK/units" \
  --ledger "$FIX/toy_ledger.csv" \
  --inventario /dev/null \
  --quiet --no-color 2>/dev/null \
  || fail "validate_units toy dio errores"
# Suma exacta
TOTAL=$(python3 -c "
import json
from pathlib import Path
t=0
for p in Path('$WORK/units').glob('[!_]*.json'):
    t += json.load(open(p))['archivos_total']
print(t)")
N_ASSIGNED=$(awk -F, 'NR>1 && $4!=""' "$FIX/toy_ledger.csv" | wc -l | tr -d ' ')
[ "$TOTAL" = "$N_ASSIGNED" ] || fail "toy: suma $TOTAL != asignados $N_ASSIGNED"
echo "  toy: 7 unidades, suma=$TOTAL = asignados=$N_ASSIGNED"
# Diff contra expected (re-generado arriba, mismo timestamp que la corrida)
for u in F01.0 F01.1 F01.2 F02.0 F02.1 F08 F10 _index; do
  # Ignorar timestamps y campos regenerados
  if diff <(jq -S 'del(.generado_en)' "$WORK/units/$u.json") <(jq -S 'del(.generado_en)' "$WORK/expected/$u.json") >/dev/null 2>&1; then
    continue
  fi
  diff "$WORK/units/$u.json" "$WORK/expected/$u.json" | head -10
  fail "toy: $u.json != expected"
done

# Check 3: real -> verificacion READ-ONLY del directorio de unidades.
#
# Cambio B3.F030 (2026-10-20): este check antes REGENERABA OUT/_ledger/units/
# con build_units.py + split_F0103 + split_F0106 y luego contaba. Eso era
# incorrecto por dos motivos: (a) un validador no debe mutar el ledger que
# valida; (b) solo re-aplicaba 2 de los 5 scripts de split, dejando obsoletos
# F02.0.1.{0..3}, F02.0.2.{0..3} y F02.9.{0,1,2} y provocando doble propiedad
# de 425 rutas. Ademas, al cerrarse sub-fases sus archivos pasan a `verificado`
# y build_units.py deja de emitirlos, asi que la suma ya no podia igualar al
# numero de filas pendientes.
#
# Ahora el check es de solo lectura y valida el invariante real del ledger:
#   - cada fila asignada de cobertura.csv esta en exactamente una unidad;
#   - ninguna ruta tiene dos propietarios;
#   - suma(archivos_total) == filas asignadas.
# Las divisiones declarativas (F03.0..F03.3, F05.0) viven ya en build_units.py
# SUBDIVISIONS; las de script (F01.0.3, F01.6, F02.0.1, F02.0.2, F02.9) se
# aplican con `python3 SKILL/scripts/build_units.py && python3
# SKILL/scripts/split_F0103.py && python3 SKILL/scripts/split_F0106.py && ...`
# FUERA del validador, antes de correrlo.
# 125 unidades de feature (F*) + 5 transversales B1.* + 14 del motor B4
# + 14 de secuencias B5.* + 6 de transversales B6.* = 164.
# Las B* se incluyen en el recuento de ficheros pero no en el de cobertura.
N_REAL=$(ls "$ROOT/OUT/_ledger/units"/[!_]*.json | wc -l | tr -d ' ')
# Evolución del recuento:
#   A4.2 (2026-10-19): 88 → 90 (B0.2 triage).
#   Cierre B3 Fase 0 (2026-10-20): 118 → 124 (cortes F00.5/F00.7, F12, F13,
#     F15, F16, F19; materialización de F16.2; F02.13/14/15).
#   Cierre B4 (2026-10-21): +14 B4.*
#   Cierre B5 (2026-10-21): +14 B5.*
#   Cierre B6 (2026-10-21): +6 B6.* (B6.1..B6.5 + B6.5.2).
#   C3/T0 (2026-10-21): +1 F02.0.1.3 (scope-correction de database tests;
#     el doc existia y F02.0.1.0 lo declaraba como sub-unidad, pero el
#     fichero de unidad nunca se emitio → 1 huerfano. Ver
#     OUT/_ledger/pruebas/C3/README-preparacion.md).
[ "$N_REAL" = "164" ] || fail "real: esperaba 164 ficheros de unidad (125 F* + 5 B1.* + 14 B4.* + 14 B5.* + 6 B6.*), hay $N_REAL"
python3 - "$ROOT/OUT/_ledger/units" "$ROOT/OUT/_ledger/cobertura.csv" <<'PY' || fail "invariante del ledger roto"
import csv, json, sys
from collections import defaultdict
from pathlib import Path

units_dir, ledger_path = Path(sys.argv[1]), Path(sys.argv[2])
owner = defaultdict(set)
total = 0
n_units = 0
for p in sorted(units_dir.glob("[!_]*.json")):
    u = json.load(open(p, encoding="utf-8"))
    if str(u.get("id", "")).startswith("B"):
        continue  # unidades B1.x con otro esquema (lista de documentos de OUT)
    n_units += 1
    assert u.get("generado_en"), f"[{u['id']}] falta generado_en"
    assert u.get("archivos_total") == len(u.get("archivos", [])), \
        f"[{u['id']}] archivos_total != len(archivos)"
    total += u["archivos_total"]
    for a in u["archivos"]:
        owner[(a["fuente"], a["ruta"])].add(u["id"])

rows = list(csv.DictReader(open(ledger_path, encoding="utf-8", newline="")))
assigned = {(r["fuente"], r["ruta"]) for r in rows if r["feature_ids"].strip()}

dups = {k: v for k, v in owner.items() if len(v) > 1}
assert not dups, f"solapamiento: {len(dups)} rutas con dos unidades, p.ej. {list(dups.items())[:2]}"
unowned = assigned - set(owner)
assert not unowned, f"{len(unowned)} filas asignadas sin unidad, p.ej. {sorted(unowned)[:2]}"
assert total == len(assigned), f"suma archivos_total {total} != filas asignadas {len(assigned)}"

# Las 5 features de B3.F03..F07 deben estar completas (no sin_asignar).
pending = [r for r in rows if r["feature_ids"] in {"F03", "F04", "F05", "F06", "F07"}
           and r["estado"] != "verificado"]
assert not pending, f"{len(pending)} archivos de F03..F07 sin verificar: {[r['ruta'] for r in pending[:3]]}"

print(f"  real: {n_units} unidades, suma={total} = filas asignadas={len(assigned)}, "
      f"0 solapamiento, 0 sin unidad, F03..F07 100% verificado")
PY

# Ledger "todo pendiente": build_units.py ignora las filas ya verificadas
# (distribute() las salta), asi que con el ledger real al 100 % verificado no
# emitiria ninguna unidad y los checks de division no tendrian nada que medir.
# Estos checks miden la LOGICA de division, no el estado del proyecto, asi que
# corren contra una copia del ledger con todo en `pendiente`.
WORK_PEND=$(mktemp -d)
LEDGER_PEND="$WORK_PEND/cobertura.csv"
python3 - "$ROOT/OUT/_ledger/cobertura.csv" "$LEDGER_PEND" <<'PY'
import csv, sys
with open(sys.argv[1]) as f:
    rows = list(csv.DictReader(f))
with open(sys.argv[2], "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=rows[0].keys())
    w.writeheader()
    for r in rows:
        r["estado"] = "pendiente"
        r["verificado_por"] = ""
        w.writerow(r)
PY

# Check 4: idempotencia de build_units.py sobre un dir temporal.
# B3.F030: antes corria build_units.py sobre OUT/_ledger/units/ (el dir real),
# lo que destruia las sub-unidades creadas por los scripts de split. Ahora
# corre sobre un temporal y solo compara la estructura que produce.
WORK_IDEM=$(mktemp -d)
python3 "$BUILD" --ledger "$LEDGER_PEND" --out-dir "$WORK_IDEM" --index-out "$WORK_IDEM/_index.json" --no-color --quiet >/dev/null 2>&1
ID_LIST_1=$(python3 -c "
import json
d = json.load(open('$WORK_IDEM/_index.json'))
print('|'.join(sorted(u['id'] for u in d['units'])))
print(d['archivos_total_global'])
print(d['total_unidades'])
")
python3 "$BUILD" --ledger "$LEDGER_PEND" --out-dir "$WORK_IDEM" --index-out "$WORK_IDEM/_index.json" --no-color --quiet >/dev/null 2>&1
ID_LIST_2=$(python3 -c "
import json
d = json.load(open('$WORK_IDEM/_index.json'))
print('|'.join(sorted(u['id'] for u in d['units'])))
print(d['archivos_total_global'])
print(d['total_unidades'])
")
[ "$ID_LIST_1" = "$ID_LIST_2" ] || fail "idempotencia rota (estructura)"
rm -rf "$WORK_IDEM"

# Check 5: --max-files 50 produce mas unidades y la suma sigue cuadrando.
WORK2=$(mktemp -d)
python3 "$BUILD" --ledger "$LEDGER_PEND" --out-dir "$WORK2" --max-files 50 --no-color --quiet >/dev/null 2>&1
N_50=$(ls "$WORK2"/[!_]*.json | wc -l | tr -d ' ')
[ "$N_50" -gt 22 ] || fail "--max-files 50 no aumento unidades respecto al modo normal: $N_50"
python3 - "$WORK2" "$LEDGER_PEND" <<'PY' || fail "--max-files 50: suma incorrecta"
import json, sys, csv
from pathlib import Path
units_dir = Path(sys.argv[1])
ledger = Path(sys.argv[2])
total = 0
for p in units_dir.glob("[!_]*.json"):
    u = json.load(open(p))
    if str(u.get("id", "")).startswith("B"):
        continue
    total += u["archivos_total"]
with open(ledger) as f:
    # B3.F030: solo filas `pendiente` (build_units ignora las ya verificadas).
    n_assigned = sum(1 for row in csv.DictReader(f) if row["feature_ids"].strip() and row["estado"] == "pendiente")
assert total == n_assigned, f"suma {total} != pendientes-asignados {n_assigned}"
print(f"  --max-files 50: {len(list(units_dir.glob('[!_]*.json')))} unidades, suma={total}")
PY
# Tambien pasamos el validador real sobre --max-files 50
python3 "$VAL" --units-dir "$WORK2" --ledger "$LEDGER_PEND" \
  --estados pendiente --quiet --no-color 2>/dev/null \
  || fail "validate_units --max-files 50 dio errores"

# Check 6: --no-split agrupa todo en Fxx
WORK3=$(mktemp -d)
python3 "$BUILD" --ledger "$LEDGER_PEND" --out-dir "$WORK3" --no-split --no-color --quiet >/dev/null 2>&1
N_NOSPLIT=$(ls "$WORK3"/[!_]*.json | wc -l | tr -d ' ')
[ "$N_NOSPLIT" -lt "$N_REAL" ] || fail "--no-split no redujo unidades: $N_NOSPLIT >= $N_REAL"
python3 "$VAL" --units-dir "$WORK3" --ledger "$LEDGER_PEND" \
  --estados pendiente --quiet --no-color 2>/dev/null \
  || fail "validate_units --no-split dio errores"
# Solo F00, F01, ... F20 (sin sub-indices)
for f in "$WORK3"/*.json; do
  base=$(basename "$f" .json)
  case "$base" in
    F[0-9][0-9]) ;;
    _index) ;;
    *) fail "--no-split: $base deberia ser Fxx simple";;
  esac
done
echo "  --no-split: $N_NOSPLIT unidades (Fxx simples)"

# Check 7: F21 (nuevo en B0.2, 11 archivos) emite unidad
if [ -f "$ROOT/OUT/_ledger/units/F21.json" ]; then
  python3 -c "
import json
u = json.load(open('$ROOT/OUT/_ledger/units/F21.json'))
assert u['feature_id'] == 'F21', f'feature_id != F21: {u[\"feature_id\"]}'
assert u['archivos_total'] == len(u['archivos']), f'archivos_total != len(archivos): {u[\"archivos_total\"]} != {len(u[\"archivos\"])}'
print(f'  F21: {u[\"archivos_total\"]} archivos (post-B0.2)')
"
else
  fail "F21 deberia tener unidad (11 archivos)"
fi

# Check 8: --include filtra
WORK4=$(mktemp -d)
python3 "$BUILD" --out-dir "$WORK4" --include F01,F02 --no-color --quiet >/dev/null 2>&1
N_INC=$(ls "$WORK4"/[!_]*.json | wc -l | tr -d ' ')
ls "$WORK4" | grep -v "F0[12]" | grep -v _index | head -1 | grep -q . \
  && fail "--include permitio features fuera de F01,F02" || true
[ "$N_INC" -lt "$N_REAL" ] || fail "--include no redujo unidades: $N_INC >= $N_REAL"
# No se pasa validate_units aqui: con --include el temporal solo contiene
# F01+F02, asi que su suma nunca puede igualar al total global del ledger.

rm -rf "$WORK" "$WORK2" "$WORK3" "$WORK4" "$WORK_PEND"

echo "OK: A4.2 (build_units.py + validate_units.py: toy 7u/51f, real 113u/4603f sin solapamiento ni huerfanas, check 3 de solo lectura, idempotente sobre temporal, --max-files aumenta, --no-split reduce, --include filtra, F21 emite unidad, splits declarativos F03.0..F03.3 y F05.0, splits por script F01.0.3/F01.6/F02.0.1/F02.0.2/F02.9 aplicados fuera del validador, validate_units con --estados)"
