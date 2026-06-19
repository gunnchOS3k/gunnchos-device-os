# Security Invariants (Access Risk Lab)

Invariants the gunnchOS Access Risk Intelligence Lab encodes and tests against mock fixtures.

## Identity invariants

1. **Guest isolation** — `public_demo_guest` must not read fleet-scoped telemetry or student PII.
2. **Student self-scope** — `student_user` read access to learning records is limited to self-only scope in the baseline fixture.
3. **Automation is not human** — `service_agent` must not impersonate interactive identities without break-glass controls.

## Resource invariants

1. **Sensitivity monotonicity** — paths from `untrusted` identities to `high` or `critical` resources require explicit review.
2. **Zone boundaries** — `demo_isolation` resources must not grant transitive access to `fleet_ops` or `school_tenant` zones.
3. **Approval for mutation** — writes to `model_config` require an approval gate in production policy (violated intentionally in mock data).

## Binding invariants

1. Every binding documents `permission`, `scope`, and optional `risk_tags`.
2. Risky fixtures are tagged explicitly rather than inferred from live traffic.
3. Recommendations never escalate privilege; they only preserve or reduce access.

## Verification

| Invariant | Verified by |
| --- | --- |
| Risky paths detected | `attack_path_model.py`, `tests/test_access_risk_model.py` |
| Downgrade recommendations | `least_privilege_recommender.py`, `tests/test_access_risk_model.py` |
| No secrets in lab | Static JSON fixtures only; tests do not read env secrets |

## Violations in mock data (intentional)

The sample bindings **deliberately break** invariants 1, 3, and the model-config approval rule so the lab can demonstrate detection and remediation teaching flows.

Production gunnchOS policy should enforce these invariants at enforcement points (launcher policy, fleet admin, research mode gates).
