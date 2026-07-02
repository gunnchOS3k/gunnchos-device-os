# GunnchOS Phase 1 — Media Mode & Policy Bridge

Phase 1 builds on the Phase 0 shell (PR #30, merged) by adding **Streaming Media Mode**, a **Python→React policy bridge**, and **real frontend/Python tests**.

## What Phase 1 adds

| Deliverable | Status | Location |
|-------------|--------|----------|
| Media Mode UI | Prototype | `apps/launcher_mock/src/shell/MediaMode.tsx` |
| Media hub cards | Prototype | `apps/launcher_mock/src/shell/MediaHub.tsx` |
| Playback diagnostics | Prototype | `apps/launcher_mock/src/shell/MediaDiagnostics.tsx` |
| Media app metadata (Python) | Real | `gunnchos_device_os/media_apps.py` |
| Policy bridge export | Real | `scripts/export_launcher_contract.py` |
| React contract consumer | Real | `apps/launcher_mock/src/hooks/useLauncherContract.ts` |
| Vitest frontend tests | Real | `apps/launcher_mock/src/shell/shell.test.tsx` |
| Media policy pytest | Real | `tests/test_media_policy.py` |

## Run

```bash
# Export policy contract (required before build/test)
python3 scripts/export_launcher_contract.py

cd apps/launcher_mock
npm install
npm run build
npm test

# Python tests
pytest tests/test_media_policy.py -q
```

## OS modes (product vision)

- **Campus Mode** — school, productivity, coding shortcuts
- **Media Mode** — full-screen streaming/media experience (Phase 1)
- **Game Mode** — first-party games, performance priority
- Developer/Lab, Studio/Creative, Offline/Library, Guardian/School, Admin/Recovery — policy layers (Phase 1+)

## Claim boundary

Phase 1 does **not** claim official Netflix/Hulu/Disney+ certification or DRM circumvention. Routes are **browser route prototypes** with honest DRM/HDCP disclaimers.

See [MEDIA_MODE.md](MEDIA_MODE.md), [STREAMING_MEDIA_REQUIREMENTS.md](STREAMING_MEDIA_REQUIREMENTS.md), [PYTHON_REACT_BRIDGE.md](PYTHON_REACT_BRIDGE.md).
