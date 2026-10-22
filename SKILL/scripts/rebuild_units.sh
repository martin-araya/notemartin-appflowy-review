#!/usr/bin/env bash
# rebuild_units.sh — pipeline canonico de reconstruccion de
# OUT/_ledger/units/ tras cambiar SUBDIVISIONS en build_units.py.
#
# Los pasos NO son intercambiables: cada uno arregla una consecuencia del
# anterior.
#
#   1. build_units.py --prune   genera las unidades de las features con filas
#                               pendientes y aparta a .stale-bak/ las
#                               obsoletas de esas mismas features.
#   2. sync_units_from_docs.py  fija `archivos` de cada unidad: para las que
#                               tienen documento, manda el frontmatter
#                               `archivos_cubiertos` (fuente de verdad de una
#                               feature cerrada); para las que no, lo que
#                               acaba de generar build_units. Resuelve los
#                               conflictos de propiedad a favor de la unidad
#                               con documento y re-ancla las filas huerfanas.
#   3. build_units.py --index-only  reconstruye _index.json desde el disco,
#                               incluyendo las features cerradas que no se
#                               regeneran.
#
# `align_units.py` y `restore_unit_files.py` quedan disponibles para
# reparaciones puntuales, pero NO forman parte del pipeline: el primero
# vacia unidades cerradas cuando se ejecuta su heuristica por defecto.
#
# Uso:
#   rebuild_units.sh [--dry-run]

set -u
set -o pipefail

ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
DRY=""
[ "${1:-}" = "--dry-run" ] && DRY="--dry-run"

echo "== 1/4 build_units.py --prune"
python3 "$ROOT/SKILL/scripts/build_units.py" --prune --no-color || exit 1

echo "== 2/3 sync_units_from_docs.py (documento = fuente de verdad)"
python3 "$ROOT/SKILL/scripts/sync_units_from_docs.py" $DRY | head -40 || exit 1

echo "== 3/3 build_units.py --index-only"
python3 "$ROOT/SKILL/scripts/build_units.py" --index-only --no-color || exit 1

echo "== validate_units.py"
python3 "$ROOT/SKILL/scripts/validate_units.py" --no-color | tail -3