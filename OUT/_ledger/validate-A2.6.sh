#!/usr/bin/env bash
# validate-A2.6.sh — Prueba de la Fase A2.6 (extract_misc.py + misc.json).
# Salida: 0 si OK, 1 si algún check falla.
#
# Criterios del ROADMAP.md A2.6:
#   1. misc.json existe, JSON válido, schema_version=1.0.
#   2. Cada salida no vacía: routes, shortcuts, feature_flags, error_codes,
#      i18n_keys, startup_tasks.
#   3. El número de ErrorCode coincide con las variantes del enum (>= 100).
set -u
fail() { echo "FAIL: $1" >&2; exit 1; }
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
JSON="$ROOT/OUT/_ledger/extract/misc.json"

[ -f "$JSON" ] || fail "no existe $JSON (ejecuta primero SKILL/scripts/extract_misc.py)"

# Check 1: JSON válido
jq empty "$JSON" 2>/dev/null || fail "JSON inválido en $JSON"

# Check 2: schema_version
SCHEMA=$(jq -r '.schema_version // ""' "$JSON")
[ "$SCHEMA" = "1.0" ] || fail "schema_version='$SCHEMA' (esperado '1.0')"

# Check 3 (test ROADMAP A2.6): cada salida no vacía
N_ROUTES=$(jq -r '.routes.total // 0' "$JSON")
N_SHORTCUTS=$(jq -r '.shortcuts.total // 0' "$JSON")
N_FLAGS=$(jq -r '.feature_flags.total // 0' "$JSON")
N_ERRCODES=$(jq -r '.error_codes.total // 0' "$JSON")
N_I18N=$(jq -r '.i18n_keys.unique_keys // 0' "$JSON")
N_TASKS=$(jq -r '.startup_tasks.total // 0' "$JSON")

[ "$N_ROUTES"    -gt 0 ] || fail "routes.total = 0 (esperado > 0)"
[ "$N_SHORTCUTS" -gt 0 ] || fail "shortcuts.total = 0 (esperado > 0)"
[ "$N_FLAGS"     -gt 0 ] || fail "feature_flags.total = 0 (esperado > 0)"
[ "$N_ERRCODES"  -gt 0 ] || fail "error_codes.total = 0 (esperado > 0)"
[ "$N_I18N"      -gt 0 ] || fail "i18n_keys.unique_keys = 0 (esperado > 0)"
[ "$N_TASKS"     -gt 0 ] || fail "startup_tasks.total = 0 (esperado > 0)"

# Check 4 (test ROADMAP A2.6): ErrorCode >= 100 (umbral sano)
[ "$N_ERRCODES" -ge 100 ] || fail "error_codes.total=$N_ERRCODES (esperado >= 100)"

# Check 5: ErrorCode en repr u8 (o similar)
REPR=$(jq -r '.error_codes.repr // ""' "$JSON")
[ -n "$REPR" ] || fail "error_codes.repr vacío"

# Check 6: feature_flags.enum == "FeatureFlag"
FE_ENUM=$(jq -r '.feature_flags.enum // ""' "$JSON")
[ "$FE_ENUM" = "FeatureFlag" ] || fail "feature_flags.enum='$FE_ENUM' (esperado FeatureFlag)"

# Check 7: error_codes.enum == "ErrorCode"
EC_ENUM=$(jq -r '.error_codes.enum // ""' "$JSON")
[ "$EC_ENUM" = "ErrorCode" ] || fail "error_codes.enum='$EC_ENUM' (esperado ErrorCode)"

# Check 8: ErrorCode variants todos con index en rango u8 (0-255)
BAD_IDX=$(python3 - "$JSON" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
bad = 0
for v in d["error_codes"]["variants"]:
    idx = v.get("index")
    if idx is None or not (0 <= idx <= 255):
        bad += 1
print(bad)
PY
)
[ "$BAD_IDX" = "0" ] || fail "$BAD_IDX ErrorCode variants con index fuera de rango u8"

# Check 9: startup_tasks tiene 'PlatformErrorCatcherTask' como primera (o en posición baja)
T0=$(python3 - "$JSON" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
tasks = d["startup_tasks"]["ordered_tasks"]
for i, t in enumerate(tasks):
    if "PlatformError" in t.get("class", ""):
        print(i)
        sys.exit(0)
print("-1")
PY
)
[ "$T0" -ge 0 ] && [ "$T0" -le 3 ] || fail "PlatformErrorCatcherTask no está entre las 3 primeras tareas (idx=$T0)"

# Check 10: summary coherente
SUM_TOT=$(jq -r '.summary.total_routes' "$JSON")
SUM_SC=$(jq -r '.summary.total_shortcuts' "$JSON")
SUM_FF=$(jq -r '.summary.total_feature_flags' "$JSON")
SUM_EC=$(jq -r '.summary.total_error_codes' "$JSON")
SUM_I18N=$(jq -r '.summary.total_i18n_keys' "$JSON")
SUM_ST=$(jq -r '.summary.total_startup_tasks' "$JSON")
[ "$SUM_TOT" = "$N_ROUTES" ]    || fail "summary.total_routes=$SUM_TOT ≠ real=$N_ROUTES"
[ "$SUM_SC"  = "$N_SHORTCUTS" ] || fail "summary.total_shortcuts=$SUM_SC ≠ real=$N_SHORTCUTS"
[ "$SUM_FF"  = "$N_FLAGS" ]     || fail "summary.total_feature_flags=$SUM_FF ≠ real=$N_FLAGS"
[ "$SUM_EC"  = "$N_ERRCODES" ]  || fail "summary.total_error_codes=$SUM_EC ≠ real=$N_ERRCODES"
[ "$SUM_I18N" = "$N_I18N" ]     || fail "summary.total_i18n_keys=$SUM_I18N ≠ real=$N_I18N"
[ "$SUM_ST"  = "$N_TASKS" ]     || fail "summary.total_startup_tasks=$SUM_ST ≠ real=$N_TASKS"

# Resumen
echo "OK: A2.6 (JSON valido, routes=$N_ROUTES, shortcuts=$N_SHORTCUTS, feature_flags=$N_FLAGS, error_codes=$N_ERRCODES (repr=$REPR), i18n_keys=$N_I18N, startup_tasks=$N_TASKS, PlatformErrorCatcherTask idx=$T0)"
exit 0
