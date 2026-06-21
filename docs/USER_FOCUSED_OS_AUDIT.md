# User-Focused OS Audit

**Date:** 2026-06-21  
**Scope:** Existing repo inventory, README accuracy, persona coverage gaps  
**Status:** device OS alpha · user-focused OS experience layer · prototype OS package  

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

This audit documents **what exists today**, **what is mock or placeholder**, and **gaps** for artists, writers, musicians, children, guardians, non-technical users, advanced researchers, and accessibility-first users. **No existing work is removed or superseded** — this file complements `product/`, `docs/`, and `gunnchos_device_os/`.

---

## 1. Executive summary

| Area | Exists | Maturity | Primary gap |
|------|--------|----------|-------------|
| Launcher | Yes (Python + mock UI) | Alpha / mock launch | No real app execution on hardware |
| Mode manager | Yes (dual layers) | Data-driven policies | Two mode systems not fully unified |
| App registry | Yes | 15 EVT apps + 11 research launcher apps | Most creative apps are placeholders |
| Policy engine | Yes | Profile + mode rules | No runtime enforcement on device |
| Profile system | Yes (dual) | 8 EVT profiles + 22 personas | Personas not wired to EVT launcher UI |
| Accessibility | Yes (manager + product docs) | Design intent + config | No WCAG audit; switch/voice placeholders |
| Steam / gaming | Yes (docs + integration stub) | Mock | `steam_unavailable` edge case documented |
| WSL / dev | Yes (docs + script + module) | Documented pathway | Not validated on target hardware |
| Media | Yes (browser-route docs) | Policy only | No proprietary app integration |
| Tests | Yes (22 test files) | CI smoke | No dedicated user-focused OS pytest suite |
| CI | Yes (GitHub Actions) | Smoke + EVT demo | User-focused demo not in CI yet |
| README | Yes | Mostly accurate | EVT-1 section stronger than user-focused layer |

---

## 2. Launcher

### What exists

| Artifact | Path | Notes |
|----------|------|-------|
| EVT-1 launcher | `gunnchos_device_os/launcher.py` | `launch_app()`, policy check, mock launch |
| Research launcher package | `src/gunnchos_launcher/` | Bridges, campus modes, QoS, fleet stubs |
| Launcher mock UI | `apps/launcher_mock/` | npm app; build in `make e2e` |
| Demo scripts | `scripts/run_device_os_demo.py`, `scripts/run_user_focused_os_demo.py` | JSON output to `results/` |
| Dock / input | `gunnchos_device_os/dock_manager.py`, `input_mapper.py` | Controller-first for handheld profile |

### Gaps

- Launcher mock does not yet expose all 12 journey presets or 22 personas as first-class routes (README implies customization routes; verify against `apps/launcher_mock` when extending).
- `launch_app()` returns `"mock": True` — no subprocess or package manager integration.
- Two launcher codepaths (`src/gunnchos_launcher` vs `gunnchos_device_os`) may confuse contributors.

---

## 3. Mode manager

### What exists

| Layer | Path | Modes / presets |
|-------|------|-----------------|
| EVT-1 modes | `gunnchos_device_os/mode_manager.py` | School, Developer, Coder, Play, Media, Research Measurement, Admin |
| Journey presets | `gunnchos_device_os/journey_preset_engine.py`, `config/journey_presets.yaml` | Scooter → Spaceship + Guardian, Classroom, Library, Offline (12 total) |
| Legacy mode manager | `src/gunnchos_launcher/mode_manager.py`, `src/mode_manager/` | Research / campus integration |
| Campus modes | `src/gunnchos_launcher/campus_modes.py` | Fleet / school deployment reports |

### Gaps

- EVT modes (School/Play/…) and journey presets (Scooter/Studio/…) coexist; mapping between them is documented in product PRD but not a single runtime API.
- Mode switching UI in launcher mock covers EVT modes, not all journey presets.
- No user-tested validation that preset transitions feel predictable (WCAG 3.2 intent only).

---

## 4. App registry

### What exists

| Registry | Path | Count |
|----------|------|-------|
| EVT-1 apps | `gunnchos_device_os/app_registry.py` | 15 apps (browser, vscode, steam, waike_offline, …) |
| Research apps | `src/gunnchos_launcher/app_registry.py` | 11 research / fleet apps |
| App packs | `config/app_packs.yaml`, `gunnchos_device_os/app_pack_manager.py` | learn, write, art, music, game, research, offline, … |
| Validation | `scripts/validate_user_focused_os.py` | Pack completeness checks |

### Gaps

