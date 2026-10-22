# pruebas/A4.3/ — `run_subagent.py` + 3 contratos de subagente

**Fase**: A4.3 — Contratos de subagente (Bloque A4 · Orquestación).
**Fecha**: 2026-10-18.
**Plan completo**: `1792363730747-subagent-contracts-a43.md`.

## Entregables

| Archivo | Rol |
|---|---|
| `SKILL/references/subagent-contract.md` | **Esquemas canónicos** de los 4 JSON (AutorInput, AutorOutput, RevisorInput, RevisorOutput) + reglas duras |
| `SKILL/references/subagent-autor-prompt.md` | Prompt del subagente autor (referenciado en `SKILL.md:105`) |
| `SKILL/references/subagent-revisor-prompt.md` | Prompt del subagente revisor (referenciado en `SKILL.md:106`) |
| `SKILL/scripts/run_subagent.py` | Mock determinista (~360 líneas, Python 3 stdlib). Modo autor crea el documento; modo revisor ejecuta los 3 validadores |
| `OUT/_ledger/pruebas/A4.3/fixtures/trivial_unit.json` | Copia de `OUT/_ledger/units/F11.json` (2 archivos reales) |
| `OUT/_ledger/validate-A4.3.sh` | 9 checks; sale 0 si todo OK |
| `OUT/_ledger/pruebas/A4.3/smoke.log` | Trazas reales (104 líneas) |

## Resumen de la prueba literal del ROADMAP A4.3

> "Ejecutar autor+revisor en una unidad trivial devuelve JSON válido."

**Unidad trivial**: `F11` (2 archivos: `export_tab.dart` y
`document_exporter.dart`).

**Modo autor**:
- Carga la unidad, lee los archivos reales de `SRC/`, captura la
  primera línea no vacía de cada uno.
- Genera `OUT/09-features/F11-exportacion-ui/F11-exportacion-ui.md`
  con las 19 secciones de la plantilla `feature` (frontmatter válido,
  secciones con prosa placeholder, Mermaid placeholders en §3/§9/§10,
  tabla real de archivos en §12 con citas `ruta:línea` reales).
- Devuelve `AutorOutput` con `filas_ledger_cubiertas = 2`,
  `archivos_extra_detectados = 0`, `preguntas_abiertas = [...]`.

**Modo revisor**:
- Ejecuta los 3 validadores reales sobre el documento creado:
  - `validate_evidence.py` → exit 0 (las 2 citas de §12 son correctas).
  - `validate_template.py` → exit 0 (frontmatter + 19 secciones en orden).
  - `validate_mermaid.sh` → exit 0 (los 3 bloques Mermaid placeholder
    renderizan OK con `mmdc`).
- Devuelve `RevisorOutput`: `veredicto: "aprobado"`, 0 correcciones,
  muestreo `pct: 0` (mock no muestrea realmente).

**JSON strict**: ambos modos producen JSON parseable con
`schema_version: 1` y todos los campos obligatorios del contrato.

## Comandos

```bash
# Modo autor: crea el documento y devuelve AutorOutput a --out
python3 SKILL/scripts/run_subagent.py \
  --rol autor \
  --unit OUT/_ledger/pruebas/A4.3/fixtures/trivial_unit.json \
  --out /tmp/autor.json --out-root /tmp

# Modo revisor: ejecuta validadores y devuelve RevisorOutput a --out
python3 SKILL/scripts/run_subagent.py \
  --rol revisor \
  --unit OUT/_ledger/pruebas/A4.3/fixtures/trivial_unit.json \
  --out /tmp/revisor.json --out-root /tmp

# JSON a stdout (consumo programático)
python3 SKILL/scripts/run_subagent.py --rol autor --json ...

# Validador de la fase
bash OUT/_ledger/validate-A4.3.sh
```

## Esquema del contrato (resumen)

| Esquema | Campos obligatorios |
|---|---|
| `AutorInput` | `schema_version`, `unit_id`, `unit_path`, `src_root`, `inventario_path`, `catalogos_dir`, `plantilla`, `plantilla_path`, `out_root`, `max_secciones`, `allowed_refs` |
| `AutorOutput` | `schema_version`, `documento`, `filas_ledger_cubiertas[]`, `archivos_extra_detectados[]`, `preguntas_abiertas[]`, `metricas` |
| `RevisorInput` | `schema_version`, `documento`, `unit`, `inventario`, `evidencia_minima_pct` |
| `RevisorOutput` | `schema_version`, `veredicto` (`aprobado`\|`rechazado`), `correcciones[]`, `muestreo_verificado`, `validaciones.{evidence,template,mermaid}` |

## Tabla de muestreo (revisor)

| `unit.feature_id` | `evidencia_minima_pct` |
|---|---|
| `F01`, `F02`, `F06` | 100 |
| Motor export/import (`unit.dependencias[*].id` empieza por `B4.`) | 100 |
| Resto | 30 |

## Decisión de diseño: mock vs LLM real

El runner es un **mock determinista** (no usa un LLM). Esto:
- Cumple la prueba literal del ROADMAP sin depender de un LLM en CI.
- Produce un documento **estructuralmente válido** (pasa los 3
  validadores) pero **semánticamente vacío** (citas reales a la
  primera línea del archivo; resto es placeholder).
- Permite testear el contrato (entrada/salida JSON, validadores,
  veredicto) sin coste de API ni flake de LLM.

La integración con un LLM real (Hermes/Cline/Kilo) se materializa en
el Bloque B (features y motor) cuando se redactan los documentos de
cada feature usando estos prompts como input del modelo.

## Cobertura de la prueba literal del ROADMAP A4.3

| Criterio ROADMAP | Check validador | Resultado |
|---|---|---|
| Prompts de autor y revisor en `references/` | check 1 | 3 archivos no vacíos ✅ |
| Entrada/salida exactas de `AGENTS.md §8` | contrato + prompts | 4 esquemas + reglas duras ✅ |
| Ejecutar autor+revisor en unidad trivial | checks 3–6 | JSON parseable en ambos ✅ |
| Devuelve JSON válido | checks 3, 5 | `schema_version: 1` + campos completos ✅ |
| Contrato coherente | check 7 | 4 esquemas presentes ✅ |

Plan completo: `1792363730747-subagent-contracts-a43.md`. Log: `smoke.log`.

**Siguiente fase**: **A4.4 — `STATE.md` y reanudación** (el
orquestador puede retomar desde cualquier fase leyendo `STATE.md` +
ledger; cortar la ejecución a mitad de un bloque y reanudar en otra
herramienta).
