# Phase 2A Acceptance Checklist

## Automated

- [ ] `git checkout` clean on branch
- [ ] `python3 scripts/export_launcher_contract.py`
- [ ] `python3 scripts/check_launcher_contract_fresh.py`
- [ ] `pytest -q` (140+ tests; `pytest.ini` sets pythonpath)
- [ ] `cd apps/launcher_mock && npm run build`
- [ ] `cd apps/launcher_mock && npm test` (25+ tests)
- [ ] `make validate-full` (optional wrapper)

## Manual

- [ ] File Manager: create folder
- [ ] File Manager: create/edit/save text file
- [ ] Refresh browser — file content persists
- [ ] Export/import workspace JSON
- [ ] Notes: create/edit/save note
- [ ] Refresh browser — note persists
- [ ] Campus dock opens Files and Notes
- [ ] Settings toggles persist after refresh
- [ ] Claim boundary visible (prototype storage labels)
- [ ] No false OS filesystem or certification claims

## Retired mocks

- [ ] `FileManagerMock.tsx` removed
- [ ] No default static-only file tree in production path
