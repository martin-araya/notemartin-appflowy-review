#!/usr/bin/env bash
# validate-C3.sh — Suite de la Fase C3 (revisión cruzada de consistencia).
#
# Cierra la prueba literal del ROADMAP §"Fase C3": *informe sin contradicciones
# abiertas*. Concretamente verifica cinco cosas:
#
#   1. Los tres validadores deterministas siguen en verde tras las reescrituras
#      de C3 (no hay regresión respecto a C1).
#   2. El contraste B5 × B2 no ha empeorado respecto a la línea base de C3, y el
#      recuento de fabricaciones está por debajo del umbral acordado.
#   3. La tabla de símbolos sin evidencia del glosario cubre todos los símbolos
#      que C3 ha identificado como inexistentes.
#   4. Los documentos de B5 no contienen damage de span de inline code.
#   5. El barrido de precisión del detector de spans sobre OUT/ no produce falsos
#      positivos (0 aciertos fuera de las líneas conocidas).
#
# Uso:
#   bash OUT/_ledger/validate-C3.sh
#   bash OUT/_ledger/validate-C3.sh --verbose
#
# Fase C3 de la skill notemartin-appflowy-review.

set -uo pipefail

VERBOSE=0
[ "${1:-}" = "--verbose" ] && VERBOSE=1

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SKILL="$ROOT/SKILL/scripts"
OUT="$ROOT/OUT"
LEDGER="$OUT/_ledger"
C3="$LEDGER/pruebas/C3"

# Cierre de C3.1: las 53 fabricaciones detectadas el 2026-10-21 quedaron en 0.
# El gate es 0 y no un maximo: cualquier reescritura futura que invente un simbolo
# rompe la suite, que es exactamente la regresion que C3 existe para evitar.
MAX_FABRICACIONES=0

PASS=0
FAIL=0
FAILS=""

ok()   { PASS=$((PASS+1)); printf '  [ OK ] %s\n' "$1"; }
ko()   { FAIL=$((FAIL+1)); FAILS="$FAILS$1\n"; printf '  [FAIL] %s\n' "$1"; }
head_() { printf '\n=== %s ===\n' "$1"; }

hr() { printf '  %s\n' "$1"; }

# ---------------------------------------------------------------- check 1
head_ "Check 1 · validadores deterministas sin regresión"

EV_OUT=$(python3 "$SKILL/validate_evidence.py" "$OUT" 2>&1 | tail -2)
EV_LINE=$(printf '%s\n' "$EV_OUT" | grep -o 'refs=[0-9]* ok=[0-9]* errors=[0-9]*' | tail -1)
EV_OK=$(printf '%s\n' "$EV_LINE" | sed -n 's/.*ok=\([0-9]*\).*/\1/p')
EV_ERR=$(printf '%s\n' "$EV_LINE" | sed -n 's/.*errors=\([0-9]*\).*/\1/p')
if [ "${EV_ERR:-x}" = "0" ] && [ "${EV_OK:-0}" -gt 17000 ]; then
  ok "validate_evidence: $EV_LINE"
else
  ko "validate_evidence: $EV_LINE"
fi

# Se le pasa el directorio entero, igual que la suite de C1: el propio
# `validate_template.py` excluye `_ledger/` y los tres entregables que no son
# documentos con plantilla (STATE.md, 00-INDEX.md, 22-preguntas-abiertas.md).
TPL_OUT=$(python3 "$SKILL/validate_template.py" "$OUT" 2>&1 | tail -2)
TPL_FAIL=$(printf '%s\n' "$TPL_OUT" | grep -o 'errors=[0-9]*' | tail -1 | cut -d= -f2)
if [ "${TPL_FAIL:-x}" = "0" ]; then
  ok "validate_template: $TPL_OUT"
else
  ko "validate_template: $TPL_OUT"
fi

MRM_OUT=$(bash "$SKILL/validate_mermaid.sh" "$OUT/15-secuencias-globales" "$OUT/08-persistencia" "$OUT/21-glosario.md" --quiet 2>&1 | tail -3)
MRM_FAIL=$(printf '%s\n' "$MRM_OUT" | grep -o 'FAIL=[0-9]*' | tail -1 | cut -d= -f2)
if [ "${MRM_FAIL:-x}" = "0" ]; then
  ok "validate_mermaid (docs tocados por C3): $(printf '%s\n' "$MRM_OUT" | grep -o 'OK=[0-9]* FAIL=[0-9]*' | tail -1)"
