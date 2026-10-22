# C5 · Índice final

**Fecha:** 2026-10-21 · **Fase:** C5

> Las tres filas de la tabla siguiente citan **documentos de `OUT/`**, no ficheros
> de `SRC/`, así que se escriben como `fichero, línea N` en lugar de `ruta:N`:
> `validate_evidence.py` contrasta las referencias contra `inventario.json`, que
> solo contiene el código fuente, y las contaría como evidencia rota.

## Prueba del ROADMAP: «todos los enlaces resuelven»

`SKILL/scripts/build_index.py` regeneró `OUT/00-INDEX.md` (272 documentos,
3 483 enlaces cruzados) y la cifra de enlaces sin resolver en **entregables es 0**.

## Tres enlaces que sí estaban rotos

| documento | enlace | resolución |
|---|---|---|
| `15-secuencias-globales/00-indice-secuencias-globales.md`, línea 208 | `[[B6]]` | No existe ningún documento con `id: B6`: los transversales son `B6.1`–`B6.5`. Sustituido por `[[B6.1]]`–`[[B6.5]]`. |
| `18-build-ci-distribucion.md`, línea 513 | `[[B6.5.2]]` | Esa sub-unidad nunca se emitió como documento; el destino real es `B6.5` (`21-glosario.md`). |
| `21-glosario.md`, línea 47 | `[[IdDelDocumento]]` | Marcador de plantilla dentro de la prosa que *explica* la sintaxis de enlace interno. Reescrito sin corchetes dobles para que no se cuente como referencia. |

## Corrección al indexador: entregables frente a material de trabajo

Los 18 enlaces que quedaban sin resolver están **todos** en
`OUT/_ledger/briefs/`, y sus objetivos son `X`, `Fxx` y `B4.x`: marcadores de
plantilla de un brief de unidad, no referencias a documentos. El indexador los
contaba igual que los de los entregables, de modo que su cifra —«18 no
resueltas»— mezclaba huecos de plantilla con deuda real y hacía creer que quedaba
trabajo sin hacer.

Se añadió `_is_meta()` y el informe separa las dos cifras:

- **Enlaces no resueltos en entregables**: la cifra que decide el criterio de
  cierre del ROADMAP.
- **Marcadores de plantilla en material de trabajo**: los de `_ledger/`, con la
  nota de que no son entregable.

El JSON de `--check-links` devuelve las dos listas por separado
(`unresolved` y `unresolved_template_placeholders`), de modo que un gate
automatizable puede comprobar la primera y no la segunda.

## Estado del índice

| Métrica | Valor |
|---|---|
| Documentos `.md` en `OUT/` | 272 |
| Documentos con `id` en frontmatter | 192 |
| Cobertura de fuente (verificado) | **100,00 %** |
| Cobertura de docs (verificado) | 70,22 % |
| Enlaces cruzados totales | 3 483 |
| Enlaces no resueltos en entregables | **0 ✓** |

## Lo que la cifra de cobertura de docs no significa

El 70,22 % de cobertura de documentos no es un pendiente de revisión: es la
proporción de documentos cuyo `estado` de frontmatter es `verificado` sobre el
total, y el resto son documentos auxiliares (índices de sección, plantillas de
revisión, este mismo fichero). La cobertura que importa —la del **código**— es
del 100,00 % sobre 4 603 ficheros, y esa no ha cambiado desde C2.
