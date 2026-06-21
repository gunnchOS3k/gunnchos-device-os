# Offline-First Walkthrough

**Audience:** Rural connectivity advocates, librarians, low-bandwidth users  
**Duration:** ~10 minutes  
**Status:** capability demo — sync is placeholder  

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

**Not claimed:** production sync protocol or conflict resolution tested in field.

---

## Principle (30 sec)

"Offline is not an error. The device should say: your work is safe here — we'll sync when you choose."

Persona: `low_bandwidth_offline_user`  
Preset: `offline`

---

## Prerequisites

```bash
PYTHONPATH=. python3 scripts/run_user_focused_os_demo.py
```

Inspect scenarios: `offline_library`, and profiles with `offline_first: true`.

---

## Step 1 — Enable offline mode (2 min)

```python
from gunnchos_device_os.offline_mode_manager import enable_offline_mode
import json
print(json.dumps(enable_offline_mode("offline"), indent=2))
```

Discuss returned capabilities:

- offline_lessons
- offline_writing
- offline_sketching
- offline_coding
- offline_music
- offline_games (license_dependent)

---

## Step 2 — Offline preset layout (2 min)

From `journey_preset_engine.get_preset("offline")`:

- Workspace: offline_backpack
- Widgets: offline_status, sync_queue, storage_available
- Blocked: cloud streaming, online-only social

**User sees:** status badge "Working offline" — not a red error banner (design intent).

---

## Step 3 — Library guest session (2 min)

Scenario `offline_library` in demo JSON:

| Field | Value |
|-------|-------|
| Persona | library_community_user |
| Preset | offline |
| Pack | community_library_pack / offline_essentials |

**Narrative:** Pat uses WAIKE Offline and browser essentials without login. Session ends → device resets for next guest (policy intent).

---

## Step 4 — Onboarding choice (1 min)

Onboarding question: "Will you use this offline?"

If yes → offline preset or `offline_first` on UserProfile.

Show in `onboarding_wizard.py` logic.

---

## Step 5 — Connectivity loss edge case (1 min)

`edge_case_policy` + `config/edge_cases.yaml` entry `connectivity_lost`:

- Plain-language user_message
- Work saved locally
- Optional auto-switch to offline preset

Read user_message aloud from config — emphasize understandable wording (WCAG 3.3 intent).

---

## Step 6 — What works offline vs not (2 min)

| Works (alpha intent) | Requires network |
|----------------------|------------------|
| WAIKE lesson list mock | Netflix/Hulu/YouTube streaming |
| Local write/sketch/music stubs | Steam online multiplayer |
| vscode local projects | Live edge_io export |
| Accessibility settings cache | Cloud profile sync |
| scaly_wings_edu (licensed local) | Fleet OTA (deferred) |

---

## Step 7 — Sync honesty (1 min)

| Feature | Status |
|---------|--------|
| sync_queue widget | UI spec |
| Conflict resolution | last-write-wins placeholder |
| Encrypted queue | Documented, not implemented |

Say: "Sync when online is designed — not production-ready."

---

## Step 8 — App pack offline flags (1 min)

```bash
PYTHONPATH=. python3 -c "
from gunnchos_device_os.app_pack_manager import list_app_packs, get_app_pack
for p in list_app_packs():
    print(p, get_app_pack(p).get('offline_support'))
"
```

Validator requires `offline_support` on every pack.

---

## Simulated user day

**Morning:** No Wi-Fi at home. Jordan opens Car preset → device suggests Offline. Writes essay offline.

**Afternoon:** Library Wi-Fi. sync_queue shows 1 pending item (placeholder). Jordan taps sync.

**Evening:** Guest Pat uses library kiosk — offline essentials, session reset.

---

## Presenter checklist

- [ ] Said offline-first is mode, not failure
- [ ] Labeled sync as placeholder
- [ ] Did not claim full offline parity with online streaming
- [ ] Referenced low_bandwidth_offline_user persona

---

## Related docs

- `docs/OFFLINE_FIRST_USER_EXPERIENCE.md`
- `product/OFFLINE_FIRST_REQUIREMENTS.md`
- `docs/OFFLINE_FIRST_DESIGN.md`
- [persona_demo_transcripts.md](persona_demo_transcripts.md) — Pat (library guest)
