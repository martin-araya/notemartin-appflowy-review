#!/usr/bin/env bash
# validate-A2.2.sh — Prueba de la Fase A2.2 (extract_protobuf.py + protobuf.json).
# Salida: 0 si OK, 1 si algún check falla.
#
# Criterios del ROADMAP.md A2.2:
#   1. protobuf.json existe y es JSON válido con schema_version=1.0.
#   2. Tiene entidades (structs y enums) extraídas.
#   3. El cruce con events.json (A2.1) resuelve todos los input/output:
#      cada uno aparece como entity o está en missing_event_pbs.
#   4. Conteos internos coherentes.
set -u
fail() { echo "FAIL: $1" >&2; exit 1; }
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
JSON="$ROOT/OUT/_ledger/extract/protobuf.json"
EVENTS="$ROOT/OUT/_ledger/extract/events.json"

[ -f "$JSON" ] || fail "no existe $JSON (ejecuta primero SKILL/scripts/extract_protobuf.py)"
[ -f "$EVENTS" ] || fail "no existe $EVENTS (A2.1 debe estar cerrado)"

# Check 1: JSON válido
jq empty "$JSON" 2>/dev/null || fail "JSON inválido en $JSON"

# Check 2: schema_version
SCHEMA=$(jq -r '.schema_version // ""' "$JSON")
[ "$SCHEMA" = "1.0" ] || fail "schema_version='$SCHEMA' (esperado '1.0')"

# Check 3: tiene entidades y no vacío
ENTITY_COUNT=$(jq -r '.entities | length' "$JSON")
[ "$ENTITY_COUNT" -gt 0 ] || fail "no hay entidades en $JSON"

# Check 4: summary coherente
SUM_TOT=$(jq -r '.summary.total_entities' "$JSON")
SUM_STR=$(jq -r '.summary.total_structs'  "$JSON")
SUM_ENUM=$(jq -r '.summary.total_enums'   "$JSON")
ACT_TOT=$ENTITY_COUNT
ACT_STR=$(jq -r '[.entities[] | select(.kind=="struct")] | length' "$JSON")
ACT_ENUM=$(jq -r '[.entities[] | select(.kind=="enum")]   | length' "$JSON")
[ "$SUM_TOT"  = "$ACT_TOT"  ] || fail "summary.total_entities=$SUM_TOT ≠ len(entities)=$ACT_TOT"
[ "$SUM_STR"  = "$ACT_STR"  ] || fail "summary.total_structs=$SUM_STR ≠ struct count=$ACT_STR"
[ "$SUM_ENUM" = "$ACT_ENUM" ] || fail "summary.total_enums=$SUM_ENUM ≠ enum count=$ACT_ENUM"
[ "$SUM_TOT"  = "$((SUM_STR + SUM_ENUM))" ] \
  || fail "summary: total($SUM_TOT) ≠ structs($SUM_STR) + enums($SUM_ENUM)"

# Check 5: cruce con events.json (TEST ROADMAP A2.2)
# Cada input/output de events.json debe estar en entity_names o en missing_event_pbs.
python3 - "$JSON" "$EVENTS" <<'PY' || fail "cruce con events.json incompleto: hay inputs/outputs sin resolver ni reportar como faltantes"
import json, sys
pb = json.load(open(sys.argv[1], encoding="utf-8"))
ev = json.load(open(sys.argv[2], encoding="utf-8"))
entity_names = {e["name"] for e in pb["entities"]}
missing_names = {m["name"] for m in pb["cross_ref"]["missing_event_pbs"]}
unresolved = []
for c in ev.get("crates", []):
    for v in c.get("variants", []):
        for kind, val in (("input", v.get("input")), ("output", v.get("output"))):
            if val and val not in entity_names and val not in missing_names:
                unresolved.append((c["crate"], v["name"], kind, val))
assert not unresolved, (
    f"{len(unresolved)} input/output no resueltos: "
    + ", ".join(f"{c}::{v}.{k}={val}" for c, v, k, val in unresolved[:10])
)
# Además, el total unique_inputs + unique_outputs de protobuf.cross_ref debe
# coincidir con lo que se deriva de events.json.
got_inputs = set(pb["cross_ref"]["unique_event_inputs"])
got_outputs = set(pb["cross_ref"]["unique_event_outputs"])
exp_inputs = {v["input"] for c in ev["crates"] for v in c["variants"] if v.get("input")}
exp_outputs = {v["output"] for c in ev["crates"] for v in c["variants"] if v.get("output")}
assert got_inputs == exp_inputs, f"unique_event_inputs mismatch: {len(got_inputs - exp_inputs)} extra, {len(exp_inputs - got_inputs)} missing"
assert got_outputs == exp_outputs, f"unique_event_outputs mismatch: {len(got_outputs - exp_outputs)} extra, {len(exp_outputs - got_outputs)} missing"
PY

# Check 6: no duplicates (crate, name)
DUPES=$(python3 - "$JSON" <<'PY'
import json, sys
pb = json.load(open(sys.argv[1], encoding="utf-8"))
seen = {}
dupes = 0
for e in pb["entities"]:
    parts = e["file"].split("/")
    crate = parts[4] if len(parts) > 4 else "<unknown>"
    key = (crate, e["name"])
    if key in seen:
        dupes += 1
    seen[key] = True
print(dupes)
PY
)
[ "$DUPES" = "0" ] || fail "$DUPES (crate,name) duplicados en entities[]"

# Check 7: cada entity tiene file y decl_line > 0
BAD_FIELDS=$(python3 - "$JSON" <<'PY'
import json, sys
pb = json.load(open(sys.argv[1], encoding="utf-8"))
bad = 0
for e in pb["entities"]:
    if not e.get("file") or not e.get("decl_line"):
        bad += 1
print(bad)
PY
)
[ "$BAD_FIELDS" = "0" ] || fail "$BAD_FIELDS entidades sin file o decl_line"

# Check 8: ningún pb.index null en campos con pb (defensivo)
BAD_PB=$(python3 - "$JSON" <<'PY'
import json, sys
pb = json.load(open(sys.argv[1], encoding="utf-8"))
bad = 0
for e in pb["entities"]:
    if e["kind"] != "struct":
        continue
    for f in e.get("fields", []):
        if f.get("pb") is not None and f["pb"].get("index") is None:
            bad += 1
print(bad)
PY
)
[ "$BAD_PB" = "0" ] || fail "$BAD_PB campos con #[pb(...)] sin index"

# Resumen
MISSING_COUNT=$(jq -r '.cross_ref.missing_event_pbs | length' "$JSON")
RESOLVED_I=$(jq -r '.cross_ref.resolved_inputs | length' "$JSON")
RESOLVED_O=$(jq -r '.cross_ref.resolved_outputs | length' "$JSON")
UNIQUE_I=$(jq -r '.cross_ref.unique_event_inputs | length' "$JSON")
UNIQUE_O=$(jq -r '.cross_ref.unique_event_outputs | length' "$JSON")

echo "OK: A2.2 (JSON valido, $ENTITY_COUNT entidades ($ACT_STR structs + $ACT_ENUM enums), cruce con events.json resuelto: $RESOLVED_I/$UNIQUE_I inputs + $RESOLVED_O/$UNIQUE_O outputs, $MISSING_COUNT missing reportados)"
exit 0
