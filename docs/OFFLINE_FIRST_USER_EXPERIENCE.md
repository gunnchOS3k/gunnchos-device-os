# Offline-First User Experience

**Status:** device OS alpha · offline-first learning mode — sync and conflict handling are placeholders  

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## 1. Principle

**Offline is not an error state.** Users on unreliable networks, rural connections, or deliberate airplane mode should complete learning, writing, sketching, coding, and licensed play without shame or broken UX.

The `low_bandwidth_offline_user` persona and `offline_first: true` profile flag drive offline-first behavior.

---

## 2. Offline journey preset

**Preset ID:** `offline`  
**Module:** `gunnchos_device_os/offline_mode_manager.py`

| Attribute | Value |
|-----------|-------|
| Workspace | offline_backpack |
| Widgets | offline_status, sync_queue, storage_available |
| Entry | User choice in onboarding OR automatic on connectivity loss (planned) |
| Privacy | No network calls; encrypted sync queue placeholder |
| Exit | car, bicycle, library when online |

---

## 3. Offline capabilities

| Capability ID | Apps | Sync when online |
|---------------|------|------------------|
| offline_lessons | waike_offline, gunnchai3k | when_online (merge placeholder) |
| offline_writing | write_placeholder | when_online (conflict prompt placeholder) |
| offline_sketching | sketch_placeholder | when_online |
| offline_coding | vscode, waike_offline | when_online |
| offline_music | music_notes_placeholder | when_online |
| offline_games | scaly_wings_edu | license_dependent |

**Not claimed:** production sync protocol or conflict resolution tested in field.

---

## 4. App packs with offline support

From `config/app_packs.yaml` — each pack declares `offline_support: true|false`:

| Pack | Offline | Notes |
|------|---------|-------|
| learn_pack | yes | Core lessons |
| write_pack | yes | Local documents |
| art_pack | yes | Local canvas files |
| music_pack | yes | Local projects |
| offline_essentials_pack | yes | Library / low-bandwidth persona |
| game_pack | partial | Licensed local installs only |
| research_pack | partial | Measurement cache |

---

## 5. User experience flows

### Choose offline at onboarding

1. Question: "Will you use this offline?"
2. If yes → offline preset or offline_first flag on profile.
3. `enable_offline_mode("offline")` returns capability list + sync_queue stub.
4. Home shows offline_status widget.

### Lose connectivity mid-session

1. Edge case `connectivity_lost` (edge_case_policy).
2. User message in plain language: work saved locally.
3. Optional auto-switch to offline preset (configurable).
4. Sync queue holds pending uploads (placeholder).

### Library guest offline

1. library_community_user + offline essentials.
2. Session completes without account.
3. Reset on exit — no PII retained.

Demo: `run_user_focused_os_demo.py` scenario `offline_library`.

---

## 6. What works offline today (alpha)

| Activity | Evidence | Limitation |
|----------|----------|------------|
| Run pytest / demos | README smoke | Dev machine, not device image |
| WAIKE lesson list | waike_integration.list_offline_lessons() | Mock lesson IDs |
| Write/sketch/music | Creator workflow defs | Placeholder apps |
| Accessibility settings | Local cache in demo | No real OS cache layer |
| gunnchAI tutor | tutor_session_start mock | No local model |

---

## 7. What requires connectivity

| Activity | Offline behavior |
|----------|------------------|
| Netflix / Hulu / YouTube streaming | Blocked in offline preset |
| Steam online multiplayer | Blocked; local licensed games may work |
| edge_io live export | Queued to sync_queue placeholder |
| Fleet admin updates | Deferred |
| Cloud profile sync | import/export local file only today |

---

## 8. Sync placeholder honesty

| Feature | Status |
|---------|--------|
| sync_queue widget | UI spec only |
| conflict resolution | last-write-wins placeholder in docs |
| encrypted queue | Documented intent, not implemented |
| bandwidth-aware sync | Future |

---

## 9. Accessibility offline

- All 16 accessibility features load from local defaults.
- Captions for **cached** media only.
- simplified_language strings bundled with offline lesson pack (intent).

See [ACCESSIBILITY_AND_INCLUSION.md](ACCESSIBILITY_AND_INCLUSION.md).

---

## 10. Evidence and gaps

| Claim | Evidence | Gap |
|-------|----------|-----|
| Offline preset defined | journey_presets.yaml | No OS network stack |
| offline_mode_manager | Python module | No real connectivity hook |
| App pack offline flags | app_packs.yaml | Placeholder apps |
| Demo scenario | user_focused_os demo JSON | Synthetic |

---

## 11. Related documents

- `product/OFFLINE_FIRST_REQUIREMENTS.md`
- `docs/OFFLINE_FIRST_DESIGN.md` (minimal legacy pointer)
- [APP_PACKS_AND_WORKSPACES.md](APP_PACKS_AND_WORKSPACES.md)
- `demo/offline_first_walkthrough.md`
