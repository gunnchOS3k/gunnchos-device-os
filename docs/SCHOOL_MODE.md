# School Mode

**Status:** device OS alpha · policy definition in `config/modes.yaml`  
**Module:** `gunnchos_device_os/mode_manager.py`

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## Purpose

**School** mode optimizes shared and 1:1 school devices for focused learning with strict child safety, filtered network, and no invasive surveillance.

---

## Policy summary

| Key | Value |
|-----|-------|
| `allowed_apps` | browser, waike_offline, gunnchai3k, scaly_wings_edu |
| `blocked_apps` | steam, netflix, hulu, vscode, terminal |
| `telemetry` | aggregated_opt_in |
| `network` | filtered |
| `update` | admin_scheduled |
| `child_safety` | strict |
| `performance` | school |
| `simplified_home` | true |
| `focus_mode` | true |
| `offline_lessons` | true |
| `guardian_hooks` | true |
| `teacher_policy_hooks` | true |
| `no_invasive_surveillance` | true |
| `privacy_safe_telemetry` | true |

Accessibility defaults: `simplified_language`, `focus_mode`.

---

## User experience intent

- Simplified home screen with fewer distractions
- Offline WAIKE lessons available (`waike_offline`)
- gunnchAI3k tutor for guided reflection (privacy-safe prompts)
- No terminal or unrestricted IDE — coding intro via approved edu apps

---

## Transition restrictions

From School (or Library, Guardian):

- Transition to **Admin** or **Developer** requires explicit consent (`mode_policy.can_transition`)
- Child profiles need guardian approval for Developer

See [MODE_TRANSITION_RULES.md](MODE_TRANSITION_RULES.md).

---

## Guardian and privacy alignment

| System | School mode hook |
|--------|------------------|
| `guardian_policy.py` | App approval for younger age bands |
| `privacy_security_model.py` | `school_mode` profile defaults — strict privacy |
| `guardian_defaults.yaml` | `school_library_profile_safety: true` |

---

## WAIKE integration

Tutor card `school_wireless_basics` targets high school School mode — see [WAIKE_TUTOR_CARDS.md](WAIKE_TUTOR_CARDS.md).

---

## Test evidence

```bash
PYTHONPATH=. pytest tests/test_modes.py::test_school_mode
```

Asserts: `simplified_home`, steam blocked, `no_invasive_surveillance`.

---

## Claim boundary

School mode is a **policy stub**. It does not prove COPPA compliance, MDM enrollment, or classroom management certification.
