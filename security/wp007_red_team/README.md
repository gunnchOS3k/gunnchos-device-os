# WP-007 — Independent Security / Red-Team Readiness (implementer)

Digital-only package preparing `INTERNAL_RED_TEAM_READY` for an **independent**
verifier. This directory does **not** certify EXTERNAL pentest.

## Contents

| Path | Role |
| --- | --- |
| `corpus/ATTACK_CORPUS.json` | Implementer attack case IDs |
| `../../docs/security/wp007/THREAT_MODEL.md` | STRIDE threat model |
| `../../docs/security/wp007/EXTERNAL_ASSESSMENT_PACKET.md` | E7 packet (not executed) |
| `../../docs/security/wp007/GOLDEN_JOURNEY_CONTROL_MAP.json` | GJ ↔ control map |
| `../../docs/security/wp007/DEFECT_REGISTER.json` | Fixed S0/S1 + S2 backlog |
| `../../gunnchos_device_os/security_red_team/harness.py` | Runnable harness |
| `../../artifacts/wp007/` | Results / readiness JSON |

## Run

```bash
make wp007-red-team
# or
PYTHONPATH=.:src python3 scripts/run_wp007_red_team.py
```

## Claim boundary

- `INTERNAL_RED_TEAM_READY` prepared for verifier (implementer does not self-certify PASS)
- `external_pentest=EXTERNAL_PENDING`
- No `production_ready` security claim
- `PHYSICAL_EXECUTION_FREEZE` honored
