# AppFlowy — revisión técnica

Documentación de ingeniería inversa de **AppFlowy**, construida desde el código
fuente y verificada referencia a referencia.

| | |
|---|---|
| Versión | v1.0 |
| Generado | 2026-10-22 |
| Documentos | 193 |
| Ficheros de código cubiertos | 4603 |
| Cobertura del código | 100,00 % |
| Referencias verificadas | 6849 |

## Por dónde empezar

1. **`00-INDEX.md`** — índice completo: qué documento cubre qué, con estado y
   cobertura.
2. **`01-resumen-ejecutivo.md`** — diez minutos de contexto: arquitectura, capas
   y mapa mental.
3. **`21-glosario.md`** — el vocabulario del código, con evidencia por entrada.

## Aviso sobre las referencias

Cada afirmación técnica lleva una referencia `fuente:ruta:línea` al fichero
exacto del código fuente del que procede. Las citas de `OUT/` son **verificables**:
se contrastaron contra el inventario de 4603 ficheros, y las que no resolvían
se corrigieron o se retiraron.

Un apartado del glosario recoge los símbolos que se han citado y **no existen en
el código**, junto con el símbolo real que los sustituye. Es deliberado: una
documentación que solo dice lo que está bien no permite juzgar cuánto se puede
fiar uno de ella.

## Diagramas

Todos los diagramas están en Mermaid (`mermaid` en bloques delimitados) y pasan
`validate_mermaid.sh`. Obsidian, GitHub y la web de Mermaid los renderizan sin
configuración; Notion requiere convertirlos a imagen.
