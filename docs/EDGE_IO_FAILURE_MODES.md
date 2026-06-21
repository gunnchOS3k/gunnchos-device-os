# Edge-IO Failure Modes

**Status:** device OS alpha · from `config/edge_io_contract.yaml` and `edge_io_contract.py`

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## Configured failure modes

### consent_denied

| Field | Value |
|-------|-------|
| Trigger | `start_field_session(..., consent=False)` |
| started | false |
| user_message | Measurement stopped. No data was collected. |
| safe_fallback | local_only |
| next_action | return_to_launcher |
| technical_log | edge_io_session_blocked:no_consent |

### edge_io_unavailable

| Field | Value |
|-------|-------|
| Trigger | Field measurement app not installed (future) |
| user_message | Field measurement app is not available right now. |
| safe_fallback | offline_mode |
| next_action | retry_or_cancel |

### export_failed

| Field | Value |
|-------|-------|
| Trigger | Invalid export format |
| user_message | Export did not complete. Your local session is still saved. |
| safe_fallback | local_only |
| next_action | retry_export |
| technical_log | edge_io_export_failed:fmt={fmt} |

---

## Research operator missing

Not in YAML — hardcoded in Python:

```python
start_field_session(..., consent=True, research_operator=False)
```

| Field | Value |
|-------|-------|
| started | false |
| user_message | Research measurement needs a research operator profile. |
| next_action | switch_profile |
| technical_log | edge_io_session_blocked:not_research_operator |

---

## Success paths

| API | Success indicator |
|-----|-------------------|
| start_field_session | started: true |
| export_session | exported: true, path: edge_io_export_{id}.{fmt} |
| stop_session | stopped: true |

All include `"mock": true` in alpha.

---

## UX requirements

1. Never imply data was collected when `started: false`
2. Offer `next_action` as recovery hint
3. Preserve local session on export failure

---

## Tests

```bash
PYTHONPATH=. pytest tests/test_edge_io_contract.py
```

---

## Related documents

- [EDGE_IO_INTEGRATION_CONTRACT.md](EDGE_IO_INTEGRATION_CONTRACT.md)
- [demo/edge_io_integration_walkthrough.md](../demo/edge_io_integration_walkthrough.md)

---

## Claim boundary

`edge_io_unavailable` path is **documented** — not exercised against real missing app in alpha tests.
