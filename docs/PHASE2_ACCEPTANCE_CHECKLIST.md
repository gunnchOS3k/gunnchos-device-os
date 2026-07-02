# Phase 2 Acceptance Checklist (Planning PR)

Use this checklist to verify the operational gap audit PR is complete.

## Documentation

- [x] [FULL_OPERATIONAL_GAP_MATRIX.md](FULL_OPERATIONAL_GAP_MATRIX.md) covers all major requirement areas
- [x] [MOCK_RETIREMENT_PLAN.md](MOCK_RETIREMENT_PLAN.md) lists mocks and replacements
- [x] [PHASE2_PLAN.md](PHASE2_PLAN.md) defines implementation scope
- [x] [BETA_RELEASE_GATE.md](BETA_RELEASE_GATE.md) defines beta criteria
- [x] [issues/](issues/) backlog with P0/P1/P2 issues
- [x] README status table updated
- [x] [WHAT_IS_REAL_TODAY.md](WHAT_IS_REAL_TODAY.md) updated

## Validation (run on PR branch)

- [ ] `python3 scripts/export_launcher_contract.py`
- [ ] `pytest -q` (report failures if any)
- [ ] `cd apps/launcher_mock && npm install && npm run build && npm test`

## Claim boundary

- [x] No new false certification claims
- [x] No DRM circumvention documented or implied
- [x] Beta/GA not claimed

## Next implementation PRs (recommended order)

1. OS-008 + OS-009: CI contract export + full test suite
2. OS-003 + OS-004: Real file manager + notes
3. OS-002 + OS-007: Browser open + local media player
4. OS-005 + OS-006: Game launch adapter + Anime Aggressors
5. OS-001: Bootable image prototype (parallel track)
