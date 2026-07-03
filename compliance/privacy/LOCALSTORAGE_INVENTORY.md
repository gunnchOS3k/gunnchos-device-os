# localStorage Inventory (launcher shell)

| Key | Module | PII risk | Youth data |
|-----|--------|----------|------------|
| `gunnchos-profile` | Onboarding | Low (display name optional) | Possible if student enters name |
| `gunnchos-settings-v1` | Settings | None | Preference data only |
| `gunnchos-workspace-v1` | File Manager | User-dependent | User-created files |
| `gunnchos-notes-v1` | Notes | User-dependent | User-created notes |
| `gunnchos-encrypted-workspace-v1` | Encrypted workspace (PR #44) | User-dependent | Encrypted at rest in browser |
| `gunnchos-local-media-recent` | Local media | Low (filenames) | Possible filenames |
| `gunnchos-deployment-mode` | Policy | None | Mode selection only |

**Passphrase for encrypted workspace is never stored in localStorage.**
