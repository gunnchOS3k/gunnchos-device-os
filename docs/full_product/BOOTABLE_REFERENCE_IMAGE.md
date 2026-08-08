# FULL PRODUCT CONTINUATION IV — Bootable reference image + platform coherence

## Scope

Continuation from merged #59/#58 (runtime service matrix, reproducible *digital* system-image path, dual-screen workflow validators, dock continuity suite, cloud/fleet/security).

This wave delivers a **genuinely bootable DEV/VM reference image** under QEMU aarch64, plus platform coherence for packaging, update/recovery, dual-screen runtime workflows, and dock fault-injection expansion.

## Honest tokens

| Token | Meaning |
|-------|---------|
| `GUNNCHOS_BOOTABLE_REFERENCE_IMAGE_DIGITAL_PASS` | QEMU serial boot evidence contains required markers (kernel+initramfs+init+services+shell+net+updater+recovery) |
| `GUNNCHOS_APP_PACKAGING_DIGITAL_PASS` | First-party app + game package manifests validate |
| `GUNNCHOS_UPDATE_RECOVERY_DIGITAL_PASS` | A/B corrupt/interrupted update, rollback, factory reset suite passes |
| `GUNNCHOS_DUAL_SCREEN_RUNTIME_WORKFLOW_DIGITAL_PASS` | Sequenced dual-screen runtime workflows + service cross-wire + fault detection |
| `DOCK_CONTINUITY_SIMULATION_PASS` | Continuity suite including fault-injection expansions |
| `GUNNCHOS_PHYSICAL_BOOT_PENDING` | Always co-emitted — no physical device boot claim |

**Not claimed:** `FULL_OPERATIONAL_PRODUCT`, production keys, physical boot, MDM, carrier networking.

## Bootable reference image

- **Target:** `qemu-system-aarch64` machine `virt`, linux direct-kernel boot (`-kernel` / `-initrd`)
- **Rootfs:** Alpine 3.21 minirootfs + gunnchOS overlay (`os_build/bootable_reference/overlay`)
- **Init:** `/init` starts 17 long-lived service stubs, shell self-test, loopback networking, A/B updater status, recovery self-check
- **Evidence:** `results/full_product/bootable_reference/qemu_serial_boot.log` + `BOOT_EVIDENCE.json`

```bash
PYTHONPATH=.:src python3 scripts/build_bootable_reference_image.py
PYTHONPATH=.:src pytest -q tests/test_bootable_reference_image.py
```

## Platform coherence commands

```bash
PYTHONPATH=.:src pytest -q \
  tests/test_bootable_reference_image.py \
  tests/test_app_packaging.py \
  tests/test_update_recovery_completeness.py \
  tests/test_dual_screen_runtime.py \
  tests/test_dock_continuity_sim_suite.py \
  tests/test_runtime_services.py
```
