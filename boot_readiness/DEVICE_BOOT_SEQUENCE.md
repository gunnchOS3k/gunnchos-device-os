# Device Boot Sequence

**Status:** intended sequence documented · **not executed on reference hardware**

Aligns with hardware repo: `../gunnchos-hardware-industrial-design/dvt/DVT_SOFTWARE_HARDWARE_INTEGRATION_PLAN.md`

---

## Phases (intended)

```
Power → Bootloader → HW detect → Profile bind → Policy init → Shell → First-run (if new)
```

---

## Phase 1 — Power and firmware

| Step | Action | Simulated today | Hardware evidence |
|------|--------|-----------------|-------------------|
| 1.1 | Power button / wake | N/A | not linked |
| 1.2 | Bootloader / UEFI handoff | N/A | not linked |
| 1.3 | Secure boot trust check (if enabled) | doc only | `docs/SECURE_BOOT_AND_TRUST_MODEL.md` |

Flash layout: **TBD** per hardware `docs/OS_HARDWARE_CONTRACT.md`.

---

## Phase 2 — Hardware profile detection

| Step | Action | Simulated today | Hardware evidence |
|------|--------|-----------------|-------------------|
| 2.1 | Read hardware IDs (ACPI/SMBIOS/DT) | explicit `device_id` param | not linked |
| 2.2 | Map to OS profile | manifest loader | [HARDWARE_PROFILE_DETECTION_PLAN.md](HARDWARE_PROFILE_DETECTION_PLAN.md) |
| 2.3 | Handle ambiguous ID (e.g. `student_14` vs `student_14_5`) | manual | mapping table needed |

Implementation stub: `gunnchos_device_os/hardware_capability_detector.py`

---

## Phase 3 — Capability and policy init

| Step | Action | Simulated today |
|------|--------|-----------------|
| 3.1 | Load YAML profile | yes |
| 3.2 | Run capability detect | yes (profile-based) |
| 3.3 | Initialize input/display/power/thermal/storage/network policies | yes (software) |
| 3.4 | Evaluate boot readiness checks | yes |

---

## Phase 4 — Boot decision

| Outcome | Condition | User message (simulated) |
|---------|-----------|--------------------------|
| Boot OK | all checks pass | "Device profile loaded — simulated boot OK." |
| Boot fail | any check fails | "Boot readiness check failed in simulation." |
| Safe mode | critical policy fail (intended HW) | Enter safe mode — see recovery plan |
| Recovery | unrecoverable boot (intended HW) | USB recovery — see recovery plan |

API: `hardware_boot_readiness.evaluate_boot_readiness()`

---

## Phase 5 — Shell and mode

| Step | Action | Notes |
|------|--------|-------|
| 5.1 | Apply default journey preset (e.g. scooter) | per profile |
| 5.2 | Enforce guardian/marshal defaults | wearables venue |
| 5.3 | Mode matrix available | `hardware_mode_policy.py` |

---

## Phase 6 — First run

See [FIRST_RUN_HARDWARE_BINDING.md](FIRST_RUN_HARDWARE_BINDING.md).

---

## Per-SKU notes

| SKU | Boot-specific concern |
|-----|----------------------|
| Student 14.5 | Dock EDID hotplug at login |
| Handheld Hybrid | Controller vs touch default; TV dock |
| DS-XL Coder | Dual-display init order |
| Wearables / Arena | Marshal policy before Play mode |

---

## Claim boundary

This sequence is **design intent**. Simulated boot readiness validates profile presence only, not firmware or driver behavior on silicon.
