# Edge-IO Data Contract

**Status:** device OS alpha · metric schema placeholders  
**Config:** `config/edge_io_contract.yaml` → `metrics`  
**Module:** `gunnchos_device_os/edge_io_contract.py`

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## Metric fields

| Metric | Type intent | PII / private |
|--------|-------------|---------------|
| timestamp | ISO8601 | No |
| device_profile | string (device class id) | No |
| network_type | enum placeholder (wifi, ethernet, …) | No |
| signal_metadata_placeholder | aggregate RF metadata | No raw payloads |
| latency_ms_placeholder | float | No |
| packet_loss_aggregate_placeholder | float % | Aggregate only |
| device_temperature_placeholder | float | No |
| battery_level_placeholder | float % | No |
| location_optional_off_by_default | geo (optional) | **Off by default** |
| notes | user/researcher text | User-controlled |

---

## Export formats

```python
export_session(session_id, fmt="json")  # or "csv"
```

Invalid format → failure from `failure_modes.export_failed`.

Successful export includes `no_private_payloads: True`.

---

## Session record (mock success)

```json
{
  "started": true,
  "user_id": "u1",
  "device_profile": "ds_xl_coder",
  "metrics": ["timestamp", "..."],
  "local_only": true,
  "user_can_stop": true,
  "technical_log": "edge_io_session_start:...",
  "mock": true
}
```

---

## Alignment with 7GC / research spine

Exported metadata may feed **7gc-digital-twin** smoke exports — aggregate community connectivity research, not individual surveillance.

Launcher fleet panel references Edge-IO session stubs.

---

## WAIKE task

`research_measurement_task` in `config/waike_student_tasks.yaml` — output `measurement_export.json`.

---

## Tests

```bash
PYTHONPATH=. pytest tests/test_edge_io_contract.py
```

---

## Claim boundary

Placeholder metric names (`*_placeholder`) indicate **non-final schema** — not calibrated field instruments.
