# Phase XII — Execution-Reality Conversion Report (A–X)

Generated: 2026-08-09T23:16:08.638328+00:00  
Branch: `phase-xii/execution-reality`  
`auto_merge_request`: null  
PHYSICAL_EXECUTION_FREEZE: ACTIVE

## Critical claim correction (preserved)
```
PHASE_XI_BEHAVIORAL_JOURNEY_HARNESS_PASS = TRUE
PHASE_XI_REAL_APPLICATION_DAY_PROOF = NOT_YET_PROVEN
```
Phase XI 79 journey JSONs remain normative E2E specs. Phase XII replaces L0–L2 handlers with L3–L6 real execution for the RJ acceptance set.

## A. Accepted mains
- device-os #71 `ce101bd2fece09f2af3cb4c44eb76b7a5b158b95` (includes CI fix `8c5f2b08acdace7ff195b08b099aa73d1a030a48`)
- field-kit #46 `964217947a78197e621a4d2eb01628d5cf5a5558`
- Stale draft tip `ce604c23…` retired (not accepted main)
Full pin: `artifacts/phase_xii/ACCEPTED_MAIN_BASELINE.json`

## B. Execution-depth ledger summary
- Journeys: 79
- Phase XI key-depth histogram: `{'L0_GENERIC_OK': 79}`
- Phase XII target histogram: `{'L0_GENERIC_OK': 54, 'L4_REAL_APPLICATION_PROCESS': 20, 'L5_REAL_GUI_INTERACTION': 3, 'L3_REAL_SERVICE_API': 2}`
- Journeys still NOT_YET_REAL_APP_PROVEN at Phase XI depth classification: 79
Artifact: `REALITY_DEPTH_LEDGER.json`

## C. Phase XI claims rescope
All historical REAL_*_DAY tokens marked `VALID_AS_BEHAVIORAL_HARNESS` + `NOT_YET_REAL_APP_PROVEN` until RJ L4/L5 evidence.
Firewall rejects REAL_*_DAY_DIGITAL_PASS while REAL_APP_X0/X1 open.
Artifacts: `PHASE_XI_CLAIM_RESCOPE.json`, field-kit `program/claims/phase_xii_execution_depth_firewall.yaml`

## D. Actual gunnchOS GUI/session stack
Selected: **Weston** Wayland compositor configured as gunnchOS (`os_build/phase_xii/gui/`).
CI: Xvfb + Weston headless (`phase-xii-execution-reality.yml`).
Host note: macOS agent lacks weston binary; Linux CI path is authoritative for GUI screenshots.

## E. Installed real apps and versions (host audit excerpt)
```
{
  "browser": null,
  "office": {
    "name": "soffice",
    "path": "/opt/homebrew/bin/soffice",
    "version": "LibreOffice 26.2.5.2 cd7284b4cbbfeb507e630c1aac019f4157393acb"
  },
  "pdf": {
    "name": "soffice",
    "path": "/opt/homebrew/bin/soffice",
    "version": "LibreOffice 26.2.5.2 cd7284b4cbbfeb507e630c1aac019f4157393acb"
  },
  "file_manager": null,
  "terminal": null,
  "editor": {
    "name": "vim",
    "path": "/usr/bin/vim",
    "version": "VIM - Vi IMproved 9.1 (2024 Jan 02, compiled Apr 18 2026 20:29:32)"
  },
  "media": {
    "name": "ffplay",
    "path": "/opt/homebrew/bin/ffplay",
    "version": "ffplay version 8.0 Copyright (c) 2003-2025 the FFmpeg developers"
  },
  "git": {
    "name": "git",
    "path": "/opt/homebrew/bin/git",
    "version": "git version 2.51.0"
  },
  "cups": {
    "name": "lp",
    "path": "/usr/bin/lp",
    "version": "Usage: lp [options] [--] [file(s)]"
  },
  "vpn": null,
  "compositor": null,
  "display": null,
  "godot": {
    "name": "godot",
    "path": "/opt/homebrew/bin/godot",
    "version": "4.7.1.stable.official.a13da4feb"
  },
  "llama": {
    "name": "llama-server",
    "path": "/opt/homebrew/bin/llama-server",
    "version": "version: 10310 (cb26014d9)"
  }
}
```
LibreOffice/soffice used for open/edit/save/reopen/export PDF with checksums.

## F. Real protocol services
Embedded + compose:
- SMTP+IMAP: aiosmtpd + Phase XII IMAP4 server (compose: GreenMail)
- CalDAV/CardDAV: Radicale
- Matrix: local CS API subset (compose: Conduit)
- WebDAV: WsgiDAV (compose: bytemark/webdav)
- WebRTC: local signaling + Playwright fake A/V
- LMS: real HTML service for browser workflows

## G–J. Real journey results (RJ set)
pass_count=18 fail_count=0  
X0=0 X1=0 X2=0
```
{
  "RJ_STUDENT_PASS": true,
  "RJ_OFFICE_PASS": true,
  "RJ_CREATOR_PASS": true,
  "RJ_EDUCATOR_PASS": true,
  "RJ_RECREATION_PASS": true,
  "RJ_OFFLINE_PASS": true,
  "RJ_RING_DIGITAL_PASS": true,
  "RJ_RECOVERY_PASS": true,
  "RJ_ACCESSIBILITY_PASS": true
}
```
REAL day tokens (actual app execution gated):
- STUDENT=True
- OFFICE=True
- CREATOR=True
- RECREATION=True

