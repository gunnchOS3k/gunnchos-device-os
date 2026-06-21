# Guardian Controls Test Plan

**Version:** 1.0

---

## Purpose

Validate guardian approval flows, age bands, audit logging, and child profile restrictions. **Does not claim** production MDM deployed.

---

## Setup

- Child profile (age band from `config/guardian_defaults.yaml`)
- Guardian profile linked
- Test apps: allowed, denied, needs-approval
- Play mode time limit configured

---

## Personas covered

- Guardian operator
- High school student (child profile)
- Pre-K learner (strict band)
- Gamer (Play approval)

---

## Device classes covered

- Student 14.5
- Handheld Hybrid
- DS-XL Coder (child coding with approval)
- All classes with guardian_restrictions in deploy targets

---

## Test steps

| ID | Step |
|----|------|
| G-01 | Child requests app install — guardian approve |
| G-02 | Child requests app install — guardian deny |
| G-03 | Mode transition to Play — approval required |
| G-04 | Play time limit reached — block with message |
| G-05 | Telemetry opt-in — guardian only |
| G-06 | Factory reset — requires guardian PIN |
| G-07 | Audit log records G-01–G-06 (no private content) |
| G-08 | Child sees age-appropriate block explanation |

---

## Expected results

- No install/mode change without approval when policy requires
- Child telemetry off unless guardian opts in
- Audit entries tamper-evident locally
- Plain-language block messages

---

## Evidence to collect

- Guardian policy pytest output
- Demo: `demo/guardian_controls_walkthrough.md`
- Automated approval flow tests (RC backlog #16)
- Audit log sample (redacted)

---

## Pass/fail criteria

**Pass:** All G-01–G-08 pass; pytest guardian suite green; 0 bypass of child policy.

**Fail:** Silent approval; missing audit; child can enable telemetry alone.

---

## Known limitations

- Production MDM not integrated — mock guardian UI
- COPPA certification requires legal review — not claimed
