# Known Issues — v1.0.0-rc.1

1. Human validation sessions not yet run (`J6_CLASS=HUMAN_VALIDATION_PENDING`).
2. Physical printer / camera-mic AV / EVT / DVT / PVT pending — no physical claim.
3. bootable-reference image rebuild fails on host Python 3.14 (`tarfile.AbsoluteLinkError`); RC1 uses preexisting immutable lab images (checksummed) + Cont VIII digital package.
4. Validation Center npm audit: critical/high findings in Vitest/Vite **test toolchain** (not participant static runtime). Defer dependency major bump to pre-GA.
5. Unity product lanes (Anime Aggressors #51/#52) deferred to v1.1; outside freeze runtime.
