# Telemetry Consent Mapping

| Level | Shell setting / MDM | Data collected (prototype) | Transmitted |
|-------|---------------------|----------------------------|-------------|
| none | `telemetry_consent_level: none` | None | No |
| diagnostics | Default in school MDM sample | Would be crash logs (future) | Not implemented |
| analytics | — | Would be usage events (future) | Not implemented |
| full | — | Would include feature analytics (future) | Not implemented |

## Mapping to UI

- Settings `aiPrivacy` toggle: local preference only — does not control telemetry pipeline (none exists)
- MDM sample policies define intended fleet defaults (`mdm/sample_policies/`)

## Before beta claim

- Implement consent UI aligned with actual telemetry
- Document retention and deletion in privacy policy
- Legal review of consent language
