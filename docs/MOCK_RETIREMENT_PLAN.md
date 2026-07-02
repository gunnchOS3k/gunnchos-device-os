# GunnchOS Mock Retirement Plan

**Goal:** Retire every mock with a documented real replacement. No new mocks without an issue and retirement target.

**Last updated:** 2026-07-02

---

## Retirement priority

| Priority | Mock | Target phase |
|----------|------|--------------|
| P0 | Browser/PWA hub mock | Phase 2 |
| P0 | File manager mock | Phase 2 |
| P0 | Game launch mock | Phase 2 |
| P0 | Local media placeholder | Phase 2 |
| P0 | Python→React manual export | Phase 2 |
| P1 | Settings mock values | **Partial (Phase 2A)** — display/privacy/network persist; system stats still mock |
| P1 | Media playback mock | Phase 2–3 |
| P1 | AI assistant panel | Phase 3 |
| P1 | Guardian/school enforcement stubs | Phase 3 |
| P2 | Fleet/MDM stubs | Field pilot |
| P2 | Updater/recovery design-only | RC |

---

## Mock inventory

### Browser/PWA hub mock

| Field | Detail |
|-------|--------|
| **Why it exists** | Phase 0 shell needed navigation to school/web targets without a browser engine |
| **Location** | `apps/launcher_mock/src/shell/BrowserPwaHub.tsx` — mock frame, external link only |
| **Replaces with** | Embedded Chromium shell (Electron/Wayland kiosk) or system browser delegate |
| **Minimum real implementation** | Open URL in sandboxed webview; PWA install hook; no iframe security bypass |
| **Test needed** | E2E: open Google Docs, D2L URL loads |
| **Owner area** | Shell / browser |
| **Blocking dependencies** | Browser engine choice; Linux base image |

### File manager mock

| Field | Detail |
|-------|--------|
| **Status** | **RETIRED in Phase 2A** — replaced by `FileManager.tsx` |
| **Replaced with** | `localWorkspaceStore.ts` + `FileManager.tsx` |

### Settings mock

| Field | Detail |
|-------|--------|
| **Status** | **Partially retired (Phase 2A)** — `settingsStore.ts` persists theme, a11y, offline, AI privacy |
| **Still mock** | Wi-Fi, storage stats, system update labels in `SettingsPanel.tsx` |

### Media playback mock

| Field | Detail |
|-------|--------|
| **Why it exists** | Phase 1 Media Mode; honest DRM boundary |
| **Location** | `MediaHub.tsx`, `MediaMode.tsx` — browser route prototype cards |
| **Replaces with** | Real browser embed for YouTube; `<video>` for local files |
| **Minimum real implementation** | YouTube opens in webview; Netflix/Hulu show DRM disclaimer + browser route |
| **Test needed** | YouTube load smoke; DRM warning visible for Netflix/Hulu |
| **Owner area** | Media Mode |
| **Blocking dependencies** | Browser CDM path research (no circumvention) |

### Local media placeholder

| Field | Detail |
|-------|--------|
| **Why it exists** | Offline Mode policy allows local media |
| **Location** | `media_apps.py` `local_media`; MediaHub card |
| **Replaces with** | HTML5 video/audio player + file picker |
| **Minimum real implementation** | Play MP4/WebM/MP3 from user-selected file |
| **Test needed** | Play local sample file |
| **Owner area** | Media Mode |
| **Blocking dependencies** | File manager or file picker |

### Network/audio diagnostics mock

| Field | Detail |
|-------|--------|
| **Why it exists** | Media Mode UX for streaming quality |
| **Location** | `MediaDiagnostics.tsx` — static indicators |
| **Replaces with** | Network Information API + real BT/audio status from OS |
| **Minimum real implementation** | Show online/offline; estimated bandwidth; audio output name |
| **Test needed** | Offline hides streaming cards |
| **Owner area** | Media Mode / system |
| **Blocking dependencies** | OS audio/network APIs |

### AI assistant panel mock

| Field | Detail |
|-------|--------|
| **Why it exists** | Product vision: AI learning companion |
| **Location** | `CampusMode.tsx` AI sidebar |
| **Replaces with** | Backend API (local or cloud) with privacy controls |
| **Test needed** | Query/response smoke; privacy mode blocks logging |
| **Owner area** | AI / education |
| **Blocking dependencies** | Model API; student data policy |

### Game launch mock

