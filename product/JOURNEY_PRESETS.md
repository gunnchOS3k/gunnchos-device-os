# Journey Presets

Twelve data-driven workflow presets for the gunnchOS user-focused OS experience layer. Users may switch presets at any time; exit paths define allowed transitions.

**Status:** device OS alpha · workflow presets — not a finished shipping OS.

---

## Preset overview

| Preset | Metaphor | Complexity | Primary audience |
|--------|----------|------------|------------------|
| Scooter | Simplest path | Minimum | Pre-K, first-time, overwhelmed |
| Bicycle | Guided exploration | Low–medium | Early readers, middle school |
| Car | Full productivity | Medium | High school, college daily work |
| Studio | Creative focus | Medium | Artists, writers, musicians |
| Arcade | Play and recreation | Medium | Gamers, casual users |
| Workshop | Maker and developer | Medium–high | CS students, makers, game dev |
| Laboratory | Research and measurement | High | Graduate/postdoc researchers |
| Spaceship | Power-user control | Maximum | Advanced developers, postdocs |
| Guardian | Family safety | Supervised | Youth with guardian oversight |
| Classroom | Teacher deployment | Managed | Educators, fleet sessions |
| Library | Shared public access | Guest | Community, library kiosks |
| Offline | Disconnected operation | Variable | Low-bandwidth users |

---

## 1. Scooter Mode

**Purpose:** Simplest possible interface — one primary action per screen, no forced complexity.

| Field | Specification |
|-------|---------------|
| **Home screen layout** | Single row of 3–4 large icons; no widget grid; persistent "Help" and "More" affordance |
| **Allowed apps** | gunnchAI3k, WAIKE Offline, scaly_wings_edu, touch_alphabet_placeholder, settings (simple view) |
| **Blocked apps** | browser (unrestricted), steam, terminal, vscode, social_placeholder, edge_io |
| **Default accessibility** | large_text: true, simplified_language: true, reduced_motion: true, touch_navigation: true, high_contrast: optional |
| **Recommended widgets** | none (icons only) |
| **Data/privacy policy** | strict; no telemetry without guardian consent; local-only activity cache |
| **Performance profile** | efficiency; low animation; prefetch minimal |
| **Onboarding text** | "Welcome! Tap a picture to start. You can always ask for help." |
| **Exit paths** | bicycle, guardian, offline, accessibility via settings |

---

## 2. Bicycle Mode

**Purpose:** Guided learning and creation — step-by-step paths with visible progress.

| Field | Specification |
|-------|---------------|
| **Home screen layout** | Two rows of icons + one progress widget; "Today's goal" banner |
| **Allowed apps** | gunnchAI3k, WAIKE Offline, browser (school_safe filter), scaly_wings_edu, scratch_placeholder, write_placeholder |
| **Blocked apps** | steam, terminal (unrestricted), edge_io, social_placeholder |
| **Default accessibility** | simplified_language: true, touch_navigation: true, keyboard_navigation: true, captions_preference: true |
| **Recommended widgets** | progress_tracker, daily_goal, lesson_reminder |
| **Data/privacy policy** | strict; aggregate opt-in telemetry; no private content inspection |
| **Performance profile** | balanced; cache lessons aggressively |
| **Onboarding text** | "Let's explore together. Pick what you want to learn or create today." |
| **Exit paths** | scooter, car, studio, guardian, offline |

---

## 3. Car Mode

**Purpose:** Full student productivity — homework, essays, research, light coding.

| Field | Specification |
|-------|---------------|
| **Home screen layout** | App grid (2×4) + homework widget + calendar widget |
| **Allowed apps** | browser, gunnchAI3k, WAIKE Offline, write_placeholder, vscode, presentation_placeholder, steam (time-windowed) |
| **Blocked apps** | edge_io (unless research persona), unrestricted terminal |
| **Default accessibility** | keyboard_navigation: true, touch_navigation: true, focus_mode: available |
| **Recommended widgets** | homework_due, calendar, tutor_shortcut, notes |
| **Data/privacy policy** | standard; school-safe network policy; telemetry aggregate opt-in |
| **Performance profile** | balanced; multi-task friendly |
| **Onboarding text** | "Your study station is ready. Pin the apps you use most." |
| **Exit paths** | bicycle, studio, arcade, workshop, offline, guardian |

---

## 4. Studio Mode

**Purpose:** Artist, writer, musician creation — focus-first creative workstation.

