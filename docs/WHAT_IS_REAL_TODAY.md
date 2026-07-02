# What Is Real Today

**Last updated:** Phase 3 beta closure sprint (2026-07-02). Full audit: [FULL_OPERATIONAL_GAP_MATRIX.md](FULL_OPERATIONAL_GAP_MATRIX.md)

## Real (validated in repo)

- `gunnchos_device_os` Python policy package + `config/modes.yaml`
- CI gate: contract export, pytest, frontend build/test (`make validate-full`)
- **File Manager v1** — browser localStorage workspace
- **Notes app v1** — browser localStorage
- **Browser/PWA open behavior** — external tab launches (`appLaunchService.ts`)
- **Game launch adapter** + **Anime Aggressors web vertical slice**
- **Shell policy enforcement** — `policyEnforcementService.ts` (not production MDM)
- **Settings persistence** — theme, a11y, offline, AI privacy toggles
- **Beta gate dashboard** — `beta_gate/beta_gate_status.yaml` + validator
- **Known issues registry** — `docs/KNOWN_ISSUES.md`
- **Accessibility / privacy baselines** — documented, not certified
- **Image prototype track** — container kiosk packaging (not bootable OS)
- Container validation evidence — `hardware_validation/CONTAINER_KIOSK_VALIDATION_LOG.md`

## Prototype / honest labels

- **Local media player** — pending PR #35 merge to main
- Browser/PWA — external tab route; no embedded shell
- Local workspace / notes — browser localStorage, not production FS
- Policy enforcement — shell UI prototype
- Bootable image — container/OS-layer track only
- Hardware — no physical device validation
- Games — Anime Aggressors slice only; Foot Racing / Earth Species not connected
- AI assistant — UI shell only

## Not real (not claimed)

- Production filesystem / encrypted storage
- Google Drive sync
- Netflix/Hulu certification / DRM CDM
- Production MDM, secure boot, fleet deployment
- Accessibility or privacy legal certification
- GA / beta release claim (`beta_ready: false`)

## Release readiness

| Stage | Met? |
|-------|------|
| Alpha (shell + policy) | **Yes** |
| Beta candidate | **No** — see [BETA_CANDIDATE_REPORT.md](../release_artifacts/BETA_CANDIDATE_REPORT.md) |
| RC / GA / Production | **No** |

Smoke: `make validate-full` · Beta gate: `python3 scripts/validate_beta_gate.py`
