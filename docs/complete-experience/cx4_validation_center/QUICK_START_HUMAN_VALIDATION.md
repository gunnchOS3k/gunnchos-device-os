# Quick Start — Human Validation

1. `./scripts/start-validation-center` (or `make validation-center`)
2. Open **Moderator** → complete the 6-step wizard → copy session code
3. Participant opens **Enter Session** → code (+ token) → accessibility → consent → **Start**
4. One task at a time → rate → attach evidence → submit session
5. Reviewer opens **Awaiting Review** → review → sign (cannot promote pilot/rehearsal to final gating)
6. Export when needed; stop with `./scripts/start-validation-center --stop`

Until an accepted frozen build exists with real hardware prerequisites attested: **PILOT_NON_GATING** only.  
`CX4_FINAL_HUMAN_VALIDATION_ELIGIBLE` stays false until owner freeze + real hardware prerequisites. Do not invent human PASS.

## Fail-closed validators

```bash
# Refuse incomplete evidence
PYTHONPATH=.:src python3 -m gunnchos_device_os.cx4_validation_center validate-session path/to/session.json

# Defect intake → triage → revalidation plan
PYTHONPATH=.:src python3 -m gunnchos_device_os.cx4_validation_center refinement-loop path/to/session.json --out artifacts/complete_experience/cx4_2/refinement_loop

# Freeze identity against accepted main (does not invent hardware readiness)
PYTHONPATH=.:src python3 -m gunnchos_device_os.cx4_validation_center freeze-check \
  --portal-commit 6467551bbd68732d4681d763c35cc3b5da410879 \
  --target-commit 438aaf2b54d3365d681dd6eeeb73f6ac58663acc
```

