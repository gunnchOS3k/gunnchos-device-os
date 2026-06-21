# Scooter to Spaceship Model

**Status:** design principle for user-focused OS — partial implementation in presets and demos  

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## 1. Core principle (approved language)

> gunnchOS must scale from scooter to spaceship. The same device should support a child learning letters, a high school student writing essays, a musician recording ideas, an artist sketching, a gamer relaxing, a CS student coding, and a postdoctoral researcher running experiments.

This describes **design intent**, not a claim that every workflow is fully implemented today. See `product/CLAIM_BOUNDARY.md` §7.

---

## 2. Metaphor map

| Vehicle | Preset ID | Complexity | Who it is for |
|---------|-----------|------------|---------------|
| **Scooter** | scooter | Minimum | Pre-K, first-time users, overwhelmed users, a11y-first seeking simplicity |
| **Bicycle** | bicycle | Low–medium | Early readers, middle school, guided learners |
| **Car** | car | Medium | High school, college daily productivity |
| **Studio** | studio | Medium (focused) | Artists, writers, musicians |
| **Arcade** | arcade | Medium (play) | Gamers, casual recreation |
| **Workshop** | workshop | Medium–high | CS students, makers, game dev, cybersecurity |
| **Laboratory** | laboratory | High | Graduate researchers, field measurement |
| **Spaceship** | spaceship | Maximum | Postdocs, software engineers, power users |

### Special presets (not in vehicle sequence)

| Preset | Role |
|--------|------|
| Guardian | Family safety overlay |
| Classroom | Teacher/fleet deployment |
| Library | Shared kiosk / guest |
| Offline | Disconnected operation |

---

## 3. Scooter — minimum complexity

**Feels like:** One big button at a time. No settings maze.

| Attribute | Value |
|-----------|-------|
| Home layout | 3–4 large icons, single row |
| Settings depth | simple |
| Language | simplified_language on |
| Motion | reduced_motion on |
| Blocked | unrestricted browser, steam, terminal |
| Exit to | bicycle, guardian, offline |

**Example user:** Sam, pre_k_learner — demo scenario in `run_user_focused_os_demo.py`.

---

## 4. Bicycle — guided exploration

**Feels like:** Training wheels with a visible path forward.

| Attribute | Value |
|-----------|-------|
| Home layout | Two icon rows + progress widget |
| Settings depth | guided |
| Widgets | progress_tracker, daily_goal |
| Allowed | school_safe browser, scratch_placeholder |
| Exit to | scooter, car, studio, guardian |

---

## 5. Car — daily productivity

**Feels like:** A dependable study desk.

| Attribute | Value |
|-----------|-------|
| Home layout | 2×4 grid + homework + calendar |
| Settings depth | full |
| Apps | browser, vscode, write, steam (time-windowed) |
| Exit to | bicycle, studio, arcade, workshop |

---

## 6. Studio — creative focus

**Feels like:** A calm room with tools on the wall.

| Attribute | Value |
|-----------|-------|
| Layout | Workspace-centric (art_table, essay_studio, music_studio) |
| focus_mode | Available / on by default |
| Blocked | steam, distraction apps |
| Exit to | car, offline, arcade (break) |

---

## 7. Arcade — play

**Feels like:** Console living room.

| Attribute | Value |
|-----------|-------|
| Input | controller_navigation emphasized |
| Apps | steam, scaly_wings, edgegesture |
| Youth | play_time_window if guardian active |

---

## 8. Workshop — maker and developer

**Feels like:** Bench + IDE.

| Attribute | Value |
|-----------|-------|
| Apps | vscode, terminal, wsl_ubuntu, git placeholders |
| Personas | college_cs_stem_student, game_developer, hardware_engineer |
| Exit to | spaceship, car |

---

## 9. Laboratory — research

**Feels like:** Field kit + data capture.

| Attribute | Value |
|-----------|-------|
| Apps | field_measurement, edge_io, research notes |
| Telemetry | research_opt_in_only |
| Personas | graduate_researcher, wireless_6g_researcher |

---

## 10. Spaceship — full control

**Feels like:** Bridge of the ship — every instrument available.

| Attribute | Value |
|-----------|-------|
| Settings depth | power_user |
| Customization | import/export, advanced panels |
| Restrictions | Minimal — explicit consent for telemetry |
| Personas | postdoctoral_researcher, software_engineer |

---

## 11. Growth without forced complexity

Users **choose** when to move up the ladder:

- Onboarding question: "simple, guided, or full control?"
- Settings always offer " simplify my device" → Scooter fallback
- Edge case `overwhelmed_user` auto-suggests Scooter

**Design rule:** Never require Spaceship complexity for basic tasks.

---

## 12. Complexity vs EVT modes

| Journey preset | Rough EVT mode overlap |
|----------------|------------------------|
| Scooter, Bicycle, Guardian | School |
| Car, Classroom | School (+ broader apps) |
| Workshop, Spaceship | Developer / Coder |
| Arcade | Play |
| Studio | (no direct EVT mode — UX layer only) |
| Laboratory | Research Measurement |
| Offline | Cross-cutting |

Unification is planned; not a single API today.

---

## 13. Demo and evidence

```bash
PYTHONPATH=. python3 scripts/run_user_focused_os_demo.py
```

Output: `results/user_focused_os_demo_output.json` — scenarios from pre_k_scooter through researcher_laboratory_spaceship.

**Not claimed:** User-tested comprehension of metaphor; launcher mock shows all presets.

---

## 14. Related documents

- `product/JOURNEY_PRESETS.md` — full preset specifications
- [PREK_TO_POSTDOC_USE_CASES.md](PREK_TO_POSTDOC_USE_CASES.md)
- [CUSTOMIZATION_SYSTEM.md](CUSTOMIZATION_SYSTEM.md)
- `demo/scooter_to_spaceship_walkthrough.md`
