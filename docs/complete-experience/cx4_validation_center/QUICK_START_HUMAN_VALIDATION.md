# Quick Start — Human Validation

1. `./scripts/start-validation-center` (or `make validation-center`)
2. Open **Moderator** → complete the 6-step wizard → copy session code
3. Participant opens **Enter Session** → code (+ token) → accessibility → consent → **Start**
4. One task at a time → rate → attach evidence → submit session
5. Reviewer opens **Awaiting Review** → review → sign (cannot promote pilot/rehearsal to final gating)
6. Export when needed; stop with `./scripts/start-validation-center --stop`

Until an accepted frozen build exists: **PILOT_NON_GATING** only.  
`CX4_FINAL_HUMAN_VALIDATION_ELIGIBLE=false`. Do not invent human PASS.
