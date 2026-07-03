# GunnchOS Data Inventory (Phase 4F readiness)

**Status:** Self-assessment — not legal certification.

## Local browser storage (launcher shell)

| Key | Data class | Contents | Retention | Export | Delete |
|-----|------------|----------|-----------|--------|--------|
| `gunnchos-profile` | Profile | Onboarding choices, display name | Until cleared | Manual JSON export N/A | Re-run onboarding / clear storage |
| `gunnchos-settings-v1` | Preferences | Theme, a11y, offline, AI privacy | Persistent | Settings UI | Clear localStorage |
| `gunnchos-workspace-v1` | User content | File manager text files (unencrypted mode) | Persistent | File Manager export | Reset workspace |
| `gunnchos-notes-v1` | User content | Notes titles and bodies | Persistent | Notes export | Reset notes |
| `gunnchos-encrypted-workspace-v1` | User content (encrypted) | AES-GCM ciphertext (Phase 4A pending PR #44) | Persistent | Encrypted backup export | Reset encrypted workspace |
| `gunnchos-local-media-recent` | Metadata | Recent local media filenames/paths | Persistent | None | Clear in app |
| `gunnchos-deployment-mode` | Policy test | School/Library/Guardian mode selector | Persistent | N/A | Clear localStorage |

## Server-side / cloud (prototype)

| System | Status | Notes |
|--------|--------|-------|
| Analytics pipeline | Not implemented | No telemetry transmission in prototype |
| Cloud sync | Not implemented | |
| AI assistant backend | Not implemented | UI shell only |
| MDM fleet server | Not implemented | Phase 4D local policy only |

## Third-party services (browser tab launches)

External services (Google, Netflix, etc.) have their own privacy policies when opened via browser — GunnchOS does not embed certified CDM shells.

See [THIRD_PARTY_DEPENDENCIES.md](../legal/THIRD_PARTY_DEPENDENCIES.md).
