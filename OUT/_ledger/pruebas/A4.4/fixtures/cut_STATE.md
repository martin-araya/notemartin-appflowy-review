# STATE — `notemartin-appflowy-review`

> Estado de la ejecución. Se actualiza al cerrar **cada** fase (A4.4). Permite reanudar la skill en cualquier sesión o herramienta (Hermes ↔ Cline ↔ Kilo Code) leyendo este fichero + `_ledger/cobertura.csv`.

## Última fase cerrada

**A4.3 — Contratos de subagente (test fixture)** ✅ (2026-10-18)

**Cierre Bloque A4 parcial: A4.1 + A4.2 + A4.3. Falta A4.4 (STATE/reanudación). Previo: Bloque A1 + A2.1..A2.7 + A3.1..A3.5 + A4.1 + A4.2.**

## Última fase por abrir

A4.4 — `STATE.md` y reanudación (el orquestador puede retomar desde cualquier fase leyendo `STATE.md` + ledger; corte y reanudación cross-herramienta).

## Índice de fases

| Fase | Bloque | Estado | Fecha | Notas |
|---|---|---|---|---|
| A0.1 — Estructura de carpetas | A0 | ✅ | 2026-10-08 | `tree SKILL` coincide con `AGENTS.md §2`. |
| A0.0 — Reconstruir `PROMPT.md` (fase nueva) | A0 | ✅ | 2026-10-18 | Derivado de `AGENTS.md`+`ROADMAP.md`. Marcado como "consolidar en fase posterior" al inicio del fichero. |
| A0.2 — `SKILL.md` | A0 | ✅ | 2026-10-18 | `SKILL/SKILL.md` (177 líneas, ≤ 500) + `SKILL/AGENTS.md` (copia) + `PROMPT.md` (reconstruido, 341 líneas). |
| A0.3 — References | A0 | ✅ | 2026-10-18 | 6 ficheros en `SKILL/references/` (R-001..R-006), 562 líneas, validador `OUT/_ledger/validate-A0.3.sh` OK. |
| A0.4 — Esqueleto de salida | A0 | ✅ | 2026-10-18 | `SKILL/templates/output-skeleton/` con 55 `.md` + 27 directorios + 21 `.gitkeep`, validador `OUT/_ledger/validate-A0.4.sh` OK. |
| A1.1 — `fetch_sources.sh` | A1 | ✅ | 2026-10-18 | Gate. `SKILL/scripts/fetch_sources.sh` (≈ 280 líneas, bash+python3) + `OUT/_ledger/sources.json` con 3 entradas (appflowy `5cf3a36`, collab `4dfccef`, editor `470c4e7`); validador `OUT/_ledger/validate-A1.1.sh` OK. Plan en `1792331925242-fase-a1-1-fetch-sources-plan.md`. |
| A1.2 — `inventory.py` | A1 | ✅ | 2026-10-18 | `SKILL/scripts/inventory.py` (Python 3 stdlib) + `OUT/_ledger/inventario.json` (4.603 archivos, 671.876 LOC, 23.8 MB) + `assets.json` (1.186 binarios). Conteos `find` y `inventario` coinciden (.rs=1025, .dart=2581). Validador `OUT/_ledger/validate-A1.2.sh` OK. Plan en `1792331925242-fase-a1-2-inventory-plan.md`. |
| A1.3 — Esquema del ledger | A1 | ✅ | 2026-10-18 | `SKILL/scripts/init_ledger.py` (Python 3 stdlib) + `OUT/_ledger/cobertura.csv` (4.603 filas, 7 columnas, todas `estado=sin_asignar`); validador `OUT/_ledger/validate-A1.3.sh` OK. Plan en `1792331925242-fase-a1-3-ledger-plan.md`. **Cierra el Bloque A1.** |
| A2.1 — `extract_events.py` | A2 | ✅ | 2026-10-18 | `SKILL/scripts/extract_events.py` (Python 3 stdlib, 350 líneas) + `OUT/_ledger/extract/events.json` (4.150 líneas, 140 KB; 8 crates, 229 variantes, 224 registradas, 5 `sin_handler` legítimas) + validador `OUT/_ledger/validate-A2.1.sh` (11 checks, `exit=0`). Casos del ROADMAP (`flowy-document::CreateDocument`, `flowy-document::OpenDocument`) verificados. Plan en `1792333525128-fase-a2-1-extract-events.md`. |
| A2.2 — `extract_protobuf.py` | A2 | ✅ | 2026-10-18 | `SKILL/scripts/extract_protobuf.py` (Python 3 stdlib) + `OUT/_ledger/extract/protobuf.json` (22.412 líneas, 616 KB; 10 crates, 439 entidades = 389 structs + 50 enums, 1.030 campos, 158 `one_of`) + cruce con `events.json` (141 inputs + 84 outputs únicos, 0 `missing`) + validador `OUT/_ledger/validate-A2.2.sh` (8 checks, `exit=0`). Plan en `1792333525128-fase-a2-2-extract-protobuf.md`. |
| A2.3 — `extract_notifications.py` | A2 | ✅ | 2026-10-18 | `SKILL/scripts/extract_notifications.py` (Python 3 stdlib) + `OUT/_ledger/extract/notifications.json` (1.608 líneas, 48 KB; 6 enums Rust con 70 variantes + 16 emitters + 5 parsers Dart + 29 listeners) + cruce Rust↔Dart (`DocumentNotification` 5 variantes / 3 con listener; 0 `source_mismatches`) + validador `OUT/_ledger/validate-A2.3.sh` (7 checks, `exit=0`). Plan en `1792333525128-fase-a2-3-extract-notifications.md`. |
| A2.4 — `extract_blocs.py` | A2 | ✅ | 2026-10-18 | `SKILL/scripts/extract_blocs.py` (Python 3 stdlib) + `OUT/_ledger/extract/blocs.json` (9.369 líneas, 268 KB; 142 blocs = 125 Bloc + 17 Cubit; 33 en `plugins/database/application/`) con eventos freezed+sealed cross-file + validador `OUT/_ledger/validate-A2.4.sh` (8 checks, `exit=0`). Plan en `1792333525128-fase-a2-4-extract-blocs.md`. |
| A2.5 — `extract_deps.py` | A2 | ✅ | 2026-10-18 | `SKILL/scripts/extract_deps.py` (Python 3 stdlib + `tomli`) + `OUT/_ledger/extract/deps.json` (3.644 líneas, 104 KB; Rust: 31 crates, 150 internal edges, 368 external deps; Dart: 8 packages, 12 internal edges, 326 resueltos en lock; 38 workspace.dependencies) + bloques Mermaid para Rust y Dart + validador `OUT/_ledger/validate-A2.5.sh` (9 checks, `exit=0`). Plan en `1792333525128-fase-a2-5-extract-deps.md`. |
| A2.6 — `extract_misc.py` | A2 | ✅ | 2026-10-18 | `SKILL/scripts/extract_misc.py` (Python 3 stdlib) + `OUT/_ledger/extract/misc.json` (13.540 líneas, 504 KB; 6 bloques: 35 routes, 13 shortcuts, 9 feature_flags, 133 error_codes `#[repr(u8)]`, 1.637 i18n_keys, 15 startup_tasks en orden) + validador `OUT/_ledger/validate-A2.6.sh` (10 checks, `exit=0`). Plan en `1792333525128-fase-a2-6-extract-misc.md`. |
| **A2.7 — `extract_codegen.sh`** | A2 | ✅ | 2026-10-18 | `SKILL/scripts/extract_codegen.sh` (bash + python3) + `OUT/_ledger/pruebas/A2.7/codegen-result.json` (2.6 KB; outcome=`failed`) + `codegen-fallido.md` (2.8 KB) + validador `OUT/_ledger/validate-A2.7.sh` (7 checks, `exit=0`). Caso (b) del ROADMAP: toolchain incompleto (`cargo-make`/`protoc`/`protoc-gen-dart` ausentes, sin `Makefile.toml`, `flowy-codegen` es lib sin binario). A2.2 es independiente y ya pasó. Plan en `1792333525128-fase-a2-7-codegen.md`. |
| **A2.6 — `extract_misc.py`** | A2 | ✅ | 2026-10-18 | `SKILL/scripts/extract_misc.py` (Python 3 stdlib) + `OUT/_ledger/extract/misc.json` (13.540 líneas, 504 KB; 6 bloques: 35 routes, 13 shortcuts, 9 feature_flags, 133 error_codes `#[repr(u8)]`, 1.637 i18n_keys, 15 startup_tasks en orden) + validador `OUT/_ledger/validate-A2.6.sh` (10 checks, `exit=0`). Plan en `1792333525128-fase-a2-6-extract-misc.md`. |
| **A3.1 — `validate_mermaid.sh`** | A3 | ✅ | 2026-10-18 | `SKILL/scripts/validate_mermaid.sh` (bash + awk + python3 stdlib para fcntl, 350 líneas) + 3 fixtures en `OUT/_ledger/pruebas/A3.1/fixtures/` (positive/broken/mixed) + `OUT/_ledger/validate-A3.1.sh` (8 checks, `exit=0`). Extrae bloques `mermaid` con `awk`, los renderiza con `mmdc -i … -o …`, reporta `ERROR <archivo>:<n>` con n=1-based sólo sobre bloques `mermaid`. Soporta `--quiet`, `--keep`, `--limit N`, `--jobs N`, `--no-color`, `--mmdc-bin PATH`, `--puppeteer-config PATH`. Plan en `1792358647985-fase-a3-1-validate-mermaid.md`. **Abre el Bloque A3 (Validadores).** |
| **A3.2 — `validate_evidence.py`** | A3 | ✅ | 2026-10-18 | `SKILL/scripts/validate_evidence.py` (Python 3 stdlib, 300 líneas) + 4 fixtures en `OUT/_ledger/pruebas/A3.2/fixtures/` (valid/fake_path/out_of_range/mixed) + `OUT/_ledger/validate-A3.2.sh` (9 checks, `exit=0`). Encuentra refs `[fuente:]ruta:línea[–fin]` con state machine (excluye fenced blocks), valida 4 condiciones: archivo en inventario, fuente válida, línea/rango en archivo real, `inicio ≤ fin`. 4 códigos de error (`E_PATH_NOT_IN_INVENTORY`, `E_FUENTE_MISMATCH`, `E_LINE_OUT_OF_RANGE`, `E_RANGE_INVERTED`). Soporta `--json`, `--quiet`, `--no-color`, `--inventario PATH`. Plan en `1792358647985-fase-a3-2-validate-evidence.md`. |
| **A3.3 — `validate_template.py`** | A3 | ✅ | 2026-10-18 | `SKILL/scripts/validate_template.py` (Python 3 stdlib, ~440 líneas) + 6 fixtures en `OUT/_ledger/pruebas/A3.3/fixtures/` (valid_feature, valid_export, missing_section_13, missing_frontmatter, bad_estado, out_of_order) + `OUT/_ledger/validate-A3.3.sh` (10 checks, `exit=0`). Parsea frontmatter YAML custom (sin PyYAML) y valida 5 campos obligatorios; auto-detecta plantilla por prefijo del `id` (`Fxx.y` → feature 19 secciones; `B4.N` → export 11 secciones); valida orden, duplicados, huecos y secciones vacías. 11 códigos de error. Soporta `--template feature|export`, `--json`, `--quiet`, `--no-color`, `--allow-extra-sections`. Plan en `1792358647985-fase-a3-3-validate-template.md`. |
| **A3.4 — `validate_coverage.py`** | A3 | ✅ | 2026-10-18 | `SKILL/scripts/validate_coverage.py` (Python 3 stdlib, ~280 líneas) + 4 fixtures CSV en `OUT/_ledger/pruebas/A3.4/fixtures/` (toy_50pct/toy_100pct/toy_0pct/toy_multi_capa) + `OUT/_ledger/validate-A3.4.sh` (10 checks, `exit=0`). Lee `cobertura.csv`, calcula % global y por capa de archivos en `verificado`, agrupa por `capa`, lista faltantes (`sin_asignar` y `pendiente`) con `--limit N` (default 50). Tabla Markdown + JSON. Soporta `--threshold N` (default 100) para gate de CI. Exit 0/1 según threshold. Modo real sobre `cobertura.csv` actual reporta 0% con 4.603 sin_asignar. Plan en `1792358647985-fase-a3-4-validate-coverage.md`. |
| **A3.5 — `build_index.py`** | A3 | ✅ | 2026-10-18 | `SKILL/scripts/build_index.py` (Python 3 stdlib, ~420 líneas) + 6 fixtures en `OUT/_ledger/pruebas/A3.5/fixtures/` (A.md, B.md, C.md, 00-INDEX.md, _ledger/sources.json, _ledger/cobertura.csv) + `OUT/_ledger/validate-A3.5.sh` (10 checks, `exit=0`). Recorre `OUT/`, parsea frontmatter (reusando parser YAML de A3.3), construye `id → ruta_rel`, extrae refs `[[X]]` (excluyendo fenced blocks y el propio `00-INDEX.md`), genera `00-INDEX.md` con 9 secciones: resumen, commits, cobertura de docs, cobertura de fuente, árbol, tabla de docs, mapa de enlaces, no resueltos, cómo regenerar. Soporta `--check-links`, `--json`, `--quiet`, `--no-color`, `--out`, `--out-dir`. Modo "todo resuelto" verificado con D.md con id `NOEXISTE` → exit 0. Plan en `1792358647985-fase-a3-5-build-index.md`. **Cierre del Bloque A3.** |
| **A4.1 — `assign_ledger.py`** | A4 | ✅ | 2026-10-18 | `SKILL/scripts/assign_ledger.py` (Python 3 stdlib, ~660 líneas) + 5 fixtures en `OUT/_ledger/pruebas/A4.1/fixtures/` (toy_inventario.json con 32 archivos, toy_ledger.csv, expected_ledger.csv, verified_ledger.csv, expected_verified_ledger.csv) + `OUT/_ledger/validate-A4.1.sh` (8 checks, `exit=0`). Implementa matching por reglas de ruta de `PROMPT.md §4` (líneas 143–159) extendidas con F00/F18/F19/F20 para cubrir infraestructura compartida; 188 patrones compilados. Reescribe `cobertura.csv` poblando `feature_ids` y moviendo `sin_asignar → pendiente`; preserva `verificado`. Genera `OUT/_ledger/sin_asignar.{md,json}` para triage B0.2. Precedencia por longitud de prefijo (F14 > F17 para `localization.dart`). Soporta `--dry-run`, `--min-coverage`, `--strict`, `--json`, `--quiet`, `--no-color`. Cobertura real **92.96 %** (4.279/4.603; 324 `sin_asignar`). Plan en `1792363730747-assign-ledger-a41.md`. **Abre el Bloque A4.** |
| **A4.2 — `build_units.py` + `validate_units.py`** | A4 | ✅ | 2026-10-18 | `SKILL/scripts/build_units.py` (Python 3 stdlib, ~480 líneas) + `SKILL/scripts/validate_units.py` (~140 líneas) + 2 fixtures en `OUT/_ledger/pruebas/A4.2/fixtures/` (toy_ledger.csv con 51 filas, expected_units/ con 7 unidades regeneradas en cada corrida) + `OUT/_ledger/validate-A4.2.sh` (7 checks, `exit=0`). Genera `OUT/_ledger/units/<id>.json` (88 unidades reales + `_index.json`) por feature/sub-feature; las features con > 120 archivos se subdividen siguiendo la tabla de ROADMAP B3.F01 (10 sub-unidades) y B3.F02 (13 sub-unidades) y por afinidad estructural para F00/F05/F09/F16/F19. Sub-división a un solo nivel para evitar explosión combinatoria de IDs. Suma exacta: **4.279 archivos en unidades = 4.279 asignados**, sin solapamiento. Soporta `--max-files`, `--no-split`, `--include LIST`, `--quiet`, `--no-color`, `--json`. F10 (0 archivos) queda en `features_vacias`. Plan en `1792363730747-build-units-a42.md`. |
| **A4.3 — Contratos de subagente** | A4 | ✅ | 2026-10-18 | 3 archivos en `SKILL/references/` (`subagent-contract.md` con los 4 esquemas JSON: `AutorInput`, `AutorOutput`, `RevisorInput`, `RevisorOutput` + reglas duras; `subagent-autor-prompt.md`; `subagent-revisor-prompt.md`) + `SKILL/scripts/run_subagent.py` (mock determinista ~360 líneas, modos `autor` y `revisor`) + 1 fixture en `OUT/_ledger/pruebas/A4.3/fixtures/` (`trivial_unit.json` = F11 con 2 archivos) + `OUT/_ledger/validate-A4.3.sh` (9 checks, `exit=0`). El mock produce un documento estructuralmente válido (19 secciones, 3 placeholders Mermaid) y el revisor ejecuta los 3 validadores reales (`validate_evidence`, `validate_template`, `validate_mermaid`) sobre él, devolviendo `veredicto: aprobado` con 0 correcciones. Tabla de muestreo del revisor: 30 % por defecto, 100 % para F01/F02/F06 y motor export/import (B4.*). Prompts referenciados desde `SKILL.md:105-106` (ya existían los placeholders). Plan en `1792363730747-subagent-contracts-a43.md`. |

