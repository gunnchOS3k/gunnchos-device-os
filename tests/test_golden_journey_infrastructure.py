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


def test_scorecards_distinguish_five_statuses():
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
        assert card["INDEPENDENT_VERIFICATION"]["status"] in {"PENDING", "NOT_CLAIMED", "FAIL", "BLOCKED"}
        assert card["INDEPENDENT_VERIFICATION"]["status"] != "PASS"
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


def test_verifier_stub_paths_exist():
    plan = ROOT / "quality/golden_journeys/verifier/INDEPENDENT_GOLDEN_ACCEPTANCE_PLAN.md"
    results = ROOT / "quality/golden_journeys/verifier/INDEPENDENT_GOLDEN_ACCEPTANCE_RESULTS.md"
    assert plan.exists()
    assert results.exists()
    text = plan.read_text(encoding="utf-8")
    assert "VERIFIER OWNED" in text
    assert "Implementer stub" in text


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
    # Committed scorecard remains non-independent
    card = json.loads(
        (ROOT / "quality/golden_journeys/scorecards/GOLDEN-01.scorecard.json").read_text(
            encoding="utf-8"
        )
    )
    assert card["INDEPENDENT_VERIFICATION"]["status"] == "PENDING"
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
        assert card["INDEPENDENT_VERIFICATION"]["status"] != "PASS"
