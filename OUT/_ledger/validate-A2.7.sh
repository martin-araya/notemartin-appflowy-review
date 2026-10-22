#!/usr/bin/env bash
# validate-A2.7.sh — Prueba de la Fase A2.7 (extract_codegen.sh + codegen-result.json).
# Salida: 0 si OK, 1 si algún check falla.
#
# Criterios del ROADMAP.md A2.7:
#   1. codegen-result.json existe, JSON válido, schema_version=1.0.
#   2. outcome ∈ {"success", "failed"}.
#   3. Si outcome="success": existen .proto generados y se comparan con A2.2.
#   4. Si outcome="failed": existe codegen-fallido.md con causa documentada.
set -u
fail() { echo "FAIL: $1" >&2; exit 1; }
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
JSON="$ROOT/OUT/_ledger/pruebas/A2.7/codegen-result.json"
FAIL_MD="$ROOT/OUT/_ledger/pruebas/A2.7/codegen-fallido.md"

# Check 1: JSON existe
[ -f "$JSON" ] || fail "no existe $JSON (ejecuta primero SKILL/scripts/extract_codegen.sh)"

# Check 2: JSON válido
jq empty "$JSON" 2>/dev/null || fail "JSON inválido en $JSON"

# Check 3: schema_version
SCHEMA=$(jq -r '.schema_version // ""' "$JSON")
[ "$SCHEMA" = "1.0" ] || fail "schema_version='$SCHEMA' (esperado '1.0')"

# Check 4: outcome
OUTCOME=$(jq -r '.outcome // ""' "$JSON")
case "$OUTCOME" in
  success|failed) ;;
  *) fail "outcome='$OUTCOME' (esperado 'success' o 'failed')" ;;
esac

# Check 5: prerrequisitos todos presentes (al menos como objeto)
PREREQ_KEYS=$(jq -r '.prerequisites | keys | length' "$JSON")
[ "$PREREQ_KEYS" -ge 6 ] || fail "prerrequisitos incompletos: $PREREQ_KEYS (esperado >= 6)"

# Check 6: si outcome="success", verificar .proto y comparar con A2.2
if [ "$OUTCOME" = "success" ]; then
  PROTOS_DIR=$(jq -r '.output_dir' "$JSON")
  PROTOS_COUNT=$(find "$PROTOS_DIR/protos" -name "*.proto" 2>/dev/null | wc -l | tr -d ' ')
  [ "$PROTOS_COUNT" -gt 0 ] || fail "outcome=success pero no hay .proto en $PROTOS_DIR/protos"

  # Comparar con A2.2.
  A2_2_JSON="$ROOT/OUT/_ledger/extract/protobuf.json"
  if [ -f "$A2_2_JSON" ]; then
    A22_COUNT=$(jq -r '.entities | length' "$A2_2_JSON")
    # Buscar cuántos entity names de A2.2 aparecen en algún .proto.
    MATCHED=$(jq -r --arg dir "$PROTOS_DIR/protos" '
      .entities[].name as $name |
      ([$name] | any(. != "")) as $ok |
      $name
    ' "$A2_2_JSON" 2>/dev/null | while read -r name; do
      if [ -n "$name" ] && grep -rq "message $name\b" "$PROTOS_DIR/protos"/*.proto 2>/dev/null; then
        echo "$name"
      fi
    done | wc -l | tr -d ' ')
    if [ "$A22_COUNT" -gt 0 ]; then
      PCT=$((MATCHED * 100 / A22_COUNT))
      [ "$PCT" -ge 80 ] || fail "solo $MATCHED/$A22_COUNT ($PCT%) entities de A2.2 aparecen en .proto"
    fi
  fi
  echo "OK: A2.7 (codegen exitoso, $PROTOS_COUNT .proto en $PROTOS_DIR/protos, $MATCHED/$A22_COUNT match A2.2)"
else
  # Check 7: outcome="failed" → codegen-fallido.md debe existir
  [ -f "$FAIL_MD" ] || fail "outcome=failed pero no existe $FAIL_MD"
  # Tamaño mínimo del documento de fallo.
  SIZE=$(wc -c < "$FAIL_MD" | tr -d ' ')
  [ "$SIZE" -ge 100 ] || fail "codegen-fallido.md tiene $SIZE bytes (esperado >= 100)"

  # failure_cause_summary no vacío
  CAUSE=$(jq -r '.failure_cause_summary // ""' "$JSON")
  [ -n "$CAUSE" ] || fail "failure_cause_summary vacío"

  # Contar estrategias intentadas.
  ATTEMPTS=$(jq -r '.attempts | length' "$JSON")
  echo "OK: A2.7 (codegen no ejecutado en este entorno: $CAUSE, $ATTEMPTS intento(s) documentado(s) en $FAIL_MD)"
fi
exit 0
