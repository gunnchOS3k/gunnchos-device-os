# gunnchOS Access Risk Intelligence Lab

Defensive, mock-only lab for exploring IAM graphs, risky access paths, and least-privilege recommendations on gunnchOS device and fleet surfaces.

## Contents

| Path | Purpose |
| --- | --- |
| `sample_identities.json` | Mock principals (student, educator, service agent, research operator, demo guest) |
| `sample_resources.json` | Mock protected resources and sensitivity zones |
| `sample_iam_bindings.json` | Mock bindings including intentional risky paths |
| `attack_path_model.py` | Build graph, detect risky paths, write `risk_report_example.md` |
| `least_privilege_recommender.py` | Emit downgrade recommendations as markdown |
| `ACCESS_GRAPH_MODEL.md` | Graph schema and tooling overview |
| `risk_taxonomy.md` | Severity levels and risk tag definitions |

## Quick start

```bash
python security/access-risk/attack_path_model.py
python security/access-risk/least_privilege_recommender.py
pytest -q tests/test_access_risk_model.py
```

## Expected risky paths (educational fixtures)

1. **Guest → telemetry** — demo guest reads fleet telemetry
2. **Service agent impersonation** — automation can assume student identity
3. **Educator over-export** — bulk export of all student records
4. **Research model config** — write without approval gate

## Safety notes

- All data is synthetic.
- No API keys, tokens, or live IAM exports are stored in this lab.
- Outputs are suitable for walkthroughs, papers, and CI smoke checks.

See also: `demo/access_risk_walkthrough.md` and `docs/ACCESS_RISK_INTELLIGENCE_ALIGNMENT.md`.
