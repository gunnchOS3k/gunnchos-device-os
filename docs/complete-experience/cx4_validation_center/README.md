# CX4.1 Validation Center

First-party **gunnchOS Validation Center** for human/field evidence collection.

- UI: `apps/validation_center/`
- Python contracts/store: `gunnchos_device_os/cx4_validation_center/`
- Evidence: `artifacts/complete_experience/cx4_1/`

Software readiness does **not** set human/physical PASS tokens.

## CX4.2 Pilot readiness

- One-click launch: `./scripts/start-validation-center` / `make validation-center`
- Evidence eligibility doctrine (`ValidationEvidenceEligibility` v1)
- Freeze check + materiality compare
- Human Validation Day packet + participant guide
- Rehearsal is `REHEARSAL_NON_GATING` only — never real human PASS

`CX4_FINAL_HUMAN_VALIDATION_ELIGIBLE=false` until an accepted frozen build exists.
