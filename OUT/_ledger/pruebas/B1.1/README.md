# pruebas/B1.1/ — `03-estructura-del-repo.md` (2026-10-19)

**Objetivo:** verificar que el documento raíz del Bloque B1 describe el monorepo AppFlowy en su totalidad: cada carpeta de primer y segundo nivel de `SRC/{appflowy,collab,editor}` aparece con su propósito, las tablas de conteos (por capa, fuente × lenguaje, fuente × capa, assets) están alineadas con el inventario real, y todos los validadores pasan en verde.

**Ejecutar:**

```bash
OUT/_ledger/validate-B1.1.sh
```

**Salida (2026-10-19):**

```
─── validate_template ───
OUT/03-estructura-del-repo.md: OK
--- summary: files=1 ok=1 errors=0 warns=0 ---
OK: template
─── validate_evidence ───
--- summary: refs=32 ok=32 errors=0 ---
OK: evidence
─── validate_mermaid ───
OK=5 FAIL=0
OK: mermaid
─── validate_B1_1_coverage ───
OK: coverage

OK: B1.1 (template+evidence+mermaid+coverage, 4/4 checks)
exit=0
```

## Resultado por validador

| Validador | Métrica | Resultado |
|---|---|---|
| `validate_template.py --template structure` (modo nuevo) | frontmatter + 11 secciones numeradas + Relacionado con | OK, 0 errors / 0 warns |
| `validate_evidence.py` | refs `[fuente:]ruta:línea` resueltas contra `inventario.json` | 32 / 32 OK |
| `validate_mermaid.sh` | bloques `mermaid` renderizan con `mmdc` | 5 / 5 OK |
| `validate_B1_1_coverage.py` (nuevo) | prueba literal del ROADMAP: cada carpeta L1+L2 (excl. `.git*`) está declarada en el doc | 72 / 72 carpetas; 0 missing |

## Cobertura de carpetas (prueba literal del ROADMAP)

Total de carpetas reales L1+L2 (excluyendo `.git/` y `.github/`) en `SRC/`: **72**.
Cada una se nombra explícitamente en `OUT/03-estructura-del-repo.md`. Exclusiones documentadas en §11.1 del propio doc:

- `appflowy/frontend/.vscode/` — config de IDE.
- `appflowy/doc/imgs/`, `appflowy/doc/readme/` — recursos auxiliares; el doc los nombra como sub-carpetas L2 de `doc/`.
- `editor/assets/images/`, `editor/documentation/images/` — recursos (no código).
- `appflowy/frontend/rust-lib/target/` — generado por Cargo.

## Tablas de conteos (cruzan con `inventario.json`)

| Tabla | Conteo total | Coherencia con `inventario.json` |
|---|---:|---|
| §7 — por capa | 4 603 | ✅ suma de `by_capa` |
| §7.1 — fuente × capa | 4 603 | ✅ suma por fuente y global |
| §8 — fuente × lenguaje (top) | 4 603 | ✅ `dart=2 581` y `rust=1 025` coinciden con `find` |
| §9 — assets | 1 186 (63,5 MB) | ✅ `assets.json:counts.assets` |

## Diagramas (5 bloques Mermaid, todos validados)

1. §10.1 — `flowchart LR` raíz con subgraphs `AppFlowy` / `Collab` / `Editor` y las 15 capas (`ui`, `bloc`, `service`, `rust-handler`, `rust-manager`, `collab`, `persistence`, `server`, `ffi`, `dispatch`, `codegen`, `test`, `build`, `config`, `i18n`).
2. §10.2 — subgrafo Rust A: crates de feature + infraestructura (≤ 60 nodos).
3. §10.2 — subgrafo Rust B: `build-tool/*` + `event-integration-test` + crates que usan `derive`.
4. §10.3 — subgrafo Dart: `appflowy_flutter` + 7 paquetes internos + `appflowy_editor` (git override).
5. §10.4 — subgrafo `collab/`: 4 crates de dominio + auxiliares + plugins + importer.

## Extensión del validador de plantilla

`SKILL/scripts/validate_template.py` se extendió con un modo `structure` para los documentos raíz del Bloque B1 (id `B1.x`):

```python
"structure": {
    "required_sections": list(range(1, 12)),
    "optional_sections": [],
    "id_pattern": re.compile(r"^B1\.\d+$"),
    "estados": {"verificado", "pendiente"},
},
```

Cambios: añadir la entrada a `TEMPLATES` y una rama de auto-detección en `detect_template` (antes de `export`). Backward-compatible: `feature` y `export` no se tocan. Justificación: sienta precedente para `02-stack-y-dependencias.md` (B1.2), `04-arquitectura-global.md` (B1.3), `05-arranque-y-ciclo-de-vida.md` (B1.4), `06-puente-flutter-rust/` (B1.5), `07-motor-colaborativo-crdt/` (B1.6), `08-persistencia/` (B1.7).

## Artefactos

| Archivo | Contenido |
|---|---|
| `folders-l1-l2.txt` | 139 líneas: listado derivado del inventario agrupado por fuente y nivel. |
| `real-folders-{appflowy,collab,editor}.txt` | Resultado crudo de `find -type d -maxdepth 2` sobre cada fuente. |
| `validate_B1_1_coverage.py` | Script nuevo (3,2 KB) que automatiza la prueba literal. |
| `validate_template.log` / `validate_evidence.log` / `validate_mermaid.log` | Salida de los 3 validadores A3.x. |
| `coverage.json` | Resultado estructurado del validador de cobertura. |
| `OUT/_ledger/validate-B1.1.sh` | Suite bash que orquesta los 4 checks (template + evidence + mermaid + coverage). |
| `OUT/03-estructura-del-repo.md` | Documento entregado (583 líneas, 12 secciones `## `). |

## Cierre del Bloque B1.1

| Entregable | Tamaño | Estado |
|---|---|---|
| `OUT/03-estructura-del-repo.md` | 583 líneas · 32 refs verificadas · 5 diagramas Mermaid | ✅ |
| `OUT/_ledger/pruebas/B1.1/validate_B1_1_coverage.py` | 3,2 KB (nuevo) | ✅ |
| `OUT/_ledger/validate-B1.1.sh` | 1,2 KB (nuevo) | ✅ 4/4 checks |
| `SKILL/scripts/validate_template.py` | +7 líneas (modo `structure`) | ✅ backward-compatible |

Próxima fase: **B1.2 — `02-stack-y-dependencias.md` + `17-grafo-dependencias.md`**.
