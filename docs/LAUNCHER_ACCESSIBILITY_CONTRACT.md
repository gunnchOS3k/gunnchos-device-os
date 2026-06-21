# Launcher Accessibility Contract

**Status:** device OS alpha · design intent, not WCAG certification  
**Implementation:** `apps/launcher_mock/`, `gunnchos_device_os/accessibility_manager.py`

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## Scope

This contract defines **minimum accessibility expectations** for the launcher mock and how they align with the Python `accessibility_manager.py` and `config/accessibility_defaults.yaml`. It does **not** claim WCAG 2.2 AA certification.

---

## Principles

1. **Perceivable** — high contrast and large text toggles in user-focused view affect global font scale and colors
2. **Operable** — minimum 44×44px touch targets on primary navigation; labeled view switches
3. **Understandable** — plain-language disclaimers ("Not a finished shipping OS")
4. **Robust** — semantic buttons and nav landmarks; native selects for device/mode

---

## User-focused accessibility features

| Feature | UI control | State keys | Maps to Python |
|---------|------------|------------|----------------|
| Large text | AccessibilityPanel toggle | `largeText` → `fontScale 1.25` | `large_text` in accessibility defaults |
| High contrast | AccessibilityPanel toggle | `highContrast` → `#000`/`#fff` | `high_contrast` |
| Reduced motion | AccessibilityPanel toggle | `reducedMotion` | `reduced_motion` (CSS intent; limited animation in alpha) |
| Screen reader labels | Tab `aria-label`, `aria-current` | — | `screen_reader_labels` device default |
| Keyboard navigation | Focusable controls | — | `keyboard_navigation` on ds_xl_coder |

---

## Fleet view requirements

| Element | Requirement | Alpha status |
|---------|-------------|--------------|
| View switch to user-focused | `aria-label="Switch to user-focused experience"`, min-height 44px | Implemented |
| Campus/device/mode selects | Associated `<label>` text | Implemented |
| App grid buttons | Visible text label per app | Implemented |
| Panel headings | `<h3>` in Panel component | Implemented |
| Color contrast (dark theme) | Target 4.5:1 for body text | Manual check recommended |
| Skip link | Skip to main content | **Not implemented** |

---

## User-focused view requirements

| Element | Requirement | Alpha status |
|---------|-------------|--------------|
| Section nav | `<nav aria-label="User-focused sections">` | Implemented |
| Active tab | `aria-current="page"` | Implemented |
| Tab buttons | `aria-label="Go to {label}"` | Implemented |
| Fleet return | `aria-label="Switch to fleet launcher view"` | Implemented |
| Heading hierarchy | Single `<h1>` per view | Implemented |
| Focus order | Logical tab order left-to-right | Implemented |

---

## Persona and preset accessibility

Personas in `personaData.ts` include accessibility hints (e.g., simplified language, focus mode) aligned with `config/personas.yaml`. Selecting a persona may recommend presets with `accessibility_defaults` from journey config.

**Gap:** Persona-specific a11y toggles are not auto-applied on selection — user must confirm in Accessibility tab.

---

## Device class defaults

From `config/device_classes.yaml`:

| Class | Default a11y hints |
|-------|-------------------|
| student_14_5 | screen_reader_labels |
| handheld_hybrid | controller_navigation, touch_navigation |
| ds_xl_coder | keyboard_navigation, focus_mode |
| wearables_arena_set | audio_cues, haptic_cues, simplified_language |

---

## Testing evidence

| Test | Path |
|------|------|
| Python a11y feature coverage | `tests/test_accessibility_manager.py` |
| Validation script | `scripts/validate_accessibility_coverage.py` |
| Manual walkthrough | `demo/accessibility_walkthrough.md` |
| Launcher automated a11y | **Gap** — no axe-core CI |

---

## Known limitations (alpha)

- Partial theming in fleet view (documented in `demo/accessibility_walkthrough.md`)
- No live screen reader test log in repo
- Reduced motion toggle does not disable all transitions
- Controller navigation not simulated in browser mock
- Haptic/audio cues are documentation-only for wearables class

---

## Related documents

- [ACCESSIBILITY_AND_INCLUSION.md](ACCESSIBILITY_AND_INCLUSION.md)
- [product/ACCESSIBILITY_REQUIREMENTS.md](../product/ACCESSIBILITY_REQUIREMENTS.md)
- [LAUNCHER_COMPONENT_MAP.md](LAUNCHER_COMPONENT_MAP.md)
