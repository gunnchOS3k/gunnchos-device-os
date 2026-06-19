# Access Risk Intelligence Alignment

How the `security/access-risk/` lab aligns with gunnchOS product and research goals.

## Mission fit

The lab supports **role-proof access review** for:

- Classroom device consoles bound to `console_device`
- School-tenant learning records with youth-safety constraints
- Fleet telemetry used for operations and research measurement
- Research ML configuration with approval boundaries
- Public demo sandboxes isolated from production data planes

## Product spine mapping

| gunnchOS concern | Lab fixture | Doc reference |
| --- | --- | --- |
| Student session safety | `student_user`, `student_learning_records` | `docs/security/YOUTH_SAFETY_MODEL.md` |
| Educator admin surface | `educator_admin`, `admin_console` | `docs/security/FLEET_ADMIN_SECURITY.md` |
| Service automation | `service_agent` impersonation edge | `docs/security/SECURE_BY_DESIGN_MODEL.md` |
| Research measurement | `research_operator`, `model_config` | `src/gunnchos_launcher/research_measurement_mode.py` |
| Public demo path | `public_demo_guest`, `public_demo_app` | `docs/BOOT_AND_DEMO_PATH.md` |

## Research questions enabled

1. Which mock identities can reach high-sensitivity resources in one hop?
2. Where do approval gates fail in the fixture graph?
3. What least-privilege downgrades close the highest-severity paths first?

## CI integration

`tests/test_access_risk_model.py` validates graph construction, risky-path detection, and recommendation generation without secrets. The workflow in `.github/workflows/ci.yml` runs these tests with the existing pytest suite.

## Non-goals

- Live IAM enumeration or cloud API calls
- Storing real student data or credentials
- Automated remediation in production tenants

This alignment doc is descriptive. The lab is educational and defensive.
