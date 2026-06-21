# QA Master Test Plan

**Version:** 1.0 · **Gate coverage:** alpha → production_release

---

## Purpose

Coordinate all gunnchOS testing: automated regression, persona UAT, accessibility validation track, hardware handoffs, and release evidence. Ensures no RC/GA claim without linked reports.

---

## Setup

| Item | Requirement |
|------|-------------|
| Repository | Clean checkout at release tag or `main` |
| Python | 3.11+; `pip install -r requirements.txt` |
| Node | 20+ for launcher mock e2e (when added) |
| Demo outputs | Run all `scripts/run_*_demo.py` before pytest |
| Hardware | Reference devices per SKU (when available) |
| Test data | `config/`, demo JSON, UAT persona checklist |

```bash
python scripts/run_user_focused_os_demo.py
python scripts/run_mode_policy_demo.py
python scripts/run_deploy_contract_demo.py
python scripts/run_privacy_security_demo.py
python scripts/run_edge_io_contract_demo.py
python scripts/run_waike_integration_demo.py
PYTHONPATH=.:src pytest -q tests/
```

---

## Personas covered

| Persona | Primary plan |
|---------|--------------|
| Pre-K learner (Scooter) | USER_ACCEPTANCE_TEST_PLAN |
| High school student (Car) | USER_ACCEPTANCE, SCHOOL_LIBRARY |
| Writer / Studio | USER_ACCEPTANCE, CREATOR |
| Musician / Artist | CREATOR_WORKSTATION |
| Gamer (Arcade) | GAMING_MEDIA |
| CS student (Workshop) | DEV_WORKSTATION |
| Researcher (Laboratory/Spaceship) | USER_ACCEPTANCE, DEV (Edge-IO) |
| Guardian operator | GUARDIAN_CONTROLS |
| Offline library user | OFFLINE_MODE, SCHOOL_LIBRARY |
| Accessibility-first user | ACCESSIBILITY, USER_ACCEPTANCE |
| Teacher / IT admin | SCHOOL_LIBRARY |

---

## Device classes covered

| Class | Plans |
|-------|-------|
| Student 14.5 | All plans; primary GA SKU |
| Handheld Hybrid | GAMING_MEDIA, PERFORMANCE, BATTERY_THERMAL |
| DS-XL Coder | DEV_WORKSTATION, OFFLINE deploy |
| Wearables / Arena | OFFLINE, ACCESSIBILITY (placeholder) |

---

## Test plan index

| ID | Plan | Alpha | RC | GA |
|----|------|-------|----|----|
| M-01 | REGRESSION_TEST_PLAN | Required | Required | Required |
| M-02 | USER_ACCEPTANCE_TEST_PLAN | Partial | Required | Required |
| M-03 | ACCESSIBILITY_TEST_PLAN | Contract | Required | Required |
| M-04 | OFFLINE_MODE_TEST_PLAN | Mock | Required | Required |
| M-05 | GUARDIAN_CONTROLS_TEST_PLAN | pytest | Required | Required |
| M-06 | SCHOOL_LIBRARY_TEST_PLAN | pytest | Required | Required |
| M-07 | DEV_WORKSTATION_TEST_PLAN | Mock | Required | Required |
| M-08 | CREATOR_WORKSTATION_TEST_PLAN | Mock | Partial | Required |
| M-09 | GAMING_MEDIA_TEST_PLAN | Mock | Partial | Required |
| M-10 | PERFORMANCE_TEST_PLAN | — | Baseline | Required |
| M-11 | BATTERY_THERMAL_TEST_HANDOFF | — | Handheld | Required |

---

## Test steps (master workflow)

1. Run automated regression (M-01)
2. Execute domain plans for release scope
3. Record evidence in [TEST_REPORT_TEMPLATE.md](TEST_REPORT_TEMPLATE.md)
4. File reports under `qa/reports/` (create at execution time)
5. Link hashes in [../release_gates/RELEASE_EVIDENCE_MATRIX.md](../release_gates/RELEASE_EVIDENCE_MATRIX.md)
6. Release owner sign-off

---

## Expected results

- All P0 cases pass for target gate
- No undocumented failures
- Claim boundary section completed in report

---

## Evidence to collect

- CI run URL + pytest summary
- Demo JSON hashes
- Manual test logs with screenshots (RC+)
- Hardware test logs (GA+)
- Signed TEST_REPORT per gate

---

## Pass/fail criteria

| Gate | Pass |
|------|------|
| Alpha | pytest green + validators green + demo 11 scenarios |
| RC | Alpha + all RC-required plans executed + 0 open P0 |
| GA | RC + hardware plans + performance/battery baselines |
| Production | GA + fleet rollback drill evidence |

**Fail:** Any P0 failure, missing evidence, or claim beyond gate allowed language.

---

## Known limitations

- Launcher mock ≠ production shell until installer exists
- Steam/media tests are dry-run mocks — not partner certification
- Wearables/Arena hardware may be placeholder only
- Accessibility plan is validation track — **does not claim** certification
- Hardware UAT blocked until reference devices available

---

## Related

- [../release_gates/RELEASE_GATE_MATRIX.md](../release_gates/RELEASE_GATE_MATRIX.md)
- [../requirements/SHIPPABLE_OS_REQUIREMENTS.md](../requirements/SHIPPABLE_OS_REQUIREMENTS.md)
