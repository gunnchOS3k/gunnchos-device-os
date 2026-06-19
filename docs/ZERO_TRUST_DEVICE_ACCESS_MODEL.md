# Zero Trust Device Access Model

Zero-trust framing for gunnchOS device and console access, aligned with the Access Risk Intelligence Lab.

## Principles

### 1. Never trust, always verify

Every session—student, educator, service, or demo—is evaluated against policy using identity, device posture, and resource sensitivity. Mock lab identities include `trust_level` to make this explicit.

### 2. Least privilege by default

Bindings grant the minimum permission required for the task scope. The lab's `least_privilege_recommender.py` demonstrates downgrades when fixtures drift (bulk export, impersonation, unapproved writes).

### 3. Assume breach

Risky paths are expected to be found in reviews, not hidden. The attack path model treats tagged edges as first-class findings.

### 4. Explicit zones

Resources declare a `zone` (for example `classroom_edge`, `school_tenant`, `fleet_ops`, `demo_isolation`). Cross-zone access requires stronger controls and logging.

## Device access layers

```text
┌─────────────────────────────────────────────────────────┐
│  Identity (role, trust_level, session_type)             │
└──────────────────────────┬──────────────────────────────┘
                           │ policy decision
┌──────────────────────────▼──────────────────────────────┐
│  Device / app surface (console_device, public_demo_app) │
└──────────────────────────┬──────────────────────────────┘
                           │ scoped permission
┌──────────────────────────▼──────────────────────────────┐
│  Data / config plane (records, telemetry, model_config) │
└─────────────────────────────────────────────────────────┘
```

## Control patterns

| Pattern | Lab example | Production direction |
| --- | --- | --- |
| Scope limitation | `self_only` student read | Launcher mode manager |
| Approval gate | model config write | Research measurement mode |
| Break-glass | service impersonation | Ticketed support sessions |
| Sandbox isolation | public demo app | Demo boot path |

## Metrics for maturity

- Count of high/critical risky paths in IAM reviews (target: zero in production)
- Percentage of bindings with documented scope and owner
- Time to remediate flagged cross-zone reads

## Related artifacts

- `security/access-risk/` — mock graph and tooling
- `docs/SECURITY_INVARIANTS.md` — invariant checklist
- `docs/security/THREAT_MODEL.md` — broader threat context (stub)

This model is educational and complements hardware secure boot and OTA policies documented elsewhere in the repo.
