# Mode Policy Matrix

**Status:** device OS alpha · derived from `config/modes.yaml`  
**Module:** `gunnchos_device_os/mode_manager.py`

> This is a user-focused OS alpha package and launcher/customization framework. It is not yet a finished shipping OS image.

---

## Full mode matrix

| Mode | Telemetry | Network | Update | Child safety | Performance | Notable flags |
|------|-----------|---------|--------|--------------|-------------|---------------|
| School | aggregated_opt_in | filtered | admin_scheduled | strict | school | simplified_home, focus_mode, guardian_hooks, no_invasive_surveillance |
| Developer | aggregated_opt_in | standard | user_prompt | standard | balanced | wsl_path, git_github_path, rollback_safe_reset |
| Coder | aggregated_opt_in | standard | user_prompt | standard | balanced | — |
| Research Measurement | research_opt_in_only | standard | admin_scheduled | strict | balanced | edge_io_integration, no_private_packet_capture, export csv/json |
| Play | minimal | standard | user_prompt | standard | gaming | — |
| Media | minimal | standard | user_prompt | standard | balanced | streaming via browser placeholders |
| Studio | local_diagnostics | standard | user_prompt | standard | creative | write/sketch/music placeholders |
| Workshop | aggregated_opt_in | standard | user_prompt | standard | developer | hardware_lab_placeholder |
| Laboratory | research_opt_in_only | standard | admin_scheduled | strict | balanced | research_notebook_placeholder |
| Guardian | none | filtered | admin_scheduled | strict | school | youth-safe subset of School |
| Library | none | filtered | admin_scheduled | strict | school | minimal app set |
| Offline | none | offline_only | deferred | standard | low_power | offline lessons/creative |
| Admin | audit_only | standard | immediate | admin_override | balanced | unrestricted apps |

---

## App allow/block snapshot

| Mode | Allowed (sample) | Blocked (sample) |
|------|------------------|------------------|
| School | waike_offline, gunnchai3k | steam, vscode, terminal |
| Developer | vscode, terminal, wsl_ubuntu | steam |
| Research Measurement | field_measurement, edge_io | steam, netflix |
| Play | steam, scaly_wings | — |
| Media | youtube, netflix, hulu | steam, vscode |
| Offline | waike_offline, write_placeholder | steam, netflix |

Full lists in YAML — placeholders indicate apps not yet integrated.

---

## Telemetry × consent matrix

| Mode | Default telemetry category | Consent required to enable? |
|------|---------------------------|----------------------------|
| School | aggregated_opt_in | Per privacy profile |
| Developer | aggregated_opt_in | Yes (transition rule) |
| Research Measurement | research_opt_in_only | Yes |
| Guardian / Library / Offline | none | N/A |
| Admin | audit_only | Admin policy |

Cross-reference: [CONSENT_AND_TELEMETRY.md](CONSENT_AND_TELEMETRY.md)

---

## Transition gate matrix

| To mode → | Child (no guardian) | School device (no consent) |
|-----------|---------------------|----------------------------|
| Developer | Blocked | Blocked |
| Admin | Blocked | Blocked |
| Workshop | Blocked | Allowed* |
| Laboratory | Blocked | Allowed* |
| Play | Allowed* | Allowed |

\*Subject to other guardian/time rules in future; alpha only enforces table in [MODE_TRANSITION_RULES.md](MODE_TRANSITION_RULES.md).

---

## Device class × mode availability

| Mode | student_14_5 | handheld_hybrid | ds_xl_coder | wearables_arena_set |
|------|:------------:|:---------------:|:-----------:|:-------------------:|
| School | ✓ | ✓ | — | ✓ |
| Developer | ✓ | ✓ | ✓ | — |
| Research Measurement | — | — | ✓ | — |
| Play | ✓ | ✓ | — | ✓ |
| Guardian | ✓ | — | — | — |
| Workshop | — | ✓ | ✓ | — |
| Laboratory | — | — | ✓ | — |

Source: `config/device_classes.yaml` → `supported_modes`

---

## Validation

```bash
PYTHONPATH=. pytest tests/test_modes.py
python scripts/run_mode_policy_demo.py
```

---

## Related documents

- [MODES_OVERVIEW.md](MODES_OVERVIEW.md)
- [SCHOOL_MODE.md](SCHOOL_MODE.md)
- [DEVELOPER_MODE.md](DEVELOPER_MODE.md)
- [RESEARCH_MEASUREMENT_MODE.md](RESEARCH_MEASUREMENT_MODE.md)
