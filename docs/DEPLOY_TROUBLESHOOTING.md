# Deploy Troubleshooting

**Status:** device OS alpha · operator guide for mock deploy failures

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## Quick diagnostic

```python
from gunnchos_device_os.deploy_contract import deploy_package, get_deploy_target

target = get_deploy_target("student_14_5")
print(target["allowed_package_types"], target["allowed_transports"])
```

---

## Symptom: "Deploy needs your OK first"

| Cause | Fix |
|-------|-----|
| `user_consent=False` | Pass `user_consent=True` to `deploy_package()` |
| UX: user dismissed dialog | Re-open deploy; confirm consent |

`next_action`: `request_user_consent`

---

## Symptom: "A guardian or teacher must approve"

| Cause | Fix |
|-------|-----|
| Youth target with `guardian_restrictions: true` | Pass `guardian_approved=True` after guardian UI |
| School policy | Teacher approval workflow (future) |

`next_action`: `request_guardian_approval`

---

## Symptom: Package type not allowed

| Cause | Fix |
|-------|-----|
| e.g. `game_project` on `classroom_library_shared` | Choose allowed type: lesson_pack, web_app, media_project |
| Wrong target for edge task | Use `ds_xl_local_preview` for edge_measurement_task |

`next_action`: `choose_allowed_package_type`

---

## Symptom: Transport not supported

| Cause | Fix |
|-------|-----|
| usb_c on classroom target | Use local_wifi or offline_export_bundle |
| local_wifi on ds_xl_local_preview | Use local_folder_export only |

`next_action`: `choose_allowed_transport`

---

## Symptom: Nothing happens in launcher mock

| Cause | Fix |
|-------|-----|
| Deploy button is mock | Run `python scripts/run_deploy_contract_demo.py` for JSON |
| No backend connected | Expected in alpha |

---

## Wi-Fi / USB issues (future hardware)

| Symptom | Check |
|---------|-------|
| Device not found | Same subnet; firewall; retry pairing |
| USB not detected | Cable data-capable; target trust USB port policy |
| Transfer stalled | Disk space; bundle size limits |
| Signature failed | Rebuild bundle on DS-XL |

---

## Safe fallback: local folder export

When network deploy fails:

1. Export package to folder (`local_folder_export` transport)
2. Copy via USB drive or approved school share
3. Import on target with same consent/guardian rules where applicable

See [diagrams/deploy_flow_offline_bundle.mmd](../diagrams/deploy_flow_offline_bundle.mmd).

---

## Demo reproduction

```bash
python scripts/run_deploy_contract_demo.py
cat results/ds_xl_deploy_demo_output.json
```

---

## Escalation

For alpha research prototype issues, file GitHub issue with:

- `technical_log` string from failure response
- Target ID and package type
- Label `track:deploy`

---

## Claim boundary

Troubleshooting for **mock JSON failures** is fully supported; hardware transport debugging is future scope.
