# Data Minimization

**Status:** device OS alpha · policy from `config/privacy_defaults.yaml`  
**Modules:** `privacy_security_model.py`, `edge_io_contract.py`, `deploy_contract.py`, `security_event_log.py`

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## Policy flags

From `config/privacy_defaults.yaml` → `data_minimization`:

| Flag | Value | Enforcement (alpha) |
|------|-------|---------------------|
| `no_private_payload` | true | Documented in deploy + research modes |
| `no_hidden_telemetry` | true | Consent gating |
| `no_keystroke_logging` | true | Not implemented as feature (prohibited) |
| `no_message_content` | true | Redacted in security_event_log |
| `export_path` | placeholder | `request_export()` mock |
| `delete_path` | placeholder | `request_delete()` mock |

---

## What we do not collect (by design)

- Message bodies or chat content
- Keystroke logs
- Private packet payloads (Edge-IO contract)
- Browsing history with PII query strings
- Location (off by default in Edge-IO metrics)

---

## What may be collected (with consent)

| Data class | Mode / profile | Consent required |
|------------|----------------|------------------|
| Aggregated app usage counts | School, Developer | opt_in_aggregate |
| Research session metadata | Research Measurement | opt_in_research |
| Local diagnostics | Adult default | local_only or opt-in |
| Synthetic fleet metrics | Fleet mock UI | Labeled synthetic |

---

## Redaction

`security_event_log.py` redacts keys in `_SENSITIVE_KEYS`:

`password`, `message_content`, `private_payload`, `keystroke`, `location`

---

## Deploy packages

Transport safety: `no_private_data_default: true` — packages should not embed user PII or private captures.

---

## Research measurement

`mode_policy.research_mode_policy()` blocks:

- private_packet_capture
- message_content
- keystroke_logging

Edge-IO export: `no_private_payloads: True` on successful export.

---

## Child profiles

Default: telemetry **none**, consent **denied**, local-only **true**.

---

## Export and delete (placeholders)

Users may request:

```python
request_export(user_id)  # export_queued_placeholder
request_delete(user_id)  # delete_queued_placeholder
```

Production implementation requires secure workflow — not in alpha.

---

## Related documents

- [PRIVACY_SECURITY_MODEL.md](PRIVACY_SECURITY_MODEL.md)
- [CONSENT_AND_TELEMETRY.md](CONSENT_AND_TELEMETRY.md)
- [EDGE_IO_DATA_CONTRACT.md](EDGE_IO_DATA_CONTRACT.md)
