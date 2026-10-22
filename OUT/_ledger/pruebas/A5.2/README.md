# pruebas/A5.2 — Ajuste de la skill

**Fase**: A5.2 — Ajuste de la skill (Bloque A5 · Piloto).
**Fecha**: 2026-10-19.
**Plan completo**: `/Users/martin/.local/share/kilo/plans/1792365664864-fase-a52-ajuste-skill.md`.
**Estado**: ✅ Cerrado y aprobado.

## Entregables

| Archivo | Rol |
|---|---|
| `SKILL/CHANGELOG.md` | Diff narrativo de la skill (entregable principal de A5.2) |
| `SKILL/scripts/run_subagent.py` | Reescrito: solo modo `revisor` + `--gate-100` + auto-elevación |
| `SKILL/scripts/run_subagent_placeholder.py` | Renombre del antiguo modo `autor` (mock de A4.3) |
| `SKILL/scripts/run_subagent_author.sh` | Wrapper de producción que invoca un LLM externo |
| `SKILL/references/diagram-conventions.md` | + trampas Mermaid (H1, H2) |
| `SKILL/references/evidence-rules.md` | + ejemplo canónico de ruta (H3) |
| `SKILL/references/subagent-contract.md` | + nota `out_root` + auto-elevación pct + triage extras (H5, H6, H8) |
| `SKILL/references/subagent-autor-prompt.md` | + aviso placeholder + recordatorio ruta (H3, H4) |
| `SKILL/references/subagent-revisor-prompt.md` | + fila B4.* + caso `--gate-100` (H6) |
| `SKILL/references/patterns.md` | + §8 canales Rust→Dart + §9 feature↔unidad (H7) |
| `OUT/22-preguntas-abiertas.md` | + 4 preguntas abiertas del piloto F08 (H9) |
| `OUT/_ledger/pruebas/A5.2/README.md` | Este archivo |
| `OUT/_ledger/pruebas/A5.2/validate-A5.2.sh` | Smoke ejecutable del gate |
| `OUT/_ledger/pruebas/A5.2/gen-diff.sh` | Regenera el diff unificado de `references/` |
| `OUT/_ledger/pruebas/A5.2/diff-references.patch` | Diff unificado de los 6 archivos editados |

## Resumen de la prueba literal del ROADMAP A5.2

> "diff de `references/` documentado en `SKILL/CHANGELOG.md`."

| Check | Esperado | Real |
|---|---|---|
| `SKILL/CHANGELOG.md` existe, sección `## [0.2.0]` con al menos 3 entradas Added/Changed/Fixed | sí | ✅ 6 Added / 6 Changed / 6 Fixed / 0 Removed |
| `run_subagent_placeholder.py` existe y sigue funcionando como mock | sí | ✅ `python3 run_subagent_placeholder.py --rol autor --unit F08.json` produce doc placeholder |
| `run_subagent.py --rol autor` → error de uso | sí | ✅ `error: argument --rol: invalid choice: 'autor'` |
| `run_subagent.py --rol revisor` sobre F08 re-ejecutado | `aprobado` | ✅ `veredicto=aprobado, correcciones=0, pct_efectivo=30` |
| `--gate-100` funciona | pct=100 en features 🔒 | ✅ `_effective_pct(F01, 30, False) == 100`; con `--gate-100` siempre 100 |
| `OUT/22-preguntas-abiertas.md` contiene las 4 preguntas abiertas de F08 | sí | ✅ sección "De F08 — Búsqueda e indexación (2026-10-18)" con 4 entradas |
| `ROADMAP.md` línea 110 contiene `✅` | sí | ✅ |
| `validate-A5.2.sh` 5/5 checks | exit 0 | ✅ |

## Hallazgos del piloto A5.1 que motivaron los cambios

