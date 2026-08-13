# Privacy & Security Model

**Status:** device OS alpha · consent and telemetry policy  
**Module:** `gunnchos_device_os/privacy_security_model.py`  
**Config:** `config/privacy_defaults.yaml`

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## Purpose

The privacy and security model defines **profile-based defaults** for privacy level, consent state, telemetry category, and local-only mode — plus placeholder export/delete paths.

---

## Privacy levels

From config: `minimal`, `standard`, `strict`, `youth_safe`, `research`

---

## Profile defaults

| Profile key | Privacy level | Default consent | Telemetry category |
|-------------|---------------|-----------------|-------------------|
| child_profile | youth_safe | denied | none |
| school_mode | strict | local_only | aggregate_usage |
| library_mode | strict | denied | none |
| research_measurement | research | not_asked | research_measurement_metadata |
| adult_default | standard | not_asked | local_diagnostics |

---

## API

```python
from gunnchos_device_os.privacy_security_model import (
    get_profile_defaults,
    get_telemetry_policy,
    request_export,
    request_delete,
)

get_telemetry_policy("child", "not_asked")  # enabled: False, category: none
request_export("user-1")  # local JSON export; mock=False; not GDPR certification
```

Profile type mapping includes aliases: `pre_k`, `elementary` → `child_profile`; `research_operator` → `research_measurement`.

---

## Data minimization alignment

Config block `data_minimization`:

- `no_private_payload: true`
- `no_hidden_telemetry: true`
- `no_keystroke_logging: true`
- `no_message_content: true`

See [DATA_MINIMIZATION.md](DATA_MINIMIZATION.md).

---

## Related modules

| Module | Role |
|--------|------|
| `consent_policy.py` | Explicit consent state machine |
| `security_event_log.py` | Redacted admin/security events |
| `mode_policy.py` | Telemetry consent on mode transition |
| `edge_io_contract.py` | Research session consent gate |

---

## User-facing doc

[PRIVACY_AND_TELEMETRY_FOR_USERS.md](PRIVACY_AND_TELEMETRY_FOR_USERS.md) — plainer language summary.

---

## Validation

```bash
PYTHONPATH=. pytest tests/test_privacy_security_model.py
python scripts/run_privacy_security_demo.py
```

---

## Claim boundary

Export/delete paths are **placeholders**. No GDPR certification or production data pipeline is claimed.

See [PRIVACY_SECURITY_LIMITATIONS.md](PRIVACY_SECURITY_LIMITATIONS.md).
