# Deuda técnica

El informe de una revisión vive en `.scratch/code-review/<fecha>-<modo>/report.md` y se pierde con la siguiente. **La deuda, no**: es lo único de una revisión que sobrevive, porque lo que reaparece en varias revisiones es precisamente lo que hay que pagar. Por eso vive en el repo revisado, commiteada, en `docs/technical-debt.md` (o donde diga `--debt`).

La escribe `scripts/write_report.sh` a partir de los informes crudos de los sub-agentes. No es un archivo que alguien rellene a mano al principio: es un archivo que las revisiones van rellenando solas.

## Qué entra

Una fila por hallazgo que cumpla **CR-03**: citar una `ruta:línea` real del diff.

| Eje | Entra | No entra |
|---|---|---|
| Standards | `violación de CONTRIBUTING.md · src/a.ts:42 — …` | `posible Duplicated Code — sin ubicación` |
| Spec | `requisito incumplido · src/b.ts:10 — …` | `el spec es ambiguo` sin línea del diff |

Un hallazgo sin `ruta:línea` no se archiva: se cuenta en el informe como *no verificable* y se queda ahí. Una deuda que no se puede localizar es una opinión, y las opiniones no se archivan como deuda.

## Cómo se identifica la reaparición

La clave de coincidencia es **eje + tipo + ruta, sin número de línea**. Si la revisión de marzo señaló `src/a.ts:42` y la de junio señala `src/a.ts:58` por el mismo tipo de problema, es la misma deuda con `Veces = 2`, no dos deudas. La línea se mueve con el código; el problema no.

## Quién cierra

El script **nunca cierra nada**. Lo único que hace con las filas abiertas que no han vuelto a aparecer es listarlas en el informe, bajo "Abiertas que esta revisión no ha vuelto a señalar". Cerrar es una decisión humana: mover la fila a `## Cerradas` con su fecha, o annotar por qué sigue viva.

La razón es la misma que en el resto de esta skill: un hallazgo que no se reproduce en un diff no está resuelto, está fuera de alcance. Las dos cosas son diferentes y solo una se arregla con un `git commit`.

## Formato

```
| ID | Eje | Tipo | Ubicación | Resumen | Veces | Primera | Última | Estado |
```

- `ID`: `TDE-NNN`, correlativo, estable en el tiempo. Nunca se renumera.
- `Eje` / `Tipo`: tal cual los emite el sub-agente (`Standards`/`Spec`, `posible Duplicated Code`, `falta`, `scope-creep`…).
- `Ubicación`: `ruta:línea` del hallazgo.
- `Resumen`: una línea. Si un hallazgo necesita dos líneas, es dos hallazgos.
- `Veces`: revisiones en las que ha aparecido.
- `Primera` / `Última`: fechas de la revisión.
- `Estado`: `abierta` o `cerrada`.

## Qué se lee de un vistazo

Un fichero con quince filas `Veces = 4` y ninguna cerrada dice más sobre un repo que cualquier párrafo de resumen. Ese es el objetivo: que la deuda tenga historial y no dependa de que alguien recuerde lo que dijo en una conversación.