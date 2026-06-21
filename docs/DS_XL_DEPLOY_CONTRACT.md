# DS-XL Deploy Contract

**Status:** device OS alpha · mock deploy API  
**Module:** `gunnchos_device_os/deploy_contract.py`  
**Config:** `config/deploy_targets.yaml`

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## Purpose

The DS-XL deploy contract defines how a **DS-XL Coder** (`ds_xl_coder` device class) packages projects for transfer to target devices. It encodes:

- Allowed package types per target
- Allowed transport methods (local Wi-Fi, USB-C, folder export, offline bundle)
- Safety policies (consent, guardian approval, no silent deploy)
- Failure responses with user messages and technical logs

All deploy operations return `"mock": True` in alpha — no bytes are transferred on the network.

---

## Source device

```yaml
# config/deploy_targets.yaml
source_device: ds_xl_coder
```

The DS-XL is the primary **build-once, deploy-many** workstation in EVT-1 alpha planning.

---

## API

```python
from gunnchos_device_os.deploy_contract import (
    deploy_package,
    get_deploy_target,
    get_transport_policy,
    list_deploy_targets,
)

result = deploy_package(
    source="ds_xl_coder",
    target_id="student_14_5",
    package_type="python_project",
    transport="local_wifi",
    user_consent=True,
    guardian_approved=True,
)
# success path includes rollback_path placeholder
```

### Success response fields

| Field | Description |
|-------|-------------|
| `success` | `True` |
| `source`, `target`, `package_type`, `transport` | Echo inputs |
| `safety_policy_applied` | Transport safety policy dict |
| `rollback_path` | `"delete_package_or_rollback_placeholder"` |
| `user_message` | Plain-language confirmation |
| `technical_log` | Structured log string |
| `mock` | Always `True` in alpha |

### Failure response fields

| Field | Description |
|-------|-------------|
| `success` | `False` |
| `user_message` | Plain-language reason |
| `technical_log` | Structured rejection code |
| `next_action` | Suggested UX step |
| `safe_fallback` | e.g. `local_folder_export` |

---

## Deploy targets

| Target ID | Display name | Guardian | School restrictions |
|-----------|--------------|----------|-------------------|
| `student_14_5` | Student 14.5 | Yes | Yes |
| `handheld_hybrid` | Handheld Hybrid | Yes | Yes |
| `ds_xl_local_preview` | DS-XL Local Preview | No | No |
| `classroom_library_shared` | Classroom / Library Shared | Yes | Yes |
| `wearables_arena_placeholder` | Wearables / Arena (future) | Yes | Yes |

---

## Package types (global)

`web_app`, `python_project`, `game_project`, `lesson_pack`, `media_project`, `edge_measurement_task`, `research_notebook`

Each target allows a **subset** — see YAML for per-target lists.

---

## Transport methods

| Transport | Trust prompt | Signed bundle (placeholder) |
|-----------|--------------|----------------------------|
| `local_wifi` | Yes | Yes |
| `usb_c` | Yes | Yes |
| `local_folder_export` | No | No |
| `qr_pairing_placeholder` | Yes | Yes |
| `offline_export_bundle` | No | Yes |

Safety policies require `no_silent_deploy: true` for all transports (validated in tests).

---

## Demo

```bash
python scripts/run_deploy_contract_demo.py
# writes results/ds_xl_deploy_demo_output.json
```

---

## Related documents

- [LOCAL_DEPLOY_SECURITY_MODEL.md](LOCAL_DEPLOY_SECURITY_MODEL.md)
- [DEPLOY_PACKAGE_FORMAT.md](DEPLOY_PACKAGE_FORMAT.md)
- [DEPLOY_FAILURE_MODES.md](DEPLOY_FAILURE_MODES.md)
- [LOCAL_WIFI_USBC_DEPLOY_FLOW.md](LOCAL_WIFI_USBC_DEPLOY_FLOW.md)
- [demo/ds_xl_deploy_walkthrough.md](../demo/ds_xl_deploy_walkthrough.md)

---

## Claim boundary

| Real today | Not claimed |
|------------|-------------|
| Config-driven allow lists | Production code signing |
| Consent/guardian gates in Python | OTA fleet push |
| Demo JSON output | Hardware USB deploy stack |
