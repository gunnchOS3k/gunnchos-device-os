# Release Candidate Backlog

**20 issue-ready tasks** · Target gate: `release_candidate` · **not shipping yet**

Copy each task into GitHub Issues with labels: `release-candidate`, `shippable-os`.

---

## Task 1 — Fix CI demo generation dependency

**Title:** Fix CI demo output generation for clean checkout

**Description:** Ensure `results/user_focused_os_demo_output.json` and related demo outputs are generated in CI before pytest. Update `tests/test_user_focused_os_demo.py` to self-generate if missing via subprocess.

**Acceptance criteria:**
- CI runs all demo scripts before pytest
- Clean checkout passes `pytest -q tests/`
- No reliance on untracked local artifacts

**Labels:** `ci`, `P0`, `release-candidate`

---

## Task 2 — Create installer bundle

**Title:** Create Windows-first gunnchOS OS-layer installer prototype

**Description:** Build pipeline producing unsigned/dev-signed installer bundling launcher, configs, and policy engine. Document install/uninstall steps.

**Acceptance criteria:**
- Installer artifact produced in CI on tag
- Documented in `release_artifacts/INSTALLER_STATUS.md` with honest status
- Install smoke test log (reference PC)

**Labels:** `release-engineering`, `P0`, `release-candidate`

---

## Task 3 — Create version manifest

**Title:** Generate version manifest from build pipeline

**Description:** Implement generation from [../release_artifacts/VERSION_MANIFEST_TEMPLATE.json](../release_artifacts/VERSION_MANIFEST_TEMPLATE.json).

**Acceptance criteria:**
- `manifest.json` emitted per build with semver + build_id
- Validated against JSON schema in CI

**Labels:** `release-engineering`, `P0`

---

## Task 4 — Add checksums

**Title:** Add checksum generation and verification

**Description:** Emit `checksums.sha256` for all release artifacts; installer verifies before apply.

**Acceptance criteria:**
- Checksum file in release bundle
- CI job verifies hashes match
- Update `CHECKSUMS_STATUS.md`

**Labels:** `release-engineering`, `P0`

---

## Task 5 — Add SBOM generation

**Title:** Add SBOM generation for release bundles

**Description:** SPDX JSON covering Python + npm dependencies per [../release_artifacts/SBOM_REQUIREMENTS.md](../release_artifacts/SBOM_REQUIREMENTS.md).

**Acceptance criteria:**
- `sbom.spdx.json` in release output
- Security review diff script (initial)

**Labels:** `security`, `P0`, `release-candidate`

---

## Task 6 — Add release notes generation

**Title:** Automate release notes from template

**Description:** Populate [../release_artifacts/RELEASE_NOTES_TEMPLATE.md](../release_artifacts/RELEASE_NOTES_TEMPLATE.md) from changelog + manifest.

**Acceptance criteria:**
- `RELEASE_NOTES.md` generated on tag
- Includes claim boundary section

**Labels:** `release-engineering`, `P1`

---

## Task 7 — Add signed update manifest placeholder

**Title:** Signed update manifest placeholder in build pipeline

**Description:** Dev-signed manifest structure per [../release_artifacts/SIGNING_REQUIREMENTS.md](../release_artifacts/SIGNING_REQUIREMENTS.md).

**Acceptance criteria:**
- Manifest signature field populated (dev key)
- Updater mock verifies signature in test

**Labels:** `security`, `P0`

---

## Task 8 — Add rollback/recovery demo

**Title:** Rollback and recovery demo with logged output

**Description:** Script demonstrating failed update → rollback → recovery menu paths; log to `results/rollback_recovery_demo_output.json`.

**Acceptance criteria:**
- Demo script + pytest validation
- Recovery artifact requirements cross-linked

**Labels:** `os-core`, `P0`

---

## Task 9 — Add hardware compatibility matrix validation

**Title:** Automated hardware compatibility matrix validation

**Description:** Test that `device_classes.yaml` fields satisfy [../requirements/HARDWARE_COMPATIBILITY_REQUIREMENTS.md](../requirements/HARDWARE_COMPATIBILITY_REQUIREMENTS.md) schema; cross-check deploy targets.

**Acceptance criteria:**
- `tests/test_hardware_compatibility_matrix.py`
- Validator script optional
- Draft compatibility report template filled from YAML

**Labels:** `hardware`, `P1`, `release-candidate`

---

## Task 10 — Add accessibility report generator

**Title:** Accessibility report generator from test checklist

