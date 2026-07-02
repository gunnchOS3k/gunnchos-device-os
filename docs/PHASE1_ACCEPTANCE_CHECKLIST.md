# Phase 1 Acceptance Checklist

## Setup

- [ ] `git checkout main && git pull` — Phase 0 (PR #30) merged
- [ ] `python3 scripts/export_launcher_contract.py` succeeds
- [ ] `cd apps/launcher_mock && npm install` succeeds
- [ ] `npm run build` succeeds
- [ ] `npm test` succeeds
- [ ] `pytest tests/test_media_policy.py -q` succeeds

## Media Mode UI

- [ ] Media Mode visible from Campus dock
- [ ] YouTube card visible
- [ ] Netflix card visible
- [ ] Hulu card visible
- [ ] Local Media card visible
- [ ] DRM/HDCP disclaimer visible on Netflix/Hulu
- [ ] Restrictions summary visible
- [ ] Exit to Campus works
- [ ] Game Mode still shows three first-party games

## Policy bridge

- [ ] `launcherContract.json` generated and valid JSON
- [ ] React Media Mode reads from contract
- [ ] Media Mode allows YouTube/Netflix/Hulu (policy test)
- [ ] Media Mode blocks Steam/VS Code (policy test)
- [ ] School Mode blocks Netflix/Hulu (policy test)
- [ ] Offline Mode blocks streaming, allows local media (policy test)

## Claim boundary

- [ ] No official streaming certification claimed
- [ ] No DRM circumvention suggested or implemented
- [ ] README and docs updated
- [ ] `docs/WHAT_IS_REAL_TODAY.md` updated

## PR

- [ ] PR targets `main`
- [ ] PR body includes test commands and results
- [ ] PR not auto-merged — Edmund reviews
