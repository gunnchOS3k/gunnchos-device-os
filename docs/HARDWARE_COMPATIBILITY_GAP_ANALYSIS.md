# Hardware Compatibility Gap Analysis

**Status:** gap analysis complete · **gaps remain open**

**Hardware repo reference:** [`../gunnchos-hardware-industrial-design`](../gunnchos-hardware-industrial-design)

---

## Summary

The OS compatibility layer covers profile loading, policy checks, simulated boot readiness, and release documentation scaffolding. Gaps fall into three tiers: **documentation mirror** (addressed this pass), **lab validation** (not started), and **production release** (blocked on hardware maturity).

---

## Gap matrix

| Gap ID | Area | Current state | Required for hardware-compatible claim | Owner | Priority |
|--------|------|---------------|----------------------------------------|-------|----------|
| GAP-001 | Physical boot | Simulated via `hardware_boot_readiness.py` | Boot logs on reference hardware per SKU | OS + HW integration | **P0** |
| GAP-002 | Driver / HLK | Not run | Windows HLK or equivalent driver certification evidence | OS + HW | **P0** |
| GAP-003 | Battery runtime | Profile targets only (`school_day`, etc.) | DVT battery test reports per `dvt/DVT_BATTERY_TEST_PLAN.md` | HW lab | **P0** |
| GAP-004 | Thermal throttle | Policy YAML + `hardware_thermal_policy.py` | DVT thermal logs per `dvt/DVT_THERMAL_TEST_PLAN.md` | HW lab | **P0** |
| GAP-005 | Display/input on silicon | Profile assumptions | DVT display/input plan execution | HW lab | **P0** |
| GAP-006 | Dual-screen shell (DS-XL) | Software workflow documented | Hardware dual-display bring-up | OS + HW | **P1** |
| GAP-007 | Steam / gaming path (Handheld) | Mock route in OS | Partner or lab gaming compatibility evidence | OS + partners | **P1** |
| GAP-008 | Arena marshal controls (Wearables) | Policy warnings only | Field pilot with venue safety rules | OS + ops | **P1** |
| GAP-009 | Mechanical fit | Placeholder STLs + bbox JSON | Mechanical correctness gate pass | HW mechanical | **P1** |
| GAP-010 | Regulatory | `certification/CERTIFICATION_STATUS.md`: not certified | FCC/CE/UKCA/IEC evidence | HW compliance | **P0** |
| GAP-011 | DVT completion | `dvt/DVT_STATUS.md`: not complete | Executed DVT with signoff | HW engineering | **P0** |
| GAP-012 | PVT / production | `pvt/PVT_STATUS.md`, `production_release/PRODUCTION_RELEASE_STATUS.md` | PVT pass + production release gate | HW + CM | **P0** |
| GAP-013 | Device ID mapping | `student_14` vs `student_14_5` | Canonical ID table + detection plan | OS + HW | **P2** |
| GAP-014 | Secure update flash layout | Hardware contract: "Flash layout TBD — EVT-1 docs only" | Locked partition map + recovery images | OS + HW | **P1** |
| GAP-015 | Dock / USB-C DP Alt Mode | Profile flags `true` | Electrical + display lab validation | HW lab | **P1** |

---

## Per device class gaps

### Student 14.5 (`student_14_5`)

| Dimension | Profile says | Hardware evidence | Gap |
|-----------|--------------|-------------------|-----|
| Display 14.5″ 1920×1200 | yes | placeholder mechanical only | No panel validation |
| WSL / dev path | yes | N/A (OS feature) | Not run on reference laptop-class hardware |
| Webcam / mic privacy | placeholder shutter | schematic skeleton | No sensor bring-up |
| School-day battery | target flag | no DVT battery report | **open** |
| Passive fanless thermal | policy class | no thermal logs | **open** |

### Handheld Hybrid (`handheld_hybrid`)

| Dimension | Profile says | Hardware evidence | Gap |
|-----------|--------------|-------------------|-----|
| Controller-first input | yes | factory test script placeholder | No HID mapping on device |
| TV / dock mode | yes | USB-C DP in contract | Not electrically validated |
| Active cooling | policy class | no thermal plan execution | **open** |
| Steam path | yes | not in hardware repo | Partner evidence missing |

### DS-XL Coder (`ds_xl_coder`)

| Dimension | Profile says | Hardware evidence | Gap |
|-----------|--------------|-------------------|-----|
| Dual-screen touch | yes | dual-screen form in JSON | OS shell not proven on hardware |
| Deploy source role | yes | deploy contract in OS repo | Transport not validated on real link |
| 1 TB NVMe min | profile | no storage qualification | **open** |

### Wearables / Arena Set (`wearables_arena_set`)

| Dimension | Profile says | Hardware evidence | Gap |
|-----------|--------------|-------------------|-----|
| Future-target placeholder | yes | smallest bbox placeholder | Lowest maturity SKU |
| Marshal controls | policy warnings | no field pilot | Arena safety not validated |
| WSL blocked | engine blockers | N/A | By design — document only |
| eMMC 64 GB | profile | no flash qualification | **open** |

---

## Hardware repo maturity vs OS readiness

| Hardware gate | Hardware repo status | OS can claim |
|---------------|---------------------|--------------|
| Mechanical correctness | planning / placeholder STLs | profile mirror only |
| DVT | not complete | simulated checks only |
| PVT | not complete | none |
| Certification | not certified | none |
| Production release | not released | none |

Source paths:

- `../gunnchos-hardware-industrial-design/mechanical_correctness/MECHANICAL_CORRECTNESS_STATUS.md`
- `../gunnchos-hardware-industrial-design/dvt/DVT_STATUS.md`
- `../gunnchos-hardware-industrial-design/pvt/PVT_STATUS.md`
- `../gunnchos-hardware-industrial-design/certification/CERTIFICATION_STATUS.md`
- `../gunnchos-hardware-industrial-design/production_release/PRODUCTION_RELEASE_STATUS.md`

---

## Recommended closure order

1. Lock canonical device ID map (`student_14` ↔ `student_14_5`) in `boot_readiness/HARDWARE_PROFILE_DETECTION_PLAN.md`.
2. Execute DVT display/input/battery/thermal plans on first reference hardware for Student 14.5.
3. Attach lab logs to `hardware_release/HARDWARE_COMPATIBILITY_EVIDENCE_MATRIX.md`.
4. Run OS boot readiness on same hardware; compare simulated vs actual detection.
5. Expand to Handheld and DS-XL after Student 14.5 reference path is proven.
6. Defer wearables/arena hardware-compatible claim until mechanical and safety pilots exist.

---

## Claim boundary

Closing documentation gaps does **not** close validation gaps. All current hardware compatibility remains **simulated/profile-based** until lab and field evidence is linked.

---

## Related documents

- [HARDWARE_REPO_COMPATIBILITY_AUDIT.md](HARDWARE_REPO_COMPATIBILITY_AUDIT.md)
- [../hardware_compat/HARDWARE_VALIDATION_STATUS.md](../hardware_compat/HARDWARE_VALIDATION_STATUS.md)
- [../hardware_release/HARDWARE_COMPATIBILITY_STATUS.md](../hardware_release/HARDWARE_COMPATIBILITY_STATUS.md)