- Creative apps (`sketch_placeholder`, `write_placeholder`, `music_notes_placeholder`) are registry slots, not installable apps.
- Streaming apps are browser-route labels only (`youtube`, `netflix`, `hulu`) — see media section.
- App pack apps like `placeholder_writer` differ from registry IDs — naming consistency gap for integrators.

---

## 5. Policy engine

### What exists

| Component | Path | Behavior |
|-----------|------|----------|
| EVT policy engine | `gunnchos_device_os/policy_engine.py` | Profile + mode → allow/deny app |
| Mode policies | `gunnchos_device_os/mode_manager.py` | allowed_apps, blocked_apps, telemetry tier |
| Persona blocks | `config/personas.yaml` | Per-persona blocked_apps |
| Edge cases | `gunnchos_device_os/edge_case_policy.py`, `config/edge_cases.yaml` | 24 fallbacks (steam_unavailable, wsl_unavailable, …) |
| Security / QoS | `src/gunnchos_launcher/security_policy.py`, `qos_policy.py` | Research fleet policies |
| Parental controls | `gunnchos_device_os/parental_controls.py`, `tests/test_parental_controls.py` | Mock content filter |

### Gaps

- Policy is evaluated in Python demos only — no OS-level enforcement.
- Guardian overlay vs School mode vs Guardian preset — three related concepts; docs now clarify in `GUARDIAN_AND_YOUTH_SAFETY.md`.
- `production MDM` explicitly **not claimed** (`product/CLAIM_BOUNDARY.md`).

---

## 6. Profile system

### What exists

| System | Path | Coverage |
|--------|------|----------|
| EVT profiles | `gunnchos_device_os/profile_manager.py` | 8 roles: student, parent_guardian, educator, developer, admin, research_operator, guest, community_partner |
| User profile schema | `gunnchos_device_os/user_profile_schema.py` | Persona, age_band, journey_preset, customization_depth, a11y needs |
| Personas | `config/personas.yaml`, `gunnchos_device_os/persona_engine.py` | 22 personas with onboarding copy |
| Onboarding | `gunnchos_device_os/onboarding_wizard.py` | 7-question first-run tree |
| State store | `gunnchos_device_os/user_state_store.py` | Profile persistence stub |
| Device profiles | `src/gunnchos_launcher/device_profile.py` | Student14, HandheldHybrid, DSXLCoder |

### Gaps

- EVT `profile_manager` (8 roles) and user-focused `UserProfile` (22 personas) are parallel — demos use both; unified UX model pending.
- Profile import/export exists in `customization_engine.py` but not user-tested.
- Non-technical users: Scooter/Bicycle presets and onboarding exist; **no participant studies** confirming comprehension.

---

## 7. Accessibility documentation and implementation

### What exists

| Artifact | Path | Depth |
|----------|------|-------|
| Product requirements | `product/ACCESSIBILITY_REQUIREMENTS.md` | WCAG + UDL matrices, 16 features |
| Short doc | `docs/ACCESSIBILITY_REQUIREMENTS.md` | Pointer to ACCESSIBILITY_AND_LOW_COST.md |
| Legacy doc | `docs/16_ACCESSIBILITY_AND_YOUTH_SAFETY.md` | High-level; not user-focused |
| Manager | `gunnchos_device_os/accessibility_manager.py` | 16 supported features |
| Defaults | `config/accessibility_defaults.yaml` | Per-preset defaults |
| Low-cost note | `ACCESSIBILITY_AND_LOW_COST.md` | Hardware cost alignment |

### Gaps

- **Not WCAG 2.1 AA certified** — design intent only.
- `switch_access` and `voice_input` are **placeholders**.
- No automated a11y test suite (axe, pa11y) in CI.
- Screen reader labels are a config flag, not validated against a real AT stack.
- Accessibility-first persona exists; **no study with disabled participants**.

---

## 8. Steam and gaming documentation

### What exists

| Artifact | Path |
|----------|------|
| Doc | `docs/STEAM_AND_GAMING_MODE.md`, `docs/14_GAMING_AND_INTERACTIVE_MEDIA_MODE.md` |
| Integration stub | `gunnchos_device_os/steam_integration.py` |
| Script | `scripts/install_steam_shortcut.ps1` |
| Mode policy | Play mode allows steam; School blocks steam |
| Edge case | `steam_unavailable` in `edge_case_policy.py` |
| Persona | `gamer` → Arcade preset, `game_pack` |

### Gaps

- **No Steam compatibility guarantee** — honest boundary in `product/CLAIM_BOUNDARY.md`.
- Games are mock launches; Scaly Wings / EdgeGesture are named slots.
- Controller-first navigation tested for HandheldHybrid profile only (`test_os_modules.py`).
- Educational games for children: `scaly_wings_edu` placeholder — no licensed catalog.

