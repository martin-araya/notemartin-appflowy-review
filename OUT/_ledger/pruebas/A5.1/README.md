# pruebas/A5.1 — Piloto F08 Búsqueda

**Fase**: A5.1 — Piloto F08 Búsqueda (Bloque A5 · Piloto).
**Fecha**: 2026-10-18.
**Plan completo**: `/Users/martin/.local/share/kilo/plans/1792365664864-fase-a51-piloto-f08-busqueda.md`.
**Estado**: ✅ Cerrado y aprobado.

## Entregables

| Archivo | Rol |
|---|---|
| `OUT/09-features/F08-busqueda-e-indexacion/F08-busqueda-e-indexacion.md` | Documento principal (476 líneas, 19 secciones) |
| `OUT/_ledger/autor_f08_output.json` | `AutorOutput` con 21 filas cubiertas + 4 archivos extra + 4 preguntas abiertas |
| `OUT/_ledger/revisor_f08_output.json` | `RevisorOutput` con `veredicto=aprobado`, 0 correcciones |
| `OUT/_ledger/cobertura.csv` | 21 filas de F08 mutadas a `verificado;F08;revisor_A5.1` |
| `OUT/_ledger/pruebas/A5.1/README.md` | Este archivo |
| `OUT/_ledger/pruebas/A5.1/validate-A5.1.sh` | Smoke ejecutable del gate |

## Resumen de la prueba literal del ROADMAP A5.1

> "documento aprobado por el revisor; 100% de archivos de F08 cubiertos; ≥ 1 flowchart, ≥ 2 sequence, ≥ 1 state; validadores en verde."

| Check | Esperado | Real |
|---|---|---|
| Documento existe | sí | `OUT/09-features/F08-busqueda-e-indexacion/F08-busqueda-e-indexacion.md` (476 líneas) |
| `validate_template.py` | exit 0 | ✅ exit 0 |
| `validate_evidence.py` | exit 0, 0 errores | ✅ 101/101 refs OK, 0 errores |
| `validate_mermaid.sh` | exit 0, todos los bloques renderizan | ✅ 5/5 bloques OK (1 classDiagram, 1 flowchart, 2 sequenceDiagram, 1 stateDiagram-v2) |
| 100% archivos F08 cubiertos | 21/21 | ✅ 21/21 en `cobertura.csv` |
| `run_subagent.py --rol revisor` | `aprobado, 0 correcciones` | ✅ `veredicto=aprobado`, `correcciones=[]` |
| ≥ 1 flowchart | sí | ✅ 1 (TD, §9) |
| ≥ 2 sequence | sí | ✅ 2 (§10.1 búsqueda local, §10.2 indexación full) |
| ≥ 1 state | sí | ✅ 1 (`stateDiagram-v2` §11) |
| `ROADMAP.md` línea 107 contiene `✅` | sí | ✅ |

## Hallazgos y decisiones relevantes

1. **Alcance de F08 (nota pre-A5.1)**: la línea 107 original del ROADMAP mencionaba `flowy-search-pub` y `command_palette`, pero la unidad `F08.json` (A4.2) solo cubre los 21 archivos del backend. Se decidió ejecutar el piloto contra los 21 archivos reales; el documento referencia las áreas externas en §Relacionado con. ROADMAP.md y STATE.md actualizados para reflejar la decisión.

2. **Canal de resultados**: el resultado de búsqueda NO viaja por `flowy-notification` (como las demás notificaciones Rust→Dart), sino por un `IsolateSink` con `stream_port` del payload de `SearchQueryPB`. El enum `SearchNotification` se compila y se exporta pero está sin uso efectivo. Documentado en §5.

3. **`run_subagent.py` modo autor es un mock**: el modo `autor` del script de A4.3 produce placeholders, no contenido real con evidencia. Para A5.1 se **bypaseó** el modo autor (el documento se escribió directamente con la información de los 21 archivos y los catálogos A2.x) y se usó el modo `revisor` (que sí ejecuta los 3 validadores reales). Artefacto `autor_f08_output.json` producido manualmente con el mismo esquema JSON de `AutorOutput`.

4. **`run_subagent.py --out-root`**: el modo revisor concatena `out_root / unit.documento`. Para que resuelva a `OUT/09-features/...` hay que pasar `--out-root` apuntando al directorio del proyecto (no a `OUT/`), porque el campo `documento` ya incluye el prefijo `OUT/`. Documentado en el comando del `validate-A5.1.sh`.

5. **Archivos extra detectados**: el documento necesitó citar 4 archivos no asignados a F08 (`search_deps.rs`, `module.rs`, `lib.rs`, `app_life_cycle.rs` de `flowy-core`) para entender el cableado completo. Declarados en `autor_f08_output.json::archivos_extra_detectados` para triage del orquestador; no se reasignan en esta fase.

## Comandos de reproducción

```bash
# 1. Validar plantilla
python3 SKILL/scripts/validate_template.py OUT/09-features/F08-busqueda-e-indexacion/F08-busqueda-e-indexacion.md
# 2. Validar evidencia
python3 SKILL/scripts/validate_evidence.py OUT/09-features/F08-busqueda-e-indexacion/F08-busqueda-e-indexacion.md
# 3. Validar Mermaid
bash SKILL/scripts/validate_mermaid.sh OUT/09-features/F08-busqueda-e-indexacion/F08-busqueda-e-indexacion.md
# 4. Revisor
python3 SKILL/scripts/run_subagent.py --rol revisor --unit OUT/_ledger/units/F08.json --out OUT/_ledger/revisor_f08_output.json --out-root .
# 5. Smoke A5.1
bash OUT/_ledger/pruebas/A5.1/validate-A5.1.sh
```

## Veredicto del revisor (literal)

```json
{
  "schema_version": 1,
  "veredicto": "aprobado",
  "correcciones": [],
  "validaciones": {
    "evidence": {"exit": 0, "errores": []},
    "template": {"exit": 0, "errores": []},
    "mermaid": {"exit": 0, "bloques_ok": 5, "bloques_ko": 0, "errores": []}
  }
}
```

## Pendientes transferidos a A5.2

- Sub-fase propuesta `A4.3.1`: añadir flag `--gate-100` a `run_subagent.py` para que las features marcadas 🔒 (F01, F02, F06, F08, motor export/import) eleven el umbral de muestreo a 100% automáticamente.
- `SearchFilterPB` sin uso → cablear o eliminar (documentado en §17).
- `FolderSearchHandler` comentado en frontend/rust-lib/flowy-core/src/deps_resolve/search_deps.rs:13 → reactivar o documentar como reservado.
- `SearchNotification` declarado pero sin emisor → decidir si se elimina o se cablea.
