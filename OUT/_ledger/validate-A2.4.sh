#!/usr/bin/env bash
# validate-A2.4.sh — Prueba de la Fase A2.4 (extract_blocs.py + blocs.json).
# Salida: 0 si OK, 1 si algún check falla.
#
# Criterios del ROADMAP.md A2.4:
#   1. blocs.json existe, JSON válido, schema_version=1.0.
#   2. DocumentBloc, ShareBloc presentes con sus eventos.
#   3. BLoCs de `plugins/database/application` (≥ 5) presentes.
#   4. Conteos internos coherentes.
set -u
fail() { echo "FAIL: $1" >&2; exit 1; }
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
JSON="$ROOT/OUT/_ledger/extract/blocs.json"

[ -f "$JSON" ] || fail "no existe $JSON (ejecuta primero SKILL/scripts/extract_blocs.py)"

# Check 1: JSON válido
jq empty "$JSON" 2>/dev/null || fail "JSON inválido en $JSON"

# Check 2: schema_version
SCHEMA=$(jq -r '.schema_version // ""' "$JSON")
[ "$SCHEMA" = "1.0" ] || fail "schema_version='$SCHEMA' (esperado '1.0')"

# Check 3: tiene blocs no vacío
BLOCS_COUNT=$(jq -r '.blocs | length' "$JSON")
[ "$BLOCS_COUNT" -gt 0 ] || fail "no hay blocs en $JSON"

# Check 4 (test ROADMAP A2.4): DocumentBloc presente con eventos
DOC=$(jq -e '.blocs[] | select(.name == "DocumentBloc")' "$JSON" 2>/dev/null) \
  || fail "no se encontró DocumentBloc en blocs[]"
DOC_ETYPE=$(echo "$DOC" | jq -r '.event_type')
DOC_STYPE=$(echo "$DOC" | jq -r '.state_type')
DOC_EVENTS=$(echo "$DOC" | jq -r '.events | length')
[ "$DOC_ETYPE" = "DocumentEvent" ] || fail "DocumentBloc.event_type='$DOC_ETYPE' (esperado DocumentEvent)"
[ "$DOC_STYPE" = "DocumentState" ] || fail "DocumentBloc.state_type='$DOC_STYPE' (esperado DocumentState)"
[ "$DOC_EVENTS" -ge 5 ] || fail "DocumentBloc.events=$DOC_EVENTS (esperado >= 5)"

# Check 5 (test ROADMAP A2.4): ShareBloc presente con eventos
SHARE=$(jq -e '.blocs[] | select(.name == "ShareBloc")' "$JSON" 2>/dev/null) \
  || fail "no se encontró ShareBloc en blocs[]"
SHARE_ETYPE=$(echo "$SHARE" | jq -r '.event_type')
SHARE_STYPE=$(echo "$SHARE" | jq -r '.state_type')
SHARE_EVENTS=$(echo "$SHARE" | jq -r '.events | length')
[ "$SHARE_ETYPE" = "ShareEvent" ] || fail "ShareBloc.event_type='$SHARE_ETYPE' (esperado ShareEvent)"
[ "$SHARE_STYPE" = "ShareState" ] || fail "ShareBloc.state_type='$SHARE_STYPE' (esperado ShareState)"
[ "$SHARE_EVENTS" -ge 4 ] || fail "ShareBloc.events=$SHARE_EVENTS (esperado >= 4)"

# Check 6 (test ROADMAP A2.4): BLoCs de plugins/database/application (umbral >= 5)
DBAPP_COUNT=$(python3 - "$JSON" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
n = sum(1 for b in d["blocs"] if "/plugins/database/application/" in b["file"])
print(n)
PY
)
[ "$DBAPP_COUNT" -ge 5 ] || fail "blocs en plugins/database/application: $DBAPP_COUNT (esperado >= 5)"

# Check 7: cada Bloc con event_type debe tener ≥1 evento (o warning explícito)
BAD=$(python3 - "$JSON" <<'PY'
import json, sys
d = json.load(open(sys.argv[1], encoding="utf-8"))
bad = 0
for b in d["blocs"]:
    if b["kind"] != "Bloc":
        continue
    if b["event_type"] and not b["events"]:
        bad += 1
print(bad)
PY
)
[ "$BAD" = "0" ] || fail "$BAD Blocs con event_type declarado pero events[] vacío"

# Check 8: summary coherente
SUM_BL=$(jq -r '.summary.total_blocs' "$JSON")
SUM_CU=$(jq -r '.summary.total_cubits' "$JSON")
SUM_TOT=$((SUM_BL + SUM_CU))
ACT_TOT=$BLOCS_COUNT
ACT_BL=$(jq -r '[.blocs[] | select(.kind=="Bloc")]  | length' "$JSON")
ACT_CU=$(jq -r '[.blocs[] | select(.kind=="Cubit")] | length' "$JSON")
[ "$ACT_TOT" = "$SUM_TOT" ] || fail "summary.total_blocs+cubits=$SUM_TOT ≠ len(blocs)=$ACT_TOT"
[ "$ACT_BL"  = "$SUM_BL"  ] || fail "summary.total_blocs=$SUM_BL ≠ real Bloc=$ACT_BL"
[ "$ACT_CU"  = "$SUM_CU"  ] || fail "summary.total_cubits=$SUM_CU ≠ real Cubit=$ACT_CU"

# Resumen
echo "OK: A2.4 (JSON valido, $ACT_TOT blocs ($ACT_BL Bloc + $ACT_CU Cubit), DocumentBloc OK con $DOC_EVENTS eventos, ShareBloc OK con $SHARE_EVENTS eventos, $DBAPP_COUNT blocs en plugins/database/application)"
exit 0
