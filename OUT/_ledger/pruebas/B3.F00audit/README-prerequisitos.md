# B3.F00audit — Fase 0 del cierre del Bloque B3: reparación del ledger de unidades

Bitácora de las reparaciones **bloqueantes** que precedieron a la escritura de
cualquier documento. Sin ellas, `build_units.py` destruía unidades existentes y
el invariante `suma(archivos_total) == filas asignadas` no se podía sostener.

Plan ejecutor: `~/.local/share/kilo/plans/1792513584673-b3-cierre-ledger-completo.md` §3.

---

## 0.1 Auditoría de la fuga de F02 — 114 archivos sin documentar

F02 estaba marcada ✅ en el ROADMAP con 537 de sus 651 archivos verificados. Los
114 restantes (`appflowy/frontend/rust-lib/flowy-database2/`) no estaban en
ningún documento. `audit_f02_leak.py` los clasifica comparándolos con las
referencias `ruta:línea` extraídas por `validate_evidence.extract_refs` de los 21
documentos de `OUT/09-features/F02-bases-de-datos/`:

| Grupo | Total | (a) citados | (b) mencionados sin cita | (c) sin cubrir |
|---|---:|---:|---:|---:|
| Raíz de `flowy-database2` (`lib.rs`, `event_map.rs`, `event_handler.rs`, `manager.rs`, `notification.rs`, `template.rs`, manifests) | 9 | 4 | 0 | **5** |
| `src/entities/**` (entidades protobuf y changesets) | 49 | 4 | 0 | **45** |
| `src/services/mod.rs`, `src/services/setting/*`, `src/utils/*` | 5 | 2 | 0 | **3** |
| `tests/database/**` (13 carpetas de tests) | 51 | 0 | 0 | **51** |
| **Total** | **114** | **10** | **0** | **104** |

**Decisión**: 104 archivos sin cubrir son material de B3, no de B4. Se crean tres
unidades nuevas (declaradas en `SUBDIVISIONS["F02"]`):

| Unidad | arch | Documento | Contenido |
|---|---:|---|---|
| `F02.13` | 14 | `13-fluy-database2-raiz-eventos-y-manager.md` | `lib.rs`, `event_map.rs` (**`DatabaseEvent` completo**), `event_handler.rs`, `manager.rs`, `notification.rs` (**`DatabaseNotification` completo**), `template.rs`, `services/{mod,setting/*}`, `utils/*`, manifests |
| `F02.14` | 49 | `14-fluy-database2-entidades-y-changesets.md` | Todas las entidades PB de `src/entities/**` |
| `F02.15` | 51 | `15-fluy-database2-tests.md` | Batería de `tests/database/**` (cell, field, filter, group, sort, layout, calculations, pre_fill, share, mock_data) |

Los 10 archivos de la categoría (a) quedan cubiertos por los documentos que ya
los citaban y se marcan `verificado` al cerrar `F02.13`.

> Hallazgo de fondo: **B2.1 (`11-catalogo-eventos-ffi.md`) ya catalogaba las 24
> variantes de `DatabaseEvent` y B2.4 las 24 de `DatabaseNotification`**, pero no
> existía ningún documento de feature que explicara `manager.rs` ni el
> `DatabaseEditor`. Ese hueco es exactamente lo que cubren F02.13–F02.15.

## 0.2 Cambios en `SKILL/scripts/build_units.py`

| Cambio | Motivo |
|---|---|
| `FEATURE_TITLES["F21"] = "Icon/Emoji picker"` | F21 se creó en B0.2 sin título: la unidad decía `titulo: "F21"` y `documento: …/F21-f21/F21-f21.md`. |
| `FEATURE_TITLES["F00"]` recortado a 80 chars | El título original generaba un slug que `_doc_path` recortaba de forma inconsistente. |
| `F00_SUBS`: entrada de índice `F00.0` + `F00.7.0`…`F00.7.8` | `F00.7` estaba partida por primer segmento de ruta: 11 sub-unidades de **1 archivo** (`.dockerignore`, `LICENSE`, `install.sh`…) y `F00.7.13` con **517**. Corte declarativo por naturaleza. |
| `F00_SUBS`: `F00.5.1`/`F00.5.1.2` y `F00.5.6`/`F00.5.6.2`/`F00.5.6.3` | `appflowy_backend` (121) y `flowy_infra_ui` (203) superaban el umbral de ~120 (`AGENTS.md §8`). Corte por `lib/` vs `example/` + nativo. |
| `F09_SUBS`: entrada de índice `F09.0` | `F09.1`–`F09.4` declaraban una dependencia `F09.0` inexistente. Precedente: `F05.0`. |
| `F16_SUBS` reescrito (`F16.0`, `F16.1.1`, `F16.1.2.{1,2,3}`, `F16.2`) | `F16.1.1`/`F16.1.2` existían **solo en disco**: `build_units.py` no las generaba, así que cualquier regeneración las borraba y devolvía `F16.1` con 184 archivos. |
| `F19_SUBS`: entrada de índice `F19.0` + `editor/test/{editor_state_test.dart,test_helper.dart,l10n}` en `F19.5` | `F19.1`–`F19.5` declaraban `F19.0`; 3 ficheros huérfanos caían en el índice. |
| `F12_SUBS`, `F13_SUBS`, `F15_SUBS` nuevas | 72 + 127 + 53 archivos en unidades de un solo documento, por encima del umbral o con dominios muy distintos (Dart↔Rust en F15). |
| `ALWAYS_EMIT = {"F16.2"}` | `F16.2` cubre `editor_plugins/mobile_*`, ya asignado a F01.6.4. Sin esto desaparecía y no se podía dejar por escrito la corrección de scope. |
| `--prune` | Sin él, cambiar `SUBDIVISIONS` deja unidades huérfanas que `validate_units.py` cuenta como doble propiedad. Protege las unidades con filas ya verificadas y las de 0 archivos (índices). |
| `--index-only` | Reconstruye `_index.json` leyendo **todo** el directorio. Antes solo indexaba las features regeneradas, y perdía F01/F03–F07 del índice. |
| `write_index` usa `load_units_from_disk()` | Ídem. |
| `_split_recursive()` (nuevo, **no usado**) | Se probó la división recursiva y se descartó: fragmentaba los paquetes Dart en ~35 unidades de 1–15 archivos (`example/`, `android/`, `ios/` son andamiaje). Se conserva documentando el descarte. |

