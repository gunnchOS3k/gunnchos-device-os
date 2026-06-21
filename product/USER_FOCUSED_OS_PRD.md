# User-Focused OS Experience Layer — Product Requirements

**Status:** device OS alpha · user-focused OS experience layer · prototype OS package  
**Not claimed:** finished shipping OS · certified operating system · production MDM

---

## 1. Purpose

gunnchOS is a **user-focused OS experience layer** for gunnchOS devices. It sits above hardware and kernel concerns as a **profile-driven shell**, **launcher and mode manager**, and **customization framework** that adapts the same physical device to many human needs.

This PRD defines what the experience layer must do for real people — from first-time learners to postdoctoral researchers — without claiming a finished shipping OS image.

---

## 2. Core principle

> gunnchOS must scale from scooter to spaceship. The same device should support a child learning letters, a high school student writing essays, a musician recording ideas, an artist sketching, a gamer relaxing, a CS student coding, and a postdoctoral researcher running experiments.

**Scooter** = minimum complexity, one-tap paths, no forced settings.  
**Spaceship** = full power-user control, deep settings, advanced tools — chosen, not imposed.

---

## 3. Experience surfaces

The user-focused OS experience layer must support eight primary surfaces on the same device:

| Surface | Who it serves | What it feels like |
|---------|---------------|-------------------|
| **Friendly shell** | First-time users, pre-K learners, overwhelmed users | Large targets, plain words, one primary action per screen |
| **Creative workstation** | Artists, writers, musicians, video creators | Studio layout, file templates, export flows, focus mode |
| **Study station** | Pre-K through postdoc learners | Lessons, essays, research reading, tutor access, school-safe defaults |
| **Game console** | Gamers, casual play, educational games | Controller-first, arcade layout, parental time windows |
| **Dev station** | CS students, software engineers, game developers | Coding lab, terminal, VS Code, WSL-compatible strategy |
| **Research terminal** | Graduate/postdoc researchers, wireless/6G experimenters | Measurement tools, edge-io bridge, telemetry consent, lab workspace |
| **Community access** | Libraries, schools, shared kiosks | Library mode, guest profiles, privacy-safe session reset |
| **Customizable personal device** | Everyone | Themes, layouts, widgets, profile import/export, growth over time |

---

## 4. Journey presets (scooter → spaceship)

Users enter through **workflow presets** — data-driven modes, not hard-coded UI only:

| Preset | Complexity | Primary use |
|--------|------------|-------------|
| Scooter | Minimum | First tap, pre-readers, accessibility-first |
| Bicycle | Guided | Early exploration, middle school |
| Car | Productivity | High school and college daily work |
| Studio | Creative | Art, writing, music |
| Arcade | Recreation | Games and media |
| Workshop | Maker/dev | Coding, hardware, game dev, cybersecurity |
| Laboratory | Research | Field measurement, experiments |
| Spaceship | Power user | Full developer/researcher control |
| Guardian | Safety | Family supervision |
| Classroom | Deployment | Teacher/mentor fleet view |
| Library | Shared access | Public/community kiosk |
| Offline | Disconnected | Low/no bandwidth |

See [JOURNEY_PRESETS.md](JOURNEY_PRESETS.md) for full preset specifications.

---

## 5. Persona coverage

The experience layer must provide an onboarding route for every persona in [PERSONA_MATRIX.md](PERSONA_MATRIX.md):

- Pre-K learner through postdoctoral researcher
- Parents, teachers, community library users
- Creators (artist, writer, musician)
- Gamers and game developers
- Software, hardware, and cybersecurity learners
- Wireless/6G researchers
- Accessibility-first and low-bandwidth/offline users

No persona may be left without a default journey preset, app pack, workspace, and safe fallback.

---

## 6. Customization depth

Users choose how much control they want:

| Depth | Settings view | Typical user |
|-------|---------------|--------------|
| `simple` | Essential choices only | Scooter, pre-K, first-time |
| `guided` | Step-by-step with explanations | Bicycle, middle school |
| `full` | All common settings visible | Car, Studio, most adults |
| `power_user` | Advanced panels, export/import | Spaceship, Workshop |

Customization includes: theme, font scale, contrast, home layout, pinned apps, widgets, input method, profile export/import, reset to safe defaults.

See [CUSTOMIZATION_REQUIREMENTS.md](CUSTOMIZATION_REQUIREMENTS.md).

---

## 7. Accessibility-first UX

All surfaces must be designed for perceivable, operable, understandable, and robust interaction. Defaults vary by journey preset; users may override.

