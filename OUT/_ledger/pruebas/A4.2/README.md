# pruebas/A4.2/ — `build_units.py` + `validate_units.py` + 88 unidades

**Fase**: A4.2 — Generador de unidades de trabajo (Bloque A4 · Orquestación).
**Fecha**: 2026-10-18.
**Plan completo**: `1792363730747-build-units-a42.md`.

## Entregables

| Archivo | Rol |
|---|---|
| `SKILL/scripts/build_units.py` | Generador de unidades (~480 líneas, Python 3 stdlib) |
| `SKILL/scripts/validate_units.py` | Validador de esquema y coherencia (~140 líneas) |
| `OUT/_ledger/pruebas/A4.2/fixtures/toy_ledger.csv` | 51 filas con 4 features (F01, F02, F08, F10) + 1 multi-feature |
| `OUT/_ledger/pruebas/A4.2/fixtures/expected_units/` | 8 JSON (F01.0, F01.1, F01.2, F02.0, F02.1, F08, F10, _index) — regenerado en cada corrida |
| `OUT/_ledger/validate-A4.2.sh` | 7 checks; sale 0 si todo OK |
| `OUT/_ledger/pruebas/A4.2/smoke.log` | Trazas reales |
| `OUT/_ledger/units/*.json` | **88 unidades reales** (1 por feature o sub-feature) + `_index.json` |
| `OUT/_ledger/units/_index.json` | Índice resumido con todas las unidades |

## Resumen de la prueba literal del ROADMAP A4.2

- **Suma exacta**: archivos en todas las unidades = **4.279** = total de filas con `feature_ids` en `cobertura.csv` ✅
- **Sin solapamiento**: 0 archivos duplicados entre unidades (verificado por `validate_units.py`) ✅
- **Sub-división**: 7 features con > 120 archivos se dividen automáticamente; F01 → 12 sub-unidades (F01.0.1..F01.0.3 + F01.1..F01.9), F02 → 14, F00 → 26 (7 paquetes + 14 sub-grupos del catch-all), F19 → 14, F16 → 3, F09 → 4, F05 → 2.
- **Toy**: 7 unidades, 51 archivos = 51 asignados.
- **F10 (0 archivos)**: queda en `features_vacias` del índice, sin generar unidad.

## Distribución de unidades por feature (corrida real)

| Feature | Unidades | Archivos |
|---|---:|---:|
| F00 Infraestructura compartida | 26 | 1.529 |
| F01 Documentos y editor | 12 | 710 |
| F02 Bases de datos | 14 | 651 |
| F03 Folder, workspaces, vistas | 1 | 85 |
| F04 Sidebar, favoritos, recientes, papelera, tabs, command palette | 1 | 30 |
| F05 Usuario, auth, sesión | 2 | 126 |
| F06 Sync y servidores | 1 | 35 |
| F07 Almacenamiento de archivos | 1 | 55 |
| F08 Búsqueda e indexación | 1 | 21 |
| F09 IA | 4 | 166 |
| F10 Importación (UI) | — (0 archivos) | 0 |
| F11 Exportación (UI) | 1 | 2 |
| F12 Compartir, publicar, niveles de acceso | 1 | 59 |
| F13 Ajustes, apariencia, temas, fuentes | 1 | 84 |
| F14 Internacionalización | 1 | 6 |
| F15 Notificaciones in-app y recordatorios | 1 | 37 |
| F16 Mobile | 3 | 184 |
| F17 Plataforma (ventanas, deeplinks, auto-update, hotkeys, feature flags, errores, logging) | 1 | 19 |
| F18 Motor Colab (CRDT, plugins, importer, entity, derive) | 1 | 113 |
| F19 Editor (tests, ejemplos, l10n, configuración) | 14 | 354 |
| F20 Colab (raíz: configuración, CI, docs, manifests) | 1 | 13 |
| **Total** | **88** | **4.279** |

## Comandos

```bash
# Corrida real (escribe units/<id>.json y units/_index.json)
python3 SKILL/scripts/build_units.py

# Dry-run (reporte a stderr sin escribir)
python3 SKILL/scripts/build_units.py --quiet  # no escribe resumen

# Ajustar umbral de división
python3 SKILL/scripts/build_units.py --max-files 50   # divide mas agresivamente
python3 SKILL/scripts/build_units.py --no-split       # una unidad por feature

# Validar el directorio de unidades
python3 SKILL/scripts/validate_units.py

# Validador de la fase (7 checks)
bash OUT/_ledger/validate-A4.2.sh
```

## Estructura de cada `units/<id>.json`

```json
{
  "schema_version": 1,
  "id": "F01.3",
  "feature_id": "F01",
  "sub_index": 3,
  "titulo": "Media y archivos: image, video, file, cover, link_preview, link_embed",
  "fuentes": ["appflowy"],
  "archivos": [{"fuente": "appflowy", "ruta": "...", "capa": "ui", "estado": "pendiente"}, ...],
  "archivos_total": 35,
  "catalogos": ["blocs.json", "deps.json", "events.json", "misc.json", "notifications.json", "protobuf.json"],
  "dependencias": [{"id": "F01.0", "tipo": "indice", "nota": "..."}],
  "plantilla": "feature",
  "documento": "OUT/09-features/F01-documentos-y-editor/01.3-media-archivos.md",
  "metricas": {"archivos": 35, "por_capa": {"ui": 30, "service": 5}, "por_fuente": {"appflowy": 35}},
  "prioridad": 2,
  "concurrencia": "paralela",
  "generado_en": "2026-10-18T..."
}
```

## Cobertura de la prueba literal del ROADMAP A4.2

| Criterio ROADMAP | Check validador | Resultado |
|---|---|---|
| Suma archivos unidades = asignados | suma de `archivos_total` en `validate_units.py` | **4.279 = 4.279** ✅ |
| `OUT/_ledger/units/<id>.json` por feature/sub | `ls units/` cuenta | 88 ✅ |
| División > 120 archivos | F00/F01/F02/F19/F16/F09/F05 se subdividen | sí ✅ |
| Toy: 7 unidades y suma = 51 | `validate-A4.2.sh` check 2 | ✅ |
| Idempotencia | estructura idéntica entre 2 corridas | ✅ |
| `--max-files 50` aumenta unidades | check 5 | 153 unidades ✅ |
| `--no-split` reduce a Fxx simples | check 6 | 20 unidades ✅ |
| `--include F01,F02` filtra | check 8 | solo F01/F02 ✅ |
| `validate_units.py` sin errores | `validate-A4.2.sh` | OK ✅ |

Plan completo: `1792363730747-build-units-a42.md`. Log: `smoke.log`.

**Siguiente fase**: **A4.3 — Contratos de subagente** (prompts autor/revisor en `references/` con entrada/salida exactas de `AGENTS.md §8`).
