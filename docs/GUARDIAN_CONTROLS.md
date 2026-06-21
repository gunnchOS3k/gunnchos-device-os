# Guardian Controls

**Status:** device OS alpha · mock family safety  
**Modules:** `gunnchos_device_os/guardian_controls.py`, `gunnchos_device_os/guardian_policy.py`  
**Config:** `config/guardian_defaults.yaml`

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

**Important:** Guardian controls are **mock** — not production MDM or certified parental controls.

---

## Purpose

Guardian controls provide **age-band defaults** for screen time, content filtering, app approval, mode approval, and privacy-safe telemetry settings on youth profiles.

---

## API — guardian_controls.py

```python
from gunnchos_device_os.guardian_controls import (
    apply_guardian_defaults,
    enable_guardian_controls,
)

controls = apply_guardian_defaults("elementary")
# screen_time_minutes, content_filter, app_approval, mock: True

profile = enable_guardian_controls("child-1", "elementary")
# enabled: True, controls: {...}
```

### Age band defaults (in-module)

| Age band | Screen time (min) | Content filter | App approval |
|----------|-------------------|----------------|--------------|
| pre_k | 30 | strict | true |
| elementary | 60 | strict | true |
| middle_school | 90 | moderate | true |
| high_school | 120 | moderate | false |
| undergraduate+ | none | light | false |

All responses include `"mock": True`.

---

## API — guardian_policy.py

```python
from gunnchos_device_os.guardian_policy import (
    get_age_band_policy,
    approve_app,
    approve_mode,
)

approve_app("steam", "elementary", approved_list=[])  # approved: False
approve_mode("Developer", "elementary", guardian_approved=False)  # approved: False
```

Restricted modes: Developer, Admin, Workshop, Laboratory.

---

## YAML config highlights

`config/guardian_defaults.yaml`:

- Per-band `play_window` time ranges
- Global defaults: `private_content_inspection: false`, `privacy_safe_telemetry: true`
- `media_caution` lists per filter level

---

## Launcher mock

`GuardianPanel.tsx` — toggle only; does not call Python API.

---

## Integration points

| System | Hook |
|--------|------|
| `mode_policy.py` | Guardian approval for child → unrestricted modes |
| `deploy_contract.py` | `guardian_approved` flag on deploy |
| `modes.yaml` Guardian mode | Strict filtered subset |
| WAIKE | Tutor card `guardian_screen_balance` |

---

## Demo

```bash
python scripts/run_guardian_policy_demo.py
```

Walkthrough: [demo/guardian_controls_walkthrough.md](../demo/guardian_controls_walkthrough.md)

---

## Related documents

- [YOUTH_SAFETY_MODEL.md](YOUTH_SAFETY_MODEL.md)
- [GUARDIAN_AUDIT_LOG_MODEL.md](GUARDIAN_AUDIT_LOG_MODEL.md)
- [GUARDIAN_LIMITATIONS.md](GUARDIAN_LIMITATIONS.md)

---

## Claim boundary

Use **mock guardian controls** language only. Do not claim COPPA/GDPR-K certification or production MDM.
