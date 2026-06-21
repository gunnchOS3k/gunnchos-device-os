# Deploy Flow Diagrams

**Status:** device OS alpha · Mermaid source diagrams  
**Location:** `diagrams/deploy_flow_*.mmd`

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## Diagram index

| File | Transport | Description |
|------|-----------|-------------|
| [deploy_flow_local_wifi.mmd](../diagrams/deploy_flow_local_wifi.mmd) | local_wifi | DS-XL → target over LAN |
| [deploy_flow_usbc.mmd](../diagrams/deploy_flow_usbc.mmd) | usb_c | DS-XL → target over cable |
| [deploy_flow_offline_bundle.mmd](../diagrams/deploy_flow_offline_bundle.mmd) | offline_export_bundle | ZIP bundle for sneaker-net |

---

## Render locally

```bash
# With mermaid-cli (optional)
npx @mermaid-js/mermaid-cli -i diagrams/deploy_flow_local_wifi.mmd -o diagrams/deploy_flow_local_wifi.png
```

CI validates file existence via `tests/test_deploy_docs.py`.

---

## Common swimlanes

All three diagrams use actors:

- **Developer** — builds package on DS-XL
- **DS-XL** — source device (`source_device: ds_xl_coder`)
- **User** — consent
- **Guardian** — optional approval
- **Target** — receiving device class

---

## Decision diamonds (shared)

```
Package type allowed? → Transport allowed? → User consent? → Guardian OK? → Trust prompt? → Deploy
```

Any failure → safe fallback (`local_folder_export` or retry).

---

## Cross-links

| Doc | Topic |
|-----|-------|
| [LOCAL_WIFI_USBC_DEPLOY_FLOW.md](LOCAL_WIFI_USBC_DEPLOY_FLOW.md) | Step tables |
| [DEPLOY_PAIRING_MODEL.md](DEPLOY_PAIRING_MODEL.md) | Wi-Fi/QR pairing |
| [DEPLOY_ROLLBACK_MODEL.md](DEPLOY_ROLLBACK_MODEL.md) | Undo path |
| [DEPLOY_FAILURE_MODES.md](DEPLOY_FAILURE_MODES.md) | Error codes |

---

## Other diagrams in repo

- `docs/diagrams/os_system_architecture.mmd`
- `docs/diagrams/device_mode_state_machine.mmd`
- `docs/diagrams/secure_boot_update_flow.mmd`

Deploy-specific diagrams live in top-level `diagrams/` for issue #9 test paths.

---

## Claim boundary

Diagrams illustrate **intended flows** — not verified on hardware.
