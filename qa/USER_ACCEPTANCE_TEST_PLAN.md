# User Acceptance Test Plan

**Version:** 1.0 · **Execution status:** not yet run on RC build

---

## Purpose

Validate end-user journeys for all user-focused demo personas against launcher/OS-layer behavior. Required before RC and GA sign-off.

---

## Setup

- Install target build (or launcher mock for alpha partial run)
- Reset test profiles
- Load persona checklist from `results/user_focused_os_demo_output.json`
- Network: online + one offline scenario

---

## Personas covered

| # | Persona | Preset / mode |
|---|---------|---------------|
| 1 | Pre-K learner | Scooter Mode |
| 2 | High school student | Car Mode |
| 3 | Writer | Studio Mode |
| 4 | Musician | Music Studio |
| 5 | Artist | Art Table |
| 6 | Gamer | Arcade Mode |
| 7 | CS student | Workshop Mode |
| 8 | Researcher | Laboratory / Spaceship |
| 9 | Guardian operator | Guardian controls |
| 10 | Offline library user | Library / Offline |
| 11 | Accessibility-first user | Accessibility defaults |

---

## Device classes covered

- Student 14.5 (primary)
- Handheld Hybrid (personas 6, 1)
- DS-XL Coder (personas 7, 8)
- Wearables/Arena (persona 1 optional placeholder)

---

## Test steps

For each persona:

1. Complete first-run wizard (or load preset profile)
2. Verify default app packs visible
3. Verify accessibility defaults applied
4. Execute primary workflow (write, play, code, research, etc.)
5. Attempt one blocked action (guardian/school) — verify plain-language message
6. Switch mode if allowed — verify policy
7. End session (shared device personas: verify cleanup)
8. Record pass/fail + screenshot

---

## Expected results

- Primary action reachable in ≤3 taps/clicks from home
- No dead-end screens
- Preset matches demo JSON scenario names
- Safety/privacy notes visible where defined in demo output
- Shared device: no data visible to next profile

---

## Evidence to collect

- Completed persona matrix spreadsheet
- Screenshots or screen recording (consented)
- Log excerpts (no private content)
- Report filed via [TEST_REPORT_TEMPLATE.md](TEST_REPORT_TEMPLATE.md)

---

## Pass/fail criteria

**Pass:** All 11 personas complete primary workflow; 0 P0 UX failures; guardian blocks understandable.

**Fail:** Any P0 (crash, data leak on shared device, wrong child policy); >2 P1 without waiver.

---

## Known limitations

- Alpha runs may use launcher mock only — mark report "mock-only"
- Steam/real apps not required for alpha partial pass
- Hardware-specific layout issues deferred to compatibility report
