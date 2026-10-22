#!/usr/bin/env bash
# validate-A2.1.sh — Prueba de la Fase A2.1 (extract_events.py + events.json).
# Salida: 0 si OK, 1 si algún check falla (imprime el check fallido).
#
# Criterios del ROADMAP.md A2.1:
#   1. events.json existe y es JSON válido con schema_version=1.0.
#   2. flowy-document aparece con `CreateDocument` (input CreateDocumentPayloadPB,
#      sin output) y `OpenDocument` (input OpenDocumentPayloadPB, output DocumentDataPB).
#   3. Toda variante del enum tiene handler registrado o está marcada sin_handler.
#   4. Conteos internos coherentes.
set -u
fail() { echo "FAIL: $1" >&2; exit 1; }
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
JSON="$ROOT/OUT/_ledger/extract/events.json"

[ -f "$JSON" ] || fail "no existe $JSON (ejecuta primero SKILL/scripts/extract_events.py)"

# Check 1: JSON válido
jq empty "$JSON" 2>/dev/null || fail "JSON inválido en $JSON"

# Check 2: schema_version
SCHEMA=$(jq -r '.schema_version // ""' "$JSON")
[ "$SCHEMA" = "1.0" ] || fail "schema_version='$SCHEMA' (esperado '1.0')"

# Check 3: tiene crates y no vacío
CRATES_COUNT=$(jq -r '.crates | length' "$JSON")
[ "$CRATES_COUNT" -gt 0 ] || fail "no hay crates en $JSON (¿SRC/<fuente>/frontend/rust-lib/**/event_map.rs vacío?)"

# Check 4: flowy-document presente
HAS_DOC=$(jq -e '.crates[] | select(.crate=="flowy-document")' "$JSON" >/dev/null 2>&1 && echo y || echo n)
[ "$HAS_DOC" = "y" ] || fail "falta crate 'flowy-document'"

# Check 5 (test ROADMAP): CreateDocument
jq -e '.crates[] | select(.crate=="flowy-document")
       | .variants[] | select(.name=="CreateDocument")
       | (.input == "CreateDocumentPayloadPB" and .output == null)' \
  "$JSON" >/dev/null \
  || fail "flowy-document::CreateDocument: input/output no coinciden (esperado input=CreateDocumentPayloadPB, output=null)"

# Check 6 (test ROADMAP): OpenDocument
jq -e '.crates[] | select(.crate=="flowy-document")
       | .variants[] | select(.name=="OpenDocument")
       | (.input == "OpenDocumentPayloadPB" and .output == "DocumentDataPB")' \
  "$JSON" >/dev/null \
  || fail "flowy-document::OpenDocument: input/output no coinciden (esperado input=OpenDocumentPayloadPB, output=DocumentDataPB)"

# Check 7: ninguna variante tiene sin_handler=True con registrations no vacío
BAD1=$(jq -r '[.crates[].variants[]
              | select(.sin_handler == true and (.registrations | length) != 0)]
              | length' "$JSON")
[ "$BAD1" = "0" ] || fail "$BAD1 variantes con sin_handler=true y registrations no vacío"

# Check 8: ninguna variante registrada tiene sin_handler=True
BAD2=$(jq -r '[.crates[].variants[]
              | select(.sin_handler == false and (.registrations | length) == 0)]
              | length' "$JSON")
[ "$BAD2" = "0" ] || fail "$BAD2 variantes con sin_handler=false y registrations vacío"

# Check 9: todo handler registrado debe tener handler_file resuelto (no null)
# (los handlers sin resolver se documentan como warning, pero aquí exigimos 0
#  para que la fase sea bloqueante: si un handler falta, hay que arreglar el script)
BAD3=$(jq -r '[.crates[].variants[].registrations[]
              | select(.handler_file == null or .handler_line == null)]
              | length' "$JSON")
[ "$BAD3" = "0" ] || fail "$BAD3 registros de handlers sin resolver (handler_file o handler_line null)"

# Check 10: conteos internos coherentes (summary == sum(crate.summary))
EXPECT_TOT=$(jq -r '[.crates[].summary.total_variants]    | add' "$JSON")
EXPECT_REG=$(jq -r '[.crates[].summary.registered]       | add' "$JSON")
EXPECT_SIN=$(jq -r '[.crates[].summary.sin_handler]      | add' "$JSON")
SUM_TOT=$(jq -r '.summary.total_variants'    "$JSON")
SUM_REG=$(jq -r '.summary.total_registered'  "$JSON")
SUM_SIN=$(jq -r '.summary.total_sin_handler' "$JSON")
[ "$EXPECT_TOT" = "$SUM_TOT" ] || fail "summary.total_variants=$SUM_TOT ≠ sum(crate.total_variants)=$EXPECT_TOT"
[ "$EXPECT_REG" = "$SUM_REG" ] || fail "summary.total_registered=$SUM_REG ≠ sum(crate.registered)=$EXPECT_REG"
[ "$EXPECT_SIN" = "$SUM_SIN" ] || fail "summary.total_sin_handler=$SUM_SIN ≠ sum(crate.sin_handler)=$EXPECT_SIN"

# Check 11: total = registered + sin_handler
[ "$SUM_TOT" = "$((SUM_REG + SUM_SIN))" ] \
  || fail "summary: total($SUM_TOT) ≠ registered($SUM_REG) + sin_handler($SUM_SIN)"

# Resumen para el log
SIN_HANDLER_LIST=$(jq -r '.crates[]
                       | select(.summary.sin_handler > 0)
                       | .crate as $c
                       | .variants[]
                       | select(.sin_handler)
                       | "  - \($c)::\(.name) (index=\(.index))"' \
                       "$JSON")
[ -z "$SIN_HANDLER_LIST" ] && SIN_HANDLER_LIST="  (ninguna)"

echo "OK: A2.1 (JSON valido, flowy-document OK, CreateDocument input=CreateDocumentPayloadPB output=null, OpenDocument input=OpenDocumentPayloadPB output=DocumentDataPB, sin_handler consistentes, handlers resueltos, conteos coherentes)"
echo "  crates_with_event_map: $CRATES_COUNT"
echo "  total_variants:        $SUM_TOT"
echo "  total_registered:      $SUM_REG"
echo "  total_sin_handler:     $SUM_SIN"
echo "  sin_handler variants:"
echo "$SIN_HANDLER_LIST"
exit 0