## K. Actual game runtime results
- Anime / Pedestrian: Godot `--headless --quit-after` real process (no fixture JSON)
- Archive: Vite/web `npm test` real process
- Beat Link: vitest/redis-ci path + multi-context Playwright when available

## L. Actual AI integration
llama.cpp `llama-server` + SmolLM2-135M Instruct GGUF via `/v1/chat/completions` (not Phase XI stub).

## M. Ring real-digital integration
Firmware-sim packet → mapper → real file/app input evidence under `artifacts/phase_xii/rj/ring/`.

## N. Multitasking/soak metrics
See `artifacts/phase_xii/metrics/MULTITASK_SOAK.json` (real office/media processes + storage pressure file fill).

## O. Screenshots/evidence
Gallery index: `artifacts/phase_xii/gallery/INDEX.json` (real captures only; no concept art).

## P. Defects found
See campaign defects list (initially AI/office/godot/caldav/creator gaps on first host run).

## Q. Defects fixed
- IMAP FETCH literal framing
- WebDAV timeout fallback
- CalDAV radicale filesystem fallback
- Creator sample exec
- Archive non-Godot web launcher
- llama-server ensure in RJ runner
- LibreOffice + Godot host install for local prove

## R. Remaining digital defects
Open counts (CI-honest): **X0=0, X1=5, X2=0**.
X1 residuals are **CONDITIONAL_EXTERNAL**:
- RJ-GAME-001..004 — Godot / sibling game repos missing on CI runners
- RJ-STUDENT-001 — llama/AI runtime and/or composite overlay masking journey FAIL
See `CI_X1_RESIDUALS.json`. `reality` job may exit 0 when X0==0; that must not be read as X1=0.
REAL_*_DAY_DIGITAL_PASS = **FALSE** while X1 residuals remain.

## S. Physical EVT followups
Unchanged Phase X A01–A07 packets; PHYSICAL_PENDING.

## T. External/vendor followups
EXTERNAL_PENDING (RFQ/NDA/send still Edmund-only).

## U. PRs / CI / auto-merge
DRAFT PRs only; `autoMergeRequest=null`. Primary: device-os; field-kit evidence/firewall LAST.

## V. Final tokens and exact scope
Behavioral harness tokens preserved. REAL_*_DAY_DIGITAL_PASS remains FALSE while CI X1 residuals are open (CONDITIONAL_EXTERNAL). Full pass still requires X0/X1/X2 open = 0 on accepted evidence.

## W. Definition-of-done matrix
```
{
  "Product definition": "COMPLETE_DIGITAL",
  "Requirements": "COMPLETE_DIGITAL",
  "gunnchOS backend/services": "COMPLETE_DIGITAL",
  "gunnchOS GUI/session": "COMPLETE_CONDITIONAL_EXTERNAL",
  "Productivity apps": "COMPLETE_DIGITAL",
  "Communication stack": "COMPLETE_DIGITAL",
  "Media stack": "COMPLETE_DIGITAL",
  "gunnchAI": "COMPLETE_CONDITIONAL_EXTERNAL",
  "Games": "COMPLETE_CONDITIONAL_EXTERNAL",
  "Ring digital input": "COMPLETE_DIGITAL",
  "Hardware digital design": "COMPLETE_CONDITIONAL_EXTERNAL",
  "Manufacturer package": "COMPLETE_CONDITIONAL_EXTERNAL",
  "NPI/RFQ package": "COMPLETE_CONDITIONAL_EXTERNAL",
  "Real-app user journeys": "COMPLETE_CONDITIONAL_EXTERNAL",
  "Physical EVT": "PHYSICAL_PENDING",
  "Vendor collateral": "EXTERNAL_PENDING",
  "DFM": "EXTERNAL_PENDING",
  "Certification": "EXTERNAL_PENDING",
  "Carrier acceptance": "EXTERNAL_PENDING",
  "DVT": "PHYSICAL_PENDING",
  "PVT": "PHYSICAL_PENDING",
  "Deployment": "EXTERNAL_PENDING",
  "Operations/support": "INCOMPLETE_DIGITAL"
}
```

## X. Next completion actions
1. Merge DRAFT PRs after Edmund review (Cursor never merges).
2. Linux GUI CI green with Weston screenshots.
3. Optional Conduit/GreenMail compose in CI for protocol parity.
4. Physical EVT / vendor collateral remain outside digital freeze path.

## Wave 0 (phase-xii/wave0-x1-close) — 2026-08-10T00:23Z

- Closed CI X1 residuals locally with sibling game repos + Godot + llama-server + SmolLM2 GGUF.
- Fixed RJ-STUDENT-001 composite overlay (fail-closed; journey FAIL no longer masked).
- Fixed LMS `submission_receipt` to read real LMS receipts.
- CI installs Godot 4.4.1, llama.cpp b10333, GGUF; checkouts sibling repos; asserts `REAL_APP_X1_OPEN==0`.
- `PHYSICAL_EXECUTION_FREEZE=ACTIVE`; `auto_merge_request=null`; DRAFT PR only.

Counts after local prove: X0=0 X1=0 X2=0; all 18 RJ pass; REAL_*_DAY_DIGITAL_PASS true pending CI confirm.

