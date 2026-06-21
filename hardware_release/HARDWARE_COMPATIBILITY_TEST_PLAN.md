# Hardware Compatibility Test Plan

**Status:** plan documented · **execution not started on hardware**

Aligns with hardware repo DVT plans under `../gunnchos-hardware-industrial-design/dvt/`.

---

## Test phases

| Phase | Environment | Goal |
|-------|-------------|------|
| P0 | CI / simulation | Profile load, engine rules, simulated boot |
| P1 | OS lab (reference HW) | Boot, display, input, storage |
| P2 | Hardware DVT lab | Battery, thermal, electrical per hardware plans |
| P3 | Field pilot | Guardian, arena, school fleet scenarios |
| P4 | Release regression | Pre-release matrix on golden units |

**Current phase: P0 only**

---

## P0 — Simulation (automated)

| Test ID | Description | Pass criteria |
|---------|-------------|---------------|
| HC-T0-001 | Load all device profiles | YAML parses; required fields present |
| HC-T0-002 | Compatibility engine mode matrix | Known blockers fire for wearables |
| HC-T0-003 | Simulated boot all SKUs | `boot_ready_simulated: true` |
| HC-T0-004 | Policy modules import | no import errors |
| HC-T0-005 | Evidence tag present | `real_hardware_validation_required` in results |

Run via existing pytest / CI as applicable.

---

## P1 — Reference hardware (manual + logs)

| Test ID | SKU | Description | HW DVT alignment |
|---------|-----|-------------|------------------|
| HC-T1-001 | Student 14.5 | Cold boot to shell | DVT SW/HW integration |
| HC-T1-002 | Student 14.5 | Panel 1920×1200 | DVT display/input |
| HC-T1-003 | Student 14.5 | Keyboard + touch + stylus | DVT display/input |
| HC-T1-004 | Student 14.5 | Dock external display | DVT display/input |
| HC-T1-005 | Handheld | Controller mapping | DVT display/input |
| HC-T1-006 | Handheld | TV dock mode | DVT display/input |
| HC-T1-007 | DS-XL | Dual-screen init | DVT display/input |
| HC-T1-008 | DS-XL | Deploy to Student (Wi-Fi/USB) | DVT SW/HW integration |
| HC-T1-009 | Wearables | Marshal-gated Play | field policy |
| HC-T1-010 | All | Safe mode entry | boot_readiness recovery |
| HC-T1-011 | All | USB recovery boot | recovery artifacts |

---

## P2 — Lab DVT (hardware repo owned)

Execute hardware repo plans; OS consumes reports:

- `dvt/DVT_BATTERY_TEST_PLAN.md`
- `dvt/DVT_THERMAL_TEST_PLAN.md`
- `dvt/DVT_ELECTRICAL_TEST_PLAN.md`
- `dvt/DVT_MECHANICAL_TEST_PLAN.md`
- `dvt/DVT_ENVIRONMENTAL_TEST_PLAN.md`
- `dvt/DVT_DROP_AND_DURABILITY_TEST_PLAN.md`

OS-specific additions:

| Test ID | Description |
|---------|-------------|
| HC-T2-001 | Mode switch under thermal load |
| HC-T2-002 | Offline boot after network disable |
| HC-T2-003 | Guardian policy on Student reference |
| HC-T2-004 | WSL dry-run on Student (if image ready) |

---

## P3 — Field pilot

See [HARDWARE_PILOT_TEST_PLAN.md](HARDWARE_PILOT_TEST_PLAN.md).

---

## P4 — Release regression

Before R3 signoff, re-run P1 subset on **three units per SKU** from PVT build.

---

## Pass/fail recording

Update [HARDWARE_COMPATIBILITY_EVIDENCE_MATRIX.md](HARDWARE_COMPATIBILITY_EVIDENCE_MATRIX.md) per test with:

- Test ID
- Date / operator
- Artifact path
- Pass/fail
- Blocking defects filed

---

## Claim boundary

This test plan does not imply any P1+ test has been executed. P0 simulation is the only active phase today.
