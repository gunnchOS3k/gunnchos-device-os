# Creator Workflow Requirements

Requirements for artist, writer, musician, and related creative workflows in the gunnchOS user-focused OS experience layer.

**Status:** device OS alpha · creator mode manager — placeholder apps where real integrations are not yet wired.

---

## 1. Goals

The same device that teaches letters must also support serious creative work. Creator workflows provide:

- Focused workspace layouts (Studio preset)
- Curated app packs with beginner-friendly descriptions
- File templates for immediate start
- Export formats for sharing
- Offline support where feasible
- Collaboration placeholders for future integration

---

## 2. Supported creator modes

Defined in `creator_mode_manager.py` → `CREATOR_WORKFLOWS`:

| Mode | Default workspace | App pack | Primary persona |
|------|-----------------|----------|-----------------|
| Artist | art_table | art_pack | artist |
| Writer | essay_studio | write_pack | writer |
| Musician | music_studio | music_pack | musician |
| Video creator | art_table | art_pack | artist (extended) |
| Game designer | coding_lab | game_dev_pack | game_developer |
| Photographer | art_table | art_pack | artist (extended) |
| Streamer | game_room | game_pack | gamer (placeholder) |

---

## 3. Per-workflow requirements

### 3.1 Artist

| Field | Requirement |
|-------|-------------|
| Default workspace | `art_table` — canvas center, tools sidebar |
| App pack | `art_pack` — sketch_placeholder, palette_placeholder |
| File templates | `sketch.canvas`, `palette.gpalette` |
| Export formats | PNG, SVG, PDF |
| Collaboration | share_link_placeholder |
| Offline support | **Required** — full sketch and export offline |
| Journey preset | Studio |
| Theme | artist_canvas |
| Success moment | Save first sketch and export shareable PNG |

### 3.2 Writer

| Field | Requirement |
|-------|-------------|
| Default workspace | `essay_studio` — distraction-free editor center |
| App pack | `write_pack` — write_placeholder |
| File templates | `essay.md`, `outline.md` |
| Export formats | MD, DOCX, PDF |
| Collaboration | comment_placeholder |
| Offline support | **Required** — full writing offline with sync |
| Journey preset | Studio |
| Theme | writer_focus |
| Success moment | Complete draft in focus_mode without distraction |

### 3.3 Musician

| Field | Requirement |
|-------|-------------|
| Default workspace | `music_studio` — timeline/notes center, instruments sidebar |
| App pack | `music_pack` — music_notes_placeholder |
| File templates | `song.project`, `notes.txt` |
| Export formats | WAV, MP3, MIDI |
| Collaboration | jam_session_placeholder |
| Offline support | **Required** — record and save ideas offline |
| Journey preset | Studio |
| Theme | musician_studio |
| Success moment | Record idea and save project offline |

### 3.4 Video creator

| Field | Requirement |
|-------|-------------|
| Default workspace | `art_table` (adapted for storyboard) |
| App pack | `art_pack` |
| File templates | `storyboard.md`, `clip.project` |
| Export formats | MP4, WebM |
| Collaboration | review_link_placeholder |
| Offline support | **Not required** — document dependency; graceful degrade |
| Journey preset | Studio |
| Success moment | Complete storyboard and export clip placeholder |

### 3.5 Game designer

| Field | Requirement |
|-------|-------------|
| Default workspace | `coding_lab` |
| App pack | `game_dev_pack` — level_editor_placeholder, vscode |
| File templates | `game.design`, `level.tmx` |
| Export formats | JSON, ZIP |
| Collaboration | playtest_placeholder |
| Offline support | **Required** — design and local playtest offline |
| Journey preset | Workshop |
| Success moment | Build and playtest level offline |

### 3.6 Photographer

| Field | Requirement |
|-------|-------------|
| Default workspace | `art_table` (gallery view) |
| App pack | `art_pack` |
| File templates | `album.album` |
| Export formats | JPG, RAW, PNG |
| Collaboration | gallery_placeholder |
| Offline support | **Required** — organize and export offline |
| Journey preset | Studio |
| Success moment | Organize album and export selected images |

### 3.7 Streamer (placeholder)

| Field | Requirement |
|-------|-------------|
| Default workspace | `game_room` |
| App pack | `game_pack` |
| File templates | `stream.overlay` |
| Export formats | MP4 |
| Collaboration | chat_moderation_placeholder |
| Offline support | **Not required** — document as online-dependent |
| Journey preset | Arcade |
| Success moment | Configure overlay placeholder (future) |

---

## 4. Workspace requirements (creator)

Each creator workspace in `config/workspaces.yaml` must define:

| Field | Requirement |
|-------|-------------|
| `app_layout` | Ordered list of apps visible in workspace |
| `widgets` | At least one widget (e.g., recent_projects) |
| `files_folders` | Default project folder paths |
| `quick_actions` | **Non-empty** — e.g., "New sketch", "Export", "Save" |
| `focus_settings` | Distraction reduction options |
| `save_export_flow` | Plain-language description of save/export steps |

---

## 5. App pack requirements (creator)

Creator app packs in `config/app_packs.yaml`:

| Pack | Apps | Offline | Privacy warning |
|------|------|---------|-----------------|
| art_pack | sketch_placeholder, palette_placeholder | true | null |
| write_pack | write_placeholder | true | null |
| music_pack | music_notes_placeholder | true | null |
| game_dev_pack | level_editor_placeholder, vscode | true | null |

Each pack must include: `why_it_exists`, `required_mode`, `beginner_friendly_description`, `compatible_modes`.

---

## 6. Studio preset integration

Studio Mode (see [JOURNEY_PRESETS.md](JOURNEY_PRESETS.md)) is the default journey preset for artist, writer, musician personas:

- Allowed apps: creative placeholders + reference browser
- Blocked apps: steam, edgegesture (reduce distraction)
- focus_mode available by default
- Performance profile: creative — prioritize input latency
- Exit path to Arcade for break sessions

---

## 7. Onboarding integration

Onboarding question 7 ("learning, creating, playing, working, researching, or all") maps `create` → Studio preset.

Creator personas receive:

- Correct default_app_pack and default_workspace from personas.yaml
- Studio preset unless user selects power_user → may start in Workshop (game designer)
- Recommended widgets: recent_projects, export_shortcut

---

## 8. Edge cases (creator-specific)

| Case | Behavior |
|------|----------|
| Storage almost full | Prompt save/export before new project |
| Offline | Creator workflows with offline_support=true continue; others show message |
| Overwhelmed | Fall back to Scooter; preserve project files |
| No AI | Creative apps unaffected; gunnchAI3k tutor hidden only |

---

## 9. Demo requirements

`run_user_focused_os_demo.py` must simulate:

1. Writer entering Studio / essay_studio
2. Musician entering music_studio
3. Artist entering art_table

Demo output JSON must include workspace details, app pack, and export format list.

---

## 10. Claim boundary

**Allowed:** creator workflow modeling · file templates · export format specification · offline-first creative intent

**Not claimed:** professional-grade DAW/NLE/IDE replacement · cloud collaboration production-ready · user-tested creator UX

See [CLAIM_BOUNDARY.md](CLAIM_BOUNDARY.md).
