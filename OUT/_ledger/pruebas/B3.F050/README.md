# B3.F05 — Usuario, auth (local/cloud/third-party), sesión, miembros, roles, migraciones

**ROADMAP ref:** línea 289 (`B3.F05`).

F05 se dividió en **3 sub-unidades** (131 archivos) y cerró con **3 documentos** en `OUT/09-features/F05-usuario-auth-sesion/`.

| Sub | Doc | Líneas | Archivos | Secciones | Refs | Mermaid | Suite | Revisor |
|---|---|---:|---:|---:|---:|---:|---|---|
| **F05.0** | `0.0-indice-usuario-auth-sesion.md` | 586 | 0 (índice) | 19 | 150 | 4 | ✅ | aprobado |
| **F05.1** | `1-usuario-appflowy-flutter-lib-user-dart.md` | 738 | 73 (Dart) | 19 | 209 | 5 | ✅ | aprobado |
| **F05.2** | `2-usuario-flowy-user-collab-user-rust-collab.md` | 753 | 58 (Rust+Collab) | 19 | 73 | 5 | ✅ | aprobado |
| | | **2 077** | **131** | | **432** | **14** | | |

Todas las suites: `template=1/1`, `evidence=N/N`, `mermaid=N OK`, `cobertura=N/N`, `revisor=aprobado, 0 correcciones`.

## Por qué existe F05.0

`units/F05.1.json` y `F05.2.json` declaraban `dependencias: [{id: "F05.0", tipo: "indice"}]`, pero `F05_SUBS` en `SKILL/scripts/build_units.py` no tenía entrada de índice: la dependencia la generaba `_unit_dependencies()` sin que nadie materializara `F05.0.json`. Se añadió la entrada `("F05.0", …, _exact("__F05_INDEX_SENTINEL__"))` al principio de `F05_SUBS`, de modo que el índice nace con 0 archivos y `F05.1` conserva sus 73 (los 5 ficheros de `workspace/application/{user,appearance_defaults,subscription_success_listenable}` entraron explícitamente en el matcher de F05.1 para que no caigan como `resto` del índice).

## Distribución del código cubierto

| Subárbol | Archivos |
|---|---:|
| `flowy-user/src/entities/**` | 17 |
| `flowy-user/src/services/**` (incl. `data_import/`) | 10 |
| `flowy-user/src/migrations/**` | 9 |
| `flowy-user/src/user_manager/**` | 6 |
| `flowy-user/src/{lib,event_handler,event_map,notification}.rs` + config/build | 7 |
| `collab-user/**` (src + tests) | 9 |
| `lib/user/**` (Dart: application, auth, domain, presentation) | 68 |
| `workspace/application/{user/3, appearance_defaults, subscription_success_listenable}` | 5 |
| **Total** | **131** |

## Pruebas literales superadas

