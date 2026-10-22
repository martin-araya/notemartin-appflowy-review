## Foco de esta unidad

`flowy-ai` completo (67 ficheros). Es la unidad más grande de F09 y el corazón
del subsistema de IA. Cubre a la vez **chat**, **completion**, **IA local**,
**MCP**, **embeddings**, **selección de modelo**, **offline**, **middleware** y
**`ai_tool`**, así que organízalo por subsistema.

### Subsistemas que debes identificar leyendo el árbol

Verifica los nombres reales con `rg`; el mapa esperado es:

- `ai_manager.rs`: el `AIManager`, qué subsistemas registra y cómo se inyecta
  desde `flowy-core`.
- `chat.rs` / `chat_context`: contexto de chat, historial y streaming.
- `completion.rs`: completions (escritura libre en el editor).
- `local_ai/`: modelos locales (Ollama, LM Studio…), recursos y prompts.
- `mcp/`: Model Context Protocol (servidores, herramientas, recursos).
- `embeddings/`: generación de vectores y búsqueda semántica.
- `model_select.rs`: selección de modelo por tarea.
- `offline/`: cola de peticiones cuando no hay red.
- `middleware/`: middleware de peticiones (auth, reintentos, telemetría).
- `ai_tool/`: herramientas invocables por el modelo.
- `search/`: búsqueda sobre el contenido del usuario para fundamentar.

### Pruebas literales

1. **Tabla completa de los eventos de `flowy-ai`** desde
   `OUT/_ledger/extract/events.json` (crate `flowy-ai`): todas sus variantes con
   input/output y línea de handler.
2. **Tabla completa de `ChatNotification`** desde
   `OUT/_ledger/extract/notifications.json` (10 variantes), con su listener Dart
   (`plugins/ai_chat/`, que está en `[[F09.3]]`: cross-ref) o marcada sin uso.
3. Tabla de los **subsistemas** con: fichero, tipo/clase pública, qué resuelve y
   quién lo consume.
4. Tabla de los **modelos de IA** soportados y cómo se eligen (por tarea, por
   usuario, por disponibilidad offline).
5. Tabla de las **herramientas MCP** y de las **`ai_tool`**: nombre, firma,
   propósito.
6. `classDiagram` de `AIManager` y sus subsistemas (nombres verificados).

## Diagramas mínimos (6)

- 1 `flowchart TD` con `subgraph` por capa: UI → BLoC → FFI → `flowy-ai` →
  proveedor (cloud | local | MCP) → streaming de vuelta.
- 2 `sequenceDiagram`: (a) una pregunta de chat con streaming token a token;
  (b) un completion en el editor.
- 1 `stateDiagram-v2`: la máquina de estados de un mensaje de chat
  (pendiente → enviando → en streaming → completado / error).
- 1 `flowchart LR`: el pipeline de embeddings (documento → chunk → embedding →
  `flowy-sqlite-vec` → búsqueda).
- 1 `flowchart TD`: el camino offline (sin red → cola → reintento).
- 1 `sequenceDiagram`: una llamada a una herramienta MCP o `ai_tool`.