---

## 9. WSL and developer documentation

### What exists

| Artifact | Path |
|----------|------|
| Doc | `docs/WSL_DEV_ENVIRONMENT.md`, `docs/15_DEVELOPER_MODE_AND_DEPLOY_PIPELINE.md`, `docs/WINDOWS_FIRST_STRATEGY.md` |
| Module | `gunnchos_device_os/wsl_dev_tools.py` |
| Script | `scripts/install_wsl_dev_environment.ps1`, `scripts/install_dev_tools_windows.ps1` |
| Personas | `college_cs_stem_student`, `software_engineer`, `game_developer` → Workshop/Spaceship |
| Edge case | `wsl_unavailable` |

### Gaps

- WSL is a **documented strategy**, not proven on gunnchOS hardware image.
- VS Code / terminal are registry entries only.
- Cybersecurity learner persona has `lab_vm_placeholder` — no VM sandbox implementation.

---

## 10. Media documentation

### What exists

| Artifact | Path |
|----------|------|
| Doc | `docs/MEDIA_STREAMING_MODE.md`, Media mode in `mode_manager.py` |
| Apps | browser, youtube, netflix, hulu (browser routes) |
| Policy | DRM/HDCP required — **no circumvention** |
| Guardian | Media content caution by age band |

### Gaps

- No Netflix/Hulu app integration beyond browser labels.
- Offline media explicitly blocked in offline preset for streaming apps.
- Captions preference is a setting flag — no player integration test.

---

## 11. Tests

### What exists

| Category | Files | Coverage |
|----------|-------|----------|
| Launcher / modes | `test_launcher.py`, `test_mode_manager.py`, `test_launcher_mode_manager.py`, `test_policy_engine.py` | EVT-1 paths |
| Profiles / devices | `test_profile_manager.py`, `test_device_profiles.py`, `test_launcher_device_profiles.py` | 8 profiles, device classes |
| Parental / privacy | `test_parental_controls.py`, `test_telemetry_consent.py`, `test_privacy_filter.py` | Mock controls |
| OS modules | `test_os_modules.py` | Health, input, WAIKE, gunnchAI |
| Research | `test_research_measurement_mode.py`, `test_seven_gc_bridge.py`, … | Bridge stubs |
| Demo output | `test_evt1_demo_output.py` | JSON artifact shape |
| Access risk | `test_access_risk_model.py` | Security submodule |

### Gaps

- **No `tests/test_user_focused_os.py`** — persona/preset/onboarding not in pytest.
- `scripts/validate_user_focused_os.py` exists but is **not run in CI** (`.github/workflows/ci.yml`).
- `scripts/run_user_focused_os_demo.py` not in CI (EVT demo is).
- No usability or accessibility automated tests.

---

## 12. CI

### What exists

`.github/workflows/ci.yml`:

- `pytest -q tests/` with `PYTHONPATH=.:src`
- `scripts/run_device_os_demo.py` + artifact check
- Access risk smoke scripts

`Makefile`: `test`, `e2e` / `smoke`, config validation, launcher build, tool exports.

### Gaps

- User-focused OS validation and demo not in CI pipeline.
- No launcher_mock journey-preset route tests in CI.
- No claim-boundary linter run in CI (`validate_user_focused_os.py` forbidden-pattern check planned in CLAIM_BOUNDARY §10).

---

## 13. README accuracy

### Accurate today

- "Not a shipping OS image" — correct.
- EVT-1 alpha section matches `gunnchos_device_os` modules and demo script.
- Evidence status (smoke vs field validation) — aligned with `docs/EVIDENCE_STANDARD.md`.
- Integrations listed as bridges/stubs — correct.

### Partially accurate / needs cross-link

- README mentions "21 modules" and "7 modes incl. Coder · 8 profiles" — accurate for EVT layer; **does not prominently list** 22 personas / 12 journey presets (now in `product/USER_FOCUSED_OS_PRD.md`).
- "Launcher mock exposes customization routes" — verify when extending; user-focused routes may be incomplete vs Python demo.
- Audience table does not yet point to new user-focused docs in this pass.

### Recommended README additions (not applied in this audit)

- Link to `docs/USER_FOCUSED_OS_ARCHITECTURE.md` and `demo/user_focused_os_walkthrough.md`.
- Note dual profile systems for contributors.

---

## 14. Persona and audience gaps

### Children (pre-K through middle school)

| Need | Exists | Gap |
|------|--------|-----|
| Simple UI (Scooter) | Yes | No child UX study |
| Guardian required | Yes in config | Mock controls only |
| Offline lessons | WAIKE stub | No full lesson CDN |
| Touch / large targets | a11y defaults | No hardware touch test |
| Educational games | scaly_wings_edu placeholder | No game binary |

