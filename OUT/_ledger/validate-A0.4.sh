#!/usr/bin/env bash
# validate-A0.4.sh — Prueba de la Fase A0.4 (SKILL/templates/output-skeleton/).
# Salida: 0 si OK, 1 si algún check falla (imprime el check).
set -u
fail() { echo "FAIL: $1" >&2; exit 1; }
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
S="$ROOT/SKILL/templates/output-skeleton"
[ -d "$S" ] || fail "no existe $S"

md=$(find "$S" -type f -name '*.md' | wc -l | tr -d ' ')
[ "$md" -eq 55 ] || fail "se esperaban 55 .md, hay $md"

bad=0
while IFS= read -r f; do
  rg -q "^id: " "$f"             || { echo "  sin id: $f" >&2; bad=$((bad+1)); }
  rg -q "^estado: pendiente$" "$f" || { echo "  sin estado: $f" >&2; bad=$((bad+1)); }
  n=$(rg -c "^---$" "$f" | tr -d ' ')
  [ "$n" -eq 2 ] || { echo "  frontmatter mal cerrado ($n ---): $f" >&2; bad=$((bad+1)); }
done < <(find "$S" -type f -name '*.md')
[ "$bad" -eq 0 ] || fail "$bad checks fallidos sobre los .md"

for d in 06-puente-flutter-rust 07-motor-colaborativo-crdt 08-persistencia \
         09-features 10-motor-export-import _ledger; do
  [ -d "$S/$d" ] || fail "falta directorio raíz $d"
done

fc=$(find "$S/09-features" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')
[ "$fc" -eq 18 ] || fail "se esperaban 18 subcarpetas en 09-features, hay $fc"

# Carpetas que contendrán JSON/CSV deben tener .gitkeep
for d in "$S/_ledger" "$S/_ledger/extract" "$S/_ledger/units"; do
  [ -f "$d/.gitkeep" ] || fail "falta .gitkeep en $d"
done

# Las 17 features (F01..F17) + F2x-descubiertas = 18 deben tener .gitkeep
feat_gitkeep=0
for d in "$S"/09-features/*/; do
  [ -f "$d/.gitkeep" ] && feat_gitkeep=$((feat_gitkeep+1))
done
[ "$feat_gitkeep" -eq 18 ] || fail "se esperaban 18 .gitkeep en features, hay $feat_gitkeep"

echo "OK: A0.4 ($md .md con frontmatter, $fc features, 6 subárboles principales, .gitkeep en _ledger y features)"
