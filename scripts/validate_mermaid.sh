#!/usr/bin/env bash
# validate_mermaid.sh — extrae cada bloque ```mermaid de uno o varios
# archivos .md y los renderiza con mmdc (mermaid-cli). Falla con
# `archivo:bloque_nº` si algún bloque no parsea.
#
# Fase A3.1 de la skill `notemartin-appflowy-review`.
# Spec: ROADMAP.md líneas 83–93 y AGENTS.md §7.

set -u
set -o pipefail

SCRIPT_NAME=$(basename "$0")

# --- defaults ---
QUIET=0
KEEP=0
LIMIT=0
JOBS=1
NO_COLOR=0
MMDC_BIN_OVERRIDE=""
PUPPETEER_CONFIG=""

# Reintentos por bloque solo ante fallos de infraestructura de Puppeteer
# (ProtocolError / timeout). 3 intentos bastan para absorber la intermitencia
# observada sobre OUT/: la misma pasada daba 3 fallos y luego 0 sobre documentos
# que despues pasaban uno a uno.
MMDC_RETRIES=3
MMDC_RETRY_SLEEP=2

# --- counts (associative array not strictly needed; use plain vars) ---
TOTAL_OK=0
TOTAL_FAIL=0
FAIL_LINES=()
VERBOSE_LOG=""
DEBUG=0
INCLUDE_ALL=0

usage() {
  cat <<'USAGE'
Uso: validate_mermaid.sh [OPCIONES] PATH [PATH …]

PATH puede ser un archivo .md o un directorio (recursivo).

Opciones:
  -h, --help                Mostrar ayuda y salir (exit 0).
      --quiet               Sólo imprime resumen final; oculta "archivo: N bloques".
      --keep                Conserva SVG en <archivo>.mermaid/<n>.svg.
      --debug               Log estructurado a stderr con timestamps.
      --mmdc-bin PATH       Ruta explícita al binario mmdc.
      --puppeteer-config P  Pasa --puppeteerConfigFile a mmdc.
      --limit N             Procesa sólo los primeros N bloques mermaid por archivo (0 = sin límite).
      --jobs N              Procesa N archivos en paralelo (default 1).
      --no-color            Desactiva colores ANSI.
      --all                 Valida también OUT/_ledger/ y los meta-ficheros
                            (00-INDEX.md, STATE.md, 22-preguntas-abiertas.md).
                            Por defecto se excluyen: no son entregables y
                            OUT/_ledger/pruebas/A3.1/fixtures/ contiene
                            bloques rotos a propósito.

Exit codes:
  0  Todos los bloques mermaid renderizan OK.
  1  Al menos un bloque mermaid falló al renderizar.
  2  Error de uso (CLI) o mmdc no encontrado.

Formato de error por bloque:
  ERROR <ruta>:<n>: <primera línea de stderr de mmdc>

La numeración es 1-based y se aplica únicamente a los bloques etiquetados
`mermaid` (no a todos los fenced code blocks del archivo).
USAGE
}

color_red()   { [[ "$NO_COLOR" == "1" ]] && printf '%s' "$1" || printf '\033[31m%s\033[0m' "$1"; }
color_green() { [[ "$NO_COLOR" == "1" ]] && printf '%s' "$1" || printf '\033[32m%s\033[0m' "$1"; }
color_dim()   { [[ "$NO_COLOR" == "1" ]] && printf '%s' "$1" || printf '\033[2m%s\033[0m' "$1"; }

log_debug() {
  [[ "$DEBUG" == "1" ]] && printf '[%s] %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$*" >&2
}

# --- arg parsing ---
PATHS=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --quiet) QUIET=1 ;;
    --keep) KEEP=1 ;;
    --debug) DEBUG=1 ;;
    --mmdc-bin) MMDC_BIN_OVERRIDE="$2"; shift ;;
    --puppeteer-config) PUPPETEER_CONFIG="$2"; shift ;;
    --limit) LIMIT="$2"; shift ;;
    --jobs) JOBS="$2"; shift ;;
    --no-color) NO_COLOR=1 ;;
    --all) INCLUDE_ALL=1 ;;
    --) shift; while [[ $# -gt 0 ]]; do PATHS+=("$1"); shift; done ;;
    -*) printf '%s: opción desconocida: %s\n' "$SCRIPT_NAME" "$1" >&2; usage >&2; exit 2 ;;
    *) PATHS+=("$1") ;;
  esac
  shift
