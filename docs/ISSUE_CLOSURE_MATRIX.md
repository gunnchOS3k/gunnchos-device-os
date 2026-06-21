# Issue Closure Matrix — Operational OS Pass

**Branch:** `issue-backlog-operational-os-pass`  
**Status:** device OS alpha · documentation and contract closure for issues #1–#10 and #12

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

Use this matrix when opening PRs that close backlog issues. Every closing PR should include `Closes #X` in the description (one issue per PR when possible).

---

## Closure matrix

| Issue | Title | Concrete artifact(s) | Tests / validation | Close status | PR keyword |
|-------|-------|----------------------|-------------------|--------------|------------|
| #1 | Device classes & hardware/software contract | `gunnchos_device_os/device_classes.py`, `config/device_classes.yaml`, `docs/DEVICE_CLASSES.md`, `docs/HARDWARE_SOFTWARE_DEVICE_CLASS_CONTRACT.md` | `pytest tests/test_device_classes.py` | Ready to close on doc merge | `Closes #1` |
| #2 | Launcher mock architecture & accessibility | `apps/launcher_mock/`, `docs/LAUNCHER_MOCK_ARCHITECTURE.md`, `docs/LAUNCHER_NAVIGATION_MODEL.md`, `docs/LAUNCHER_ACCESSIBILITY_CONTRACT.md`, `docs/LAUNCHER_COMPONENT_MAP.md`, `apps/launcher_mock/README.md`, `apps/launcher_mock/src/user-focused/README.md` | `pytest tests/test_launcher_architecture_docs.py`; manual `cd apps/launcher_mock && npm run dev` | Ready to close on doc merge | `Closes #2` |
| #3 | DS-XL deploy contract & local deploy security | `gunnchos_device_os/deploy_contract.py`, `config/deploy_targets.yaml`, `docs/DS_XL_DEPLOY_CONTRACT.md`, `docs/LOCAL_DEPLOY_SECURITY_MODEL.md`, `docs/DEPLOY_PACKAGE_FORMAT.md`, `docs/DEPLOY_FAILURE_MODES.md`, `demo/ds_xl_deploy_walkthrough.md`, `scripts/run_deploy_contract_demo.py` | `pytest tests/test_deploy_contract.py`; `python scripts/run_deploy_contract_demo.py` | Ready to close on doc merge | `Closes #3` |
| #4 | School mode | `config/modes.yaml` (School), `gunnchos_device_os/mode_manager.py`, `docs/SCHOOL_MODE.md`, `docs/MODES_OVERVIEW.md` | `pytest tests/test_modes.py`; `python scripts/run_mode_policy_demo.py` | Ready to close | `Closes #4` |
| #5 | Developer mode | `config/modes.yaml` (Developer), `docs/DEVELOPER_MODE.md`, `gunnchos_device_os/mode_policy.py` | `pytest tests/test_modes.py tests/test_mode_policy.py` | Ready to close | `Closes #5` |
| #6 | Research measurement mode | `config/modes.yaml` (Research Measurement), `gunnchos_device_os/edge_io_contract.py`, `docs/RESEARCH_MEASUREMENT_MODE.md` | `pytest tests/test_modes.py tests/test_edge_io_contract.py`; `python scripts/run_edge_io_contract_demo.py` | Ready to close | `Closes #6` |
| #7 | Guardian controls & youth safety model | `gunnchos_device_os/guardian_controls.py`, `gunnchos_device_os/guardian_policy.py`, `config/guardian_defaults.yaml`, `docs/GUARDIAN_CONTROLS.md`, `docs/YOUTH_SAFETY_MODEL.md`, `docs/GUARDIAN_AUDIT_LOG_MODEL.md`, `docs/GUARDIAN_LIMITATIONS.md`, `demo/guardian_controls_walkthrough.md` | `pytest tests/test_guardian_policy.py`; `python scripts/run_guardian_policy_demo.py` | Ready to close on doc merge | `Closes #7` |
| #8 | Privacy, consent, telemetry, threat model | `gunnchos_device_os/privacy_security_model.py`, `gunnchos_device_os/consent_policy.py`, `gunnchos_device_os/security_event_log.py`, `config/privacy_defaults.yaml`, `docs/PRIVACY_SECURITY_MODEL.md`, `docs/CONSENT_AND_TELEMETRY.md`, `docs/DATA_MINIMIZATION.md`, `docs/THREAT_MODEL.md`, `docs/SECURITY_EVENT_LOG_MODEL.md`, `docs/PRIVACY_SECURITY_LIMITATIONS.md` | `pytest tests/test_privacy_security_model.py tests/test_consent_policy.py tests/test_security_event_log.py`; `python scripts/run_privacy_security_demo.py` | Ready to close on doc merge | `Closes #8` |
| #9 | Deploy flow diagrams (Wi-Fi, USB-C, offline bundle) | `docs/LOCAL_WIFI_USBC_DEPLOY_FLOW.md`, `docs/DEPLOY_FLOW_DIAGRAMS.md`, `docs/DEPLOY_PAIRING_MODEL.md`, `docs/DEPLOY_ROLLBACK_MODEL.md`, `docs/DEPLOY_TROUBLESHOOTING.md`, `diagrams/deploy_flow_local_wifi.mmd`, `diagrams/deploy_flow_usbc.mmd`, `diagrams/deploy_flow_offline_bundle.mmd` | `pytest tests/test_deploy_docs.py` | Ready to close on doc merge | `Closes #9` |
| #10 | Edge-IO integration contract | `gunnchos_device_os/edge_io_contract.py`, `config/edge_io_contract.yaml`, `docs/EDGE_IO_INTEGRATION_CONTRACT.md`, `docs/EDGE_IO_DATA_CONTRACT.md`, `docs/EDGE_IO_PRIVACY_SAFETY.md`, `docs/EDGE_IO_FAILURE_MODES.md`, `demo/edge_io_integration_walkthrough.md` | `pytest tests/test_edge_io_contract.py`; `python scripts/run_edge_io_contract_demo.py` | Ready to close on doc merge | `Closes #10` |
| #12 | WAIKE integration (tutor cards, tasks, instructor guide) | `gunnchos_device_os/waike_integration.py`, `config/waike_tutor_cards.yaml`, `config/waike_student_tasks.yaml`, `docs/WAIKE_INTEGRATION.md`, `docs/WAIKE_TUTOR_CARDS.md`, `docs/WAIKE_STUDENT_TASKS.md`, `docs/WAIKE_DEVICE_PATHWAYS.md`, `docs/WAIKE_INSTRUCTOR_GUIDE.md`, `docs/WAIKE_ASSESSMENT_AND_REFLECTION.md`, `demo/waike_device_os_walkthrough.md` | `pytest tests/test_waike_integration.py`; `python scripts/run_waike_integration_demo.py` | Ready to close on doc merge | `Closes #12` |

---

## PR template snippet

```markdown
## Summary
- Adds operational OS pass documentation for issue #X
- References existing Python modules and YAML config (alpha contracts)

## Claim boundary
This is a device OS alpha — not a finished shipping OS image.

## Test plan
- [ ] pytest (issue-specific tests listed in ISSUE_CLOSURE_MATRIX.md)
- [ ] Demo script (if applicable)
- [ ] Manual launcher mock check (issues #2 only)

Closes #X
```

---

## Post-close evidence (future, not required for alpha closure)

| Issue | Next real evidence |
|-------|-------------------|
| #1 | Hardware EVT boot log matching device class assumptions |
| #3, #9 | Signed bundle deploy on physical DS-XL → student device |
| #7 | Production MDM integration + security review |
| #8 | User data export/delete on real profile store |
| #10 | Live session with edge-io-measurement-node |
| #12 | waike-research-ops portfolio sync + instructor pilot |

See `quality/CLAIMS_TO_EVIDENCE_MATRIX.md` and `docs/WHAT_WOULD_MAKE_THIS_FINAL.md`.
