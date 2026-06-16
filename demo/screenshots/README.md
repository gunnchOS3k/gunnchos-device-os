# Demo Screenshots

Placeholder directory for Access Risk Intelligence Lab walkthrough captures.

## Suggested captures

1. `risk-report-terminal.png` — output of `attack_path_model.py`
2. `least-privilege-table.png` — markdown table from `least_privilege_recommender.py`
3. `pytest-access-risk.png` — green `pytest -q tests/test_access_risk_model.py` run

## How to add

```bash
python security/access-risk/attack_path_model.py
python security/access-risk/least_privilege_recommender.py
pytest -q tests/test_access_risk_model.py
# Capture terminal or export markdown to PDF for slides
```

Do not commit real credentials, live IAM exports, or student data in screenshots.
