# gunnchos-device-os

**GunnchOS** — an education-first, creator-first, gamer-first operating system for affordable handheld devices.

> Phase 0 shell merged (PR #30). Phase 1 adds Media Mode and policy bridge. Not yet a bootable shipping OS image.

## Run GunnchOS

```bash
python3 scripts/export_launcher_contract.py
cd apps/launcher_mock && npm install && npm run dev
# → http://localhost:5173 — onboarding → Campus → Media Mode → Game Mode
```

Tests:

```bash
cd apps/launcher_mock && npm test
pytest tests/test_media_policy.py -q
```

Linux container prototype:

```bash
docker compose -f os_build/linux_desktop/docker-compose.yml up --build
# → http://localhost:8080
```

See [docs/PHASE0.md](docs/PHASE0.md), [docs/PHASE1.md](docs/PHASE1.md), [docs/PHASE2_PLAN.md](docs/PHASE2_PLAN.md), [GUNNCHOS_REQUIREMENTS_v0.1.md](GUNNCHOS_REQUIREMENTS_v0.1.md).

## Operational status (honest)

**GunnchOS is not a finished shipping OS.** Phase 0–1 provide a runnable shell prototype with policy framework and tests.

| Category | Real today | Prototype today | Mock today | Missing for beta | Missing for GA |
|----------|------------|-----------------|------------|------------------|----------------|
| **Shell & modes** | First boot, Campus/Game/Media UI, Vitest smoke | Mode switching, dock | App launches, game launch | Policy enforcement in shell | Full a11y on hardware |
| **Policy** | Python modes, media metadata, contract export | Guardian/school in config | Shell enforcement | CI auto-export | Kernel enforcement |
| **Productivity** | PWA list, contract apps | — | File manager, browser frame, settings | Real FS, notes, PDF, webview | Cloud sync |
| **Media** | DRM disclaimers, Media Mode UI | YouTube external link | Netflix/Hulu playback, local player | Local video, webview YouTube | Service certification |
| **Games** | Game metadata, Game Mode UI | — | Launch (mock) | One real game build | Three vertical slices |
| **Platform** | Docker prototype, SBOM scripts | HW compat (simulated) | Updater, rollback | Installable image | Production OTA |

Full matrix: [docs/FULL_OPERATIONAL_GAP_MATRIX.md](docs/FULL_OPERATIONAL_GAP_MATRIX.md) · Mocks: [docs/MOCK_RETIREMENT_PLAN.md](docs/MOCK_RETIREMENT_PLAN.md) · Beta gate: [docs/BETA_RELEASE_GATE.md](docs/BETA_RELEASE_GATE.md)

---

A user-focused operating system alpha and launcher/customization framework for gunnchOS modular student devices.

## Start here

- [docs/USER_FOCUSED_OS_ARCHITECTURE.md](docs/USER_FOCUSED_OS_ARCHITECTURE.md)
- [docs/DEVICE_CLASSES.md](docs/DEVICE_CLASSES.md)
- [docs/MODES_OVERVIEW.md](docs/MODES_OVERVIEW.md)
- [docs/LAUNCHER_MOCK_ARCHITECTURE.md](docs/LAUNCHER_MOCK_ARCHITECTURE.md)
- [docs/DS_XL_DEPLOY_CONTRACT.md](docs/DS_XL_DEPLOY_CONTRACT.md)
- [docs/PRIVACY_SECURITY_MODEL.md](docs/PRIVACY_SECURITY_MODEL.md)
- [docs/WAIKE_INTEGRATION.md](docs/WAIKE_INTEGRATION.md)
- [docs/ISSUE_CLOSURE_MATRIX.md](docs/ISSUE_CLOSURE_MATRIX.md)
- [hardware_compat/HARDWARE_COMPATIBILITY_CONTRACT.md](hardware_compat/HARDWARE_COMPATIBILITY_CONTRACT.md)
- [docs/HARDWARE_OS_TRACEABILITY.md](docs/HARDWARE_OS_TRACEABILITY.md)

## Run demos

```bash
python scripts/run_user_focused_os_demo.py
python scripts/run_mode_policy_demo.py
python scripts/run_deploy_contract_demo.py
python scripts/run_privacy_security_demo.py
python scripts/run_edge_io_contract_demo.py
python scripts/run_waike_integration_demo.py
python scripts/run_guardian_policy_demo.py
python scripts/run_hardware_compatibility_demo.py
python scripts/run_hardware_boot_readiness_demo.py
python scripts/run_device_specific_mode_demo.py
python scripts/run_firmware_probe_demo.py
python scripts/run_firmware_compatibility_demo.py
python scripts/run_capsule_update_client_demo.py
```

## Validations

```bash
python scripts/validate_user_focused_os.py
python scripts/validate_issue_closure.py
python scripts/validate_shippable_requirements.py
python scripts/validate_release_gates.py
python scripts/validate_release_artifacts.py
python scripts/validate_qa_package.py
python scripts/validate_hardware_manifests.py
python scripts/validate_hardware_compatibility.py
python scripts/validate_hardware_release_evidence.py
python scripts/validate_firmware_compat.py
python scripts/validate_cross_repo_firmware_bridge.py
pytest -q
```

## Firmware compatibility track

gunnchos-device-os mirrors firmware manifests and interface contracts from [gunnchos-hardware-industrial-design](https://github.com/gunnchOS3k/gunnchos-hardware-industrial-design) and validates host-side firmware compatibility in a harness.

Start here:
- [firmware_compat/README.md](firmware_compat/README.md)
- [firmware_compat/CLAIM_BOUNDARY.md](firmware_compat/CLAIM_BOUNDARY.md)
- [cross_repo_firmware_bridge/README.md](cross_repo_firmware_bridge/README.md)
- [results/REAL_FIRMWARE_COMPATIBILITY_IMPLEMENTATION_REPORT.md](results/REAL_FIRMWARE_COMPATIBILITY_IMPLEMENTATION_REPORT.md)

Current status:
- Firmware compatibility harness exists (host/emulated probes and contract sync).
- Capsule update client is simulation-only (never flashes real firmware).
- Implemented in firmware compatibility harness / OS firmware probe / cross-repo contract sync. Physical-board validation remains pending.

## Hardware compatibility track

gunnchos-device-os mirrors device families from [gunnchos-hardware-industrial-design](https://github.com/gunnchOS3k/gunnchos-hardware-industrial-design) and validates profile-based OS compatibility.

Start here:
- [hardware_compat/README.md](hardware_compat/README.md)
- [hardware_compat/HARDWARE_CLAIM_BOUNDARY.md](hardware_compat/HARDWARE_CLAIM_BOUNDARY.md)
- [docs/HARDWARE_REPO_INTEGRATION.md](docs/HARDWARE_REPO_INTEGRATION.md)
- [hardware_release/HARDWARE_COMPATIBILITY_EVIDENCE_MATRIX.md](hardware_release/HARDWARE_COMPATIBILITY_EVIDENCE_MATRIX.md)

Current status:
- Hardware-aware OS alpha exists (simulated detection).
- Four device profiles: Student 14.5, Handheld Hybrid, DS-XL Coder, Wearables/Arena Set.
- Physical hardware boot and HLK-style validation **not proven**.

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
