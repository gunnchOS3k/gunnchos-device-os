# Guardian and Youth Safety

**Status:** device OS alpha · mock guardian controls — not production MDM or COPPA/GDPR-K certified  

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## 1. Goals

- Youth users get **age-appropriate defaults** without surveillance-by-default.
- Guardians **supervise** (time, apps, content level) without reading private messages or inspecting creative files by default.
- System scales from **pre-K through high school** and transitions cleanly to adult profiles.

**Not claimed:** production parental controls, certified youth safety product, or legal compliance review.

---

## 2. Three related concepts

| Concept | Module / config | Purpose |
|---------|-----------------|---------|
| **Guardian preset** | journey_presets.yaml `guardian` | UX mode emphasizing supervision tools |
| **Guardian controls** | guardian_controls.py | Age-band defaults (mock: true) |
| **Parental controls** | parental_controls.py, School mode | Content filter + screen time in EVT demos |

All three align on policy intent; **unified UI not shipped**.

---

## 3. Age bands

From `user_profile_schema.py` and `guardian_controls.AGE_BAND_DEFAULTS`:

| Age band | Guardian default | Screen time (min/day) | Content filter | App approval |
|----------|------------------|----------------------|----------------|--------------|
| pre_k | Required | 30 | strict | yes |
| elementary | Required | 60 | strict | yes |
| middle_school | Recommended | 90 | moderate | yes |
| high_school | Optional | 120 | moderate | no |
| undergraduate+ | Off | none | light | no |

---

## 4. Guardian control fields (mock)

`enable_guardian_controls(profile_id, age_band)` returns:

| Field | Behavior |
|-------|----------|
| school_mode_restrictions | Limits apps during school hours |
| play_time_window | e.g. 15:00–19:00 for games |
| media_content_caution | Filter level by age |
| app_approval_list | New apps need guardian OK (youth bands) |
| privacy_safe_telemetry | Aggregate only; no content payloads |
| private_content_inspection | **False by default** |
| emergency_unlock_path | guardian_pin_or_biometric (documented) |
| audit_log | placeholder |

Every response includes `"mock": true`.

---

## 5. Personas with guardian requirements

From `config/personas.yaml`:

- `pre_k_learner` — guardian_required: true; blocked steam, browser, youtube, …
- `early_reader` — guardian_required: true
- `middle_school_explorer` — guardian recommended via age_band

`parent_guardian` persona uses Guardian preset and guardian_dashboard workspace.

---

## 6. Guardian preset UX

| Attribute | Specification |
|-----------|---------------|
| Home | guardian_dashboard workspace |
| Apps | settings, guardian tools, approved child apps, gunnchAI3k (help) |
| Blocked for child profiles | Unapproved social, unrestricted browser |
| Telemetry | privacy_safe; guardian consent for youth |
| Exit | car, bicycle, scooter (child view); admin tools for guardian |

---

## 7. School mode alignment

EVT **School mode** (`mode_manager.py`):

- Blocks steam, netflix, vscode, terminal
- Allows waike_offline, gunnchai3k, scaly_wings_edu, filtered browser
- child_safety: strict

Fleet / classroom: `school_fleet_policy.py`, `docs/WAIKE_SCHOOL_MODE.md`.

---

## 8. Play and media windows

| Context | Policy |
|---------|--------|
| Arcade / Play mode | Allowed outside school hours if guardian permits |
| play_time_window | Configurable in guardian_controls |
| Media mode | Browser routes only; DRM required |
| High school gamer | App approval off; time windows may still apply |

---

## 9. Privacy principles for youth

| Principle | Implementation intent |
|-----------|----------------------|
| No private content inspection | Default false in guardian_controls |
| Minimal telemetry | Aggregated opt-in; no chat logging |
| Guardian consent for pre-K telemetry | strict privacy_level in personas.yaml |
| Session reset (library) | Guest profiles — no persistent PII |

See [PRIVACY_AND_TELEMETRY_FOR_USERS.md](PRIVACY_AND_TELEMETRY_FOR_USERS.md).

---

## 10. Edge cases

From `config/edge_cases.yaml`:

| Edge case | Fallback |
|-----------|----------|
| guardian_unavailable | Safe locked screen + emergency unlock path doc |
| youth_requests_blocked_app | Plain-language denial + request approval flow (stub) |
| overwhelmed_user (child) | Scooter + simplified_language |

---

## 11. User journeys

### Guardian sets up child device

1. Onboarding: guardian=true, who=pre_k or child.
2. Wizard assigns Scooter + pre_k_learner or early_reader.
3. `enable_guardian_controls` applies age-band defaults.
4. Child sees 3–4 large icons; browser blocked.
5. Guardian opens guardian_dashboard (mock) to approve apps.

### Teen with optional guardian

1. high_school_student → Car preset.
2. Guardian optional; play_time_window if linked.
3. steam allowed in window; blocked in School mode.

Demo: `run_user_focused_os_demo.py` scenario `guardian_controls`.

---

## 12. Evidence and gaps

| Claim | Evidence | Gap |
|-------|----------|-----|
| Age-band defaults exist | guardian_controls.py | Not enforceable on OS |
| Guardian-required personas | personas.yaml | No PIN/biometric implementation |
| No content inspection default | Policy documented | Legal review pending |
| School + guardian alignment | mode_manager + presets | Unified admin UI missing |

---

## 13. Related documents

- `product/YOUTH_AND_GUARDIAN_REQUIREMENTS.md`
- `docs/security/YOUTH_SAFETY_MODEL.md`
- [PREK_TO_POSTDOC_USE_CASES.md](PREK_TO_POSTDOC_USE_CASES.md)
- [PRIVACY_AND_TELEMETRY_FOR_USERS.md](PRIVACY_AND_TELEMETRY_FOR_USERS.md)
