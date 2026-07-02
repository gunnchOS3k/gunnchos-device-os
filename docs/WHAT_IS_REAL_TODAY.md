# What Is Real Today

**Last updated:** Phase 2C conflict resolution (2026-07-02). Full audit: [FULL_OPERATIONAL_GAP_MATRIX.md](FULL_OPERATIONAL_GAP_MATRIX.md)

## Real (validated in repo)

- `gunnchos_device_os` Python policy package
- `config/modes.yaml` mode policies
- `gunnchos_device_os/media_apps.py` structured media metadata
- `scripts/export_launcher_contract.py` + `scripts/check_launcher_contract_fresh.py`
- `apps/launcher_mock` React shell (Phase 0–2A)
- Vitest frontend tests (`npm test`) — 40+ tests
- Media + launcher contract pytest
- **File Manager v1** — browser localStorage workspace (`FileManager.tsx`)
- **Notes app v1** — browser localStorage (`NotesApp.tsx`)
- **Settings persistence** — display/privacy/network subset (`settingsStore.ts`)
- **Browser/PWA open behavior** — `appLaunchService.ts` opens real URLs in new tab (`BrowserPwaHub.tsx`)
- **Local Media Player v1** — HTML5 browser-backed local file playback (`LocalMediaPlayer.tsx`)
  - Local file picker for audio/video (MP4, WebM, MP3, etc.)
  - Recent media metadata in localStorage only
  - **Does not** persist media blobs across refresh
  - **Does not** handle DRM streaming
  - **Not** a production OS media library
- **Game launch adapter** — `gameLaunchService.ts` + readiness checklist (Phase 2D)
- **Anime Aggressors web slice** — playable vertical slice at `games/anime-aggressors-web/` (Phase 2E)
- Linux container prototype (`os_build/linux_desktop/`)
- **Image prototype track** — kiosk packaging scripts (`os_build/image_prototype/`) — not bootable OS
- CI runs contract export, pytest, frontend build/test
- Beta gate dashboard (`beta_gate/beta_gate_status.yaml`)

## Prototype / mock (honest labels)

- Browser/PWA hub — external tab route prototype; no embedded browser shell
- Settings — system stats (storage/RAM/Wi-Fi) still mock labels
- Media Mode streaming — browser route prototypes; Netflix/Hulu DRM disclaimers only
- Local media — browser file picker prototype; metadata-only persistence
- AI assistant panel — UI shell only
- Game launches — adapter wired; Foot Racing / Earth Species not connected
- Network/audio diagnostics — mock indicators
- Shell policy enforcement — partial (see Phase 3)

## Not real (not claimed)

- Production filesystem / encrypted storage
- Google Drive sync
- Bootable OS image on target hardware
- Kernel, secure boot, TPM validation
- Official Netflix/Hulu/Disney+ certification
- DRM circumvention or guaranteed Widevine
- Production MDM/fleet deployment
- Real browser CDM integration
- Accessibility or privacy legal certification

## Release readiness

| Stage | Met? |
|-------|------|
| Alpha (shell + policy) | **Yes** |
| Beta | **No** — see [BETA_RELEASE_GATE.md](BETA_RELEASE_GATE.md) |
| RC / GA / Production | **No** |

Smoke: `make e2e` · Launcher: `cd apps/launcher_mock && npm run dev`
