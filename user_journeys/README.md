# Phase XI user journeys

Machine-readable real-user journey harness for gunnchOS3k.

- `personas/` — P01–P15
- `journeys/` — J-* definitions (schema in `schema/`)
- `fixtures/` — local legal fixtures (no commercial cloud)
- `services/` — discovery for in-process IMAP/SMTP/CalDAV/Matrix/WebDAV/WebRTC/LMS/ring/MDM
- `evidence/` — per-journey run evidence
- `reports/` — campaign, tokens, defects, A–R

Run:

```bash
make phase-xi-test
make phase-xi-representative
make phase-xi-journeys
```

`PHYSICAL_EXECUTION_FREEZE` remains active. Tokens are earned only when blocking journeys pass.
