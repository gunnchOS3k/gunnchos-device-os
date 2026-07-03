# Phase 4A: Encrypted Workspace Storage Prototype

## Claim boundary

**This is a prototype encrypted workspace in the browser launcher shell — not OS full-disk encryption or a production filesystem.**

## What was implemented

| Component | Path |
|-----------|------|
| Web Crypto helpers (PBKDF2 + AES-GCM) | `apps/launcher_mock/src/services/workspaceCrypto.ts` |
| Encrypted session store | `apps/launcher_mock/src/services/encryptedWorkspaceStore.ts` |
| Settings UI | `apps/launcher_mock/src/shell/EncryptedWorkspacePanel.tsx` |
| File Manager / Notes integration | `localWorkspaceStore.ts`, `notesStore.ts` |

## Features

- Passphrase-based encryption via Web Crypto API (PBKDF2-SHA256, AES-GCM)
- Never stores plaintext passphrase — only salt, IV, ciphertext, metadata
- Enable / unlock / lock / change passphrase
- Export and import encrypted backup JSON
- Reset encrypted workspace
- Unencrypted prototype mode continues with warning when encryption disabled
- Migration from existing localStorage workspace on enable

## What is NOT implemented

- Production OS filesystem
- Full-disk encryption
- Hardware-backed keys (TPM/Secure Enclave)
- Cross-device sync
- Encrypted media blobs (File Manager text files only in this slice)

## Tests

```bash
cd apps/launcher_mock && npm test -- encryptedWorkspace
```

## Beta gate

`encrypted_storage` status: **prototype** — browser-backed encrypted workspace only.
