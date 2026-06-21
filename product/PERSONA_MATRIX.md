# Persona Matrix

All 22 personas for the gunnchOS user-focused OS experience layer. Each persona must have an onboarding route, default journey preset, app pack, workspace, and safe fallback.

**Status:** device OS alpha — persona modeling, not user-tested UX with real participants.

| Persona | Primary need | Default mode | Apps/tools | Customization level | Safety/privacy needs | Offline needs | Success moment |
|---------|--------------|--------------|------------|---------------------|----------------------|---------------|----------------|
| Pre-K learner | Letter sounds, colors, simple touch games | Scooter | gunnchAI3k, WAIKE Offline Lessons, scaly_wings_edu, touch_alphabet_placeholder | simple | Strict guardian required; blocked browser/social; kid_safe theme; no telemetry without guardian consent | Offline lessons, cached alphabet activities | Child completes first letter activity without help |
| Early reader | Reading practice, short writing, safe exploration | Scooter / Bicycle | WAIKE Offline, gunnchAI3k, scaly_wings_edu, read_aloud_placeholder | simple / guided | Guardian required; content filter strict; app approval on | Offline lessons and read-aloud cache | Child reads a short story aloud and saves progress |
| Middle school explorer | Homework, safe browsing, light coding, games | Bicycle | browser, gunnchAI3k, WAIKE Offline, scaly_wings_edu, scratch_placeholder | guided | Moderate content filter; school-mode restrictions; guardian optional | Offline lessons and homework files | Student finishes assignment and shares with teacher |
| High school student | Essays, research, coding classes, tutoring, games | Car | browser, gunnchAI3k, WAIKE Offline, vscode, write_placeholder, steam (if licensed) | full | School-safe browsing; play time windows; standard privacy | Offline writing, lessons, licensed offline games | Student submits essay and opens coding project in one session |
| College non-STEM student | Writing, research, presentations, streaming, notes | Car | browser, write_placeholder, gunnchAI3k, presentation_placeholder, media via browser | full | Standard privacy; no mandatory telemetry | Offline writing and cached lecture PDFs | Student completes research paper draft offline then syncs |
| College CS/STEM student | VS Code, Git, Python/C++, WSL, local preview | Workshop | vscode, terminal, wsl_ubuntu, git_placeholder, gunnchAI3k, browser | full | Developer tools with standard privacy; no root by default | Offline coding templates, local Git repos | Student runs and commits first project locally |
| Graduate researcher | Literature, data, field measurement, edge experiments | Laboratory | field_measurement, edge_io, browser, vscode, research_notes_placeholder | full / power_user | Research telemetry opt-in; strict privacy for field data | Offline field notes, cached papers, local measurement cache | Researcher captures measurement and exports to edge-io bridge |
| Postdoctoral researcher | Advanced experiments, custom tooling, full system access | Spaceship | vscode, terminal, wsl_ubuntu, field_measurement, edge_io, seven_gc_export_placeholder | power_user | Minimal restrictions; explicit telemetry consent; audit log | Offline coding, measurement cache, deferred sync | Researcher runs custom experiment pipeline and exports results |
| Parent/guardian | Supervise youth, approve apps, review activity | Guardian | guardian_dashboard workspace, browser (limited), gunnchAI3k, settings | guided / full | Full guardian controls; privacy-safe telemetry; no private content inspection | Offline guardian settings cache | Guardian approves app and sees age-appropriate home screen |
| Teacher/mentor | Deploy lessons, monitor class, fleet visibility | Classroom | gunnchAI3k, WAIKE Offline, teacher_console workspace, fleet_view_placeholder | full | Student-safe defaults; privacy-respecting aggregate telemetry | Offline lesson deployment pack | Teacher pushes lesson to class devices offline-ready |
| Artist | Sketch, color, export artwork | Studio | sketch_placeholder, palette_placeholder, art_table workspace, art_pack | full | Standard privacy; local-first creative files | Offline sketching and export to PNG/SVG | Artist saves first sketch and exports shareable image |
| Writer | Essays, outlines, long-form writing | Studio | write_placeholder, essay_studio workspace, write_pack | full | Standard privacy; focus mode available | Offline writing with sync when online | Writer completes draft in focus mode without distraction |
| Musician | Record ideas, notes, simple compositions | Studio | music_notes_placeholder, music_studio workspace, music_pack | full | Standard privacy; local audio files | Offline music notes and project files | Musician records idea and saves project offline |
| Gamer | Games, controller play, relaxation | Arcade | steam, scaly_wings, edgegesture, game_room workspace, game_pack | full | Play time windows if youth; content caution; parental restrictions | Licensed offline games (scaly_wings_edu, local installs) | Gamer launches favorite game with controller in one tap |
| Game developer | Game design, level editing, playtesting | Workshop | game_dev_pack, coding_lab, vscode, level_editor_placeholder | full / power_user | Developer tools; sandboxed builds | Offline project files and local playtest | Developer builds and playtests level offline |
| Software engineer | Full dev stack, terminals, deploy pipelines | Spaceship | vscode, terminal, wsl_ubuntu, git_placeholder, deploy_placeholder | power_user | Advanced settings visible; explicit consent for telemetry | Offline repos, local build, sync when online | Engineer deploys from device to test environment |
| Hardware engineer | Schematics, firmware, bench tools | Workshop | hardware_bench workspace, hardware_maker_pack, terminal, firmware_placeholder | full / power_user | Maker tools; USB policy awareness | Offline schematics and firmware cache | Engineer flashes test firmware and reads bench output |
| Cybersecurity learner | Safe labs, CTF practice, network tools | Workshop | cybersecurity_pack, terminal, lab_vm_placeholder, browser (restricted lab) | full | Sandboxed lab environment; no production network by default | Offline lab scenarios and cached challenges | Learner completes CTF challenge in isolated lab mode |
| Wireless/6G researcher | URLLC measurement, edge orchestration, field kit | Laboratory | field_measurement, edge_io, oran_traffic_class_placeholder, research_pack | power_user | Research telemetry opt-in; no private packet capture | Offline measurement cache, deferred export | Researcher captures URLLC sample and exports to research bridge |
| Library/community user | Shared access, guest sessions, easy reset | Library | browser, WAIKE Offline, library_kiosk workspace, community_library_pack | simple | Session reset on exit; no persistent PII; guest profile | Offline essentials pack | User completes session and device resets cleanly for next guest |
| Accessibility-first user | Perceivable, operable UI regardless of ability | Scooter / Bicycle (with a11y overrides) | accessibility_essentials_pack, high contrast theme, screen reader labels | guided (expandable to full) | Reduced telemetry; no color-only meaning; captions default on | Offline with full a11y defaults cached | User navigates home screen with preferred input method independently |
| Low-bandwidth/offline user | Work without reliable internet | Offline | offline_essentials_pack, WAIKE Offline, write_placeholder, sketch_placeholder, scaly_wings_edu | simple / guided | Minimal network calls; privacy-safe sync queue | Full offline-first plan; sync when online | User completes full work session with no connectivity |

