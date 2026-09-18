# Human Validation Day Runbook

Usable by operators (including Edmund) without reading source code.

This runbook is for **pilot / final-prep** use of the Validation Center.  
It does **not** by itself make `CX4_FINAL_HUMAN_VALIDATION_ELIGIBLE=true`.

## What computer / device to use

- A laptop or workstation that can run host-side Device OS tools (no QEMU required).
- The device under test (Student 14.5, Handheld Hybrid, DS-XL, Edge I/O, dock, etc.) when the pack requires it.
- Prefer the **accepted release / main build** once it exists. Until then, sessions default to **PILOT_NON_GATING**.

## What branch / release is eligible

- Final gating requires a frozen, accepted build (see `validation-center freeze-check`).
- Today the CX Validation Center stack is still **DRAFT / unmerged**, so:
  - `CX4_FINAL_HUMAN_VALIDATION_ELIGIBLE=false`
  - New sessions default to `PILOT_NON_GATING`
  - Rehearsals are `REHEARSAL_NON_GATING` and never count as real human evidence

## How to launch

```bash
./scripts/start-validation-center
# or
make validation-center
```

Loopback default (`127.0.0.1`). For phones on the same LAN only:

```bash
./scripts/start-validation-center --lan
```

LAN mode warns about exposure, uses high-entropy tokens, and does not list sessions anonymously. Revoke access when done.

Shutdown (only this launcher’s process):

```bash
./scripts/start-validation-center --stop
```

## Links (after launch)

- Participant entry: `http://127.0.0.1:8765/#entry`
- Participant flow: `http://127.0.0.1:8765/#participant`
- Moderator: `http://127.0.0.1:8765/#moderator`
- Reviewer: `http://127.0.0.1:8765/#reviewer`

## How to start a session (moderator)

1. Open Moderator → guided wizard (6 steps).
2. Choose pack(s): Human Accessibility, Printer, Camera/Mic/AV, Peripheral, Device EVT, Ergonomics, Support/Recovery, or custom tasks.
3. Record device/SKU, build/version, commit (shown at launch), hardware notes.
4. Use a **participant alias** (preferred).
5. Select required media consent expectations.
6. Review tasks + expected duration.
7. Launch → copy **session code** + participant URL / QR guidance.
8. Eligibility stays **PILOT_NON_GATING** (moderator cannot force FINAL).

## Accessibility options

Participants can set larger text, high contrast, simplified instructions, and reduced motion **before Start**, and again via Accessibility Options.

## What evidence to capture

Use the evidence buttons: Screenshot, Photo, Video, Audio, File, Note, Report Issue.  
Consent is shown before attach. If capture is unavailable, use file upload — the session must not fail.

## How ratings work

Per task: completion, ease / confidence / satisfaction (labeled 1–5), accessibility impact, optional comfort, free-text prompts. Free text is never mandatory. “Prefer not to answer” is available for optional scales. Ratings autosave and survive restart.

## How submission works

Complete tasks → Final review → Submit Session. Submitted snapshots are immutable. Amendments create a new version.

## How review / signoff works

Reviewer opens **Awaiting Review**, inspects pack / build / **gating eligibility class**, ratings, evidence, issues. Actions: evidence sufficient/insufficient, clarification, pass/fail/not assessable, sign review.  
Reviewers **cannot** turn rehearsal/pilot into `FINAL_GATING_ACCEPTED`.

## How to export evidence

```bash
PYTHONPATH=.:src python3 -m gunnchos_device_os.cx4_validation_center export  # via service API / qualify paths
```

Exports: JSON, CSV, static HTML, evidence ZIP. Eligibility class is preserved. Private evidence is excluded from public/share exports by default.

## If a participant stops

Use Pause / Stop session. Progress autosaves. Resume with the same session code + token (unless revoked).

## If the app crashes

Restart with `./scripts/start-validation-center`. Autosave / backup pending sessions; restore preserves ratings and evidence.

## How to identify material drift

```bash
PYTHONPATH=.:src python3 -m gunnchos_device_os.cx4_validation_center freeze-check
PYTHONPATH=.:src python3 -m gunnchos_device_os.cx4_validation_center compare-freeze <submission.json>
```

Material classes include UI, accessibility, task logic, evidence pipeline, device behavior. Material drift invalidates reuse of final evidence and recommends targeted revalidation.

## Where evidence is stored

Local-first under the Validation Center store / `artifacts/complete_experience/cx4_2/` for this campaign. No hidden cloud upload.

## Freeze check (today)

`FINAL_GATING_ELIGIBLE=false` until an accepted frozen target exists. The freeze-check command explains missing conditions.
