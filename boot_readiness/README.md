# Boot Readiness

**Status:** Simulated boot readiness exists. Real hardware boot is not yet proven.

Boot readiness documentation and simulation for gunnchOS device profiles. This package defines requirements, sequences, detection plans, and fallbacks for **profile-based** boot evaluation.

**Code:** `gunnchos_device_os/hardware_boot_readiness.py`  
**Hardware repo:** [`../gunnchos-hardware-industrial-design`](../gunnchos-hardware-industrial-design)

---

## Documents

| Document | Purpose |
|----------|---------|
| [BOOT_READINESS_REQUIREMENTS.md](BOOT_READINESS_REQUIREMENTS.md) | What must be true before boot-ready claim |
| [DEVICE_BOOT_SEQUENCE.md](DEVICE_BOOT_SEQUENCE.md) | Intended boot sequence per phase |
| [HARDWARE_PROFILE_DETECTION_PLAN.md](HARDWARE_PROFILE_DETECTION_PLAN.md) | How OS detects SKU from hardware signals |
| [SAFE_MODE_AND_RECOVERY_PLAN.md](SAFE_MODE_AND_RECOVERY_PLAN.md) | Safe mode and recovery paths |
| [FIRST_RUN_HARDWARE_BINDING.md](FIRST_RUN_HARDWARE_BINDING.md) | First-run binding to detected profile |
| [BOOT_FAILURE_FALLBACKS.md](BOOT_FAILURE_FALLBACKS.md) | Failure modes and degraded boot |
| [BOOT_READINESS_STATUS.md](BOOT_READINESS_STATUS.md) | Current status |

---

## What exists today

- `evaluate_boot_readiness(device_id)` returns simulated pass when profile fields satisfy checks
- Checks: profile, display, input, storage, battery policy, thermal policy, accessibility defaults, recovery/safe mode flags
- Explicit `status: simulated` and claim boundary in API response

---

## What does not exist today

- Firmware/UEFI handoff logs on reference boards
- Automatic SKU detection from ACPI/DT/EFID without explicit `device_id`
- HLK-validated boot drivers
- Field recovery image tested on hardware

---

## Related packages

- `hardware_compat/` — profiles consumed at boot simulation
- `hardware_release/` — evidence required for boot-ready release claim
- `requirements/BOOT_AND_RECOVERY_REQUIREMENTS.md`