## Pruebas

### pruebas/A0.2/ — Carga y disparo de la skill (2026-10-18)

**Objetivo:** verificar que `SKILL/SKILL.md` se carga en Hermes, Cline y Kilo Code, queda listada por nombre y se dispara con el prompt canónico.

**Validación estática (ejecutada en este entorno, sin agentes externos):**

| # | Check | Resultado |
|---|---|---|
| 1 | Frontmatter abre y cierra con `---` (líneas 1 y 4) | ✅ |
| 2 | `name: notemartin-appflowy-review` presente | ✅ |
| 3 | `description:` no vacía y ≥ 6 verbos de disparo | ✅ — contiene: revisa, documenta, auditoría, análisis, mapea, ingeniería inversa, informe técnico |
| 4 | `wc -l SKILL/SKILL.md` ≤ 500 | ✅ — 177 líneas |
| 5 | §3 (8 etapas) tiene 8 filas | ✅ |
| 6 | §8 (referencias) tiene 8 filas en `pendiente` | ✅ |
| 7 | `SKILL/AGENTS.md` byte-a-byte = `AGENTS.md` | ✅ — `diff -q` sin salida, 205 líneas idénticas |
| 8 | `PROMPT.md` existe y tiene ≥ 7 secciones `## ` | ✅ — 41 secciones `## `, 341 líneas |
| 9 | Referencias cruzadas a `PROMPT.md`/`AGENTS.md`/`ROADMAP.md` | ✅ — 19 menciones en `SKILL.md` |
| 10 | Sin emojis decorativos (solo notación funcional 🔒/🔀 ya usada en `AGENTS.md`/`ROADMAP.md`) | ✅ |

**Prompt de prueba canónico** (extraído de `SKILL/SKILL.md §9`):

```
Revisa AppFlowy completo. Quiero OUT/appflowy-review/ con la
arquitectura global, todas las features documentadas con diagramas
Mermaid, el motor colaborativo, la persistencia, la búsqueda, la IA
y el motor de exportación/importación. Idioma español, evidencia
ruta:línea, cobertura verificable por ledger.
```

**Resultado de la prueba en agente (Kilo Code, sesión actual):**

- El agente (Kilo Code) cargó `SKILL/SKILL.md` correctamente y respondió a las solicitudes del orquestador siguiendo el router (§3 etapas 0–7, §4 orquestación, §5 reanudación, §8 punteros). El propio hecho de que las tareas T1–T7 de este plan se ejecutaron con éxito aplicando las reglas de `AGENTS.md` citadas desde `SKILL.md §2` y `§8` confirma que el router funciona.
- Hermes Agent y Cline: no se pudieron cargar en este entorno. La validación queda pendiente de repetición manual en ambas herramientas. Resultado esperado al cargar: la skill aparece listada por `name: notemartin-appflowy-review` y el prompt canónico la dispara devolviendo un plan que arranca por la Etapa 0 (A0 ya completa) y propone A0.3 / A0.4.

**Criterio de aprobación (del `ROADMAP.md`):**

> cargarla en Hermes, Cline y Kilo Code; las tres la listan y la disparan con "revisa AppFlowy completo".

**Estado:** aprobación parcial (1 de 3 agentes verificado en este entorno; 2 pendientes de prueba manual). Se documenta en `OUT/22-preguntas-abiertas.md` como punto a cerrar antes de A0.3.

### pruebas/A0.3/ — `SKILL/references/` (2026-10-18)

**Objetivo:** verificar que los 6 documentos de referencia existen, sin secciones vacías, con frontmatter A3.3 y con la numeración de secciones exigida por la prueba de la fase (`feature-template.md` ≥ 19, `export-template.md` ≥ 11).

**Ejecutar:**

```bash
OUT/_ledger/validate-A0.3.sh
```

**Salida (2026-10-18):**

```
OK: A0.3 (6 referencias, 20 secciones en feature-template, 11 en export-template, frontmatter completo, sin secciones vacías)
exit=0
```

**Resultado por fichero:**

| Fichero | Líneas | Frontmatter A3.3 | Secciones `## ` | Notas |
|---|---|---|---|---|
| `repo-map.md` | 80 | ✅ | 5 | snapshot de `AGENTS.md §4` |
| `patterns.md` | 74 | ✅ | 8 | 7 patrones ampliados |
| `evidence-rules.md` | 56 | ✅ | 4 | 5 reglas + 3 ejemplos |
| `diagram-conventions.md` | 160 | ✅ | 5 | 6 tipos Mermaid + esqueletos |
| `feature-template.md` | 104 | ✅ | 24 (20 numeradas) | 19 obligatorias + 1 opcional |
| `export-template.md` | 88 | ✅ | 16 (11 numeradas) | 11 obligatorias |

`SKILL/SKILL.md §8` actualizado: las 6 filas pasan de `pendiente` a `✅ disponible`. Las 2 filas de prompts de subagente (A4.3) siguen en `pendiente`.

### pruebas/A0.4/ — `templates/output-skeleton/` (2026-10-18)

**Objetivo:** verificar que el esqueleto de salida existe, contiene 55 `.md` con frontmatter mínimo, los 27 directorios del árbol y los `.gitkeep` en las carpetas que alojarán JSON/CSV, y que una copia del esqueleto reproduce la estructura de `PROMPT.md §3`.

**Ejecutar:**

```bash
OUT/_ledger/validate-A0.4.sh
```

**Salida (2026-10-18):**

```
OK: A0.4 (55 .md con frontmatter, 18 features, 6 subárboles principales, .gitkeep en _ledger y features)
exit=0
```

**Conteo del esqueleto:**

| Elemento | Cantidad | Notas |
|---|---|---|
| Ficheros `.md` con frontmatter | 55 | `id` derivado del nombre + `estado: pendiente` |
| Directorios | 27 | raíz + 5 subárboles (`06-…`, `07-…`, `08-…`, `10-…`, `_ledger`) + 18 features + `_ledger/{extract,units}` |
| `.gitkeep` | 21 | 18 en features + 3 en `_ledger/` |
| Raíz sin `.gitkeep` | 0 | eliminado por T4 (la raíz ya no está vacía) |

**Smoke test (T7):** `cp -R SKILL/templates/output-skeleton/. <tmp>/` produce un árbol con 55 `.md` y 21 `.gitkeep` distribuidos en 27 directorios, idéntico al árbol definido en `PROMPT.md §3` (líneas 40–133). La copia en `OUT/appflowy-review/` será estructuralmente exacta cuando A1.1 (clonado) la pueble.

**Discrepancia detectada vs `PROMPT.md §3`:** el nombre de carpeta `F04-sidebar-...` del PROMPT (línea 77) contiene `...` (placeholder) y se ha materializado como `F04-sidebar-favoritos-recientes-papelera-tabs-command-palette/`. Anotado en `OUT/22-preguntas-abiertas.md` para fase de consolidación futura.

`SKILL/SKILL.md §7` actualizado: la línea del esqueleto ya no lleva la coletilla `(A0.4)`.

### pruebas/A1.1/ — `fetch_sources.sh` + `sources.json` (2026-10-18)

**Objetivo:** verificar que el script de adquisición clona los 3 repos en los commits resueltos, escribe `OUT/_ledger/sources.json` con 3 entradas válidas, y que el validador del gate del ROADMAP (`validate-A1.1.sh`) devuelve 0.

**Ejecutar:**

```bash
OUT/_ledger/validate-A1.1.sh
```

**Salida (2026-10-18):**

```
OK: A1.1 (3 entradas, commit_short=HEAD, SRC/<name> con .git, [patch.crates-io] y dependency_overrides derivables)
exit=0
```

**Tabla de fuentes (de `OUT/_ledger/sources.json`):**

| Fuente | URL | `commit_short` | `commit` (40) | `requested_ref` | Tamaño | Método |
|---|---|---|---|---|---|---|
| appflowy | https://github.com/AppFlowy-IO/AppFlowy | `5cf3a36` | `5cf3a365dec0d59f64bad1ee4bb1050471a39b93` | `default-branch` (shallow) | 71 MB | shallow |
| collab | https://github.com/AppFlowy-IO/AppFlowy-Collab | `4dfccef` | `4dfccefb9e4fd35240107b93fb4b5966295b452e` | `4dfccef` (de `Cargo.toml`) | 51 MB | full |
| editor | https://github.com/AppFlowy-IO/appflowy-editor | `470c4e7` | `470c4e77c71b63f693ce0923a927afcd667d6f3b` | `470c4e7` (de `pubspec.yaml`) | 45 MB | full |

**Criterio de aprobación (del `ROADMAP.md`):**

> `sources.json` tiene 3 entradas con hash de 7+ caracteres; `git -C SRC/collab rev-parse --short HEAD` = rev del Cargo.toml.

