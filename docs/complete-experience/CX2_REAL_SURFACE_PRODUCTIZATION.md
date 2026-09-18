# CX2 — Real User Surface + Provider Productization

Stacked on CX1. First-party surfaces live in the existing `apps/launcher_mock` gunnchOS shell (`CompleteExperienceShell`) plus `gunnchos_device_os/cx2` authorities.

## Authorities

| Surface | GUI | Backend |
|---------|-----|---------|
| Home | `cx2/surfaces/HomeSurface.tsx` | `ProductShell.home_model` |
| Vault | `VaultSurface.tsx` | CX1 Vault + CX2 shell |
| App Center | `AppCenterSurface.tsx` | `RealAppCenterProvider` (local package repo) |
| Connect | `ConnectSurface.tsx` | SMTP/IMAP + CalDAV/CardDAV stacks |
| Assist | `AssistSurface.tsx` | rendered a11y controls; HUMAN pending |
| Care | `CareSurface.tsx` | Support bundle / recovery |

## Evidence classes

`CONTRACT_PASS`, `HARNESS_PASS`, `REAL_PROVIDER_CLI_PASS`, `REAL_PROVIDER_GUI_PASS`, `REAL_USER_JOURNEY_DIGITAL_PASS`, `HUMAN_VALIDATION_PENDING`, `PHYSICAL_VALIDATION_PENDING`, `EXTERNAL_PROVIDER_PENDING`, `NOT_APPLICABLE`

CX1 overstatements are reclassified in `artifacts/complete_experience/cx2/CX1_RECLASSIFICATION.json` without rewriting CX1 history.

## Claim boundary

- `FULL_COMPLETE_EXPERIENCE_COMPLETE=false`
- No Device Lab #134 / Portal #14/#15 / WAIKE/gunnchAI changes
- Physical print + human a11y + AV quality remain pending

## CLI

```bash
python -m gunnchos_device_os.cx2 first-run --name Alex
python -m gunnchos_device_os.cx2 journeys
python -m gunnchos_device_os.cx2 evidence --repo-root .
```

## Tests

```bash
python -m pytest tests/cx0 tests/cx1 tests/cx2 -q
cd apps/launcher_mock && npm test -- --run src/cx2
```
