# User Experience Requirements

**Status:** user-focused alpha exists · production shell **not proven**

> UX requirements for shippable gunnchOS. Evidence: launcher mock, user-focused demo, `docs/LAUNCHER_NAVIGATION_MODEL.md`.

---

## Core model: scooter → spaceship

Users start with simple presets (Scooter Mode) and can grow into advanced workspaces (Spaceship / Laboratory). Both paths must remain valid — no forced expert UI.

---

## Navigation requirements

| Requirement | Description |
|-------------|-------------|
| One clear primary action per screen | Single dominant CTA; secondary actions de-emphasized |
| Beginner and expert paths | "More control" reveals advanced settings |
| No dead-end screens | Every screen offers back, home, or help |
| Reversible destructive actions | Confirm + undo window where feasible |
| Human-readable errors | No raw error codes without explanation |
| Advanced settings hidden | Behind "More control" or admin mode |
| First-run wizard | Persona → preset → accessibility → guardian (if child) |
| Profile import/export | JSON or signed bundle; validate schema |
| Safe reset | Profile reset without full factory unless chosen |
| Persona/preset migration | Upgrade preserves preset mappings across versions |

---

## Personas (minimum coverage)

From user-focused demo — all must remain reachable post-install:

- Pre-K learner (Scooter)
- High school student (Car)
- Writer (Studio)
- Musician (Music Studio)
- Artist (Art Table)
- Gamer (Arcade)
- CS student (Workshop)
- Researcher (Laboratory / Spaceship)
- Guardian controls operator
- Offline library user
- Accessibility-first user

---

## Mode and preset coherence

- Preset selection sets default app packs, accessibility, and mode policy
- Mode transitions follow `docs/MODE_TRANSITION_RULES.md`
- Guardian blocks surfaced in plain language

---

## Evidence

| Artifact | Status |
|----------|--------|
| `results/user_focused_os_demo_output.json` | 11 scenarios |
| `apps/launcher_mock/` user-focused route | prototype |
| `scripts/run_user_focused_os_demo.py` | CI-generated |

---

## QA linkage

[../qa/USER_ACCEPTANCE_TEST_PLAN.md](../qa/USER_ACCEPTANCE_TEST_PLAN.md) exercises UX scenarios per persona.

---

## Claim boundary

UX requirements describe target experience. Launcher mock is not a finished shipping OS shell.
