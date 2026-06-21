# Edge-IO Integration Walkthrough

**Status:** device OS alpha · demo guide

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## Part 1 — Inspect contract

```bash
PYTHONPATH=. python -c "
from gunnchos_device_os.edge_io_contract import get_contract
c = get_contract()
print(c['integration'])
print(c['session'])
print(c['metrics'])
"
```

Confirm `contract_version: 0.1-alpha` and `no_private_packet_payloads: true`.

---

## Part 2 — Blocked session (no consent)

```python
from gunnchos_device_os.edge_io_contract import start_field_session

r = start_field_session("researcher-1", "ds_xl_coder", consent=False)
assert r["started"] is False
print(r["user_message"])
# → Measurement stopped. No data was collected.
```

---

## Part 3 — Blocked session (not research operator)

```python
r = start_field_session("student-1", "ds_xl_coder", consent=True, research_operator=False)
assert r["started"] is False
print(r["next_action"])  # switch_profile
```

---

## Part 4 — Happy path

```python
from gunnchos_device_os.edge_io_contract import start_field_session, export_session, stop_session

s = start_field_session("researcher-1", "ds_xl_coder", consent=True, research_operator=True)
assert s["started"] and s["local_only"]

e = export_session("demo-session", "json")
assert e["exported"] and e["no_private_payloads"]

stop = stop_session("demo-session")
assert stop["stopped"]
```

---

## Part 5 — Run demo script

```bash
python scripts/run_edge_io_contract_demo.py
```

Inspect `results/` output if written by script.

---

## Part 6 — Mode policy check

```python
from gunnchos_device_os.mode_policy import research_mode_policy
p = research_mode_policy()
assert p["consent_required"] and p["local_only_default"]
```

---

## Part 7 — WAIKE laboratory task

Open `config/waike_student_tasks.yaml` → `research_measurement_task`:

- Mode: Laboratory
- Task: Run consent-gated Edge-IO mock session
- Output: measurement_export.json

---

## Part 8 — Launcher mock (optional)

Fleet view → Research links panel mentions Edge-IO session (synthetic).

Switch to Research Measurement concept via mode dropdown in fleet view.

---

## Discussion prompts

1. Why require research operator profile?
2. What metrics should never leave the device?
3. How does this differ from packet capture tools?

---

## Tests

```bash
PYTHONPATH=. pytest tests/test_edge_io_contract.py tests/test_modes.py::test_research_mode
```

---

## Claim boundary

Walkthrough uses **mock API** — not live edge-io-measurement-node hardware.
