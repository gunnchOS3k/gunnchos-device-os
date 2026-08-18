# Traceability matrix — device OS

| Diagram element | Source path |
|---|---|
| Launcher mock shell | `apps/launcher_mock/src/shell/GunnchOSShell.tsx` |
| Onboarding | `gunnchos_device_os/onboarding_wizard.py`, `apps/launcher_mock/src/shell/FirstBootFlow.tsx` |
| Modes | `gunnchos_device_os/mode_manager.py`, `config/modes.yaml` |
| Device classes | `gunnchos_device_os/device_classes.py`, `config/device_classes.yaml` |
| Runtime profiles | `gunnchos_device_os/runtime_profiles.py` |
| Service-continuity RQ1 | `gunnchos_device_os/service_continuity/` |
| Boot probe | `gunnchos_device_os/boot/probe.py` |
| Boot recovery | `gunnchos_device_os/boot/recovery.py` |
| OTA simulation | `gunnchos_device_os/ota_state_machine.py` |
| Connectivity | `gunnchos_device_os/connectivity_orchestrator.py` |
| Radio capability | `gunnchos_device_os/radio_capability.py` |
| Hardware profile | `gunnchos_device_os/hardware_profile.py`, `hardware_compat/device_profiles/*.yaml` |
| App launch | `gunnchos_device_os/launcher.py`, `gunnchos_device_os/app_runtime.py` |
| gunnchAI bridge | `gunnchos_device_os/gunnchai_integration.py` |
| WAIKE bridge | `gunnchos_device_os/waike_integration.py` |
| Edge-IO contract | `gunnchos_device_os/edge_io_contract.py` |
| Digital image | `gunnchos_device_os/system_image.py`, `os_build/reproducible_system_image/` |
| Linux container prototype | `os_build/linux_desktop/docker-compose.yml` |
| CI | `.github/workflows/ci.yml` |
| Make: tests | `Makefile` `test` |
| Make: launcher | `Makefile` `build-launcher` |
| Make: boot software path | `Makefile` `gate1-boot` |
| Make: digital image | `Makefile` `system-image` |
| Make: QEMU DEV/VM | `Makefile` `bootable-reference` |
| Make: reproduce | `Makefile` `reproduce` |
