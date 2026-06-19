# Access Graph Model

The gunnchOS Access Risk Intelligence Lab models authorization as a directed graph for defensive analysis.

## Nodes

| Node type | Source file | Examples |
| --- | --- | --- |
| Identity | `sample_identities.json` | `student_user`, `service_agent` |
| Resource | `sample_resources.json` | `telemetry_bucket`, `model_config` |

Identities carry `role`, `trust_level`, and `session_type`. Resources carry `sensitivity`, `data_class`, and `zone`.

## Edges

Each IAM binding becomes a directed edge:

```text
identity --[permission:scope]--> resource
```

Optional metadata includes `risk_tags` and `approval_gate`.

## Risk propagation

`attack_path_model.py` flags edges with known `risk_tags`:

- `guest_to_telemetry` — untrusted principal reaches fleet telemetry
- `service_agent_impersonate` — automation can assume human identity
- `educator_over_export` — bulk export of student learning records
- `model_config_without_approval` — privileged write without dual control

## Outputs

| Artifact | Producer |
| --- | --- |
| `risk_report_example.md` | `attack_path_model.py` |
| `least_privilege_recommendations.md` | `least_privilege_recommender.py` |

## Usage

```bash
python security/access-risk/attack_path_model.py
python security/access-risk/least_privilege_recommender.py
pytest -q tests/test_access_risk_model.py
```

All inputs are mock fixtures. No secrets or live tenant bindings are required.
