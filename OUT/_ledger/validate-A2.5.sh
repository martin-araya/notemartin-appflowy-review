#!/usr/bin/env bash
# validate-A2.5.sh — Prueba de la Fase A2.5 (extract_deps.py + deps.json).
# Salida: 0 si OK, 1 si algún check falla.
#
# Criterios del ROADMAP.md A2.5:
#   1. deps.json existe, JSON válido, schema_version=1.0.
#   2. El grafo Rust muestra `flowy-core` dependiendo de los 8 crates
#      `flowy-*` de feature (user, folder, document, database2, storage,
#      ai, search, date).
#   3. `dart-ffi` depende de `flowy-core`.
#   4. El grafo Dart muestra `appflowy` con 7 internal_path packages.
#   5. Conteos internos coherentes.
set -u
fail() { echo "FAIL: $1" >&2; exit 1; }
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
JSON="$ROOT/OUT/_ledger/extract/deps.json"

[ -f "$JSON" ] || fail "no existe $JSON (ejecuta primero SKILL/scripts/extract_deps.py)"

# Check 1: JSON válido
jq empty "$JSON" 2>/dev/null || fail "JSON inválido en $JSON"

# Check 2: schema_version
SCHEMA=$(jq -r '.schema_version // ""' "$JSON")
[ "$SCHEMA" = "1.0" ] || fail "schema_version='$SCHEMA' (esperado '1.0')"

# Check 3: rust.crates no vacío
RC=$(jq -r '.rust.crates | length' "$JSON")
[ "$RC" -gt 0 ] || fail "no hay rust.crates en $JSON"

# Check 4 (test ROADMAP A2.5): flowy-core depende de los 8 flowy-* de feature
FLOWY_FEATURES=(flowy-user flowy-folder flowy-document flowy-database2 flowy-storage flowy-ai flowy-search flowy-date)
MISSING=$(python3 - "$JSON" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
fc = next((c for c in d["rust"]["crates"] if c["name"] == "flowy-core"), None)
if fc is None:
    print("NO_FLOWY_CORE")
    sys.exit()
features = ["flowy-user","flowy-folder","flowy-document","flowy-database2","flowy-storage","flowy-ai","flowy-search","flowy-date"]
missing = [f for f in features if f not in fc["internal_dependencies"]]
print(",".join(missing) if missing else "")
PY
)
if [ "$MISSING" = "NO_FLOWY_CORE" ]; then
  fail "no se encontró crate flowy-core en rust.crates[]"
fi
if [ -n "$MISSING" ]; then
  fail "flowy-core no depende de: $MISSING"
fi

# Check 5 (test ROADMAP A2.5): dart-ffi depende de flowy-core
DFFI_OK=$(python3 - "$JSON" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
dffi = next((c for c in d["rust"]["crates"] if c["name"] == "dart-ffi"), None)
if dffi is None:
    print("NO_DART_FFI")
elif "flowy-core" in dffi["internal_dependencies"]:
    print("OK")
else:
    print("MISSING_FLOWY_CORE")
PY
)
case "$DFFI_OK" in
  OK) ;;
  NO_DART_FFI) fail "no se encontró crate dart-ffi en rust.crates[]" ;;
  *) fail "dart-ffi no depende de flowy-core" ;;
esac

# Check 6: appflowy con 7 internal_path packages
APP_INT=$(python3 - "$JSON" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
app = d["dart"]["packages"][0]
internal = [x for x in app["internal_dependencies"] if x.get("kind") == "internal_path"]
print(len(internal))
PY
)
[ "$APP_INT" = "7" ] || fail "appflowy internal_path packages: $APP_INT (esperado 7)"

# Check 7: Mermaid Rust no vacío y contiene flowy-core como origen
MR=$(jq -r '.rust.mermaid' "$JSON")
[ -n "$MR" ] || fail "rust.mermaid vacío"
echo "$MR" | grep -q "flowy-core -->" || fail "rust.mermaid no contiene aristas desde flowy-core"

# Check 8: Mermaid Dart no vacío y contiene appflowy --> appflowy_backend
MD=$(jq -r '.dart.mermaid' "$JSON")
[ -n "$MD" ] || fail "dart.mermaid vacío"
echo "$MD" | grep -q "appflowy --> appflowy_backend" || fail "dart.mermaid no contiene appflowy --> appflowy_backend"

# Check 9: summary coherente
SR_TOT=$(jq -r '.rust.summary.total_crates' "$JSON")
SR_EDG=$(jq -r '.rust.summary.total_internal_edges' "$JSON")
SD_TOT=$(jq -r '.dart.summary.total_packages' "$JSON")
SD_INT=$(jq -r '.dart.summary.total_internal_packages' "$JSON")
SD_EDG=$(jq -r '.dart.summary.total_internal_edges' "$JSON")
ACT_RC=$RC
[ "$SR_TOT" = "$ACT_RC" ] || fail "rust.summary.total_crates=$SR_TOT ≠ real=$ACT_RC"
ACT_DP=$(jq -r '.dart.packages | length' "$JSON")
ACT_IP=$(jq -r '.dart.internal_packages | length' "$JSON")
ACT_DE=$(jq -r '[.dart.packages[].internal_dependencies | length] | add' "$JSON" 2>/dev/null || echo 0)
[ "$SD_TOT" = "$((ACT_DP + ACT_IP))" ] || fail "dart.summary.total_packages=$SD_TOT ≠ app(1)+internal($ACT_IP)"
[ "$SD_INT" = "$ACT_IP" ] || fail "dart.summary.total_internal_packages=$SD_INT ≠ real=$ACT_IP"

# Resumen
N_RUST_INT=$(jq -r '[.rust.crates[].internal_dependencies | length] | add' "$JSON")
N_DART_INT=$(jq -r '.dart.summary.total_internal_edges' "$JSON")
echo "OK: A2.5 (JSON valido, $RC crates Rust con $SR_EDG internal edges, flowy-core -> 8 flowy-* features OK, dart-ffi -> flowy-core OK, appflowy -> 7 internal_path packages OK, $ACT_DP+1 packages Dart con $N_DART_INT internal edges)"
exit 0
