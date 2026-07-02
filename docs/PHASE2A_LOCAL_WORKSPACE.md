# GunnchOS Phase 2A — Local Workspace

**Branch:** `phase2a-local-workspace-and-ci-gate`  
**Status:** Implementation (not beta)

Phase 2A replaces key mocks with working browser-backed storage and adds CI protection.

## Real after this PR

| Capability | Location |
|------------|----------|
| CI contract export + freshness check | `.github/workflows/ci.yml`, `scripts/check_launcher_contract_fresh.py` |
| Unified validation script | `scripts/run_full_validation.sh`, `make validate-full` |
| pytest without manual PYTHONPATH | `pytest.ini` (`pythonpath = src .`) |
| Local workspace storage | `apps/launcher_mock/src/services/localWorkspaceStore.ts` |
| File Manager v1 | `apps/launcher_mock/src/shell/FileManager.tsx` |
| Notes app v1 | `apps/launcher_mock/src/shell/NotesApp.tsx` |
| Settings persistence (subset) | `apps/launcher_mock/src/services/settingsStore.ts` |
| Contract includes `files` + `notes` | `scripts/export_launcher_contract.py` |

## Still not real

- Production OS filesystem / encrypted storage
- Google Drive sync
- Bootable OS image
- Native app sandbox
- Full settings backend (Wi-Fi, storage stats remain labeled mock)
- Browser/PWA shell (mock frame)
- Game launch adapter
- Local media player

## Mocks retired

- `FileManagerMock.tsx` — **removed** (replaced by `FileManager.tsx`)
- Static mock file tree — **removed**
- Settings toggles that did not persist — **partially retired** (display/privacy/network subset persists)

## Run

```bash
# Full validation (recommended)
make validate-full

# Or step by step
python3 scripts/export_launcher_contract.py
python3 scripts/check_launcher_contract_fresh.py
pytest -q
cd apps/launcher_mock && npm install && npm run build && npm test
```

## Manual test checklist

1. Complete onboarding → Campus Mode
2. Open **Files** → create folder + text file → edit → save → refresh page → content persists
3. Export workspace JSON → import on fresh profile
4. Open **Notes** → create note → save → refresh → note persists
5. Settings → toggle large text / offline mode → refresh → toggles persist
6. Confirm claim labels: "browser-backed workspace storage prototype"

## Next PRs

1. Browser/PWA open behavior
2. Local media player
3. Game launch adapter
4. Wire Anime Aggressors
5. Bootable image prototype