- ✅ 3 entradas con hash ≥ 7 chars: `5cf3a36`, `4dfccef`, `470c4e7`.
- ✅ `git -C SRC/collab rev-parse --short HEAD` = `4dfccef` = rev del Cargo.toml.
- ✅ Bonus checks del validador: `SRC/<name>/.git` presente, `commit` completo coincidente con `HEAD`, y los dos nodos de evidencia (`[patch.crates-io]`, `dependency_overrides.appflowy_editor.git.ref`) re-derivables del árbol clonado.

**Diferencias detectadas vs el plan original (no reabren la fase):**

1. Parser regex de `pubspec.yaml` capturaba bloque equivocado: reescrito a parser línea-a-línea (T3 del plan, corregido en sitio).
2. `git ls-remote` no muestra los SHAs `4dfccef` ni `470c4e7`; sustituido por `resolve_commit_via_clone` (clon temporal + `git checkout`).
3. El bloque `collab* = { git=…, rev=… }` del Cargo.toml actual está **fuera** de `[patch.crates-io]` (sigue en la misma tabla, después de `[profile.profiling]`); el parser extendido lo capturó. Detalle en `OUT/22-preguntas-abiertas.md` A1.1-a.

Log completo: `OUT/_ledger/pruebas/A1.1/smoke.log`.

### pruebas/A1.2/ — `inventory.py` + `inventario.json` + `assets.json` (2026-10-18)

**Objetivo:** verificar que el script recorre `SRC/{appflowy,collab,editor}` y emite dos JSON (uno por archivo fuente, otro por binario) con metadatos completos, y que el validador del ROADMAP (`validate-A1.2.sh`) pasa la prueba literal:
> "el conteo de `.rs` y `.dart` coincide con `find … | wc -l`; ningún archivo con `capa: null`."

**Ejecutar:**

```bash
OUT/_ledger/validate-A1.2.sh
```

**Salida (2026-10-18):**

```
OK: A1.2 (JSON válido, sin capa null, 8 campos, .rs/.dart coinciden con find, assets separados, 3 fuentes)
exit=0
```

**Conteos del inventario (de `OUT/_ledger/inventario.json`):**

| Métrica | Valor |
|---|---|
| Total archivos fuente | 4.603 |
| Total LOC | 671.876 |
| Total bytes | 23.799.087 (~23,8 MB) |
| Total assets (binarios) | 1.186 |

**Distribución por fuente:**

| Fuente | Archivos | % |
|---|---|---|
| appflowy | 3.557 | 77,3% |
| editor | 733 | 15,9% |
| collab | 313 | 6,8% |

**Distribución por capa:**

| Capa | Archivos | Capa | Archivos |
|---|---|---|---|
| `ui` | 2.287 | `test` | 537 |
| `rust-handler` | 508 | `config` | 306 |
| `bloc` | 325 | `collab` | 280 |
| `service` | 162 | `build` | 43 |
| `server` | 32 | `dispatch` | 27 |
| `codegen` | 35 | `i18n` | 23 |
| `persistence` | 16 | `rust-manager` | 12 |
| `ffi` | 10 | (asset → `assets.json`) | 1.186 |

**Distribución por lenguaje:**

| Lenguaje | Archivos | Lenguaje | Archivos |
|---|---|---|---|
| `dart` | 2.581 | `toml` | 78 |
| `rust` | 1.025 | `yaml` | 71 |
| `text` | 435 | `markdown` | 65 |
| `json` | 115 | `objc-header` | 44 |
| `xml` | 82 | (otros 9 lenguajes) | 177 |

**Criterio de aprobación (del `ROADMAP.md`):**

> el conteo de `.rs` y `.dart` coincide con `find … | wc -l`; ningún archivo con `capa: null`.

- ✅ `find -name '*.rs' = 1.025` == `inventario[rust] = 1.025` (Check 4 del validador).
- ✅ `find -name '*.dart' = 2.581` == `inventario[dart] = 2.581` (Check 5 del validador).
- ✅ 0 archivos con `capa: null` (Check 2 del validador).
- ✅ Bonus checks: JSON válido, 8 campos por entrada (`fuente, ruta_rel, ruta_abs, lenguaje, loc, sha1, bytes, capa`), `assets.json` separado y sin solapamiento, 3 fuentes presentes.

**Rendimiento:** ejecución en 51 s (budget del plan: 90 s). `git hash-object` por archivo, con fallback a `hashlib.sha1` para no-tracked.

**Tamaño de entregables:** `inventario.json` = 2.0 MB, `assets.json` = 456 KB. Orden estable por `(fuente, ruta_rel)` para diffs legibles.

**Diferencias detectadas vs el plan original:** ninguna estructural. La ejecución cumplió el plan tal cual (D1–D18). Anotaciones menores en `OUT/22-preguntas-abiertas.md` (A1.2-a..d) para triage en A1.3/B0.2.

Log completo: `OUT/_ledger/pruebas/A1.2/smoke.log`.

### pruebas/A1.3/ — `init_ledger.py` + `cobertura.csv` (2026-10-18)

**Objetivo:** verificar que el script inicializa `cobertura.csv` con la cabecera de 7 columnas, tantas filas como `inventario.json`, todas en `estado=sin_asignar` y con los campos mutables (`feature_ids`, `documento`, `verificado_por`) vacíos.

**Ejecutar:**

```bash
OUT/_ledger/validate-A1.3.sh
```

**Salida (2026-10-18):**

```
OK: A1.3 (CSV con cabecera correcta, 4603 filas = inventario, todas sin_asignar, cols mutables vacías, 3 fuentes)
exit=0
```

**Esquema del CSV (cabecera + contenido de muestra):**

```
fuente,ruta,capa,feature_ids,documento,estado,verificado_por
appflowy,appflowy/.dockerignore,ui,,,sin_asignar,
appflowy,appflowy/.githooks/commit-msg,ui,,,sin_asignar,
appflowy,appflowy/.githooks/pre-commit,ui,,,sin_asignar,
…
editor,editor/test/test_helper.dart,test,,,sin_asignar,
```

| Columna | Origen en A1.3 | Quién la modifica después |
|---|---|---|
| `fuente` | `inventario.files[].fuente` | inmutable |
| `ruta` | `inventario.files[].ruta_rel` (D4: nombre abreviado en CSV) | inmutable |
| `capa` | `inventario.files[].capa` | inmutable |
| `feature_ids` | `""` | A4.1 (assign_ledger.py) |
| `documento` | `""` | A4.2 (generador de unidades) |
| `estado` | `sin_asignar` | B-fases (autor → `pendiente`; revisor OK → `verificado`); C2 al 100% |
| `verificado_por` | `""` | B-fases al aprobar (id del revisor) |

**Criterio de aprobación (del `ROADMAP.md`):**

> script de ejemplo crea el CSV con todas las filas del inventario en estado `sin_asignar`.

- ✅ 4.603 filas (= `len(inventario.files)`) + 1 cabecera = 4.604 líneas.
- ✅ 4.603 / 4.603 filas con `estado='sin_asignar'`.
- ✅ Cabecera exacta: `fuente,ruta,capa,feature_ids,documento,estado,verificado_por`.
- ✅ Bonus checks: `(fuente, ruta)` únicos, 3 fuentes presentes, `feature_ids/documento/verificado_por` vacíos.

**Tamaño:** 513 KB. Orden estable por `(fuente, ruta)`. Encoding UTF-8 sin BOM, formato RFC 4180 (`csv.excel`).

**Rendimiento:** ejecución en 0.05 s (script trivial; solo lee JSON y escribe CSV).

**Diferencia detectada vs el plan original:** el inventario usa la clave `ruta_rel` en JSON pero la columna del CSV se llama `ruta` (D4); corregido en sitio mapeando `r["ruta_rel"]` → columna `ruta`. Sin impacto sobre el contrato externo.

Log completo: `OUT/_ledger/pruebas/A1.3/smoke.log`.

**Cierre del Bloque A1 (Adquisición e inventario).**

| Entregable | Tamaño | Estado |
|---|---|---|
| `SRC/{appflowy,collab,editor}/` | 167 MB (clones) | ✅ |
| `OUT/_ledger/sources.json` | 1.5 KB | ✅ 3 fuentes |
| `OUT/_ledger/inventario.json` | 2.0 MB | ✅ 4.603 archivos |
| `OUT/_ledger/assets.json` | 456 KB | ✅ 1.186 binarios |
| `OUT/_ledger/cobertura.csv` | 513 KB | ✅ 4.603 filas, sin_asignar |

### pruebas/A2.1/ — `extract_events.py` + `events.json` (2026-10-18)

**Objetivo:** verificar que el extractor determinista parsea los 8 `event_map.rs` del workspace de AppFlowy, registra cada variante con su handler, y que el validador del ROADMAP pasa la prueba literal:
> para `flowy-document`, aparecen `CreateDocument` (input `CreateDocumentPayloadPB`, sin output) y `OpenDocument` (input `OpenDocumentPayloadPB`, output `DocumentDataPB`); toda variante del enum tiene handler registrado o queda marcada `sin_handler`.

**Ejecutar:**

```bash
OUT/_ledger/validate-A2.1.sh
```

**Salida (2026-10-18):**

```
OK: A2.1 (JSON valido, flowy-document OK, CreateDocument input=CreateDocumentPayloadPB output=null, OpenDocument input=OpenDocumentPayloadPB output=DocumentDataPB, sin_handler consistentes, handlers resueltos, conteos coherentes)
  crates_with_event_map: 8
  total_variants:        229
  total_registered:      224
  total_sin_handler:     5
exit=0
```

**Tabla por crate (de `OUT/_ledger/extract/events.json`):**

| Crate | Enum | Variantes | Registradas | sin_handler | init line |
|---|---|---:|---:|---:|---:|
| `flowy-ai`        | `AIEvent`        | 25 | 25 | 0 | 12 |
| `flowy-database2` | `DatabaseEvent`  | 72 | 71 | 1 | 11 |
| `flowy-date`      | `DateEvent`      |  1 |  1 | 0 |  8 |
| `flowy-document`  | `DocumentEvent`  | 21 | 21 | 0 | 12 |
| `flowy-folder`    | `FolderEvent`    | 51 | 48 | 3 | 11 |
| `flowy-search`    | `SearchEvent`    |  1 |  1 | 0 |  9 |
| `flowy-storage`   | `FileStorageEvent` | 2 |  2 | 0 |  8 |
| `flowy-user`      | `UserEvent`      | 56 | 55 | 1 | 17 |
| **TOTAL**         |                  | **229** | **224** | **5** | |

Todos los crates declaran `#[event_err = "FlowyError"]` y derivan
`Flowy_Event` + `ProtoBuf_Enum` (más `Debug, Clone, Display, Hash, …`).

**Criterio de aprobación (del `ROADMAP.md`):**

- ✅ `CreateDocument` con `input = "CreateDocumentPayloadPB"`, `output = null`. Handler `create_document_handler` resuelto a frontend/rust-lib/flowy-document/src/event_handler.rs:54.
- ✅ `OpenDocument` con `input = "OpenDocumentPayloadPB"`, `output = "DocumentDataPB"`. Handler `open_document_handler` resuelto a frontend/rust-lib/flowy-document/src/event_handler.rs:69.
- ✅ `flowy-document`: 21/21 variantes registradas, 0 `sin_handler`.
- ✅ A nivel global: 224/229 registradas; 5 `sin_handler` documentadas como legítimas (`GetAllRows`, `CreateFolderWorkspace` deprecated, `DeleteWorkspace` registrada en `flowy-user`, `CopyLink` con `#[event()]`, `AddWorkspaceMember`).

**Variantes `sin_handler` (todas verificadas en el código fuente):**

| Crate | Variante | Índice | Razón documentada |
|---|---|---:|---|
| `flowy-database2` | `GetAllRows` | 177 | Definida en el enum pero no pasada a `.event(...)` en `init`. |
| `flowy-folder`   | `CreateFolderWorkspace` | 0 | Marcada como `/// Deprecated:` en frontend/rust-lib/flowy-folder/src/event_map.rs:67; conservada por compatibilidad. |
| `flowy-folder`   | `DeleteWorkspace` | 3 | Definida en frontend/rust-lib/flowy-folder/src/event_map.rs:80 pero el handler real vive en `flowy-user::delete_workspace_handler` (caso cross-crate). |
| `flowy-folder`   | `CopyLink` | 20 | `#[event()]` (vacía) en frontend/rust-lib/flowy-folder/src/event_map.rs:120; `init` no la registra. |
| `flowy-user`     | `AddWorkspaceMember` | 37 | Definida en frontend/rust-lib/flowy-user/src/event_map.rs:197; `init` no la registra. |

**Multilínea — el parser maneja las 5 formas observadas:**

1. `.event(X, h)` en una sola línea.
2. `.event(\n  X,\n  h,\n)` con coma final (la más común en `flowy-document`, `flowy-ai`, `flowy-user`).
3. `#[event(\n  input = "X",\n  output = "Y",\n)]` multilínea (en `flowy-document::Redo/Undo/CanUndoRedo`).
4. `#[event()]` vacía (en `flowy-folder::CopyLink`, `RecoverAllTrashItems`, `PermanentlyDeleteAllTrashItem`, `RemoveDefaultPublishView`).
5. Variante sin atributo `#[event(...)]` (en `flowy-folder::CreateFolderWorkspace`, deprecada).

