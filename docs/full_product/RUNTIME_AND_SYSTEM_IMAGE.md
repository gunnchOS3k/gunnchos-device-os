# FULL PRODUCT CONTINUATION III — gunnchOS runtime + system image

## Scope

Continuation from merged #57 (sandbox, DEV attestation, OTA SM, identity, runtime profiles, dual-screen). This wave adds:

1. Integrated **runtime service architecture** (18 services, including privacy)
2. **Reproducible system image** digital path
3. Dual-screen **workflow stubs + validators**
4. Expanded **dock continuity simulation** suite

## Honest tokens

| Token | Meaning |
|-------|---------|
| `GUNNCHOS_RUNTIME_SERVICE_MATRIX_DIGITAL_PASS` | All required services registered with deps/API |
| `GUNNCHOS_REPRODUCIBLE_SYSTEM_IMAGE_DIGITAL_PASS` | DEV bundle builds + validates reproducibly |
| `GUNNCHOS_DUAL_SCREEN_WORKFLOW_DIGITAL_PASS` | All workflow types validate |
| `DOCK_CONTINUITY_SIMULATION_PASS` | Continuity simulation suite ok |
| `GUNNCHOS_PHYSICAL_*_PENDING` | Physical evidence not claimed |

**Not claimed:** `FULL_OPERATIONAL_PRODUCT`, production keys, bootable disk image, MDM.

## Service matrix (digital)

HAL, input, ring, display, dock, continuity, identity, permissions, sandbox, updater, recovery, diagnostics, connectivity, AI interface, profile manager, a11y, fleet agent — each with startup, deps, config, persistence, fault injection, and API via `RuntimeSupervisor`.

## Commands

```bash
PYTHONPATH=.:src pytest -q \
  tests/test_runtime_services.py \
  tests/test_system_image.py \
  tests/test_dual_screen_workflows.py \
  tests/test_dock_continuity_sim_suite.py
```
