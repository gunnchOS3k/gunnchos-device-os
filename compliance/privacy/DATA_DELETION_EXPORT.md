# Data Deletion and Export Notes

## Export (available in prototype)

| Data | Export path |
|------|-------------|
| Workspace | File Manager → export JSON |
| Notes | Notes app → export JSON |
| Encrypted workspace | Settings → encrypted backup export (PR #44) |

## Deletion

| Action | Effect |
|--------|--------|
| Reset workspace / notes | Clears respective localStorage keys |
| Reset encrypted workspace | Clears encrypted envelope + re-seeds demo |
| Clear browser site data | Removes all GunnchOS localStorage for origin |
| Re-run onboarding | Resets profile key |

## Not implemented

- Secure wipe of OS partition
- Remote wipe via MDM
- Cross-device deletion sync

## DPIA template

See [DPIA_TEMPLATE.md](DPIA_TEMPLATE.md) for processing activity documentation.
