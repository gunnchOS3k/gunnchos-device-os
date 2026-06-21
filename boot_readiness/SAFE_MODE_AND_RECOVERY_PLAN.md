# Safe Mode and Recovery Plan

**Status:** plan documented · **recovery images not hardware-tested**

OS requirements baseline: `requirements/BOOT_AND_RECOVERY_REQUIREMENTS.md`  
Release artifacts: `release_artifacts/RECOVERY_ARTIFACT_REQUIREMENTS.md`

---

## Safe mode

### Purpose

Boot a minimal OS surface when:

- Profile detection is ambiguous or failed
- Critical driver/display init fails
- Unsupported mode would brick normal boot
- Guardian/marshal policy requires restricted shell

### Simulated status

`hardware_boot_readiness.py` sets `safe_mode_path_available: True` when profile loads — **policy flag only**.

### Intended safe mode capabilities

| Capability | Included |
|------------|----------|
| Text or minimal GUI diagnostics | yes |
| Network for recovery download (optional) | yes |
| USB recovery trigger | yes |
| Profile re-selection | yes |
| Full gaming/developer modes | no |
| Deploy source (DS-XL) | degraded / disabled |

---

## Recovery paths

| Path | Use case | Hardware evidence |
|------|----------|-------------------|
| USB recovery image | OS corruption, failed update | not tested |
| Bootloader recovery partition | A/B update rollback | flash layout TBD |
| Network recovery (guardian/admin) | Fleet-managed reinstall | not tested |
| Factory reset | User-initiated wipe | not tested |

Hardware secure update: `../gunnchos-hardware-industrial-design/docs/OS_HARDWARE_CONTRACT.md` — flash layout TBD.

---

## Per-SKU considerations

| SKU | Safe mode note |
|-----|----------------|
| Student 14.5 | Keyboard-required diagnostics; external display optional |
| Handheld Hybrid | Controller + touch navigation in safe mode |
| DS-XL Coder | Single-screen fallback layout in safe mode |
| Wearables / Arena | Minimal UI; marshal/admin only for venue reset |

---

## Entry triggers (intended)

1. Failed boot readiness on hardware (T1 checks)
2. User key chord at boot (TBD per platform)
3. Guardian/admin fleet command
4. Update rollback failure

---

## Exit triggers

1. Successful re-bind to profile after fix
2. Recovery image flash complete
3. Explicit admin signoff for venue devices

---

## Integration with mode policy

Unsupported mode combinations fall back per [../docs/HARDWARE_MODE_POLICY.md](../docs/HARDWARE_MODE_POLICY.md) before safe mode is needed in normal operation. Safe mode is **last resort**, not default fallback.

---

## Evidence required

| Artifact | Gate |
|----------|------|
| USB recovery boots on each SKU | T1 boot readiness |
| Safe mode reachable without brick | BR-009 |
| Rollback after failed update | update requirements |

Track in `../hardware_release/HARDWARE_COMPATIBILITY_EVIDENCE_MATRIX.md`.

---

## Claim boundary

Safe mode and recovery are **planned**. Simulated boot only asserts that recovery fallback flags exist in profile evaluation — not that recovery media works on hardware.
