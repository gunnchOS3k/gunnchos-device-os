# QA Package

**Status:** test plans documented · **hardware UAT not yet executed**

Manual and automated test plans for shippable gunnchOS. All plans require evidence collection before RC/GA claims.

## Documents

| Plan | Scope |
|------|-------|
| [QA_MASTER_TEST_PLAN.md](QA_MASTER_TEST_PLAN.md) | Master index |
| [USER_ACCEPTANCE_TEST_PLAN.md](USER_ACCEPTANCE_TEST_PLAN.md) | Persona UAT |
| [ACCESSIBILITY_TEST_PLAN.md](ACCESSIBILITY_TEST_PLAN.md) | A11y validation track |
| [PERFORMANCE_TEST_PLAN.md](PERFORMANCE_TEST_PLAN.md) | Performance baselines |
| [BATTERY_THERMAL_TEST_HANDOFF.md](BATTERY_THERMAL_TEST_HANDOFF.md) | HW team handoff |
| [OFFLINE_MODE_TEST_PLAN.md](OFFLINE_MODE_TEST_PLAN.md) | Offline scenarios |
| [SCHOOL_LIBRARY_TEST_PLAN.md](SCHOOL_LIBRARY_TEST_PLAN.md) | Shared devices |
| [GUARDIAN_CONTROLS_TEST_PLAN.md](GUARDIAN_CONTROLS_TEST_PLAN.md) | Youth safety |
| [DEV_WORKSTATION_TEST_PLAN.md](DEV_WORKSTATION_TEST_PLAN.md) | Developer path |
| [CREATOR_WORKSTATION_TEST_PLAN.md](CREATOR_WORKSTATION_TEST_PLAN.md) | Creator workspaces |
| [GAMING_MEDIA_TEST_PLAN.md](GAMING_MEDIA_TEST_PLAN.md) | Play/media routes |
| [REGRESSION_TEST_PLAN.md](REGRESSION_TEST_PLAN.md) | Automated regression |
| [TEST_REPORT_TEMPLATE.md](TEST_REPORT_TEMPLATE.md) | Report template |

## Validation

```bash
python scripts/validate_qa_package.py
```

## Claim boundary

Passing pytest and documented plans does **not** claim GA release or accessibility certified on hardware.
