# Creator Modes

**Status:** device OS alpha · creator mode manager — placeholder apps where integrations are pending  

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## 1. Purpose

The same device that teaches letters must support **serious creative work**. Creator modes bundle workspace layout, app pack, templates, export formats, and offline expectations for artists, writers, musicians, and related personas.

**Not claimed:** professional creative suite, DAW-grade audio, or industry-standard design tool parity.

---

## 2. Supported creator workflows

**Module:** `gunnchos_device_os/creator_mode_manager.py`  
**Requirements:** `product/CREATOR_WORKFLOW_REQUIREMENTS.md`

| Creator mode | Workspace | App pack | Primary persona | Journey preset |
|--------------|-----------|----------|-----------------|----------------|
| Artist | art_table | art_pack | artist | Studio |
| Writer | essay_studio | write_pack | writer | Studio |
| Musician | music_studio | music_pack | musician | Studio |
| Video creator | art_table | art_pack | artist (extended) | Studio |
| Game designer | coding_lab | game_dev_pack | game_developer | Workshop |
| Photographer | art_table | art_pack | artist (extended) | Studio |
| Streamer | game_room | game_pack | gamer (placeholder) | Arcade |

---

## 3. Artist workflow

| Aspect | Specification |
|--------|---------------|
| Layout | Canvas center, tools sidebar (art_table) |
| Apps | sketch_placeholder, palette_placeholder, browser (reference) |
| Templates | sketch.canvas, palette.gpalette |
| Export | PNG, SVG, PDF (documented; stub implementation) |
| Theme | artist_canvas |
| Offline | **Required** — full sketch and export offline |
| Success moment | Save first sketch; export shareable PNG |

**Gap:** No real drawing binary; placeholder IDs in app_packs.yaml.

---

## 4. Writer workflow

| Aspect | Specification |
|--------|---------------|
| Layout | Distraction-free editor center (essay_studio) |
| Apps | write_placeholder, gunnchAI3k (outline help), browser |
| Templates | essay.md, outline.md |
| Export | MD, DOCX, PDF |
| Theme | writer_focus |
| Accessibility | focus_mode recommended |
| Offline | **Required** — autosave local; sync placeholder |
| Success moment | Complete draft in focus_mode without distraction |

**Gap:** write_placeholder vs placeholder_writer naming in app_packs.yaml.

---

## 5. Musician workflow

| Aspect | Specification |
|--------|---------------|
| Layout | Timeline/notes center, instruments sidebar (music_studio) |
| Apps | music_notes_placeholder |
| Templates | song.project, notes.txt |
| Export | WAV, MP3, MIDI |
| Theme | musician_studio |
| Offline | **Required** — record and save ideas offline |
| Success moment | Record idea and save project offline |

**Gap:** No audio engine; export formats are requirements only.

---

## 6. Extended creator modes

### Video creator / photographer

Reuse art_table + art_pack with export emphasis on video/image formats (documented in CREATOR_WORKFLOW_REQUIREMENTS).

### Game designer

Workshop preset + game_dev_pack + coding_lab workspace. Links to vscode, level_editor_placeholder.

### Streamer (placeholder)

Arcade/game_room layout — **not** a streaming platform integration. Browser-route policy only for platforms.

---

## 7. User journey (writer example)

1. Onboarding: who=writer or goal=create → Studio preset.
2. Persona engine assigns write_pack + essay_studio.
3. CustomizationEngine applies writer_focus theme.
4. focus_mode enabled via accessibility defaults.
5. User opens write_placeholder → local template essay.md.
6. Offline autosave via offline_mode_manager capability `offline_writing`.
7. Export (stub) → MD/PDF when user chooses share.

Demo: `scripts/run_user_focused_os_demo.py` scenario `writer_studio`.

---

## 8. Collaboration placeholders

| Feature | Status |
|---------|--------|
| share_link_placeholder | Documented only |
| comment_placeholder | Documented only |
| jam_session_placeholder | Documented only |

**Not claimed:** real-time co-editing or cloud sync.

---

## 9. Policy and safety

- Studio preset blocks steam, edgegesture, fleet_admin by default.
- Creative files local-first; no cloud upload without consent.
- Youth creators inherit guardian overlay if guardian_required.

---

## 10. Evidence and gaps

| Claim | Evidence | Gap |
|-------|----------|-----|
| Creator workflows defined | creator_mode_manager.py | No real apps |
| Studio preset configured | journey_presets.yaml | Mock UI |
| Offline creative required | OFFLINE_FIRST_REQUIREMENTS | Local save stub |
| Demo scenarios | run_user_focused_os_demo.py | Synthetic JSON only |

---

## 11. Related documents

- [APP_PACKS_AND_WORKSPACES.md](APP_PACKS_AND_WORKSPACES.md)
- [OFFLINE_FIRST_USER_EXPERIENCE.md](OFFLINE_FIRST_USER_EXPERIENCE.md)
- [CUSTOMIZATION_SYSTEM.md](CUSTOMIZATION_SYSTEM.md)
- `demo/creator_workflow_walkthrough.md`
