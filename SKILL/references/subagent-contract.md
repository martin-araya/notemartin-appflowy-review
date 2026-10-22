# R-008 — Contrato del subagente (autor + revisor)

> Skill: `notemartin-appflowy-review` · Bloque A4 · A4.3.
> Referencia operativa: `AGENTS.md §8` (líneas 167–174) y `SKILL.md §2` (líneas 55–60).
>
> Este documento es la **fuente de verdad** de los esquemas JSON de
> entrada y salida de los dos subagentes del Bloque B (features y motor).
> Su contenido se inyecta literal en `subagent-autor-prompt.md` y
> `subagent-revisor-prompt.md`.

## 1. Modelo general

- **Orquestador**: ejecuta scripts (`build_units.py`, validadores),
  mantiene el ledger, crea unidades de trabajo, asigna, integra,
  dispara verificación. No escribe documentos de feature.
- **Unidad de trabajo**: `OUT/_ledger/units/<id>.json` (producida por
  `build_units.py` en A4.2). Una unidad = una feature o sub-feature.
- **Subagente autor**: lee todos los archivos de la unidad (no
  excerpts), redacta el documento Markdown con la plantilla
  correspondiente, devuelve un `AutorOutput` estricto.
- **Subagente revisor**: contexto limpio, sin acceso al razonamiento
  del autor. Ejecuta los tres validadores (`validate_evidence.py`,
  `validate_template.py`, `validate_mermaid.sh`) y hace muestreo
  semántico de las afirmaciones. Devuelve `RevisorOutput` estricto.

Si la plataforma no soporta subagentes, el orquestador ejecuta las
unidades en serie con el mismo contrato; el revisor sigue siendo una
pasada separada con contexto limpio (ver `AGENTS.md §9`).

## 2. Esquema `AutorInput`

El orquestador entrega al autor un objeto JSON con este esquema:

