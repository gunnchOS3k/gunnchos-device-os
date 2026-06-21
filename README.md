# gunnchos-device-os

A user-focused operating system alpha and launcher/customization framework for gunnchOS modular student devices.

> This repository is a device OS alpha and launcher/customization framework. It is not a finished shipping OS image.

## Start here

- [docs/USER_FOCUSED_OS_ARCHITECTURE.md](docs/USER_FOCUSED_OS_ARCHITECTURE.md)
- [docs/DEVICE_CLASSES.md](docs/DEVICE_CLASSES.md)
- [docs/MODES_OVERVIEW.md](docs/MODES_OVERVIEW.md)
- [docs/LAUNCHER_MOCK_ARCHITECTURE.md](docs/LAUNCHER_MOCK_ARCHITECTURE.md)
- [docs/DS_XL_DEPLOY_CONTRACT.md](docs/DS_XL_DEPLOY_CONTRACT.md)
- [docs/PRIVACY_SECURITY_MODEL.md](docs/PRIVACY_SECURITY_MODEL.md)
- [docs/WAIKE_INTEGRATION.md](docs/WAIKE_INTEGRATION.md)
- [docs/ISSUE_CLOSURE_MATRIX.md](docs/ISSUE_CLOSURE_MATRIX.md)

## Run demos

```bash
python scripts/run_user_focused_os_demo.py
python scripts/run_mode_policy_demo.py
python scripts/run_deploy_contract_demo.py
python scripts/run_privacy_security_demo.py
python scripts/run_edge_io_contract_demo.py
python scripts/run_waike_integration_demo.py
python scripts/run_guardian_policy_demo.py
```

## Validations

```bash
python scripts/validate_user_focused_os.py
python scripts/validate_issue_closure.py
python scripts/validate_shippable_requirements.py
python scripts/validate_release_gates.py
python scripts/validate_release_artifacts.py
python scripts/validate_qa_package.py
pytest -q
```

## Shippable OS track

This repo now includes a shippable OS requirements package and release-gate model.

Start here:
- [requirements/SHIPPABLE_OS_REQUIREMENTS.md](requirements/SHIPPABLE_OS_REQUIREMENTS.md)
- [release_gates/RELEASE_GATE_MATRIX.md](release_gates/RELEASE_GATE_MATRIX.md)
- [release_artifacts/ARTIFACT_MANIFEST_REQUIRED.md](release_artifacts/ARTIFACT_MANIFEST_REQUIRED.md)
- [qa/QA_MASTER_TEST_PLAN.md](qa/QA_MASTER_TEST_PLAN.md)
- [roadmap/SHIPPABLE_OS_ROADMAP.md](roadmap/SHIPPABLE_OS_ROADMAP.md)

Current status:
- User-focused OS alpha exists.
- Issue backlog OS alpha exists.
- Shippable requirements exist.
- Installable image is not yet proven.
- GA release is not claimed.
- Finished shipping OS is not claimed.

CI order (clean checkout):
1. Generate demo outputs
2. Run validators
3. Run pytest

See [docs/CI_FAILURE_ANALYSIS.md](docs/CI_FAILURE_ANALYSIS.md).

## Launcher mock

```bash
cd apps/launcher_mock && npm install && npm run dev
```

Open **Your device (scooter → spaceship)** for the user-focused customization route, or use the fleet launcher view for campus/device modes.

## Integrations

- [edge-io-measurement-node](https://github.com/gunnchOS3k/edge-io-measurement-node)
- [7gc-digital-twin](https://github.com/gunnchOS3k/7gc-digital-twin)
- [waike-research-ops](https://github.com/gunnchOS3k/waike-research-ops)

## Claim boundary

This is a **device OS alpha** — a validated config-driven framework with launcher mock, mode policies, deploy contracts, guardian stubs, and privacy models. It does **not** claim:

- Finished shipping OS image
- Production MDM or parental-control enforcement
- Certified accessibility compliance
- Complete secure boot
- Official Steam or media app certification

See [product/CLAIM_BOUNDARY.md](product/CLAIM_BOUNDARY.md) and [docs/WHAT_IS_REAL_TODAY.md](docs/WHAT_IS_REAL_TODAY.md).

## Historical note

gunnchAI3k tutor integration is referenced as a learning companion bridge within this device OS layer — not as the identity of this repository.
