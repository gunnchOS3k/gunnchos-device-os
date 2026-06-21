# Creator Workflow Walkthrough

**Audience:** Artists, writers, musicians, education partners  
**Duration:** ~12 minutes  
**Status:** workflow demo with placeholder apps  

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

**Not claimed:** professional creative suite or industry-standard tool parity.

---

## Overview

Creator modes use **Studio** journey preset + task workspaces + app packs. Module: `gunnchos_device_os/creator_mode_manager.py`.

---

## Prerequisites

```bash
PYTHONPATH=. python3 scripts/run_user_focused_os_demo.py
```

Scenarios: `writer_studio`, `musician_studio`, `artist_art_table`.

---

## Walkthrough A — Writer

### Setup

| Item | Value |
|------|-------|
| Persona | writer |
| Preset | studio |
| Workspace | essay_studio |
| Pack | write_pack |
| Theme | writer_focus |

### Steps (presenter)

1. Show creator_workflow in demo JSON for writer.
2. Open `config/workspaces.yaml` entry for essay_studio — quick_actions: new_essay, focus_mode, export.
3. Enable focus_mode via accessibility defaults.
4. Explain offline_writing capability — autosave local, sync placeholder.

### Simulated session

> "Alex opens essay_studio. The home grid hides games. focus_mode dims extra chrome. Alex writes essay.md offline. Export to PDF is stubbed but documented."

**Success moment:** Draft in focus_mode without distraction.

**Honest boundary:** write_placeholder is not a shipped word processor.

---

## Walkthrough B — Artist

### Setup

| Item | Value |
|------|-------|
| Persona | artist |
| Workspace | art_table |
| Pack | art_pack |
| Theme | artist_canvas |

### Steps

1. Scenario `artist_art_table`.
2. Templates: sketch.canvas, palette.gpalette (documented).
3. Export formats: PNG, SVG, PDF.
4. offline_sketching capability.

### Simulated session

> "Casey opens art_table — canvas center, tools left. Sketch saves locally. Export PNG for sharing."

**Boundary:** sketch_placeholder — no binary art app in repo.

---

## Walkthrough C — Musician

### Setup

| Item | Value |
|------|-------|
| Persona | musician |
| Workspace | music_studio |
| Pack | music_pack |
| Theme | musician_studio |

### Steps

1. Scenario `musician_studio`.
2. Templates: song.project, notes.txt.
3. Export: WAV, MP3, MIDI (requirements only).
4. offline_music capability.

### Simulated session

> "Riley records a humming idea into music_notes_placeholder. Project saves offline on the bus."

**Boundary:** Not a DAW — notes/recording stub.

---

## Walkthrough D — Game designer (bonus)

| Item | Value |
|------|-------|
| Persona | game_developer |
| Preset | workshop |
| Workspace | coding_lab |
| Pack | game_dev_pack |

Offline project + local playtest — level_editor_placeholder.

---

## Policy notes

Studio preset **blocks** steam and distraction apps by default.

Creative files: **local-first** — no cloud upload without consent.

Youth creators inherit guardian overlay if guardian_required.

---

## API peek

```python
from gunnchos_device_os.creator_mode_manager import get_creator_workflow
from gunnchos_device_os.workspace_manager import get_workspace

print(get_creator_workflow("writer"))
print(get_workspace("essay_studio"))
```

---

## Comparison table

| Mode | Workspace | Offline | Export (documented) |
|------|-----------|---------|---------------------|
| Writer | essay_studio | yes | MD, DOCX, PDF |
| Artist | art_table | yes | PNG, SVG, PDF |
| Musician | music_studio | yes | WAV, MP3, MIDI |
| Game dev | coding_lab | yes | build artifacts |

---

## Presenter checklist

- [ ] Said Studio preset name
- [ ] Named placeholders explicitly
- [ ] Did not claim professional creative suite
- [ ] Mentioned offline intent + sync placeholder

---

## Related docs

- `docs/CREATOR_MODES.md`
- `docs/APP_PACKS_AND_WORKSPACES.md`
- `product/CREATOR_WORKFLOW_REQUIREMENTS.md`
- [persona_demo_transcripts.md](persona_demo_transcripts.md) — Alex, Casey, Riley scripts
