# Storage Security Boundary

## Honest claims

| Claim | Allowed? | Evidence |
|-------|----------|----------|
| Browser localStorage workspace prototype | Yes | Phase 2A |
| Encrypted workspace prototype (Web Crypto) | Yes | Phase 4A |
| Production OS filesystem | **No** | Not implemented |
| Full-disk encryption | **No** | Not implemented |
| Hardware-protected keys | **No** | Not implemented |

## Encrypted workspace prototype (Phase 4A)

- **Algorithm:** AES-GCM with PBKDF2-SHA256 key derivation
- **Stored:** salt, IV, ciphertext, metadata in `gunnchos-encrypted-workspace-v1`
- **Not stored:** passphrase (session memory only while unlocked)
- **Scope:** File Manager text files and Notes content in launcher shell

## Unencrypted fallback

When encryption is disabled, workspace and notes persist in plain `localStorage` with visible prototype warnings in Settings.

## Remaining P0 blocker

Production filesystem / encrypted storage at OS layer remains open until real scoped storage and hardware-backed encryption exist outside the browser shell.