**Description:** Generate markdown report from [../qa/ACCESSIBILITY_TEST_PLAN.md](../qa/ACCESSIBILITY_TEST_PLAN.md) checklist JSON — not certification.

**Acceptance criteria:**
- `scripts/generate_accessibility_report.py`
- Output template in `qa/reports/`
- Report states validation track — not certified

**Labels:** `accessibility`, `P1`

---

## Task 11 — Add security review checklist

**Title:** Complete security review checklist for RC

**Description:** Checklist covering threat model, SBOM, signing, secrets, dependency CVEs.

**Acceptance criteria:**
- `security/RC_SECURITY_REVIEW_CHECKLIST.md` complete
- All items marked pass/waive/N-A with owner

**Labels:** `security`, `P0`

---

## Task 12 — Add user acceptance test scripts

**Title:** User acceptance test helper scripts

**Description:** Scripts scaffolding [../qa/USER_ACCEPTANCE_TEST_PLAN.md](../qa/USER_ACCEPTANCE_TEST_PLAN.md) persona matrix and report export.

**Acceptance criteria:**
- `scripts/run_uat_scaffold.py`
- Validates 11 persona names against demo JSON

**Labels:** `qa`, `P1`

---

## Task 13 — Add launcher e2e tests

**Title:** Launcher mock e2e tests (Vitest/Playwright)

**Description:** Smoke tests for user-focused tab navigation, `aria-current`, mode display.

**Acceptance criteria:**
- `npm test` in `apps/launcher_mock/` runs ≥3 smoke tests
- CI job step added

**Labels:** `launcher`, `P0`, `release-candidate`

---

## Task 14 — Add app pack install/launch tests

**Title:** App pack install and launch policy tests

**Description:** pytest covering app registry schema, install/launch/uninstall policy per [../requirements/APP_ECOSYSTEM_REQUIREMENTS.md](../requirements/APP_ECOSYSTEM_REQUIREMENTS.md).

**Acceptance criteria:**
- `tests/test_app_pack_policy.py`
- Trust tier enforcement cases

**Labels:** `os-core`, `P1`

---

## Task 15 — Add school/library shared-device session cleanup tests

**Title:** Shared-device session cleanup automated tests

**Description:** Tests for profile isolation and ephemeral data clearing per [../qa/SCHOOL_LIBRARY_TEST_PLAN.md](../qa/SCHOOL_LIBRARY_TEST_PLAN.md).

**Acceptance criteria:**
- `tests/test_shared_device_session.py`
- Simulated multi-profile sequence

**Labels:** `school`, `P1`

---

## Task 16 — Add guardian approval flow tests

**Title:** Guardian approval flow integration tests

**Description:** End-to-end approval/deny/audit scenarios beyond unit policy tests.

**Acceptance criteria:**
- `tests/test_guardian_approval_flow.py`
- Covers install, mode, telemetry opt-in

**Labels:** `guardian`, `P1`

---

## Task 17 — Add Edge-IO session consent tests

**Title:** Edge-IO session consent integration tests

**Description:** Session lifecycle with consent gate, export formats, failure modes.

**Acceptance criteria:**
- Extended `tests/test_edge_io_contract.py` or new integration file
- Demo output includes session consent scenario

**Labels:** `edge-io`, `P1`

---

## Task 18 — Add WAIKE offline lesson sync tests

**Title:** WAIKE offline lesson sync tests

**Description:** Cache tutor cards + student tasks; offline launch; sync placeholder when online.

**Acceptance criteria:**
- `tests/test_waike_offline_sync.py`
- Uses YAML fixtures only (no live LMS)

**Labels:** `waike`, `P2`

---

## Task 19 — Add WSL developer setup dry-run tests

**Title:** WSL developer setup dry-run validation

**Description:** Validate `scripts/install_wsl_dev_environment.ps1` structure and documented steps; Windows CI agent dry-run when available.

**Acceptance criteria:**
- `tests/test_wsl_setup_dry_run.py`
- Script parsing / step coverage report

**Labels:** `developer`, `P2`

---

## Task 20 — Add Steam/media route dry-run tests

**Title:** Steam and media route dry-run tests

**Description:** Verify mock launch paths log correctly; guardian/school blocks enforced.

**Acceptance criteria:**
- `tests/test_steam_media_dry_run.py`
- Output JSON field validation

**Labels:** `gaming`, `P2`

---

## Completion definition for RC backlog

All P0 tasks (1–8, 11, 13) closed + RC sign-off → eligible for **release candidate** gate review. GA requires additional work in [GA_RELEASE_BACKLOG.md](GA_RELEASE_BACKLOG.md).
