# Pruebas A2.7 — `extract_codegen.sh` + `codegen-result.json`

**Fecha:** 2026-10-18
**Fase:** A2.7 (Codegen — opcional pero recomendada)
**Estado:** ✅ cerrada (outcome = `failed` documentado)

## Objetivo

Intentar ejecutar el codegen de `build-tool/flowy-codegen` para obtener
los `.proto` y el dispatch Dart generado. Si falla, documentar la causa
raíz en `codegen-fallido.md` y seguir con A2.2 (que extrae directamente
de los `.rs` fuente sin depender del codegen).

## Comandos ejecutados

```bash
bash SKILL/scripts/extract_codegen.sh
OUT/_ledger/validate-A2.7.sh
```

Log completo: [`extract.log`](extract.log) y [`validate.log`](validate.log).

## Resultado del validador

```
OK: A2.7 (codegen no ejecutado en este entorno: Toolchain missing o incompleto. ...,
       1 intento(s) documentado(s) en /Users/martin/.../codegen-fallido.md)
exit=0
```

## Outcome: `failed` (esperado en este entorno)

| Estrategia | Estado | Causa |
|---|---|---|
| `cargo_make` | **skipped** | `cargo-make` no instalado + `Makefile.toml` ausente en `rust-lib/`. |
| `cargo_run_bin` | **skipped** | `flowy-codegen/src/main.rs` no existe (solo `lib.rs`; el codegen se invoca como librería). |
| `cargo_build_manual` | **executed** (exit 0) | `cargo build -p flowy-codegen` **compila** la librería (deps ya cacheadas de un intento previo), pero **no ejecuta el codegen** (no hay binario). |

## Prerrequisitos detectados

| Herramienta | Presente | Path |
|---|---|---|
| `cargo` | ✅ | `/Users/martin/.cargo/bin/cargo` |
| `cargo-make` | ❌ | — |
| `protoc` | ❌ | — |
| `protoc-gen-dart` | ❌ | — |
| `Makefile.toml` en `SRC/appflowy/frontend/rust-lib/` | ❌ | — |
| `flowy-codegen/src/main.rs` | ❌ | (solo `lib.rs`; el codegen se invoca como librería) |
| Env `CARGO_MAKE_WORKING_DIRECTORY` | ❌ | — |
| Env `FLUTTER_FLOWY_SDK_PATH` | ❌ | — |

## Causa raíz (resumida)

`flowy-codegen` es un crate Rust que expone `dart_gen(crate_name)`,
`generate_dart_protobuf_files()`, `gen_proto_files()` como funciones de
librería (ver `build-tool/flowy-codegen/src/lib.rs` y
`src/protobuf_file/mod.rs`). Para invocar el codegen desde fuera hay
tres caminos:

1. **`cargo make <tarea>`** — la ruta oficial. Requiere `Makefile.toml`
   (no presente en este snapshot) + `cargo-make` (no instalado).
2. **`cargo run --bin flowy-codegen`** — requiere un binario con
   `main.rs` (no existe; solo `lib.rs`).
3. **Wrapper crate** — escribir un crate nuevo con
   `flowy-codegen = { path = "..." }` y un `fn main()` que llame a
   `dart_gen()`. Requiere también `protoc` y `protoc-gen-dart` para la
   generación efectiva de `.proto` + `.pb.dart`.

## Estado de A2.2 sin dependencia de A2.7

A2.2 (`extract_protobuf.py`) parsea los `.rs` fuente directamente,
sin requerir los `.proto` generados. Por tanto, A2.2 es **funcional
aunque A2.7 falle** — exactamente el caso (b) que el ROADMAP A2.7
permite explícitamente:

> Prueba: o existen `.proto` generados y coinciden con A2.2, o hay un
> `codegen-fallido.md` con causa.

✅ Cumplimos el caso (b).

## Cómo habilitar el codegen en un entorno con toolchain completo

