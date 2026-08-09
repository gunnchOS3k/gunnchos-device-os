# FULL PRODUCT CONTINUATION VI — service-specific contracts + app runtime

## Base

Branched from PR #63 tip (`bd68181`) so the QEMU TCG / SQLite CI fix is included.
`origin/main` (#62) remains red until #63 merges — Cont VI must not worsen that.

## What Cont VI adds

1. **Service-specific APIs** for all 17 runtime services (HAL→fleet_agent) with real
   semantics (inventory, pair/auth, bearers, OTA stages, revoke, etc.) — not health-only.
2. **IPC semantic tests**: request/response, mutation, persistence, dependency call,
   permission rejection, timeout, restart.
3. **QEMU boot proofs**: HAL/display/dock/connectivity/AI/updater/fleet + app launch policy.
4. **App runtime**: WAIKE, coding/creation, management/diagnostics, four games
   (Cont VII replaces beatlink stub with accepted package; launch path real).
5. **Connectivity**: `TerrestrialBearer`, `FutureNTNBearer` (no fake current NTN),
   `SimulatedNTNBearer`, `EthernetBearer`, `WiFiBearer`; RM520N-GL simulated fixture.
6. **Fleet lifecycle**: restart, multi-instance, enroll/revoke, OTA/rollback campaigns,
   stale, telemetry backlog, offline recovery.
7. **Security tests** against services + cloud plane.

## Honest tokens

| Token | Status |
|-------|--------|
| `GUNNCHOS_RUNTIME_IPC_DIGITAL_PASS` | retained when IPC semantics pass |
| `GUNNCHOS_APP_RUNTIME_DIGITAL_PASS` | earned when category launches pass |
| `GUNNCHOS_BOOTABLE_REFERENCE_IMAGE_DIGITAL_PASS` | retained if QEMU still green |
| `FULL_GUNNCHOS_PLATFORM_DIGITAL_COMPLETE` | **false / not earned** — guest IPC remains mailbox; cloud DEV-only; physical boot pending |

## Commands

```bash
make full-product-vi
# or
PYTHONPATH=.:src pytest -q tests/test_continuation_vi_*.py tests/test_bootable_reference_image.py
```


> Cont VII supersedes the Cont VI allowance for Beat Link stub content and may earn `FULL_GUNNCHOS_PLATFORM_DIGITAL_COMPLETE` without physical boot.
