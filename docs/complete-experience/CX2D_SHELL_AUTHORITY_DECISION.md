# CX2D Shell Authority Decision

**Gate:** First CX2D architecture gate  
**Token:** `CX2D_SINGLE_PRODUCTION_SHELL_AUTHORITY=true`  
**Chosen path:** **Path B**

## Audit summary

| Candidate | Role | Production readiness |
|-----------|------|----------------------|
| `apps/launcher_mock` + `src/cx2/CompleteExperienceShell` | React first-party Home/Vault/App Center/Connect/Assist/Care | Most mature rendered UX; previously misnamed “mock” |
| `gunnchos_device_os/cx2/shell/product_shell.py` | Python surface contract + provider binding | Contract/harness authority — not compositor UI |
| `apps/device_dashboard_mock` | Fleet/device admin mock | Not ordinary-user shell |
| Device Lab Interactive Guest Weston session | Guest compositor + chromium | Session/compositor, not product shell |
| `gunnchos_device_os/launcher.py` / stage2 shell | Legacy policy launchers | Not Complete Experience UX |
| Journey preset engine | Profile/policy selection | Not UI shell |
| Installable image `gunnchos-shell` | Boot stub | Not Complete Experience surfaces |

## Decision — Path B

`launcher_mock` held the only Complete Experience React surfaces. Silently treating that path as production was unsafe.

**Promote** those surfaces into:

`apps/gunnch_shell`

as the **sole production shell authority**.

`apps/launcher_mock` becomes a **deprecated research/dev adapter** that re-exports `apps/gunnch_shell` so CX2A–CX2C wiring and Device Lab/journey entries keep working without dual authorities.

Python `ProductShell` remains the **provider/contract** companion used by journey harnesses; it does not compete as a second production GUI authority.

## Explicit non-choices

- **Path A rejected:** No separate pre-existing production shell package owns these surfaces.
- **Path C deferred:** A formal `ShellAuthority` interface can be added later; Path B already yields one production GUI package without dual peers.

## Migration notes

- Source of truth: `apps/gunnch_shell/src/CompleteExperienceShell.tsx` (+ surfaces/css/theme)
- Adapter: `apps/launcher_mock/src/cx2/*` re-exports production package
- Tests: `apps/gunnch_shell` owns production vitest; launcher_mock keeps adapter smoke tests
- Linux lab must launch `gunnch_shell` (Vite build or packaged webview), not a second shell

## Authority token

```
CX2D_SINGLE_PRODUCTION_SHELL_AUTHORITY=true
```
