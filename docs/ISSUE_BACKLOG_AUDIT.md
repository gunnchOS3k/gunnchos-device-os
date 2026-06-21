# Issue Backlog Audit — Operational OS Pass

**Branch:** `issue-backlog-operational-os-pass`  
**Scope:** Open issues #1–#10 and #12  
**Status:** device OS alpha · not a finished shipping OS image  
**Audit date:** 2026-06-21

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## Purpose

This audit inventories what exists on branch `issue-backlog-operational-os-pass` versus what each backlog issue requires for closure. It maps Python modules, YAML config, launcher mock routes, documentation, demos, tests, and README coverage.

---

## Issue summary

| Issue | Title (operational) | Primary modules | Config |
|-------|-------------------|-----------------|--------|
| #1 | Device classes & hardware/software contract | `device_classes.py` | `config/device_classes.yaml` |
| #2 | Launcher mock architecture & component map | `apps/launcher_mock/` | — |
| #3 | DS-XL deploy contract & local deploy security | `deploy_contract.py` | `config/deploy_targets.yaml` |
| #5 | OS modes (School, Developer, Research Measurement, …) | `mode_manager.py`, `mode_policy.py` | `config/modes.yaml` |
| #7 | Guardian controls & youth safety | `guardian_controls.py`, `guardian_policy.py` | `config/guardian_defaults.yaml` |
| #8 | Privacy, consent, telemetry, security event log | `privacy_security_model.py`, `consent_policy.py`, `security_event_log.py` | `config/privacy_defaults.yaml` |
| #9 | Deploy flow diagrams (Wi-Fi, USB-C, offline bundle) | `deploy_contract.py` | `config/deploy_targets.yaml` |
| #10 | Edge-IO integration contract | `edge_io_contract.py` | `config/edge_io_contract.yaml` |
| #12 | WAIKE integration (tutor cards, student tasks, pathways) | `waike_integration.py` | `config/waike_tutor_cards.yaml`, `config/waike_student_tasks.yaml` |

Issues #4, #6, and #11 are out of scope for this pass.

---

## Existing vs missing artifacts (this pass)

### Issue #1 — Device classes

| Artifact | Status |
|----------|--------|
| `gunnchos_device_os/device_classes.py` | **Exists** |
| `config/device_classes.yaml` (4 classes) | **Exists** |
| `docs/DEVICE_CLASSES.md` | **Created this pass** |
| `docs/HARDWARE_SOFTWARE_DEVICE_CLASS_CONTRACT.md` | **Created this pass** |
| `tests/test_device_classes.py` | **Exists** |
| Bootable HAL / ACPI battery signals | **Missing** (future hardware) |

### Issue #2 — Launcher mock

| Artifact | Status |
|----------|--------|
| `apps/launcher_mock/` (fleet + user-focused views) | **Exists** |
| `docs/LAUNCHER_MOCK_ARCHITECTURE.md` | **Created this pass** |
| `docs/LAUNCHER_NAVIGATION_MODEL.md` | **Created this pass** |
| `docs/LAUNCHER_ACCESSIBILITY_CONTRACT.md` | **Created this pass** |
| `docs/LAUNCHER_COMPONENT_MAP.md` | **Created this pass** |
| `apps/launcher_mock/README.md` | **Created this pass** |
| `apps/launcher_mock/src/user-focused/README.md` | **Created this pass** |
| Launcher mock automated UI tests | **Missing** (`npm test` is placeholder) |
| Production shell / installable image | **Missing** |

### Issue #3 — DS-XL deploy

| Artifact | Status |
|----------|--------|
| `gunnchos_device_os/deploy_contract.py` | **Exists** |
| `config/deploy_targets.yaml` | **Exists** |
| `scripts/run_deploy_contract_demo.py` | **Exists** |
| `docs/DS_XL_DEPLOY_CONTRACT.md` | **Created this pass** |
| `docs/LOCAL_DEPLOY_SECURITY_MODEL.md` | **Created this pass** |
| `docs/DEPLOY_PACKAGE_FORMAT.md` | **Created this pass** |
| `docs/DEPLOY_FAILURE_MODES.md` | **Created this pass** |
| `demo/ds_xl_deploy_walkthrough.md` | **Created this pass** |
| Signed bundle verification on device | **Missing** (placeholder) |
| Real Wi-Fi/USB transport | **Missing** (mock API only) |

### Issue #5 — Modes

| Artifact | Status |
|----------|--------|
| `gunnchos_device_os/mode_manager.py` | **Exists** |
| `gunnchos_device_os/mode_policy.py` | **Exists** |
| `config/modes.yaml` (12 modes + transition rules) | **Exists** |
| Mode docs (`MODES_OVERVIEW`, per-mode, matrix, transitions) | **Created this pass** |
| `tests/test_modes.py`, `tests/test_mode_policy.py` | **Exists** |
| Kernel-level mode enforcement | **Missing** |

### Issue #7 — Guardian

| Artifact | Status |
|----------|--------|
| `guardian_controls.py`, `guardian_policy.py` | **Exists** |
| `config/guardian_defaults.yaml` | **Exists** |
| Guardian docs + walkthrough | **Created this pass** |
| `tests/test_guardian_policy.py` | **Exists** |
| Production MDM / COPPA certification | **Missing** (mock only) |

### Issue #8 — Privacy & security

