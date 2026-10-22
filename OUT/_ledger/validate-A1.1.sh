#!/usr/bin/env bash
# validate-A1.1.sh — Prueba de la Fase A1.1 (fetch_sources.sh + sources.json).
# Salida: 0 si OK, 1 si algún check falla (imprime el check fallido).
set -u
fail() { echo "FAIL: $1" >&2; exit 1; }
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
JSON="$ROOT/OUT/_ledger/sources.json"
[ -f "$JSON" ] || fail "no existe $JSON (ejecuta primero SKILL/scripts/fetch_sources.sh)"

# Check 1: JSON válido + 3 entradas + nombres correctos + commits con longitud ≥ 7
python3 - "$JSON" <<'PY' || fail "sources.json inválido o incompleto"
import json, sys
d = json.load(open(sys.argv[1]))
assert d.get("schema_version") == 1, f"schema_version esperado 1, hay {d.get('schema_version')}"
assert "sources" in d, "falta clave 'sources'"
assert len(d["sources"]) == 3, f"se esperan 3 entradas, hay {len(d['sources'])}"
names = {s["name"] for s in d["sources"]}
assert names == {"appflowy", "collab", "editor"}, f"nombres inesperados: {names}"
for s in d["sources"]:
    assert "commit" in s, f"{s['name']}.commit ausente"
    assert len(s["commit"]) >= 7, f"{s['name']}.commit corto ({len(s['commit'])}): {s['commit']}"
    assert "commit_short" in s, f"{s['name']}.commit_short ausente"
    assert s["commit_short"] == s["commit"][:7], \
        f"{s['name']}.commit_short={s['commit_short']} no es prefijo de commit={s['commit'][:7]}"
    assert "url" in s, f"{s['name']}.url ausente"
    assert "path" in s, f"{s['name']}.path ausente"
    assert "cloned_at" in s, f"{s['name']}.cloned_at ausente"
PY

# Check 2: la prueba del ROADMAP — rev-parse de SRC/collab == sources.json[collab].commit_short
COLLAB_HEAD=$(git -C "$ROOT/SRC/collab" rev-parse --short HEAD 2>/dev/null || echo none)
COLLAB_JSON=$(python3 -c 'import json; print(json.load(open("'"$JSON"'"))["sources"][1]["commit_short"])')
[ "$COLLAB_HEAD" = "$COLLAB_JSON" ] \
  || fail "collab HEAD=$COLLAB_HEAD ≠ sources.json[collab].commit_short=$COLLAB_JSON"

# Check 3: cada SRC/<name> tiene .git y HEAD legible
for n in appflowy collab editor; do
  [ -d "$ROOT/SRC/$n/.git" ] || fail "SRC/$n no es repo git"
  h=$(git -C "$ROOT/SRC/$n" rev-parse HEAD 2>/dev/null) || fail "SRC/$n no tiene HEAD legible"
  j=$(python3 -c 'import json,sys; print([s["commit"] for s in json.load(open("'"$JSON"'"))["sources"] if s["name"]=="'"$n"'"][0])')
  [ "$h" = "$j" ] || fail "SRC/$n HEAD=$h ≠ sources.json[$n].commit=$j"
done

# Check 4: el rev de collab en sources.json debe ser derivable del Cargo.toml clonado
python3 - "$ROOT" <<'PY' || fail "no se puede re-derivar el rev de Collab del Cargo.toml"
import re, sys
toml = open(f"{sys.argv[1]}/SRC/appflowy/frontend/rust-lib/Cargo.toml").read()
m = re.search(r'\[patch\.crates-io\](.*?)(?=\n\[|\Z)', toml, re.S)
assert m, "[patch.crates-io] ausente en Cargo.toml"
block = m.group(1)
revs = set(re.findall(r'rev\s*=\s*"([0-9a-f]{7,40})"', block))
assert revs, "no hay revs en [patch.crates-io]"
PY

# Check 5: el ref del editor debe ser derivable del pubspec.yaml clonado
python3 - "$ROOT" <<'PY' || fail "no se puede re-derivar el ref del editor del pubspec.yaml"
import re, sys
y = open(f"{sys.argv[1]}/SRC/appflowy/frontend/appflowy_flutter/pubspec.yaml").read()
m = re.search(r'^\s*dependency_overrides:\s*\n((?:\s+.*\n)+)', y, re.M)
assert m, "dependency_overrides ausente en pubspec.yaml"
m2 = re.search(r'^\s*appflowy_editor:\s*\n((?:\s+.*\n)+)', m.group(1), re.M)
assert m2, "appflowy_editor ausente en dependency_overrides"
ref = re.search(r'^\s*ref:\s*([^\s#]+)\s*$', m2.group(1), re.M)
assert ref, ".git.ref ausente en dependency_overrides.appflowy_editor"
PY

echo "OK: A1.1 (3 entradas, commit_short=HEAD, SRC/<name> con .git, [patch.crates-io] y dependency_overrides derivables)"
