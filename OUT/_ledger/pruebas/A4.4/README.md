# pruebas/A4.4/ — `resume.py` + `record_unit_state.py` + simulación de corte

**Fase**: A4.4 — `STATE.md` y reanudación (cierre del Bloque A4 · Orquestación).
**Fecha**: 2026-10-18.
**Plan completo**: `1792363730747-resume-state-a44.md`.

## Entregables

| Archivo | Rol |
|---|---|
| `SKILL/scripts/resume.py` | Orquestador determinista (~330 líneas, Python 3 stdlib). Lee `STATE.md` + `cobertura.csv` + `units/_index.json` + `OUT/09-features/*.partial.md` y produce `resume-plan.{json,md}` con la siguiente fase, totales, orden de ejecución priorizado, unidades in-flight, huérfanas y decisiones de triage pendientes. Opcional: `--regenerate-state-section` reescribe la sección `## Cómo reanudar` de `STATE.md` |
| `SKILL/scripts/record_unit_state.py` | Auxiliar (~120 líneas) con `--verificar`, `--marcar_in_flight`, `--desmarcar_in_flight`. Modifica `cobertura.csv` in-place |
| `OUT/_ledger/pruebas/A4.4/fixtures/cut_cobertura.csv` | Cobertura simulada con 4 unidades verificadas (F11, F14, F18, F20), resto pendiente |
| `OUT/_ledger/pruebas/A4.4/fixtures/cut_STATE.md` | STATE.md con la sección "Última fase cerrada" detectable por el regex de `resume.py` |
| `OUT/_ledger/pruebas/A4.4/fixtures/docs_root/OUT/09-features/F01-documentos-y-editor/01.1-bloques-texto.partial.md` | Documento parcial para F01.1 (simula corte) |
| `OUT/_ledger/pruebas/A4.4/fixtures/docs_root/OUT/09-features/F01-documentos-y-editor/01.4-menciones-inline-actions-emoji.partial.md` | Documento parcial para F01.4 |
| `OUT/_ledger/validate-A4.4.sh` | 10 checks; sale 0 si todo OK |
| `OUT/_ledger/pruebas/A4.4/smoke.log` | Trazas reales (88 líneas) |

## Resumen de la prueba literal del ROADMAP A4.4

> "Cortar la ejecución a mitad de un bloque y reanudar en otra herramienta sin rehacer unidades aprobadas."

La prueba se simula con la fixture `cut_cobertura.csv` (134 verificados
de 4 unidades) + 2 archivos `.partial.md` (F01.1 y F01.4).

**`resume.py` sobre la fixture**:
- `totales`: `asignados=4279 verificados=134 pendientes=4145 in_flight=2 sin_asignar=324`.
- `unidades_verificadas_omitir`: `[F11, F14, F18, F20]`.
- `unidades_in_flight`: `[F01.1, F01.4]` con sus `partial_docs`.
- `orden_ejecucion`: `F01.1` y `F01.4` **primeros** (in_flight), luego las pendientes por prioridad.
- 0 unidades verificadas en el orden de ejecución (no se reejecutan).

**`record_unit_state.py` sobre la fixture**:
- `--verificar F03`: 85 filas pasan a `estado=verificado` (antes 134, después 219).
- `--marcar_in_flight F06`: 35 filas reciben marca `in_flight:` en `verificado_por`.
- `--desmarcar_in_flight F06`: la marca se elimina.
- CSV preserva cabecera y orden de columnas.

**`--regenerate-state-section`**:
- Reemplaza solo la sección `## Cómo reanudar` de `STATE.md` (preserva el resto).
- Documenta la última fase cerrada, totales, siguiente acción y pasos numerados.

## Comandos

