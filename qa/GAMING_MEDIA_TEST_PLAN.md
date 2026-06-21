# Gaming and Media Test Plan

**Version:** 1.0 · **Not partner certification**

---

## Purpose

Dry-run validation of Play mode Steam route, controller mapping, media apps, guardian/school blocks, and dock path. **Does not claim** official Steam/media certification.

---

## Setup

- Play mode profile with guardian limits
- School mode profile with Play blocked
- Controller paired (Handheld Hybrid)
- Steam integration mock (`steam_integration.py`)
- Media apps mock

---

## Personas covered

- Gamer (Arcade)
- High school student (school block)
- Guardian operator (time limit)

---

## Device classes covered

- Handheld Hybrid (primary)
- Student 14.5 (Steam + dock)
- DS-XL — media only

---

## Test steps

| ID | Step |
|----|------|
| GM-01 | Launch Steam route from Play mode (dry-run log) |
| GM-02 | Controller navigates Play library mock |
| GM-03 | Performance governor active in Play |
| GM-04 | Guardian time limit — block with message |
| GM-05 | School mode — Play entry hidden/blocked |
| GM-06 | Media app route from Media mode |
| GM-07 | Captions preference honored (stub) |
| GM-08 | External display/dock path (when hardware available) |
| GM-09 | Verify no DRM bypass hooks exist (code review) |

---

## Expected results

- Dry-run produces launch log entry — not real Steam unless installed
- Blocks enforced with plain language
- No DRM circumvention code paths
- Dock mirrors/extends per policy

---

## Evidence to collect

- Steam/media dry-run test output (RC backlog #20)
- Demo JSON steam entry
- Guardian block screenshot
- Code review sign-off on DRM boundary

---

## Pass/fail criteria

**Pass:** GM-01–GM-07 pass; GM-09 code review pass; 0 policy bypass.

**Fail:** Play available in school when blocked; DRM bypass; silent limit enforcement.

---

## Known limitations

- Steam/media routes are mocks until partner integration
- Real game compatibility not tested
- Official certification requires partner documents — not claimed
