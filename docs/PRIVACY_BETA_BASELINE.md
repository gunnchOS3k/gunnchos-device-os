# Privacy Beta Baseline

**Status:** Prototype documentation — **not** legal certification.

Phase 4F readiness package: `compliance/privacy/` · [PHASE4F_COMPLIANCE_READINESS.md](PHASE4F_COMPLIANCE_READINESS.md)

## Local data (browser localStorage only)

| Key | Purpose | Sent to server |
|-----|---------|----------------|
| `gunnchos-profile` | Onboarding profile | No |
| `gunnchos-settings-v1` | Theme, a11y, offline, AI privacy | No |
| `gunnchos-workspace-v1` | File manager workspace | No |
| `gunnchos-notes-v1` | Notes content | No |
| `gunnchos-local-media-recent` | Recent media metadata (PR #35) | No |
| `gunnchos-deployment-mode` | Policy test mode | No |

## Not sent in prototype

- No analytics pipeline
- No cloud sync
- No AI prompt transmission (AI panel is UI-only)

## Guardian / School / Library boundaries

- Policy modes block or warn on apps per `config/modes.yaml`
- Library mode shows login warning — no saved passwords by default
- Guardian mode blocks selected apps in shell UI

## AI assistant

- UI shell only — no backend
- `aiPrivacy` toggle persists locally

## Evidence

- `apps/launcher_mock/src/services/privacyStatus.ts`
- `docs/GUARDIAN_AND_YOUTH_SAFETY.md`
