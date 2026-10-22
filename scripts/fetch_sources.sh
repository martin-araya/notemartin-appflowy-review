#!/usr/bin/env bash
# fetch_sources.sh — Adquiere SRC/{appflowy,collab,editor} en los rev correctos
#   y escribe OUT/_ledger/sources.json.
# Ver AGENTS.md §3 y ROADMAP.md A1.1.
#
# Uso: fetch_sources.sh [--appflowy-url URL] [--appflowy-ref REF]
#                       [--collab-url URL] [--editor-url URL]
#                       [--src-root DIR] [--out-root DIR]
#                       [--dry-run] [--force|-f] [--help|-h]
#
# Sin flags, clona AppFlowy en HEAD de su rama por defecto (shallow),
# lee el rev de AppFlowy-Collab de [patch.crates-io] en su Cargo.toml,
# lee el ref del appflowy-editor de dependency_overrides.appflowy_editor.git.ref
# en su pubspec.yaml, y clona ambos en los commits resueltos.

set -euo pipefail

# ---------- defaults (D8) ----------
APPFLOWY_URL_DEFAULT="https://github.com/AppFlowy-IO/AppFlowy"
COLLAB_URL_DEFAULT="https://github.com/AppFlowy-IO/AppFlowy-Collab"
EDITOR_URL_DEFAULT="https://github.com/AppFlowy-IO/appflowy-editor"
APPFLOWY_URL="$APPFLOWY_URL_DEFAULT"
COLLAB_URL="$COLLAB_URL_DEFAULT"
EDITOR_URL="$EDITOR_URL_DEFAULT"
APPFLOWY_REF=""
SRC_ROOT=""
OUT_ROOT=""
DRY_RUN=0
FORCE=0

# ---------- usage ----------
usage() {
  cat <<'USAGE'
fetch_sources.sh — Adquiere SRC/{appflowy,collab,editor} en los rev correctos

USO
  fetch_sources.sh [opciones]

OPCIONES
  --appflowy-url URL   Override URL de AppFlowy (default: AppFlowy-IO/AppFlowy)
  --appflowy-ref REF   Commit/branch/tag a fijar para AppFlowy (default: HEAD shallow)
  --collab-url URL     Override URL de AppFlowy-Collab
  --editor-url URL     Override URL de appflowy-editor
  --src-root DIR       Raíz de los clones (default: <skill_root>/SRC)
  --out-root DIR       Raíz de salida del ledger (default: <skill_root>/OUT)
  --dry-run            Resuelve refs e imprime plan; NO clona, NO escribe JSON
  --force, -f          Borra SRC/<name> si el commit no coincide con el solicitado
  --help, -h           Muestra esta ayuda

SALIDA
  Escribe OUT/_ledger/sources.json con 3 entradas (appflowy, collab, editor).

CÓDIGOS DE SALIDA
  0  OK
  1  Error de uso o parseo
  2  Fallo de clonación o checkout
  3  Inconsistencia post-clone
  4  SRC/<name> existe con otro commit y no se pasó --force
USAGE
}

# ---------- helpers ----------
die() {
  local code="$1"; shift
  echo "ERROR: $*" >&2
  exit "$code"
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die 1 "comando requerido no encontrado: $1"
}

