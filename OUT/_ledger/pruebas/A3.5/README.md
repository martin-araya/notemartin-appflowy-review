# pruebas/A3.5 — `build_index.py` (2026-10-18)

## Objetivo

Verificar que el generador del índice de la skill:

1. Recorre `OUT/` (excluyendo `.git`, `node_modules`, `_wip`,
   `fixtures`, `pruebas`), parsea el frontmatter de cada `.md` y
   construye un dict `id → ruta_rel`.
2. Extrae todas las referencias cruzadas `[[id]]` (excluyendo
   bloques ```código```) y las resuelve contra el dict.
3. Genera `00-INDEX.md` con 9 secciones: resumen, commits,
   cobertura de docs, cobertura de fuente, árbol, tabla de docs,
   mapa de enlaces, no resueltos, cómo regenerar.
4. Soporta `--check-links` (no escribe, sólo verifica), `--json`
   (machine-readable), `--quiet` y `--no-color`.

Materializa la prueba literal del ROADMAP A3.5:

> "genera `00-INDEX.md` (árbol, estado de cada doc, cobertura,
> commits de fuentes) y enlaces cruzados `<F..>` → rutas reales.
> Prueba: todos los enlaces del índice resuelven."

## Comandos

```bash
cd /Users/martin/Desktop/projects/Skills/notemartin-appflowy-review
bash OUT/_ledger/validate-A3.5.sh
```

## Salida (verbatim, 2026-10-18)

```
[2026-10-18T22:12:36Z]   OK  check 1: script ejecutable
[2026-10-18T22:12:36Z]   OK  check 2: --help imprime uso y sale 0
[2026-10-18T22:12:36Z]   OK  check 3: 00-INDEX.md contiene los 4 ids (A, B, C, 00-INDEX) en la tabla
[2026-10-18T22:12:36Z]   OK  check 4: sección 8 (no resueltos) contiene sólo NOEXISTE, no A ni B
[2026-10-18T22:12:36Z]   OK  check 5: sección 2 (Commits) menciona los 3 commit_short (5cf3a36, 4dfccef, 470c4e7)
[2026-10-18T22:12:36Z]   OK  check 6: sección 4 (cobertura fuente) muestra bloc, ui, GLOBAL=4/2=50.00%
[2026-10-18T22:12:36Z]   OK  check 7: --check-links exit 1 por [[NOEXISTE]]
[2026-10-18T22:12:36Z]   OK  check 8: --json produce JSON parseable con unresolved_count == 1
[2026-10-18T22:12:36Z]   OK  check 9: modo 'todo resuelto' (con D.md con id NOEXISTE) → --check-links exit 0
[2026-10-18T22:12:36Z]   OK  check 10: sección 5 (árbol) muestra los 4 docs
[2026-10-18T22:12:36Z] ---
[2026-10-18T22:12:36Z] resultado: 10/10 checks OK (0 fallidos)
[2026-10-18T22:12:36Z] OK: A3.5 (build_index.py funciona: genera 00-INDEX.md con árbol, estado, cobertura, commits; resuelve [[id]] → rutas reales)
exit=0
```

## Tabla de resultados

| # | Check | Esperado | Resultado |
|---|---|---|---|
| 1 | `SKILL/scripts/build_index.py` existe y es ejecutable | `test -x` | ✅ |
| 2 | `--help` imprime uso y sale 0 | exit 0 + grep `build_index.py` | ✅ |
| 3 | `00-INDEX.md` contiene los 4 ids (A, B, C, 00-INDEX) | grep 4 líneas | ✅ |
| 4 | Sección "no resueltos" contiene sólo `NOEXISTE` (no A ni B) | awk + grep | ✅ |
| 5 | Sección "Commits" menciona los 3 commit_short | grep 3 | ✅ |
| 6 | Cobertura de fuente: bloc, ui, GLOBAL=4/2=50.00% | grep | ✅ |
| 7 | `--check-links` exit 1 por `[[NOEXISTE]]` | exit 1 | ✅ |
| 8 | `--json` parseable con `unresolved_count == 1` | `python3 -m json.tool` | ✅ |
| 9 | Modo "todo resuelto" (con D.md con id `NOEXISTE`) → `--check-links` exit 0 | exit 0 | ✅ |
| 10 | Árbol muestra los 4 docs | grep | ✅ |

## Cobertura de la prueba literal del ROADMAP

| Frase del ROADMAP | Materializada en |
|---|---|
| "genera `00-INDEX.md`" | `render_index()` produce el Markdown con 9 secciones; check 3 (4 ids) + check 6 (cobertura). |
| "árbol" | Sección 5 (`build_tree`); check 10. |
| "estado de cada doc" | Sección 6 (tabla con `estado`); check 3. |
| "cobertura" | Secciones 3 (docs) y 4 (fuente, reusando lógica A3.4); check 6. |
| "commits de fuentes" | Sección 2 (de `sources.json`); check 5. |
| "enlaces cruzados `<F..>` → rutas reales" | `build_id_index()` + `extract_cross_refs()`; sección 7 (mapa) y 8 (no resueltos); check 4. |
| "todos los enlaces del índice resuelven" | check 4 (sección 8 sólo lista `NOEXISTE`); check 9 (modo "todo resuelto" → exit 0). |

