---
id: 00-INDEX
titulo: Índice de la skill `notemartin-appflowy-review`
estado: verificado
generado: 2026-10-20T16:17:08Z
---

# 00 — Índice de la skill

> Regenerar con: `python3 SKILL/scripts/build_index.py --out-dir OUT/`.

## 1. Resumen

| Métrica | Valor |
|---|---|
| Documentos `.md` en `OUT/` | 4 |
| Documentos con `id` en frontmatter | 4 |
| Commits de fuentes | 3 |
| Cobertura de fuente (verificado) | 50.00% |
| Cobertura de docs (verificado) | 75.00% |
| Enlaces cruzados totales | 4 |
| Enlaces no resueltos | 1 |

## 2. Commits de fuentes

| Fuente | Commit | URL |
|---|---|---|
| appflowy | `5cf3a36` | https://github.com/AppFlowy-IO/AppFlowy |
| collab | `4dfccef` | https://github.com/AppFlowy-IO/AppFlowy-Collab |
| editor | `470c4e7` | https://github.com/AppFlowy-IO/appflowy-editor |

## 3. Cobertura de docs en `OUT/`

| estado | total | % |
|---|---:|---:|
| verificado | 3 | 75.00% |
| pendiente | 1 | 25.00% |
| sin_asignar | 0 | 0.00% |
| **GLOBAL** | **4** | **75.00%** |

## 4. Cobertura de fuente (`cobertura.csv`)

| capa | total | verificado | % |
|---|---:|---:|---:|
| bloc | 2 | 1 | 50.00% |
| ui | 2 | 1 | 50.00% |
| **GLOBAL** | **4** | **2** | **50.00%** |

## 5. Árbol de documentos

```
fixtures/
├── 00-INDEX.md  (9 secciones, 2.1 KB)
├── A.md  (0 secciones, 0.1 KB)
├── B.md  (0 secciones, 0.1 KB)
├── C.md  (0 secciones, 0.1 KB)
```

## 6. Tabla de documentos

| ruta | id | título | estado |
|---|---|---|---|
| `00-INDEX.md` | 00-INDEX | Índice de la skill `notemartin-appflowy-review` | verificado |
| `A.md` | A | Doc A | verificado |
| `B.md` | B | Doc B | pendiente |
| `C.md` | C | Doc C con ref rota | verificado |

## 7. Mapa de enlaces cruzados

| origen | → | destino |
|---|---|---|
| `A.md` (línea 4) | → | `B.md` (id `B`) |
| `B.md` (línea 4) | → | `A.md` (id `A`) |
| `B.md` (línea 4) | → | `B.md` (id `B`) |
| `C.md` (línea 4) | → | `✗ no resuelto` (`NOEXISTE`) |

## 8. Enlaces no resueltos

- `C.md:4` → `[[NOEXISTE]]` (id no encontrado en el out-dir)

## 9. Cómo regenerar

```bash
cd /path/to/notemartin-appflowy-review
python3 SKILL/scripts/build_index.py --out-dir OUT/
```