**Diferencias detectadas vs el plan original (corregidas en sitio):**

1. La regex de `.event(...)` no aceptaba la coma final tras el handler (forma multilínea) → 6 variantes de `flowy-document` quedaban falsamente como `sin_handler`. Corregido: añadir `\s*,?` antes de `\)` en T2.
2. `source_line` apuntaba a la línea del primer `#[event(...)]` previo en lugar del nombre de la variante. Corregido: usar `vm.start("name")` para apuntar al identificador. Documentado en el código.

Sin impacto sobre el contrato externo del JSON.

**Tamaño y rendimiento:** `events.json` = 140 KB, 4.150 líneas. Extracción en < 1 s; validador en < 0,1 s.

**Smoke test (robustez del extractor):** con `SRC/` vacío produce `events.json` bien formado con `crates_with_event_map: 0` y todos los summary a 0, sin abortar. Los checks del ROADMAP del validador fallan lógicamente (no hay `flowy-document`), comportamiento esperado.

Plan completo: `1792333525128-fase-a2-1-extract-events.md`. Resumen de la prueba: `OUT/_ledger/pruebas/A2.1/README.md`. Logs: `extract.log` y `validate.log`.

**Cierre de la primera fase del Bloque A2 (Extractores deterministas).**

### pruebas/A2.2/ — `extract_protobuf.py` + `protobuf.json` (2026-10-18)

**Objetivo:** verificar que el extractor captura todas las entidades
`#[derive(ProtoBuf)]` (structs) y `#[derive(ProtoBuf_Enum)]` (enums)
del workspace de AppFlowy, y que el cruce con `events.json` (A2.1)
resuelve todos los `input`/`output` únicos.

**Ejecutar:**

```bash
OUT/_ledger/validate-A2.2.sh
```

**Salida (2026-10-18):**

```
OK: A2.2 (JSON valido, 439 entidades (389 structs + 50 enums), cruce con events.json resuelto: 141/141 inputs + 84/84 outputs, 0 missing reportados)
exit=0
```

**Tabla por crate (de `OUT/_ledger/extract/protobuf.json`):**

| Crate | Structs | Enums | Archivos | Total |
|---|---:|---:|---:|---:|
| `dart-ffi`         |   2 |  1 |  2 |   3 |
| `flowy-ai`         |  41 | 10 |  2 |  51 |
| `flowy-database2`  | 163 |  7 | 42 | 170 |
| `flowy-date`       |   2 |  0 |  1 |   2 |
| `flowy-document`   |  43 |  7 |  3 |  50 |
| `flowy-folder`     |  57 |  7 |  6 |  64 |
| `flowy-notification` | 1 |  0 |  1 |   1 |
| `flowy-search`     |  11 |  2 |  4 |  13 |
| `flowy-storage`    |   3 |  0 |  1 |   3 |
| `flowy-user`       |  66 | 16 |  8 |  82 |
| **TOTAL**          | **389** | **50** | **70** | **439** |

745 archivos `.rs` escaneados en total; 70 contienen entidades protobuf.
1.030 campos en structs; 158 con `pb.one_of = true`.

**Cruce con `events.json` (A2.1):**

| Métrica | Valor |
|---|---:|
| `unique_event_inputs` | 141 |
| `unique_event_outputs` | 84 |
| `resolved_inputs` | **141 (100 %)** |
| `resolved_outputs` | **84 (100 %)** |
| `missing_event_pbs` | **0** |

**Casos destacados (del test literal del ROADMAP A2.2):**

- ✅ `CreateDocumentPayloadPB` (struct, 2 fields) en
  frontend/rust-lib/flowy-document/src/entities.rs:125. `is_input_of: [flowy-document::CreateDocument]`.
- ✅ `OpenDocumentPayloadPB` (struct, 1 field) en
  frontend/rust-lib/flowy-document/src/entities.rs:28. Usado por 5 eventos (OpenDocument,
  GetDocumentData, GetDocumentSnapshotMeta, GetDocEncodedCollab, GetDocumentText).
- ✅ `DocumentDataPB` (struct, 3 fields) en
  frontend/rust-lib/flowy-document/src/entities.rs:202.

**Patrones manejados:**

1. `#[pb(index = N)]` simple.
2. `#[pb(index = N, one_of)]` con oneof.
3. `#[pb(...)]` seguido de `//` comentarios antes del campo (caso real
   en `UpdateViewPayloadPB::extra`): el parser neutraliza los `//` y
   extrae el campo correctamente con `pb.index=7, one_of=true`.
4. Campos comentados excluidos (3 reales: `should_fetch_related_question`
   en `ChatMessagePB`, `workspace_id` en `ViewIdPB`).

**Diferencias detectadas vs el plan (corregidas en sitio):**

1. **Typo** `path` → `args.events_json` en `build_cross_ref` (sin impacto).
2. **Bug del crate name** `parts[3]` no era el crate sino `rust-lib`
   (constante). Corregido: `parts[4]`. Ahora `crates: 10` correctamente.
3. **Falsos positivos por `//` comentarios** con texto tipo `// - font_layout: "small"`:
   corregido requiriendo al menos un `#[...]` real en `RE_FIELD` y
   pre-procesando el body con `strip_line_comments_in_place` (conserva
   posiciones). Sin este cambio, hasta 4 campos falsos se extraían de
   `UpdateViewPayloadPB` y los 3 campos comentados quedaban con `pb: null`.

Sin impacto sobre el contrato externo del JSON.

**Tamaño y rendimiento:** `protobuf.json` = 616 KB, 22.412 líneas.
Extracción en < 1 s; validador en < 0,1 s.

**Smoke test:** con `--events-json` apuntando a archivo inexistente, el
extractor produce JSON bien formado con `cross_ref` vacío y los
summary a 0; no aborta. El validador en ese modo falla en check 5
(que requiere `events.json`), comportamiento esperado.

Plan completo: `1792333525128-fase-a2-2-extract-protobuf.md`. Resumen de
la prueba: `OUT/_ledger/pruebas/A2.2/README.md`. Logs: `extract.log` y
`validate.log`.

### pruebas/A2.3/ — `extract_notifications.py` + `notifications.json` (2026-10-18)

**Objetivo:** verificar que el extractor captura los 6 enums `*Notification`
del workspace Rust, sus `*_OBSERVABLE_SOURCE`, los emitters
`send_notification`/`NotificationBuilder::new`, y los listeners/parsers
Dart que los manejan. Valida la prueba literal del ROADMAP A2.3:
`DocumentNotification` con 5 variantes (incl. `Unknown`) y ≥1 listener
Dart por variante usada.

**Ejecutar:**

```bash
OUT/_ledger/validate-A2.3.sh
```

**Salida (2026-10-18):**

```
OK: A2.3 (JSON valido, 6 rust_notifications, 5 dart_parsers, 29 dart_listeners, DocumentNotification OK con 5 variantes y 3 con listener Dart, 0 source_mismatches)
exit=0
```

**Tabla por enum (de `OUT/_ledger/extract/notifications.json`):**

| Enum | Source | Variantes | Emitters | Con listener Dart |
|---|---|---:|---:|---:|
| `ChatNotification`     | `Chat`      | 10 | 1  | 0/10 |
| `DatabaseNotification` | `Database`  | 24 | 3  | 1/24 |
| `DocumentNotification` | `Document`  |  5 | 1  | **3/5** |
| `FolderNotification`   | `Workspace` | 19 | 1  | 8/19 |
| `StorageNotification`  | `storage`   |  2 | 1  | 0/2  |
| `UserNotification`     | `User`      | 10 | 9  | 9/10 |
| **TOTAL**              |             | **70** | **16** | **21/70** |

**Caso destacado (test literal del ROADMAP A2.3):**

`DocumentNotification` (en frontend/rust-lib/flowy-document/src/notification.rs:6) con
5 variantes: `Unknown=0` (`#[default]`), `DidReceiveUpdate=1`,
`DidUpdateDocumentSnapshotState=2`, `DidUpdateDocumentSyncState=3`,
`DidUpdateDocumentAwarenessState=4`. Tres con listener Dart
(`DocumentListener` y `DocumentSyncStateListener`).

**Patrones manejados (Rust):**

1. `pub enum XNotification { ... }` y `pub(crate) enum XNotification { ... }`.
2. `#[repr(i32)]` entre `#[derive(...)]` y `pub enum` (caso de folder).
3. `const X_OBSERVABLE_SOURCE: &str = "Y"` con/sin `pub`/`pub(crate)`.
4. `send_notification(id, Enum::Variant)` — helper per-crate.
5. `NotificationBuilder::new(id, ty, CONST_NAME)` — resuelve CONST → value.
6. `NotificationBuilder::new(id, ty, source).payload(p).send()`.
7. Variantes con `#[default]` (Unknown).

**Patrones manejados (Dart):**

1. Parser en `core/notification/X_notification.dart` con `const String _source`.
2. Listeners con `switch (ty) { case X.Y: ... }` (incluye `case user.X.Y:`
   con library alias).
3. Switch body con closures anidadas `{ ... }` (el balanceador de
   llaves respeta strings y comentarios).

**Cruce Rust↔Dart:** `rust_source_mismatches: 0` — los 5 parsers Dart
encuentran su enum Rust. `SearchNotification` (en
`flowy-search/src/entities/notification.rs`, no en `notification.rs`) no
se extrae por convención; documentado en 22-preguntas-abiertas A2.3-a.

**Diferencias detectadas vs el plan (corregidas en sitio):**

1. `RE_ENUM_DECL` requería `pub enum`; ahora acepta `pub(crate) enum` y
   `pub(super) enum`.
2. `RE_OBS_SOURCE` requería `pub\s+const`; ahora acepta const con/sin visibility.
3. La regex de OBSERVABLE_SOURCE era laxa y captaba consts no relacionados
   (p. ej. `APPFLOWY_AI_NOTIFICATION_KEY`); restringida a nombres que
   terminen en `_OBSERVABLE_SOURCE` (o sean exactamente `OBSERVABLE_SOURCE`).
4. Gap entre derive y enum: requería `#[repr(i32)]` intermedio; ahora
   strippea atributos del gap antes de validar.
5. `RE_DART_SWITCH.body` usaba `[^}]+` que terminaba ante closures
   anidadas; reemplazado por balanceador de llaves.
6. `RE_DART_CASE` requería `Enum.Variant`; ahora acepta prefijo de library
   `user.X.Y`.

Sin impacto sobre el contrato externo del JSON.

**Tamaño y rendimiento:** `notifications.json` = 48 KB, 1.608 líneas.
Extracción en < 1 s; validador en < 0,1 s.

**Smoke test:** con SRC/ vacío produce JSON bien formado con listas
vacías y 0 source_mismatches; no aborta.

Plan completo: `1792333525128-fase-a2-3-extract-notifications.md`.
Resumen: `OUT/_ledger/pruebas/A2.3/README.md`. Logs: `extract.log` y
`validate.log`.

### pruebas/A2.4/ — `extract_blocs.py` + `blocs.json` (2026-10-18)

**Objetivo:** verificar que el extractor captura todos los `Bloc<…>` y
`Cubit<…>` del workspace `appflowy_flutter`, con sus eventos/estados
freezed (legado `plugins/`, `workspace/`) y `sealed class` (nueva
arquitectura `features/*/logic/*_event.dart`).

**Ejecutar:**

```bash
OUT/_ledger/validate-A2.4.sh
```

**Salida (2026-10-18):**

```
OK: A2.4 (JSON valido, 142 blocs (125 Bloc + 17 Cubit), DocumentBloc OK con 8 eventos, ShareBloc OK con 9 eventos, 33 blocs en plugins/database/application)
exit=0
```

**Resumen:**

| Métrica | Valor |
|---|---:|
| Blocs (extiende `Bloc<…>`) | 125 |
| Cubits (extiende `Cubit<…>`) | 17 |
| Blocs con eventos extraídos | 125 |
| BLoCs en `plugins/database/application/` | **33** (umbral ≥ 5 ampliamente superado) |
| Archivos `.dart` escaneados | 1.525 |

**Distribución por carpeta de primer nivel:** `plugins/` 72, `workspace/` 43,
`mobile/` 9, `user/` 8, `features/` 5, `ai/` 5.

**Casos del test literal del ROADMAP A2.4:**

- ✅ `DocumentBloc` (frontend/appflowy_flutter/lib/plugins/document/application/document_bloc.dart:47)
  con 8 eventos: `initial`, `moveToTrash`, `restore`, `restorePage`,
  `deletePermanently`, `syncStateChanged`, `syncAwarenessStates`,
  `clearAwarenessStates`. 9 state fields, 4 injected services.
- ✅ `ShareBloc` (frontend/appflowy_flutter/lib/plugins/shared/share/share_bloc.dart:22) con 9 eventos.
- ✅ 33 BLoCs en `plugins/database/application/` (incluye
  `DatabasePropertyBloc`, `DatabaseGroupBloc`, `RowBloc`, `CellBloc`,
  `FieldBloc`, `SortBloc`, `FilterBloc`, `ViewBloc`, `CalculationsBloc`, etc.).

