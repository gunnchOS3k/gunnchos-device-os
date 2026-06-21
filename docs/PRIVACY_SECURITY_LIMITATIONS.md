# Privacy & Security Limitations

**Status:** device OS alpha · honest gaps for issue #8 closure

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## Implemented (alpha)

| Feature | Module | Test |
|---------|--------|------|
| Profile-based telemetry defaults | privacy_security_model.py | test_privacy_security_model.py |
| Consent state machine | consent_policy.py | test_consent_policy.py |
| Child telemetry off | get_telemetry_policy | test_no_telemetry_for_child |
| Research consent gate | research_requires_consent | test_research_requires_consent |
| Redacted security log | security_event_log.py | test_security_event_log.py |
| Data minimization YAML flags | privacy_defaults.yaml | Documented |

---

## Placeholders (not production)

| Feature | Status |
|---------|--------|
| User data export | `export_queued_placeholder` |
| User data delete | `delete_queued_placeholder` |
| Crash report upload | `crash_reports_placeholder` category only |
| Fleet telemetry backend | Synthetic mock in launcher |
| Encrypted log storage | Not implemented |
| GDPR DSAR automation | Not implemented |

---

## Not certified

- GDPR compliance
- COPPA / GDPR-K youth certification
- SOC 2 / ISO 27001
- Formal penetration test
- WCAG for privacy UX

---

## Forbidden claims

- "Enterprise-grade security"
- "Zero telemetry guaranteed on hardware" (policy only in Python)
- "Production privacy pipeline"
- "Certified youth-safe telemetry"

---

## Safe claims

- "Privacy-first defaults for child profiles in alpha config"
- "Consent-gated research telemetry design"
- "Sensitive fields redacted in security event log prototype"

---

## Next evidence

1. End-to-end export/delete on real profile store
2. Third-party security review
3. Telemetry pipeline with differential privacy analysis (if aggregate enabled)
4. Field study documenting user comprehension of consent prompts

See `docs/WHAT_WOULD_MAKE_THIS_FINAL.md` and `[Evidence TODO]` issues.

---

## Related documents

- [PRIVACY_SECURITY_MODEL.md](PRIVACY_SECURITY_MODEL.md)
- [product/CLAIM_BOUNDARY.md](../product/CLAIM_BOUNDARY.md)
- [THREAT_MODEL.md](THREAT_MODEL.md)
