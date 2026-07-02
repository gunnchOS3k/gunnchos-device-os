# What Is Real Today

**Last updated:** Phase 2 planning (2026-07-02). Full audit: [FULL_OPERATIONAL_GAP_MATRIX.md](FULL_OPERATIONAL_GAP_MATRIX.md)

## Real (validated in repo)

- `gunnchos_device_os` Python policy package
- `config/modes.yaml` mode policies
- `gunnchos_device_os/media_apps.py` structured media metadata
- `scripts/export_launcher_contract.py` + `scripts/check_launcher_contract_fresh.py`
- `apps/launcher_mock` React shell (Phase 0–2A)
- Vitest frontend tests (`npm test`) — 25+ tests
- Media + launcher contract pytest
- **File Manager v1** — browser localStorage workspace (`FileManager.tsx`)
- **Notes app v1** — browser localStorage (`NotesApp.tsx`)
- **Settings persistence** — display/privacy/network subset (`settingsStore.ts`)
- Linux container prototype (`os_build/linux_desktop/`)
- CI runs contract export, pytest, frontend build/test
- **Browser/PWA open behavior** — `appLaunchService.ts` opens real URLs in new tab (`BrowserPwaHub.tsx`)

## Prototype / mock (honest labels)

- Browser/PWA hub — external tab route prototype; no embedded browser shell
- Settings — system stats (storage/RAM/Wi-Fi) still mock labels
- Media Mode playback — browser route prototypes, not certified streaming
- Local media player — placeholder
- AI assistant panel — UI shell only
- Game launches — **launch adapter prototype** (`gameLaunchService.ts`); web builds pending Phase 2E
- Network/audio diagnostics — mock indicators

## Not real (not claimed)

- Bootable OS image on hardware
- Kernel, secure boot, TPM validation
- Official Netflix/Hulu/Disney+ certification
- DRM circumvention or guaranteed Widevine
- Production MDM/fleet deployment
- Real browser CDM integration

## Release readiness

| Stage | Met? |
|-------|------|
| Alpha (shell + policy) | **Yes** |
| Beta | **No** — see [BETA_RELEASE_GATE.md](BETA_RELEASE_GATE.md) |
| RC / GA / Production | **No** |

Smoke: `make e2e` · Launcher: `cd apps/launcher_mock && npm run dev`
