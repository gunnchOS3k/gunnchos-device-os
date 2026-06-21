# Boot and Recovery Requirements

**Status:** design requirements · boot/recovery **not production-proven**

> Defines boot health, safe mode, and recovery behavior for gunnchOS. Secure boot and factory recovery on hardware require per-SKU evidence — not claimed today. This document does not claim secure boot complete on all devices without per-SKU reports.

---

## Boot requirements

| Requirement | Description | Alpha evidence |
|-------------|-------------|----------------|
| Boot health check | Verify launcher, policy engine, critical configs on startup | Mock only |
| Device-class detection | Load profile from `device_classes.yaml` contract | Python module + tests |
| Mode persistence | Last mode restored unless policy blocks | `mode_manager.py` |
| Corrupted config fallback | Load safe defaults; surface repair UI | **planned** |
| Boot timing budget | Launcher interactive within documented SLA per SKU | **not measured** |

---

## Safe mode

- Trigger: failed boot count, user key chord, guardian/admin policy
- Behavior: minimal launcher, network optional, no third-party app auto-launch
- Exit: successful health check or explicit user confirmation
- Logging: security event for safe mode entry/exit

---

## Recovery menu

Must offer (wording may vary by SKU):

1. **Restart launcher** — reload configs without full OS reboot
2. **Last known good config** — restore previous policy bundle
3. **Rollback OS-layer** — tie to [UPDATE_AND_ROLLBACK_REQUIREMENTS.md](UPDATE_AND_ROLLBACK_REQUIREMENTS.md)
4. **Repair profile** — reset single profile; preserve others on shared devices
5. **Factory reset** — wipe gunnchOS profiles and app data; confirm twice
6. **Offline recovery** — apply recovery bundle from USB (see recovery artifacts)

---

## User data protection

- Factory reset requires explicit confirmation; guardian PIN on child profiles
- School/library shared device: session end clears ephemeral data by default ([SCHOOL_LIBRARY_REQUIREMENTS.md](SCHOOL_LIBRARY_REQUIREMENTS.md))
- Recovery must not upload private content without consent
- Rollback from failed update must not destroy user documents outside gunnchOS sandbox

---

## Guardian / school / admin recovery rules

| Role | Allowed actions |
|------|-----------------|
| Guardian | Approve reset, restore last good, block factory reset without PIN |
| School admin | Shared-device wipe, library mode reset, no guardian PIN bypass without policy |
| Device admin | Full factory reset, recovery bundle apply, audit log export |

---

## Rollback from failed update

- Detect failed update via health check or explicit failure log
- Auto-offer rollback to previous known good version
- Preserve user data per rollback policy in updater design

---

## Evidence required

| Stage | Evidence |
|-------|----------|
| RC | Recovery menu demo on reference hardware; rollback drill log |
| GA | Per-SKU recovery test report; factory reset data wipe verification |

---

## Claim boundary

Recovery requirements are specified here. The repo does **not** claim secure boot complete on all devices or hardware-validated recovery paths.