| # | Hallazgo | Acción |
|---|---|---|
| H1 | `classDiagram` rompe con `Option~T~` y `Vec~T~` |规范的写法 documentada en `diagram-conventions.md` |
| H2 | `stateDiagram-v2` rompe con `<br/>` y `:` extras |规范的写法 documentada |
| H3 | Rutas cortas en evidencias → 73 % de errores iniciales | Ejemplo canónico en `evidence-rules.md` |
| H4 | `run_subagent.py --rol autor` es un mock que no produce documentos reales | Renombre a `run_subagent_placeholder.py`; wrapper real `run_subagent_author.sh` |
| H5 | `--out-root` debe ser la raíz del proyecto, no `OUT/` | Documentado en script y contrato |
| H6 | Auto-elevación de `evidencia_minima_pct` para features 🔒 no implementada | `--gate-100` + mapeo `feature_id → 100` en el script |
| H7 | F08: discrepancia entre descripción narrativa de ROADMAP y unidad real | `patterns.md §9` formaliza la precedencia unidad > ROADMAP |
| H8 | 4 archivos extra detectados en F08 necesitan triage explícito | Procedimiento en `subagent-contract.md §3` |
| H9 | 4 preguntas abiertas del piloto no volcadas al global | Añadidas a `OUT/22-preguntas-abiertas.md` |

## Comandos de reproducción

```bash
# 1. Validar que el modo autor ya no existe en run_subagent.py
python3 SKILL/scripts/run_subagent.py --rol autor --unit OUT/_ledger/units/F08.json
# → debe fallar con "invalid choice: 'autor'"

# 2. Validar que el placeholder sigue disponible (compatibilidad A4.3)
python3 SKILL/scripts/run_subagent_placeholder.py --rol autor --unit OUT/_ledger/units/F08.json
# → produce el doc placeholder en OUT/OUT/09-features/...

# 3. Re-ejecutar el revisor sobre F08
python3 SKILL/scripts/run_subagent.py --rol revisor --unit OUT/_ledger/units/F08.json --out /tmp/f08_revisor.json --out-root .

# 4. Validar gate-100 con F01 (debe elevar pct a 100 automáticamente)
python3 -c "
import sys, json
sys.path.insert(0, 'SKILL/scripts')
import importlib.util
spec = importlib.util.spec_from_file_location('ra', 'SKILL/scripts/run_subagent.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
u = json.load(open('OUT/_ledger/units/F01.0.1.json'))
print('F01 pct sin flag =', m._effective_pct(u, 30, False))   # 100
print('F01 pct con --gate-100 =', m._effective_pct(u, 30, True))  # 100
"

# 5. Wrapper de producción (requiere un LLM externo configurado en KILO_AUTHOR_CMD)
bash SKILL/scripts/run_subagent_author.sh --help

# 6. Regenerar el diff unificado
bash OUT/_ledger/pruebas/A5.2/gen-diff.sh

# 7. Smoke A5.2 (5/5 checks)
bash OUT/_ledger/pruebas/A5.2/validate-A5.2.sh
```

## Estructura final de `SKILL/`

```
SKILL/
├── AGENTS.md
├── CHANGELOG.md                         # ← nuevo (A5.2)
├── SKILL.md
├── references/
│   ├── diagram-conventions.md           # ← editado
│   ├── evidence-rules.md                # ← editado
│   ├── export-template.md
│   ├── feature-template.md
│   ├── patterns.md                      # ← editado
│   ├── repo-map.md
│   ├── subagent-autor-prompt.md         # ← editado
│   ├── subagent-contract.md             # ← editado
│   └── subagent-revisor-prompt.md       # ← editado
├── scripts/
│   ├── …
│   ├── run_subagent.py                  # ← reescrito (solo revisor)
│   ├── run_subagent_placeholder.py      # ← nuevo (mock de A4.3)
│   └── run_subagent_author.sh           # ← nuevo (wrapper de producción)
└── templates/
    └── …
```

## Pendientes transferidos a Parte B

- El triage de los 4 archivos extra de F08 (`flowy-core/src/{deps_resolve/search_deps.rs, module.rs, lib.rs, app_life_cycle.rs}`) sigue abierto: reasignar, mover a F2x, o mantener en sus features actuales.
- `SearchFilterPB` sin uso → cablear o eliminar (F08 §17).
- `FolderSearchHandler` comentado en frontend/rust-lib/flowy-core/src/deps_resolve/search_deps.rs:13 → reactivar o documentar como reservado.
- `SearchNotification` declarado pero sin emisor → decidir si se elimina o se cablea.
- Próximo piloto de Parte B: **F01 — Documentos y editor** (B3.F01.0–B3.F01.9) o **F02 — Bases de datos** (B3.F02.0–B3.F02.12), según criterio de cobertura + dependencias.
