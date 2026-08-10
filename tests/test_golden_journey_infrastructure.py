"""WP-003 Golden Journey infrastructure — implementer harness tests (not independent verification)."""

from __future__ import annotations

import json
from pathlib import Path

from gunnchos_device_os.golden_journeys import CLAIM_BOUNDARY
from gunnchos_device_os.golden_journeys.path_map import select_journeys_for_paths
from gunnchos_device_os.golden_journeys.scorecard import validate_scorecards


ROOT = Path(__file__).resolve().parents[1]


def test_catalog_has_ten_journeys():
    catalog = json.loads(
        (ROOT / "quality/golden_journeys/GOLDEN_JOURNEYS.json").read_text(encoding="utf-8")
    )
    ids = [j["id"] for j in catalog["journeys"]]
    assert ids == [f"GOLDEN-{i:02d}" for i in range(1, 11)]
    assert catalog["doctrine"]["implementer_may_not_claim_independent_verification"] is True
    assert catalog["doctrine"]["frontier_parity_tokens_forbidden"] is True


def test_scorecards_and_fixtures_valid():
    report = validate_scorecards(root=ROOT)
    assert report["ok"], report["errors"]
    assert report["scorecard_count"] == 10
    assert report["independent_verification_claimed"] is False


def test_scorecards_distinguish_statuses_and_honesty_tokens():
    """After VP-003, committed scorecards may carry verifier PASS/FAIL/PARTIAL.

    Implementer self-certification remains forbidden: claim_boundary stays false,
    and PASS is allowed only when updated_by is the independent verifier.
    """
    allowed = {"PENDING", "NOT_CLAIMED", "PASS", "PARTIAL", "FAIL", "BLOCKED"}
    for i in range(1, 11):
        jid = f"GOLDEN-{i:02d}"
        card = json.loads(
            (ROOT / "quality/golden_journeys/scorecards" / f"{jid}.scorecard.json").read_text(
                encoding="utf-8"
            )
        )
        for key in (
            "FUNCTIONAL_PASS",
            "PRODUCT_QUALITY_SCORE",
            "INDEPENDENT_VERIFICATION",
            "PHYSICAL_PENDING",
            "HUMAN_VALIDATION_PENDING",
        ):
            assert key in card
        status = card["INDEPENDENT_VERIFICATION"]["status"]
        assert status in allowed
        updated_by = card.get("updated_by", "")
        if status in {"PASS", "PARTIAL"}:
            assert updated_by.startswith("independent-verifier"), (
                f"{jid} status={status} requires independent verifier authority, got {updated_by}"
            )
            assert not updated_by.startswith("implementer")
        assert card["PHYSICAL_PENDING"]["pending"] is True
        assert card["HUMAN_VALIDATION_PENDING"]["pending"] is True
        assert card["claim_boundary"] == CLAIM_BOUNDARY
        assert (
            card["PRODUCT_QUALITY_SCORE"]["dimensions"]["user_preference"]["value"]
            == "NOT_MEASURED"
        )


def test_path_selection_maps_dock_to_office_and_handheld():
    sel = select_journeys_for_paths(
        ["gunnchos_device_os/dock_manager.py"], root=ROOT, major_pr=True
    )
    assert "GOLDEN-04" in sel["selected"]
    assert "GOLDEN-05" in sel["selected"]


def test_path_selection_maps_identity_to_golden_10():
    sel = select_journeys_for_paths(
        ["gunnchos_device_os/phase_xv/identity/__init__.py"], root=ROOT, major_pr=True
    )
    assert sel["selected"] == ["GOLDEN-10"]
    assert sel["severities"]["GOLDEN-10"] == "S0"


def test_major_pr_unknown_defaults_to_s0():
    sel = select_journeys_for_paths(
        ["docs/unrelated.md"], root=ROOT, major_pr=True
    )
    assert sel["selected"] == ["GOLDEN-09", "GOLDEN-10"]
    assert sel["reason"] == "major_pr_default_s0"


def test_competitor_matrix_has_no_fabricated_scores():
    matrix = json.loads(
        (
            ROOT / "quality/golden_journeys/COMPETITOR_READINESS_GAP_MATRIX.json"
        ).read_text(encoding="utf-8")
    )
    assert matrix["doctrine"]["no_fabricated_competitor_measurements"] is True
    assert matrix["doctrine"]["frontier_parity_claimed"] is False
    strategies = {c["strategy"] for c in matrix["capabilities"]}
    assert strategies >= {"MUST_MATCH", "MUST_EXCEED", "NOT_RELEVANT", "DIFFERENT_APPROACH"}
    for cap in matrix["capabilities"]:
        assert cap["competitor_score"] is None


def test_competitor_matrix_consistency_zero():
    from gunnchos_device_os.golden_journeys.scorecard import (
        validate_competitor_matrix_consistency,
    )

    report = validate_competitor_matrix_consistency(root=ROOT)
    assert report["ok"], report["errors"]
    assert report["COMPETITOR_MATRIX_CONTRADICTIONS"] == 0


