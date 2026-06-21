# School and Library Test Plan

**Version:** 1.0

---

## Purpose

Validate shared-device behavior, session cleanup, classroom/library modes, and privacy-safe session end per [../requirements/SCHOOL_LIBRARY_REQUIREMENTS.md](../requirements/SCHOOL_LIBRARY_REQUIREMENTS.md).

---

## Setup

- Shared device profile with 3 test users
- School mode policy from `config/modes.yaml`
- Library catalog cache
- Teacher/admin test account

---

## Personas covered

- High school student (classroom)
- Offline library user
- Teacher / IT admin
- Pre-K learner (library station)

---

## Device classes covered

- Student 14.5 (classroom cart)
- Classroom/library shared deploy target
- Handheld Hybrid (library checkout — optional)

---

## Test steps

| ID | Step |
|----|------|
| S-01 | Student A login; open document; end session |
| S-02 | Student B login — verify no A data visible |
| S-03 | Clipboard cleared after session end |
| S-04 | Teacher mode: restrict app set |
| S-05 | Library mode: time limit warning |
| S-06 | Offline lesson in library mode |
| S-07 | Admin wipe between classes |
| S-08 | Security event log entry for session end (no doc content) |

---

## Expected results

- Default: no private data retention between sessions
- School allowlist enforced
- Session end UX clear
- Admin actions audited

---

## Evidence to collect

- Before/after profile screenshots (synthetic data only)
- Audit log export
- pytest school mode policy results
- Automated session cleanup test output (RC backlog #15)

---

## Pass/fail criteria

**Pass:** S-01–S-08 pass; automated cleanup tests green; 0 cross-profile leakage.

**Fail:** Any user A artifact visible to B; missing audit on admin wipe.

---

## Known limitations

- Real classroom fleet not deployed — lab/simulated only
- FERPA compliance is institutional — not claimed here
