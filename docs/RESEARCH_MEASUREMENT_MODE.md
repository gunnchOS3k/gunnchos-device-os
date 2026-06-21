# Research Measurement Mode

**Status:** device OS alpha · consent-gated field research policy  
**Modules:** `gunnchos_device_os/mode_manager.py`, `gunnchos_device_os/mode_policy.py`, `gunnchos_device_os/edge_io_contract.py`

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## Purpose

**Research Measurement** mode supports ethical field measurement workflows integrating **Edge-IO** with strict privacy: no private packet capture, consent prompts, local-only logging default, research operator profile.

Primary device class: **ds_xl_coder**. Related mode: **Laboratory**.

---

## Policy summary

| Key | Value |
|-----|-------|
| `allowed_apps` | field_measurement, edge_io, browser |
| `blocked_apps` | steam, netflix |
| `telemetry` | research_opt_in_only |
| `network` | standard |
| `update` | admin_scheduled |
| `child_safety` | strict |
| `edge_io_integration` | true |
| `consent_prompts` | true |
| `local_only_logging` | true |
| `no_private_packet_capture` | true |
| `export_formats` | csv, json |
| `research_operator_profile` | true |
| `field_measurement_workflow` | true |

---

## Transition and payload rules

`mode_policy.research_mode_policy()` returns:

```python
{
    "no_private_payload": { "blocked_data": [private_packet_capture, message_content, keystroke_logging] },
    "consent_required": True,
    "local_only_default": True,
}
```

Transition to Research Measurement requires consent (`telemetry_requires_consent`).

---

## Edge-IO session flow

1. User switches to Research Measurement mode (with consent)
2. `edge_io_contract.start_field_session()` — requires `consent=True` and `research_operator=True`
3. Metrics collected per `config/edge_io_contract.yaml` (placeholders)
4. Export via `export_session()` — csv/json only
5. User stop via `stop_session()`

See [EDGE_IO_INTEGRATION_CONTRACT.md](EDGE_IO_INTEGRATION_CONTRACT.md).

---

## Privacy defaults

`privacy_security_model.get_profile_defaults("research")` maps to `research_measurement` defaults — explicit consent required.

---

## WAIKE task

`research_measurement_task` in `config/waike_student_tasks.yaml` — Laboratory pathway.

---

## Test evidence

```bash
PYTHONPATH=. pytest tests/test_modes.py::test_research_mode
PYTHONPATH=. pytest tests/test_mode_policy.py::test_research_no_private_payload
PYTHONPATH=. pytest tests/test_edge_io_contract.py
```

---

## Claim boundary

Research Measurement mode does **not** prove IRB approval, carrier-grade drive tests, or live edge-io-measurement-node integration without cross-repo evidence.
