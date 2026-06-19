# Access Risk Intelligence Walkthrough

Step-by-step demo of the mock lab for papers, reviews, or onboarding.

## Prerequisites

- Python 3.11+
- Repository checkout on branch `role-proof-access-risk-intelligence`
- No cloud credentials required

## Step 1 — Inspect mock principals and resources

```bash
cat security/access-risk/sample_identities.json
cat security/access-risk/sample_resources.json
```

Note the five identities and six resources, including sensitivity and zone labels.

## Step 2 — Review intentional risky bindings

```bash
cat security/access-risk/sample_iam_bindings.json
```

Look for `risk_tags` on bindings involving:

- `public_demo_guest` → `telemetry_bucket`
- `service_agent` → `student_user` (`impersonate`)
- `educator_admin` → `student_learning_records` (`export` / bulk)
- `research_operator` → `model_config` (`approval_gate: false`)

## Step 3 — Generate risk report

```bash
python security/access-risk/attack_path_model.py
cat security/access-risk/risk_report_example.md
```

Expect four risky paths in the example output.

## Step 4 — Generate least-privilege table

```bash
python security/access-risk/least_privilege_recommender.py
cat security/access-risk/least_privilege_recommendations.md
```

Compare current permissions with recommended downgrades.

## Step 5 — Run automated checks

```bash
pytest -q tests/test_access_risk_model.py
```

## Discussion prompts

1. Which path would you remediate first in a school fleet rollout?
2. How would you enforce demo isolation without blocking legitimate telemetry for ops?
3. What audit events would you emit for break-glass impersonation?

## Screenshots

Placeholder assets live in `demo/screenshots/`. Capture terminal output of the commands above for slides or evidence bundles.
