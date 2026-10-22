#!/usr/bin/env bash
# Genera el diff unificado de `SKILL/references/` antes/después de A5.2.
# Asume que existe `/tmp/refs-before-a52/` con la snapshot pre-A5.2 (lo
# crea el orquestador en el paso 0.1 del plan).
# Salida: `OUT/_ledger/pruebas/A5.2/diff-references.patch`.

set -u
set -o pipefail

SCRIPT_NAME=$(basename "$0")
SCRIPT_DIR=$(cd "$(dirname "$0")" && pwd)
PROJECT_ROOT=$(cd "$SCRIPT_DIR/../../../.." && pwd)
SNAPSHOT="${1:-/tmp/refs-before-a52}"
OUT="$SCRIPT_DIR/diff-references.patch"

if [[ ! -d "$SNAPSHOT" ]]; then
  echo "[$SCRIPT_NAME] ERROR: no existe snapshot $SNAPSHOT" >&2
  exit 2
fi

: > "$OUT"
EXIT=0
for f in diagram-conventions.md evidence-rules.md subagent-contract.md subagent-autor-prompt.md subagent-revisor-prompt.md patterns.md; do
  before="$SNAPSHOT/$f"
  after="$PROJECT_ROOT/SKILL/references/$f"
  if [[ ! -f "$before" || ! -f "$after" ]]; then
    echo "[$SCRIPT_NAME] WARN: $f no existe en snapshot o en destino, se omite." >&2
    continue
  fi
  diff -u "$before" "$after" >> "$OUT" 2>/dev/null || EXIT=$?
done

# Eliminar ruido: líneas "\ No newline at end of file" (cosmético)
# y el separador final.
if [[ -s "$OUT" ]]; then
  n=$(grep -c '^@@' "$OUT" || true)
  size=$(wc -c < "$OUT" | tr -d ' ')
  echo "[$SCRIPT_NAME] OK: $n hunks, $size bytes -> $OUT" >&2
else
  echo "[$SCRIPT_NAME] WARN: diff vacío." >&2
fi

exit $EXIT
