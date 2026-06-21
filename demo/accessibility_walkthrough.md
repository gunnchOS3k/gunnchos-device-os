# Accessibility Walkthrough

**Audience:** Accessibility reviewers, educators, AT specialists  
**Duration:** ~15 minutes  
**Status:** design + config demo — not WCAG audit  

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

**Not claimed:** WCAG 2.1 AA certification, Section 508, or validation with assistive technology users.

---

## 1. Frame the approach (2 min)

gunnchOS treats accessibility as **defaults per journey preset**, with user overrides. Principles: Perceivable, Operable, Understandable, Robust (POUR).

Docs: `docs/ACCESSIBILITY_AND_INCLUSION.md`, `docs/UDL_ALIGNMENT.md`.

---

## 2. List supported features (3 min)

```bash
PYTHONPATH=. python3 -c "
from gunnchos_device_os.accessibility_manager import SUPPORTED_FEATURES
print('\n'.join(SUPPORTED_FEATURES))
"
```

Expect 16 features including:

- keyboard_navigation, touch_navigation, controller_navigation
- screen_reader_labels, captions_preference
- reduced_motion, high_contrast, large_text, simplified_language
- focus_mode, color_safe_mode, audio_cues, haptic_cues, one_hand_mode
- switch_access (**placeholder**), voice_input (**placeholder**)

Say placeholders out loud.

---

## 3. Preset defaults (3 min)

```bash
PYTHONPATH=. python3 -c "
from gunnchos_device_os.accessibility_manager import get_defaults
import json
for p in ['scooter', 'bicycle', 'car', 'studio', 'arcade']:
    print(p, json.dumps(get_defaults(p), indent=2))
"
```

| Preset | Key defaults |
|--------|--------------|
| Scooter | large_text, simplified_language, reduced_motion, touch |
| Bicycle | simplified_language, captions, keyboard + touch |
| Car | keyboard + touch |
| Studio | focus_mode, color_safe available |
| Arcade | controller, captions |

Source: `config/accessibility_defaults.yaml`.

---

## 4. accessibility_first_user persona (3 min)

Run demo scenario:

```bash
PYTHONPATH=. python3 scripts/run_user_focused_os_demo.py | grep -A2 accessibility_first
```

Or inspect JSON scenario `accessibility_first`:

- Profile flags: high_contrast, large_text, reduced_motion
- Theme: high_contrast via CustomizationEngine
- App pack: accessibility_essentials_pack

**Success moment (design):** Navigate home with preferred input independently.

---

## 5. POUR mapping examples (2 min)

| Principle | Demo point |
|-----------|------------|
| Perceivable | high_contrast theme tokens in themes.yaml |
| Operable | controller_first on HandheldHybrid — `test_os_modules.py` |
| Understandable | simplified_language on Scooter; edge case plain messages |
| Robust | validate_coverage() checks 16 keys; offline cache intent |

---

## 6. Youth + seizures + motion (1 min)

- reduced_motion default for youth presets
- kid_safe theme low stimulation
- Edge case motor_limitations extends timeouts

---

## 7. Neurodiversity and cognitive load (1 min)

- Scooter: one primary action per screen
- overwhelmed_user → Scooter fallback
- focus_mode in Studio for writers

---

## 8. Offline accessibility (1 min)

Offline preset caches a11y settings — no network fetch for font/contrast preferences.

See `demo/offline_first_walkthrough.md`.

---

## 9. Honest gaps (2 min)

| Gap | Next step |
|-----|-----------|
| No NVDA/VoiceOver test log | USER_TESTING_PLAN P3 |
| switch_access not implemented | Document only |
| Launcher mock partial theming | Engineering backlog |
| No automated axe/pa11y in CI | Add when UI stable |

---

## 10. Validator

```bash
PYTHONPATH=. python3 -c "
from gunnchos_device_os.accessibility_manager import apply_settings, validate_coverage
s = apply_settings({'high_contrast': True})
print('missing:', validate_coverage(s))
"
```

Empty missing list = all 16 keys present.

---

## Presenter checklist

- [ ] Stated "accessibility-first UX" not "WCAG certified"
- [ ] Named switch_access and voice_input as placeholders
- [ ] Referenced USER_TESTING_PLAN for AT sessions
- [ ] Did not claim user-tested with disabled participants

---

## Related docs

- `product/ACCESSIBILITY_REQUIREMENTS.md`
- `ACCESSIBILITY_AND_LOW_COST.md`
- `docs/CLAIMS_TO_EVIDENCE_USER_EXPERIENCE.md`
