# Youth and Guardian Requirements

Requirements for guardian controls, youth safety, and age-appropriate experiences in the gunnchOS user-focused OS experience layer.

**Status:** device OS alpha · mock guardian controls — not production MDM or certified youth safety product.

---

## 1. Goals

Youth users must have safe, age-appropriate defaults. Guardians must supervise without surveillance-by-default. The system must scale from pre-K through high school and transition cleanly to adult profiles.

---

## 2. Age bands

From `user_profile_schema.py`:

| Age band | Typical personas | Guardian default |
|----------|------------------|------------------|
| `pre_k` | pre_k_learner | Required |
| `elementary` | early_reader | Required |
| `middle_school` | middle_school_explorer | Recommended |
| `high_school` | high_school_student | Optional |
| `undergraduate` | college_* | Off |
| `graduate` | graduate_researcher | Off |
| `postdoc` | postdoctoral_researcher | Off |
| `adult` | parent_guardian, teacher, creators, engineers | Off |
| `senior` | accessibility-first (optional) | Configurable |

---

## 3. Guardian controls (mock)

Implemented in `guardian_controls.py`. **Marked mock: true** — not production MDM.

### 3.1 Age-band defaults

| Age band | Screen time (min/day) | Content filter | App approval required |
|----------|----------------------|----------------|----------------------|
| pre_k | 30 | strict | yes |
| elementary | 60 | strict | yes |
| middle_school | 90 | moderate | yes |
| high_school | 120 | moderate | no |
| undergraduate+ | none | light | no |

### 3.2 Control fields

| Control | Requirement |
|---------|-------------|
| `school_mode_restrictions` | Always true for youth age bands |
| `play_time_window` | Default 15:00–19:00 for pre_k through middle_school |
| `media_content_caution` | Maps to content_filter level |
| `app_approval_list` | Guardian must approve new apps when enabled |
| `privacy_safe_telemetry` | Aggregate only; no private content inspection |
| `private_content_inspection` | **Default false** — never inspect messages/files by default |
| `emergency_unlock_path` | guardian_pin_or_biometric |
| `audit_log` | Placeholder — log preset changes and app approvals |

### 3.3 Enable flow

`enable_guardian_controls(profile_id, age_band)` returns enabled controls with age-band defaults applied.

Onboarding question 6 ("Are guardian controls needed?") sets `guardian_required: true` and selects Guardian preset for pre_k/child.

---

## 4. Guardian Mode preset

See [JOURNEY_PRESETS.md](JOURNEY_PRESETS.md) — Guardian overlay:

- Youth sees underlying Scooter/Bicycle/Car layout with approved apps only
- Guardian dashboard workspace for parent_guardian persona
- Widgets: screen_time_remaining, approved_apps, ask_guardian
- Blocked: steam (unless approved), unrestricted browser, social_placeholder, terminal

---

## 5. Persona-specific safety requirements

| Persona | privacy_level | guardian_required | blocked_apps (typical) |
|---------|---------------|-------------------|------------------------|
| pre_k_learner | strict | true | browser, steam, terminal, social |
| early_reader | strict | true | steam, social, unrestricted browser |
| middle_school_explorer | strict | false (recommended) | steam (time-windowed), social |
| high_school_student | standard | false | none (school policy may apply) |
| parent_guardian | standard | n/a (supervisor) | n/a |
| gamer (youth) | standard | per age band | none in Arcade within play window |

---

## 6. Privacy and telemetry (youth)

| Requirement | Detail |
|-------------|--------|
| No private content inspection | Messages, files, browsing history not inspected by default |
| Privacy-safe telemetry | Aggregate opt-in only; no individual surveillance |
| Guardian consent | Telemetry for pre_k/elementary requires guardian consent |
| No biometric surveillance | Not enabled by default |
| Audit log | Placeholder for app approvals and preset changes — not full activity monitoring |

---

## 7. Content and app restrictions

| Category | Youth rule |
|----------|------------|
| Browser | school_safe filter in Guardian/Bicycle/Car |
| Games | Play time windows; steam requires approval for pre_k–middle_school |
| Social | social_placeholder blocked for pre_k, elementary |
| Developer tools | terminal, vscode restricted for pre_k, elementary |
| Research tools | edge_io, field_measurement blocked for youth unless educator override |
| Media | Official browser routes only; no DRM bypass claims |

---

## 8. Edge cases (youth/guardian)

| Case | Requirement |
|------|-------------|
| `guardian_lockout` | Lock preset changes after failed unlock attempts; emergency_unlock_path |
| `child_to_adult_switch` | Guided transition wizard; relax controls with guardian consent |
| `unsafe_app_request` | Show guardian approval path |
| `only_games` | Apply play windows for youth |
| `only_school` | Block games; enforce school_safe |
| `overwhelmed` | Simplify to Scooter — especially for young users |

---

## 9. Themes and accessibility (youth)

- `kid_safe` theme available in Guardian and youth presets
- large_text, simplified_language, reduced_motion defaults in Scooter
- Captions default on for media
- No alarming error colors in youth UI

---

## 10. Transition: child to adult

When age band upgrades or guardian releases controls:

1. Run transition wizard (onboarding subset)
2. Suggest preset upgrade: Scooter → Bicycle → Car
3. Migrate apps and files; preserve creative work
4. Relax screen time and app approval gradually
5. Log transition in audit_log placeholder
6. Trigger `child_to_adult_switch` edge case handler

---

## 11. Teacher/classroom integration

Classroom Mode complements guardian controls:

- Teacher deploys lessons with student-safe defaults
- Fleet visibility placeholder — aggregate, not individual surveillance
- Student devices may inherit classroom policy overlay
- Exit to Car or Offline for homework

---

## 12. Demo requirements

Demo must simulate:

- Guardian enabling controls for youth profile
- Pre-K learner in Scooter with guardian overlay
- Screen time widget visible in Guardian preset

---

## 13. Validation rules

Validators must fail if:

- pre_k_learner or early_reader lacks guardian_required: true
- private_content_inspection defaults to true
- Guardian preset allows unrestricted terminal for pre_k/elementary
- Docs claim production MDM or certified youth safety

---

## 14. Claim boundary

**Allowed:** mock guardian controls · age-band defaults · privacy-safe telemetry intent · youth preset restrictions

**Not claimed:** production MDM · COPPA/GDPR-K certification · real-time content moderation · certified parental control product

See [CLAIM_BOUNDARY.md](CLAIM_BOUNDARY.md).
