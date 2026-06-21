# Local Wi-Fi and USB-C Deploy Flow

**Status:** device OS alpha · logical flow (mock transport)  
**Module:** `gunnchos_device_os/deploy_contract.py`  
**Diagrams:** `diagrams/deploy_flow_local_wifi.mmd`, `diagrams/deploy_flow_usbc.mmd`

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## Overview

DS-XL Coder (`ds_xl_coder`) builds a package and transfers it to a target device class using **local Wi-Fi** or **USB-C**. Both transports share the same safety policy in `config/deploy_targets.yaml`.

---

## Shared prerequisites

1. Package type allowed on target (`allowed_package_types`)
2. Transport allowed on target (`allowed_transports`)
3. `user_consent=True` (both Wi-Fi and USB-C require consent)
4. `guardian_approved=True` if target has `guardian_restrictions: true`
5. Target trust prompt acknowledged (placeholder UX)

---

## Local Wi-Fi flow

| Step | Actor | Action |
|------|-------|--------|
| 1 | Developer | Build package on DS-XL |
| 2 | DS-XL | Show target picker (student_14_5, handheld, …) |
| 3 | User | Confirm consent dialog |
| 4 | Guardian | Approve if youth target |
| 5 | Target device | Show trust prompt ("Accept package from DS-XL?") |
| 6 | DS-XL | Call `deploy_package(..., transport="local_wifi")` |
| 7 | System | Apply signed bundle placeholder verification |
| 8 | Target | Install to user workspace; offer rollback |

See diagram: [diagrams/deploy_flow_local_wifi.mmd](../diagrams/deploy_flow_local_wifi.mmd)

---

## USB-C flow

| Step | Actor | Action |
|------|-------|--------|
| 1 | Developer | Connect target via USB-C cable |
| 2 | DS-XL | Detect device; show package summary |
| 3 | User | Confirm consent on DS-XL screen |
| 4 | Guardian | Approve if required |
| 5 | Target | Trust prompt on target screen |
| 6 | DS-XL | Call `deploy_package(..., transport="usb_c")` |
| 7 | System | Transfer bundle over USB (future MTP/adb-class) |
| 8 | Target | Verify signature placeholder; install |

See diagram: [diagrams/deploy_flow_usbc.mmd](../diagrams/deploy_flow_usbc.mmd)

---

## Policy comparison

| Policy field | local_wifi | usb_c |
|--------------|:----------:|:-----:|
| requires_user_consent | ✓ | ✓ |
| requires_target_trust_prompt | ✓ | ✓ |
| guardian_approval_for_child | ✓ | ✓ |
| no_silent_deploy | ✓ | ✓ |
| no_private_data_default | ✓ | ✓ |
| signed_bundle_placeholder | ✓ | ✓ |

---

## Failure handling

| Failure | User experience |
|---------|-----------------|
| No consent | "Deploy needs your OK first. Nothing was sent." |
| No guardian | "A guardian or teacher must approve…" |
| Wrong package type | Package type not allowed message |
| Wrong transport | Transport not supported message |

Fallback: `local_folder_export` — see offline bundle flow.

---

## Alpha limitation

`deploy_package()` returns JSON only — **no network or USB I/O** occurs. Flows describe intended UX for EVT+ hardware.

---

## Related documents

- [DS_XL_DEPLOY_CONTRACT.md](DS_XL_DEPLOY_CONTRACT.md)
- [DEPLOY_PAIRING_MODEL.md](DEPLOY_PAIRING_MODEL.md)
- [DEPLOY_TROUBLESHOOTING.md](DEPLOY_TROUBLESHOOTING.md)
