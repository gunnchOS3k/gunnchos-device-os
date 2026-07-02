# GunnchOS Phase 0 — Prototype OS Shell

Phase 0 delivers a **clickable GunnchOS experience** that proves the product vision before hardware images ship.

## Deliverables

| Deliverable | Status | Location |
|-------------|--------|----------|
| Linux base image (container) | ✅ | `os_build/linux_desktop/` |
| GunnchOS launcher | ✅ | `apps/launcher_mock/src/shell/` |
| Browser/PWA hub | ✅ | `shell/BrowserPwaHub.tsx` |
| Game Mode mock | ✅ | `shell/GameMode.tsx` |
| Settings mock | ✅ | `shell/SettingsPanel.tsx` |
| File manager mock | ✅ | `shell/FileManagerMock.tsx` |
| App icons | ✅ | `components/AppIcon.tsx` (SVG) |
| First boot flow | ✅ | `shell/FirstBootFlow.tsx` |
| Student profile setup | ✅ | `data/studentProfile.ts` + localStorage |

## Run locally

```bash
cd apps/launcher_mock
npm install
npm run dev
# → http://localhost:5173
```

First launch shows the onboarding wizard. Complete it to enter **Campus Mode**.

## Run Linux prototype

```bash
docker compose -f os_build/linux_desktop/docker-compose.yml up --build
# → http://localhost:8080
```

## System modes

### Campus Mode
Main desktop for school, coding, creativity, and productivity:
- App launcher with dock
- Browser & PWA hub (Google Workspace, D2L, NotebookLM, GitHub, VS Code Web, etc.)
- File manager (Downloads, Offline Documents, Code Projects)
- AI study assistant panel
- Settings (profile, display, privacy, network, system)

### Game Mode
Console-style interface:
- Full-screen game library
- Three first-party games: Anime Aggressors, Foot Racing Game, Earth Species Artifact Adventure
- Performance profiles (battery / balanced / performance)
- Controller-first navigation mock
- FPS overlay toggle

## Dev views

The launcher includes hidden dev views for legacy research tooling:
- **gunnchos** — Phase 0 shell (default)
- **fleet** — 7GC fleet deployment mock
- **user-focused** — Persona/journey preset explorer

Switch via the dev bar when in fleet/user-focused views, or "Dev: Fleet view" button in Campus Mode.

## What's next (Phase 1)

- Wire Python `onboarding_wizard.py` to React shell via local API
- Real browser iframe/shell for PWA targets
- Local notes, PDF reader, camera/recorder mocks
- Google Workspace offline fallback
- Persist profile to filesystem (not just localStorage)

## Requirements source

Product requirements: `GUNNCHOS_REQUIREMENTS_v0.1.md` (repo root)