def test_unprivileged_net_audio_are_fallback_only_not_e4():
    from gunnchos_device_os.device_lab.hw_backends.network import NetworkBackend
    from gunnchos_device_os.device_lab.hw_backends.audio import AudioBackend

    net = NetworkBackend()
    net.start()
    n = net.dock_ethernet_attach()
    assert n.get("e4_reference_proof") is False
    assert n.get("NOT_E4_REFERENCE_PROOF") is True
    assert n.get("FALLBACK_ONLY") is True
    net.dock_ethernet_detach()

    aud = AudioBackend()
    aud.start()
    a = aud.dock_attach()
    assert a.get("e4_reference_proof") is False
    assert a.get("FALLBACK_ONLY") is True
    aud.dock_detach()


def test_g04_office_dock_records_backend_honesty():
    from gunnchos_device_os.device_lab.scenarios.office_dock import run

    result = run(repo_root=ROOT)
    assert result["ok"] is True
    assert result["VF2_UNPRIVILEGED_FALLBACK"] == "AVAILABLE"
    assert result["VF3"] == "MODELED_ONLY"
    assert result["VF4"] == "PHYSICAL_PENDING"
    assert result["SILICON_EXACT_EMULATION"] is False
    # Default CI/dev path is logical fallback, not E4 reference proof.
    assert result["network_backend"]["NOT_E4_REFERENCE_PROOF"] is True
    assert result["audio_backend"]["NOT_E4_REFERENCE_PROOF"] is True
    assert result["VF2_REQUIRED_GOLDEN_BACKENDS"] == "FALLBACK_ONLY"


def test_verifier_owned_paths_exist():
    plan = ROOT / "quality/golden_journeys/verifier/INDEPENDENT_GOLDEN_ACCEPTANCE_PLAN.md"
    results = ROOT / "quality/golden_journeys/verifier/INDEPENDENT_GOLDEN_ACCEPTANCE_RESULTS.md"
    assert plan.exists()
    assert results.exists()
    text = plan.read_text(encoding="utf-8")
    assert "VERIFIER OWNED" in text
    # After VP-003 execution the plan is real acceptance content, not an implementer stub.
    assert "Independence attestation" in text or "Independent Golden Acceptance Plan" in text


def test_supporting_subset_student_journey_and_no_independent_claim():
    from gunnchos_device_os.golden_journeys.harness import run_supporting_subset

    report = run_supporting_subset(
        ["GOLDEN-01"],
        root=ROOT,
        write_scorecards=False,
        write_report=False,
    )
    assert report["claim_boundary"]["independent_verification_claimed"] is False
    assert report["claim_boundary"]["frontier_parity_claimed"] is False
    row = report["journeys"][0]
    assert row["INDEPENDENT_VERIFICATION"] == "PENDING"
    assert row["FUNCTIONAL_PASS"] in {"PASS", "FAIL"}
    # Supporting harness report stays PENDING; committed scorecard may already hold
    # independent verifier PASS/PARTIAL/FAIL, but claim_boundary must remain false.
    card = json.loads(
        (ROOT / "quality/golden_journeys/scorecards/GOLDEN-01.scorecard.json").read_text(
            encoding="utf-8"
        )
    )
    assert card["INDEPENDENT_VERIFICATION"]["status"] in {
        "PENDING",
        "NOT_CLAIMED",
        "PASS",
        "PARTIAL",
        "FAIL",
        "BLOCKED",
    }
    if card["INDEPENDENT_VERIFICATION"]["status"] in {"PASS", "PARTIAL"}:
        assert str(card.get("updated_by", "")).startswith("independent-verifier")
    assert card["claim_boundary"]["independent_verification_claimed"] is False


def test_merge_recommendation_blocks_on_schema_ok_and_s0_s1(tmp_path):
    import shutil

    from gunnchos_device_os.golden_journeys.merge_gate import recommend_merge as _rec

    # Isolate writable quality tree so tests do not dirty committed scorecards
    staging = tmp_path / "device-os"
    for rel in ("quality/golden_journeys", "user_journeys"):
        src = ROOT / rel
        dst = staging / rel
        shutil.copytree(
            src,
            dst,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "runtime"),
        )
    (staging / "artifacts").mkdir(parents=True, exist_ok=True)
    report = _rec(
        journey_ids=["GOLDEN-09", "GOLDEN-10"],
        root=staging,
        run_harness=True,
        major_pr=True,
    )
    assert report["auto_merge"] is False
    assert report["draft_only"] is True
    assert report["claim_boundary"]["independent_verification_claimed"] is False
    if report["merge_recommended"]:
        assert report["supporting_run_ok"] is True
    for jid in ("GOLDEN-09", "GOLDEN-10"):
        card = json.loads(
            (
                staging / "quality/golden_journeys/scorecards" / f"{jid}.scorecard.json"
            ).read_text(encoding="utf-8")
        )
        # Merge gate must never set claim_boundary independent token true.
        assert card["claim_boundary"]["independent_verification_claimed"] is False
