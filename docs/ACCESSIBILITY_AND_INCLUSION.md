# Accessibility and Inclusion

**Status:** device OS alpha · accessibility-first UX — not WCAG 2.1 AA certified  

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## 1. Commitment (design intent)

gunnchOS treats accessibility as a **default**, not an add-on. The experience layer must work for:

- Neurodiverse users (predictability, reduced stimulation, focus mode)
- Low vision (large text, high contrast, no color-only meaning)
- Motor limitations (large targets, keyboard/controller, one-hand mode, switch access placeholder)
- Cognitive load sensitivity (simplified language, one primary action, extended timeouts)
- Language diversity (plain language, reading level, preferred_language on profile)
- Offline and low-bandwidth users (a11y settings cached locally)

**Not claimed:** formal WCAG audit, Section 508 certification, or user-tested validation with participants with disabilities.

---

## 2. POUR principles mapping

### Perceivable

| User need | Feature | Preset defaults |
|-----------|---------|-----------------|
| See content clearly | `large_text`, `high_contrast`, `color_safe_mode` | Scooter, accessibility_first_user |
| Hear alternatives | `captions_preference`, `audio_cues` | Bicycle, Arcade |
| Non-visual access | `screen_reader_labels` on all controls | All presets (global) |
| Reduced visual noise | `reduced_motion`, focus layouts | Scooter, kid_safe theme |

**Implementation:** `accessibility_manager.py`, `config/accessibility_defaults.yaml`, `theme_manager.py`.

**Gap:** Labels are configuration flags — not validated with NVDA, VoiceOver, or TalkBack.

### Operable

| User need | Feature | Notes |
|-----------|---------|-------|
| Keyboard-only use | `keyboard_navigation` | Tab order, visible focus — spec in product doc |
| Touch / motor | `touch_navigation` | ≥44×44 dp equivalent targets |
| Game controller | `controller_navigation` | Arcade, HandheldHybrid profile |
| One hand | `one_hand_mode` | Reachable target zones |
| Switch access | `switch_access` | **Placeholder** — scanning UI documented only |
| Voice | `voice_input` | **Placeholder** — must not block other inputs |
| Enough time | Edge case `motor_limitations` | Extends session timeouts |
| Seizure safety | `reduced_motion` default for youth | Scooter, Guardian |

### Understandable

| User need | Feature | Notes |
|-----------|---------|-------|
| Plain language | `simplified_language` | Scooter/Bicycle copy |
| Predictable navigation | Documented preset exit paths | See JOURNEY_PRESETS |
| Error recovery | `edge_case_policy.py` user_message strings | Plain-language, not codes |
| Reading level | Persona + age_band in profile | Onboarding maps who → persona |

### Robust

| User need | Feature | Notes |
|-----------|---------|-------|
| Works offline | A11y defaults in offline cache | offline preset |
| Works across presets | `validate_coverage()` | 16 feature keys |
| Edge case fallbacks | overwhelmed_user → scooter | `config/edge_cases.yaml` |
| Compatible with AT | screen_reader_labels | Robust intent; AT testing pending |

---

## 3. Universal Design for Learning (UDL)

See [UDL_ALIGNMENT.md](UDL_ALIGNMENT.md) for full guideline table.

Summary:

- **Engagement:** Persona choice, scooter-to-spaceship growth, focus_mode, guardian self-regulation aids
- **Representation:** Multiple modalities — text, audio cues, captions, high contrast
- **Action & expression:** Touch, keyboard, controller, creator workflows, voice placeholder

---

## 4. Neurodiversity

| Approach | Implementation |
|----------|----------------|
| Reduced stimulation | kid_safe theme, reduced_motion, Scooter single-row layout |
| Predictability | Consistent Home + Help; preset exit paths documented |
| Focus support | focus_mode in Studio/Workshop |
| Overwhelm recovery | Edge case routes to Scooter with simplified_language |
| Optional structure | Bicycle progress widgets — can hide via customization |

**Gap:** No co-design sessions with neurodiverse users documented.

---

## 5. Low vision

| Control | User path |
|---------|-----------|
| Large text | Settings → Accessibility → Text size (or preset default) |
| High contrast | Theme `high_contrast` or a11y toggle |
| Color-safe palettes | `color_safe_mode` in Studio |
| No color-only status | Policy in product ACCESSIBILITY_REQUIREMENTS |

---

## 6. Motor

| Control | User path |
|---------|-----------|
| Large touch targets | Scooter, touch_navigation |
| Keyboard navigation | Car and above defaults |
| Controller | Arcade, gamer persona |
| One-hand mode | Accessibility settings |
| Switch access | Placeholder — document only |

Edge case: `motor_limitations` extends timeouts and suggests larger targets.

---

## 7. Cognitive load

| Control | User path |
|---------|-----------|
| One primary action per screen | Scooter preset spec |
| Simplified language | Scooter/Bicycle |
| Guided onboarding | 7 questions, not full settings dump |
| Settings depth | simple / guided / full / power_user |
| Focus mode | Studio writer/artist workflows |

---

## 8. Language

| Field | Source |
|-------|--------|
| `preferred_language` | UserProfile (future UI) |
| Onboarding copy | Per persona in personas.yaml |
| simplified_language flag | Short sentences when true |

**Gap:** No i18n/l10n framework in repo today — English-first scaffold.

---

## 9. Offline accessibility

When `offline_mode_manager.enable_offline_mode()` is active:

- Accessibility settings load from local cache (no network fetch).
- Captions for cached media only (no streaming).
- Screen reader labels remain on all offline-pack apps.

See [OFFLINE_FIRST_USER_EXPERIENCE.md](OFFLINE_FIRST_USER_EXPERIENCE.md).

---

## 10. accessibility_first_user persona

| Field | Value |
|-------|-------|
| Default preset | Scooter or Bicycle with overrides |
| App pack | accessibility_essentials_pack |
| Success moment | Navigate home with preferred input independently |

Demo scenario in `scripts/run_user_focused_os_demo.py` applies high_contrast + large_text + reduced_motion.

---

## 11. Evidence and gaps

| Claim | Evidence today | Gap |
|-------|----------------|-----|
| 16 a11y features defined | `accessibility_manager.SUPPORTED_FEATURES` | AT validation |
| Preset defaults exist | `config/accessibility_defaults.yaml` | Launcher mock rendering |
| WCAG-aligned intent | `product/ACCESSIBILITY_REQUIREMENTS.md` | No third-party audit |
| Switch / voice | IDs in manager | Not implemented |

---

## 12. Related documents

- [UDL_ALIGNMENT.md](UDL_ALIGNMENT.md)
- [SCOOTER_TO_SPACESHIP_MODEL.md](SCOOTER_TO_SPACESHIP_MODEL.md)
- `product/ACCESSIBILITY_REQUIREMENTS.md`
- `ACCESSIBILITY_AND_LOW_COST.md`
- [CLAIMS_TO_EVIDENCE_USER_EXPERIENCE.md](CLAIMS_TO_EVIDENCE_USER_EXPERIENCE.md)
