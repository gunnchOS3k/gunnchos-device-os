# What Is Real Today

**Last updated:** Phase 4H beta gate reconciliation (2026-07-02). Full audit: [FULL_OPERATIONAL_GAP_MATRIX.md](FULL_OPERATIONAL_GAP_MATRIX.md)

## Real (validated in repo)

- `gunnchos_device_os` Python policy package + `config/modes.yaml`
- CI gate: contract export, pytest, frontend build/test (`make validate-full`)
- **File Manager v1** — browser localStorage workspace (`FileManager.tsx`)
- **Notes app v1** — browser localStorage (`NotesApp.tsx`)
- **Encrypted workspace prototype (Phase 4A)** — Web Crypto PBKDF2 + AES-GCM in launcher shell ([PHASE4A_ENCRYPTED_WORKSPACE.md](PHASE4A_ENCRYPTED_WORKSPACE.md))
- **Browser/PWA open behavior** — external tab launches (`appLaunchService.ts`)
- **Local Media Player v1** — merged as a browser-backed local playback prototype (`LocalMediaPlayer.tsx`)
  - HTML5 audio/video file picker
  - Recent media metadata in localStorage only
  - **Does not** persist media blobs across refresh
  - **Does not** handle DRM streaming
  - **Not** a production OS media library
- **Game launch adapter** + **first-party web vertical slices** (Anime Aggressors, Foot Racing, Earth Species)
- **Shell policy enforcement** — `policyEnforcementService.ts` (not production MDM)
- **Settings persistence** — theme, a11y, offline, AI privacy toggles
- **Beta gate dashboard** — `beta_gate/beta_gate_status.yaml` + validator
- **Known issues registry** — `docs/KNOWN_ISSUES.md`
- **Accessibility / privacy baselines** — documented, not certified
- **Installable OS image track (Phase 4B)** — reproducible OS-layer bundle prototype ([PHASE4B_INSTALLABLE_IMAGE.md](PHASE4B_INSTALLABLE_IMAGE.md))
  - `scripts/build_installable_image.sh` produces tarball + manifest + checksums
  - **Not** a bootable ISO/IMG
  - **Not** hardware-validated
- **Image prototype track** — container kiosk packaging (Phase 2F)
- **Reference hardware validation package (Phase 4C)** — matrix, templates, collector ([PHASE4C_HARDWARE_VALIDATION.md](PHASE4C_HARDWARE_VALIDATION.md)); no physical device report
- **Streaming certification readiness (Phase 4E)** — tracker and checklists ([PHASE4E_STREAMING_CDM_CERTIFICATION.md](PHASE4E_STREAMING_CDM_CERTIFICATION.md)); not certified
- **Compliance readiness packet (Phase 4F)** — self-assessment docs ([PHASE4F_COMPLIANCE_READINESS.md](PHASE4F_COMPLIANCE_READINESS.md)); not certified

## Prototype / honest labels

- Browser/PWA — external tab route; no embedded browser shell
- Local media — browser file picker prototype; metadata-only persistence
- Local workspace / notes — browser localStorage; optional encrypted prototype (not OS FS)
- Policy enforcement — shell UI prototype
- Media Mode streaming — browser route prototypes; Netflix/Hulu DRM disclaimers only
- Bootable / installable image — OS-layer bundle prototype (Phase 4B); not bootable ISO, not hardware-validated
- Hardware — validation package only; no physical device report (Phase 4C)
- Streaming — readiness tracking only; no CDM or service certification (Phase 4E)
- Games — all three first-party titles are web vertical slices only; not full games or native builds
- AI assistant — UI shell only
- Settings — system stats (storage/RAM/Wi-Fi) still mock labels

## Not real (not claimed)

- Production OS filesystem / full-disk encrypted storage (Phase 4A is browser prototype only)
- Google Drive sync
- Bootable OS image on target hardware (Phase 4B bundle is not a bootable ISO/IMG)
- Kernel, secure boot, TPM validation
- Official Netflix/Hulu/Disney+ certification / DRM CDM
- Production MDM/fleet deployment
- Real browser CDM integration
- Accessibility or privacy legal certification
- GA / beta release claim (`beta_ready: false`)

## Release readiness

| Stage | Met? |
|-------|------|
| Alpha (shell + policy) | **Yes** |
| Beta candidate | **No** — see [BETA_CANDIDATE_REPORT.md](../release_artifacts/BETA_CANDIDATE_REPORT.md) |
| RC / GA / Production | **No** |

Smoke: `make validate-full` · Beta gate: `python3 scripts/validate_beta_gate.py`
