# gunnchOS Access Risk Report (Example)

Defensive lab output generated from mock identities, resources, and IAM bindings.
No live credentials or tenant data are used.

## Summary

- Identities modeled: **5**
- Resources modeled: **6**
- IAM bindings modeled: **10**
- Risky paths detected: **8**

## Risky Access Paths

### 1. Educator bulk export (`educator_over_export`)

- **Severity:** high
- **Path:** `educator_admin` → `student_learning_records`
- **Permission:** `export` (`bulk_all_students`)
- **Source role:** `educator`
- **Target sensitivity:** `high`
- **Rationale:** Educator role can export all student learning records in bulk.

### 2. bulk_pii_exfiltration (`bulk_pii_exfiltration`)

- **Severity:** medium
- **Path:** `educator_admin` → `student_learning_records`
- **Permission:** `export` (`bulk_all_students`)
- **Source role:** `educator`
- **Target sensitivity:** `high`
- **Rationale:** Flagged by mock policy.

### 3. Service agent impersonation (`service_agent_impersonate`)

- **Severity:** critical
- **Path:** `service_agent` → `student_user`
- **Permission:** `impersonate` (`support_sessions`)
- **Source role:** `automation`
- **Target sensitivity:** `unknown`
- **Rationale:** Automation principal can assume an interactive student identity.

### 4. identity_takeover (`identity_takeover`)

- **Severity:** medium
- **Path:** `service_agent` → `student_user`
- **Permission:** `impersonate` (`support_sessions`)
- **Source role:** `automation`
- **Target sensitivity:** `unknown`
- **Rationale:** Flagged by mock policy.

### 5. Model config write without approval (`model_config_without_approval`)

- **Severity:** critical
- **Path:** `research_operator` → `model_config`
- **Permission:** `write` (`experiment_profiles`)
- **Source role:** `research`
- **Target sensitivity:** `critical`
- **Rationale:** Research operator can mutate ML policy without an approval gate.

### 6. policy_drift (`policy_drift`)

- **Severity:** medium
- **Path:** `research_operator` → `model_config`
- **Permission:** `write` (`experiment_profiles`)
- **Source role:** `research`
- **Target sensitivity:** `critical`
- **Rationale:** Flagged by mock policy.

### 7. Guest reads fleet telemetry (`guest_to_telemetry`)

- **Severity:** high
- **Path:** `public_demo_guest` → `telemetry_bucket`
- **Permission:** `read` (`aggregate_metrics`)
- **Source role:** `guest`
- **Target sensitivity:** `high`
- **Rationale:** Untrusted demo guest can read telemetry outside the demo isolation zone.

### 8. cross_zone_leakage (`cross_zone_leakage`)

- **Severity:** medium
- **Path:** `public_demo_guest` → `telemetry_bucket`
- **Permission:** `read` (`aggregate_metrics`)
- **Source role:** `guest`
- **Target sensitivity:** `high`
- **Rationale:** Flagged by mock policy.

## Recommended Next Steps

1. Run `least_privilege_recommender.py` for downgrade suggestions.
2. Add approval gates for privileged automation and research mutations.
3. Isolate demo guests from fleet telemetry and student data planes.
