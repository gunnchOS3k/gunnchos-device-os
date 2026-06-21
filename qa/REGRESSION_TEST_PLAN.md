# Regression Test Plan

**Version:** 1.0

---

## Purpose

Automated regression suite preventing OS alpha regressions and gating RC/GA releases. Primary execution: pytest + CI validators.

---

## Setup

```bash
pip install -r requirements.txt
python scripts/run_user_focused_os_demo.py
python scripts/run_mode_policy_demo.py
python scripts/run_deploy_contract_demo.py
python scripts/run_privacy_security_demo.py
python scripts/run_edge_io_contract_demo.py
python scripts/run_waike_integration_demo.py
python scripts/validate_user_focused_os.py
python scripts/validate_issue_closure.py
python scripts/validate_shippable_requirements.py
python scripts/validate_release_gates.py
python scripts/validate_release_artifacts.py
python scripts/validate_qa_package.py
PYTHONPATH=.:src pytest -q tests/
```

---

## Personas covered

Indirect via demo JSON and policy tests: all 11 user-focused scenarios validated by `test_user_focused_os_demo.py`.

---

## Device classes covered

- `tests/test_device_classes.py` — all 4 YAML classes
- Deploy targets — student_14_5, handheld_hybrid, ds_xl, wearables placeholder

---

## Test steps

| Suite | Path | Focus |
|-------|------|-------|
| Device classes | `tests/test_device_classes.py` | Schema, 4 classes |
| Modes | `tests/test_modes.py`, `test_mode_policy.py` | 12 modes, transitions |
| Deploy | `tests/test_deploy_contract.py` | Targets, transports |
| Guardian | `tests/test_guardian_policy.py` | Age bands, approval |
| Privacy | `tests/test_privacy_security_model.py`, consent, security log | Child defaults |
| Edge-IO | `tests/test_edge_io_contract.py` | Consent gate |
| WAIKE | `tests/test_waike_integration.py` | YAML schema, cards |
| Launcher docs | `tests/test_launcher_architecture_docs.py` | Doc existence |
| Deploy docs | `tests/test_deploy_docs.py` | Diagrams |
| Shippable package | `tests/test_shippable_requirements.py`, release gates, artifacts, qa | Package integrity |
| User-focused demo | `tests/test_user_focused_os_demo.py` | 11 scenarios |

---

## Expected results

- All tests pass on clean checkout after demo generation
- Validators print OK
- No forbidden false claims in requirements docs

---

## Evidence to collect

- CI run URL
- pytest summary artifact
- Validator stdout captured in CI log

---

## Pass/fail criteria

**Pass:** 100% pytest pass; all validators OK; 0 P0 open.

**Fail:** Any test fail; validator fail; demo output missing.

---

## Known limitations

- No launcher React component tests yet (RC backlog #13)
- No hardware-in-loop automation
- Mock integrations only for Steam/WSL/live Edge-IO

---

## RC expansion

Add: launcher e2e, app pack tests, session cleanup, guardian approval automation per RC backlog.