### Guardians and parents

| Need | Exists | Gap |
|------|--------|-----|
| Guardian preset + dashboard workspace | Yes | Dashboard is data-only |
| App approval | Config + mock | No real approval UI flow |
| No private content inspection | Policy documented | Not legally reviewed |
| Emergency unlock | Documented path | Not implemented |

### Non-technical users

| Need | Exists | Gap |
|------|--------|-----|
| Onboarding wizard | Yes | Not in launcher mock |
| Plain language | simplified_language flag | Copy not professionally edited |
| One primary action (Scooter) | Preset spec | Mock UI only |
| Help / overwhelmed fallback | edge_case `overwhelmed_user` | Not user-tested |

### Artists, writers, musicians

| Need | Exists | Gap |
|------|--------|-----|
| Studio preset + workspaces | Yes | Apps are placeholders |
| Creator mode manager | Yes | No real canvas/editor/audio |
| Export formats | Documented | No export implementation |
| Offline creative work | Required in product | Local save stub only |

### Advanced researchers (grad / postdoc / wireless)

| Need | Exists | Gap |
|------|--------|-----|
| Laboratory / Spaceship presets | Yes | Strongest research bridge stubs |
| edge_io, field_measurement | Registry + tests | Not field-deployed |
| Telemetry consent | Yes | Opt-in mock only |
| Custom tooling | Spaceship preset | No package manager |

### Accessibility-first users

| Need | Exists | Gap |
|------|--------|-----|
| Persona + essentials pack | Yes | No AT validation |
| High contrast / large text | Theme + manager | Launcher mock theming partial |
| Multiple input methods | keyboard, touch, controller | switch_access, voice_input placeholder |
| Reduced motion / captions | Config | No media player hook |

---

## 15. Related documents (preserved)

| Document | Role |
|----------|------|
| `product/USER_FOCUSED_OS_PRD.md` | Product source of truth |
| `product/CLAIM_BOUNDARY.md` | Allowed / forbidden language |
| `product/PERSONA_MATRIX.md` | 22 personas |
| `product/JOURNEY_PRESETS.md` | 12 presets |
| `docs/WHAT_IS_REAL_TODAY.md` | Minimal inventory (consider expanding) |
| `demo/device_os_evt1_walkthrough.md` | EVT-1 demo steps |
| `quality/CLAIMS_TO_EVIDENCE_MATRIX.md` | Repo-wide evidence |

---

## 16. New documentation from this pass

| File | Purpose |
|------|---------|
| `docs/USER_FOCUSED_OS_ARCHITECTURE.md` | Experience layer architecture |
| `docs/CUSTOMIZATION_SYSTEM.md` | Themes, layouts, import/export |
| `docs/ACCESSIBILITY_AND_INCLUSION.md` | POUR + UDL user-facing |
| `docs/UDL_ALIGNMENT.md` | UDL guideline mapping |
| `docs/PREK_TO_POSTDOC_USE_CASES.md` | Stage table |
| `docs/CREATOR_MODES.md` | Artist/writer/musician flows |
| `docs/SCOOTER_TO_SPACESHIP_MODEL.md` | Complexity metaphor |
| `docs/GUARDIAN_AND_YOUTH_SAFETY.md` | Guardian user experience |
| `docs/OFFLINE_FIRST_USER_EXPERIENCE.md` | Offline UX |
| `docs/PRIVACY_AND_TELEMETRY_FOR_USERS.md` | User-facing privacy |
| `docs/APP_PACKS_AND_WORKSPACES.md` | Bundles and layouts |
| `docs/USER_FOCUSED_OS_LIMITATIONS.md` | Honest limits |
| `docs/USER_TESTING_PLAN.md` | Planned studies |
| `docs/CLAIMS_TO_EVIDENCE_USER_EXPERIENCE.md` | UX claim matrix |
| `demo/*.md` | Walkthrough scripts |

---

## 17. Audit conclusion

The repo contains a **credible alpha scaffold** for a user-focused OS experience layer: data-driven personas, journey presets, customization, accessibility defaults, guardian mocks, offline planning, and creator workflow definitions. **Evidence today is code + config + synthetic demo JSON**, not field validation or participant studies.

**Highest-value next steps** (documentation only; not implemented here):

1. Add `tests/test_user_focused_os.py` and CI steps for `validate_user_focused_os.py` + `run_user_focused_os_demo.py`.
2. Unify EVT modes and journey presets in launcher mock routes.
3. Replace placeholder creative apps with one real offline app each (sketch, write, music notes).
4. IRB-scoped usability study for Scooter onboarding and guardian flows.
