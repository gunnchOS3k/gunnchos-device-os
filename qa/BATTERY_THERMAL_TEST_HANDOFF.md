# Battery and Thermal Test Handoff

**Version:** 1.0 · **Owner:** Hardware program → OS QA

---

## Purpose

Define handoff from hardware/industrial design to OS QA for battery runtime and thermal behavior on Handheld Hybrid and docked Student 14.5. Required before GA on portable SKUs.

---

## Setup

| Item | Spec |
|------|------|
| Devices | Handheld Hybrid EVT reference; Student 14.5 on battery |
| Ambient | 25°C ±3°C |
| Display | 50% brightness default unless noted |
| Network | Wi-Fi on unless offline test |
| Load scripts | OS-provided gaming/dev workload scripts (TBD) |

---

## Personas covered

- Gamer — sustained Play mode
- High school student — mixed school + media
- CS student — Developer mode compile loop

---

## Device classes covered

- Handheld Hybrid (primary)
- Student 14.5 on battery (secondary)
- DS-XL Coder — battery spot check
- Wearables/Arena — out of scope until hardware exists

---

## Test steps (hardware team executes; OS QA witnesses)

1. Full charge; record design capacity vs reported
2. Idle drain 1 hr — launcher home
3. Play mode 2 hr — mock or real game
4. School mode 2 hr — document + browser mock
5. Thermal imaging at 30/60/120 min (handheld)
6. Throttle events from performance governor log
7. Low-battery warning UX verification
8. Docked play thermal (handheld + dock)

---

## Expected results

- Runtime within hardware PRD targets (document actual)
- Skin temp within design limits
- OS shows low-battery policy before hard shutdown
- No silent shutdown without warning

---

## Evidence to collect

- Battery log CSV
- Thermal photos / sensor log
- OS event log excerpts
- Signed handoff memo: HW lead + QA lead

---

## Pass/fail criteria

**Pass:** Results within PRD or documented waiver; UX warnings verified.

**Fail:** Safety limit exceeded; missing low-battery UX; >15% runtime regression vs PRD without waiver.

---

## Known limitations

- EVT hardware may differ from DVT/PVT
- Workload scripts may be mock until games integrated
- OS alpha may not read real ACPI battery — mark "blocked on HAL"

---

## Handoff checklist

- [ ] Reference devices available
- [ ] OS build with performance governor
- [ ] Logging enabled
- [ ] QA report template assigned
