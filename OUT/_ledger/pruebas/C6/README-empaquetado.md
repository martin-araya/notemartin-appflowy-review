# C6 · Empaquetado

**Fecha:** 2026-10-21 · **Fase:** C6 · **Herramienta:** `SKILL/scripts/package_dist.py`

## Prueba del ROADMAP

> «Abrir 3 documentos al azar en Notion y Obsidian con diagramas renderizados.»

No hay interfaz gráfica en este entorno, así que el script **no simula** la
apertura: la **anticipa**, comprobando las condiciones que la harían fallar. Es un
matiz que conviene dejar explícito, porque una prueba que se declara ejecutada sin
haber ejecutado lo que dice medir es peor que no tenerla.

| verificación | qué comprueba | resultado |
|---|---|---|
| **V1** Enlaces | Los 3 456 enlaces `[[id]]` de la copia resuelven, con el resolver de `build_index.py` | **3 456 / 3 456** |
| **V2** Mermaid | Fences balanceados; 791 bloques contados; ninguno anidado en inline code | **791 balanceados** |
| **V3** Notion | Encabezados sin `#` inicial ni `|`, que son los dos que rompen la importación | **0 problemas** |
| **V4** Portabilidad | Sin rutas absolutas de la máquina de generación, sin referencias a `SRC/` | **0 problemas** |
| **V5** Obsidian | Los 3 508 enlaces convertidos a ruta relativa apuntan a ficheros existentes | **3 508 / 3 508** |
| **V6** Archivo | `OUT-appflowy-review-v1.0.tar.gz` | **2,3 MiB** |

**Resultado: 6/6.**

## Artefactos

| Ruta | Contenido |
|---|---|
| `dist/` | 193 documentos (9,6 MiB), con `README.md` y `00-INDEX.md` en la raíz |
| `dist-obsidian/` | La misma copia con `[[id]]` reescritos a `[[ruta/relativa.md]]`, para que Obsidian resuelva sin configuración |
| `OUT-appflowy-review-v1.0.tar.gz` | El archivo de distribución (2,3 MiB) |

## La prueba que salió de la propia verificación

Escribir el validador fue más útil que pasarlo. Cuatro de las seis verificaciones
encontraron algo, y en tres de los cuatro casos lo que encontraron era un error
**del propio validador**, no de la documentación:

**V2 contaba cuatro backticks como un fence.** El primer pase marcó `22-preguntas-abiertas.md` línea 615 y `STATE.md` línea 1404 como «bloque mermaid dentro de una línea» y «fence sin cerrar». Los dos son prosa que **explica la convención** escribiendo ```` ```mermaid ```` como span inline. CommonMark permite abrir un span de código inline con N backticks, así que una línea que empieza por cuatro no es un fence. Corregido: ahora solo cuenta una línea con **exactamente** tres backticks más un tag de lenguaje opcional. El recuento pasó de 791 con 4 errores a **791 con 0**.

**V3 rechazaba casi todos los encabezados.** La primera regla blacklistaba `\`, `` ` ``, `*`, `_`, `[`, `]`, `#`, `~`, `<`, `>`. Con eso marcaba **1 217 encabezados** —casi todos los que llevan código en línea— como incompatibles con Notion. Notion los acepta sin problema. La regla real es mucho más estrecha: solo un `#` **al inicio** del cuerpo del encabezado crearía un nivel anidado, y una `|` se interpretaría como separador de tabla. Reducida a eso, quedan **0** problemas reales.

**V5 contaba como enlaces rotos 16 textos con corchetes dobles.** Eran `[[:space:]]` (un ejemplo de shortcode de emoji), `[[id]]` (la propia sintaxis, explicada en `STATE.md`), `[[{"insert":"a"},...]]` (un fragmento JSON de ejemplo), `[[B3.F07]]` y `[[F02.X.1]]` (marcadores de plantilla) y `[[F04.12 / B4.X]]` (dos destinos en un solo par de corchetes). Ninguno es una referencia a un documento. Corregido: el criterio pasó a ser «el enlace apunta a un fichero que existe en la copia», verificado contra el sistema de archivos.

Un cuarto intento de arreglo de V5 falló y también ilustra por qué: cambiar al resolver de ids, que ahora recibía rutas en lugar de ids y reportaba 86 enlaces «sin convertir» que en realidad estaban correctamente convertidos. La solución fue medir contra el sistema de archivos, no contra un índice de identificadores.

## Lo que encontró de verdad

Dos defectos reales en la documentación, ambos de portabilidad:

| documento | defecto | corrección |
|---|---|---|
| `15-secuencias-globales/00-indice-secuencias-globales.md`, línea 13 | Un enlace `file:///Users/martin/Desktop/projects/Skills/notemartin-appflowy-review/STATE.md` — una ruta absoluta de la máquina donde se generó | Enlace relativo a `STATE.md` |
| `22-preguntas-abiertas.md`, línea 562 | `` `/Users/martin/.cargo/bin/cargo` `` en las precondiciones de entorno | `$CARGO_HOME/bin/cargo`, normalmente `~/.cargo/bin/cargo` |
| `STATE.md`, líneas 1 350, 1 385 y 1 447 | Tres rutas absolutas equivalentes (`cargo`, `mmdc`) | Versiones con `~` |

Ninguno habría salido de los validadores de contenido: los tres son rutas
absolutas, y un lector que recibe el paquete en otra máquina no tiene forma de
seguirlas.

## Lo que este empaquetado no cubre

- **Los diagramas no se renderizan a imagen.** La copia de Notion contiene los
  bloques Mermaid como texto; importarla requiere convertirlos antes (con
  `mmdc` o mermaid.live). La verificación V3 comprueba que los encabezados son
  importables, no que la conversión funcione.
- **No se prueba en un vault real de Obsidian.** V5 comprueba que los enlaces
  apuntan a ficheros existentes, que es la condición necesaria para que el
  grafo de Obsidian los resuelva, pero no que el índice de Obsidian se construya
  como se espera.
- **`00-INDEX.md` y `STATE.md` se incluyen**, y son meta-documentos: describen el
  proceso de construcción, no AppFlowy. Un lector final no los necesita, pero
  tampoco estorban, y son los que permiten auditar cómo se obtuvo el resultado.

## Reejecución

```bash
python3 SKILL/scripts/package_dist.py            # genera y verifica
python3 SKILL/scripts/package_dist.py --check-only  # verifica sin regenerar
```

Sale 1 si alguna de las seis verificaciones falla, de modo que sirve como gate.