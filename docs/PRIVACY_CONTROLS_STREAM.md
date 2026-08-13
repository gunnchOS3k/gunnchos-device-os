# Privacy controls + digital inventory STREAM

**Digital prep only.** Legal approval remains **HUMAN/EXTERNAL**.
**EXTERNAL_PENTEST_COMPLETE=false.** Does **not** claim E7, COPPA, FERPA, GDPR,
or production privacy/security readiness.

## Implemented (this PR)

- Enforceable local privacy controller: accounts, telemetry, AI context/memory,
  voice/vision/screen, Ring, WAIKE/minors, games, diagnostics.
- Minimization, permissions, export, delete, retention, revocation, log redaction.
- Child/minor profiles with guardian gates (software policy, not kernel).
- Automated SBOM / HBOM / AI-BOM inventory. Unknown provenance →
  `UNKNOWN_RELEASE_BLOCKING`.
- Beat Link catalog rights scan; Archive provenance field check; AI model
  license fields machine-tracked.
- External pentest *readiness* package (scope, hashes, threat-model IDs,
  endpoints, RoE schema).

## Pending HUMAN / EXTERNAL

- Legal review of privacy policy / youth data (counsel).
- License determinations still `REVIEW_REQUIRED` in the field-kit license register.
- Commissioned EXTERNAL pentest execution and E7 evidence.
- Production trust root, physical Ring, live school tenant.
- Any claim of shipping/release with remaining `UNKNOWN_RELEASE_BLOCKING`.

## Remaining OPEN

- WP-006 license-release-gate complete audit (not started as a cycle packet).
- Human usability / guardian UX copy.
- Physical / RF Ring pairing privacy.
- Vendor RoE signature and lab SHA freeze for an actual engagement.