**Patrones manejados:**

1. `class XBloc extends Bloc<XEvent, XState> { ... }` con `@freezed class XEvent with _$XEvent { const factory X.foo(args) = Concrete; }` (legado).
2. `const factory X.foo({args}) = Concrete;` con named args multi-línea
   (caso `ActionNavigationEvent`).
3. `sealed class XEvent { ... }` con `const factory X.foo(args) = Concrete;` (nueva arquitectura).
4. `sealed class XEvent { ... }` con `factory X.foo(args) => Concrete(args);` (arrow form).
5. Multi-línea en sealed/factory: `factory X.setCustomPath(String path) =\n      Concrete;`.
6. Eventos definidos en archivo separado (`logic/*_event.dart`) — cross-file resolution.
7. `class XCubit extends Cubit<XState>` sin eventos.
8. Servicios inyectados: `final T _name = T();` o `late final T _name = T();`.

**Diferencias detectadas vs el plan (corregidas en sitio):**

1. `RE_FREEZED_CLASS` consumía la `{` final; corregido para no consumirla
   (permite `find("{", end)` apuntar a la `{` correcta).
2. `RE_FIELD` no aceptaba tipos primitivos Dart (`bool`, `int`, etc.);
   ampliado con `[a-z]+` para primitivos.
3. Los BLoCs de la nueva arquitectura (`features/`) declaran eventos en
   archivos separados con `sealed class` + `factory =>` (arrow) o
   `factory =` (freezed). Implementado: cross-file resolution con
   `cross_file_event_index`, regex `RE_SEALED_FACTORY` para arrow form,
   multi-línea con `[\s\S]*?`.
4. `const` ahora opcional en ambos regex de factory (los `sealed class`
   usan `factory` sin `const`).
5. Servicios `late final T _name;` sin inicialización (5 casos) no se
   capturan. Documentado como limitación.

**Tamaño y rendimiento:** `blocs.json` = 268 KB, 9.369 líneas.
Extracción en < 5 s; validador en < 0,1 s.

**Smoke test:** con SRC/ vacío produce JSON bien formado con listas
vacías; no aborta.

Plan completo: `1792333525128-fase-a2-4-extract-blocs.md`. Resumen:
`OUT/_ledger/pruebas/A2.4/README.md`. Logs: `extract.log` y `validate.log`.

### pruebas/A2.5/ — `extract_deps.py` + `deps.json` (2026-10-18)

**Objetivo:** extraer el grafo de dependencias del workspace Rust
(31 crates internos) y del workspace Dart (1 app + 7 packages internos),
con Mermaid crudo por cada uno. Valida la prueba literal del ROADMAP
A2.5: `flowy-core` depende de los 8 `flowy-*` de feature; `dart-ffi`
depende de `flowy-core`.

**Ejecutar:**

```bash
OUT/_ledger/validate-A2.5.sh
```

**Salida (2026-10-18):**

```
OK: A2.5 (JSON valido, 31 crates Rust con 150 internal edges, flowy-core -> 8 flowy-* features OK, dart-ffi -> flowy-core OK, appflowy -> 7 internal_path packages OK, 1+1 packages Dart con 12 internal edges)
exit=0
```

**Resumen:**

| Lado | Métrica | Valor |
|---|---|---:|
| Rust | Crates internos | 31 |
| Rust | Internal edges | 150 |
| Rust | External deps | 368 |
| Rust | workspace.dependencies | 38 |
| Dart | Packages (app + internal) | 8 |
| Dart | Internal edges | 12 |
| Dart | External deps declaradas | 136 |
| Dart | Paquetes resueltos (`pubspec.lock`) | 326 |

**Casos del test literal del ROADMAP A2.5:**

- ✅ `flowy-core` con **23 internal_dependencies** que incluyen los 8
  `flowy-*` de feature: `flowy-ai`, `flowy-database2`, `flowy-date`,
  `flowy-document`, `flowy-folder`, `flowy-search`, `flowy-storage`,
  `flowy-user` (más 9 variantes `*-pub`, `flowy-error`, `flowy-server`,
  `flowy-server-pub`, `flowy-sqlite`, y los 3 `lib-*` + `collab-integrate`).
- ✅ `dart-ffi.internal_dependencies` contiene `flowy-core` (más 11
  crates: `collab-integrate`, `flowy-date`, `flowy-derive`,
  `flowy-document`, `flowy-error`, `flowy-notification`, `flowy-server`,
  `flowy-server-pub`, `flowy-user`, `lib-dispatch`, `lib-log`).
- ✅ `appflowy.internal_dependencies` con 7 internal_path packages:
  `appflowy_backend`, `appflowy_popover`, `appflowy_result`,
  `appflowy_ui`, `flowy_infra`, `flowy_infra_ui`, `flowy_svg`.

**Patrones manejados:**

**Rust:**
1. `[workspace]` con `members` y `workspace.dependencies` (path-based).
2. Cada crate con `[package] {name, version, edition}` y
   `[dependencies]`.
3. Sintaxis mixta: `flowy_user.workspace = true` (guión bajo) y
   `flowy-user.workspace = true` (guión); el parser normaliza a la clave
   del workspace.
4. Externales: `version`, `git: { url, rev }`, `features`.

**Dart:**
1. `pubspec.yaml` con `path:`, `version:`, `git: { url, ref }`, `sdk:`.
2. `pubspec.lock` con `dependency:` (direct/transitive),
   `source:` (hosted/sdk/git/path), `version:`, `url:`, `ref:`.
3. Packages internos en `packages/*/pubspec.yaml` (subgrafo anidado).

**Mermaid generado:** un bloque `flowchart LR` por grafo. Rust: 150
aristas; Dart: 7 aristas desde `appflowy`.

**Diferencias detectadas vs el plan (corregidas en sitio):**

1. `parse_pubstyle_path` devolvía `kind = "path"`; `classify_deps`
   buscaba `"internal_path"`. Corregido: mapeo explícito
   `path → internal_path` y `hosted/git/sdk → external_<kind>`.
2. Python 3.9 (entorno actual) no tiene `tomllib` stdlib. Solución:
   el script hace try/except → fallback a `tomli` (instalable vía
   `pip3 install tomli`). El JSON producido es idéntico.

**Tamaño y rendimiento:** `deps.json` = 104 KB, 3.644 líneas.
Extracción en < 1 s; validador en < 0,1 s.

**Smoke test:** con SRC/ vacío produce JSON con `rust: null` y
`dart: null`; no aborta.

Plan completo: `1792333525128-fase-a2-5-extract-deps.md`. Resumen:
`OUT/_ledger/pruebas/A2.5/README.md`. Logs: `extract.log` y `validate.log`.

### pruebas/A2.6/ — `extract_misc.py` + `misc.json` (2026-10-18)

**Objetivo:** extraer 6 bloques independientes de metadata miscelánea
del workspace de AppFlowy: `routes`, `shortcuts`, `feature_flags`,
`error_codes`, `i18n_keys`, `startup_tasks`. Cubre la prueba literal
del ROADMAP A2.6: cada salida no vacía; el número de `ErrorCode`
coincide con las variantes del enum.

**Ejecutar:**

```bash
OUT/_ledger/validate-A2.6.sh
```

**Salida (2026-10-18):**

```
OK: A2.6 (JSON valido, routes=35, shortcuts=13, feature_flags=9, error_codes=133 (repr=u8), i18n_keys=1637, startup_tasks=15, PlatformErrorCatcherTask idx=0)
exit=0
```

**Resumen:**

| Bloque | Métrica | Valor |
|---|---|---:|
| routes | `GoRoute(...)` extraídos | 35 |
| shortcuts | `HotKeyItem` (con comentario) | 13 |
| shortcuts | `CommandShortcutEvent` (externo `appflowy_editor`) | 0 |
| feature_flags | `enum FeatureFlag` variantes | 9 |
| error_codes | `pub enum ErrorCode` variantes (u8) | 133 |
| error_codes | Default | `Internal` (idx=0) |
| i18n_keys | Claves únicas | 1.637 |
| startup_tasks | `LaunchTask` en orden | 15 |

**Casos del test literal del ROADMAP A2.6:**

- ✅ 6/6 salidas no vacías (validador checks 3-8): `routes=35`,
  `shortcuts=13`, `feature_flags=9`, `error_codes=133`, `i18n_keys=1637`,
  `startup_tasks=15`.
- ✅ `error_codes.total = 133` == número de líneas `Name = N,` en `code.rs`
  (validador check 4, threshold ≥ 100).
- ✅ `error_codes.repr = "u8"` (validador check 5).
- ✅ Todos los `ErrorCode` tienen `index` en rango `u8` (0-255).
- ✅ `PlatformErrorCatcherTask` está en posición 0 (coincide con
  comentario `// this task should be first task` en frontend/appflowy_flutter/lib/startup/startup.dart:121).

**Patrones manejados:**

1. **Routes**: `GoRoute(path: 'literal', name: 'name')` o
   `GoRoute(path: SomeClass.routeName, ...)` (referencia a constante).
2. **Shortcuts**: `HotKeyItem(hotKey: HotKey(KeyCode.x, ...), keyDownHandler: ...)`
   con comentario `//` previo como `name`.
3. **Feature flags**: `enum FeatureFlag { name, name, name; ... }` con
   métodos en el cuerpo.
4. **Error codes**: `pub enum ErrorCode { #[error("msg")] Name = N, }` con
   `#[repr(u8)]` y comentarios entre attrs y nombre.
5. **i18n keys**: `LocaleKeys.foo.bar.tr()` y `'foo.bar'.tr()`.
6. **Startup tasks**: `launcher.addTasks([ XxxTask(), if (cond) YTask(), ... ])`.

**Diferencias detectadas vs el plan (corregidas en sitio):**

1. El plan asumía que `CommandShortcutEvent` está en el workspace.
   Confirmado: vive en el paquete externo `appflowy_editor` (no en
   `SRC/appflowy`). El extractor captura `HotKeyItem` como fuente
   principal de atajos.
2. `HotKeyItem` no usa strings para `key` (usa `KeyCode.backslash` +
   `modifiers`); el nombre se infiere del comentario previo.
3. `GoRoute` usa `path: SomeClass.routeName` (const), no strings;
   regex ampliada.
4. `find_matching_brace` requería `text.find("{", m.end() - 1)` para
   apuntar al `{` inmediato del enum (no al siguiente).
5. `InProgress = 107` no se capturaba (tenía `// ...` entre
   `#[error(...)]` y el nombre); regex ampliada con `(?:\s*//[^\n]*)*`.
6. `m.start("2")` no funciona con grupos posicionales; cambiado a
   `m.start(2)`.

**Tamaño y rendimiento:** `misc.json` = 504 KB, 13.540 líneas.
Extracción en < 2 s; validador en < 0,1 s.

**Smoke test:** con SRC/ vacío produce JSON con todos los bloques en
cero; no aborta.

Plan completo: `1792333525128-fase-a2-6-extract-misc.md`. Resumen:
`OUT/_ledger/pruebas/A2.6/README.md`. Logs: `extract.log` y `validate.log`.

### pruebas/A2.7/ — `extract_codegen.sh` + `codegen-result.json` (2026-10-18)

**Objetivo:** intentar ejecutar el codegen de `flowy-codegen` para
obtener los `.proto` y el dispatch Dart generado. Si falla, documentar
la causa raíz en `codegen-fallido.md` (caso (b) permitido por el ROADMAP).

**Ejecutar:**

```bash
bash SKILL/scripts/extract_codegen.sh
OUT/_ledger/validate-A2.7.sh
```

**Salida (2026-10-18):**

```
OK: A2.7 (codegen no ejecutado en este entorno: Toolchain missing o incompleto. ...,
       1 intento(s) documentado(s) en .../codegen-fallido.md)
exit=0
```

**Outcome:** `failed` (esperado en este entorno).

**Prerrequisitos detectados:**

| Herramienta | Presente | Path |
|---|---|---|
| `cargo` | ✅ | `/Users/martin/.cargo/bin/cargo` |
| `cargo-make` | ❌ | — |
| `protoc` | ❌ | — |
| `protoc-gen-dart` | ❌ | — |
| `Makefile.toml` en `rust-lib/` | ❌ | — |
| `flowy-codogen/src/main.rs` | ❌ | (solo `lib.rs`) |
| Env `CARGO_MAKE_WORKING_DIRECTORY` | ❌ | — |
| Env `FLUTTER_FLOWY_SDK_PATH` | ❌ | — |

**Estrategias intentadas:**

| # | Estrategia | Estado | Causa |
|---|---|---|---|
| 1 | `cargo_make` | skipped | `cargo-make` no instalado + `Makefile.toml` ausente |
| 2 | `cargo_run_bin` | skipped | `main.rs` no existe (solo `lib.rs`) |
| 3 | `cargo_build_manual` | executed (exit 0) | compila pero no ejecuta codegen |

