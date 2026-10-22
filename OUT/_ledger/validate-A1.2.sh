#!/usr/bin/env bash
# validate-A1.2.sh — Prueba de la Fase A1.2 (inventory.py + inventario.json + assets.json).
# Salida: 0 si OK, 1 si algún check falla (imprime el check fallido).
set -u
fail() { echo "FAIL: $1" >&2; exit 1; }
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
INV="$ROOT/OUT/_ledger/inventario.json"
AST="$ROOT/OUT/_ledger/assets.json"
[ -f "$INV" ] || fail "no existe $INV (ejecuta primero SKILL/scripts/inventory.py)"
[ -f "$AST" ] || fail "no existe $AST"

# Check 1: JSON válido, schema_version=1, files presente
python3 - "$INV" <<'PY' || fail "inventario.json inválido"
import json, sys
d = json.load(open(sys.argv[1]))
assert d.get("schema_version") == 1, f"schema_version esperado 1, hay {d.get('schema_version')}"
assert "files" in d, "falta clave 'files'"
assert isinstance(d["files"], list), "'files' no es lista"
assert len(d["files"]) > 0, "lista de files vacía"
PY

# Check 2: ninguna entrada con capa null
python3 - "$INV" <<'PY' || fail "algún archivo con capa null"
import json, sys
d = json.load(open(sys.argv[1]))
bad = [f for f in d["files"] if not f.get("capa")]
assert not bad, f"{len(bad)} archivos con capa null (ej: {bad[:3]})"
PY

# Check 3: cada entrada tiene los 8 campos requeridos
python3 - "$INV" <<'PY' || fail "algún archivo sin los 8 campos requeridos"
import json, sys
d = json.load(open(sys.argv[1]))
required = {"fuente", "ruta_rel", "ruta_abs", "lenguaje", "loc", "sha1", "bytes", "capa"}
for f in d["files"]:
    missing = required - f.keys()
    assert not missing, f"{f.get('ruta_rel', '?')} falta {missing}"
PY

# Check 4: conteo .rs coincide con find (sin .git, target, build)
find_rs=$(find "$ROOT/SRC" -name '*.rs' -not -path '*/.git/*' -not -path '*/target/*' -not -path '*/build/*' 2>/dev/null | wc -l | tr -d ' ')
inv_rs=$(python3 -c "import json; d=json.load(open('$INV')); print(sum(1 for f in d['files'] if f['lenguaje']=='rust'))")
[ "$find_rs" = "$inv_rs" ] || fail "rs: find=$find_rs ≠ inventario=$inv_rs"

# Check 5: conteo .dart coincide con find
find_dart=$(find "$ROOT/SRC" -name '*.dart' \
  -not -path '*/.git/*' \
  -not -path '*/.dart_tool/*' \
  -not -path '*/build/*' \
  -not -path '*/.symlinks/*' \
  -not -path '*/Pods/*' \
  -not -path '*/ephemeral/*' \
  2>/dev/null | wc -l | tr -d ' ')
inv_dart=$(python3 -c "import json; d=json.load(open('$INV')); print(sum(1 for f in d['files'] if f['lenguaje']=='dart'))")
[ "$find_dart" = "$inv_dart" ] || fail "dart: find=$find_dart ≠ inventario=$inv_dart"

# Check 6: assets.json válido
python3 - "$AST" <<'PY' || fail "assets.json inválido"
import json, sys
d = json.load(open(sys.argv[1]))
assert d.get("schema_version") == 1
assert "assets" in d
assert isinstance(d["assets"], list)
for a in d["assets"]:
    for k in ("fuente", "ruta_rel", "ruta_abs", "formato", "bytes", "sha1"):
        assert k in a, f"asset {a.get('ruta_rel','?')} falta {k}"
PY

# Check 7: ningún asset aparece también en inventario
python3 - "$INV" "$AST" <<'PY' || fail "hay archivos duplicados entre inventario y assets"
import json, sys
inv = {(f["fuente"], f["ruta_rel"]) for f in json.load(open(sys.argv[1]))["files"]}
ast = {(a["fuente"], a["ruta_rel"]) for a in json.load(open(sys.argv[2]))["assets"]}
overlap = inv & ast
assert not overlap, f"{len(overlap)} duplicados: {list(overlap)[:3]}"
PY

# Check 8: las 3 fuentes están presentes
python3 - "$INV" <<'PY' || fail "alguna fuente falta en inventario"
import json, sys
d = json.load(open(sys.argv[1]))
fuentes = {f["fuente"] for f in d["files"]}
for expected in ("appflowy", "collab", "editor"):
    assert expected in fuentes, f"falta fuente {expected}"
PY

echo "OK: A1.2 (JSON válido, sin capa null, 8 campos, .rs/.dart coinciden con find, assets separados, 3 fuentes)"
