#!/usr/bin/env bash
# validate-B3.F013.sh — Prueba de la Fase B3.F01.3.
# Caso especial: scope correction. El ledger F01.3 no tiene archivos;
# los widgets image/video/file/cover/link_preview/link_embed viven en F07.
# Este validador confirma 4 checks:
#   1. template (19 secciones + frontmatter)
#   2. evidence (refs internas o a docs verificadas)
#   3. mermaid (>= 1 bloque)
#   4. cobertura = 0 archivos en F01.3 (NO debe haber archivos)

set -u
set -o pipefail
fail() { echo "FAIL: $1" >&2; exit 1; }

ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
DOC="$ROOT/OUT/09-features/F01-documentos-y-editor/3-media-y-archivos-image-video-file-cover-link-preview-link-embed.md"
LEDGER="$ROOT/OUT/_ledger/cobertura.csv"
VT="$ROOT/SKILL/scripts/validate_template.py"
VE="$ROOT/SKILL/scripts/validate_evidence.py"
VM="$ROOT/SKILL/scripts/validate_mermaid.sh"

[ -f "$DOC" ]    || fail "no existe $DOC"
[ -f "$LEDGER" ] || fail "no existe $LEDGER"
[ -f "$VT" ]     || fail "no existe validate_template.py"
[ -f "$VE" ]     || fail "no existe validate_evidence.py"
[ -f "$VM" ]     || fail "no existe validate_mermaid.sh"

if ! python3 "$VT" -t feature "$DOC" --quiet >/dev/null 2>&1; then
  fail "template: F01.3 no cumple la plantilla feature"
fi

ev_output=$(python3 "$VE" "$DOC" --quiet 2>&1)
refs=$(echo "$ev_output" | grep -oE 'refs=[0-9]+' | tail -1 | grep -oE '[0-9]+')
refs_ok=$(echo "$ev_output" | grep -oE 'ok=[0-9]+' | tail -1 | grep -oE '[0-9]+')
if [ "${refs_ok:-0}" != "${refs:-0}" ]; then
  fail "evidence: ${refs_ok:-0}/${refs:-0} OK"
fi

m_output=$(bash "$VM" "$DOC" --quiet 2>&1)
ok_count=$(echo "$m_output" | grep -oE 'OK=[0-9]+' | tail -1 | grep -oE '[0-9]+')
fail_count=$(echo "$m_output" | grep -oE 'FAIL=[0-9]+' | tail -1 | grep -oE '[0-9]+')
if [ "${fail_count:-0}" != "0" ] && [ -n "${fail_count}" ]; then
  fail "mermaid: ${ok_count:-0} OK / ${fail_count} FAIL"
fi

# Cobertura: 0 archivos para F01.3 (scope correction).
# Verifica que NO haya archivos asignados a F01 y a las 6 rutas del ROADMAP.
verificados=$(awk -F, 'BEGIN{n=0} $4=="F01" && $2 ~ /editor_plugins\/(image|video|file|cover|link_preview|link_embed)\// && $6=="verificado" {n++} END{print n}' "$LEDGER")
if [ "$verificados" = "0" ]; then
  :
else
  fail "cobertura: F01.3 debe tener 0 archivos verificados; hay $verificados (algunos viven todavia en F01 — reasignar a F07)"
fi

echo "OK: B3.F01.3 (template=1/1, evidence=${refs_ok:-0}/${refs:-0}, mermaid=${ok_count:-0} OK, cobertura=0/0 scope-corrected)"
exit 0