1. Instalar Rust toolchain (rustup, versión según `rust-toolchain.toml`).
2. `cargo install cargo-make`.
3. Instalar Protocol Buffers compiler (`brew install protobuf`).
4. Instalar el plugin Dart de protoc (`dart pub global activate protoc_plugin`).
5. Recuperar/crear `Makefile.toml` en `frontend/rust-lib/`.
6. Configurar env vars:
   ```bash
   export CARGO_MAKE_WORKING_DIRECTORY=$PWD
   export FLUTTER_FLOWY_SDK_PATH=packages/appflowy_backend
   ```
7. Ejecutar `cargo make codegen`.

## Estructura del JSON de resultado

```jsonc
{
  "schema_version": "1.0",
  "generated_at": "2026-10-18T21:16:25Z",
  "tool": {"name": "extract_codegen.sh", "version": "1.0"},
  "fuentes": ["appflowy"],
  "workspace_root": ".../rust-lib",

  "prerequisites": {
    "cargo":            {"present": true,  "path": "/Users/martin/.cargo/bin/cargo"},
    "cargo_make":       {"present": false, "path": ""},
    "protoc":           {"present": false, "path": ""},
    "protoc_gen_dart":  {"present": false, "path": ""},
    "makefile_toml":    {"present": false, "path": ""},
    "flowy_codegen_main": {"present": false, "path": "(lib.rs only — ...)"},
    "cargo_make_working_directory": {"present": false, "value": ""},
    "flutter_flowy_sdk_path":      {"present": false, "value": ""}
  },

  "attempts": [
    {
      "strategy": "cargo_build_manual",
      "command": "cd <rustlib> && cargo build -p flowy-codegen --features proto_gen,dart_event 2>&1",
      "started_at": "...",
      "finished_at": "...",
      "duration_sec": 0,
      "exit_code": 0,
      "stdout_tail": "Finished `dev` profile ...",
      "stderr_tail": "",
      "cause": "compila pero no ejecuta codegen (flowy-codegen es lib, no bin); requiere wrapper"
    }
  ],

  "outcome": "failed",
  "failure_cause_summary": "Toolchain missing o incompleto. ...",
  "output_dir": "/tmp/codegen-run"
}
```

## Tamaño y rendimiento

| Métrica | Valor |
|---|---|
| `codegen-result.json` | 2.6 KB |
| `codegen-fallido.md` | 2.8 KB |
| `codegen-result.md` | 1.5 KB |
| Tiempo del script | < 1 s (todas las estrategias skipped o fallan rápido) |

## Diferencias detectadas vs el plan original (corregidas en sitio)

| # | Diferencia | Acción |
|---|---|---|
| 1 | `cargo` SÍ está presente en el sistema (`/Users/martin/.cargo/bin/cargo`); el plan asumía que faltaba. | Reordenado: estrategia 3 (cargo build) SÍ se intenta y compila exitosamente; el problema es que el codegen no se ejecuta (falta binario). |
| 2 | Bash `echo` no interpreta `\t` (escape sequences). | Corregido: usar `printf 'present\t%s\n'` en `check_prereq()`. |
| 3 | Bash export con tabs en valores se "manglea" en env vars. | Solución: escribir a archivo `.prereq.env` con `|` como separador, leer en Python y convertir `|` → `\t`. |
| 4 | `flowy-codegen` se invoca como librería, no como binario. | Documentado en `codegen-fallido.md` y `codegen-result.md` como estrategia "wrapper crate" recomendada para un entorno con toolchain. |

Sin impacto sobre la decisión de cierre de fase: el test del ROADMAP
permite (b) `failed documentado`, y nuestro `codegen-fallido.md` cumple
el criterio.

## Criterio de aprobación del ROADMAP

> Prueba: o existen `.proto` generados y coinciden con A2.2, o hay un `codegen-fallido.md` con causa.

- ✅ `codegen-result.json` con `outcome: "failed"` y `failure_cause_summary` no vacío.
- ✅ `codegen-fallido.md` existe, > 100 bytes, documenta causa raíz, prerrequisitos faltantes, estrategia intentada, código relevante, y plan de remediación.
- ✅ Validador acepta outcome=failed con checks 1-7.
- ✅ A2.2 (`extract_protobuf.py`) es independiente y ya pasó en A2.2.
