# gunnchDevice Lab

Virtual Device & Ecosystem Simulator for gunnchOS (WP-003R foundation + WP-011 critical path).

## Tokens (honesty)

```text
GUNNCHDEVICE_LAB_FOUNDATION = PART_OF_WP003R
GUNNCHDEVICE_LAB_PROFILE_SYNC_PREPARED = true
GUNNCHDEVICE_LAB_GUEST_IMAGE_PREPARED = true
GUNNCHDEVICE_LAB_GUEST_AGENT_PREPARED = true
GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE = false   # master stays false
SILICON_EXACT_EMULATION = false
BEHAVIORAL_DEVICE_PROFILE = true
VF4/VF5/VF6 = PHYSICAL_PENDING
```

## CLI

```bash
PYTHONPATH=.:src python3 scripts/gunnchctl devices
PYTHONPATH=.:src python3 scripts/gunnchctl profile sync
PYTHONPATH=.:src python3 scripts/gunnchctl profile verify
PYTHONPATH=.:src python3 scripts/gunnchctl profile diff
PYTHONPATH=.:src python3 scripts/gunnchctl image build
PYTHONPATH=.:src python3 scripts/gunnchctl image inspect
PYTHONPATH=.:src python3 scripts/gunnchctl image verify
PYTHONPATH=.:src python3 scripts/gunnchctl start student_14_5
PYTHONPATH=.:src python3 scripts/gunnchctl start student_14_5 --real-guest
PYTHONPATH=.:src python3 scripts/gunnchctl test GOLDEN-04 --device handheld_docked
PYTHONPATH=.:src python3 scripts/gunnchctl ui --host 127.0.0.1 --port 8765
```

Or: `python3 -m gunnchos_device_os.device_lab …`

## Profiles (hardware-synced)

| Profile | Compute MPN (accepted) | RAM | Storage |
|---------|------------------------|-----|---------|
| student_14_5 | ADLINK COM-HPC-mMTL-155H-32G | 32 GB | NVMe 512 GB (PC801) |
| dsxl_coder | same COM module | 32 GB | NVMe ≥256 GB (matrix; SSD MPN TBD) |
| handheld_hybrid | Radxa RM121-D8E32 | 8 GB | 32 GB eMMC on-module |
| handheld_docked | handheld + dock | 8 GB | 32 GB eMMC |
| dock | Intel JHL8440 (+ JHL9040R retimer) | N/A | N/A |
| edge_io_rings | Nordic nRF52840-QIAA-R | MCU | flash |
| full_ecosystem | aggregate | aggregate | aggregate |

Source pin: `hardware_truth/accepted_hardware_truth.json` (from `gunnchos-hardware-industrial-design` EXACT_MPN_MATRIX / BOM). **Do not invent MPNs.**

CI drift gate: `gunnchctl profile verify` fails on stale RAM/storage/MPN.

## Real guest (QEMU)

- Image: hybrid Alpine minirootfs + real gunnchOS service overlay (`os_build/bootable_reference`).
- `gunnchctl start --real-guest` launches a **real QEMU process** (HVF on Apple Silicon same-arch, KVM on Linux, else TCG).
- Headless default for CI (`-display none`). Live path: `GUNNCHDEVICE_LAB_DISPLAY=vnc|spice` binds **localhost-only** VNC/SPICE (noVNC UI polish later — not fake screenshots).
- Persist disk: `persist.qcow2` under the session work dir.
- Guest agent: `gunnchGuestAgent` foundation (boot complete, process/package stubs→real, display info, logs, metrics, shutdown/reboot hooks). Host mailbox used until virtio-serial is fully linked; serial heartbeats are HOST_OBSERVED.
- No production keys. No unauthenticated broad network (usernet off unless `GUNNCHDEVICE_LAB_USERNET=1` with `restrict=on`).

### Host acceleration notes

| Host | Same-arch guest | Accel |
|------|-----------------|-------|
| macOS Apple Silicon | aarch64 | HVF |
| macOS Intel | x86_64 | HVF |
| Linux + `/dev/kvm` | matching | KVM |
| Cross-arch / no KVM | any | TCG (slow) |

Recorded QEMU versions should come from `qemu-system-* --version` on the operator host (Homebrew `qemu` preferred on macOS).

## Journey mapping

| Journey | Scenario | Profile |
|---------|----------|---------|
| GOLDEN-04 | LAB-SCENARIO-OFFICE-DOCK | handheld_docked |
| GOLDEN-06 | LAB-SCENARIO-DSXL-DUALSCREEN | dsxl_coder |
| GOLDEN-07 | LAB-SCENARIO-RING-REAL-INPUT | edge_io_rings (+ student host) |
| GOLDEN-08 | LAB-SCENARIO-LOCAL-AI-TUTOR | student_14_5 |

## Honesty / limitations

- Modeled ≠ physical. One display ≠ DS-XL dual guest outputs.
- QEMU virt ≠ Radxa RK3588 / ADLINK COM-HPC silicon replica.
- Guest RAM may be **VIRTUAL_CONSTRAINED** below profile GB to protect the host.
- Calibration / EVT / physical measurement: **PHYSICAL_PENDING**.
- Full ecosystem simultaneous sim + polished live UI/apps: **not complete** (master token false).
- If CI cannot run QEMU: tests must report `SKIPPED_ENVIRONMENT` — never claim PASS when skipped.

## WP-010 calibration interfaces (schema only)

- Physical test ID + calibration ingestion + metric map + prediction↔measurement + evidence linkage
- Instrument import adapters under `instrument_import/`
- **VF4/VF5/VF6 remain PHYSICAL_PENDING** — no CALIBRATED_EVT0
