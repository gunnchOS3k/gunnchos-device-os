# App Packs and Workspaces

**Status:** device OS alpha · data-driven bundles — placeholder apps in many packs  

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## 1. Concepts

| Concept | Definition | Module |
|---------|------------|--------|
| **App pack** | Curated bundle of apps with shared purpose and offline flag | app_pack_manager.py |
| **Workspace** | Task-focused layout with quick_actions | workspace_manager.py |
| **Journey preset** | Allowed/blocked apps + default layout | journey_preset_engine.py |
| **Persona** | Default pack + workspace assignment | persona_engine.py |

---

## 2. App packs

**Config:** `config/app_packs.yaml`

| Pack ID | Purpose | Required mode | Offline | Personas |
|---------|---------|---------------|---------|----------|
| learn_pack | Homework, lessons, tutoring | bicycle | yes | pre_k through college |
| write_pack | Essays, notes, research writing | studio | yes | writer, college_non_stem |
| art_pack | Sketch, paint, reference | studio | yes | artist |
| music_pack | Notes, composition | studio | yes | musician |
| game_pack | Games, controller play | arcade | partial | gamer |
| game_dev_pack | Level design, code | workshop | yes | game_developer |
| coding_pack | VS Code, terminal, Git | workshop | yes | college_cs_stem, software_engineer |
| research_pack | Measurement, edge-io | laboratory | partial | graduate_researcher, wireless_6g_researcher |
| hardware_maker_pack | Bench, firmware | workshop | yes | hardware_engineer |
| cybersecurity_pack | Lab VM, CTF | workshop | yes | cybersecurity_learner |
| community_library_pack | Guest essentials | library | yes | library_community_user |
| offline_essentials_pack | Low-bandwidth core | offline | yes | low_bandwidth_offline_user |
| accessibility_essentials_pack | A11y-focused tools | scooter/bicycle | yes | accessibility_first_user |
| guardian_pack | Supervision tools | guardian | yes | parent_guardian |

Each pack includes:

- `beginner_friendly_description` — plain language for onboarding
- `why_it_exists` — contributor documentation
- `compatible_modes` — which presets may use this pack
- `privacy_warning` — null or explicit (e.g. online-only tools)

---

## 3. Workspaces

**Config:** `config/workspaces.yaml`

| Workspace ID | Layout intent | Quick actions (examples) |
|--------------|---------------|--------------------------|
| homework_desk | Study surface | open_lesson, ask_tutor, check_calendar |
| essay_studio | Distraction-free writing | new_essay, focus_mode, export |
| art_table | Canvas center | new_sketch, palette, export_png |
| music_studio | Timeline / notes | new_project, record_idea, export |
| coding_lab | IDE + terminal split | new_repo, open_terminal, run |
| game_room | Controller-first | launch_steam, local_games |
| hardware_bench | Schematic + serial | flash_firmware, read_sensor |
| guardian_dashboard | Supervision | approve_app, screen_time, child_view |
| teacher_console | Class deploy | push_lesson, fleet_status |
| library_kiosk | Guest simple | start_session, help, end_session |
| offline_backpack | Offline hub | sync_status, storage, essentials |
| research_lab | Measurement focus | capture, export_edge_io, notes |

Validator requires every workspace to have `quick_actions`.

---

## 4. How packs and workspaces combine

```
Persona (artist)
  → default_app_pack: art_pack
  → default_workspace: art_table
  → journey_preset: studio
  → CustomizationEngine may pin additional apps
```

Onboarding calls `get_app_pack()` and `get_workspace()` after persona selection.

---

## 5. App registry vs pack apps

**Registry** (`app_registry.py`): canonical app IDs for policy engine.

**Packs** may reference placeholder IDs (e.g. `placeholder_writer`) not yet in registry — **integration gap** documented in audit.

Policy evaluation uses registry IDs; pack install would map placeholders to real packages in future.

---

## 6. Mode compatibility

App packs declare `compatible_modes`. Attempting to activate a pack incompatible with current preset should trigger edge case or wizard suggestion (stub).

Example: research_pack incompatible with Scooter — blocked apps include edge_io.

---

## 7. Offline support matrix

| Pack | offline_support | User expectation |
|------|-----------------|------------------|
| learn_pack | true | Lessons work on bus |
| write_pack | true | Essay autosave local |
| art_pack | true | Sketch without Wi-Fi |
| game_pack | partial | Licensed installs only |
| research_pack | partial | Cache measurements; export later |

---

## 8. Beginner-friendly copy example

**learn_pack:** "Start here for homework help, guided lessons, and safe browsing."

Shown during onboarding and app pack picker (UI placeholder).

---

## 9. API summary

```python
from gunnchos_device_os.app_pack_manager import get_app_pack, list_app_packs
from gunnchos_device_os.workspace_manager import get_workspace, list_workspaces

pack = get_app_pack("write_pack")
workspace = get_workspace("essay_studio")
```

---

## 10. Evidence and gaps

| Claim | Evidence | Gap |
|-------|----------|-----|
| Packs validated | validate_user_focused_os.py | CI not wired |
| Workspaces have quick_actions | validator | Mock UI layouts |
| Persona defaults | personas.yaml | Placeholder apps |

---

## 11. Related documents

- [CREATOR_MODES.md](CREATOR_MODES.md)
- [OFFLINE_FIRST_USER_EXPERIENCE.md](OFFLINE_FIRST_USER_EXPERIENCE.md)
- [USER_FOCUSED_OS_ARCHITECTURE.md](USER_FOCUSED_OS_ARCHITECTURE.md)
- `product/PERSONA_MATRIX.md`
