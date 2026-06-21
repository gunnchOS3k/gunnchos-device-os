# Guardian Controls Walkthrough

**Status:** device OS alpha · hands-on demo guide

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## Part 1 — Python policy demo

```bash
pip install -r requirements.txt
python scripts/run_guardian_policy_demo.py
```

Review output for age-band policies and approval examples.

---

## Part 2 — App approval

```python
from gunnchos_device_os.guardian_policy import approve_app, get_age_band_policy

# Elementary requires approval
assert approve_app("steam", "elementary", [])["approved"] is False
assert approve_app("waike_offline", "elementary", ["waike_offline"])["approved"] is True

p = get_age_band_policy("middle_school")
print(p["play_window"], p["content_filter"])
```

---

## Part 3 — Mode approval

```python
from gunnchos_device_os.guardian_policy import approve_mode
from gunnchos_device_os.mode_policy import can_transition

# Policy layer
assert approve_mode("Developer", "elementary")["approved"] is False

# Transition layer
r = can_transition("School", "Developer", profile_type="elementary", guardian_approved=False)
assert r["allowed"] is False
print(r["user_message"])
```

---

## Part 4 — Enable guardian controls (mock)

```python
from gunnchos_device_os.guardian_controls import enable_guardian_controls

g = enable_guardian_controls("student-a", "elementary")
assert g["enabled"] and g["controls"]["mock"]
assert g["controls"]["private_content_inspection"] is False
```

---

## Part 5 — Launcher mock

```bash
cd apps/launcher_mock && npm run dev
```

1. Switch to **Your device (scooter → spaceship)**
2. Open **Guardian** tab
3. Toggle guardian on — read mock disclaimer
4. Open **Home** tab to see guardian state in summary

---

## Part 6 — WAIKE tutor card

Read `config/waike_tutor_cards.yaml` → `guardian_screen_balance`:

- Mode: Guardian
- Note: "Guardian controls are a stub — not production enforcement."

---

## Discussion questions

1. Why is `private_content_inspection` always false?
2. How do guardian policy and mode policy differ?
3. What would need to change for a real school deployment?

---

## Tests

```bash
PYTHONPATH=. pytest tests/test_guardian_policy.py
```

---

## Claim boundary

This walkthrough demonstrates **mock APIs** only — not live parental control enforcement on hardware.
