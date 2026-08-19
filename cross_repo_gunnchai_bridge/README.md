# gunnchAI3k ↔ device-os cross-repo bridge

Explicit pin + optional sibling verification. See
[docs/GUNNCHAI_DEVICE_OS_COMPAT_CONTRACT.md](../docs/GUNNCHAI_DEVICE_OS_COMPAT_CONTRACT.md).

| File | Role |
| --- | --- |
| `GUNNCHAI_COMPAT_CONTRACT.json` | Versioned ACCEPTED_MAIN pairing pin |
| `../gunnchos_device_os/cross_repo_gunnchai/contract.py` | Loader + schema validation |
| `../scripts/verify_gunnchai_sibling_contract.py` | Optional sibling artifact check |

Claim boundary: digital contract only. Not physical boot, not frontier parity.
