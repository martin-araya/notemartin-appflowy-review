# Resumen de cierre — Parte C

Generado al terminar C7. Ninguna fase del ROADMAP queda abierta; C4 se ejecutó
y **no se declaró cerrada** por quedar en 90,0 % frente a un umbral del 95 %.

| Fase | Prueba | Resultado |
|---|---|---|
| C0–C6 (Bloques B) | suites por bloque | 5/5 |
| **C1** Pasada global de validadores | 5 checks | **5/5** · `validate_evidence` 18 019/18 019 |
| **C2** Cobertura | `--threshold 100` | **4 603/4 603 = 100,00 %** |
| **C3** Revisión cruzada | `contrast_B5_B2 --check` = 0 | **7/7** · 53 fabricaciones detectadas y 0 restantes |
| **C4** Utilidad | ≥ 95 % | **90,0 %** — no cerrada |
| **C5** Índice final | enlaces resueltos | **0 sin resolver** en entregables |
| **C6** Empaquetado | 6 verificaciones | **6/6** |
| **C7** Retroalimentación | smoke test | **9/9**; destino inexistente |

## Validadores al cierre

| Validador | Resultado |
|---|---|
| `validate_template` | 190/190, 0 errores |
| `validate_evidence` | **18 019/18 019**, 0 errores |
| `validate_mermaid` | **791/791**, 0 fallos |
| `validate_coverage --threshold 100` | **4 603/4 603 = 100,00 %** |
| `contrast_B5_B2 --check` | **0 fabricaciones** en 257 referencias |
| `validate-C1.sh` | **5/5** |
| `validate-C3.sh` | **7/7** |
| `package_dist.py` | **6/6** |
| smoke test de portabilidad (C7) | **9/9** |

## Correcciones de tooling que salieron de esta parte

Ninguna era visible sobre AppFlowy; todas aparecieron por probar fuera de su
contexto o por reejecutar lo que ya se daba por verde.

| script | defecto | cómo apareció |
|---|---|---|
| `resume.py` | `scan_orphan_docs` leía el id del nombre de archivo en vez del frontmatter, y daba 3 huérfanos falsos | C3, al preparar la fase |
| `validate-C1.sh` | check 5e exigía exactamente 10 marcas de retirada; se quedó obsoleto al resolverlas | C3.1 |
| `validate-A4.2.sh` | esperaba 143 ficheros de unidad, cifra anterior a B4/B5/B6; **fallaba desde el cierre de B4** | C3 |
| `contrast_B5_B2.py` | el regex exigía minúscula en el miembro de `Enum::Miembro`, lo que hacía **inalcanzable** la rama de verificación de variantes: informaba «0 fabricaciones» sobre documentos que tenían 53 | C3.1, al contrastar contra un caso conocido falso |
| `build_index.py` | contaba los marcadores de plantilla de `_ledger/` como referencias rotas | C5 |
| `package_dist.py` | (tres bugs propios, corregidos antes de usarse como gate) | C6 |
| `extract_events.py` | `relative_to(SKILL_ROOT)` → `ValueError` con `--src-root` externo | **C7**, smoke test |
| `validate_evidence.py` | fuente fija `appflowy`; sobre un inventario ajeno fallaban **todas** las referencias | **C7**, smoke test |
| `validate_mermaid.sh` | intermitente por `ProtocolError` de Puppeteer (3 fallos y luego 0 sobre los mismos docs) | C6, reejecutando C1 |

## La lección que las cuatro fases repiten

Las tres primeras fases de la Parte C encontrou fallos que **ningún validador
veía**, y eran siempre de la misma familia:

1. C1: daño de Markdown que el parser de referencias aceptaba.
2. C1: referencias que resuelven a la línea correcta pero describen algo que no
   está en ella.
3. C3: símbolos que no existen dentro de líneas que sí existen.
4. C4: documentos que afirman con `[VERIFICADO]` cosas que el código desmiente
   (`EncodedCollab` con cinco campos, `CollabPluginType` con cuatro variantes).

El patrón es que **validar la forma no valida el contenido**. Una referencia
`ruta:línea` puede ser correcta en sus tres componentes y seguir diciendo una
falsedad. Y lo que separa a los bloques que fallan de los que no, no es el rigor
del autor: es que los features pasaron por autor → **revisor independiente que
abría el código**, y ninguno de los miles de documentos de `09-features/` tiene
una sola fabricación.

Dos corolarios operativos que salen de aquí:

- Un detector que informa «0 hallazgos» debe contrastarse contra un caso conocido
  antes de aceptar su veredicto. El de C3 era capaz de decir «0» sobre 53.
- La revisión manual solo tiene valor cuando el revisor mira el código. Repetir
  los validadores sobre el mismo árbol no añade nada.
