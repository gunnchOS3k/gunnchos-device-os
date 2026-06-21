"""Tests for QA package."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_qa_plans():
    plans = [
        "qa/QA_MASTER_TEST_PLAN.md",
        "qa/ACCESSIBILITY_TEST_PLAN.md",
        "qa/USER_ACCEPTANCE_TEST_PLAN.md",
    ]
    for rel in plans:
        assert (ROOT / rel).exists(), rel
