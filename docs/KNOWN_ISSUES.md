# GunnchOS Known Issues

**Last updated:** Phase 4E streaming certification readiness rebase after Phase 4C merge (2026-07-02)  
**Beta claim:** Not allowed — see [release_artifacts/BETA_CANDIDATE_REPORT.md](../release_artifacts/BETA_CANDIDATE_REPORT.md)

| ID | Severity | Area | Status | Workaround | Beta impact | Owner | Release blocker |
|----|----------|------|--------|------------|-------------|-------|-----------------|
| KI-001 | High | Storage | Open | Use browser localStorage workspace; export JSON manually | No production filesystem | shell | Yes |
| KI-002 | High | Storage | In progress | Enable encrypted workspace prototype in Settings (Phase 4A) | Browser crypto only — not OS/hardware encryption | platform | Yes |
| KI-003 | High | Productivity | Open | Open Google Drive in external browser tab | No offline sync | shell | Yes |
| KI-004 | High | Browser | Open | External tab opens via `appLaunchService` | No embedded certified shell | shell | Yes |
| KI-005 | High | Media | Open | Use disclaimers; open services in browser; track readiness in `streaming_certification/` | No official Netflix/Hulu/Disney+/Max/Prime certification — readiness tracking only (Phase 4E) | media | Yes |
| KI-017 | High | Media | Open | See `streaming_certification/CDM_READINESS_CHECKLIST.md` | No Widevine/CDM integration; no DRM circumvention | media | Yes |
| KI-018 | Medium | Media | Open | See `streaming_certification/HDCP_EXTERNAL_DISPLAY_CHECKLIST.md` | HDCP external display not validated on hardware | media | Yes |
| KI-019 | Medium | Media | Open | See `SERVICE_CERTIFICATION_TRACKER.yaml` — max resolution unknown unless evidence path exists | Service tracker cannot mark certified without evidence | media | Yes |
| KI-006 | Medium | Media | Open | Re-select local files after refresh | Local media player is separate from DRM-protected streaming; blobs not persisted | media | Yes |
| KI-007 | High | OS Build | In progress | Use OS-layer installable bundle prototype (Phase 4B) | Not bootable ISO/IMG — no boot evidence | os_build | Yes |
| KI-008 | High | Hardware | In progress | Use validation package + container log; fill report on reference hardware | No physical device report — template/container/host-info only (Phase 4C) | hardware | Yes |
| KI-009 | High | Security | Open | Document claim boundaries only | No production secure boot | platform | Yes |
| KI-010 | High | Fleet | Open | None | No production MDM | fleet | Yes |
| KI-011 | Medium | Accessibility | In progress | Use WCAG self-assessment + a11y toggles (Phase 4F readiness) | No WCAG certification | a11y | Yes |
| KI-012 | High | Privacy | In progress | Review compliance readiness packet (Phase 4F) | No legal/privacy certification | privacy | Yes |
| KI-013 | Medium | Games | Open | Play all three web vertical slices from Game Mode | Vertical slices only — not full games or native builds | game | Partial |
| KI-014 | Low | Games | Open | Launch from Game Mode when web build available | Vertical slice only — not full game | game | No |
| KI-015 | Medium | Policy | In progress | Use deployment mode selector for testing | Shell prototype — not production MDM | policy | Yes |
| KI-016 | Medium | AI | Open | UI panel only | No AI backend; privacy toggle local only | ai | Yes |

## Sections

- **Severity:** Critical / High / Medium / Low
- **Status:** Open / In progress / Mitigated / Won't fix (prototype)
- **Beta impact:** Whether this blocks a honest beta claim
- **Release blocker:** Yes if beta cannot be claimed until resolved or documented with honest boundary

## Streaming certification boundaries (Phase 4E)

- No Widevine/CDM integration in this build
- No official Netflix, Hulu, Disney+, Max, Prime Video, or other partner certification
- No DRM circumvention — ever
- Compatibility tracking is readiness/evidence only
- HDCP external display behavior is not validated on reference hardware
- Max confirmed resolution per service remains unknown/untested unless an evidence path is recorded
- Local HTML5 media player is separate from DRM-protected streaming services