| Field | Detail |
|-------|--------|
| **Why it exists** | Phase 0 Game Mode shell |
| **Location** | `GameMode.tsx` — "Launch (mock)" button |
| **Replaces with** | Game launch adapter (local binary, web build URL, or container) |
| **Minimum real implementation** | Launch one first-party game build (Anime Aggressors web/Godot) |
| **Test needed** | Launch returns process/URL; exit returns to library |
| **Owner area** | Game Mode |
| **Blocking dependencies** | Playable game artifact; launch protocol |

### Steam/gaming path mock

| Field | Detail |
|-------|--------|
| **Why it exists** | Play mode policy includes Steam |
| **Location** | `gunnchos_device_os/steam_integration.py` |
| **Replaces with** | Steam Linux client or Proton path on device |
| **Minimum real implementation** | Detect Steam install; launch library (optional for beta) |
| **Test needed** | Steam path probe on Linux image |
| **Owner area** | Game Mode |
| **Blocking dependencies** | Linux desktop image; GPU drivers |

### WSL/dev tools mock

| Field | Detail |
|-------|--------|
| **Why it exists** | Windows-first research scaffold |
| **Location** | `gunnchos_device_os/wsl_dev_tools.py` |
| **Replaces with** | Linux container (distrobox/Podman) or native dev packages |
| **Minimum real implementation** | Terminal + Python + Git in container |
| **Test needed** | `git clone` + `python -c` smoke |
| **Owner area** | Developer mode |
| **Blocking dependencies** | Container runtime on base image |

### Updater mock

| Field | Detail |
|-------|--------|
| **Why it exists** | Shippable OS requirement design |
| **Location** | `gunnchos_device_os/updater.py` — `PLACEHOLDER_SIGNATURE` |
| **Replaces with** | Signed manifest + apply + verify pipeline |
| **Test needed** | Apply update on ref device; signature fail rejects |
| **Owner area** | Release engineering |
| **Blocking dependencies** | Signing infra; partition layout |

### Rollback design-only

| Field | Detail |
|-------|--------|
| **Why it exists** | Update safety requirement |
| **Location** | `gunnchos_device_os/rollback.py` — `"mock": True` |
| **Replaces with** | A/B partition rollback or snapshot restore |
| **Test needed** | Rollback drill log after forced bad update |
| **Owner area** | Release engineering |
| **Blocking dependencies** | Updater prototype |

### Recovery design-only

| Field | Detail |
|-------|--------|
| **Why it exists** | GA requirement |
| **Location** | Docs only (`requirements/INSTALLABLE_IMAGE_REQUIREMENTS.md`) |
| **Replaces with** | Recovery USB/image builder |
| **Test needed** | Boot recovery; factory reset |
| **Owner area** | Release engineering |
| **Blocking dependencies** | Bootable image |

### Hardware detection simulation

| Field | Detail |
|-------|--------|
| **Why it exists** | Pre-EVT research; no boards in loop |
| **Location** | `hardware_boot_readiness.py`, `hardware_component_runtime/` |
| **Replaces with** | Real probe on EVT/DVT hardware |
| **Test needed** | Per-SKU signed test report |
| **Owner area** | Hardware compat |
| **Blocking dependencies** | Reference hardware availability |

### Fleet/MDM stubs

| Field | Detail |
|-------|--------|
| **Why it exists** | 7GC fleet research prototype |
| **Location** | `FleetView.tsx`, `src/gunnchos_launcher/` stubs |
| **Replaces with** | MDM enrollment (if claimed) or remove from student SKU |
| **Test needed** | Enrollment smoke (if in scope) |
| **Owner area** | Fleet / programs |
| **Blocking dependencies** | MDM vendor choice; not required for beta student device |

### Guardian/school/library policy stubs

| Field | Detail |
|-------|--------|
| **Why it exists** | YAML + Python policy without shell enforcement |
| **Location** | `config/modes.yaml`, `guardian_policy.py`; UI summaries in MediaMode |
| **Replaces with** | Shell reads contract; blocks launches; browser content filters |
| **Minimum real implementation** | School mode hides Netflix/Hulu cards; launch denied with message |
| **Test needed** | Policy pytest + UI integration test |
| **Owner area** | Policy / shell |
| **Blocking dependencies** | Real app launch path to enforce against |

---

## Retirement process

1. Open issue from [docs/issues/](../issues/) backlog
2. Implement minimum real replacement
3. Add test that fails if mock path is used
4. Update [WHAT_IS_REAL_TODAY.md](WHAT_IS_REAL_TODAY.md) and gap matrix
5. Remove or gate mock code behind `DEV_MOCK` flag only if needed for demos
