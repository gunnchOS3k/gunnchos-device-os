"""WP-007 red-team harness regression (implementer)."""
from __future__ import annotations

import json
from pathlib import Path

from gunnchos_device_os.security_red_team.harness import run_red_team


ROOT = Path(__file__).resolve().parents[2]


def test_red_team_harness_s0_s1_clear():
    report = run_red_team(write=True)
    assert report["SECURITY_S0"] == 0
    assert report["SECURITY_S1"] == 0
    assert report["INTERNAL_RED_TEAM_READY"] is True
    assert report["external_pentest"] == "EXTERNAL_PENDING"
    assert report["production_ready_security_claimed"] is False
    assert report["cases_passed"] == report["cases_total"]
    readiness = ROOT / "artifacts" / "wp007" / "INTERNAL_RED_TEAM_READINESS.json"
    assert readiness.exists()
    data = json.loads(readiness.read_text(encoding="utf-8"))
    assert data["INTERNAL_RED_TEAM_READY"] is True
    assert data["implementer_self_certify"] is False


def test_attack_corpus_case_ids_present():
    corpus = json.loads(
        (ROOT / "security" / "wp007_red_team" / "corpus" / "ATTACK_CORPUS.json").read_text(
            encoding="utf-8"
        )
    )
    ids = {c["id"] for c in corpus["cases"]}
    report = run_red_team(write=False)
    harness_ids = {c["case_id"] for c in report["cases"] if c["case_id"].startswith("SEC-")}
    assert ids == harness_ids


def test_golden_journey_control_map_covers_g01_g10():
    mapping = json.loads(
        (ROOT / "docs" / "security" / "wp007" / "GOLDEN_JOURNEY_CONTROL_MAP.json").read_text(
            encoding="utf-8"
        )
    )
    expected = {f"GOLDEN-{i:02d}" for i in range(1, 11)}
    got = {j["id"] for j in mapping["journeys"]}
    assert got == expected
