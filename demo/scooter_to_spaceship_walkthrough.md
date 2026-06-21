# Scooter to Spaceship Walkthrough

**Audience:** Product, education partners, UX reviewers  
**Duration:** ~15 minutes  
**Status:** design walkthrough — presets evidenced in config; UI partially mocked  

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## Metaphor introduction (presenter script)

"Imagine complexity as vehicles. A **scooter** is one tap, one path — perfect for a four-year-old or anyone overwhelmed. A **spaceship** has every instrument — for a postdoc who wants full control. Same device. User chooses the vehicle, not the factory."

Approved principle: `product/CLAIM_BOUNDARY.md` §7.

---

## Stop 1 — Scooter (pre-K)

**Persona:** `pre_k_learner`  
**Preset:** `scooter`

| Attribute | Value |
|-----------|-------|
| Layout | 3–4 large icons, single row |
| Language | simplified_language on |
| Blocked | browser, steam, terminal |

**Demo command excerpt:**

```bash
PYTHONPATH=. python3 -c "
from gunnchos_device_os.journey_preset_engine import get_preset
import json
print(json.dumps(get_preset('scooter'), indent=2)[:1200])
"
```

**User story:** Sam taps a picture story. Caregiver nearby. No settings maze.

**Success moment:** First letter activity without help.

---

## Stop 2 — Bicycle (middle school)

**Persona:** `middle_school_explorer`  
**Preset:** `bicycle`

- Progress widget visible
- school_safe browser allowed
- scratch_placeholder for light coding

**User story:** Jordan picks today's goal, finishes homework, shares with teacher.

**Exit paths:** Can return to Scooter or advance to Car.

---

## Stop 3 — Car (high school / college daily)

**Persona:** `high_school_student`  
**Preset:** `car`

- 2×4 app grid + homework widget
- vscode for coding class
- steam time-windowed

Demo scenario: `high_school_car` in `run_user_focused_os_demo.py`.

---

## Stop 4 — Studio (creators)

**Presets:** `studio`  
**Personas:** writer, artist, musician

| Persona | Workspace | Feel |
|---------|-----------|------|
| Writer | essay_studio | Distraction-free |
| Artist | art_table | Canvas center |
| Musician | music_studio | Ideas + timeline |

**Note:** Apps are placeholders — say so explicitly.

---

## Stop 5 — Arcade (play)

**Persona:** `gamer`  
**Preset:** `arcade`

- controller_navigation emphasized
- steam, scaly_wings in allowed list
- Guardian may set play_time_window

---

## Stop 6 — Workshop (makers / CS)

**Persona:** `college_cs_stem_student`  
**Preset:** `workshop`

- vscode, terminal, wsl_ubuntu
- wsl_unavailable edge case if WSL missing

Demo scenario: `cs_workshop`.

---

## Stop 7 — Laboratory (research)

**Persona:** `graduate_researcher`  
**Preset:** `laboratory`

- field_measurement, edge_io
- research_opt_in telemetry

---

## Stop 8 — Spaceship (power user)

**Persona:** `postdoctoral_researcher`  
**Preset:** `spaceship`

- customization_depth: power_user
- Full settings, import/export
- Minimal app blocking

Demo scenario: `researcher_laboratory_spaceship` includes both laboratory and spaceship context.

---

## Special presets (brief)

| Preset | One-line |
|--------|----------|
| Guardian | Supervision overlay — mock controls |
| Classroom | Teacher fleet — placeholder |
| Library | Guest session reset |
| Offline | No network shame |

---

## Downshift demo

Explain edge case `overwhelmed_user`:

- User can always simplify → Scooter
- Onboarding "simple control" → Scooter for learners

**Design rule:** Complexity is chosen, not imposed.

---

## Full demo run

```bash
PYTHONPATH=. python3 scripts/run_user_focused_os_demo.py
```

Review all scenarios in order of complexity.

---

## Presenter do-not-say list

- Do not say "all workflows fully implemented"
- Do not say "user-tested scooter metaphor"
- Do not say "shipping OS"

---

## Related docs

- `docs/SCOOTER_TO_SPACESHIP_MODEL.md`
- `docs/PREK_TO_POSTDOC_USE_CASES.md`
- `product/JOURNEY_PRESETS.md`
