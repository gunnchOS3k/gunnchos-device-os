# Persona Demo Transcripts

**Status:** presenter scripts for synthetic demos — not quotes from real users  

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

Each transcript pairs a **persona** with narrator lines and expected demo output. Run demo first:

```bash
PYTHONPATH=. python3 scripts/run_user_focused_os_demo.py
```

---

## 1. Pre-K learner — Sam (`pre_k_scooter`)

**Narrator:** "Sam is four. The device opens in Scooter mode — big pictures, no browser."

**Onboarding copy (from personas.yaml):** "Let's explore colors, sounds, and stories together — tap a big picture to begin."

**Presenter actions:**

1. Show scenario `pre_k_scooter` in demo JSON.
2. Point to `journey_preset.allowed_apps`: waike_offline, scaly_wings_edu.
3. Note `guardian_required: true`.

**Simulated user line:** "I tap the story. It reads to me."

**Success moment:** First letter activity without help.

**Boundary:** "Guardian controls are mock — not production parental controls."

---

## 2. High school student — Jordan (`high_school_car`)

**Narrator:** "Jordan needs homework, an essay, and coding club — Car mode is the study station."

**Presenter actions:**

1. Scenario `high_school_car`.
2. Preset `car`: homework widget, vscode allowed, steam time-windowed.
3. Contrast with School EVT mode blocking steam.

**Simulated user line:** "I pinned WAIKE and VS Code. Steam works after 3 PM."

**Success moment:** Essay submitted and coding project opened same session.

---

## 3. Writer — Alex (`writer_studio`)

**Narrator:** "Alex writes in Studio mode — essay_studio workspace, focus theme."

**Presenter actions:**

1. Scenario `writer_studio` + `creator_workflow` block.
2. Show write_pack, focus_mode in a11y defaults.
3. Acknowledge write_placeholder — no real editor binary.

**Simulated user line:** "The screen is calm. I don't see game icons."

**Success moment:** Draft completed in focus mode.

---

## 4. Musician — Riley (`musician_studio`)

**Narrator:** "Riley captures a melody idea offline."

**Presenter actions:**

1. Scenario `musician_studio`.
2. Workspace `music_studio`, music_pack.
3. offline capability `offline_music`.

**Simulated user line:** "I hum into notes and save — Wi-Fi is out."

**Success moment:** Idea saved offline.

**Boundary:** "No DAW — music_notes_placeholder only."

---

## 5. Artist — Casey (`artist_art_table`)

**Narrator:** "Casey sketches at art_table with artist_canvas theme."

**Presenter actions:**

1. Scenario `artist_art_table`.
2. art_pack, export formats PNG/SVG documented.

**Simulated user line:** "Export gives me a PNG to share."

---

## 6. Gamer — Taylor (`gamer_arcade`)

**Narrator:** "Taylor relaxes in Arcade — controller-first."

**Presenter actions:**

1. Scenario `gamer_arcade`.
2. Allowed: steam, scaly_wings, edgegesture.
3. Mention steam_unavailable edge case honestly.

**Simulated user line:** "One tap and my controller works."

**Boundary:** "No Steam compatibility guarantee on all hardware."

---

## 7. CS student — Morgan (`cs_workshop`)

**Narrator:** "Morgan codes in Workshop — VS Code, terminal, WSL path."

**Presenter actions:**

1. Scenario `cs_workshop`.
2. coding_pack / workshop preset.
3. wsl_unavailable fallback if WSL not installed.

**Simulated user line:** "I commit locally and sync later."

---

## 8. Postdoc researcher — Dr. Lee (`researcher_laboratory_spaceship`)

**Narrator:** "Dr. Lee runs experiments — Laboratory for capture, Spaceship for tooling."

**Presenter actions:**

1. Scenario `researcher_laboratory_spaceship`.
2. Show `laboratory_preset` block + spaceship profile.
3. Telemetry: research opt-in only.

**Simulated user line:** "I know exactly what exports to edge-io."

**Success moment:** Custom pipeline export (mock).

---

## 9. Guardian setup (`guardian_controls`)

**Narrator:** "A parent configures screen time and app approval."

**Presenter actions:**

1. Scenario `guardian_controls`.
2. Read `"mock": true` aloud.
3. private_content_inspection: false.

**Simulated guardian line:** "I approve Scaly Wings Edu. I don't read Sam's stories."

---

## 10. Library guest — Pat (`offline_library`)

**Narrator:** "Pat uses a community device offline — no account needed."

**Presenter actions:**

1. Scenario `offline_library` + `offline_mode` block.
2. library_community_user persona, offline_backpack workspace.

**Simulated user line:** "I finished browsing WAIKE lessons. I log out — next person gets a clean device."

---

## 11. Accessibility-first — Jordan A (`accessibility_first`)

**Narrator:** "Jordan A uses high contrast, large text, reduced motion."

**Presenter actions:**

1. Scenario `accessibility_first`.
2. Show `accessibility_settings` and `theme_applied` in JSON.

**Simulated user line:** "I can read every button without straining."

**Boundary:** "Not WCAG certified — design intent with AT testing planned."

---

## 12. Onboarding sample (`onboarding_sample`)

**Narrator:** "Any persona can start from seven questions."

**Presenter actions:**

1. Read `onboarding_sample` from demo root JSON.
2. Show resulting UserProfile fields.

---

## Quick reference table

| Scenario key | Persona | Preset |
|--------------|---------|--------|
| pre_k_scooter | pre_k_learner | scooter |
| high_school_car | high_school_student | car |
| writer_studio | writer | studio |
| musician_studio | musician | studio |
| artist_art_table | artist | studio |
| gamer_arcade | gamer | arcade |
| cs_workshop | college_cs_stem_student | workshop |
| researcher_laboratory_spaceship | postdoctoral_researcher | spaceship |
| guardian_controls | (guardian) | guardian |
| offline_library | library_community_user | offline |
| accessibility_first | accessibility_first_user | car + a11y |

Full matrix: `product/PERSONA_MATRIX.md`.

---

## Related docs

- [user_focused_os_walkthrough.md](user_focused_os_walkthrough.md)
- [scooter_to_spaceship_walkthrough.md](scooter_to_spaceship_walkthrough.md)
- `docs/PREK_TO_POSTDOC_USE_CASES.md`