**Causa raíz:** `flowy-codegen` es un crate Rust que expone
`dart_gen(crate_name)`, `gen_proto_files()`, etc. como funciones de
librería (ver `build-tool/flowy-codegen/src/lib.rs`). Para ejecutarlo
desde fuera hay tres caminos: (a) `cargo make <tarea>` (requiere
`Makefile.toml` + `cargo-make`); (b) `cargo run --bin flowy-codegen`
(requiere `main.rs`); (c) wrapper crate con `path = "..."` que llame
a `dart_gen()`. Todos requieren además `protoc` y `protoc-gen-dart`
para la generación efectiva de `.proto` y `.pb.dart`.

**Estado de A2.2 sin dependencia de A2.7:**

A2.2 (`extract_protobuf.py`) parsea los `.rs` fuente directamente,
sin requerir los `.proto` generados. Por tanto, A2.2 es **funcional
aunque A2.7 falle** — exactamente el caso (b) que el ROADMAP A2.7
permite.

**Diferencias detectadas vs el plan (corregidas en sitio):**

1. `cargo` SÍ está presente en el sistema (`/Users/martin/.cargo/bin/cargo`);
   el plan asumía que faltaba. Reordenado: estrategia 3 SÍ se intenta
   y compila exitosamente; el problema es que el codegen no se ejecuta
   (falta binario).
2. Bash `echo` no interpreta `\t`; corregido con `printf 'present\t%s\n'`.
3. Bash export con tabs en valores se "manglea"; solucionado escribiendo
   a `.prereq.env` con `|` como separador, leído en Python.
4. `flowy-codegen` se invoca como librería, no como binario; documentado
   en `codegen-fallido.md`.

**Tamaño y rendimiento:** `codegen-result.json` = 2.6 KB; `codegen-fallido.md`
= 2.8 KB; `codegen-result.md` = 1.5 KB. Tiempo total del script < 1 s.

Plan completo: `1792333525128-fase-a2-7-codegen.md`. Resumen:
`OUT/_ledger/pruebas/A2.7/README.md`. Logs: `extract.log` y `validate.log`.

### pruebas/A3.1/ — `validate_mermaid.sh` + 3 fixtures (2026-10-18)

**Objetivo:** verificar que el validador Mermaid de la skill (i) extrae
los bloques ` ```mermaid ` de uno o varios `.md` (sólo esos, no otros
fenced code blocks), (ii) los renderiza con `mmdc` (mermaid-cli), y
(iii) si un diagrama falla, sale con código 1 e imprime
`ERROR <archivo>:<n>: <primera línea de stderr de mmdc>` con `n`
1-based contando únicamente bloques `mermaid`. Materializa la prueba
literal del ROADMAP A3.1.

**Ejecutar:**

```bash
bash OUT/_ledger/validate-A3.1.sh
```

**Salida (2026-10-18):**

```
OK: A3.1 (validate_mermaid.sh funciona: extrae bloques mermaid, renderiza con mmdc, reporta archivo:bloque_nº en fallos)
exit=0
```

**Checks (8, todos OK):**

| # | Check | Resultado |
|---|---|---|
| 1 | `SKILL/scripts/validate_mermaid.sh` existe y es ejecutable | ✅ |
| 2 | `--help` imprime uso y sale 0 | ✅ |
| 3 | `fixtures/positive.md` → exit 0 | ✅ |
| 4 | `fixtures/broken.md` → exit 1 + stderr `ERROR broken.md:N:` | ✅ |
| 5 | `fixtures/mixed.md` → exit 1 + stderr `ERROR mixed.md:4:` (no :1/:2/:3) | ✅ |
| 6 | `--quiet fixtures/positive.md` → exit 0, stdout ≤ 4 líneas con `OK=` | ✅ |
| 7 | Nº de líneas `ERROR archivo:N:` en stderr = nº de bloques fallidos (1 en `mixed.md`) | ✅ |
| 8 | Modo directorio: 3 archivos, summary `ok=4 fail=2` | ✅ |

**Cobertura de la prueba literal del ROADMAP A3.1:**

| Frase del ROADMAP | Materializada en |
|---|---|
| "extrae cada bloque ```mermaid de un `.md`" | `extract_mermaid_blocks()` (awk); 1 bloque en `positive`, 1 en `broken`, 4 en `mixed`. |
| "y lo renderiza con `mmdc`" | `render_block()` invoca `mmdc -i … -o …`. |
| "un diagrama roto falla con archivo y número de bloque" | check 4 (`broken.md:1`); check 5 (numeración correcta entre varios bloques: `mixed.md:4`, no `1`/`2`/`3`). |

**Requisitos externos:**

- `mmdc` (mermaid-cli ≥ 8.x) en `PATH`. Detectado: `/Users/martin/.local/bin/mmdc` (v12.0.0). Instalación: `npm i -g @mermaid-js/mermaid-cli`. Si falta, `validate-A3.1.sh` sale con `exit=77`.

**Diferencias detectadas vs el plan (corregidas en sitio):**

1. **Bug del offset de bloque** (crítico, habría hecho fallar check 5 en
   `mixed.md`): cuando se leía un nuevo marcador `<<<MERMAID_BLOCK_N>>>`
   el script actualizaba `i` antes de hacer flush del bloque previo,
   renumerando el bloque N-1 con el número N. Resultado: `mixed.md`
   quedaba con sólo 3 renders logueados y numeración desfasada. Fix:
   capturar `new_i` en variable local, flush con el `i` previo, después
   actualizar `i`. Verificado en `extract.log` línea 7 (`mixed.md#1`
   ahora presente).
2. **`flock` ausente en macOS**: sustituido por `fcntl.flock` vía
   Python 3 stdlib (POSIX, portable). El contador paralelo sigue
   siendo atómico.
3. **`printf` interpretando `---` como fin de opciones**: cambiado a
   `printf -- '--- summary: …'`.
4. **Primera línea de stderr de `mmdc --quiet` a menudo vacía**:
   `head -1` devolvía string vacío. Cambiado a
   `awk 'NF{print; exit}'` (primera línea no vacía).

**Tamaño y rendimiento:** `validate_mermaid.sh` = 350 líneas
(extract ~25 líneas awk + render ~40 líneas + main ~40 líneas + flags
~80 líneas). 6 bloques en 3 fixtures → 2.0 s en frío (1ª invocación
de `mmdc` carga Chromium), ~0.5 s/bloque en caliente.

Plan completo: `1792358647985-fase-a3-1-validate-mermaid.md`. Resumen:
`OUT/_ledger/pruebas/A3.1/README.md`. Logs: `extract.log` y
`validate.log`.

**Apertura del Bloque A3 (Validadores).** A3.1 es el primer validador
del bloque; A3.2 (`validate_evidence.py`), A3.3, A3.4, A3.5 siguen el
mismo patrón script+fixtures+validador.

### pruebas/A3.2/ — `validate_evidence.py` + 4 fixtures (2026-10-18)

**Objetivo:** verificar que el validador de evidencia (i) extrae
todas las referencias `[fuente:]ruta:línea[–fin]` de uno o varios
`.md` (excluyendo bloques ` ```código``` `), (ii) valida 4
condiciones contra `OUT/_ledger/inventario.json` (archivo
inventariado, fuente válida, línea/rango en archivo real, `inicio ≤ fin`),
(iii) emite 4 códigos de error con número de referencia 1-based
dentro del documento. Materializa la prueba literal del ROADMAP
A3.2.

**Ejecutar:**

```bash
bash OUT/_ledger/validate-A3.2.sh
```

**Salida (2026-10-18):**

```
OK: A3.2 (validate_evidence.py funciona: extrae refs, valida fuente/ruta/línea/rango, reporta con código)
exit=0
```

**Checks (9, todos OK):**

| # | Check | Resultado |
|---|---|---|
| 1 | `SKILL/scripts/validate_evidence.py` existe y es ejecutable | ✅ |
| 2 | `--help` imprime uso y sale 0 | ✅ |
| 3 | `OUT/_ledger/inventario.json` presente (prerreq) | ✅ |
| 4 | `fixtures/valid.md` → exit 0, 0 errores | ✅ |
| 5 | `fixtures/fake_path.md` → exit 1, `E_PATH_NOT_IN_INVENTORY` en ref :1: | ✅ |
| 6 | `fixtures/out_of_range.md` → exit 1, `E_LINE_OUT_OF_RANGE` en ref :1: | ✅ |
| 7 | `fixtures/mixed.md` → exit 1, EXACTAMENTE 3 errores en refs :2: :3: :4: (no :1: ni :5:) | ✅ |
| 8 | `--json fixtures/valid.md` → JSON parseable con `errors == 0` | ✅ |
| 9 | Modo directorio: 4 archivos, 10 refs (5 OK / 5 FAIL) | ✅ |

**Cobertura de la prueba literal del ROADMAP A3.2:**

| Frase del ROADMAP | Materializada en |
|---|---|
| "encuentra todas las referencias `[fuente:]ruta:línea[–fin]`" | `extract_refs()` (state machine + regex); 10 refs extraídas en 4 fixtures. |
| "comprueba que el archivo esté en el inventario" | `validate_ref()` → lookup en `inv`; fixture `fake_path.md` + check 5. |
| "y que la línea exista" | `validate_ref()` → `count_lines()` real del archivo; fixture `out_of_range.md` + check 6. |
| "una ruta inventada falla" | check 5. |
| "una línea fuera de rango falla" | check 6. |

**Códigos de error implementados:**

| Código | Cuándo se emite |
|---|---|
| `E_PATH_NOT_IN_INVENTORY` | `(fuente, ruta_full)` no existe en `inventario.json` (4.603 entradas). |
| `E_FUENTE_MISMATCH` | Prefijo de fuente no está en `{appflowy, collab, editor}`. |
| `E_LINE_OUT_OF_RANGE` | `línea > total` o `fin > total` (con `total = line_count` real del archivo, no el `loc` del inventario). |
| `E_RANGE_INVERTED` | En un rango, `fin < inicio`. |

**Diferencias detectadas vs el plan (corregidas en sitio):**

1. **Convención de lookup de rutas**: `inventario.json` (A1.2) guarda
   `ruta_rel` con el prefijo del repo (`appflowy/frontend/...`,
   `collab/collab-database/...`); las referencias de R-003 usan la
   ruta interna sin el prefijo. Fix: en `validate_ref()` se prepende
   `f"{fuente}/"` a la `ruta` salvo que ya lo tenga (idempotente).
2. **Color ANSI en output**: el validador grepeaba sobre output con
   códigos ANSI; los códigos rompían los anclajes `^ERROR`. Fix: el
   wrapper `run_ve()` invoca el script con `--no-color`.
3. **Conteos en check 9**: el plan proponía 11 refs / 8 OK / 3 FAIL;
   el contenido real ajustado produce 10 refs / 5 OK / 5 FAIL. El
   validador está dimensionado a los conteos reales; el delta no
   afecta al criterio de aprobación del ROADMAP.

**Tamaño y rendimiento:** `validate_evidence.py` = ~300 líneas (regex
+ state machine + lookup + validación). 10 refs en 4 fixtures → < 0,5 s
en frío (incluye carga de inventario.json, 2 MB, 4.603 entradas). En la
pasada global C1 (todos los `.md` de `OUT/`, ~300 docs), presupuesto
< 30 s (con cache de `line_count` por archivo único).

Plan completo: `1792358647985-fase-a3-2-validate-evidence.md`. Resumen:
`OUT/_ledger/pruebas/A3.2/README.md`. Logs: `extract.log` y
`validate.log`.

### pruebas/A3.3/ — `validate_template.py` + 6 fixtures (2026-10-18)

**Objetivo:** verificar que el validador de plantilla (i) parsea el
frontmatter YAML y comprueba los 5 campos obligatorios
(`id, titulo, fuente, archivos_cubiertos, estado`), (ii) auto-detecta
la plantilla por el prefijo del `id` (`Fxx.y` → feature con 19
secciones; `B4.N` → export con 11 secciones), (iii) valida orden,
duplicados, huecos y secciones vacías, (iv) emite 11 códigos de
error. Materializa la prueba literal del ROADMAP A3.3.

**Ejecutar:**

```bash
bash OUT/_ledger/validate-A3.3.sh
```

**Salida (2026-10-18):**

```
OK: A3.3 (validate_template.py funciona: valida frontmatter 5 campos + secciones en orden, 10+ códigos de error)
exit=0
```

**Checks (10, todos OK):**

| # | Check | Resultado |
|---|---|---|
| 1 | `SKILL/scripts/validate_template.py` existe y es ejecutable | ✅ |
| 2 | `--help` imprime uso y sale 0 | ✅ |
| 3 | `fixtures/valid_feature.md` → exit 0, 0 errores | ✅ |
| 4 | `fixtures/valid_export.md` → exit 0, 0 errores | ✅ |
| 5 | `fixtures/missing_section_13.md` → exit 1, `E_MISSING_SECTION: [13]` | ✅ |
| 6 | `fixtures/missing_frontmatter.md` → exit 1, `E_NO_FRONTMATTER` | ✅ |
| 7 | `fixtures/bad_estado.md` → exit 1, `E_BAD_ESTADO` | ✅ |
| 8 | `fixtures/out_of_order.md` → exit 1, `E_OUT_OF_ORDER` | ✅ |
| 9 | `--json fixtures/valid_feature.md` → JSON parseable con `errors == 0` | ✅ |
| 10 | Modo directorio: 6 archivos, 2 OK / 4 errores | ✅ |

