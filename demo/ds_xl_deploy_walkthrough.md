# DS-XL Deploy Walkthrough

**Status:** device OS alpha · demo script guide  
**Audience:** instructors, developers, research operators

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## Prerequisites

```bash
cd gunnchos-device-os
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

---

## Step 1 — Review deploy targets

```bash
PYTHONPATH=. python -c "
from gunnchos_device_os.deploy_contract import list_deploy_targets, get_deploy_target
for t in list_deploy_targets():
    g = get_deploy_target(t)
    print(t, g['allowed_package_types'], g['allowed_transports'])
"
```

Expected: five targets including `student_14_5`, `handheld_hybrid`, `ds_xl_local_preview`.

---

## Step 2 — Run deploy demo

```bash
python scripts/run_deploy_contract_demo.py
```

Inspect `results/ds_xl_deploy_demo_output.json`:

| Key | Expected |
|-----|----------|
| `success_wifi` | `"success": true` when consent + guardian approved |
| `blocked_no_consent` | `"success": false`, `next_action`: `request_user_consent` |
| `blocked_package` | game_project rejected on classroom target |
| `claim_boundary` | Deploy contract alpha disclaimer |

---

## Step 3 — Simulate happy-path deploy (Python REPL)

```python
from gunnchos_device_os.deploy_contract import deploy_package

r = deploy_package(
    "ds_xl_coder",
    "student_14_5",
    "python_project",
    "local_wifi",
    user_consent=True,
    guardian_approved=True,
)
assert r["success"]
print(r["user_message"])
```

User should see: "Package ready on Student 14.5."

---

## Step 4 — Try USB-C policy

```python
from gunnchos_device_os.deploy_contract import get_transport_policy
p = get_transport_policy("usb_c")
assert p["safety_policy"]["no_silent_deploy"] is True
```

---

## Step 5 — Launcher mock (visual, optional)

```bash
cd apps/launcher_mock && npm install && npm run dev
```

1. Open fleet view
2. Select a target device from dropdown
3. Read **Deploy (DS-XL → device)** panel — mock button only

---

## Step 6 — Read flow diagrams

- [docs/LOCAL_WIFI_USBC_DEPLOY_FLOW.md](../docs/LOCAL_WIFI_USBC_DEPLOY_FLOW.md)
- [docs/DEPLOY_FLOW_DIAGRAMS.md](../docs/DEPLOY_FLOW_DIAGRAMS.md)
- `diagrams/deploy_flow_*.mmd`

---

## Classroom discussion prompts

1. Why require guardian approval for student targets?
2. What should happen if consent is denied mid-deploy?
3. How is this different from silent OTA updates on phones?

---

## Claim boundary

This walkthrough validates **mock JSON responses** only. No files are transferred over Wi-Fi or USB in alpha.