Supported features: keyboard, controller, and touch navigation; screen reader labels; captions; reduced motion; high contrast; large text; simplified language; focus mode; color-safe mode; audio/haptic cues; one-hand mode; switch access (placeholder); voice input (placeholder).

See [ACCESSIBILITY_REQUIREMENTS.md](ACCESSIBILITY_REQUIREMENTS.md).

---

## 8. Youth and guardian

Guardian controls apply age-band defaults: screen time, content filters, app approval, school-mode restrictions, play windows, privacy-safe telemetry, no private content inspection by default, emergency unlock path.

See [YOUTH_AND_GUARDIAN_REQUIREMENTS.md](YOUTH_AND_GUARDIAN_REQUIREMENTS.md).

---

## 9. Offline-first learning mode

Offline capabilities include lessons, writing, sketching, coding templates, music notes, and licensed offline games. Sync when online with conflict handling placeholder.

See [OFFLINE_FIRST_REQUIREMENTS.md](OFFLINE_FIRST_REQUIREMENTS.md).

---

## 10. Creator workflows

Dedicated workflows for artist, writer, musician, video creator, game designer, photographer, and streamer (placeholder). Each defines workspace, app pack, templates, export formats, collaboration placeholders, and offline support.

See [CREATOR_WORKFLOW_REQUIREMENTS.md](CREATOR_WORKFLOW_REQUIREMENTS.md).

---

## 11. Edge cases and safe fallbacks

Every exceptional situation must produce a user-friendly message, safe fallback preset, technical log entry, and next action.

See [EDGE_CASE_REQUIREMENTS.md](EDGE_CASE_REQUIREMENTS.md).

---

## 12. Architecture (alpha)

```
User profile (persona, age band, skill level)
    → Persona engine (recommend preset, apps, safety, a11y)
    → Journey preset engine (layout, allowed/blocked apps, privacy, performance)
    → Customization engine (theme, layout, widgets, import/export)
    → Workspace manager (focused task layouts)
    → App pack manager (curated bundles)
    → Edge case policy (safe fallbacks)
```

Configuration is data-driven via YAML in `config/` (personas, journey presets, app packs, themes, workspaces, accessibility defaults, edge cases).

---

## 13. Success criteria (alpha)

1. Every persona maps to a journey preset, app pack, and workspace.
2. Onboarding wizard produces valid profile JSON from seven first-run questions.
3. Demo simulates pre-K through postdoc, creator, gamer, guardian, offline, and accessibility-first flows.
4. Validation scripts pass without claiming user-tested UX or shipping OS.
5. README and docs use allowed language only.

---

## 14. Claim boundary

See [CLAIM_BOUNDARY.md](CLAIM_BOUNDARY.md).

**Allowed:** device OS alpha · user-focused OS experience layer · launcher and mode manager · customization framework · profile-driven shell · workflow presets · accessibility-first UX · Windows-first / WSL-compatible strategy · offline-first learning mode · prototype OS package

**Forbidden unless proven:** finished OS · shipping OS · certified operating system · production MDM · complete secure boot · enterprise-grade fleet management · DRM bypass · Netflix/Hulu support beyond official browser/app routes · Steam compatibility guarantee

---

## 15. Related documents

| Document | Scope |
|----------|-------|
| [PERSONA_MATRIX.md](PERSONA_MATRIX.md) | All 22 personas |
| [JOURNEY_PRESETS.md](JOURNEY_PRESETS.md) | All 12 presets |
| [EDGE_CASE_REQUIREMENTS.md](EDGE_CASE_REQUIREMENTS.md) | Safe fallbacks |
| [CUSTOMIZATION_REQUIREMENTS.md](CUSTOMIZATION_REQUIREMENTS.md) | Themes, layout, profiles |
| [ACCESSIBILITY_REQUIREMENTS.md](ACCESSIBILITY_REQUIREMENTS.md) | WCAG/UDL alignment |
| [CREATOR_WORKFLOW_REQUIREMENTS.md](CREATOR_WORKFLOW_REQUIREMENTS.md) | Creative workflows |
| [YOUTH_AND_GUARDIAN_REQUIREMENTS.md](YOUTH_AND_GUARDIAN_REQUIREMENTS.md) | Family safety |
| [OFFLINE_FIRST_REQUIREMENTS.md](OFFLINE_FIRST_REQUIREMENTS.md) | Disconnected use |
| [CLAIM_BOUNDARY.md](CLAIM_BOUNDARY.md) | Honest claims |
