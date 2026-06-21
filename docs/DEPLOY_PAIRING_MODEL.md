# Deploy Pairing Model

**Status:** device OS alpha · pairing placeholders  
**Config:** `config/deploy_targets.yaml` → `qr_pairing_placeholder`, `local_wifi`

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## Pairing methods

| Method | Transport key | Targets (alpha) | Status |
|--------|---------------|-----------------|--------|
| Local Wi-Fi discovery | `local_wifi` | student_14_5, handheld, classroom | Mock API |
| USB-C direct attach | `usb_c` | student_14_5, handheld | Mock API |
| QR code pairing | `qr_pairing_placeholder` | handheld, wearables placeholder | **Placeholder only** |
| Offline ZIP | `offline_export_bundle` | Most targets | Logical bundle |

---

## Wi-Fi pairing model (planned)

1. DS-XL broadcasts ephemeral service ID on local subnet (mDNS placeholder)
2. Target scans or receives teacher-provided classroom code
3. Both devices show **matching short code** for user verification
4. Trust established → consent → guardian → transfer

**Security intent:** No wide-area pairing; local subnet only; no silent accept.

---

## QR pairing model (placeholder)

1. DS-XL displays QR containing: `{ pairing_token, package_hash_placeholder, expires_at }`
2. Target scans QR (handheld camera or arena kiosk)
3. Token validated locally
4. Same consent/guardian chain as Wi-Fi

Allowed on `handheld_hybrid` and `wearables_arena_placeholder`.

---

## Trust prompt

When `requires_target_trust_prompt: true`:

- Target shows source device name: "DS-XL Coder"
- Package type and size summary
- Accept / Decline buttons
- Decline → no partial install

---

## Classroom shared devices

`classroom_library_shared` target:

- Wi-Fi and offline bundle only (no USB from untrusted ports policy intent)
- Stricter package allow list (no `game_project`)

---

## Pairing failure modes

| Failure | Next action |
|---------|-------------|
| Token expired | Regenerate QR / restart Wi-Fi discovery |
| Code mismatch | Retry pairing |
| Wrong subnet | Move to same Wi-Fi or use USB/offline bundle |

See [DEPLOY_TROUBLESHOOTING.md](DEPLOY_TROUBLESHOOTING.md).

---

## API note

Alpha code does not implement pairing tokens — only transport allow lists and `deploy_package()` gates.

---

## Related documents

- [LOCAL_WIFI_USBC_DEPLOY_FLOW.md](LOCAL_WIFI_USBC_DEPLOY_FLOW.md)
- [LOCAL_DEPLOY_SECURITY_MODEL.md](LOCAL_DEPLOY_SECURITY_MODEL.md)
