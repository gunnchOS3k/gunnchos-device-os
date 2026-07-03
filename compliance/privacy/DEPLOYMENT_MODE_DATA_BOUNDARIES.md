# Deployment Mode Data Boundaries

| Mode | Data handling intent | Prototype enforcement |
|------|---------------------|----------------------|
| Guardian | Restrict apps; bedtime settings in MDM sample | Shell policy + MDM sample JSON |
| School | Block social/streaming; diagnostics telemetry default | Shell policy + MDM sample JSON |
| Library | Guest sessions; limited retention | MDM sample only — not enforced |
| Play | Full prototype access with warnings | Shell default |

See also `config/modes.yaml` and `apps/launcher_mock/src/services/policyEnforcementService.ts`.

**Not certified for COPPA/FERPA/GDPR compliance.**
