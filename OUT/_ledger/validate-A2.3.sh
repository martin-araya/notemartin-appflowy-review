#!/usr/bin/env bash
# validate-A2.3.sh — Prueba de la Fase A2.3 (extract_notifications.py + notifications.json).
# Salida: 0 si OK, 1 si algún check falla.
#
# Criterios del ROADMAP.md A2.3:
#   1. notifications.json existe y es JSON válido con schema_version=1.0.
#   2. DocumentNotification aparece con sus 5 variantes (incl. Unknown).
#   3. Cada variante USADA (con has_dart_listener) tiene al menos un listener
#      Dart que la maneje (esto se cumple por construcción del extractor;
#      aquí se verifica que `has_dart_listener` sea coherente).
#   4. Ningún source_mismatch (parsers Dart con _source sin enum Rust).
#   5. Conteos internos coherentes.
set -u
fail() { echo "FAIL: $1" >&2; exit 1; }
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
JSON="$ROOT/OUT/_ledger/extract/notifications.json"

[ -f "$JSON" ] || fail "no existe $JSON (ejecuta primero SKILL/scripts/extract_notifications.py)"

# Check 1: JSON válido
jq empty "$JSON" 2>/dev/null || fail "JSON inválido en $JSON"

# Check 2: schema_version
SCHEMA=$(jq -r '.schema_version // ""' "$JSON")
[ "$SCHEMA" = "1.0" ] || fail "schema_version='$SCHEMA' (esperado '1.0')"

# Check 3: tiene rust_notifications no vacío
NOTIF_COUNT=$(jq -r '.rust_notifications | length' "$JSON")
[ "$NOTIF_COUNT" -gt 0 ] || fail "no hay rust_notifications en $JSON"

# Check 4 (test ROADMAP A2.3): DocumentNotification presente con 5 variantes (incl. Unknown)
DOC=$(jq -e '.rust_notifications[] | select(.name == "DocumentNotification")' "$JSON" 2>/dev/null) \
  || fail "no se encontró DocumentNotification en rust_notifications"
VARIANT_COUNT=$(echo "$DOC" | jq -r '.variants | length')
[ "$VARIANT_COUNT" -eq 5 ] \
  || fail "DocumentNotification: $VARIANT_COUNT variantes (esperado 5: Unknown + 4 DidXxx)"
HAS_UNKNOWN=$(echo "$DOC" | jq -e '.variants[] | select(.name == "Unknown")' >/dev/null 2>&1 && echo y || echo n)
[ "$HAS_UNKNOWN" = "y" ] || fail "DocumentNotification: falta variante Unknown"

# Check 5: variantes usadas (con has_dart_listener=true) tienen listener
USED_NO_LISTENER=$(python3 - "$JSON" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
bad = 0
for enum in d["rust_notifications"]:
    for vname, u in enum["variant_usage"].items():
        if u.get("has_dart_listener"):
            # Debe aparecer en al menos un listener con este enum + variant
            found = False
            for l in d["dart_listeners"]:
                for h in l.get("handled_variants", []):
                    if h.get("enum") == enum["name"] and h.get("variant") == vname:
                        found = True
                        break
                if found: break
            if not found:
                bad += 1
print(bad)
PY
)
[ "$USED_NO_LISTENER" = "0" ] || fail "$USED_NO_LISTENER variantes marcadas con has_dart_listener pero sin listener real"

# Check 6: source_mismatches == 0
MISMATCHES=$(jq -r '.summary.rust_source_mismatches' "$JSON")
[ "$MISMATCHES" = "0" ] || fail "rust_source_mismatches=$MISMATCHES (esperado 0)"

# Check 7: summary coherente
SUM_NOTIF=$(jq -r '.summary.total_rust_notifications' "$JSON")
SUM_PARSERS=$(jq -r '.summary.total_dart_parsers' "$JSON")
SUM_LISTENERS=$(jq -r '.summary.total_dart_listeners' "$JSON")
ACT_NOTIF=$(jq -r '.rust_notifications | length' "$JSON")
ACT_PARSERS=$(jq -r '.dart_parsers | length' "$JSON")
ACT_LISTENERS=$(jq -r '.dart_listeners | length' "$JSON")
[ "$SUM_NOTIF" = "$ACT_NOTIF" ] || fail "summary.total_rust_notifications=$SUM_NOTIF ≠ real=$ACT_NOTIF"
[ "$SUM_PARSERS" = "$ACT_PARSERS" ] || fail "summary.total_dart_parsers=$SUM_PARSERS ≠ real=$ACT_PARSERS"
[ "$SUM_LISTENERS" = "$ACT_LISTENERS" ] || fail "summary.total_dart_listeners=$SUM_LISTENERS ≠ real=$ACT_LISTENERS"

# Resumen
DOC_USED=$(echo "$DOC" | jq '[.variant_usage | to_entries[] | select(.value.has_dart_listener)] | length')
echo "OK: A2.3 (JSON valido, $ACT_NOTIF rust_notifications, $ACT_PARSERS dart_parsers, $ACT_LISTENERS dart_listeners, DocumentNotification OK con 5 variantes y $DOC_USED con listener Dart, 0 source_mismatches)"
exit 0
