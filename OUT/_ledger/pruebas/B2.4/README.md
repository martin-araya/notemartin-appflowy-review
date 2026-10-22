# B2.4 — Catálogo de notificaciones Rust → Dart (`14-catalogo-notificaciones.md`)

## Artefactos generados

- `OUT/14-catalogo-notificaciones.md` (405 líneas, ~91 KB, 70 variantes en 6 enums)
- `OUT/_ledger/validate-B2.4.sh` — suite de 4 checks
- `OUT/_ledger/pruebas/B2.4/count_rows_70.py` — prueba literal del ROADMAP
- `OUT/_ledger/pruebas/B2.4/validate-B2.4.log` — log de la corrida en verde
- `SKILL/scripts/build_catalog_notifications.py` — generador determinista

## Distribución por enum

| Enum | Crate | Variantes | Emisores (con variante) | Estados |
|---|---|---:|---:|---|
| `ChatNotification` | flowy-ai | 10 | 0 | unused=10 |
| `DatabaseNotification` | flowy-database2 | 24 | 1 | unused=20, ok=4 |
| `DocumentNotification` | flowy-document | 5 | 0 | unused=4, declared_only=1 |
| `FolderNotification` | flowy-folder | 19 | 0 | unused=10, declared_only=9 |
| `StorageNotification` | flowy-storage | 2 | 1 | ok=1, emitted_only=1 |
| `UserNotification` | flowy-user | 10 | 9 | unused=3, declared_only=3, unused=… |
| **TOTAL** | — | **70** | **11** | — |

(Resumen parcial; ver §3 del documento para el desglose exacto.)

## Estados

- `ok` (8): emitidas en Rust Y con listener Dart.
- `emitted_only` (2): emitidas en Rust, sin listener Dart (debería auditarse).
- `declared_only` (13): con listener Dart pero NO emitidas en Rust.
- `unused` (47): ni emitidas ni recibidas (sentinela `Unknown` + dead code).

## Cobertura

- 70/70 variantes enumeradas (§4 + §5.* = 70 + 70).
- 49/49 variantes `sin uso en Dart` documentadas en §6 (47 unused + 2 emitted_only).
- 253/253 refs `[fuente:]ruta:línea` validadas contra `inventario.json`.
- 5 bloques Mermaid validados con `mmdc` (1 arquitectura + 4 por enum >= 10 variantes).

## Cómo regenerar

```bash
SKILL/scripts/build_catalog_notifications.py    # genera OUT/14-...md
OUT/_ledger/validate-B2.4.sh                   # corre los 4 checks
```

Si `notifications.json` cambia (nuevos enums o variantes), regenerar:

```bash
SKILL/scripts/extract_notifications.py    # A2.3 (output: OUT/_ledger/extract/notifications.json)
SKILL/scripts/build_catalog_notifications.py
OUT/_ledger/validate-B2.4.sh
```

## Estado

- ROADMAP.md línea 176 → ✅
- STATE.md → entrada B2.4 añadida
- 00-INDEX.md → regenerado
- SKILL/CHANGELOG.md → entrada `[0.6.0]`