```json
{
  "schema_version": 1,
  "unit_id": "F11",
  "unit_path": "OUT/_ledger/units/F11.json",
  "src_root": "SRC",
  "inventario_path": "OUT/_ledger/inventario.json",
  "catalogos_dir": "OUT/_ledger/extract",
  "plantilla": "feature",
  "plantilla_path": "SKILL/references/feature-template.md",
  "out_root": "OUT",
  "max_secciones": 19,
  "allowed_refs": ["SKILL/references", "OUT/_ledger/extract", "OUT/_ledger/cobertura.csv"]
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `unit_id` | string | Identificador de la unidad (`Fxx` o `Fxx.y`). |
| `unit_path` | string (ruta) | Ruta al `units/<id>.json`. |
| `src_root` | string (ruta) | Raíz de los clones (`SRC/`). |
| `inventario_path` | string (ruta) | Ruta al inventario. |
| `catalogos_dir` | string (ruta) | Directorio con `extract/*.json`. |
| `plantilla` | `"feature"` \| `"export"` | Plantilla a aplicar. |
| `plantilla_path` | string (ruta) | Ruta al `.md` de la plantilla. |
| `out_root` | string (ruta) | **Raíz del proyecto** (no `OUT/`). El script concatena `out_root / unit.documento` y `unit.documento` ya empieza por `OUT/...`. Pasar `--out-root OUT/` hace que el script busque el documento en `OUT/OUT/...` y devuelva `error: fatal`. Lección del piloto F08 (A5.1). |
| `max_secciones` | int | 19 para feature, 11 para export. |
| `allowed_refs` | array de string | Rutas que el autor puede leer. |

El autor debe **rechazar** la entrada si `schema_version != 1` o si
faltan campos obligatorios.

## 3. Esquema `AutorOutput`

El autor devuelve un objeto JSON con este esquema:

```json
{
  "schema_version": 1,
  "documento": "OUT/09-features/F11-exportacion-ui/F11-exportacion-ui.md",
  "filas_ledger_cubiertas": [
    {"fuente": "appflowy", "ruta": "appflowy/frontend/appflowy_flutter/lib/plugins/shared/share/export_tab.dart"}
  ],
  "archivos_extra_detectados": [
    {"fuente": "appflowy", "ruta": "appflowy/.../otro.dart", "motivo": "Necesario para sección 4 (eventos FFI)."}
  ],
  "preguntas_abiertas": [
    "El handler de `ExportDocument` (events.json:flowy-folder) ¿se ejecuta en `af_cloud` o en local? [NO DETERMINADO]"
  ],
  "metricas": {
    "secciones_rellenas": 19,
    "afirmaciones_verificadas": 12,
    "afirmaciones_inferidas": 3,
    "diagramas_mermaid": 2
  }
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `documento` | string (ruta) | Ruta del `.md` creado, relativa a `OUT/`. |
| `filas_ledger_cubiertas` | array | Pares `(fuente, ruta)` del `cobertura.csv` efectivamente documentados. |
| `archivos_extra_detectados` | array | Pares `(fuente, ruta)` que la unidad necesitaba pero no contenía. El orquestador decide reasignación o feature nueva (`F2x`). |
| `preguntas_abiertas` | array de string | Cosas marcadas como `[NO DETERMINADO]` que irán a `OUT/22-preguntas-abiertas.md`. |
| `metricas` | object | Conteos autorreportados; el revisor los contrasta con la realidad. |

Reglas duras:
- `filas_ledger_cubiertas` no puede estar vacío si `archivos_total > 0`.
- `documento` debe estar dentro de `out_root` y coincidir con
  `unit["documento"]` declarado en `A4.2` (renombrar sin coordinación
  rompe el resto del pipeline).
- `archivos_extra_detectados` solo se usa para archivos que **bloquean**
  la unidad; observaciones menores van a `preguntas_abiertas`.

**Triage de `archivos_extra_detectados` (procedimiento del orquestador, A5.2 H8):** al recibir el `AutorOutput`, el orquestador tiene 3 opciones:
1. **Reasignar el archivo** a la feature actual (`cobertura.csv::feature_ids` se actualiza y la unidad se regenera).
2. **Crear una feature nueva `F2x`** y mover el archivo allí.
3. **No tocar** y dejar la observación en `preguntas_abiertas` (aceptable si el archivo es solo mencionado en la prosa pero no se cita como evidencia principal).

En el piloto F08 (A5.1) se detectaron 4 archivos así (`flowy-core/src/deps_resolve/search_deps.rs`, `module.rs`, `lib.rs`, `app_life_cycle.rs`); se eligió la opción 3 porque eran menciones en §7/§19/§10.2 sin reclamar propiedad.

## 4. Esquema `RevisorInput`

```json
{
  "schema_version": 1,
  "documento": "OUT/09-features/F11-exportacion-ui/F11-exportacion-ui.md",
  "unit": { /* copia completa de OUT/_ledger/units/<id>.json */ },
  "inventario": "OUT/_ledger/inventario.json",
  "evidencia_minima_pct": 30
}
```

`evidencia_minima_pct` es 30 por defecto; **se eleva automáticamente a 100** cuando se cumple cualquiera de estas condiciones (auto-elevación implementada en `run_subagent.py` desde A5.2):

| Trigger | `evidencia_minima_pct` efectivo |
|---|---|
| `unit.feature_id ∈ {"F01", "F02", "F06"}` | 100 |
| `unit.dependencias[*].id` empieza por `B4.` (motor de export/import) | 100 |
| Flag CLI `--gate-100` (re-verificaciones forzadas, override explícito) | 100 |
| Resto | 30 (default) |

El JSON `RevisorOutput` incluye `muestreo_verificado.gate_100_explicit` y `muestreo_verificado.gate_100_auto` para que el orquestador exija el muestreo correcto sin ambigüedad. Tabla de muestreo detallada en `subagent-revisor-prompt.md` §3.

## 5. Esquema `RevisorOutput`

```json
{
  "schema_version": 1,
  "veredicto": "aprobado",
  "correcciones": [
    {
      "tipo": "evidence",
      "archivo": "OUT/09-features/.../F11.md",
      "linea": 42,
      "mensaje": "E_PATH_NOT_IN_INVENTORY: appflowy/frontend/.../inventado.dart"
    }
  ],
  "muestreo_verificado": {
    "pct": 30,
    "total_afirmaciones": 12,
    "verificadas": 4,
    "afirmaciones": [
      {"linea": 18, "etiqueta": "VERIFICADO", "evidencia": "appflowy:.../x.dart:42", "resultado": "ok"},
      {"linea": 25, "etiqueta": "INFERIDO", "evidencia": "—", "resultado": "no_aplica"}
    ]
  },
  "validaciones": {
    "evidence": {"exit": 0, "errores": 0},
    "template": {"exit": 0, "errores": 0},
    "mermaid": {"exit": 0, "bloques_ok": 2, "bloques_ko": 0}
  }
}
```

| Campo | Tipo | Descripción |
|---|---|---|
| `veredicto` | `"aprobado"` \| `"rechazado"` | Aprobado solo si las 3 validaciones pasan y el muestreo no encuentra errores. |
| `correcciones` | array | Vacío si `aprobado`. Cada entrada es accionable por el autor. |
| `muestreo_verificado` | object | Detalle del muestreo semántico. |
| `validaciones` | object | Resultado de los 3 validadores (trazabilidad). |

## 6. Reglas duras (aplican a autor y revisor)

- **Evidencia**: toda afirmación lleva `ruta:línea` o `ruta:inicio–fin`
  con prefijo de fuente si no es la principal (`appflowy:`, `editor:`,
  `collab:`). Inventar archivos, eventos o clases está prohibido.
- **Fragmentos**: ≤ 25 líneas, siempre con referencia.
- **Idiomas**: prosa en español técnico; identificadores, rutas,
  comandos y código en original.
- **Diagramas**: Mermaid con IDs sin espacios; cada diagrama precedido
  de una frase que diga qué muestra y seguido de su lectura en prosa.
- **Frontmatter**: 5 campos obligatorios
  (`id`, `titulo`, `fuente`, `archivos_cubiertos`, `estado`); `id`
  debe matchear la regex `^F\d+(\.\d+)?$` (feature) o `^B\d+(\.\d+)?$`
  (export).
- **Cobertura**: si una unidad se rechazó por cobertura, el autor
  rellena `archivos_extra_detectados`; el orquestador decide.

## 7. Errores recuperables vs fatales

| Caso | Comportamiento |
|---|---|
| Falta `unit_path` en `AutorInput` | Autor devuelve error fatal (`exit 2`); no escribe documento. |
| Falta un archivo de la unidad en disco | Autor lo declara en `archivos_extra_detectados` y deja la sección con cita parcial. |
| Validador evidencia falla | Revisor devuelve `rechazado` con `correcciones[tipo=evidence]`. |
| Validador plantilla falla | Revisor devuelve `rechazado` con `correcciones[tipo=template]`. |
| Validador Mermaid falla | Revisor devuelve `rechazado` con `correcciones[tipo=mermaid]`. |
| Muestreo < `evidencia_minima_pct` | Revisor anota warning; el orquestador puede repetir con más pct. |
| Muestreo detecta evidencia falsa | Revisor devuelve `rechazado` con `correcciones[tipo=evidencia_falsa]`. |
