# GunnchOS Mock Retirement Plan

**Goal:** Retire every mock with a documented real replacement. No new mocks without an issue and retirement target.

**Last updated:** 2026-07-02

---

## Retirement priority

| Priority | Mock | Target phase |
|----------|------|--------------|
| P0 | Browser/PWA hub mock | **Partial (Phase 2B)** — mock frame retired; external tab launch |
| P0 | File manager mock | Phase 2 |
| P0 | Game launch mock | **Partial (Phase 2D)** — adapter + readiness; web build in 2E |
| P0 | Local media placeholder | Phase 2 |
| P0 | Python→React manual export | Phase 2 |
| P1 | Settings mock values | **Partial (Phase 2A)** — display/privacy/network persist; system stats still mock |
| P1 | Media playback mock | **Partial (Phase 2C)** — local player; streaming still browser prototype |
| P1 | AI assistant panel | Phase 3 |
| P1 | Guardian/school enforcement stubs | **Partial (Phase 3)** — shell policy enforcement prototype |
| P2 | Fleet/MDM stubs | Field pilot |
| P2 | Updater/recovery design-only | RC |

---

## Mock inventory

### Browser/PWA hub mock

| Field | Detail |
|-------|--------|
| **Status** | **Partially retired (Phase 2B)** — mock frame removed; `appLaunchService.ts` opens external URLs |
| **Still prototype** | No embedded webview; PWA install; production browser shell |
| **Location** | `apps/launcher_mock/src/services/appLaunchService.ts`, `BrowserPwaHub.tsx` |

### File manager mock

| Field | Detail |
|-------|--------|
| **Status** | **RETIRED in Phase 2A** — replaced by `FileManager.tsx` |
| **Replaced with** | `localWorkspaceStore.ts` + `FileManager.tsx` |
| **Phase 4A** | Optional encrypted workspace prototype — `encryptedWorkspaceStore.ts` (not OS FS) |

### Encrypted storage mock

| Field | Detail |
|-------|--------|
| **Status** | **Partially retired (Phase 4A)** — browser encrypted workspace prototype |
| **Location** | `workspaceCrypto.ts`, `encryptedWorkspaceStore.ts`, `EncryptedWorkspacePanel.tsx` |
| **Still not real** | OS filesystem, full-disk encryption, hardware-backed keys |

### Settings mock

| Field | Detail |
|-------|--------|
| **Status** | **Partially retired (Phase 2A)** — `settingsStore.ts` persists theme, a11y, offline, AI privacy |
| **Still mock** | Wi-Fi, storage stats, system update labels in `SettingsPanel.tsx` |

### Media playback mock

| Field | Detail |
|-------|--------|
| **Status** | **Partially retired (Phase 2C)** — `LocalMediaPlayer.tsx` for local files |
| **Still prototype** | YouTube/Netflix/Hulu browser routes; no DRM CDM integration |
| **Location** | `LocalMediaPlayer.tsx`, `localMediaStore.ts`, `MediaMode.tsx` |

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
| **Status** | **Partially retired (Phase 2D)** — `gameLaunchService.ts` + `GameLaunchPanel.tsx` |
| **Still prototype** | No native sandbox; playable web build pending Phase 2E |
| **Location** | `gameLaunchService.ts`, `GameMode.tsx`, `GameLaunchPanel.tsx` |

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