- **56/56 `UserEvent`** tabuladas en F05.2 §4 (discriminantes 0–65 con 9 huecos reservados: 5, 15, 16, 18–20, 23, 32, 52, 60), y agrupadas en 11 dominios en F05.0 §4. Reparto: 41 despachados desde F05.1 · 15 desde otras unidades · **8 sin consumidor Dart en todo el repo**.
- **10/10 `UserNotification`** (discriminantes 0–9, sin huecos) en F05.2 §5; 9 con `case` efectivo en Dart + `Unknown` como centinela.
- **Los 5 eventos de miembros de workspace** con evidencia exacta: registrados en frontend/rust-lib/flowy-user/src/event_map.rs:57–68, handlers en frontend/rust-lib/flowy-user/src/event_handler.rs:574–827 (`GetMemberInfo` #56, `RemoveWorkspaceMember` #38, `UpdateWorkspaceMember` #39, `GetWorkspaceMembers` #40, `InviteWorkspaceMember` #47).
- **10 BLoCs Dart** de F05.1 con **53 eventos freezed**: `SignInBloc` (13), `ReminderBloc` (14), `SettingsUserViewBloc` (7), `PasswordBloc` (6), `SignUpBloc` (4), `AnonUserBloc` (3), `WorkspaceErrorBloc` (3), `NotificationFilterBloc` (2), `SplashBloc` (1).
- **Los 6 ficheros de `user/application/auth/`** con sus clases reales: `auth_service.dart` (`AuthService`, abstracta), `backend_auth_service.dart` (`BackendAuthService`), `af_cloud_auth_service.dart` (`AppFlowyCloudAuthService`), `af_cloud_mock_auth_service.dart` (`AppFlowyCloudMockAuthService`), `auth_error.dart` (`AuthError`), `device_id.dart` (`getDeviceId()`).
- **Los 3 caminos de login** (local/anon, AppFlowy Cloud, OAuth third-party) con `flowchart TD` propio en F05.1 §9.

## Hallazgos materiales

1. **`AuthProvider` y `SignUpMethod` no existen como tipos Dart**: lo real es `ProviderTypePB`, `AuthenticatorType` y `ProviderTypePBExtension`. `[NO DETERMINADO]`
2. **5 `UserEvent` sin despachar desde F05.1**: `GetUserWorkspace` (22), `GetMemberInfo` (56), `SetCloudConfig` (13), `GetCloudConfig` (14), `UpdateNetworkState` (24). `[NO DETERMINADO]`
3. **`workspace/application/user/user_workspace_bloc.dart` es un re-export de una línea** a `lib/features/workspace/logic/` (692 LOC reales, 14 eventos), que quedó fuera del ledger de F05. `[NO DETERMINADO]`
4. **`UserListener._userNotificationCallback` tiene un `switch` sin `break`** (frontend/appflowy_flutter/lib/user/application/user_listener.dart:98–106): el caso `DidUpdateUserWorkspace` cae también en `DidUpdateWorkspaceSetting`. Hoy es inocuo porque los PB tienen formatos distintos. `[INFERIDO]`
5. **`SignUpBloc` existe pero no hay `SignUpScreen`**, y `AppFlowyCloudAuthService.signUp` lanza `UnimplementedError`. `[NO DETERMINADO]`
6. `UserInfo` / `UserPB` no existen: lo real es `UserProfile` (frontend/rust-lib/flowy-user-pub/src/entities.rs:146) y `UserProfilePB`.
7. Los 4 pasos de migración de datos de `flowy-user/src/migrations/` (9 ficheros, 7 pasos en `migration.rs`) son **lógica de datos**, no esquema: el esquema diesel de las 6 migraciones ya está en **B1.7**. Declarado en F05.0 y F05.2 sin redeclararlo.

## Correcciones de scope (ROADMAP vs ledger)

| Prometido en el ROADMAP B3.F05 | Realidad en el ledger | Declarado en |
|---|---|---|
| "miembros, roles" (UI) | `features/share_tab/**`, `share_role.dart`, `share_access_level.dart`, `people_with_access_section.dart`, `turn_into_member_widget.dart` → **F12**; aquí solo los 5 eventos Rust | F05.0 §13, F05.1 §2/§13 |
| "migraciones" | `flowy-user/src/migrations/**` = lógica de datos (F05.2); esquema diesel en **B1.7** | F05.0 §13, F05.2 §8 |
| "sesión" | `manager_user_encryption.rs`, `session_migration.rs`, `history_user.rs` (F05.2); estado Dart en `user/domain/auth_state.dart` (F05.1) | F05.0 §13 |
| awareness / colaboradores | `user_awareness.rs` + `manager_user_awareness.rs` en **F05.2**; `document_collaborators_bloc.dart` et al. en **F01.0.1** | F05.0 §13, F06 §2 |
| auth cloud (lado servidor) | `flowy-server/src/af_cloud/impls/user/*` → **F06** | F05.2 §2 |
| recordatorios | `user/application/reminder/**` comparte terreno con **F15** | F05.1 §2/§13 |

## Suites

| Suite | Resultado |
|---|---|
| `B3.F050/validate-B3.F050.sh` | OK (cobertura 0/0, índice) |
| `B3.F051/validate-B3.F051.sh` | OK (cobertura 73/73) |
| `B3.F052/validate-B3.F052.sh` | OK (cobertura 58/58) |

## Preguntas abiertas (→ `OUT/22-preguntas-abiertas.md`)

10 entradas en `OUT/22-preguntas-abiertas.md §De B3.F05` (tipos inexistentes, 5 eventos sin despachar, `SignUpBloc` huérfano, `UserWorkspaceBloc` fuera de alcance, `signUp` inalcanzable, switch sin `break`, reintento de `load_awareness_from_server`, `notify_did_switch_plan_handler` ante timeout, payload futuro de `DidUpdateReminder`, rotación de `device_id`).

## Cross-references

- **F03.2** — `flowy-folder`: `Workspace`, `GetAllWorkspace`, `OpenWorkspace` y las 19 `FolderNotification`.
- **F03.1** — `workspace/application/workspace/` y `view/` desde el lado Dart.
- **F04** — sidebar, tabs y `WorkspaceStartScreen` como destino tras el login.
- **F06** — `af_cloud/impls/user/{cloud_service_impl,dto,util}.rs`, el lado servidor de `af_cloud_auth_service.dart`.
- **F12** — UI de compartir, miembros y niveles de acceso.
- **F13** — `settings/billing/` y `settings/plan/` del lado Dart del checkout.
- **F15** — notificaciones in-app y recordatorios.
- **F16** — `mobile_sign_in_screen.dart`, `mobile_loading_screen.dart`, `mobile_workspace_start_screen.dart`.
- **B1.4** `05-arranque-y-ciclo-de-vida.md` — `SignOut` y `OpenWorkspace` en el ciclo de vida.
- **B1.7** `08-persistencia/` — esquema de `user_table`, `user_workspace_table`, `workspace_members_table`, `user_data_migration_records`.
- **B4** — `flowy-user/src/services/data_import/**` (importación de datos de AppFlowy).
- **B6.3** — cifrado de sesión (`manager_user_encryption.rs`), tokens y almacenamiento local.
