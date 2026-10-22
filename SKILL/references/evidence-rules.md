---
id: R-003
titulo: Reglas de evidencia (ruta:línea) y etiquetas
fuente: AGENTS.md §6 (líneas 146–152)
archivos_cubiertos: [AGENTS.md]
estado: verificado
---

# R-003 — Reglas de evidencia (ruta:línea) y etiquetas

> Toda afirmación en la salida de la skill se ancla a evidencia trazable. Las tres etiquetas (`[VERIFICADO]`, `[INFERIDO]`, `[NO DETERMINADO]`) tienen semántica precisa y consecuencias distintas. `validate_evidence.py` (A3.2) y `validate_template.py` (A3.3) aplican estas reglas de forma automática.

## Las 5 reglas bloqueantes

1. **Cita `ruta:línea` o `ruta:inicio–fin`.** La ruta es **siempre relativa a la raíz del repo**, con prefijo de fuente si no es la principal. `validate_evidence.py` busca la ruta en `OUT/_ledger/inventario.json`; si la ruta está incompleta, falla con `E_PATH_NOT_IN_INVENTORY`. Formas canónicas (refinadas en el piloto F08, A5.2):
   - ✅ `appflowy/frontend/rust-lib/flowy-search/src/services/manager.rs:42–46` — ruta completa, fuente implícita `appflowy` (la principal).
   - ✅ `appflowy:appflowy/frontend/rust-lib/flowy-search/src/services/manager.rs:42–46` — prefijo de fuente explícito (recomendado para uniformidad con archivos de `collab` o `editor`).
   - ✅ `collab:collab-document/src/document.rs:120` — repo `AppFlowy-Collab`.
   - ✅ `editor:lib/src/plugins/html/html_document_encoder.dart:40` — repo `appflowy-editor`.
   - ❌ `manager.rs:42` — **ruta corta**: el validador la busca como `appflowy/manager.rs`, no existe en el inventario, y falla aunque el archivo real sea `appflowy/frontend/rust-lib/flowy-search/src/services/manager.rs`. **Esta fue la causa del 73 % de los errores iniciales del piloto F08.** Regla: nunca cites una ruta que no tenga el prefijo `appflowy/`, `collab/.../`, o `editor/.../` (o sus variantes con `appflowy:`, `collab:`, `editor:`).

2. **Etiqueta toda afirmación factual.** Por defecto `[VERIFICADO]` cuando hay evidencia. `[INFERIDO]` cuando se razona a partir del código pero no se lee directamente. `[NO DETERMINADO]` cuando la fuente no alcanza; **toda** etiqueta `[NO DETERMINADO]` debe re-listarse en `OUT/22-preguntas-abiertas.md`.

3. **Prohibido inventar.** Clases, eventos, archivos, campos. Si dudas, `rg` antes de escribirlo. Si el `rg` no encuentra, etiqueta `[NO DETERMINADO]` y deja la pregunta abierta.

4. **Fragmentos de código ≤ 25 líneas**, siempre con referencia. Si necesitas más, parte en varios fragmentos y enlázalos por nombre (`(continúa en fn foo:80)`).

5. **Inventario es la fuente de verdad.** Nunca citar un archivo que no esté en `OUT/_ledger/inventario.json`. `validate_evidence.py` lo verifica contra el CSV.

## Ejemplos sintéticos de uso

### Afirmación `[VERIFICADO]`

> El handler `open_document` se registra en `DocumentEvent::OpenDocument` con input `OpenDocumentPayloadPB` y output `DocumentDataPB` `[VERIFICADO]` (`frontend/rust-lib/flowy-document/src/event_map.rs:18–24`).

### Afirmación `[INFERIDO]`

> El debounce de notificaciones en `flowy-notification` agrupa eventos por `debounce_ms` configurado por evento `[INFERIDO]` — el código revisado muestra el parámetro pero no se localizó su valor por defecto en este snapshot.

### Afirmación `[NO DETERMINADO]`

> El tipo concreto de `Collab` usado para `user_awareness` `[NO DETERMINADO]`. Pendiente de revisar `collab-user/src/awareness.rs` cuando se clone en A1.1.

## Consecuencias operativas

| Etiqueta | Ledger (`cobertura.csv`) | Preguntas abiertas | Validador |
|---|---|---|---|
| `[VERIFICADO]` | `verificado` | no | `validate_evidence.py` ✓ |
| `[INFERIDO]` | `pendiente` | no | `validate_evidence.py` ✓ + nota explicativa |
| `[NO DETERMINADO]` | `pendiente` | **sí** (en `22-…`) | `validate_evidence.py` ⚠ + recordatorio |
| Ruta corta (sin prefijo `appflowy/`, `collab/`, `editor/`) | no se mueve | no | `validate_evidence.py` **falla** con `E_PATH_NOT_IN_INVENTORY` aunque el archivo exista. |

## Relacionado con

- `R-002 patterns.md` — los patrones que se documentan con estas reglas.
- `R-004 diagram-conventions.md` — los diagramas también llevan evidencia `ruta:línea` por nodo cuando representan código real.
- `SKILL/SKILL.md §2` — reglas R1–R5 (mismas reglas en formato compacto para el router).
- `PROMPT.md §7` — convenciones transversales (incluye idioma y estilo).
