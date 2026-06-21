# Offline-First Requirements

Requirements for disconnected and low-bandwidth operation in the gunnchOS user-focused OS experience layer.

**Status:** device OS alpha · offline-first learning mode — sync and conflict handling are placeholders.

---

## 1. Goals

Users must be able to learn, create, code, and play when internet is unavailable or unreliable. Offline is a first-class journey preset, not an error state.

The `low_bandwidth_offline_user` persona and `offline_first: true` profile flag drive offline-first behavior.

---

## 2. Offline Mode preset

See [JOURNEY_PRESETS.md](JOURNEY_PRESETS.md) — preset ID: `offline`

| Field | Specification |
|-------|---------------|
| Workspace | offline_backpack |
| Allowed apps | waike_offline, gunnchai3k, write_placeholder, sketch_placeholder, vscode (local), scaly_wings_edu, music_notes_placeholder |
| Blocked apps | Cloud streaming, online-only social, license-dependent online games |
| Widgets | offline_status, sync_queue, storage_available |
| Privacy | No network calls; encrypted sync queue placeholder |
| Entry | Automatic on connectivity loss OR explicit user/onboarding choice |

---

## 3. Offline capabilities

Defined in `offline_mode_manager.py` → `OFFLINE_CAPABILITIES`:

| Capability ID | Apps | Sync behavior |
|---------------|------|---------------|
| `offline_lessons` | waike_offline, gunnchai3k | when_online |
| `offline_writing` | write_placeholder | when_online |
| `offline_sketching` | sketch_placeholder | when_online |
| `offline_coding` | vscode, waike_offline | when_online |
| `offline_music` | music_notes_placeholder | when_online |
| `offline_games` | scaly_wings_edu | license_dependent |

### 3.1 Per-capability requirements

| Capability | Offline behavior | Sync when online |
|------------|------------------|------------------|
| Lessons | Full lesson cache; progress saved locally | Merge progress; last-write-wins placeholder |
| Writing | Full editor; autosave local | Upload drafts; conflict prompt placeholder |
| Sketching | Full canvas; export PNG/SVG local | Upload if user consents |
| Coding | Local repos; no remote Git push | Push when online; conflict handling placeholder |
| Music | Save project files locally | Upload if user consents |
| Games | scaly_wings_edu and licensed local installs | License check on reconnect |

---

## 4. Offline essentials app pack

`offline_essentials_pack` in `config/app_packs.yaml`:

| Field | Requirement |
|-------|-------------|
| Apps | waike_offline, gunnchai3k, write_placeholder, sketch_placeholder, scaly_wings_edu |
| offline_support | true |
| required_mode | offline |
| compatible_modes | scooter, bicycle, car, studio, offline |
| beginner_friendly_description | "Everything you need without internet" |
| privacy_warning | null |

---

## 5. Profile and onboarding

| Trigger | Behavior |
|---------|----------|
| Onboarding Q5: "Will you use this offline?" | Set offline_first: true; recommend Offline preset |
| Persona: low_bandwidth_offline_user | Default journey preset: offline |
| Connectivity lost | Auto-switch to Offline preset; show offline_status widget |
| Connectivity restored | Offer sync; show sync_queue widget |

`get_offline_plan(profile_offline_first)` returns full capability map and sync policy.

---

## 6. Sync requirements (placeholder)

| Field | Requirement |
|-------|-------------|
| sync_when_online | true — queue changes while offline |
| conflict_handling | placeholder_last_write_wins — document limitation |
| Queue encryption | Placeholder — document as future work |
| User consent | No upload without explicit consent for creative files |
| Telemetry | No network telemetry while offline |

**Not claimed:** production-grade sync, CRDT merge, or enterprise conflict resolution.

---

## 7. Performance offline

| Requirement | Detail |
|-------------|--------|
| Performance profile | efficiency — no background sync workers |
| Cache | Aggressive local cache for lessons and a11y settings |
| Storage | Warn via storage_almost_full edge case before offline cache fails |
| Battery | efficiency profile; reduced animations |

---

## 8. Accessibility offline

- Full accessibility settings cached locally
- No degradation of keyboard/controller/touch navigation offline
- Screen reader labels available offline
- simplified_language and large_text persist offline

---

## 9. Edge case: offline

Automatic handler when connectivity lost:

| Field | Value |
|-------|-------|
| User message | "You're offline. These apps still work — we'll sync when you're back online." |
| Safe fallback | offline |
| Next action | Switch to offline-capable apps; show offline_status |

---

## 10. Creator workflow offline support

| Workflow | Offline required |
|----------|------------------|
| Artist | yes |
| Writer | yes |
| Musician | yes |
| Game designer | yes |
| Photographer | yes |
| Video creator | no — graceful message |
| Streamer | no — graceful message |

---

## 11. Library and classroom offline

| Context | Offline behavior |
|---------|------------------|
| Library Mode | offline_essentials_pack pre-cached on device |
| Classroom Mode | Teacher deploys offline lesson pack before class |
| Guardian Mode | Offline games within approved list only |

---

## 12. Demo requirements

Demo must simulate:

- Offline library user entering Offline Mode
- Offline writing and lesson completion in demo JSON output
- offline_status and sync_queue widgets in output

`enable_offline_mode(preset_id="offline")` returns plan with mock: true flag.

---

## 13. Validation rules

Validators must fail if:

- offline preset missing from journey_presets.yaml
- offline_essentials_pack lacks offline_support: true
- Any offline capability lacks apps list
- Docs claim production sync without evidence

---

## 14. Claim boundary

**Allowed:** offline-first learning mode · local lesson/writing/sketching/coding intent · sync-when-online placeholder

**Not claimed:** guaranteed offline for all apps · Steam offline mode guarantee · cloud sync production readiness · license management for all games

See [CLAIM_BOUNDARY.md](CLAIM_BOUNDARY.md).