| Field | Specification |
|-------|---------------|
| **Home screen layout** | Workspace-centric: art_table / essay_studio / music_studio with pinned creative apps |
| **Allowed apps** | sketch_placeholder, write_placeholder, music_notes_placeholder, palette_placeholder, browser (reference), export_tools_placeholder |
| **Blocked apps** | steam, edgegesture, fleet_admin_placeholder |
| **Default accessibility** | reduced_motion: optional, focus_mode: true, color_safe_mode: available, large_text: user choice |
| **Recommended widgets** | recent_projects, inspiration_board, export_shortcut |
| **Data/privacy policy** | standard; local-first creative files; no cloud upload without consent |
| **Performance profile** | creative; prioritize input latency for drawing/writing |
| **Onboarding text** | "Create something today. Your tools are on the left; your canvas is center." |
| **Exit paths** | car, bicycle, offline, arcade (break) |

---

## 5. Arcade Mode

**Purpose:** Games and recreation — controller-first, relaxed play.

| Field | Specification |
|-------|---------------|
| **Home screen layout** | Game shelf layout; large game tiles; controller status indicator |
| **Allowed apps** | steam, scaly_wings, edgegesture, scaly_wings_edu, media via browser (time-windowed) |
| **Blocked apps** | vscode, terminal, edge_io, field_measurement |
| **Default accessibility** | controller_navigation: true, reduced_motion: user choice, captions_preference: true |
| **Recommended widgets** | play_time_remaining, recent_games, controller_battery |
| **Data/privacy policy** | standard; play time enforcement if guardian active; no gameplay telemetry without consent |
| **Performance profile** | performance; prioritize input latency and GPU where available |
| **Onboarding text** | "Pick a game and play. Controller connected? You're ready." |
| **Exit paths** | car, guardian, offline (licensed offline games only) |

---

## 6. Workshop Mode

**Purpose:** Maker, hardware, software, and game development creation.

| Field | Specification |
|-------|---------------|
| **Home screen layout** | coding_lab / hardware_bench workspace; terminal and IDE prominent |
| **Allowed apps** | vscode, terminal, wsl_ubuntu, git_placeholder, firmware_placeholder, level_editor_placeholder, browser |
| **Blocked apps** | unrestricted media apps during focus sessions |
| **Default accessibility** | keyboard_navigation: true, high_contrast: available, focus_mode: true |
| **Recommended widgets** | git_status, build_output, project_switcher |
| **Data/privacy policy** | standard; developer telemetry opt-in; sandboxed builds |
| **Performance profile** | performance; compile/build priority |
| **Onboarding text** | "Build something. Your lab is open — terminal, editor, and tools are pinned." |
| **Exit paths** | car, laboratory, spaceship, offline (local repos) |

---

## 7. Laboratory Mode

**Purpose:** Research measurement, field experiments, edge-io integration.

| Field | Specification |
|-------|---------------|
| **Home screen layout** | research_bench workspace; measurement and export tools front and center |
| **Allowed apps** | field_measurement, edge_io, browser, vscode, research_notes_placeholder, seven_gc_export_placeholder |
| **Blocked apps** | steam, scaly_wings, unrestricted social |
| **Default accessibility** | keyboard_navigation: true, screen_reader_labels: true, high_contrast: available |
| **Recommended widgets** | measurement_status, export_queue, consent_reminder |
| **Data/privacy policy** | strict; explicit telemetry consent; no private packet capture |
| **Performance profile** | measurement; URLLC latency profile where capable |
| **Onboarding text** | "Research mode active. Review telemetry consent before capturing data." |
| **Exit paths** | spaceship, workshop, offline (cached measurements) |

---

## 8. Spaceship Mode

**Purpose:** Advanced developer and researcher power tools — full control, nothing hidden.

| Field | Specification |
|-------|---------------|
| **Home screen layout** | Full app grid + system panels + advanced settings shortcut |
| **Allowed apps** | All registered apps except guardian-blocked; vscode, terminal, wsl_ubuntu, field_measurement, edge_io, steam, browser |
| **Blocked apps** | None by default (guardian/policy may override) |
| **Default accessibility** | All features available; user configures |
| **Recommended widgets** | system_monitor, git_status, measurement_status, telemetry_consent |
| **Data/privacy policy** | user-configurable; explicit consent required for telemetry |
| **Performance profile** | maximum; user controls power/thermal tradeoffs |
| **Onboarding text** | "Full control unlocked. Advanced settings are in the menu — use them when you're ready." |
| **Exit paths** | Any preset; reset_to_safe_defaults always available |

---

## 9. Guardian Mode