---

## Persona ID reference

| Display name | `persona` ID (snake_case) |
|--------------|---------------------------|
| Pre-K learner | `pre_k_learner` |
| Early reader | `early_reader` |
| Middle school explorer | `middle_school_explorer` |
| High school student | `high_school_student` |
| College non-STEM student | `college_non_stem_student` |
| College CS/STEM student | `college_cs_stem_student` |
| Graduate researcher | `graduate_researcher` |
| Postdoctoral researcher | `postdoctoral_researcher` |
| Parent/guardian | `parent_guardian` |
| Teacher/mentor | `teacher_mentor` |
| Artist | `artist` |
| Writer | `writer` |
| Musician | `musician` |
| Gamer | `gamer` |
| Game developer | `game_developer` |
| Software engineer | `software_engineer` |
| Hardware engineer | `hardware_engineer` |
| Cybersecurity learner | `cybersecurity_learner` |
| Wireless/6G researcher | `wireless_6g_researcher` |
| Library/community user | `library_community_user` |
| Accessibility-first user | `accessibility_first_user` |
| Low-bandwidth/offline user | `low_bandwidth_offline_user` |

---

## Validation rules

- Every persona must map to a valid `default_journey_preset` in `config/personas.yaml`.
- Every persona must have a `default_app_pack` and `default_workspace`.
- Guardian-required personas must default to Guardian or Scooter/Bicycle with guardian overlay.
- No persona may lack an onboarding route in `onboarding_wizard.py`.
