# Claim Boundary

Honest claims for the gunnchOS user-focused OS experience layer. This document defines what we say publicly versus what requires additional evidence.

**Status:** device OS alpha · user-focused OS experience layer · prototype OS package

---

## 1. What this is

gunnchOS, in this repository, is:

- A **user-focused OS experience layer** — profile-driven shell, launcher, and mode manager
- A **customization framework** — themes, layouts, widgets, profile import/export
- A **device OS alpha package** — data-driven personas, journey presets, app packs, workspaces
- A **prototype OS package** — demo scripts, validation, launcher mock extensions
- An **accessibility-first UX** design — WCAG/UDL aligned intent, not certified conformance
- A **Windows-first / WSL-compatible strategy** — documented pathway, not guaranteed on all platforms
- An **offline-first learning mode** — local lessons and creative work with sync placeholder

---

## 2. Allowed language

Use these phrases in README, product docs, demos, and PR descriptions:

| Phrase | Meaning |
|--------|---------|
| device OS alpha | Early experience layer; not shipping product |
| user-focused OS experience layer | Shell/customization above hardware/kernel |
| launcher and mode manager | App launching and journey preset switching |
| customization framework | Themes, layouts, profiles, import/export |
| profile-driven shell | Behavior driven by user profile and persona |
| workflow presets | Scooter through Spaceship journey modes |
| accessibility-first UX | Inclusive defaults; not certification claim |
| Windows-first / WSL-compatible strategy | Dev path documentation |
| offline-first learning mode | Local lessons/creative with deferred sync |
| prototype OS package | Research/alpha artifact |
| research prototype | Aligns with broader gunnchOS3k mission |
| mock guardian controls | Placeholder family safety — not production MDM |
| placeholder app | App slot defined; integration pending |

---

## 3. Forbidden language (unless proven)

Do **not** use these unless evidence exists in this repo and is linked:

| Forbidden claim | Why |
|-----------------|-----|
| finished OS | No shipping OS image that boots on target hardware |
| shipping OS | Not in manufacturing or retail pipeline |
| certified operating system | No formal OS certification |
| production MDM | guardian_controls.py is mock |
| complete secure boot | Secure boot is planning/docs only |
| enterprise-grade fleet management | Fleet features are prototype placeholders |
| DRM bypass | Media via official browser routes only |
| Netflix/Hulu support beyond official browser/app routes | No proprietary integration |
| Steam compatibility guarantee | steam_unavailable edge case exists |
| WCAG 2.1 AA certified | Design intent only; no audit |
| user-tested UX | No documented studies with real participants |
| COPPA/GDPR-K certified | Youth safety is mock defaults |
| commercial 6G / carrier AI-RAN | Research alignment only |
| FCC/CE/UL certified hardware | Hardware is prototype stage |
| manufacturing-ready | EVT/planning stage |

---

## 4. Claims with evidence today

| Claim | Evidence | Safe wording |
|-------|----------|--------------|
| Profile schema exists | `gunnchos_device_os/user_profile_schema.py` | "User profile schema defines persona, preset, and customization fields" |
| Persona engine exists | `gunnchos_device_os/persona_engine.py`, `config/personas.yaml` | "22 personas with onboarding routes" |
| Journey presets exist | `gunnchos_device_os/journey_preset_engine.py`, `config/journey_presets.yaml` | "12 workflow presets from Scooter to Spaceship" |
| Customization engine exists | `gunnchos_device_os/customization_engine.py` | "Theme, layout, and profile import/export" |
| Accessibility manager exists | `gunnchos_device_os/accessibility_manager.py` | "16 supported accessibility features" |
| Edge case policy exists | `gunnchos_device_os/edge_case_policy.py` | "24 edge cases with safe fallbacks" |
| Onboarding wizard exists | `gunnchos_device_os/onboarding_wizard.py` | "Seven-question first-run onboarding" |
| Demo scripts exist | `scripts/run_user_focused_os_demo.py` | "Demo simulates pre-K through postdoc flows" |
| CI smoke validation | `make test` / `pytest` | "Research prototype with CI smoke validation" |
| Launcher mock exists | `apps/launcher_mock/` | "Launcher mock exposes customization routes" |

---

## 5. Claims requiring future evidence

| Claim | Gap | Next evidence needed |
|-------|-----|----------------------|
| Real user testing | No participant studies | IRB-approved UX study with opt-in quotes |
| WCAG conformance | No formal audit | Third-party accessibility audit report |
| Production guardian controls | Mock implementation | Production MDM integration + security review |
| Offline sync production-ready | Placeholder conflict handling | Sync protocol spec + field test logs |
| WSL available on device | wsl_unavailable edge case | Windows device test log with WSL installed |
| Steam available on device | steam_unavailable edge case | Licensed Steam install test on target hardware |
| Shipping OS image | No bootable product image | Yocto/build pipeline + hardware boot log |
| Field deployment | Planned in ROADMAP | Partner MOU + deployment report |
| Zenodo DOI | Planned | Tag + Zenodo upload |

---

## 6. Synthetic and demo outputs

| Output type | Label required |
|-------------|----------------|
| `results/user_focused_os_demo_output.json` | Synthetic demo — not deployment proof |
| Guardian audit log | Placeholder |
| Collaboration share links | Placeholder |
| Sync conflict resolution | Placeholder |
| Remote wipe (lost device) | Placeholder |

All figures and JSON in `results/` must be labeled synthetic unless sourced from field data.

---

## 7. Scooter-to-spaceship principle (allowed)

This exact principle is approved for product docs:

> gunnchOS must scale from scooter to spaceship. The same device should support a child learning letters, a high school student writing essays, a musician recording ideas, an artist sketching, a gamer relaxing, a CS student coding, and a postdoctoral researcher running experiments.

It describes **design intent** for the experience layer, not a claim that all workflows are fully implemented today.

---

## 8. Per-document claim boundaries

| Document | Must not claim |
|----------|----------------|
| USER_FOCUSED_OS_PRD.md | finished shipping OS |
| PERSONA_MATRIX.md | user-tested persona validation |
| JOURNEY_PRESETS.md | all apps fully integrated |
| EDGE_CASE_REQUIREMENTS.md | all fallbacks user-tested |
| CUSTOMIZATION_REQUIREMENTS.md | visual themes production-polished |
| ACCESSIBILITY_REQUIREMENTS.md | WCAG certification |
| CREATOR_WORKFLOW_REQUIREMENTS.md | professional creative suite |
| YOUTH_AND_GUARDIAN_REQUIREMENTS.md | production parental controls |
| OFFLINE_FIRST_REQUIREMENTS.md | production sync |
| CLAIM_BOUNDARY.md | (this document defines boundaries) |

---

## 9. PR and README required disclaimer

Every public-facing summary must include:

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## 10. Validator enforcement

These scripts must fail if forbidden claims appear in user-facing docs without evidence:

- `scripts/validate_user_focused_os.py`
- `scripts/check_user_experience_files.py`

Forbidden patterns include: "finished OS", "shipping OS", "certified operating system", "production MDM", "WCAG certified", "user-tested UX" (without evidence link).

---

## 11. Related evidence documents

| Document | Path |
|----------|------|
| Claims to evidence (repo) | `CLAIMS_TO_EVIDENCE.md` |
| What is real today | `docs/WHAT_IS_REAL_TODAY.md` |
| Toy demo language audit | `quality/TOY_DEMO_LANGUAGE_AUDIT.md` |
| Evidence standard | `docs/EVIDENCE_STANDARD.md` |
| User experience claims (planned) | `docs/CLAIMS_TO_EVIDENCE_USER_EXPERIENCE.md` |
