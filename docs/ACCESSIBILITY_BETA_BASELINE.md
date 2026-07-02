# Accessibility Beta Baseline

**Status:** Prototype baseline — **not** certification.

## Implemented in launcher

- Keyboard navigation documented in Media Hub copy
- Deployment mode selector is keyboard accessible
- Primary dock buttons use `aria-label`
- Settings persist: large text, high contrast, reduced motion
- `accessibilityAudit.ts` reports toggle state — no certification claim

## Not claimed

- WCAG 2.x conformance
- Screen reader full coverage
- Hardware switch/accessibility suite integration

## Evidence

- `apps/launcher_mock/src/services/accessibilityAudit.ts`
- `apps/launcher_mock/src/services/settingsStore.ts`
- `docs/LAUNCHER_ACCESSIBILITY_CONTRACT.md`

## Tests

- Settings persistence via Vitest
- Shell primary buttons accessible names
