## Foco de esta unidad

`collab-integrate` + los crates de contratos `*-pub`: la capa que **construye**
los objetos `Collab` y les adjunta los plugins (persistencia local, sync cloud,
indexación), y los traits públicos que rompen las dependencias circulares.

### collab-integrate

- `collab_builder.rs`: cómo se construye un `Collab` desde un `ViewPB`, con qué
  `collab_type`, qué plugins se le enganchan y con qué orden.
- `plugin_provider.rs`: qué implementaciones de servidor (`af_cloud`,
  `local_server`) puede inyectar y cómo se eligen. **Corrección de scope que
  debes declarar en §2 y §13**: el ROADMAP situaba este fichero en F06; el
  cierre de B3.F03..F07 lo redirigió a F00.
- Configuración y límites de vida del `Collab` (cuándo se destruye, qué
  observers se registran).

### crates `-pub`

- Los traits públicos de `flowy-document-pub`, `flowy-folder-pub`,
  `flowy-user-pub`, `flowy-database-pub`, `flowy-ai-pub`, `flowy-search-pub`,
  `flowy-storage-pub`, `flowy-server-pub`.
- Tabla: crate `-pub` → trait/clase pública → qué crate de dominio la
  implementa → qué rompe (dependencia circular).
- Por qué existe el patrón `*-pub` (AGENTS.md §5.6): argumento con evidencia en
  los `Cargo.toml` (`grep` las dependencias reales con `extract/deps.json`).

## Pruebas literales adicionales

1. Tabla de los 8 crates `-pub`: nombre del crate, fichero, símbolos públicos
   principales con línea, y crate implementador.
2. Tabla de `CollabType` (7 variantes) con qué `ViewLayout` lo produce y qué
   `Collab` construye. **Verifica los nombres reales con `rg`**; B1.6 documenta
   un modelo de `CollabType` que puede no coincidir con este rev — si detectas
   discrepancias, lístalas en §18 como `[NO DETERMINADO]` para C3.
3. Tabla de los plugins que `collab_builder` engancha: plugin → condición →
   fichero:línea.
4. `classDiagram` de `Collab` y sus plugins (con nombres reales verificados).
5. Grafo `flowchart LR` de dependencias `*-pub` ↔ crates de dominio.
6. §12 con la tabla real de los 61 archivos de la unidad.

## Diagramas mínimos (4)

- 1 `flowchart TD` con `subgraph` por capa: view → builder → collab → plugins →
  persistencia/cloud → observers.
- 1 `sequenceDiagram`: apertura de una vista y construcción de su `Collab`.
- 1 `classDiagram` de `Collab` + plugins.
- 1 `flowchart LR` del grafo de contratos `-pub`.