## 0.3 Scripts nuevos en `SKILL/scripts/`

| Script | Qué hace |
|---|---|
| `rebuild_units.sh` | Pipeline canónico de reconstrucción: `build_units --prune` → `sync_units_from_docs` → `build_units --index-only` → `validate_units`. |
| `sync_units_from_docs.py` | **Fuente de verdad del `archivos` de cada unidad cuando el documento existe**: deriva la lista del frontmatter `archivos_cubiertos`. Resuelve conflictos a favor de la unidad con documento y luego de la más específica; re-ancla las filas que ningún documento reclama a la unidad de prefijo común más largo. Idempotente. |
| `align_units.py` | Reparación puntual de doble propiedad (ya no está en el pipeline: su heurística vaciaba unidades cerradas). |
| `restore_unit_files.py` | Reinyecta filas `verificado` perdidas al regenerar (caso F08 con 21 de 32). Sólo para cierre parcial. |
| `make_phase_suite.py` | Generador de las suites `validate-B3.<UNIT>.sh` de 5 checks (promovido desde `B3.F030`). |
| `set_unit_docs.py` | Fija rutas `documento` a mano y reindexa (promovido desde `B3.F030`, reescrito). |

### Por qué `sync_units_from_docs.py` era imprescindible

`build_units.py` genera unidades **solo desde filas pendientes**. Una feature
cerrada (F01, F03–F07) sólo sobrevive en disco por reparaciones manuales, y en
cuanto se regenera una feature a medio cerrar (F02, F08) las filas pendientes
quedan reclamadas por dos unidades. El frontmatter `archivos_cubiertos` del
documento sí sabe exactamente qué cubre, así que pasó a ser la fuente de verdad.

Dos casos concretos que sólo él arregla:

- `F02.0` acumulaba **539** rutas (las de sus sub-unidades) porque apuntaba a un
  documento inexistente.
- `F01.0.1` y `F01.0.2` reclamaban las mismas 798 rutas tras una regeneración.

## 0.4 Reparaciones de datos

| Qué | Detalle |
|---|---|
| `units/F02.0.1.json`, `units/F02.0.2.json`, `units/F03.json` | Unidades **maestro** purgadas: duplicaban la propiedad de sus hijas. `F02.0.1/2` ya se habían purgado en B3.F030 y reaparecieron al restaurar `.stale-bak`. |
| `units/F00.5.6.2.*`, `F00.7.1.*`, `F00.7.2.*` (38 ficheros) | Restos de la división recursiva descartada. Purga en `B3.F02audit/purge_stale.py`. |
| `units/F01.0.json` → `documento` | `0-indice-de-documentos-y-editor-modelo-documentbloc-servicios.md` no existe; el real es `0.0-indice-documentos-y-editor.md`. |
| `OUT/OUT/` | Artefacto de un `--out-root OUT/` mal pasado en una fase anterior. Borrado. |
| `OUT/_ledger/validate-A4.2.sh` | `N_REAL` re-baselined de 118 a **129** ficheros de unidad (124 de feature + 5 `B1.*`). |

## 0.5 Resultado

```
[build_units] unidades=124 (features con filas pendientes) + 5 B1.* en disco
[validate_units] unidades=124 archivos=4603 asignados_csv=4603 → OK

 F00  25 unidades  1556      F09   5 unidades  166     F16   6 unidades  184
 F01  23 unidades   798      F10   1 unidad     3     F17   1 unidad     56
 F02  25 unidades   651      F11   1 unidad     2     F18   1 unidad    113
 F03   4 unidades   116      F12   2 unidades   72     F19  15 unidades  354
 F04   1 unidad      66      F13   3 unidades  127     F20   1 unidad     13
 F05   3 unidades   131      F14   1 unidad     6     F21   1 unidad     11
 F06   1 unidad      35      F15   2 unidades   53
 F07   1 unidad      58      F08   1 unidad    32
 TOTAL 4603 archivos · 0 sin_asignar · 0 solapamiento · 0 sin unidad
```

`validate-A4.1.sh`, `validate-A4.2.sh` y `validate-A4.4.sh` en verde.

## 0.6 Archivos de este directorio

| Fichero | Qué es |
|---|---|
| `audit_f02_leak.py` | Auditoría de la fuga de F02 (0.1). Reutilizable si vuelve a haber feature cerrada con filas pendientes. |
| `README-audit.md` | Resultado de la auditoría, ruta a ruta. |
| `purge_stale.py` | Purga de unidades obsoletas por patrón (idempotente, con copia a `.stale-bak/`). |
| `inspect_unit_segments.py` | Vuelca la distribución por primer segmento de ruta de una unidad: sirve para dimensionar un corte antes de declararlo. |
| `count_matcher.py` | Cuenta filas del ledger que casan con unos prefijos, agrupadas por nivel de ruta. |
| `diff_units_vs_index.py` | Compara los ids presentes en disco con los de `_index.json`. |