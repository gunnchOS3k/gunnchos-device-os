# Product Requirements Summary

Full PRD: [gunnchos-hardware-industrial-design/product/PRD_GUNNCHOS_MODULAR_CONSOLE_ECOSYSTEM.md](https://github.com/gunnchOS3k/gunnchos-hardware-industrial-design/blob/main/product/PRD_GUNNCHOS_MODULAR_CONSOLE_ECOSYSTEM.md)

## OS implementation map (PRD §5.2)

| PRD module | Implementation |
|------------|----------------|
| Mode manager | `gunnchos_device_os/mode_manager.py` — School, Developer, **Coder**, Play, Media, Research, Admin |
| App launcher | `gunnchos_device_os/launcher.py` |
| Profile manager | `gunnchos_device_os/profile_manager.py` — incl. community_partner |
| Parental/school controls | `gunnchos_device_os/parental_controls.py` |
| Telemetry consent | `gunnchos_device_os/telemetry_consent.py` |
| Updater / rollback | `updater.py` · `rollback.py` |
| Device health | `device_health.py` |
| HAL | `hardware_abstraction.py` — Student14, HandheldHybrid, DSXLCoder, WearableArenaKit |
| Input mapper | `input_mapper.py` |
| Dock/display | `dock_manager.py` |
| Performance governor | `performance_governor.py` |
| Accessibility | `accessibility.py` |
| WAIKE / gunnchAI3k | `waike_integration.py` · `gunnchai_integration.py` |
| Steam / WSL / media | `steam_integration.py` · `wsl_dev_tools.py` · `media_apps.py` |

## Milestone

**EVT-1 Alpha Device + OS Package** — see PRD §11.

## Claim boundary (PRD §12)

> gunnchOS3k has an EVT-1-ready product requirements package, OS alpha architecture, schematic/PCB documentation skeleton, and manufacturing-readiness roadmap for a modular student console ecosystem.

**Not:** manufacturing-ready · certified · finished OS · shipping device
