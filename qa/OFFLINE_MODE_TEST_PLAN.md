# Offline Mode Test Plan

**Version:** 1.0

---

## Purpose

Verify gunnchOS operates with network disabled: offline bundles, library mode, WAIKE cached tasks, deploy export. Required for RC.

---

## Setup

- Disable Wi-Fi and Ethernet (or use flight mode)
- Pre-cache offline lesson pack and WAIKE tutor cards
- DS-XL as deploy source (optional)
- Shared library profile for session test

---

## Personas covered

- Offline library user
- High school student (offline lesson)
- CS student (offline deploy export)
- Researcher (Edge-IO queue offline)

---

## Device classes covered

- Student 14.5
- DS-XL Coder (deploy source)
- Handheld Hybrid
- Classroom/library shared device

---

## Test steps

| ID | Step |
|----|------|
| O-01 | Enable offline mode; verify indicator |
| O-02 | Launch cached lesson pack |
| O-03 | Open WAIKE tutor card from cache |
| O-04 | Attempt network-only action — verify message |
| O-05 | DS-XL export offline bundle to folder |
| O-06 | Import bundle on target (mock transport OK for alpha) |
| O-07 | 72-hour simulated offline (clock advance or multi-session) |
| O-08 | Re-enable network; verify explicit sync prompt |

---

## Expected results

- Core launcher and cached content usable offline
- No silent network retry storms
- Sync requires user/IT action
- No data loss on offline → online transition (design)

---

## Evidence to collect

- Step log with timestamps
- Offline indicator screenshots
- Deploy bundle hash
- pytest: offline transport allowed in deploy contract

---

## Pass/fail criteria

**Pass:** O-01 through O-06 pass; O-07 pass or documented limitation; 0 P0 data loss.

**Fail:** Crash offline; silent upload; lesson pack unavailable after cache install.

---

## Known limitations

- Live WAIKE LMS sync not tested (cross-repo)
- 72-hour test may be simulated
- Signed offline bundle verification placeholder only
