# EVT-1 OS Acceptance Criteria (PRD §5.3)

**Target:** EVT-1 alpha — **not** finished shipping OS.

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Bootable/installable image path documented | documented | [BOOT_AND_DEMO_PATH.md](BOOT_AND_DEMO_PATH.md#evt-1-alpha-path) |
| Launcher app runs | prototype | `gunnchos_device_os/launcher.py` + `apps/launcher_mock/` |
| Mode switching works | proven (model) | `mode_manager.py` · pytest |
| Steam launches from Play Mode | mock | `steam_integration.py` · demo JSON |
| VS Code/dev tools from Developer Mode | mock | `launcher.py` · `wsl_dev_tools.py` |
| WSL install script for Student 14.5" | documented | `scripts/install_wsl_dev_environment.ps1` |
| Telemetry consent flow | proven (mock) | `telemetry_consent.py` · pytest |
| Updater mock | proven | `updater.py` |
| Rollback design | proven | `rollback.py` |
| App policies testable | proven | `policy_engine.py` · pytest |
| CI runs tests | yes | `.github/workflows/ci.yml` |
| Demo walkthrough | yes | [demo/device_os_evt1_walkthrough.md](../demo/device_os_evt1_walkthrough.md) |
| Demo JSON output | yes | `results/device_os_evt1_demo_output.json` |
| Parental/school controls | prototype | `parental_controls.py` |
| Device health dashboard | mock | `device_health.py` |
| Input mapper | prototype | `input_mapper.py` |
| WAIKE/gunnchAI3k integration | mock | `waike_integration.py` · `gunnchai_integration.py` |
| Coder mode (DS-XL) | prototype | `mode_manager.py` Coder mode |

## Run validation

```bash
pip install -r requirements.txt
PYTHONPATH=.:src pytest -q
PYTHONPATH=. python3 scripts/run_device_os_demo.py
```

## Not claimed

Finished OS · certified secure boot · production MDM · Steam/media licensing · installable signed image
