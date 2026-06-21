# Accessibility Test Plan

**Version:** 1.0 · **Validation track — not certification**

---

## Purpose

Manual and automated accessibility validation per [../requirements/ACCESSIBILITY_REQUIREMENTS.md](../requirements/ACCESSIBILITY_REQUIREMENTS.md). Produces accessibility report — **does not claim** WCAG certification or accessibility certified on hardware without audit.

---

## Setup

- Enable screen reader (Narrator/VoiceOver) on test device
- Configure high contrast, large text, reduced motion
- Controller paired (Handheld Hybrid)
- Keyboard-only input path (Student 14.5)

---

## Personas covered

- Accessibility-first user (primary)
- Pre-K non-reader mode
- High school student with large text
- Researcher with keyboard-only workflow

---

## Device classes covered

- Student 14.5 — keyboard + touch
- Handheld Hybrid — controller-first
- DS-XL Coder — keyboard-first
- Wearables/Arena — touch/gesture placeholder

---

## Test steps

| ID | Step | WCAG-oriented check |
|----|------|---------------------|
| A-01 | Tab through launcher home | Focus order logical; focus visible |
| A-02 | Activate primary action via keyboard | Enter/Space works |
| A-03 | Navigate via controller | No unreachable controls |
| A-04 | Screen reader labels | Controls have accessible names |
| A-05 | High contrast theme | Text readable; not color-only status |
| A-06 | Large text | No clipped essential text |
| A-07 | Reduced motion | Animations reduced/disabled |
| A-08 | Modal dialog | Escape closes; no keyboard trap |
| A-09 | Error message | Plain language + program association |
| A-10 | Settings persistence | A11y settings survive restart |

---

## Expected results

- All P0 checks pass on reference device
- P1 issues logged with severity
- Report lists scope (e.g., launcher only) — not whole OS

---

## Evidence to collect

- Checklist with pass/fail per step
- Screen reader transcript snippets (redacted)
- Screenshots of focus indicators
- Accessibility report generator output (RC backlog #10)

---

## Pass/fail criteria

**Pass:** 0 P0 a11y blockers; P1 list attached; report filed.

**Fail:** Keyboard trap, missing names on primary actions, color-only critical status.

---

## Known limitations

- Launcher mock may not match production shell
- Switch access / voice input placeholders not tested until implemented
- Third-party apps (Steam, browser) out of scope unless integrated
- **Not a certification audit**
