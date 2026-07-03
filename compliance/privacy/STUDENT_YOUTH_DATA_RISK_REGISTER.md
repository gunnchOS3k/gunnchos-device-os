# Student / Youth Data Risk Register

| ID | Risk | Likelihood | Impact | Mitigation (current) | Residual |
|----|------|------------|--------|----------------------|----------|
| YR-001 | Student notes stored unencrypted in browser | Medium | Medium | Encrypted workspace prototype (PR #44); export guidance | High until OS FS |
| YR-002 | Profile display name in localStorage | Low | Low | Optional field; no cloud sync | Low |
| YR-003 | External browser tab exposes student to third-party trackers | Medium | High | Policy modes block/warn; disclaimers | High until embedded browser controls |
| YR-004 | AI assistant sends prompts to vendor | N/A | High | **Not implemented** — UI only | None today |
| YR-005 | Guardian mode bypass via devtools | Medium | Medium | Shell prototype only — not hardware enforcement | High |
| YR-006 | School mode insufficient for FERPA | High | High | Document boundaries; no certification claim | High |
| YR-007 | Library guest session data retention | Medium | Medium | Session design in MDM samples; not enforced | Medium |

**Review required:** Legal counsel before claiming education compliance.
