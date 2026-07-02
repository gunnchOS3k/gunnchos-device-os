# What Is Real Today

## Real (validated in repo)

- `gunnchos_device_os` Python policy package
- `config/modes.yaml` mode policies
- `gunnchos_device_os/media_apps.py` structured media metadata
- `scripts/export_launcher_contract.py` policy export
- `apps/launcher_mock` React shell (Phase 0 + Phase 1)
- Vitest frontend smoke tests (`npm test`)
- Media policy pytest (`tests/test_media_policy.py`)
- Linux container prototype (`os_build/linux_desktop/`)

## Prototype / mock (honest labels)

- Browser/PWA hub — mock frames, no live iframe
- File manager — mock folders
- Settings — mock toggles
- Media Mode playback — browser route prototypes, not certified streaming
- Local media player — placeholder
- AI assistant panel — UI shell only
- Game launches — mock; first-party games not wired to engines
- Network/audio diagnostics — mock indicators

## Not real (not claimed)

- Bootable OS image on hardware
- Kernel, secure boot, TPM validation
- Official Netflix/Hulu/Disney+ certification
- DRM circumvention or guaranteed Widevine
- Production MDM/fleet deployment
- Real browser CDM integration

Smoke: `make e2e` · Launcher: `cd apps/launcher_mock && npm run dev`
