# Guardian Limitations

**Status:** device OS alpha · honest gaps for issue #7 closure

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## What exists today

| Capability | Evidence |
|------------|----------|
| Age-band YAML defaults | `config/guardian_defaults.yaml` |
| Mock enable/disable API | `guardian_controls.py` |
| App and mode approval checks | `guardian_policy.py` |
| Mode transition gates | `mode_policy.py` |
| Launcher mock toggle | `GuardianPanel.tsx` |
| Unit tests | `tests/test_guardian_policy.py` |
| Demo script | `scripts/run_guardian_policy_demo.py` |

---

## What is mock or placeholder

| Item | Status |
|------|--------|
| Screen time enforcement | Defaults only — no timer |
| Play window enforcement | YAML windows — not scheduled |
| Audit log persistence | `"audit_log": "placeholder"` |
| Emergency unlock PIN/biometric | Named only |
| Private content inspection | Explicitly **false** — not a hidden feature |
| Remote guardian dashboard | Not implemented |
| COPPA/GDPR-K compliance | **Not certified** |
| Production MDM integration | **Not implemented** |

---

## Forbidden claims

Do not state or imply:

- "Production parental controls"
- "COPPA certified"
- "School MDM ready"
- "Guardian can read child messages"
- "Real-time location tracking for safety"

See `product/CLAIM_BOUNDARY.md`.

---

## Safe wording

- "Mock guardian controls with age-band defaults"
- "Guardian approval required for Developer mode (alpha policy check)"
- "Privacy-safe — no private content inspection by design"

---

## Next evidence for production path

1. Integration with fleet MDM or family link API
2. Persistent audit log with export
3. Security review of escalation paths
4. User study with families (opt-in, IRB if applicable)
5. Legal review for target jurisdictions

Track under `[Evidence TODO]` issues and `quality/CLAIMS_TO_EVIDENCE_MATRIX.md`.

---

## Related documents

- [GUARDIAN_CONTROLS.md](GUARDIAN_CONTROLS.md)
- [YOUTH_SAFETY_MODEL.md](YOUTH_SAFETY_MODEL.md)
- [GUARDIAN_AUDIT_LOG_MODEL.md](GUARDIAN_AUDIT_LOG_MODEL.md)
