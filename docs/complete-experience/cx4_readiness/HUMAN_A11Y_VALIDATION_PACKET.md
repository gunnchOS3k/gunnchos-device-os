# Human Accessibility Validation Packet (CX4.0)

**Status:** preparation only.
**Class:** `J6_CLASS=HUMAN_VALIDATION_PENDING`
**Never set:** `human_a11y_pass=true` from automation or this packet alone.

Automation already earned `CX3_AUTOMATED_A11Y_PASS=true`. This packet is for **human** validation.

## Plan (not completed evidence)

- Minimum participant recommendation (plan): **6** participants covering screen-reader, keyboard-only, low-vision, captions/hearing, motor/switch, cognitive/reading needs.
- This count is a **plan**, not executed evidence.

## Surfaces under test

- Home
- Vault
- App Center
- Browser
- Mail
- Writer
- Wallet
- Portfolio
- Career Profile
- Verifier
- Care
- Assist

## Participant instructions

1. Read consent/privacy notes below; confirm voluntary participation.
2. Use the assigned modality only for the assigned block (keyboard-only / SR / zoom / etc.).
3. Follow the task script; do not skip error/recovery tasks.
4. Record observations in the observation form; file issues with the template.
5. Store evidence using the naming convention.

## Consent / privacy notes

- Collect only accessibility observations needed for product improvement.
- Do not capture passwords, credentials, personal portfolio content, or minors' data.
- Redact screenshots that show personal names/emails before upload.
- Participant may stop at any time.

## Task script (per surface)

For each surface above:

1. Navigate using the assigned modality.
2. Confirm focus visibility on interactive controls.
3. Complete one primary task (open/view/edit/export as applicable).
4. Trigger one recoverable error and recover.
5. Note focus traps, missing names/roles, contrast failures, or SR silence.

### Keyboard-only tasks
- Tab/Shift-Tab through primary nav; verify order and visibility.
- Activate each primary surface without pointer.
- Escape/back returns predictably; no keyboard trap.

### Screen-reader tasks (where supported)
- Launch Orca or platform SR.
- Confirm surface title/landmark announcement.
- Confirm actionable controls expose accessible names/roles.
- Confirm status messages are announced.

### Zoom / text-scaling
- 150% and 200% scaling: layout remains usable; no clipped critical controls.

### Color / contrast observation prompts
- Primary text/icons against backgrounds meet expected contrast in default + contrast mode.
- Focus ring remains visible in contrast mode.

### Error / recovery
- Deny a permission or cancel a dialog; user can continue.
- Offline banner/state is perceivable via keyboard/SR.

## Completion criteria (human PASS rule — not auto-claimable)

Human a11y PASS requires uploaded observation forms for the planned participant set, zero unresolved severity-1 issues, and signed facilitator attestation. **This campaign does not claim that PASS.**

## Severity rubric

| Sev | Definition |
|-----|------------|
| 1 | Blocks task completion for the modality |
| 2 | Major barrier with workaround |
| 3 | Minor annoyance / polish |
| 4 | Suggestion |

## Evidence naming convention

`cx4_a11y_<participantId>_<surface>_<modality>_<YYYYMMDD>_<seq>.{png,log,md}`

Upload to: `artifacts/complete_experience/cx4_0/human_a11y/` (created at execution time).

## Facilitator checklist

- [ ] Consent recorded
- [ ] Environment recorded (device profile, SR version, zoom level)
- [ ] Tasks completed per surface
- [ ] Issues filed
- [ ] Evidence uploaded
