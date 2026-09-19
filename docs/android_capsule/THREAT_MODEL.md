# gunnchOS Capsule Threat Model (experience host on stock Android)

## Scope

Capsule-1 ships a normal Android application (`com.gunnchos.capsule`) that embeds the
production `gunnch_shell` Complete Experience. Threats are bounded to the Android app
sandbox and the typed host bridge. This is **experience parity**, not kernel/device identity.

## Assets

- User Vault documents (app-private + SAF grants)
- Session restore state
- Clipboard / share payloads mediated by the bridge
- Optional Linux guest state (if enabled later)
- Support / Care snapshots (non-root)

## Trust boundaries

1. **Android OS** — provides sandbox, permissions, intents, notifications.
2. **Capsule Host (Kotlin)** — allowlisted bridge; permission mediation; no arbitrary JS eval.
3. **Experience Runtime (WebView shell)** — production React shell assets only.
4. **Providers** — Vault / App Center / WAIKE / gunnchAI / Games / Connect / Assist / Care / Guest.
5. **Optional Guest** — QEMU TCG or experimental AVF; never replaces primary shell.

## Explicit non-goals (not protected as Capsule claims)

- Bootloader unlock, root, custom recovery, factory wipe, repartition
- Privileged Android control or hidden API production use (AVF prop probe is experimental-only)
- Bare-metal / custom-board / HW certification equivalence

## Controls

| Control | Mechanism |
| --- | --- |
| Capability allowlist | `BridgeSchemas.ALLOWED_CAPABILITIES` |
| Origin validation | `file:///android_asset/...` only |
| Payload validation | Reject `eval` / `javascript` / `code` keys; size limits |
| Permission mediation | Runtime checks before camera/mic/notifications/BT |
| No silent installs | App Center never calls package installer silently |
| Files | App-private + SAF; no broad storage permission by default |
| Network | Cleartext denied except loopback guest tooling |
| Exit | Explicit `exit_capsule` returns to Android home |

## Failure classes (oracle)

See `tools/android_capsule/oracle.py`:
`BRIDGE_ALLOWLIST_VIOLATION`, `ORIGIN_REJECT`, `PERMISSION_BYPASS`, `SILENT_INSTALL_ATTEMPT`,
`BROAD_FS_PERMISSION`, `ROOT_API_USE`, `PIXEL_WIPE_REQUIRED`, `BOOTLOADER_UNLOCK_REQUIRED`,
`SHELL_NOT_PRODUCTION`, `SESSION_LOSS`, `GUEST_OVERCLAIM`.

## Residual risks

- WebView XSS within bundled assets could call allowlisted capabilities (mitigate with CSP-ish
  local-only assets, no remote shell load in pilot).
- Intent redirection via `open_url` / `open_android_app` (mitigate with scheme/package validation).
- Experimental `SystemProperties` reflect for AVF probe (non-production; never for control plane).

## Gate

`CAPSULE_SECURITY_BOUNDARY_PASS=true` when allowlist + origin + no-root + no-wipe constraints hold
and unit tests for bridge security pass.
