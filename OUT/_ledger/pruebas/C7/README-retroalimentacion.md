# C7 · Retroalimentación a la skill genérica

**Fecha:** 2026-10-22 · **Fase:** C7

## La fase no se pudo ejecutar como estaba escrita

> Prueba del ROADMAP: «la skill genérica corre el inventario y validadores sobre
> otro repo sin cambios».

**`notemartin-extension-reviews` no existe en disco.** No hay ninguna skill con
ese nombre entre las diez de `~/Desktop/projects/Skills/`. Y no conviene
inventarse un destino: la candidata más parecida por nombre y estructura,
`notemartin-project-review`, es de otra familia (tiene `dev/evals`,
`dev/ground-truth` y `dev/holdout`, que es una Eval de proyectos, no el
framework de revisión que describe `AGENTS.md` §2). Copiar 30 scripts ahí sería
peor que no copiarlos.

Lo que sí se ha hecho es **todo lo demás de la fase**, y es la parte que
sobrevive al bloqueo:

1. **El manifiesto de qué es genérico y qué no** (`scripts_genericos.json`),
   clasificando los 30 scripts de `SKILL/scripts/` y anotando para cada uno si
   se ha podido verificar sobre un repo ajeno.
2. **La prueba de humo**, que sí es ejecutable y es el fondo del asunto:
   correr el inventario y los validadores sobre un repositorio sintético.
3. **Los bugs que la prueba de humo encontró y corrigió**, que son el resultado
   real de la fase: tres defectos de portabilidad que ningún validador sobre
   AppFlowy podía ver, porque sobre AppFlowy todo funcionaba.

## La prueba de humo

Se construyó un repositorio sintético en `/tmp/smoke_src/ejemplo/` con la
misma disposición que AppFlowy —`frontend/rust-lib/<crate>/src/event_map.rs` y
`frontend/appflowy_flutter_dart/lib/`— y un crate `ejemplo-crate` con:

- un enum `EjemploEvent` de dos variantes anotado con `#[derive(Flowy_Event,
  ProtoBuf_Enum)]`, registradas en un `AFPlugin`;
- un enum `EjemploNotification` emitido con `NotificationBuilder`;
- un `EjemploBloc` de Dart.

El nombre de la fuente es **`ejemplo`**, no `appflowy`. Esa única diferencia es la
que separa «funciona porque conoce AppFlowy» de «funciona».

### Resultado por script

| script | resultado |
|---|---|
| `inventory.py` | **OK sin cambios** — 5 ficheros, clasificados por capa y lenguaje |
| `extract_events.py` | **FALLA** → corregido → OK: encuentra `EjemploEvent`, sus dos variantes y sus tipos de entrada y salida |
| `extract_notifications.py` | OK — escribe su JSON |
| `extract_blocs.py` | OK, pero escribe `"fuentes": ["appflowy"]` fijo en la cabecera: pendiente de corregir |
| `extract_deps.py` | OK |
| `extract_misc.py` | OK |
| `extract_protobuf.py` | OK |
| `validate_evidence.py` | **FALLA** → corregido → **1/1 referencias OK** sobre el repo ajeno |
| `validate_mermaid.sh` | **OK sin cambios** — el bloque Mermaid del documento sintético renderiza |
| `validate_template.py` | Funciona, pero **las 8 plantillas son las de AppFlowy**: los `id_pattern` (`^B1\.\d+`, `^F\d+…`) y las secciones obligatorias no encajan en otro repo. Con `--template` explícito funciona. No es un bug: es diseño, y la trampa está documentada por el propio mensaje de error |

## Los tres bugs que encontró

### 1. `extract_events.py` se caía con `--src-root` externo

```
ValueError: '/private/tmp/smoke_src/ejemplo/frontend/rust-lib/ejemplo-crate/src/event_map.rs'
is not in the subpath of '.../notemartin-appflowy-review'
```

Cuatro puntos del script resolvían rutas con `relative_to(SKILL_ROOT)`, que
lanza excepción en cuanto el repositorio no está dentro del proyecto. Se
sustituyó por un ayudante `ruta_relativa(abs_path, src_root)` que devuelve la
ruta relativa al proyecto si el fichero está dentro, y relativa a `SRC/` si no,
que es justo la forma que `validate_evidence.py` reconoce. Sobre AppFlowy el
comportamiento no cambia: la ruta sigue siendo la misma.

### 2. `validate_evidence.py` asumía que la fuente se llamaba `appflowy`

