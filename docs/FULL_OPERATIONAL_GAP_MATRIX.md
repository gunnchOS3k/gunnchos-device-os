# GunnchOS Full Operational Gap Matrix

**Branch baseline:** Phase 0 (PR #30) + Phase 1 (PR #31) merged on `main`  
**Last updated:** 2026-07-02  
**Purpose:** Separate what is real, mock, and missing across release stages.

**Status legend:** `real` · `prototype` · `mock` · `missing`

---

## Summary by release stage

| Stage | What must be true | Current readiness |
|-------|-------------------|-------------------|
| **Alpha (today)** | Runnable shell, policy framework, CI smoke | **Met** |
| **Beta** | Installable prototype, core apps working, honest claims | **Not met** (~15% of beta rows real) |
| **RC** | Signed builds, hardware install proof, security review | **Not met** |
| **Field pilot** | 10–30 student users, support playbook, feedback loop | **Not met** |
| **GA** | UAT, a11y validation, update/rollback proven, all SKUs | **Not met** |
| **Production** | Fleet signing, staged rollout, SLA | **Not met** |

---

## Gap matrix

| Requirement area | Status | Evidence path | Fully operational means | Implementation work | Required tests | Hardware evidence | Release target | Priority | Risk |
|------------------|--------|---------------|-------------------------|---------------------|----------------|-------------------|----------------|----------|------|
| **Bootable OS image** | mock | `os_build/linux_desktop/` (Docker only); `os_build/yocto/README.md` (stub) | Boots on reference ARM64/x86_64 hardware; systemd init; shell autostart | Yocto/meta-gunnchos layer; kernel; init; kiosk compositor | Boot smoke on ref HW; image size check | Boot log, secure boot status on EVT board | Beta (internal image) | P0 | Critical |
| **Hardware compatibility** | prototype | `hardware_compat/`, `gunnchos_device_os/hardware_compatibility_engine.py`, `tests/test_hardware_compatibility_engine.py` | Per-SKU probe passes on physical device; drivers load | Real probe on EVT; driver binding; thermal/power profiles | HW compat pytest + on-device suite | Signed HW test report per SKU | RC | P1 | High |
| **Campus Mode** | prototype | `apps/launcher_mock/src/shell/CampusMode.tsx`, `docs/PHASE0.md` | Persistent desktop; real app launches; dock; offline-capable | Replace mocks with real app adapters; profile persistence to FS | Vitest + integration; mode smoke | Touch + keyboard on ref device | Beta | P0 | High |
| **Browser/PWA support** | mock | `BrowserPwaHub.tsx`, `data/pwaTargets.ts` | Chromium shell; PWA install; iframe/sandbox launch | Embed real browser (Electron/Wayland); PWA manifest | Browser launch e2e; PWA install test | Ref device browser DRM probe | Beta | P0 | High |
| **Google Workspace** | mock | PWA targets in `pwaTargets.ts`; contract JSON | Docs/Sheets/Drive/Gmail usable offline where supported | Browser shell + Google SSO; offline sync policy | Login flow smoke; offline doc open | Network throttling test | Beta | P1 | Medium |
| **Brightspace D2L** | mock | `pwaTargets.ts` (URL only) | Student can open course, submit assignment via browser | Browser route + school SSO integration | D2L navigation smoke | School pilot SSO test | Field pilot | P1 | Medium |
| **NotebookLM** | mock | `pwaTargets.ts` | AI notebook workflow in browser | Browser route; privacy controls wired | Open + privacy toggle test | N/A (web) | Beta | P1 | Low |
| **ChatGPT / AI assistant** | mock | `CampusMode.tsx` AI panel; `gunnchai3k` in registry | Local shell + API backend; student data boundaries | AI backend service; voice/camera input | API mock + privacy pytest | Privacy audit log | Beta | P1 | High |
| **VS Code / Cursor / dev tools** | mock | Registry entries; `wsl_dev_tools.py` mock | Container or native VS Code; Git; terminal | Linux app container; code-server or native | Dev workflow smoke: clone, edit, push | Ref device 8GB RAM stress | Beta | P1 | Medium |
| **MATLAB / STEM tools** | missing | Policy allows browser route only | Jupyter, Octave, MATLAB Online routes work | Container STEM stack; web route shortcuts | Notebook run smoke | N/A / cloud | RC | P2 | Medium |
| **CAD / creative tools** | missing | Creative hub placeholder in Campus Mode | Krita/GIMP/Blender or web CAD launch | Linux containers; web Onshape/Photopea routes | App open smoke | GPU decode on ref HW | RC | P2 | Medium |
| **File manager** | mock | `FileManagerMock.tsx` (`MOCK_FILES`) | Real FS access; Downloads; USB; scoped storage | File System Access API or native FS bridge | CRUD smoke; USB mount test | USB read/write on device | Beta | P0 | High |
| **Local notes** | missing | Not implemented | Create/edit/search notes offline | IndexedDB or FS-backed notes app | Notes CRUD test | Offline persistence on device | Beta | P0 | Medium |
| **PDF reader/annotation** | missing | `pdf` app tile placeholder | Open, scroll, annotate PDFs offline | PDF.js or native viewer | PDF open + annotation test | Storage read on device | Beta | P0 | Medium |
| **Camera** | missing | App tile only | Capture photo/video; scan documents | WebRTC/getUserMedia or native camera app | Camera permission + capture test | Front/rear camera on ref HW | RC | P1 | Medium |
| **Audio recorder** | missing | App tile only | Record, save, playback voice notes | MediaRecorder API or native app | Record/playback smoke | Mic on ref device | RC | P1 | Low |
| **Screen recorder** | missing | App tile only | Record screen for presentations | Native capture pipeline | Record + export test | Display capture on ref HW | RC | P1 | Medium |
| **Video editor** | missing | App tile; Kdenlive listed as future | Trim/export simple video | Kdenlive container or web editor | Export smoke | GPU encode test | GA | P2 | Low |
| **Media Mode / streaming** | prototype | `MediaMode.tsx`, `media_apps.py`, `tests/test_media_policy.py` | Full-screen launcher; honest DRM labels; browser routes | Real browser embed for YouTube; policy enforcement in shell | Vitest + media policy pytest | Network QoS on device | Beta | P0 | High |
| **Local media player** | mock | `local_media` in `media_apps.py`; MediaHub placeholder | Play local MP4/WebM/audio without DRM | HTML5 video player + FS picker | Playback smoke; codec matrix | HW decode verification | Beta | P0 | Medium |
| **Game Mode** | prototype | `GameMode.tsx`, `firstPartyGames.ts` | Full-screen library; real game launch; controller nav | Game launch adapter; performance profiles | Mode switch + launch smoke | Controller + FPS on ref HW | Beta | P0 | High |
| **Anime Aggressors** | mock | `firstPartyGames.ts`; external repo | Playable vertical slice; 60 FPS target | Wire to web/Godot/Unity build | Launch + FPS report | Controller test | Beta | P0 | High |
| **Foot Racing** | mock | `firstPartyGames.ts` | Playable vertical slice | Engine integration | Launch smoke | Touch + controller | Beta | P0 | Medium |
| **Earth Species Artifact Adventure** | mock | `firstPartyGames.ts` | Playable vertical slice; educational content | Engine integration | Launch + offline smoke | 30/60 FPS report | Beta | P0 | Medium |
| **Controller support** | mock | Labels in GameMode/MediaMode | btns | Input mapping; remapping; BT pairing | evdev/SDL gamepad layer | Controller nav e2e | BT controller on ref HW | Beta | P1 | Medium |
| **Touch support** | prototype | React touch targets; no gesture system | Full touch nav all modes | Gesture + one-handed mode | Touch target a11y test | Touchscreen ref device | Beta | P1 | Low |
| **Save/load** | missing | GameMode mentions cloud saves (future) | Per-game save files; cloud sync optional | Save manager service | Save/load roundtrip test | Power-loss save test | RC | P1 | Medium |
| **Cloud sync** | missing | Settings mentions cloud backup (mock) | Profile, docs, saves sync with consent | Sync backend + conflict resolution | Sync smoke test | Offline→online transition | RC | P1 | High |
| **Offline mode** | prototype | `config/modes.yaml` Offline; `OfflineModePanel.tsx` | Apps respect offline policy; local content works | Shell enforcement of mode policy; offline app set | Offline policy pytest + UI test | Airplane mode on device | Beta | P1 | Medium |
| **Guardian mode** | prototype | `guardian_policy.py`, `GuardianPanel.tsx`, modes.yaml | Parent controls enforced on device | Kernel/shell enforcement; age gates | Guardian policy pytest | Family test session | Field pilot | P1 | High |
| **School/library mode** | prototype | modes.yaml School/Library; Media restrictions in UI | Netflix/Hulu blocked; login warnings | Policy enforcement in shell + browser | School mode pytest | Library kiosk pilot | Field pilot | P1 | High |
| **Accessibility** | prototype | `AccessibilityPanel.tsx`, a11y labels in shell | WCAG-oriented validation on hardware | Screen reader; high contrast; TTS | a11y audit; axe tests | HW screen reader test | GA | P1 | High |
| **Internationalization** | missing | English only; docs mention 5 languages | UI strings externalized; 5 priority langs | i18n framework + translations | Locale switch test | N/A | GA | P2 | Medium |
| **Security/privacy** | prototype | `privacy_security_model.py`, `consent_policy.py`, `docs/PRIVACY_SECURITY_MODEL.md` | Threat model signed off; enforcement on device | Complete threat model; privacy indicators | Security pytest; review checklist | Pen test report | RC | P0 | Critical |
| **User accounts** | mock | localStorage profile in shell | Multi-profile; guest; school accounts | Account service; profile FS storage | Profile CRUD test | Multi-user switch on device | Beta | P1 | Medium |
| **App permissions** | mock | Settings UI text only | Per-app camera/mic/file permissions | Permission manager | Permission grant/deny test | Sensor indicator on HW | RC | P1 | High |
| **Updates** | mock | `updater.py`, `tests/test_updater_rollback.py` | Signed OTA; delta updates | Update pipeline; manifest signing | Update apply smoke | OTA on ref device | RC | P1 | Critical |
| **Rollback** | mock | `rollback.py` (mock flag) | Rollback after failed update | Rollback partition + drill | Rollback drill log | Failed update recovery on HW | RC | P1 | Critical |
| **Recovery** | missing | Docs only | Recovery image; factory reset | Recovery partition builder | Recovery boot test | Recovery USB boot | RC | P1 | High |
| **Installer** | missing | `requirements/INSTALLABLE_IMAGE_REQUIREMENTS.md` | Install/uninstall on ref hardware | MSI/image installer prototype | Install smoke | Install on ref SKU | Beta | P0 | Critical |
| **Version manifest** | prototype | SBOM scripts; update manifest tests | CI-generated manifest per build | Wire manifest to CI artifact | Manifest validation test | N/A | Beta | P1 | Medium |
| **Signed builds** | missing | `PLACEHOLDER_SIGNATURE` in updater | Production signing pipeline | Code signing infra | Signature verify test | Signed bundle on device | RC | P0 | Critical |
| **SBOM** | prototype | `scripts/generate_sbom.py`, `tests/test_sbom_generation.py` | SPDX/CycloneDX per release artifact | SBOM in RC pipeline | SBOM schema validation | N/A | RC | P1 | Medium |
| **QA** | prototype | `qa/QA_MASTER_TEST_PLAN.md`, validators | Executed test reports per release | Fill beta/RC test reports | Full regression suite | HW QA signoff | GA | P1 | High |
| **Hardware test evidence** | prototype | Simulated boot readiness; firmware harness | Physical EVT/DVT test reports | Run tests on reference boards | HW test suite | Signed per-SKU reports | RC | P1 | Critical |
| **Field pilot support** | missing | `roadmap/` mentions pilot | Enrollment, feedback, support playbook | Pilot ops package | Pilot checklist | 10–30 user sessions | Field pilot | P1 | High |

---

## Biggest blockers to beta

1. No installable OS image or installer (P0)
2. Browser/PWA hub is mock — no real browser shell (P0)
3. File manager, notes, PDF are mocks/missing (P0)
4. Game Mode cannot launch a real game build (P0)
5. Local media player is placeholder (P0)
6. Policy not enforced by shell — Python only (P0)
7. Python→React bridge not automated in CI on every build (P0)

## Biggest blockers to GA

1. Signed builds + update/rollback not production-proven
2. Hardware compatibility not physically validated all SKUs
3. Accessibility not validated on hardware
4. Security review incomplete
5. No RC UAT execution report
6. DRM/service certification research incomplete (do not claim until done)

---

## Related documents

- [MOCK_RETIREMENT_PLAN.md](MOCK_RETIREMENT_PLAN.md)
- [PHASE2_PLAN.md](PHASE2_PLAN.md)
- [BETA_RELEASE_GATE.md](BETA_RELEASE_GATE.md)
- [WHAT_IS_REAL_TODAY.md](WHAT_IS_REAL_TODAY.md)
- [../release_gates/RELEASE_GATE_MATRIX.md](../release_gates/RELEASE_GATE_MATRIX.md)
