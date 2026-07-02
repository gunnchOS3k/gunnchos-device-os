# Phase 3 — Shell Policy Enforcement

**Branch:** `phase3-beta-closure-sprint`

## Real after this PR

- `policyEnforcementService.ts` — centralized mode policy evaluation
- Applied in Campus Mode, Browser/PWA hub (via appLaunchService), Media Hub, Game launch
- Deployment mode selector for School/Library/Guardian/Offline/Media testing
- Blocked apps show visible reason in UI

## Still prototype

- Not production MDM or fleet policy
- Policy enforcement is shell-level UI gate — not kernel enforcement

## Decisions

| Decision | Values |
|----------|--------|
| allowed | Launch permitted |
| blocked_by_mode | Mode blocked_apps / offline network rules |
| blocked_by_school | School defaults + blocked list |
| blocked_by_guardian | Guardian blocked set |
| warning_only | Library login warning; first-party games in school context |
| unavailable | Missing app/build |

## Validation

```bash
npm test -- policy
make validate-full
```
