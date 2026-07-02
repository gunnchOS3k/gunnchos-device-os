# Python ↔ React Bridge

Phase 1 introduces a minimal **export bridge** so the React launcher shell reads policy and app data from the existing Python/YAML layer instead of hardcoding everything.

## Architecture

```
config/modes.yaml          ─┐
gunnchos_device_os/        ─┼─► scripts/export_launcher_contract.py
  app_registry.py          ─┤         │
  media_apps.py            ─┘         ▼
                          apps/launcher_mock/src/generated/launcherContract.json
                                              │
                                              ▼
                          apps/launcher_mock/src/hooks/useLauncherContract.ts
```

## Export command

```bash
python3 scripts/export_launcher_contract.py
# or
make export-launcher-contract
```

`make build-launcher` runs the export automatically before `npm run build`.

## Contract contents

- `apps` — full app registry including media metadata
- `media_apps` — structured media service definitions
- `modes` — allowed/blocked apps per mode
- `claim_boundary` — DRM/certification honesty flags
- `policy_samples` — sanity-check booleans for CI

## React usage

```typescript
import { useLauncherContract, getMediaApps } from '../hooks/useLauncherContract'

const contract = useLauncherContract()
const mediaApps = getMediaApps()
```

## Phase 1 limitations

- **Static JSON** — not a live API; re-export after Python/YAML changes
- **No write path** — profile/onboarding still uses localStorage in React
- **No FastAPI** — deferred to Phase 2 if needed

## Future (Phase 2+)

- Optional local FastAPI service for live policy evaluation
- Profile sync from `onboarding_wizard.py`
- CI step enforcing contract freshness
