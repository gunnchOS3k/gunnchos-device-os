"""Evidence consistency validator for WP-007R."""
from __future__ import annotations

import json
from pathlib import Path

from gunnchos_device_os.security.wp007.evidence_consistency import (
    evaluate_evidence_consistency,
)


ROOT = Path(__file__).resolve().parents[2]


def test_honest_prepared_state_passes_with_fail_result(tmp_path: Path):
    wp = tmp_path / "artifacts" / "wp007"
    wp.mkdir(parents=True)
    (wp / "VP-007-RESULT.json").write_text(
        json.dumps(
            {
                "overall_result": "FAIL",
                "SECURITY_S0": 0,
                "SECURITY_S1": 0,
                "tip_verified": "deadbeef",
                "production_ready": False,
                "external_pentest": "EXTERNAL_PENDING",
                "SECURITY_S2_residual": [
                    {
                        "id": "WP007-IV-RES-001",
                        "status": "RESIDUAL_DIGITAL",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (wp / "INTERNAL_RED_TEAM_READINESS.json").write_text(
        json.dumps(
            {
                "INTERNAL_RED_TEAM_READY": False,
                "implementer_prepared": True,
                "prepared_for_verifier": True,
                "independent_verified": False,
                "external_pentest": "EXTERNAL_PENDING",
                "production_ready": False,
            }
        ),
        encoding="utf-8",
    )
    (wp / "RED_TEAM_RESULTS.json").write_text(
        json.dumps({"SECURITY_S0": 0, "SECURITY_S1": 0, "open_s0": [], "open_s1": []}),
        encoding="utf-8",
    )
    report = evaluate_evidence_consistency(tmp_path)
    assert report["ok"] is True
    assert report["WP007_CANONICAL_EVIDENCE_CONTRADICTIONS"] == 0


def test_ready_true_with_fail_is_contradiction(tmp_path: Path):
    wp = tmp_path / "artifacts" / "wp007"
    wp.mkdir(parents=True)
    (wp / "VP-007-RESULT.json").write_text(
        json.dumps(
            {
                "overall_result": "FAIL",
                "SECURITY_S0": 0,
                "SECURITY_S1": 0,
                "production_ready": False,
                "SECURITY_S2_residual": [],
            }
        ),
        encoding="utf-8",
    )
    (wp / "INTERNAL_RED_TEAM_READINESS.json").write_text(
        json.dumps(
            {
                "INTERNAL_RED_TEAM_READY": True,
                "implementer_prepared": True,
                "independent_verified": False,
                "external_pentest": "EXTERNAL_PENDING",
            }
        ),
        encoding="utf-8",
    )
    (wp / "RED_TEAM_RESULTS.json").write_text(
        json.dumps({"SECURITY_S0": 0, "SECURITY_S1": 0, "open_s0": [], "open_s1": []}),
        encoding="utf-8",
    )
    report = evaluate_evidence_consistency(tmp_path)
    assert report["ok"] is False
    codes = {v["code"] for v in report["violations"]}
    assert "READINESS_TRUE_WITHOUT_PASS" in codes


def test_repo_tip_honest_state_zero_contradictions():
    report = evaluate_evidence_consistency(ROOT)
    readiness = json.loads(
        (ROOT / "artifacts/wp007/INTERNAL_RED_TEAM_READINESS.json").read_text(encoding="utf-8")
    )
    result = json.loads((ROOT / "artifacts/wp007/VP-007-RESULT.json").read_text(encoding="utf-8"))
    if readiness.get("INTERNAL_RED_TEAM_READY") and result.get("overall_result") != "PASS":
        assert report["ok"] is False
        assert report["WP007_CANONICAL_EVIDENCE_CONTRADICTIONS"] > 0
    else:
        assert report["ok"] is True
        assert report["WP007_CANONICAL_EVIDENCE_CONTRADICTIONS"] == 0
        if result.get("overall_result") == "PASS":
            assert readiness.get("independent_verified") is True
            assert readiness.get("INTERNAL_RED_TEAM_READY") is True