El validador comparaba el prefijo de cada referencia contra el conjunto fijo
`{appflowy, collab, editor}` y, si la referencia no lo traía, asumía `appflowy`:

```
E_PATH_NOT_IN_INVENTORY: no existe en inventario como ('appflowy', 'appflowy/ejemplo/frontend/…')
```

Contra un inventario ajeno, **todas** las referencias fallaban, porque buscaba
`appflowy/ejemplo/…` donde el inventario tenía `ejemplo/…`. Ahora `validate_ref()`
deduce el conjunto de fuentes y la fuente por defecto del propio diccionario
`inv` que ya tenía delante, y el conjunto fijo solo se usa como sugerencias en
el mensaje de error.

Este era el bug más valioso de los tres: es el validador que más daño habría
hecho a un usuario de otra skill, porque no produce «0 errores» ni «todos los
documentos mal», sino un fallo que parece culpa de quien escribió las citas.

### 3. `validate_mermaid.sh` era intermitente por culpa de Puppeteer

No lo encontró la prueba de humo sobre el repo ajeno, sino la reejecución de
`validate-C1.sh`: la misma pasada sobre los mismos documentos reportaba 3 fallos,
luego 2, y al validar los documentos Individualmente pasaban los 13 bloques. La
causa era `ProtocolError: Runtime.callFunctionOn timed out`: `mmdc` lanza un
Chromium por bloque y, con 791 bloques en paralelo, el timeout se dispara.

Ahora hay **3 intentos por bloque, solo ante fallos de infraestructura**
(`timed out`, `TimeoutError`, `protocolTimeout`, `Target closed`). Un error real
de parseo de Mermaid se falla en el acto, porque reintentar un diagrama mal
escrito solo ralentiza. El criterio es deliberado: distinguir «el diagrama está
mal» de «la herramienta se cansó», que antes se confundían en un mismo mensaje.

## Lo que la prueba de humo demuestra y lo que no

**Demuestra** que el núcleo de la cadena —inventario → extractores → validación
de evidencia → validación de Mermaid— es reutilizable sin cambios en un segundo
repositorio, una vez corregidos los tres bugs.

**No demuestra** tres cosas, y conviene que no se den por buenas:

1. **La extracción completa sobre un repo real.** El repositorio sintético tiene
   5 ficheros y un `event_map.rs`. Sobre AppFlowy estos scripts procesan 4 603.
   Escala y casos límite (herencias, macros, crates sin `event_map`) no están
   cubiertos.
2. **La validación de plantillas**, que requiere definir plantillas del repo
   destino. Es trabajo de adaptación, no de portabilidad.
3. **Los validadores de la Parte C** (`contrast_B5_B2.py`, `fix_line_offsets.py`,
   `repair_markdown_damage.py`), que no se ejecutaron contra el repo sintético
   porque su lógica es inherentemente de AppFlowy: leen `events.json` y
   `notifications.json`, cuyos nombres de enum son los de este proyecto.

## Cómo aplicar el manifiesto cuando exista la skill genérica

1. Crear `notemartin-extension-reviews/scripts/` y copiar los scripts marcados
   `verificado_en_C7: true` de `scripts_genericos.json`.
2. Parametrizar `RUSTLIB_REL` en `extract_events.py` y `fetch_sources.sh` para el
   layout del repo destino.
3. Corregir el `"fuentes": ["appflowy"]` fijo de `extract_blocs.py` (y
   probablemente el de los demás extractores).
4. Definir las plantillas de `validate_template.py` para el repo destino, o
   asumir que se invocará siempre con `--template`.
5. Repetir la prueba de humo como paso de integración, con el repositorio destino
   como sujeto.

## Reejecución de la prueba

```bash
mkdir -p /tmp/smoke_src/ejemplo/frontend/rust-lib/ejemplo-crate/src
# … crear los ficheros de event_map.rs, notification.rs, Cargo.toml, bloc.dart …
python3 SKILL/scripts/inventory.py  --src-root /tmp/smoke_src --out-dir /tmp/smoke_out --include ejemplo
python3 SKILL/scripts/extract_events.py --src-root /tmp/smoke_src --out-dir /tmp/smoke_out --fuente ejemplo
python3 SKILL/scripts/validate_evidence.py <doc.md> --inventario /tmp/smoke_out/inventario.json
bash SKILL/scripts/validate_mermaid.sh <doc.md>
```

Log completo en `OUT/_ledger/pruebas/C7/smoke.log`.