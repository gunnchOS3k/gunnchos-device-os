# Boot Readiness Requirements

**Status:** requirements documented · **hardware boot not proven**

---

## Goal

Define conditions that must be met before gunnchOS may claim boot readiness for a device class. Two tiers:

| Tier | Name | Current state |
|------|------|---------------|
| T0 | Simulated boot readiness | **met** (profile checks) |
| T1 | Hardware boot readiness | **not met** |

---

## T0 — Simulated (current)

All must pass in `hardware_boot_readiness.evaluate_boot_readiness()`:

| Check | Requirement |
|-------|-------------|
| `profile_available` | YAML profile loads for `device_id` |
| `display_available` | Display block has resolution or size |
| `input_available` | At least one of keyboard, touch, controller |
| `storage_sufficient` | `storage.min_gb > 0` |
| `battery_policy_available` | Battery class defined |
| `thermal_policy_available` | Thermal class defined |
| `accessibility_defaults_available` | Profile accessibility block present |
| `recovery_fallback_available` | Recovery path flagged in simulation |
| `safe_mode_path_available` | Safe mode path flagged in simulation |
| `unsupported_mode_fallback_available` | Mode fallback policy exists |

---

## T1 — Hardware (required for release claim)

| ID | Requirement | Evidence |
|----|-------------|----------|
| BR-001 | Device powers on to bootloader | Power-on log / video |
| BR-002 | Bootloader loads OS image | Boot log |
| BR-003 | Correct SKU detected or user-confirmed once | Detection plan execution |
| BR-004 | Primary display initializes at profile resolution | DVT display report |
| BR-005 | Primary input functional | DVT input report |
| BR-006 | Storage accessible at or above profile minimum | Storage qualification |
| BR-007 | Battery fuel gauge readable (if battery-powered) | DVT battery report |
| BR-008 | Thermal sensors readable (if active cooling SKU) | DVT thermal report |
| BR-009 | Safe mode reachable | Recovery test log |
| BR-010 | USB recovery image boots | Recovery artifact test |
| BR-011 | First-run binding completes | First-run test log |
| BR-012 | Unsupported mode falls back without brick | Integration test |

Hardware alignment: `../gunnchos-hardware-industrial-design/dvt/DVT_SOFTWARE_HARDWARE_INTEGRATION_PLAN.md`

---

## Per device class priority

| Order | Device | Rationale |
|-------|--------|-----------|
| 1 | Student 14.5 | Primary school deployment target |
| 2 | DS-XL Coder | Deploy source integration |
| 3 | Handheld Hybrid | Gaming thermal/battery complexity |
| 4 | Wearables / Arena | Lowest hardware maturity |

---

## Non-requirements (explicit)

- HLK certification (tracked separately in hardware release)
- Production CM signoff
- FCC/CE label compliance at boot

---

## Traceability

- OS requirements: `requirements/BOOT_AND_RECOVERY_REQUIREMENTS.md`
- Simulated implementation: `gunnchos_device_os/hardware_boot_readiness.py`
- Status: [BOOT_READINESS_STATUS.md](BOOT_READINESS_STATUS.md)
