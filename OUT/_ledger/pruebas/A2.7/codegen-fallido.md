# Codegen A2.7 — Fallo documentado

**Fecha:** 2026-10-18T21:16:25Z
**Outcome:** `failed` (esperado en este entorno).

## Causa raíz

El codegen de `build-tool/flowy-codegen` requiere las siguientes herramientas y archivos, que no están todos disponibles en este entorno:

| Prerrequisito | Estado |
|---|---|
| `cargo` | present	/Users/martin/.cargo/bin/cargo |
| `cargo-make` | absent	 |
| `protoc` | absent	 |
| `protoc-gen-dart` | absent	 |
| `Makefile.toml` en `/Users/martin/Desktop/projects/Skills/notemartin-appflowy-review/SRC/appflowy/frontend/rust-lib` | absent	 |
| `flowy-codegen/src/main.rs` | absent	(lib.rs only — flowy-codegen se invoca como librería) |
| Env `CARGO_MAKE_WORKING_DIRECTORY` | false |
| Env `FLUTTER_FLOWY_SDK_PATH` | false |

## Estrategias intentadas

### Intento 1 — cargo_build_manual

- **Comando:** `cd /Users/martin/Desktop/projects/Skills/notemartin-appflowy-review/SRC/appflowy/frontend/rust-lib && cargo build -p flowy-codegen --features proto_gen,dart_event 2>&1`
- **Exit code:** 0
- **Causa:** compila pero no ejecuta codegen (flowy-codegen es lib, no bin); requiere wrapper
- **stderr (tail):**

```
(vacío)
```


## Código relevante

El codegen se ejecuta como librería en
`/Users/martin/Desktop/projects/Skills/notemartin-appflowy-review/SRC/appflowy/frontend/rust-lib/build-tool/flowy-codegen/src/lib.rs` (líneas 1-66 definen `Project` y `ProtoCache`).
Los entry points principales son:
- `protobuf_file::mod.rs::dart_gen(crate_name: &str)` — genera `.proto` + Dart + Rust.
- `dart_event::mod.rs` — genera el dispatch Dart a partir de `Flowy.toml`.

Sin `Makefile.toml` o binario expuesto, invocar el codegen desde fuera requiere
construir manualmente un wrapper que llame a estas funciones con los env vars correctos.

## Cómo habilitar el codegen en un entorno con toolchain

1. Instalar Rust toolchain (rustup; la versión de `rust-toolchain.toml` si difiere).
2. Instalar cargo-make: `cargo install cargo-make`.
3. Instalar Protocol Buffers compiler: `brew install protobuf` (macOS) o equivalente.
4. Instalar el plugin Dart de protoc: `dart pub global activate protoc_plugin`.
5. Crear/recuperar `Makefile.toml` en `/Users/martin/Desktop/projects/Skills/notemartin-appflowy-review/SRC/appflowy/frontend/rust-lib` (no presente en este snapshot).
6. Configurar `CARGO_MAKE_WORKING_DIRECTORY=$PWD` y `FLUTTER_FLOWY_SDK_PATH=packages/appflowy_backend`.
7. Ejecutar `cargo make codegen`.

## Estado de A2.2 sin dependencia de A2.7

A2.2 (`extract_protobuf.py`) extrae las entidades `#[derive(ProtoBuf)]` y
`#[derive(ProtoBuf_Enum)]` directamente de los `.rs` fuente, sin requerir
los `.proto` generados. Por tanto, A2.2 es funcional aunque A2.7 falle.
Este es exactamente el caso (b) que el ROADMAP A2.7 permite explícitamente.
