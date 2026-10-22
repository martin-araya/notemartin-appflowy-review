---
id: fixture-a32-mix
estado: verificable
---
# Fixture mixto (A3.2)

Cinco referencias: 2 válidas y 3 con errores distintos. El validador
debe reportar exactamente las refs 2, 3 y 4 (no la 1 ni la 5).

- `appflowy/frontend/rust-lib/flowy-date/src/event_map.rs:1` (válida).
- `appflowy/this/file/is/fake.dart:5` (E_PATH_NOT_IN_INVENTORY).
- `appflowy/frontend/rust-lib/flowy-date/src/event_map.rs:99999` (E_LINE_OUT_OF_RANGE).
- `appflowy/frontend/rust-lib/flowy-date/src/event_map.rs:10-5` (E_RANGE_INVERTED).
- `collab:collab-database/src/blocks/block.rs:100` (válida).