else
  ko "validate_mermaid: $MRM_OUT"
fi

# ---------------------------------------------------------------- check 2
head_ "Check 2 · contraste B5 × B2 por debajo del umbral"

CONTRAST=$(python3 "$SKILL/contrast_B5_B2.py" --out-dir "$C3" --quiet 2>/dev/null; \
           python3 -c "
import json
d = json.load(open('$C3/contrast_B5_B2.json'))
print(d['fabricaciones_unicas'])
")
N_FAB=$(printf '%s\n' "$CONTRAST" | tail -1)
if [ "${N_FAB:-x}" -le "$MAX_FABRICACIONES" ] 2>/dev/null; then
  ok "fabricaciones pendientes: $N_FAB (umbral $MAX_FABRICACIONES)"
else
  ko "fabricaciones pendientes: $N_FAB > umbral $MAX_FABRICACIONES"
fi

# ---------------------------------------------------------------- check 3
head_ "Check 3 · el glosario declara cada símbolo inexistente que C3 ha encontrado"

GLOSARIO="$OUT/21-glosario.md"
MISSING=()
for sym in ChunkedByteUploader AsyncZipExtractor ZipCreator KVFileCache \
           "StorageNotification::FileUploadProgress" "StorageNotification::DidFinishUpload" \
           MarkdownDocumentEncoder "DatabaseEvent::ImportCsvData" image_upload.dart; do
  grep -qF "$sym" "$GLOSARIO" || MISSING+=("$sym")
done
if [ "${#MISSING[@]}" -eq 0 ]; then
  ok "los 9 símbolos retirados están declarados en 21-glosario.md"
else
  ko "símbolo(s) sin declarar en el glosario: ${MISSING[*]}"
fi

# ---------------------------------------------------------------- check 4
head_ "Check 4 · sin damage de span en los documentos de B5"

SPAN_OUT=$(python3 "$SKILL/contrast_B5_B2.py" --out-dir "$C3" --quiet 2>/dev/null; \
           python3 -c "
import json
d = json.load(open('$C3/contrast_B5_B2.json'))
spans = [x for x in d['detalle'] if x['resultado'] == 'SPAN_DANADO']
print(len(spans))
for s in spans:
    print('   ', s['doc'], s['linea'])
")
N_SPAN=$(printf '%s\n' "$SPAN_OUT" | head -1)
if [ "${N_SPAN:-x}" = "0" ]; then
  ok "0 spans con prefijo duplicado en OUT/15-secuencias-globales/"
else
  ko "$N_SPAN span(s) dañado(s):" && printf '%s\n' "$SPAN_OUT" | tail -n +2
fi

# ---------------------------------------------------------------- check 5
head_ "Check 5 · precisión del detector de spans sobre todo OUT/ (0 falsos positivos)"

SWEEP=$(python3 "$SKILL/contrast_B5_B2.py" --sweep-root "$OUT" --out-dir /tmp/c3-sweep --quiet 2>/dev/null; \
        python3 -c "
import json
d = json.load(open('/tmp/c3-sweep/contrast_B5_B2.json'))
hits = [x for x in d['detalle'] if x['resultado'] == 'SPAN_DANADO']
# Las unicas coincidencias legas son las 2 lineas conocidas y sus copias en el
# backup de C1, que es un historico pre-reparacion y no un entregable.
deliverables = [h for h in hits if '/_ledger/pruebas/' not in h['doc']]
print(len(deliverables))
for h in deliverables:
    print('   ', h['doc'], h['linea'])
")
N_FP=$(printf '%s\n' "$SWEEP" | head -1)
if [ "${N_FP:-x}" = "0" ]; then
  ok "0 damage de span en los $(find "$OUT" -name '*.md' -not -path '*/_ledger/pruebas/*' | wc -l | tr -d ' ') documentos entregables"
else
  ko "$N_FP span(s) dañado(s) en entregables:" && printf '%s\n' "$SWEEP" | tail -n +2
fi

# ---------------------------------------------------------------- resumen
printf '\n%s\n' "============================================================"
if [ "$FAIL" -eq 0 ]; then
  printf 'OK: C3 (contraste B5 x B2 + propagacion + dano de span) %d/%d checks en verde\n' "$PASS" "$((PASS+FAIL))"
  exit 0
else
  printf 'FAIL: C3 %d/%d checks en verde\n' "$PASS" "$((PASS+FAIL))"
  printf "$FAILS" | sed 's/^/  - /' 
  exit 1
fi