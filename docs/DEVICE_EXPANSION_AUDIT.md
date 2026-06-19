# Device Expansion Audit

**Pass target:** EVT-1 OS alpha — not final manufacturing or shipping OS.

## Current state

This repo is currently **concept / EVT-0 or alpha scaffold**. Existing `gunnchos_launcher` package, launcher mock UI, campus modes, telemetry bridges, and access-risk lab provide foundations. This pass moves toward **EVT-1 readiness**, not final manufacturing readiness.

## Launcher

| Item | Status | Notes |
|------|--------|-------|
| `apps/launcher_mock/` | present | React mock — not installable shell |
| Mode switching UI | partial | School/Developer/Play/Research in mock |
| EVT-1 dashboard mock | **added this pass** | `apps/device_dashboard_mock/` placeholder |

## Mode manager

| Item | Status | Notes |
|------|--------|-------|
| `src/gunnchos_launcher/mode_manager.py` | present | Legacy 5 modes |
| `gunnchos_device_os/mode_manager.py` | **added** | 6 modes incl. Media, Admin |

## App structure

| Item | Status |
|------|--------|
| `src/gunnchos_launcher/app_registry.py` | partial |
| `gunnchos_device_os/app_registry.py` | **added** — categorized apps |

## Tests

| Item | Status |
|------|--------|
| Legacy pytest (`tests/test_mode_manager.py`, etc.) | present |
| EVT-1 pytest suite | **added** |

## CI

| Item | Status | Gap |
|------|--------|-----|
| `.github/workflows/ci.yml` | present | Extend for EVT-1 demo + PYTHONPATH |
| `scripts/check_required_files.py` | present | Portfolio hardening |

## Gaps addressed this pass

| Gap | EVT-1 action |
|-----|----------------|
| Installable OS path | `scripts/build_os_alpha_bundle.py` mock bundle |
| Steam integration | `steam_integration.py` mock detect/launch |
| WSL/dev tools | `wsl_dev_tools.py` + PowerShell install scripts |
| Media/streaming | `media_apps.py` browser-route mocks |
| Updater | `updater.py` signed manifest mock |
| Rollback | `rollback.py` known-good version mock |
| Secure boot story | docs only — not implemented |
| Fleet management | `FLEET_MANAGEMENT_ROADMAP.md` |
| Hardware abstraction | `hardware_abstraction.py` device profiles |
| Device profiles | Student14, HandheldHybrid, DSXLCoder, WearableArenaKit |

## Not claimed

- certified hardware
- finished OS
- mass-production readiness
- regulatory approval
- finished Steam/media licensing
