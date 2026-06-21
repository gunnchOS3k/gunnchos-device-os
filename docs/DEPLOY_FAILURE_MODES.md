# Deploy Failure Modes

**Status:** device OS alpha · structured failures from `deploy_contract.py`

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## Failure taxonomy

| Code (technical_log prefix) | User message pattern | `next_action` | Safe fallback |
|------------------------------|---------------------|---------------|---------------|
| `deploy_rejected:package_type=` | Package type not allowed on target | `choose_allowed_package_type` | `local_folder_export` |
| `deploy_rejected:transport=` | Transport not supported for target | `choose_allowed_transport` | `local_folder_export` |
| `deploy_blocked:no_consent` | Deploy needs your OK first | `request_user_consent` | `local_folder_export` |
| `deploy_blocked:guardian_required` | Guardian/teacher must approve | `request_guardian_approval` | `local_folder_export` |

All failures return `"success": False` and `"mock": True`.

---

## Example: no consent

```python
deploy_package("ds_xl_coder", "student_14_5", "python_project", "local_wifi")
```

```json
{
  "success": false,
  "user_message": "Deploy needs your OK first. Nothing was sent.",
  "technical_log": "deploy_blocked:no_consent source=ds_xl_coder target=student_14_5",
  "next_action": "request_user_consent",
  "safe_fallback": "local_folder_export",
  "mock": true
}
```

---

## Example: disallowed package on classroom target

```python
deploy_package(
    "ds_xl_coder", "classroom_library_shared", "game_project", "local_wifi",
    user_consent=True, guardian_approved=True,
)
```

Fails because `game_project` is not in classroom allowed types.

---

## Operational failure modes (future / not implemented)

| Scenario | Planned user message | Alpha status |
|----------|---------------------|--------------|
| Wi-Fi pairing timeout | "Could not find device. Check Wi-Fi and try again." | Not implemented |
| USB device unauthorized | "This USB device is not trusted." | Not implemented |
| Signature verification failed | "Package signature invalid. Deploy cancelled." | Placeholder only |
| Insufficient storage on target | "Not enough space on target device." | Not implemented |
| Rollback failed | "Rollback incomplete — see guardian or admin." | Placeholder path |
| School hours block | "Deploy paused during school session." | Policy hook only |

Document troubleshooting steps in [DEPLOY_TROUBLESHOOTING.md](DEPLOY_TROUBLESHOOTING.md).

---

## UX requirements on failure

1. Show **user_message** in plain language (no error codes to children)
2. Log **technical_log** for admin/research operator
3. Offer **next_action** as primary button label where possible
4. Never imply data was sent when `success` is false

---

## Testing

```bash
PYTHONPATH=. pytest tests/test_deploy_contract.py::test_failed_deploy_messages
python scripts/run_deploy_contract_demo.py  # includes blocked_no_consent, blocked_package
```

---

## Related documents

- [DS_XL_DEPLOY_CONTRACT.md](DS_XL_DEPLOY_CONTRACT.md)
- [LOCAL_DEPLOY_SECURITY_MODEL.md](LOCAL_DEPLOY_SECURITY_MODEL.md)
- [demo/ds_xl_deploy_walkthrough.md](../demo/ds_xl_deploy_walkthrough.md)
