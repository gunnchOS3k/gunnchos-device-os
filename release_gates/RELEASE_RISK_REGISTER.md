# Release Risk Register

**Last updated:** 2026-06-21

| ID | Risk | Likelihood | Impact | Mitigation | Owner | Status |
|----|------|------------|--------|------------|-------|--------|
| R-001 | No installable image pipeline | High | High | RC backlog tasks 2–4; beta gate | Release eng | open |
| R-002 | Hardware not available for compatibility testing | Medium | High | YAML contract tests; defer wearables | HW program | open |
| R-003 | Launcher mock ≠ production shell | High | Medium | Launcher e2e + installer integration | UX | open |
| R-004 | Security review incomplete | Medium | High | Checklist + threat model delta | Security | open |
| R-005 | Accessibility not tested on hardware | High | Medium | Manual a11y plan before RC claim | QA | open |
| R-006 | Deploy transport mock only | High | Medium | Signed bundle + transport e2e | OS | open |
| R-007 | Guardian controls not production MDM | Medium | High | Clear claim boundary; pilot scope | Programs | open |
| R-008 | Steam/media partner certification gap | Medium | Medium | Mock routes only until partner docs | Integrations | open |
| R-009 | CI demo dependency regression | Low | Medium | Self-generating test + workflow order | CI | mitigated |
| R-010 | Cross-repo Edge-IO/WAIKE drift | Medium | Medium | Contract tests + version pins | Integrations | open |
| R-011 | Signing key ceremony not defined | Medium | High | SIGNING_REQUIREMENTS.md + security review | Security | open |
| R-012 | GA claimed without evidence | Low | Critical | Gate validators + sign-off template | Release | mitigated |

---

## Review cadence

- Weekly during RC push
- At each gate transition
- After field pilot incidents

---

## Escalation

P0 risks block RC/GA sign-off until mitigated or waived in [RELEASE_SIGNOFF_TEMPLATE.md](RELEASE_SIGNOFF_TEMPLATE.md).