**Purpose:** Family safety and supervision — guardian overlay on youth-appropriate preset.

| Field | Specification |
|-------|---------------|
| **Home screen layout** | Youth preset layout (scooter/bicycle/car) + guardian badge; approved apps only |
| **Allowed apps** | Age-band approved list from guardian_controls; gunnchAI3k, WAIKE Offline, scaly_wings_edu, approved browser |
| **Blocked apps** | All non-approved apps; steam unless approved; social_placeholder; unrestricted terminal |
| **Default accessibility** | Inherited from underlying preset + kid_safe theme option |
| **Recommended widgets** | screen_time_remaining, approved_apps, ask_guardian |
| **Data/privacy policy** | strict; privacy-safe telemetry; no private content inspection; audit log placeholder |
| **Performance profile** | efficiency; enforce play windows |
| **Onboarding text** | "This device is set up with guardian controls. Ask a guardian to approve new apps." |
| **Exit paths** | scooter, bicycle, car (within guardian rules); guardian unlock for preset change |

---

## 10. Classroom Mode

**Purpose:** Teacher/mentor deployment — lesson push, student-safe defaults, fleet visibility.

| Field | Specification |
|-------|---------------|
| **Home screen layout** | teacher_console workspace; class roster widget; lesson deployment panel |
| **Allowed apps** | gunnchAI3k, WAIKE Offline, browser (school_safe), fleet_view_placeholder, assignment_placeholder |
| **Blocked apps** | steam, personal social, unrestricted developer tools on student devices |
| **Default accessibility** | classroom-wide a11y defaults; teacher can override per student |
| **Recommended widgets** | class_roster, lesson_status, offline_ready_indicator |
| **Data/privacy policy** | school_safe network; aggregate opt-in telemetry; no individual surveillance |
| **Performance profile** | balanced; batch lesson cache |
| **Onboarding text** | "Classroom mode ready. Deploy today's lesson to connected devices." |
| **Exit paths** | car, offline, guardian (student devices) |

---

## 11. Library Mode

**Purpose:** Shared public access — guest sessions, easy reset, community-friendly.

| Field | Specification |
|-------|---------------|
| **Home screen layout** | library_kiosk workspace; large "Start session" button; session timer |
| **Allowed apps** | browser (library filter), WAIKE Offline, gunnchAI3k, community_library_pack apps |
| **Blocked apps** | steam, vscode, terminal, personal cloud sync, edge_io |
| **Default accessibility** | large_text: true, high_contrast: available, simplified_language: true, keyboard_navigation: true |
| **Recommended widgets** | session_timer, help_desk, accessibility_shortcut |
| **Data/privacy policy** | strict; no persistent PII; session wipe on exit; guest profile only |
| **Performance profile** | efficiency; fast session reset |
| **Onboarding text** | "Welcome to the community device. Tap Start — your session resets when you leave." |
| **Exit paths** | offline; session_end (automatic reset) |

---

## 12. Offline Mode

**Purpose:** No or low internet — local-first workflows with deferred sync.

| Field | Specification |
|-------|---------------|
| **Home screen layout** | offline_backpack workspace; offline-capable apps only; sync status indicator |
| **Allowed apps** | waike_offline, gunnchai3k, write_placeholder, sketch_placeholder, vscode (local), scaly_wings_edu, music_notes_placeholder |
| **Blocked apps** | Cloud-dependent media; online-only social; streaming services |
| **Default accessibility** | Full offline a11y cache; all navigation modes enabled |
| **Recommended widgets** | offline_status, sync_queue, storage_available |
| **Data/privacy policy** | strict; no network calls; sync queue encrypted placeholder |
| **Performance profile** | efficiency; no background sync |
| **Onboarding text** | "You're offline. Everything here works without internet. Changes sync when you reconnect." |
| **Exit paths** | Previous preset when online; scooter, bicycle, car, studio (offline-capable subsets) |

---

## Preset transition rules

1. Users may always reach **Scooter** or **reset to safe defaults** from any preset.
2. **Guardian** overlays youth presets; cannot be bypassed without guardian unlock.
3. **Offline** may be entered from any preset when connectivity is lost (automatic) or chosen explicitly.
4. **Spaceship** requires `customization_depth: power_user` or explicit opt-in.
5. **Classroom** and **Library** are deployment presets — typically set by admin/teacher, not youth self-service.

---

## Configuration source

Preset definitions live in `config/journey_presets.yaml` and are loaded by `journey_preset_engine.py`. Accessibility defaults per preset are in `config/accessibility_defaults.yaml`.
