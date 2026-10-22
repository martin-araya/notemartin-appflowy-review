# pruebas/A3.1 — `validate_mermaid.sh` (2026-10-18)

## Objetivo

Verificar que el validador de Mermaid de la skill:

1. Extrae cada bloque ` ```mermaid ` de un `.md` (y **solo** esos, no
   otros fenced code blocks).
2. Los renderiza con `mmdc` (mermaid-cli).
3. Si un diagrama falla, sale con código 1 e imprime una línea
   `ERROR <archivo>:<n>: <primera línea de stderr de mmdc>`.
4. La numeración `n` es 1-based y cuenta únicamente bloques `mermaid`.

Materializa la prueba literal del ROADMAP A3.1:

> "extrae cada bloque ```mermaid de un `.md` y lo renderiza con `mmdc`.
> Prueba: un diagrama roto falla con archivo y número de bloque."

## Comandos

```bash
cd /Users/martin/Desktop/projects/Skills/notemartin-appflowy-review
bash OUT/_ledger/validate-A3.1.sh
```

## Salida (verbatim, 2026-10-18)

```
[2026-10-18T21:29:54Z]   OK  check 1: script ejecutable
[2026-10-18T21:29:54Z]   OK  check 2: --help imprime uso y sale 0
[2026-10-18T21:29:54Z]   OK  check 3: positive.md exit 0
[2026-10-18T21:29:55Z]   OK  check 4: broken.md exit 1 con archivo:bloque_nº en stderr
[2026-10-18T21:29:57Z]   OK  check 5: mixed.md exit 1 identificando bloque 4 (no 1/2/3)
[2026-10-18T21:29:57Z]   OK  check 6: --quiet en positive.md: exit 0, stdout ≤ 4 líneas con OK=
[2026-10-18T21:29:57Z]   OK  check 7: nº de líneas ERROR = nº de bloques fallidos (mixed.md: 1)
[2026-10-18T21:30:00Z]   OK  check 8: modo directorio: 3 archivos, ok=4 fail=2
[2026-10-18T21:30:00Z] ---
[2026-10-18T21:30:00Z] resultado: 8/8 checks OK (0 fallidos)
[2026-10-18T21:30:00Z] OK: A3.1 (validate_mermaid.sh funciona: extrae bloques mermaid, renderiza con mmdc, reporta archivo:bloque_nº en fallos)
exit=0
```

## Tabla de resultados

| # | Check | Esperado | Resultado |
|---|---|---|---|
| 1 | Script `SKILL/scripts/validate_mermaid.sh` existe y es ejecutable | `test -x` OK | ✅ |
| 2 | `--help` imprime uso y sale 0 | exit 0 + grep `Uso:` | ✅ |
| 3 | `fixtures/positive.md` → exit 0 | exit 0 | ✅ |
| 4 | `fixtures/broken.md` → exit 1 + stderr `ERROR broken.md:N:` | exit 1 + match | ✅ |
| 5 | `fixtures/mixed.md` → exit 1 + stderr `ERROR mixed.md:4:` (no :1/:2/:3) | exit 1 + match | ✅ |
| 6 | `--quiet fixtures/positive.md` → exit 0, stdout ≤ 4 líneas con `OK=` | exit 0 + match | ✅ |
| 7 | Nº de líneas `ERROR archivo:N:` en stderr = nº de bloques fallidos | 1 (mixed) | ✅ |
| 8 | Modo directorio: 3 archivos, summary `ok=4 fail=2` | match | ✅ |

## Cobertura de la prueba literal del ROADMAP

| Frase del ROADMAP | Materializada en |
|---|---|
| "extrae cada bloque ```mermaid de un `.md`" | `extract_mermaid_blocks()` (awk en `validate_mermaid.sh:108-130`); verificado por check 5 (4 bloques en `mixed.md`, 1 bloque en `positive.md`, 1 en `broken.md`). |
| "y lo renderiza con `mmdc`" | `render_block()` invoca `mmdc -i … -o …`; verificado por checks 3, 4, 5, 8. |
| "un diagrama roto falla con archivo y número de bloque" | check 4 (`broken.md:1`); check 5 (numeración correcta entre varios bloques: `mixed.md:4`, no `1`/`2`/`3`). |

## Fixtures

| Archivo | Bloques mermaid | Esperado | Resultado |
|---|---:|---|---|
| `fixtures/positive.md` | 1 (correcto) | exit 0 | ✅ |
| `fixtures/broken.md` | 1 (sintaxis inválida: `["Inicio` sin cerrar) | exit 1 + frontend/resources/translations/es-VE.json:1 | ✅ |
| `fixtures/mixed.md` | 4 (3 correctos + 1 roto en posición 4) | exit 1 + frontend/resources/translations/es-VE.json:4 solamente | ✅ |

Total: 6 bloques; 4 OK / 2 FAIL.

## Diferencias detectadas vs el plan (corregidas en sitio)

1. **Bug del offset de bloque**: en el primer pase, cuando se leía un
   nuevo marcador `<<<MERMAID_BLOCK_N>>>` el script actualizaba `i` antes
   de hacer flush del bloque anterior, lo que renumeraba el bloque
   previo con el número del siguiente. Resultado: `mixed.md` se quedaba
   con sólo 3 renders logueados en lugar de 4 y la numeración
   quedaba desfasada. Corregido: capturar `new_i` en variable local,
   hacer flush con el `i` previo, después actualizar `i`. Verificado
   en `extract.log` línea 7 (render `mixed.md#1` ahora presente).

2. **Compatibilidad de `flock`**: macOS no incluye `flock(1)`. El plan
   original proponía usarlo para el contador paralelo. Sustituido por
   un wrapper Python con `fcntl.flock` (POSIX), atómico y portable.
   En modo serial (default) la operación es trivialmente correcta.

3. **Encadenamiento de formatos en `printf`**: el formato del summary
   empezaba con `---` literal, lo que algunos `printf` (con getopt
   interno) interpretaban como fin de opciones. Corregido a
   `printf -- '--- summary: …'`.

4. **Destino del error de `mmdc`**: con `--quiet`, los errores van a
   stderr pero la primera línea suele estar vacía. Cambiado
   `head -1` por `awk 'NF{print; exit}'` (primera línea no vacía).

5. **Edge case del exit code de `[[ ]]` dentro de `$( … )`**: el
   subshell `$( [[ "$NO_COLOR" == "1" ]] || printf '\033[31m' )` usa
   la convención de capturar stdout, no exit code. Funciona pero
   podría confundir; sin impacto.

## Requisitos externos

- `mmdc` (mermaid-cli ≥ 8.x) en `PATH`. Instalación:
  `npm i -g @mermaid-js/mermaid-cli`. Detectado en este entorno:
  `/Users/martin/.local/bin/mmdc` (versión 12.0.0).
- macOS usa Chromium vía Puppeteer (instalado por npm con
  `--allow-scripts` o como dependencia del paquete).

Si `mmdc` no está, `validate-A3.1.sh` sale con `exit=77` y mensaje
accionable (no falla con error críptico).

## Cómo reproducir desde cero

```bash
cd /Users/martin/Desktop/projects/Skills/notemartin-appflowy-review
npm i -g @mermaid-js/mermaid-cli
bash SKILL/scripts/validate_mermaid.sh --help
bash SKILL/scripts/validate_mermaid.sh OUT/_ledger/pruebas/A3.1/fixtures
bash OUT/_ledger/validate-A3.1.sh
```

## Estado

**A3.1 cerrada. Pasar a A3.2 (`validate_evidence.py`).**
