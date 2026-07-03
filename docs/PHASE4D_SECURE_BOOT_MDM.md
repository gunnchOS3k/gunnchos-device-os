# Phase 4D: Secure Boot and MDM Architecture

**Status:** Architecture + dev tooling prototype. Not production secure boot or MDM.

## Secure boot track

| Artifact | Path |
|----------|------|
| Architecture + Mermaid diagram | `security/secure_boot/ARCHITECTURE.md` |
| Claim boundary | `security/secure_boot/CLAIM_BOUNDARY.md` |
| Checklist | `security/secure_boot/SECURE_BOOT_CHECKLIST.md` |
| Dev key generation | `scripts/generate_dev_signing_keys.sh` |
| Manifest signing | `scripts/sign_release_manifest.py` |
| Manifest verification | `scripts/verify_release_manifest.py` |

### What works today

- Development RSA key pair generation (gitignored under `dev_keys/`)
- Sign/verify `release_artifacts/version_manifest.example.json` digest in CI tests

### What does not work today

- Bootloader/kernel signing on real hardware
- Firmware trust anchor
- TPM measured boot
- Rollback protection enforcement

## MDM track

| Artifact | Path |
|----------|------|
| Policy schema | `mdm/policy_schema.yaml` |
| Sample policies | `mdm/sample_policies/` |
| Enrollment example | `mdm/enrollment_profile.example.json` |
| Local policy agent | `mdm/device_policy_agent.py` |
| Claim boundary | `mdm/CLAIM_BOUNDARY.md` |

### Policy areas covered

- Allowed / blocked apps
- School, library, guardian mode settings
- Network restrictions (placeholder)
- Update channel
- Telemetry consent level
- Media and game restrictions

### What does not work today

- Remote MDM server
- Device enrollment and identity provisioning
- Remote policy push / ACK / rollback
- Fleet inventory or remote wipe

## Tests

```bash
pytest tests/test_secure_boot_mdm.py -q
```

## Beta gate

- `secure_boot`: prototype
- `production_mdm`: prototype

`beta_ready` remains **false**.
