# Phase 4F: Legal, Privacy, and Accessibility Readiness

**Status:** Readiness package only — **not certification**.

## Deliverables

| Area | Path |
|------|------|
| Overview | `compliance/README.md` |
| Privacy | `compliance/privacy/` |
| Accessibility | `compliance/accessibility/` |
| Legal | `compliance/legal/` |

## Privacy readiness

- Data inventory and localStorage inventory
- Student/youth data risk register
- AI assistant data boundary
- Telemetry consent mapping
- Deployment mode data boundaries
- Deletion/export notes
- Privacy policy draft + DPIA template

## Accessibility readiness

- WCAG self-assessment checklist
- Keyboard, screen reader, contrast, reduced motion notes
- Captions/media and controller/touch notes
- Accessibility test report template

## Legal readiness

- Terms of use draft
- Open-source license inventory
- Third-party dependencies
- Streaming and education data claim boundaries
- Child/youth safety and school/library deployment checklists

## What is NOT claimed

- COPPA / FERPA / GDPR compliance
- WCAG conformance certification
- Legal certification or attorney sign-off

## Tests

```bash
pytest tests/test_compliance_readiness.py -q
```

## Beta gate

`legal_privacy_accessibility`: **prototype** (readiness)

`beta_ready` remains **false**.