resolve_root() {
  # Localiza la raíz del proyecto (que contiene SKILL/, SRC/, OUT/) a partir
  # de la ruta del script. El script vive en <root>/SKILL/scripts/, así que
  # subimos dos niveles para llegar a la raíz.
  local src="${BASH_SOURCE[0]}"
  # Sigue symlinks (compatibilidad con symlinked scripts)
  while [ -h "$src" ]; do
    local d; d=$(cd -P "$(dirname "$src")" && pwd)
    src=$(readlink "$src")
    [[ "$src" != /* ]] && src="$d/$src"
  done
  local d; d=$(cd -P "$(dirname "$src")" && pwd)
  # SKILL/scripts/fetch_sources.sh → d = <root>/SKILL/scripts
  SKILL_ROOT="$(cd "$d/../.." && pwd)"
}

parse_args() {
  while [ $# -gt 0 ]; do
    case "$1" in
      --appflowy-url) APPFLOWY_URL="$2"; shift 2 ;;
      --appflowy-ref) APPFLOWY_REF="$2"; shift 2 ;;
      --collab-url)   COLLAB_URL="$2";   shift 2 ;;
      --editor-url)   EDITOR_URL="$2";   shift 2 ;;
      --src-root)     SRC_ROOT="$2";     shift 2 ;;
      --out-root)     OUT_ROOT="$2";     shift 2 ;;
      --dry-run)      DRY_RUN=1;         shift ;;
      --force|-f)     FORCE=1;           shift ;;
      --help|-h)      usage; exit 0 ;;
      *) die 1 "flag desconocido: $1 (use --help)" ;;
    esac
  done
  [ -z "$SRC_ROOT" ] && SRC_ROOT="$SKILL_ROOT/SRC"
  [ -z "$OUT_ROOT" ] && OUT_ROOT="$SKILL_ROOT/OUT"
}

# ---------- extractors (D6, D7) ----------
extract_collab_rev() {
  # $1 = ruta a frontend/rust-lib/Cargo.toml
  # Imprime el rev resuelto por stdout.
  python3 - "$1" <<'PY'
import re, sys
from collections import Counter
toml = open(sys.argv[1]).read()
m = re.search(r'\[patch\.crates-io\](.*?)(?=\n\[|\Z)', toml, re.S)
if not m:
    sys.exit("no hay seccion [patch.crates-io] en Cargo.toml")
block = m.group(1)
# Captura pares crate = { git = "...", rev = "..." }
crates = dict(re.findall(
    r'^([A-Za-z0-9_\-]+)\s*=\s*\{[^{}]*git\s*=\s*"[^"]*"[^{}]*rev\s*=\s*"([^"]+)"',
    block, re.M))
if not crates:
    sys.exit("no hay crates collab* con rev en [patch.crates-io]")
if 'collab' in crates:
    print(crates['collab'])
else:
    # Mayoría como fallback
    most = Counter(crates.values()).most_common(1)[0][0]
    print(most)
PY
}

extract_editor_ref() {
  # $1 = ruta a frontend/appflowy_flutter/pubspec.yaml
  python3 - "$1" <<'PY'
import re, sys
lines = open(sys.argv[1]).read().splitlines(keepends=False)
# 1) Encontrar la línea con "dependency_overrides:" a indentación 0
do_idx = None
for i, ln in enumerate(lines):
    if re.match(r'^dependency_overrides:\s*$', ln):
        do_idx = i
        break
if do_idx is None:
    sys.exit("no hay seccion dependency_overrides en pubspec.yaml")
# 2) Dentro del bloque, encontrar la primera línea "  appflowy_editor:"
#    (2 espacios) que sea HIJA directa de dependency_overrides.
ae_idx = None
for i in range(do_idx + 1, len(lines)):
    ln = lines[i]
    if re.match(r'^  appflowy_editor:\s*$', ln):
        ae_idx = i
        break
    # Si encontramos otra clave raíz (0 espacios + ":") paramos
    if re.match(r'^\S+:', ln) and not re.match(r'^\s', ln):
        break
if ae_idx is None:
    sys.exit("no hay appflowy_editor en dependency_overrides")
# 3) A partir de ae_idx+1, capturar líneas con indent > 2 espacios y
#    buscar "ref: <valor>".
ref_val = None
for i in range(ae_idx + 1, len(lines)):
    ln = lines[i]
    # Fin del bloque appflowy_editor: línea con indent ≤ 2 y no vacía
    if ln and not ln.startswith('   '):  # <3 espacios = fuera del bloque
        break
    m = re.match(r'^\s*ref:\s*(.+?)\s*(?:#.*)?$', ln)
    if m:
        ref_val = m.group(1).strip().strip('"').strip("'")
        break
if ref_val is None:
    sys.exit("no hay .git.ref dentro de dependency_overrides.appflowy_editor")
print(ref_val)
PY
}

resolve_commit_via_clone() {
  # $1 = url, $2 = ref (SHA, branch o tag) → clona en /tmp, hace checkout y
  # devuelve el SHA completo por stdout. Necesario para refs (típicamente
  # cortas) que NO aparecen en `git ls-remote` pero sí son alcanzables en
  # el historial completo (es el caso típico de commits fijados por AppFlowy).
  local url="$1" ref="$2"
  local tmp; tmp=$(mktemp -d -t fetch_src_XXXXXX)
  trap "rm -rf '$tmp'" RETURN
  git clone --quiet "$url" "$tmp/repo" 2>/dev/null \
    || { rm -rf "$tmp"; return 1; }
  if ! git -C "$tmp/repo" checkout --quiet "$ref" 2>/dev/null; then
    rm -rf "$tmp"
    return 1
  fi
  local full
  full=$(git -C "$tmp/repo" rev-parse HEAD)
  echo "$full"
}

# ---------- core (T2) ----------
clone_or_checkout() {
  # $1 name, $2 url, $3 requested_ref, $4 method ("shallow"|"full"), $5 expected_commit
  local name="$1" url="$2" req_ref="$3" method="$4" exp_commit="$5"
  local dest="$SRC_ROOT/$name"
  if [ -d "$dest/.git" ]; then
    local cur; cur=$(git -C "$dest" rev-parse HEAD 2>/dev/null || echo none)
    if [ "$cur" = "$exp_commit" ]; then
      echo "  $name ya está en $cur — no-op" >&2
      echo "$exp_commit"
      return 0
    fi
    if [ "$FORCE" -eq 1 ]; then
      echo "  --force: borrando $dest (HEAD=$cur, solicitado=$exp_commit)" >&2
      rm -rf "$dest"
    elif [ -n "$req_ref" ]; then
      # Re-checkout: fetch + checkout del ref solicitado
      echo "  $name HEAD=$cur, fetching $req_ref y haciendo checkout..." >&2
      git -C "$dest" fetch --quiet --tags --force origin "$req_ref" 2>/dev/null \
        || git -C "$dest" fetch --quiet --tags --force origin 2>/dev/null \
        || die 2 "git fetch falló en $dest"
      git -C "$dest" checkout --quiet "$req_ref" \
        || die 2 "git checkout $req_ref falló en $dest"
    else
      die 4 "$name ya clonado en $cur, solicitado $exp_commit (use --force)"
    fi
  fi
  if [ ! -d "$dest/.git" ]; then
    echo "  clonando $name desde $url ($method)..." >&2
    if [ "$method" = "shallow" ] && [ -z "$req_ref" ]; then
      git clone --depth 1 --no-tags --filter=blob:none "$url" "$dest" \
        || die 2 "git clone falló para $name ($url)"
    else
      # full clone, luego checkout del ref
      git clone "$url" "$dest" \
        || die 2 "git clone falló para $name ($url)"
      if [ -n "$req_ref" ]; then
        git -C "$dest" checkout --quiet "$req_ref" \
          || die 2 "git checkout $req_ref falló en $dest"
      fi
    fi
  fi
  local final; final=$(git -C "$dest" rev-parse HEAD 2>/dev/null || echo none)
  [ "$final" = "$exp_commit" ] || die 3 "$name HEAD=$final ≠ esperado $exp_commit"
  echo "$final"
}

# ---------- JSON writer (T5) ----------
write_sources_json() {
  # $1 = timestamp ISO 8601
  # $2..$N = pares (name, data_json)
  local ts="$1"; shift
  local out_dir="$OUT_ROOT/_ledger"
  mkdir -p "$out_dir"
  local out="$out_dir/sources.json"
  python3 - "$ts" "$SKILL_ROOT" "$out" "$@" <<'PY'
import json, sys
ts, skill_root, out = sys.argv[1], sys.argv[2], sys.argv[3]
entries = []
i = 4
while i < len(sys.argv):
    name = sys.argv[i]
    data = json.loads(sys.argv[i+1])
    data["name"] = name
    data["cloned_at"] = ts
    data["path"] = f"SRC/{name}"
    data["commit_short"] = data["commit"][:7]
    entries.append(data)
    i += 2
doc = {
    "schema_version": 1,
    "generated_at": ts,
    "skill_root": skill_root,
    "sources": entries,
}
with open(out, "w") as f:
    json.dump(doc, f, indent=2, sort_keys=False)
    f.write("\n")
print(f"  escrito {out} ({len(entries)} entradas)")
PY
}

# ---------- main (T4) ----------
main() {
  require_cmd git
  require_cmd python3

  echo "[1/5] AppFlowy → $SRC_ROOT/appflowy"
  if [ "$DRY_RUN" -eq 1 ]; then
    APPFLOWY_METHOD="shallow"
    if [ -n "$APPFLOWY_REF" ]; then APPFLOWY_METHOD="full"; fi
    echo "DRYRUN appflowy url=$APPFLOWY_URL ref=${APPFLOWY_REF:-<default>}" >&2
  else
    # Para AppFlowy, si el usuario no pasó ref, hacemos shallow; el commit se
    # resuelve tras clonar (no antes, porque ls-remote sin red falla).
    if [ -n "$APPFLOWY_REF" ]; then
      APPFLOWY_METHOD="full"
    else
      APPFLOWY_METHOD="shallow"
    fi
    # Clonamos una vez, leemos HEAD y ese será el commit
    local appflowy_dest="$SRC_ROOT/appflowy"
    if [ ! -d "$appflowy_dest/.git" ] || [ "$FORCE" -eq 1 ]; then
      [ "$FORCE" -eq 1 ] && [ -d "$appflowy_dest" ] && rm -rf "$appflowy_dest"
      if [ "$APPFLOWY_METHOD" = "shallow" ]; then
        git clone --depth 1 --no-tags --filter=blob:none "$APPFLOWY_URL" "$appflowy_dest" \
          || die 2 "git clone falló para appflowy ($APPFLOWY_URL)"
      else
        git clone "$APPFLOWY_URL" "$appflowy_dest" \
          || die 2 "git clone falló para appflowy ($APPFLOWY_URL)"
        [ -n "$APPFLOWY_REF" ] && git -C "$appflowy_dest" checkout --quiet "$APPFLOWY_REF" \
          || die 2 "git checkout $APPFLOWY_REF falló en $appflowy_dest"
      fi
    fi
    APPFLOWY_COMMIT=$(git -C "$appflowy_dest" rev-parse HEAD)
    echo "  appflowy HEAD = $APPFLOWY_COMMIT" >&2
  fi

  echo "[2/5] Extrayendo rev de AppFlowy-Collab desde Cargo.toml"
  if [ "$DRY_RUN" -eq 1 ]; then
    echo "DRYRUN: no se ha clonado AppFlowy; extracción omitida" >&2
    echo "PLAN:"
    echo "  appflowy_url=$APPFLOWY_URL"
    echo "  collab_url=$COLLAB_URL"
    echo "  editor_url=$EDITOR_URL"
    echo "  src_root=$SRC_ROOT"
    echo "  out_root=$OUT_ROOT"
    return 0
  fi
  local cargo_toml="$SRC_ROOT/appflowy/frontend/rust-lib/Cargo.toml"
  [ -f "$cargo_toml" ] || die 1 "no existe $cargo_toml"
  COLLAB_REV=$(extract_collab_rev "$cargo_toml") || die 1 "extracción de rev Collab falló"
  echo "  collab rev (de Cargo.toml) = $COLLAB_REV" >&2

  echo "[3/5] Extrayendo ref de appflowy-editor desde pubspec.yaml"
  local pubspec_yaml="$SRC_ROOT/appflowy/frontend/appflowy_flutter/pubspec.yaml"
  [ -f "$pubspec_yaml" ] || die 1 "no existe $pubspec_yaml"
  EDITOR_REF=$(extract_editor_ref "$pubspec_yaml") || die 1 "extracción de ref editor falló"
  echo "  editor ref (de pubspec.yaml) = $EDITOR_REF" >&2

  echo "[4/5] Resolviendo commits remotos"
  # Para refs (típicamente SHA cortos) que NO aparecen en `git ls-remote`
  # pero sí son alcanzables en el historial, hacemos un clone completo en
  # /tmp para resolver el SHA de 40 chars. La alternativa (clonar el destino
  # directamente y verificar post-checkout) es equivalente y más eficiente,
  # pero esta estrategia mantiene la separación resolver/clonar.
  COLLAB_COMMIT=$(resolve_commit_via_clone "$COLLAB_URL" "$COLLAB_REV") \
    || die 2 "no se pudo resolver rev $COLLAB_REV a commit en $COLLAB_URL"
  echo "  collab commit = $COLLAB_COMMIT" >&2
  EDITOR_COMMIT=$(resolve_commit_via_clone "$EDITOR_URL" "$EDITOR_REF") \
    || die 2 "no se pudo resolver ref $EDITOR_REF a commit en $EDITOR_URL"
  echo "  editor commit = $EDITOR_COMMIT" >&2

  echo "[5/5] Clonando collab y editor en sus commits resueltos"
  clone_or_checkout collab "$COLLAB_URL" "$COLLAB_REV" full "$COLLAB_COMMIT" >/dev/null
  clone_or_checkout editor "$EDITOR_URL" "$EDITOR_REF" full "$EDITOR_COMMIT" >/dev/null

  # Genera timestamp UTC
  local ts
  ts=$(python3 -c 'import datetime; print(datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"))')

  # Construye payloads para sources.json
  local appflowy_data editor_ref_full collab_ref_full
  appflowy_data=$(python3 -c "import json; print(json.dumps({
    'url': '$APPFLOWY_URL',
    'requested_ref': '${APPFLOWY_REF:-default-branch}',
    'commit': '$APPFLOWY_COMMIT',
    'method': '$APPFLOWY_METHOD',
  }))")
  collab_ref_full="$COLLAB_REV-from-cargo-toml"
  local collab_data
  collab_data=$(python3 -c "import json; print(json.dumps({
    'url': '$COLLAB_URL',
    'requested_ref': '$COLLAB_REV-from-cargo-toml',
    'commit': '$COLLAB_COMMIT',
    'method': 'full',
    'evidence': {
      'cargo_toml_path': 'SRC/appflowy/frontend/rust-lib/Cargo.toml',
      'section': '[patch.crates-io]',
    },
  }))")
  local editor_data
  editor_data=$(python3 -c "import json; print(json.dumps({
    'url': '$EDITOR_URL',
    'requested_ref': '$EDITOR_REF-from-pubspec-yaml',
    'commit': '$EDITOR_COMMIT',
    'method': 'full',
    'evidence': {
      'pubspec_path': 'SRC/appflowy/frontend/appflowy_flutter/pubspec.yaml',
      'node': 'dependency_overrides.appflowy_editor.git.ref',
    },
  }))")

  write_sources_json "$ts" \
    "appflowy" "$appflowy_data" \
    "collab"    "$collab_data" \
    "editor"    "$editor_data"

  echo "OK: A1.1 (sources.json escrito, 3 fuentes)"
}

# ---------- entrypoint ----------
resolve_root
parse_args "$@"
main
