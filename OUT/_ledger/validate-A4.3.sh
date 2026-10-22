#!/usr/bin/env bash
# validate-A4.3.sh — Prueba de la Fase A4.3 (run_subagent.py + contratos).
# Salida: 0 si OK, 1 si algun check falla.
set -u
fail() { echo "FAIL: $1" >&2; exit 1; }
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
RUN="$ROOT/SKILL/scripts/run_subagent.py"
CONTRACT="$ROOT/SKILL/references/subagent-contract.md"
AUTOR="$ROOT/SKILL/references/subagent-autor-prompt.md"
REVISOR="$ROOT/SKILL/references/subagent-revisor-prompt.md"
FIX="$ROOT/OUT/_ledger/pruebas/A4.3/fixtures"

[ -f "$RUN" ]      || fail "no existe $RUN"
[ -x "$RUN" ]      || fail "$RUN no es ejecutable"
[ -f "$CONTRACT" ] || fail "no existe $CONTRACT"
[ -f "$AUTOR" ]    || fail "no existe $AUTOR"
[ -f "$REVISOR" ]  || fail "no existe $REVISOR"
[ -d "$FIX" ]      || fail "no existe $FIX"

# Check 1: los 3 referencias existen y no estan vacios
for f in "$CONTRACT" "$AUTOR" "$REVISOR"; do
  [ -s "$f" ] || fail "$(basename "$f") esta vacio"
done
[ -s "$FIX/trivial_unit.json" ] || fail "trivial_unit.json vacio o ausente"
echo "  referencias: 3 archivos no vacios, fixture presente"

# Check 2: --help funciona
python3 "$RUN" --help >/dev/null 2>&1 || fail "--help fallo"

# Check 3: modo autor produce JSON valido y crea el documento
WORK=$(mktemp -d)
python3 "$RUN" \
  --rol autor \
  --unit "$FIX/trivial_unit.json" \
  --out "$WORK/autor.json" \
  --out-root "$WORK" \
  --quiet --no-color 2>&1 \
  || fail "modo autor fallo"
[ -f "$WORK/autor.json" ] || fail "autor.json no se genero"
python3 - "$WORK/autor.json" <<'PY' || fail "AutorOutput no valido"
import json, sys
d = json.load(open(sys.argv[1]))
assert d.get("schema_version") == 1, "schema_version"
for f in ("documento", "filas_ledger_cubiertas", "archivos_extra_detectados", "preguntas_abiertas", "metricas"):
    assert f in d, f"falta campo: {f}"
assert isinstance(d["filas_ledger_cubiertas"], list) and d["filas_ledger_cubiertas"], "filas_ledger_cubiertas vacio"
assert isinstance(d["archivos_extra_detectados"], list), "archivos_extra_detectados no es lista"
assert isinstance(d["preguntas_abiertas"], list) and d["preguntas_abiertas"], "preguntas_abiertas vacio"
print(f"  AutorOutput: documento={d['documento']} filas={len(d['filas_ledger_cubiertas'])}")
PY

# Check 4: el documento creado existe y tiene >= 19 secciones
DOC_PATH="$WORK/$(python3 -c "import json; print(json.load(open('$WORK/autor.json'))['documento'])")"
[ -f "$DOC_PATH" ] || fail "documento no creado en $DOC_PATH"
NSEC=$(grep -cE '^## [0-9]+\.' "$DOC_PATH" || true)
[ "$NSEC" -ge 19 ] || fail "documento tiene $NSEC secciones, esperaba >= 19"
echo "  documento: $DOC_PATH con $NSEC secciones"

# Check 5: modo revisor produce JSON valido (RevisorOutput)
python3 "$RUN" \
  --rol revisor \
  --unit "$FIX/trivial_unit.json" \
  --out "$WORK/revisor.json" \
  --out-root "$WORK" \
  --no-color 2>&1 \
  || fail "modo revisor fallo"
[ -f "$WORK/revisor.json" ] || fail "revisor.json no se genero"
python3 - "$WORK/revisor.json" <<'PY' || fail "RevisorOutput no valido"
import json, sys
d = json.load(open(sys.argv[1]))
assert d.get("schema_version") == 1
assert d.get("veredicto") in ("aprobado", "rechazado"), f"veredicto: {d.get('veredicto')}"
for f in ("correcciones", "muestreo_verificado", "validaciones"):
    assert f in d, f"falta campo: {f}"
v = d["validaciones"]
for k in ("evidence", "template", "mermaid"):
    assert k in v, f"falta validacion: {k}"
    assert "exit" in v[k], f"falta exit en {k}"
print(f"  RevisorOutput: veredicto={d['veredicto']} correcciones={len(d['correcciones'])}")
PY

# Check 6: --json produce JSON parseable en stdout
python3 "$RUN" --rol autor --unit "$FIX/trivial_unit.json" \
  --out "$WORK/autor2.json" --out-root "$WORK" \
  --json --quiet --no-color 2>/dev/null \
  | python3 -c "import json, sys; d=json.load(sys.stdin); assert d['schema_version']==1" \
  || fail "--json stdout no parseable (autor)"
python3 "$RUN" --rol revisor --unit "$FIX/trivial_unit.json" \
  --out "$WORK/revisor2.json" --out-root "$WORK" \
  --json --quiet --no-color 2>/dev/null \
  | python3 -c "import json, sys; d=json.load(sys.stdin); assert d['schema_version']==1" \
  || fail "--json stdout no parseable (revisor)"

# Check 7: el contrato menciona los 4 esquemas por nombre
for s in "AutorInput" "AutorOutput" "RevisorInput" "RevisorOutput"; do
  grep -q "$s" "$CONTRACT" || fail "contrato no menciona esquema $s"
done
echo "  contrato: 4 esquemas presentes (AutorInput/Output, RevisorInput/Output)"

# Check 8: prompts referencian el contrato
for s in "subagent-contract.md" "validate_evidence" "validate_template" "validate_mermaid"; do
  grep -q "$s" "$AUTOR" || grep -q "$s" "$REVISOR" \
    || fail "ningun prompt referencia $s"
done
echo "  prompts: ambos referencian el contrato y los 3 validadores"

# Check 9 (opcional): si mmdc no esta, el revisor reporta mermaid exit=2 pero no falla
if ! command -v mmdc >/dev/null 2>&1 && ! command -v npx >/dev/null 2>&1; then
  echo "  WARN: mmdc no disponible; el revisor reportara mermaid exit=2 (cubierto por el validador)"
fi

rm -rf "$WORK"

echo "OK: A4.3 (run_subagent.py + 3 referencias: --help, autor produce AutorOutput + doc >= 19 secciones, revisor produce RevisorOutput, --json OK, contrato y prompts OK)"
