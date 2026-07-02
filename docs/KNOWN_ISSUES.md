# GunnchOS Known Issues

**Last updated:** Phase 4D secure boot / MDM architecture + Phase 4E streaming (2026-07-02)  
**Beta claim:** Not allowed — see [release_artifacts/BETA_CANDIDATE_REPORT.md](../release_artifacts/BETA_CANDIDATE_REPORT.md)

| ID | Severity | Area | Status | Workaround | Beta impact | Owner | Release blocker |
|----|----------|------|--------|------------|-------------|-------|-----------------|
| KI-001 | High | Storage | Open | Use browser localStorage workspace; export JSON manually | No production filesystem | shell | Yes |
| KI-002 | High | Storage | Open | None — encrypted OS storage not implemented | Data not hardware-protected | platform | Yes |
| KI-003 | High | Productivity | Open | Open Google Drive in external browser tab | No offline sync | shell | Yes |
| KI-004 | High | Browser | Open | External tab opens via `appLaunchService` | No embedded certified shell | shell | Yes |
| KI-005 | High | Media | Open | Use disclaimers; open Netflix/Hulu in browser; track readiness in `streaming_certification/` | No service certification — readiness package only (Phase 4E) | media | Yes |
| KI-017 | High | Media | Open | See `streaming_certification/CDM_READINESS_CHECKLIST.md` | Widevine/CDM not integrated | media | Yes |
| KI-018 | Medium | Media | Open | See `streaming_certification/HDCP_EXTERNAL_DISPLAY_CHECKLIST.md` | HDCP external display not validated | media | Yes |
| KI-006 | Medium | Media | Open | Re-select local files after refresh | Blobs not persisted across refresh | media | Yes |
| KI-007 | High | OS Build | Open | Use container kiosk prototype | Not bootable on hardware | os_build | Yes |
| KI-008 | High | Hardware | Open | Use Docker/kiosk validation log only | No physical device validation | hardware | Yes |
| KI-009 | High | Security | In progress | Use dev manifest signing prototype only | No production secure boot — architecture + dev signing in Phase 4D | platform | Yes |
| KI-010 | High | Fleet | In progress | Use `mdm/device_policy_agent.py` for local policy eval | No production MDM — schema + prototype agent in Phase 4D | fleet | Yes |
| KI-011 | Medium | Accessibility | Open | Use in-app toggles (large text, contrast, motion) | No WCAG certification | a11y | Yes |
| KI-012 | High | Privacy | Open | Review `PRIVACY_BETA_BASELINE.md` | No legal/privacy review | privacy | Yes |
| KI-013 | Medium | Games | Open | Play Anime Aggressors web slice only | Foot Racing / Earth Species not connected | game | Partial |
| KI-014 | Low | Games | Open | Launch from Game Mode when web build available | Vertical slice only — not full game | game | No |
| KI-015 | Medium | Policy | In progress | Use deployment mode selector for testing | Shell prototype — not production MDM | policy | Yes |
| KI-016 | Medium | AI | Open | UI panel only | No AI backend; privacy toggle local only | ai | Yes |

## Sections

- **Severity:** Critical / High / Medium / Low
- **Status:** Open / In progress / Mitigated / Won't fix (prototype)
- **Beta impact:** Whether this blocks a honest beta claim
- **Release blocker:** Yes if beta cannot be claimed until resolved or documented with honest boundary
