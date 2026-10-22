#!/usr/bin/env bash
# validate-A0.3.sh — Prueba de la Fase A0.3 (SKILL/references/).
# Salida: 0 si OK, 1 si algún check falla (imprime el check).
set -u
fail() { echo "FAIL: $1" >&2; exit 1; }
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
R="$ROOT/SKILL/references"
[ -d "$R" ] || fail "no existe $R"
n=$(ls "$R"/*.md 2>/dev/null | wc -l | tr -d ' ')
[ "$n" -eq 6 ] || fail "se esperaban 6 .md en $R, hay $n"
for f in repo-map patterns evidence-rules diagram-conventions feature-template export-template; do
  test -s "$R/$f.md" || fail "falta o vacío $f.md"
  rg -q "^id: R-00" "$R/$f.md"     || fail "$f.md sin frontmatter id"
  for k in id titulo fuente archivos_cubiertos estado; do
    rg -q "^$k:" "$R/$f.md"         || fail "$f.md sin campo '$k' en frontmatter"
  done
done
ft=$(rg -c "^## [0-9]+\." "$R/feature-template.md" | tr -d ' ')
[ "$ft" -ge 19 ] || fail "feature-template.md tiene $ft secciones numeradas, necesita >= 19"
et=$(rg -c "^## [0-9]+\." "$R/export-template.md" | tr -d ' ')
[ "$et" -ge 11 ] || fail "export-template.md tiene $et secciones numeradas, necesita >= 11"
if rg -lU "^## .+\n\n## " "$R"/*.md >/dev/null 2>&1; then
  fail "sección vacía detectada en alguna referencia"
fi
echo "OK: A0.3 (6 referencias, $ft secciones en feature-template, $et en export-template, frontmatter completo, sin secciones vacías)"