```bash
# Generar plan sobre el ledger real
python3 SKILL/scripts/resume.py

# Plan sobre una fixture (para pruebas)
python3 SKILL/scripts/resume.py \
  --ledger OUT/_ledger/pruebas/A4.4/fixtures/cut_cobertura.csv \
  --state OUT/_ledger/pruebas/A4.4/fixtures/cut_STATE.md \
  --docs-root OUT/_ledger/pruebas/A4.4/fixtures/docs_root/OUT/09-features

# Marcar una unidad como verificada
python3 SKILL/scripts/record_unit_state.py --unit F03 --accion verificar \
  --verificado-por "yo"

# Marcar como in_flight (recuperable)
python3 SKILL/scripts/record_unit_state.py --unit F03 --accion marcar_in_flight

# Regenerar la sección "Cómo reanudar" de STATE.md
python3 SKILL/scripts/resume.py --regenerate-state-section

# Validador de la fase
bash OUT/_ledger/validate-A4.4.sh
```

## Esquema del plan (`resume-plan.json`)

```json
{
  "schema_version": 1,
  "generado_en": "2026-10-18T...",
  "fase_actual": null,
  "ultima_fase_cerrada": "A4.3",
  "ultima_fase_por_abrir": "A4.4",
  "totales": {
    "asignados": 4279, "verificados": 134, "pendientes": 4145,
    "in_flight": 2, "sin_asignar": 324, "huerfanos": 0
  },
  "siguiente_accion": "Recuperar 2 unidades in_flight antes de continuar...",
  "orden_ejecucion": [
    {"unit_id": "F01.1", "prioridad": 2, "estado": "in_flight", "concurrencia": "paralela", "archivos_total": 87, "dependencias": []},
    {"unit_id": "F01.4", "prioridad": 2, "estado": "in_flight", ...},
    ...
  ],
  "unidades_in_flight": [
    {"unit_id": "F01.1", "partial_docs": [".../01.1-bloques-texto.partial.md"]}
  ],
  "unidades_verificadas_omitir": ["F11", "F14", "F18", "F20"],
  "unidades_huerfanas": [],
  "decisiones_triage_pendientes": {
    "sin_asignar_count": 324,
    "sin_asignar_doc": "OUT/_ledger/sin_asignar.md"
  }
}
```

## Decisión de diseño: in_flight como artefacto de disco

`in_flight` se modela con **archivos `*.partial.md` en `OUT/09-features/`**,
NO como valor nuevo en la columna `estado` (que sigue siendo `pendiente`).
Esto evita una migración de esquema en `cobertura.csv` y permite que
un agente que muere a mitad de bloque deje rastro natural: el `.md`
sin terminar se renombra a `.partial.md` (convención que `record_unit_state.py`
puede automatizar). El `resume.py` los detecta por nombre y los pone
primeros en el orden de ejecución.

Adicionalmente, `record_unit_state.py --marcar_in_flight` añade una marca
`in_flight: <ts>` en la columna `verificado_por` para redundancia (el
corte puede no haber dejado `.partial.md` en disco).

## Cobertura de la prueba literal del ROADMAP A4.4

| Criterio ROADMAP | Check validador | Resultado |
|---|---|---|
| `resume.py` y `record_unit_state.py` existen | checks 1, 2 | ✅ |
| Fixture con 4 verificados + 2 in_flight | check 2 | ✅ |
| Plan con totales correctos | check 3 | 134v/2if/4145p ✅ |
| `unidades_verificadas_omitir` excluye verificados del orden | check 4 | 0 intersección ✅ |
| in_flight primeros en el orden | check 5 | F01.1 + F01.4 ✅ |
| `--json` produce JSON parseable | check 6 | ✅ |
| `record --verificar` muta CSV | check 7 | 134 → 219 ✅ |
| `record --marcar/desmarcar_in_flight` | check 8 | ✅ |
| `--regenerate-state-section` reescribe solo la sección | check 9 | ✅ |
| Resume sobre el real devuelve plan no vacío | check 10 | 4279 asignados ✅ |

Plan completo: `1792363730747-resume-state-a44.md`. Log: `smoke.log`.

**Cierre del Bloque A4 (Orquestación).** Siguiente fase: **A5.1 —
Piloto F08** (ejecutar el pipeline completo sobre la feature de
búsqueda, autor → validadores → revisor; gate 🔒 por el revisor
aprobando con 100% de archivos cubiertos).