## Fixtures

| Archivo | Contenido | Rol |
|---|---|---|
| `fixtures/A.md` | `id: A`, `estado: verificado`, body con `[[B]]` | Doc origen de ref válida |
| `fixtures/B.md` | `id: B`, `estado: pendiente`, body con `[[A]]` y `[[B]]` (self-ref) | Doc origen de ref válida + self-ref |
| `fixtures/C.md` | `id: C`, `estado: verificado`, body con `[[NOEXISTE]]` | Doc origen de ref rota |
| `fixtures/00-INDEX.md` | `id: 00-INDEX`, `estado: pendiente` (sobrescrito por el script) | El artefacto que el script regenera |
| `fixtures/_ledger/sources.json` | 3 fuentes (appflowy `5cf3a36`, collab `4dfccef`, editor `470c4e7`) | Para sección 2 del índice |
| `fixtures/_ledger/cobertura.csv` | 4 filas (2 verificado / 2 sin_asignar, capas bloc y ui) | Para sección 4 del índice |

## Salida (extracto, del `extract.log`)

```markdown
# 00 — Índice de la skill

## 1. Resumen

| Métrica | Valor |
|---|---|
| Documentos `.md` en `OUT/` | 4 |
| Documentos con `id` en frontmatter | 4 |
| Commits de fuentes | 3 |
| Cobertura de fuente (verificado) | 50.00% |
| Cobertura de docs (verificado) | 75.00% |
| Enlaces cruzados totales | 4 |
| Enlaces no resueltos | 1 |

## 2. Commits de fuentes

| Fuente | Commit | URL |
|---|---|---|
| appflowy | `5cf3a36` | https://github.com/AppFlowy-IO/AppFlowy |
| collab | `4dfccef` | https://github.com/AppFlowy-IO/AppFlowy-Collab |
| editor | `470c4e7` | https://github.com/AppFlowy-IO/appflowy-editor |

## 4. Cobertura de fuente

| capa | total | verificado | % |
|---|---:|---:|---:|
| bloc | 2 | 1 | 50.00% |
| ui | 2 | 1 | 50.00% |
| **GLOBAL** | **4** | **2** | **50.00%** |

## 7. Mapa de enlaces cruzados

| origen | → | destino |
|---|---|---|
| `A.md` (línea 4) | → | `B.md` (id `B`) |
| `B.md` (línea 4) | → | `A.md` (id `A`) |
| `B.md` (línea 4) | → | `B.md` (id `B`) |
| `C.md` (línea 4) | → | `✗ no resuelto` (`NOEXISTE`) |

## 8. Enlaces no resueltos

- `C.md:4` → `[[NOEXISTE]]` (id no encontrado en el out-dir)
```

## Diferencias detectadas vs el plan (corregidas en sitio)

1. **Cálculo de `pct` por capa en `load_cobertura`**: el plan
   asumía que el cálculo se hacía en `render_index`; la
   implementación lo hace en `load_cobertura` (más limpio, evita
   duplicación). Sin impacto funcional.
2. **Auto-referencia del índice**: el `00-INDEX.md` generado
   contiene la línea `[[NOEXISTE]]` en su sección "no resueltos",
   que el extractor de cross-refs identificaba como un nuevo
   enlace roto. Fix: `extract_cross_refs()` excluye el archivo
   `00-INDEX.md` del scan (es el artefacto generado, no producto).
3. **`out_dir_name` en árbol**: el árbol muestra el nombre del
   `out_dir` (p. ej. `fixtures/` o `OUT/`) como raíz, no siempre
   `OUT/`. Documentado.

## Requisitos externos

- Python 3 stdlib (sin dependencias externas).
- `sources.json` y `cobertura.csv` opcionales; si faltan, sus
  secciones muestran "(ausente)" en lugar de fallar.

## Cómo reproducir desde cero

```bash
cd /Users/martin/Desktop/projects/Skills/notemartin-appflowy-review
python3 SKILL/scripts/build_index.py --help
python3 SKILL/scripts/build_index.py --out-dir OUT/_ledger/pruebas/A3.5/fixtures
python3 SKILL/scripts/build_index.py --check-links --out-dir OUT/_ledger/pruebas/A3.5/fixtures
python3 SKILL/scripts/build_index.py --json --out-dir OUT/_ledger/pruebas/A3.5/fixtures
bash OUT/_ledger/validate-A3.5.sh
```

## Estado

**A3.5 cerrada. Cierre del Bloque A3 (Validadores): 5/5 fases
cerradas (A3.1..A3.5). Pasar a A4.1 (`assign_ledger.py`).**
