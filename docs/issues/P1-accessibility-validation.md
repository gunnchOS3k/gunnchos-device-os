# OS-014: Accessibility validation

**Priority:** P1 · **Release target:** GA

## Problem

Accessibility panels exist; no hardware validation or WCAG audit.

## Why it matters

Product vision includes dyslexia-friendly mode, screen reader, multilingual UI.

## Definition of done

- axe/vitest a11y checks in CI
- Hardware screen reader session on ref device
- Report in `results/`

## Tests

- Automated a11y + manual HW checklist

## Evidence required

- Signed a11y validation report

## Non-goals

- Full legal compliance certification without review

## Claim boundary

Validation report required before GA a11y claims.
