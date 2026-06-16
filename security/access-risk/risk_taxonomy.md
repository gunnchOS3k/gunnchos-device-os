# Risk Taxonomy (Mock Lab)

Educational taxonomy for the gunnchOS Access Risk Intelligence Lab.

## Severity levels

| Level | Meaning | Example in lab |
| --- | --- | --- |
| critical | Immediate policy violation or identity takeover | `service_agent_impersonate`, `model_config_without_approval` |
| high | Cross-zone data exposure or bulk exfiltration | `guest_to_telemetry`, `educator_over_export` |
| medium | Misconfiguration with limited blast radius | (reserved for future fixtures) |
| low | Expected baseline access | student self-read of learning records |

## Risk tags

### `guest_to_telemetry`

- **Pattern:** `public_demo_guest` → `telemetry_bucket`
- **Failure mode:** Demo isolation boundary leaks into fleet operations data
- **Mitigation:** Deny cross-zone reads; expose synthetic demo metrics only

### `service_agent_impersonate`

- **Pattern:** `service_agent` → `student_user` with `impersonate`
- **Failure mode:** Support automation becomes a lateral movement pivot
- **Mitigation:** Break-glass approval, short TTL sessions, immutable audit trail

### `educator_over_export`

- **Pattern:** `educator_admin` → `student_learning_records` with `export` + `bulk_all_students`
- **Failure mode:** Classroom admin can exfiltrate entire cohort PII
- **Mitigation:** Class-scoped export, watermarking, DLP review

### `model_config_without_approval`

- **Pattern:** `research_operator` → `model_config` with `write` and `approval_gate: false`
- **Failure mode:** Silent ML policy drift in production cohorts
- **Mitigation:** Dual-control approval and change tickets

## Mapping to gunnchOS surfaces

| Surface | Relevant resources |
| --- | --- |
| Classroom console | `console_device`, `student_learning_records` |
| Fleet operations | `telemetry_bucket`, `service_agent` |
| Research control plane | `model_config`, `research_operator` |
| Public demo | `public_demo_app`, `public_demo_guest` |

This taxonomy supports teaching and CI smoke validation only.
