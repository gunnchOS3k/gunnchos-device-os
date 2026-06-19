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

## Gaps addressed (PRD §5.2 full module list)

| Module | Path |
|--------|------|
| Launcher | `gunnchos_device_os/launcher.py` |
| Parental controls | `gunnchos_device_os/parental_controls.py` |
| Device health | `gunnchos_device_os/device_health.py` |
| Input mapper | `gunnchos_device_os/input_mapper.py` |
| WAIKE / gunnchAI3k | `waike_integration.py` · `gunnchai_integration.py` |
| Coder mode (DS-XL) | `mode_manager.py` |
| community_partner profile | `profile_manager.py` |
| Full PRD acceptance | `docs/EVT1_OS_ACCEPTANCE_CRITERIA.md` |

## Not claimed

- certified hardware
- finished OS
- mass-production readiness
- regulatory approval
- finished Steam/media licensing
