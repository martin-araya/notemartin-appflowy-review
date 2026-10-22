#!/usr/bin/env bash
# validate-A1.3.sh — Prueba de la Fase A1.3 (init_ledger.py + cobertura.csv).
# Salida: 0 si OK, 1 si algún check falla (imprime el check fallido).
set -u
fail() { echo "FAIL: $1" >&2; exit 1; }
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
CSV="$ROOT/OUT/_ledger/cobertura.csv"
INV="$ROOT/OUT/_ledger/inventario.json"
[ -f "$CSV" ] || fail "no existe $CSV (ejecuta primero SKILL/scripts/init_ledger.py)"
[ -f "$INV" ] || fail "no existe $INV (A1.2 debe estar cerrado)"

EXPECTED_HEADER="fuente,ruta,capa,feature_ids,documento,estado,verificado_por"

# Check 1: cabecera exacta
header=$(head -1 "$CSV" | tr -d '\r\n')
[ "$header" = "$EXPECTED_HEADER" \
  ] || fail "cabecera incorrecta: '$header' (esperado '$EXPECTED_HEADER')"

# Check 2: cardinalidad (filas = len(inventario.files))
inv_count=$(python3 -c "import json; print(len(json.load(open('$INV'))['files']))")
csv_count=$(($(wc -l < "$CSV") - 1))  # restar cabecera
[ "$csv_count" = "$inv_count" \
  ] || fail "filas: csv=$csv_count ≠ inventario=$inv_count"

# Check 3: todas las filas con estado='sin_asignar' y campos mutables vacíos,
#          (fuente,ruta) únicos, 3 fuentes presentes
python3 - "$CSV" <<'PY' || fail "alguna fila no cumple estado=sin_asignar o hay duplicados"
import csv, sys
bad_estado = []
bad_mutable = []
fuentes = set()
rutas_seen = set()
duplicados = 0
with open(sys.argv[1], encoding='utf-8', newline='') as f:
    r = csv.DictReader(f)
    for row in r:
        fuentes.add(row['fuente'])
        key = (row['fuente'], row['ruta'])
        if key in rutas_seen:
            duplicados += 1
        rutas_seen.add(key)
        if row['estado'] != 'sin_asignar':
            bad_estado.append(row['ruta'])
        for col in ('feature_ids', 'documento', 'verificado_por'):
            if row[col]:
                bad_mutable.append((row['ruta'], col, row[col]))
assert not bad_estado, f"{len(bad_estado)} filas con estado != sin_asignar (ej: {bad_estado[:3]})"
assert not bad_mutable, f"{len(bad_mutable)} campos mutables no vacíos (ej: {bad_mutable[:3]})"
assert not duplicados, f"{duplicados} (fuente,ruta) duplicados"
for expected in ('appflowy', 'collab', 'editor'):
    assert expected in fuentes, f"falta fuente {expected}"
PY

echo "OK: A1.3 (CSV con cabecera correcta, $csv_count filas = inventario, todas sin_asignar, cols mutables vacías, 3 fuentes)"