done

if [[ ${#PATHS[@]} -eq 0 ]]; then
  printf '%s: se requiere al menos un PATH\n' "$SCRIPT_NAME" >&2
  usage >&2
  exit 2
fi

# --- resolve mmdc ---
# Returns the path to mmdc (or empty + rc=1 on miss).
resolve_mmdc() {
  if [[ -n "$MMDC_BIN_OVERRIDE" ]]; then
    if [[ -x "$MMDC_BIN_OVERRIDE" ]]; then
      printf '%s' "$MMDC_BIN_OVERRIDE"
      return 0
    fi
    return 1
  fi
  if command -v mmdc >/dev/null 2>&1; then
    command -v mmdc
    return 0
  fi
  return 1
}

MMDC_BIN=$(resolve_mmdc) || {
  printf '%s: mmdc no encontrado. Instalar con:\n' "$SCRIPT_NAME" >&2
  printf '    npm i -g @mermaid-js/mermaid-cli\n' >&2
  printf 'o exportar --mmdc-bin /ruta/al/mmdc.\n' >&2
  exit 2
}

log_debug "mmdc bin: $MMDC_BIN"

# --- extract blocks from one .md file ---
# Output: prints each block on stdout separated by a NUL-like separator
# using a custom delimiter line "<<<MERMAID_BLOCK_N>>>" (we use awk).
extract_mermaid_blocks() {
  local md="$1"
  LC_ALL=C.UTF-8 awk '
    BEGIN { state=0; n=0; idx=0 }
    state==0 {
      if ($0 ~ /^```mermaid([[:space:]]|\{|$)/) {
        state=1; n++; idx=0; print "<<<MERMAID_BLOCK_" n ">>>"
        next
      }
      next
    }
    state==1 {
      if ($0 ~ /^```[[:space:]]*$/) { state=0; next }
      if (idx==0) { print; idx=1 } else { print }
    }
  ' "$md"
}

# --- process one .md file ---
process_md() {
  local md="$1"
  local tmpdir
  tmpdir=$(mktemp -d -t mermaid.XXXXXX)
  local file_ok=0
  local file_fail=0
  local block_idx=0
  local current_n=0
  local buf=""
  local total_blocks=0
  local i=0

  # First, count blocks (to enforce --limit)
  while IFS= read -r line; do
    if [[ "$line" =~ ^\<\<\<MERMAID_BLOCK_([0-9]+)\>\>\>$ ]]; then
      total_blocks=$(( total_blocks + 1 ))
    fi
  done < <(extract_mermaid_blocks "$md")

  log_debug "extract $md -> $total_blocks bloque(s)"

  # Stream blocks via a temp file
  local extract_file
  extract_file=$(mktemp -t mermaid.XXXXXX.txt)
  extract_mermaid_blocks "$md" > "$extract_file"

  local current_block=""
  local i=0
  while IFS= read -r line || [[ -n "$line" ]]; do
    if [[ "$line" =~ ^\<\<\<MERMAID_BLOCK_([0-9]+)\>\>\>$ ]]; then
      local new_i="${BASH_REMATCH[1]}"
      # Flush PREVIOUS block (still has the old i in scope).
      if [[ -n "$current_block" ]]; then
        render_block "$md" "$i" "$current_block" "$tmpdir" || true
        current_block=""
      fi
      i="$new_i"
      if [[ "$LIMIT" -gt 0 && "$i" -gt "$LIMIT" ]]; then
        log_debug "skip $md#$i (--limit $LIMIT)"
        break
      fi
      current_block=""
    else
      if [[ -n "$current_block" ]]; then
        current_block+=$'\n'"$line"
      else
        current_block="$line"
      fi
    fi
  done < "$extract_file"

  # flush last block
  if [[ -n "$current_block" ]]; then
    render_block "$md" "$i" "$current_block" "$tmpdir" || true
  fi

  rm -f "$extract_file"
  rm -rf "$tmpdir"

  if [[ "$QUIET" != "1" ]]; then
    if [[ $file_fail -gt 0 ]]; then
      printf '%s: %d bloques (%s / %s)\n' \
        "$md" "$total_blocks" \
        "$(color_green "${file_ok} OK")" \
        "$(color_red "${file_fail} FAIL")" >&2
    else
      printf '%s: %d bloques (%s)\n' "$md" "$total_blocks" \
        "$(color_green "${file_ok} OK")" >&2
    fi
  fi
}

# render one block. Returns 0 on success, 1 on failure.
render_block() {
  local md="$1"
  local n="$2"
  local body="$3"
  local tmpdir="$4"
  local mmd="${tmpdir}/block-${n}.mmd"
  local svg="${tmpdir}/block-${n}.svg"
  local err="${tmpdir}/block-${n}.err"

  printf '%s\n' "$body" > "$mmd"

  local start_s
  start_s=$(date +%s)

  # Reintentos. `mmdc` lanza un Chromium por bloque vía Puppeteer, y bajo carga
  # (791 bloques en paralelo sobre `OUT/`) el `Runtime.callFunctionOn` agota el
  # tiempo y devuelve
  #   ProtocolError: Runtime.callFunctionOn timed out
  # que NO es un error de sintaxis del diagrama. Sin reintento, el validador
  # reportaba entre 2 y 3 fallos distintos en cada pasada sobre los mismos
  # documentos que luego pasaban uno a uno, y el gate era intermitente. Solo se
  # reintenta cuando stderr delata un problema de infraestructura; un error de
  # parseo se falla en el acto, porque reintentar solo slowing.
  local rc=0
  local attempt
  for attempt in $(seq 1 "$MMDC_RETRIES"); do
    if [[ -n "$PUPPETEER_CONFIG" ]]; then
      "$MMDC_BIN" -i "$mmd" -o "$svg" --puppeteerConfigFile "$PUPPETEER_CONFIG" --quiet 2> "$err"
    else
      "$MMDC_BIN" -i "$mmd" -o "$svg" --quiet 2> "$err"
    fi
    rc=$?
    [[ $rc -eq 0 ]] && break
    if ! grep -qiE "timed out|TimeoutError|protocolTimeout|Connection closed|Target closed" "$err"; then
      break  # error real de diagrama: no insistir
    fi
    [[ "$attempt" -lt "$MMDC_RETRIES" ]] && sleep "$MMDC_RETRY_SLEEP"
  done

  local end_s
  end_s=$(date +%s)
  local dur=$(( end_s - start_s ))

  if [[ $rc -eq 0 ]]; then
    bump_counts 1 0
    file_ok=$(( file_ok + 1 ))
    [[ "$attempt" -gt 1 ]] && log_debug "render $md#$i exit=0 tras $attempt intentos (${dur}ms)"
    log_debug "render $md#$i -> mmdc exit=0 (${dur}ms)"
    if [[ "$KEEP" == "1" ]]; then
      local keepdir
      keepdir="$(dirname "$md")/$(basename "$md").mermaid"
      mkdir -p "$keepdir"
      cp -f "$svg" "$keepdir/${n}.svg" 2>/dev/null || true
    fi
    return 0
  else
    bump_counts 0 1
    file_fail=$(( file_fail + 1 ))
    local first_err
    first_err=$(awk 'NF{print; exit}' "$err" 2>/dev/null | tr -d '\n' | cut -c1-200)
    [[ -z "$first_err" ]] && first_err="mmdc failed (no stderr)"
    printf '%sERROR %s:%d: %s\n' \
      "$( [[ "$NO_COLOR" == "1" ]] || printf '\033[31m' )" \
      "$md" "$n" "$first_err" >&2
    [[ "$NO_COLOR" == "1" ]] || printf '\033[0m' >&2
    FAIL_LINES+=("$md:$n")
    log_debug "render $md#$n -> mmdc exit=$rc (${dur}ms) stderr: $first_err"
    return 1
  fi
}

# --- collect .md files ---
# Por defecto excluye `OUT/_ledger/` (cuaderno de trabajo de la skill) y los
# meta-ficheros, igual que `validate_template.py` y `validate_evidence.py`:
# `OUT/_ledger/pruebas/A3.1/fixtures/{broken,mixed}.md` son fixtures
# **deliberadamente rotos** que prueban que este script detecta fallos, y no
# entregables. Con `--all` se validan también.
collect_md_files() {
  local root="$1"
  if [[ -f "$root" ]]; then
    [[ "$root" =~ \.md$ ]] && printf '%s\n' "$root"
    return
  fi
  if [[ "${INCLUDE_ALL:-0}" == "1" ]]; then
    find "$root" -type f -name '*.md' \
      -not -path '*/.git/*' \
      -not -path '*/node_modules/*' \
      -not -path '*/_wip/*' \
      | sort
    return
  fi
  find "$root" -type f -name '*.md' \
    -not -path '*/.git/*' \
    -not -path '*/node_modules/*' \
    -not -path '*/_wip/*' \
    -not -path '*/_ledger/*' \
    -not -name '00-INDEX.md' \
    -not -name 'STATE.md' \
    -not -name '22-preguntas-abiertas.md' \
    | sort
}

# --- main ---
# Counter file used in parallel mode (and harmless in serial).
COUNTER_FILE=$(mktemp -t mermaid.XXXXXX.counts)
printf 'OK=0\nFAIL=0\n' > "$COUNTER_FILE"

# bumps OK/FAIL counters in COUNTER_FILE. Uses Python with fcntl locking
# for atomicity (macOS lacks flock). In serial mode, the lock is uncontended
# but still cheap.
bump_counts() {
  local ok_delta="$1"
  local fail_delta="$2"
  python3 - "$COUNTER_FILE" "$ok_delta" "$fail_delta" <<'PY'
import fcntl, sys, os, re
path, ok_d, fail_d = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
cur = {'OK': 0, 'FAIL': 0}
mode = 'r+' if os.path.exists(path) else 'w'
fd = os.open(path, os.O_RDWR | os.O_CREAT, 0o644)
try:
    fcntl.flock(fd, fcntl.LOCK_EX)
    if mode == 'r+':
        data = os.read(fd, 4096).decode('utf-8', 'replace')
        for line in data.splitlines():
            m = re.match(r'^(OK|FAIL)=(\d+)$', line.strip())
            if m: cur[m.group(1)] = int(m.group(2))
    cur['OK'] += ok_d
    cur['FAIL'] += fail_d
    os.lseek(fd, 0, 0)
    os.write(fd, f"OK={cur['OK']}\nFAIL={cur['FAIL']}\n".encode())
    os.ftruncate(fd, os.lseek(fd, 0, 1))
finally:
    fcntl.flock(fd, fcntl.LOCK_UN)
    os.close(fd)
PY
}

export COUNTER_FILE MMDC_BIN PUPPETEER_CONFIG QUIET KEEP LIMIT NO_COLOR DEBUG INCLUDE_ALL
export -f render_block extract_mermaid_blocks process_md log_debug collect_md_files bump_counts

if [[ "$JOBS" -gt 1 ]]; then
  TMP_LIST=$(mktemp -t mermaid.XXXXXX.list)
  for p in "${PATHS[@]}"; do
    collect_md_files "$p" >> "$TMP_LIST"
  done
  if [[ -s "$TMP_LIST" ]]; then
    xargs -I {} -P "$JOBS" bash -c 'process_md "$@"' _ {} < "$TMP_LIST"
  fi
  rm -f "$TMP_LIST"
else
  for p in "${PATHS[@]}"; do
    while IFS= read -r md; do
      [[ -n "$md" ]] && process_md "$md"
    done < <(collect_md_files "$p")
  done
fi

# Read aggregated counts.
TOTAL_OK=$(grep '^OK=' "$COUNTER_FILE" | cut -d= -f2)
TOTAL_FAIL=$(grep '^FAIL=' "$COUNTER_FILE" | cut -d= -f2)
TOTAL_OK=${TOTAL_OK:-0}
TOTAL_FAIL=${TOTAL_FAIL:-0}
rm -f "$COUNTER_FILE" "$COUNTER_FILE.lock"

# --- summary ---
if [[ "$QUIET" == "1" ]]; then
  printf 'OK=%d FAIL=%d\n' "$TOTAL_OK" "$TOTAL_FAIL"
else
  printf -- '--- summary: ok=%d fail=%d ---\n' "$TOTAL_OK" "$TOTAL_FAIL" >&2
fi

[[ $TOTAL_FAIL -gt 0 ]] && exit 1 || exit 0
