# Accessibility Requirements

**Status:** validation track defined · **accessibility not certified on hardware**

> Based on WCAG-oriented principles: perceivable, operable, understandable, robust. Launcher contract: `docs/LAUNCHER_ACCESSIBILITY_CONTRACT.md`. This document does not claim accessibility certified and validated on hardware until a validation report exists.

---

## Principles mapping

| Principle | gunnchOS requirement |
|-----------|---------------------|
| **Perceivable** | Text alternatives, contrast themes, captions preference, no color-only meaning |
| **Operable** | Keyboard, controller, touch paths; no keyboard traps; reduced motion |
| **Understandable** | Plain language mode, consistent navigation, human-readable errors |
| **Robust** | Screen reader labels, semantic structure in launcher, focus indicators |

---

## Required settings and features

| Feature | Requirement | Alpha evidence |
|---------|-------------|----------------|
| Keyboard navigation | Full launcher reachable without pointer | Contract doc; mock partial |
| Controller navigation | Handheld-first focus order | Input mapper prototype |
| Touch navigation | 44px min targets where feasible | Launcher mock |
| Screen reader labels | `aria-*` on interactive controls | Partial in mock |
| High contrast | System + in-app theme | Config placeholder |
| Large text | Scales UI text independently | Config placeholder |
| Reduced motion | Respects prefers-reduced-motion | Contract requirement |
| Captions preference | Media apps honor user setting | Policy stub |
| Focus indicators | Visible focus ring on all interactive elements | Launcher contract |
| No color-only meaning | Status uses icon + text | UX requirement |
| No keyboard traps | Modal escape always available | Test plan |
| Simple language mode | Shorter copy variant | User-focused demo personas |
| Non-reader mode | Icon-first navigation option | Scooter mode persona |
| One-hand mode | Reachability layout (handheld) | **planned** |
| Switch access | Placeholder API for assistive switches | **planned** |
| Voice input | Placeholder hook | **planned** |

---

## Persona coverage

User-focused demo includes **accessibility-first user** scenario — see `results/user_focused_os_demo_output.json`.

---

## Acceptance testing

Manual and automated accessibility validation per [../qa/ACCESSIBILITY_TEST_PLAN.md](../qa/ACCESSIBILITY_TEST_PLAN.md).

Report template: accessibility validation report (not certification) required before RC.

---

## Evidence ladder

| Stage | Evidence |
|-------|----------|
| Alpha | Contract docs + mock labels + pytest for config defaults |
| RC | Accessibility report generator output + manual pass log |
| GA | Hardware validation report on reference devices per SKU |

---

## Forbidden claims

- "Accessibility certified" without third-party audit
- "Accessibility certified and validated on hardware" without attached test report
- WCAG Level AA/AAA conformance without documented test scope

---

## Claim boundary

Accessibility **validation track** is defined. The repo does **not** claim accessibility certified on hardware or finished shipping OS accessibility compliance.
