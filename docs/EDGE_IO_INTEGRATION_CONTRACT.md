# Edge-IO Integration Contract

**Status:** device OS alpha · mock field session API  
**Module:** `gunnchos_device_os/edge_io_contract.py`  
**Config:** `config/edge_io_contract.yaml`  
**External repo:** [edge-io-measurement-node](https://github.com/gunnchOS3k/edge-io-measurement-node)

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## Contract version

```yaml
integration:
  repo: edge-io-measurement-node
  contract_version: "0.1-alpha"
```

---

## Session requirements

From `config/edge_io_contract.yaml` → `session`:

| Requirement | Value |
|-------------|-------|
| requires_consent | true |
| requires_research_operator | true |
| local_only_default | true |
| user_can_stop | true |
| no_silent_background | true |
| no_private_packet_payloads | true |
| export_formats | csv, json |

---

## API

```python
from gunnchos_device_os.edge_io_contract import (
    get_contract,
    start_field_session,
    export_session,
    stop_session,
)

start_field_session("u1", "ds_xl_coder", consent=True, research_operator=True)
export_session("session-1", "json")
stop_session("session-1")
```

---

## Mode integration

**Research Measurement** and **Laboratory** modes set `edge_io_integration: true`.

Use Research Measurement mode before starting sessions — see [RESEARCH_MEASUREMENT_MODE.md](RESEARCH_MEASUREMENT_MODE.md).

---

## Demo

```bash
python scripts/run_edge_io_contract_demo.py
```

Walkthrough: [demo/edge_io_integration_walkthrough.md](../demo/edge_io_integration_walkthrough.md)

---

## Related documents

- [EDGE_IO_DATA_CONTRACT.md](EDGE_IO_DATA_CONTRACT.md)
- [EDGE_IO_PRIVACY_SAFETY.md](EDGE_IO_PRIVACY_SAFETY.md)
- [EDGE_IO_FAILURE_MODES.md](EDGE_IO_FAILURE_MODES.md)
- [docs/10_EDGE_IO_MEASUREMENT_MODE.md](10_EDGE_IO_MEASUREMENT_MODE.md) (legacy)

---

## Claim boundary

Alpha implements **JSON mock sessions** — not live measurement node hardware or field-validated RF data.

Cross-repo integration requires evidence from edge-io-measurement-node.