| Artifact | Status |
|----------|--------|
| `privacy_security_model.py`, `consent_policy.py`, `security_event_log.py` | **Exists** |
| `config/privacy_defaults.yaml` | **Exists** |
| Privacy docs (6 files) | **Created this pass** |
| `tests/test_privacy_security_model.py`, `tests/test_consent_policy.py`, `tests/test_security_event_log.py` | **Exists** |
| GDPR/COPPA certification, real export/delete pipeline | **Missing** (placeholders) |

### Issue #9 — Deploy diagrams

| Artifact | Status |
|----------|--------|
| Deploy flow docs (5) | **Created this pass** |
| `diagrams/deploy_flow_*.mmd` (3) | **Created this pass** |
| `tests/test_deploy_docs.py` | **Exists** |
| Interactive pairing UI | **Missing** (QR placeholder in config) |

### Issue #10 — Edge-IO

| Artifact | Status |
|----------|--------|
| `edge_io_contract.py`, `config/edge_io_contract.yaml` | **Exists** |
| Edge-IO docs + walkthrough | **Created this pass** |
| `scripts/run_edge_io_contract_demo.py` | **Exists** |
| `tests/test_edge_io_contract.py` | **Exists** |
| Live edge-io-measurement-node session | **Missing** (cross-repo integration) |

### Issue #12 — WAIKE

| Artifact | Status |
|----------|--------|
| `waike_integration.py` | **Exists** |
| `config/waike_tutor_cards.yaml`, `config/waike_student_tasks.yaml` | **Exists** |
| WAIKE docs (6) + walkthrough | **Created this pass** |
| `scripts/run_waike_integration_demo.py` | **Exists** |
| `tests/test_waike_integration.py` | **Exists** |
| Full waike-research-ops LMS sync | **Missing** |

---

## Test coverage gaps

| Area | Covered today | Gap |
|------|---------------|-----|
| Device classes | Field validation, 4 classes | No cross-check vs hardware ID repo |
| Deploy contract | Targets, transport safety, failure messages | No end-to-end signed bundle test |
| Modes | 12 modes, school/developer/research policies | No launcher UI ↔ YAML sync test |
| Mode transitions | Child/guardian, school/admin blocks | No integration with real profile store |
| Guardian | Age bands, app/mode approval | No audit log persistence test |
| Privacy | Child telemetry off, consent states, redaction | No export/delete integration test |
| Edge-IO | Consent gate, export formats | No live node handshake test |
| WAIKE | YAML schema, 6+ tutor cards | No gunnchAI3k tutor API test |
| Launcher mock | Doc existence (`test_launcher_architecture_docs.py`) | No React component tests |
| Deploy diagrams | File existence + min length (`test_deploy_docs.py`) | No rendered diagram CI |

**Recommended next tests (not blocking doc closure):**

1. `test_launcher_mode_sync.py` — assert `deviceProfiles.ts` modes ⊆ `config/modes.yaml`
2. `test_deploy_walkthrough_steps.py` — parse demo markdown for required consent steps
3. Vitest smoke for `UserFocusedView` tab navigation and `aria-current`

---

## README audit

| Section | Present | Accurate for alpha? | Notes |
|---------|---------|---------------------|-------|
| Alpha disclaimer | Yes (lines 5–7, 209–211) | Yes | Matches `product/CLAIM_BOUNDARY.md` |
| User-focused entry links | Yes | Yes | Points to existing UX docs |
| Modes one-liner | Yes | Partial | Should link to new `docs/MODES_OVERVIEW.md` |
| Integrations (Edge-IO, 7GC, WAIke) | Yes | Yes | Cross-repo links correct |
| Quick start (`pytest`, launcher mock) | Yes | Yes | Commands valid |
| Evidence / smoke vs real validation | Yes | Yes | Honest limitations |
| EVT-1 OS alpha block | Yes | Yes | References demo JSON |
| Issue backlog doc index | **Missing before this pass** | — | Add links after merge |

**README updates recommended (follow-up PR):**

- Add "Operational OS pass docs" table linking issues #1, #2, #3, #5, #7, #8, #9, #10, #12 to new `docs/` files
- Link `docs/ISSUE_CLOSURE_MATRIX.md` for contributors closing backlog items

---

## Claim boundary (required)

All artifacts in this pass describe **contracts, mocks, and config-driven policy** — not production fleet management, secure boot, or certified youth safety. See:

- `product/CLAIM_BOUNDARY.md`
- `docs/WHAT_IS_REAL_TODAY.md`
- `docs/WHAT_WOULD_MAKE_THIS_FINAL.md`

---

## Validation commands

```bash
pip install -r requirements.txt
PYTHONPATH=. pytest -q \
  tests/test_device_classes.py \
  tests/test_deploy_contract.py \
  tests/test_modes.py \
  tests/test_mode_policy.py \
  tests/test_guardian_policy.py \
  tests/test_privacy_security_model.py \
  tests/test_consent_policy.py \
  tests/test_security_event_log.py \
  tests/test_edge_io_contract.py \
  tests/test_waike_integration.py \
  tests/test_launcher_architecture_docs.py \
  tests/test_deploy_docs.py

python scripts/run_deploy_contract_demo.py
python scripts/run_edge_io_contract_demo.py
python scripts/run_waike_integration_demo.py
python scripts/run_guardian_policy_demo.py
python scripts/run_privacy_security_demo.py
python scripts/run_mode_policy_demo.py
```

---

## Related documents

- [ISSUE_CLOSURE_MATRIX.md](ISSUE_CLOSURE_MATRIX.md) — per-issue closure checklist
- [product/CLAIM_BOUNDARY.md](../product/CLAIM_BOUNDARY.md) — allowed vs forbidden language
