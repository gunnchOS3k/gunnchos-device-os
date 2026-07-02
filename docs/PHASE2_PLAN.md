# GunnchOS Phase 2 Plan

**Focus:** Replace the most important mocks with working systems. **Not** a claim that GunnchOS is finished.

**Branch target:** Implementation PRs after this planning PR merges.

**Last updated:** 2026-07-02

---

## Phase 2 principles

1. **No new mock surfaces** — extend real behavior or document gaps
2. **Retire mocks** per [MOCK_RETIREMENT_PLAN.md](MOCK_RETIREMENT_PLAN.md)
3. **Preserve** Python policy layer and launcher contract pattern
4. **Honest claims** — beta checklist in [BETA_RELEASE_GATE.md](BETA_RELEASE_GATE.md)

---

## Recommended Phase 2 scope (implementation)

### Track A — Policy & CI (P0)

| Task | Deliverable | Retires |
|------|-------------|---------|
| Automate contract export in CI | `Makefile` + `.github/workflows/ci.yml` run `export_launcher_contract.py` before launcher build | Manual export step |
| Unified test gate | CI job: pytest + `npm test` in one required check | Partial coverage gap |
| Shell policy enforcement | Read `launcherContract.json` modes; block disallowed app launches in UI | Guardian/school stubs (partial) |

### Track B — Campus essentials (P0)

| Task | Deliverable | Retires |
|------|-------------|---------|
| Real file manager v1 | FS-backed list/create/delete in Downloads scope | `FileManagerMock.tsx` |
| Real notes app v1 | IndexedDB or FS markdown notes | Missing notes |
| Real browser open behavior | `window.open` or webview delegate with URL from contract | Browser hub mock frame |
| Settings persistence | Write profile + settings to localStorage → FS JSON | Settings mock values |

### Track C — Media (P0)

| Task | Deliverable | Retires |
|------|-------------|---------|
| Local media player | `<video>` + file picker for non-DRM files | Local media placeholder |
| YouTube browser route | Open YouTube in new tab/webview with disclaimer | Media playback mock (partial) |

### Track D — Game Mode (P0)

| Task | Deliverable | Retires |
|------|-------------|---------|
| Game launch adapter | `launchGame(id)` → URL or local path config | Game launch mock |
| Wire Anime Aggressors | Link to web build (e.g. GitHub Pages artifact) | First-party mock launch |

### Track E — Deferred to Phase 2.5 / 3 (P1)

- PDF reader baseline
- AI assistant backend
- Camera/audio/screen recording
- Developer tools container
- Google Drive offline integration
- Installer / bootable image prototype (may parallel Track A as P0)

---

## Phase 2 success criteria

Phase 2 is **complete** when:

- [ ] `export_launcher_contract.py` runs in CI before every launcher build
- [ ] `pytest` + `npm test` both required in CI
- [ ] File manager reads/writes real files in a scoped directory
- [ ] Notes app creates and persists at least one note
- [ ] Browser/PWA opens real URLs (not mock frame only)
- [ ] Local media plays a user-selected non-DRM file
- [ ] Game Mode launches at least one real game build
- [ ] School mode hides/blocks Netflix/Hulu in UI (policy wired)
- [ ] [BETA_RELEASE_GATE.md](BETA_RELEASE_GATE.md) checklist reviewed — beta **not claimed** until gate passes

---

## Out of scope for Phase 2

- Official Netflix/Hulu certification
- DRM circumvention or Widevine integration
- Bootable ARM64 image (plan in parallel; not required to close Phase 2 doc track)
- Android app layer
- Field pilot enrollment
- Production signing pipeline

---

## Recommended implementation PR order

1. **PR-A:** CI contract export + unified test gate
2. **PR-B:** Real file manager + notes v1
3. **PR-C:** Browser open behavior + local media player
4. **PR-D:** Game launch adapter + Anime Aggressors wire-up
5. **PR-E:** Shell policy enforcement (school/guardian/offline)

---

## Related

- [FULL_OPERATIONAL_GAP_MATRIX.md](FULL_OPERATIONAL_GAP_MATRIX.md)
- [MOCK_RETIREMENT_PLAN.md](MOCK_RETIREMENT_PLAN.md)
- [BETA_RELEASE_GATE.md](BETA_RELEASE_GATE.md)
- [issues/](../issues/) — operational gap issues
