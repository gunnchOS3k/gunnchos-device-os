# GunnchOS Known Issues

**Last updated:** Phase 4H beta gate reconciliation (2026-07-02)  
**Beta claim:** Not allowed — see [release_artifacts/BETA_CANDIDATE_REPORT.md](../release_artifacts/BETA_CANDIDATE_REPORT.md)

| ID | Severity | Area | Status | Workaround | Beta impact | Owner | Release blocker |
|----|----------|------|--------|------------|-------------|-------|-----------------|
| KI-001 | High | Storage | Open | Use browser localStorage workspace; export JSON manually | No production filesystem | shell | Yes |
| KI-002 | High | Storage | In progress | Enable encrypted workspace prototype in Settings (Phase 4A) | Browser crypto only — not OS/hardware encryption | platform | Yes |
| KI-003 | High | Productivity | Open | Open Google Drive in external browser tab | No offline sync | shell | Yes |
| KI-004 | High | Browser | Open | External tab opens via `appLaunchService` | No embedded certified shell | shell | Yes |
| KI-005 | High | Media | Open | Use disclaimers; track readiness in `streaming_certification/` (Phase 4E) | No official service certification — readiness only | media | Yes |
| KI-017 | High | Media | Open | See `streaming_certification/CDM_READINESS_CHECKLIST.md` | No Widevine/CDM integration; no DRM circumvention | media | Yes |
| KI-018 | Medium | Media | Open | See `streaming_certification/HDCP_EXTERNAL_DISPLAY_CHECKLIST.md` | HDCP external display not validated on hardware | media | Yes |
| KI-019 | Medium | Media | Open | See `SERVICE_CERTIFICATION_TRACKER.yaml` | Service tracker cannot mark certified without evidence path | media | Yes |
| KI-006 | Medium | Media | Open | Re-select local files after refresh | Local media player separate from DRM streaming; blobs not persisted | media | Yes |
| KI-007 | High | OS Build | In progress | Use OS-layer installable bundle prototype (Phase 4B) | Not bootable ISO/IMG — no boot evidence | os_build | Yes |
| KI-008 | High | Hardware | In progress | Use validation package + container log (Phase 4C) | No physical device report — template/container/host-info only | hardware | Yes |
| KI-009 | High | Security | Open | Document claim boundaries; merge PR #46 for architecture track | No production secure boot on hardware | platform | Yes |
| KI-010 | High | Fleet | Open | Merge PR #46 for MDM prototype; shell policy for testing | No production MDM enrollment/server | fleet | Yes |
| KI-011 | Medium | Accessibility | In progress | WCAG self-assessment + a11y toggles (Phase 4F) | No WCAG certification | a11y | Yes |
| KI-012 | High | Privacy | In progress | Compliance readiness packet (Phase 4F) | No legal/privacy certification | privacy | Yes |
| KI-013 | Medium | Games | Open | Play all three web vertical slices from Game Mode | Vertical slices only — not full games | game | Partial |
| KI-014 | Low | Games | Open | Launch from Game Mode when web build available | Vertical slice only | game | No |
| KI-015 | Medium | Policy | In progress | Deployment mode selector for testing | Shell prototype — not production MDM | policy | Yes |
| KI-016 | Medium | AI | Open | UI panel only | No AI backend | ai | Yes |

## Streaming certification boundaries (Phase 4E)

- No Widevine/CDM integration
- No official Netflix, Hulu, Disney+, Max, Prime Video certification
- No DRM circumvention
- HDCP external display not validated on reference hardware
- Max confirmed resolution unknown unless evidence path exists
- Local media player is separate from DRM-protected streaming

## Sections

- **Severity:** Critical / High / Medium / Low
- **Status:** Open / In progress / Mitigated / Won't fix (prototype)
- **Beta impact:** Whether this blocks a honest beta claim
- **Release blocker:** Yes if beta cannot be claimed until resolved or documented with honest boundary
