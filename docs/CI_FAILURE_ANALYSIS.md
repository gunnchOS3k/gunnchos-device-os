# CI Failure Analysis

**Branch:** `shippable-os-requirements-and-ci-fix`  
**Date:** 2026-06-21

## Failing test

`tests/test_user_focused_os_demo.py::test_demo_output_exists`

## Error

```text
AssertionError: Run scripts/run_user_focused_os_demo.py first
Missing: results/user_focused_os_demo_output.json
```

## Root cause

The GitHub Actions workflow in `.github/workflows/ci.yml` runs **pytest before demo generation**:

1. `Run tests` → `pytest -q tests/` (step runs first)
2. `User-focused OS alpha demo and validation` → runs `run_user_focused_os_demo.py` (step runs second)

`test_user_focused_os_demo.py` required `results/user_focused_os_demo_output.json` to exist on disk. That file is gitignored (`results/` in `.gitignore`) and is only created when the demo script runs. On a clean CI checkout, pytest executes first, so the file does not exist yet.

## Why it passed locally

Developers who had already run `python scripts/run_user_focused_os_demo.py` had the JSON file in `results/` locally. Pytest then passed without regenerating output.

## Correct fix

1. **Reorder CI:** Generate all demo outputs before pytest.
2. **Harden the test:** If output is missing, invoke `scripts/run_user_focused_os_demo.py` via `subprocess`, then validate JSON schema and required scenarios.
3. **Do not commit generated JSON:** Keep `results/` gitignored; CI and tests must be reproducible from scripts.

## Demo output: generate, commit, or both?

| Approach | Decision |
|----------|----------|
| Generate in CI | **Yes** — required |
| Generate in test if missing | **Yes** — makes clean checkout pass |
| Commit to git | **No** — `results/` stays gitignored |

## Node 20 deprecation warning

GitHub Actions may warn that Node 20 actions are deprecated. This workflow is Python-only (`actions/checkout@v4`, `actions/setup-python@v5`). No Node-based action versions are used in the test job. If launcher mock CI is added later, pin `actions/setup-node@v4` and document follow-up when Node 24 becomes required.

## Follow-up

- Add shippable OS validators to CI after demo generation.
- Document CI order in README shippable OS track section.
