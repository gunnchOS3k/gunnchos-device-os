"""Tests for shippable requirements package."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_requirements_exist():
    required = [
        "requirements/SHIPPABLE_OS_REQUIREMENTS.md",
        "requirements/CLAIM_BOUNDARY.md",
        "release_gates/RELEASE_GATE_MATRIX.md",
        "release_artifacts/ARTIFACT_MANIFEST_REQUIRED.md",
        "qa/QA_MASTER_TEST_PLAN.md",
        "roadmap/SHIPPABLE_OS_ROADMAP.md",
    ]
    for rel in required:
        assert (ROOT / rel).exists(), rel