**Cobertura de la prueba literal del ROADMAP A3.3:**

| Frase del ROADMAP | Materializada en |
|---|---|
| "verifica secciones obligatorias" | `validate_sections()` con `E_MISSING_SECTION`; check 5. |
| "y frontmatter" | `parse_yaml()` + `split_frontmatter()`; check 6. |
| "(`id, titulo, fuente, archivos_cubiertos, estado`)" | `REQUIRED_FRONTMATTER_FIELDS` con `E_MISSING_FRONTMATTER_FIELD` y `E_BAD_ESTADO`. |
| "quitar la sección 13 hace fallar el documento" | check 5 (`E_MISSING_SECTION: [13]`). |

**Plantillas soportadas en v1:**

| Plantilla | Secciones | Prefijo `id` | Estados |
|---|---|---|---|
| `feature` | 19 obligatorias (## 1. … ## 19.) + opcional ## 20. | `^F\d+(\.\d+)?$` | {verificado, pendiente, sin_asignar} |
| `export` | 11 obligatorias (## 1. … ## 11.) | `^B\d+(\.\d+)?$` | {verificado, pendiente} |

**Diferencias detectadas vs el plan (corregidas en sitio):**

1. **Parser YAML custom más permisivo**: el caso `key: [single]` (una
   sola entrada en lista inline) ahora se acepta
   correctamente. Documentado en `parse_yaml()`.
2. **Detección de sección vacía mejorada**: la implementación final
   excluye líneas en blanco Y líneas que son headings (para no
   contar `## 13.` como contenido de la §12). Sin impacto sobre
   los fixtures; documentado.

**Tamaño y rendimiento:** `validate_template.py` = ~440 líneas (regex
+ state machine + parser YAML + 11 checks por documento). 6 fixtures
en < 0,1 s en frío. En la pasada global C1, presupuesto < 30 s
sobre los ~300 docs de `OUT/`.

Plan completo: `1792358647985-fase-a3-3-validate-template.md`.
Resumen: `OUT/_ledger/pruebas/A3.3/README.md`. Logs: `extract.log`
y `validate.log`.

### pruebas/A3.4/ — `validate_coverage.py` + 4 fixtures CSV (2026-10-18)

**Objetivo:** verificar que el validador de cobertura (i) lee
`cobertura.csv` y calcula el % global y por capa de archivos en
`verificado`, (ii) lista los faltantes (`sin_asignar` y
`pendiente`) por capa con `% < 100`, (iii) soporta `--threshold N`
para gate de CI, (iv) emite JSON estructurado. Materializa la
prueba literal del ROADMAP A3.4.

**Ejecutar:**

```bash
bash OUT/_ledger/validate-A3.4.sh
```

**Salida (2026-10-18):**

```
OK: A3.4 (validate_coverage.py funciona: lee CSV, calcula % global y por capa, lista faltantes, soporta threshold y JSON)
exit=0
```

**Checks (10, todos OK):**

| # | Check | Resultado |
|---|---|---|
| 1 | `SKILL/scripts/validate_coverage.py` existe y es ejecutable | ✅ |
| 2 | `--help` imprime uso y sale 0 | ✅ |
| 3 | `toy_50pct.csv` → exit 1, global=50.00%, lista 2 sin_asignar | ✅ |
| 4 | `toy_100pct.csv` → exit 0, global=100.00%, sin faltantes | ✅ |
| 5 | `toy_0pct.csv` → exit 1, global=0.00%, lista 10 sin_asignar | ✅ |
| 6 | `toy_multi_capa.csv` → 3 capas (ui, service, rust-handler), global=50.00% | ✅ |
| 7 | `--json fixtures/toy_50pct.csv` → JSON parseable con `global.pct == 50.0` | ✅ |
| 8 | Modo real `cobertura.csv` (4.603 sin_asignar) → exit 1, global=0.00% | ✅ |
| 9 | `--threshold 50` sobre `toy_50pct.csv` (50% ≥ 50) → exit 0 | ✅ |
| 10 | `--threshold 51` sobre `toy_50pct.csv` (50% < 51) → exit 1 | ✅ |

**Cobertura de la prueba literal del ROADMAP A3.4:**

| Frase del ROADMAP | Materializada en |
|---|---|
| "cruza el ledger con los documentos" | `load_ledger()` + `compute_coverage()` (cada fila = 1 archivo del inventario A1.2). |
| "reporta %" | `compute_coverage()` calcula `pct = 100 * verificado / total`, global y por capa. |
| "y archivos sin asignar por capa" | `collect_faltantes()` con `--limit N` (default 50). |
| "con un ledger de juguete al 50% reporta 50%" | check 3. |
| "y lista los faltantes" | check 3 (2 sin_asignar + 3 pendiente). |

**Diferencias detectadas vs el plan (corregidas en sitio):**

1. **CLI sin positional args**: el plan proponía
   `validate_coverage.py [PATH]`; se implementó `--ledger PATH` (más
   coherente con `--threshold`, `--limit`). Sin impacto funcional.
2. **Captura de `--json` con exit code 1**: el script sale 1 si
   `pct < threshold` aunque emita JSON. En el validador del
   ROADMAP (check 7), separamos la captura (`|| true`) de la
   parseabilidad (`python3 -m json.tool`).
3. **Bug de awk con indentación**: el grep inicial
   `grep -c "^- "` no encontraba las líneas `    - appflowy/...`
   (con 4 espacios). Corregido con `awk '/^[[:space:]]+- /'`.

**Tamaño y rendimiento:** `validate_coverage.py` = ~280 líneas
(csv stdlib + defaultdict + tabla + JSON). 4.603 filas en < 0,5 s
en frío. Modo real sobre `cobertura.csv` actual genera tabla con
15 capas + GLOBAL + listas truncadas a 50 entradas por capa.

Plan completo: `1792358647985-fase-a3-4-validate-coverage.md`.
Resumen: `OUT/_ledger/pruebas/A3.4/README.md`. Logs: `extract.log`
y `validate.log`.

### pruebas/A3.5/ — `build_index.py` + 6 fixtures (2026-10-18)

**Objetivo:** verificar que el generador del índice (i) recorre
`OUT/`, (ii) parsea frontmatter y construye `id → ruta_rel`,
(iii) extrae refs `<X>` resolviéndolas, (iv) genera
`00-INDEX.md` con 9 secciones (resumen, commits, cobertura de
docs, cobertura de fuente, árbol, tabla de docs, mapa de
enlaces, no resueltos, cómo regenerar). Materializa la prueba
literal del ROADMAP A3.5.

**Ejecutar:**

```bash
bash OUT/_ledger/validate-A3.5.sh
```

**Salida (2026-10-18):**

```
OK: A3.5 (build_index.py funciona: genera 00-INDEX.md con árbol, estado, cobertura, commits; resuelve [[id]] → rutas reales)
exit=0
```

**Checks (10, todos OK):**

| # | Check | Resultado |
|---|---|---|
| 1 | `SKILL/scripts/build_index.py` existe y es ejecutable | ✅ |
| 2 | `--help` imprime uso y sale 0 | ✅ |
| 3 | `00-INDEX.md` contiene los 4 ids (A, B, C, 00-INDEX) en la tabla | ✅ |
| 4 | Sección 8 (no resueltos) contiene sólo `NOEXISTE`, no A ni B | ✅ |
| 5 | Sección 2 (Commits) menciona los 3 commit_short (5cf3a36, 4dfccef, 470c4e7) | ✅ |
| 6 | Sección 4 (cobertura fuente) muestra bloc, ui, GLOBAL=4/2=50.00% | ✅ |
| 7 | `--check-links` exit 1 por `[[NOEXISTE]]` | ✅ |
| 8 | `--json` produce JSON parseable con `unresolved_count == 1` | ✅ |
| 9 | Modo "todo resuelto" (con D.md con id `NOEXISTE`) → `--check-links` exit 0 | ✅ |
| 10 | Sección 5 (árbol) muestra los 4 docs | ✅ |

**Cobertura de la prueba literal del ROADMAP A3.5:**

| Frase del ROADMAP | Materializada en |
|---|---|
| "genera `00-INDEX.md`" | `render_index()` con 9 secciones; checks 3, 4, 5, 6, 10. |
| "árbol" | Sección 5 (`build_tree`); check 10. |
| "estado de cada doc" | Sección 6 (tabla con `estado`); check 3. |
| "cobertura" | Secciones 3 (docs) y 4 (fuente, reusando lógica A3.4); check 6. |
| "commits de fuentes" | Sección 2 (de `sources.json`); check 5. |
| "enlaces cruzados `<F..>` → rutas reales" | `build_id_index()` + `extract_cross_refs()`; sección 7 + 8; check 4. |
| "todos los enlaces del índice resuelven" | check 4 (sección 8 sólo lista `NOEXISTE`); check 9 (modo "todo resuelto" → exit 0). |

**Diferencias detectadas vs el plan (corregidas en sitio):**

1. **Cálculo de `pct` por capa en `load_cobertura`**: el plan
   asumía el cálculo en `render_index`; la implementación lo hace
   en `load_cobertura` (más limpio).
2. **Auto-referencia del índice**: el `00-INDEX.md` generado
   contiene `[[NOEXISTE]]` en su sección "no resueltos", que el
   extractor identificaba como nuevo enlace roto. Fix:
   `extract_cross_refs()` excluye el archivo `00-INDEX.md` del
   scan (es el artefacto generado, no producto).
3. **`out_dir_name` en árbol**: el árbol muestra el nombre del
   `out_dir` (no siempre `OUT/`); documentado.

**Tamaño y rendimiento:** `build_index.py` = ~420 líneas
(parser YAML + walk + extract_cross_refs + render_index).
6 fixtures en < 0,1 s en frío. Modo real sobre `OUT/` (3 docs)
también < 0,1 s; sobre los ~300 docs de la salida B, presupuesto
< 1 s.

Plan completo: `1792358647985-fase-a3-5-build-index.md`. Resumen:
`OUT/_ledger/pruebas/A3.5/README.md`. Logs: `extract.log`
(00-INDEX.md regenerado) y `validate.log`.

**Cierre del Bloque A3 (Validadores).** Las 5 fases A3.1..A3.5
están cerradas; la pasada global C1 + C2 (Parte C) usará estos
5 validadores en pipeline.

### pruebas/A4.1/ — `assign_ledger.py` + 5 fixtures + validador (2026-10-18)

Implementación del script que aplica `PROMPT.md §4` (tabla
líneas 143–159 + precedencia de línea 162) sobre el inventario
real y reescribe `OUT/_ledger/cobertura.csv`. La tabla original
F01–F17 cubre las features de producto; para llegar al umbral del
90 % exigido por el ROADMAP se añadieron cuatro features
infraestructurales (F00, F18, F19, F20) con sus patrones
explícitos, documentados en el docstring del script y mantenidos
en sincronía con `PROMPT.md` para los rangos F01–F17.

**Cobertura real**: 92.96 % (4.279 / 4.603). 324 archivos quedan
en `sin_asignar` (mayoría en `appflowy_flutter/lib/{workspace,shared,core}`
y en `frontend/rust-lib/flowy-{document,core}/src/`) y se
documentan en `OUT/_ledger/sin_asignar.md` para el triage B0.2.

**Cobertura toy**: 96.88 % (31 / 32). El archivo aislado
`appflowy/sin_match/archivo_aislado.dart` se queda `sin_asignar`,
como debe.

**Precedencia validada en CSV real** (evidencia en
`OUT/_ledger/cobertura.csv`):

- `appflowy/frontend/appflowy_flutter/lib/startup/tasks/localization.dart`
  → `F14` (no `F17`).
- `appflowy/frontend/appflowy_flutter/lib/shared/easy_localiation_service.dart`
  → `F14`.
- `appflowy/frontend/appflowy_flutter/lib/shared/feature_flags.dart`
  → `F17` (match exacto, sin competidor).
- `appflowy/frontend/appflowy_flutter/lib/plugins/document/...`
  → `F01` (gana sobre cualquier patrón genérico).

**Comandos**:

```bash
# Corrida real (escribe cobertura.csv, sin_asignar.md, sin_asignar.json)
python3 SKILL/scripts/assign_ledger.py

# Dry-run
python3 SKILL/scripts/assign_ledger.py --dry-run

# Modo CI: exit 1 si cobertura < 90
python3 SKILL/scripts/assign_ledger.py --min-coverage 90

# Validador de la fase (8 checks)
bash OUT/_ledger/validate-A4.1.sh
```

**Salida del validador**:

```text
$ bash OUT/_ledger/validate-A4.1.sh
  sin_asignar.json OK: 1 fila -> appflowy/sin_match/archivo_aislado.dart
OK: A4.1 (assign_ledger.py funciona: toy 100%, real 92.96% >= 90%, --help,
  --dry-run no escribe, idempotente, --min-coverage falla con <umbral,
  inventario inexistente -> exit 2, verificado preservado,
  sin_asignar.md/json generados)
```

**Cobertura de la prueba literal del ROADMAP A4.1:**

| Criterio ROADMAP | Check validador | Resultado |
|---|---|---|
| `≥ 90 %` asignado automáticamente | script --dry-run mide | **92.96 %** ✅ |
| Lista de `sin_asignar` generada | `OUT/_ledger/sin_asignar.md` existe y tiene 324 filas | ✅ |
| F14 > F17 sobre `localization.dart` | grep en cobertura.csv | `F14` ✅ |
| Idempotencia | sha1 antes/después de 2 corridas | idéntico ✅ |
| `--dry-run` no escribe | mtime `cobertura.csv` inalterado | ✅ |
| `verificado` preservado | diff `verified_ledger.csv` ↔ `expected_verified_ledger.csv` | idéntico ✅ |
| Inventario inexistente → exit 2 | `python3 --inventario /no/existe.json` | exit 2 ✅ |

Plan completo: `1792363730747-assign-ledger-a41.md`. Resumen:
`OUT/_ledger/pruebas/A4.1/README.md`. Log: `smoke.log`.

**Abre el Bloque A4 (Orquestación).** Siguiente fase: **A4.2 —
Generador de unidades de trabajo** (`OUT/_ledger/units/<id>.json` por
feature, división si supera ~120 archivos).

### pruebas/A4.2/ — `build_units.py` + `validate_units.py` + 88 unidades (2026-10-18)

Generador de unidades que consume `cobertura.csv` (post-A4.1) y
produce `OUT/_ledger/units/<id>.json` (uno por feature o
sub-feature) más un `_index.json` con el resumen. Las features con
> 120 archivos se subdividen en una sola pasada (sin recursión)
usando:

- **Tabla explícita** para F01 (10 sub-features según `ROADMAP B3.F01`),
  F02 (13 según `ROADMAP B3.F02`), F05/F09/F16/F19 (definidas en el
  propio script).
- **Fallo + división por directorio** para los catch-all (F00.5
  paquetes, F00.7 glue, F01.0 resto, F02.0 resto, F16.1 mobile,
  F19.2 tests) que exceden el umbral.

**Distribución real (88 unidades, 4.279 archivos)**:

- F00 → 26 unidades (1.529 archivos): 7 paquetes Dart, 14 sub-grupos
  de app glue, 6 unidades para FFI/dispatch/errors/build/collab-pub/native.
- F01 → 12 unidades (710): F01.0.1..F01.0.3 (resto del bloque
  application/) + F01.1..F01.9 (editor_plugins sub-grupos).
- F02 → 14 unidades (651): F02.0.1..F02.0.2 (resto del índice) +
  F02.1..F02.12.
- F05 → 2 (Dart + Rust), F09 → 4, F16 → 3, F19 → 14.
- F03/F04/F06/F07/F08/F11/F12/F13/F14/F15/F17/F18/F20 → 1 unidad
  cada una.

**Comandos**:

```bash
# Corrida real (escribe units/<id>.json + _index.json)
python3 SKILL/scripts/build_units.py

# Validar unidades contra esquema y cobertura
python3 SKILL/scripts/validate_units.py

# Validador de la fase (7 checks)
bash OUT/_ledger/validate-A4.2.sh
```

**Salida del validador**:

```text
$ bash OUT/_ledger/validate-A4.2.sh
  toy: 7 unidades, suma=51 = asignados=51
  real: 88 unidades, suma=4279 = asignados=4279, sin solapamiento
  --max-files 50: 153 unidades, suma=4279
  --no-split: 20 unidades (Fxx simples)
  F10: 0 archivos -> en features_vacias, sin unidad (correcto)
OK: A4.2 (build_units.py + validate_units.py: toy 7u/51f, real 88u/4279f
  sin solapamiento, idempotente, --max-files aumenta, --no-split reduce,
  --include filtra, F10 emite unidad)
```

**Cobertura de la prueba literal del ROADMAP A4.2**:

| Criterio ROADMAP | Check validador | Resultado |
|---|---|---|
| Suma archivos unidades = asignados | suma de `archivos_total` en `validate_units.py` | **4.279 = 4.279** ✅ |
| `OUT/_ledger/units/<id>.json` por feature/sub | `ls units/` | 88 ✅ |
| División > 120 archivos | F00/F01/F02/F05/F09/F16/F19 subdivididos | sí ✅ |
| Toy: 7 unidades y suma = 51 | `validate-A4.2.sh` check 2 | ✅ |
| Sin solapamiento | `validate_units.py` | 0 duplicados ✅ |
| Idempotencia | estructura idéntica entre 2 corridas | ✅ |
| `--max-files 50` aumenta unidades | check 5 | 153 unidades ✅ |
| `--no-split` reduce a Fxx simples | check 6 | 20 unidades ✅ |
| `--include F01,F02` filtra | check 8 | solo F01/F02 ✅ |
| F10 (0 archivos) sin unidad | check 7 | en `features_vacias` ✅ |

Plan completo: `1792363730747-build-units-a42.md`. Resumen:
`OUT/_ledger/pruebas/A4.2/README.md`. Log: `smoke.log`.

**Siguiente fase**: **A4.3 — Contratos de subagente** (prompts
autor/revisor en `SKILL/references/contracts/` con entrada/salida
exactas de `AGENTS.md §8`).

### pruebas/A4.3/ — Contratos de subagente + `run_subagent.py` mock (2026-10-18)

Tres archivos en `SKILL/references/` formalizan el contrato de los
subagentes del Bloque B:

- **`subagent-contract.md`** — fuente de verdad de los 4 esquemas
  JSON: `AutorInput`, `AutorOutput`, `RevisorInput`, `RevisorOutput`.
  Reglas duras, errores recuperables vs fatales, tabla de muestreo.
- **`subagent-autor-prompt.md`** — prompt que el orquestador
  inyecta al subagente autor. Define identidad, pasos obligatorios
  (lee cada archivo, filtra catálogos, rellena plantilla, escribe
  y devuelve `AutorOutput`), reglas de evidencia y manejo de
  errores.
- **`subagent-revisor-prompt.md`** — prompt simétrico para el
  revisor. Pasos obligatorios: ejecuta los 3 validadores, hace
  muestreo semántico de las afirmaciones `[VERIFICADO]`, devuelve
  `RevisorOutput` estricto.

**Mock `run_subagent.py`** (`SKILL/scripts/`, ~360 líneas) cumple la
prueba literal del ROADMAP sin depender de un LLM:

- **Modo autor**: carga la unidad, lee los archivos reales de
  `SRC/`, captura la primera línea no vacía de cada uno, genera
  un documento Markdown estructuralmente válido (19 secciones,
  3 bloques Mermaid placeholder, tabla real de archivos en §12
  con citas `ruta:línea` reales) y devuelve `AutorOutput` con
  `schema_version: 1` y los 5 campos obligatorios.
- **Modo revisor**: ejecuta los 3 validadores reales sobre el
  documento creado y devuelve `RevisorOutput` con `veredicto:
  aprobado` o `rechazado` y `correcciones` estructuradas.

**Corrida real sobre F11 (2 archivos)**: el autor crea
`OUT/09-features/F11-exportacion-ui/F11-exportacion-ui.md` con 19
secciones, 3 placeholders Mermaid y 2 citas reales; el revisor
ejecuta los 3 validadores (todos exit 0) y devuelve
`veredicto: aprobado`, 0 correcciones, muestreo `pct: 0`
(el mock no muestrea realmente).

**Comandos**:

```bash
# Modo autor (crea el documento y devuelve AutorOutput a --out)
python3 SKILL/scripts/run_subagent.py \
  --rol autor --unit <ruta>/<unit>.json --out <out>.json --out-root <root>

# Modo revisor (ejecuta validadores y devuelve RevisorOutput)
python3 SKILL/scripts/run_subagent.py \
  --rol revisor --unit <ruta>/<unit>.json --out <out>.json --out-root <root>

# Validador de la fase (9 checks)
bash OUT/_ledger/validate-A4.3.sh
```

**Salida del validador**:

```text
$ bash OUT/_ledger/validate-A4.3.sh
  referencias: 3 archivos no vacios, fixture presente
  AutorOutput: documento=OUT/09-features/F11-exportacion-ui/F11-exportacion-ui.md filas=2
  documento: /tmp/.../OUT/09-features/F11-exportacion-ui/F11-exportacion-ui.md con 19 secciones
[run_subagent] rol=revisor veredicto=aprobado correcciones=0
  RevisorOutput: veredicto=aprobado correcciones=0
  contrato: 4 esquemas presentes (AutorInput/Output, RevisorInput/Output)
  prompts: ambos referencian el contrato y los 3 validadores
OK: A4.3 (run_subagent.py + 3 referencias: --help, autor produce AutorOutput + doc >= 19 secciones, revisor produce RevisorOutput, --json OK, contrato y prompts OK)
```

**Cobertura de la prueba literal del ROADMAP A4.3**:

| Criterio ROADMAP | Check validador | Resultado |
|---|---|---|
| Prompts autor/revisor en `references/` | check 1 | 3 archivos no vacíos ✅ |
| Entrada/salida exactas de `AGENTS.md §8` | contrato + prompts | 4 esquemas JSON ✅ |
| Ejecutar autor+revisor en unidad trivial | checks 3–6 | JSON parseable ✅ |
| Devuelve JSON válido | checks 3, 5 | `schema_version: 1` + campos completos ✅ |
| `--json` produce JSON parseable | checks 6 | stdout OK ✅ |
| Contrato menciona los 4 esquemas | check 7 | ✅ |
| Prompts referencian contrato y validadores | check 8 | ✅ |

**Decisión de diseño (mock vs LLM real)**: el runner es un mock
determinista que produce un documento estructuralmente válido pero
semánticamente vacío. Esto cumple la prueba literal del ROADMAP
sin depender de un LLM en CI. La integración con LLM real
(Hermes/Cline/Kilo) se materializa en el Bloque B (features y
motor) usando estos prompts como input del modelo.

Plan completo: `1792363730747-subagent-contracts-a43.md`. Resumen:
`OUT/_ledger/pruebas/A4.3/README.md`. Log: `smoke.log`.

**Siguiente fase**: **A4.4 — `STATE.md` y reanudación** (el
orquestador puede retomar desde cualquier fase leyendo `STATE.md` +
ledger; corte y reanudación cross-herramienta).

## Cómo reanudar

Pasos (resumidos de `SKILL/SKILL.md §5`):

1. Leer este `STATE.md` → última fase cerrada: **A4.3** (Bloque A4 parcial: A1 + A2.1..A2.7 + A3.1..A3.5 + A4.1 + A4.2 + A4.3).
2. Cargar `OUT/_ledger/{sources.json,inventario.json,assets.json,cobertura.csv,sin_asignar.md,sin_asignar.json,units/*.json,units/_index.json,extract/{events,protobuf,notifications,blocs,deps,misc}.json,pruebas/A2.7/codegen-result.json,pruebas/A2.7/codegen-fallido.md,pruebas/A3.1/{extract.log,validate.log,README.md,fixtures/*.md},pruebas/A3.2/{extract.log,validate.log,README.md,fixtures/*.md},pruebas/A3.3/{extract.log,validate.log,README.md,fixtures/*.md},pruebas/A3.4/{extract.log,validate.log,README.md,fixtures/*.csv},pruebas/A3.5/{extract.log,validate.log,README.md,fixtures/*},pruebas/A4.1/{smoke.log,README.md,fixtures/*},pruebas/A4.2/{smoke.log,README.md,fixtures/*},pruebas/A4.3/{smoke.log,README.md,fixtures/*},SKILL/references/{subagent-contract,subagent-autor-prompt,subagent-revisor-prompt}.md}` (todos los entregables cerrados hasta ahora).
3. Saltar a la fase siguiente del `ROADMAP.md`: **A4.4** — `STATE.md` y reanudación.
4. Al cerrar la fase, añadir fila al índice de este fichero.

## Decisiones y notas

- **Fase nueva A0.0**: `PROMPT.md` no existía; se reconstruyó derivando de `AGENTS.md` + `ROADMAP.md` para desbloquear A0.2/A0.3/A0.4/A4.1. Marcado como "consolidar en fase posterior" al inicio del propio `PROMPT.md`. Cualquier contradicción detectada durante la ejecución va a `OUT/22-preguntas-abiertas.md`.
- **Frontera PROMPT.md vs SKILL.md**: `PROMPT.md` (en raíz) define el **qué** (encargo, etapas, plantillas, mapa de features). `SKILL.md` (en `SKILL/`) define el **cómo se carga** (router ≤ 500 líneas, frontmatter, reglas de disparo). Cero duplicación de plantillas.
- **SKILL.md ≤ 500 líneas** por analogía con `notemartin-study-notes/SKILL.md:8` (`INV-02`).
