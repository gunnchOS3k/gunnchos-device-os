"""18-course WAIKE seed depth: unique, executable, honest."""

from __future__ import annotations

import json
from pathlib import Path

from gunnchos_device_os.first_party_apps.waike_app import run_waike_app
from gunnchos_device_os.waike_curriculum.auditor import SIMILARITY_S1, pairwise_similarity
from gunnchos_device_os.waike_curriculum.catalog import COURSE_IDS, FACETS
from gunnchos_device_os.waike_curriculum.content import FORBIDDEN_PHRASES, assert_all_seeds, seed_for
from gunnchos_device_os.waike_curriculum.labs import FIXTURES, SOLVERS, run_all_labs, run_lab
from gunnchos_device_os.waike_integration import list_offline_lessons

ROOT = Path(__file__).resolve().parents[2]


def test_eighteen_accepted_ids():
    assert len(COURSE_IDS) == 18
    assert len(set(COURSE_IDS)) == 18
    assert_all_seeds()
    assert set(SOLVERS) == set(COURSE_IDS)
    assert set(FIXTURES) == set(COURSE_IDS)


def test_labs_all_execute():
    result = run_all_labs()
    assert result["ok"] is True
    assert result["count"] == 18
    # Domain-specific expected fragments — not a shared template output.
    assert run_lab("NETWORKING_INFRA")["result"]["usable_hosts"] == 62
    assert run_lab("WIRELESS_6G")["result"]["symbol_samples"] == 80
    assert run_lab("HARDWARE_ENGINEERING")["result"]["vout"] == 3.75
    assert run_lab("CYBER_SOC")["result"]["burst_users"] == ["ada"]
    assert run_lab("CLOUD_DEVOPS")["result"]["ok"] is True
    assert run_lab("DATA_VIZ_BI")["result"]["counts"] == [3, 1, 1]


def test_not_templated_pairwise():
    sim = pairwise_similarity()
    assert sim["templated_cluster_detected"] is False
    assert sim["worst_jaccard"] < SIMILARITY_S1
    for cid in COURSE_IDS:
        blob = seed_for(cid)["lesson"].lower()
        for phrase in FORBIDDEN_PHRASES:
            assert phrase not in blob


def test_artifacts_and_register(tmp_path, monkeypatch):
    register = ROOT / "artifacts/waike/WAIKE_COURSE_REGISTER.json"
    assert register.exists()
    payload = json.loads(register.read_text(encoding="utf-8"))
    assert payload["full_curriculum_complete"] is False
    assert payload["HUMAN_E6"] is False
    assert payload["STUDENT_VALIDATED"] is False
    assert len(payload["courses"]) == 18
    assert payload["counts"]["course_complete"] == 0
    assert not payload["S0_open"]
    ids = [row["course_id"] for row in payload["courses"]]
    assert ids == list(COURSE_IDS)
    for row in payload["courses"]:
        assert row["course_complete"] is False
        assert row["engagement_readiness"] == "DIGITAL_SEED_NOT_COHORT_READY"
        assert row["lab_executable"] is True
        assert row["product_content_class"] == "REAL_SEED_EXECUTABLE"
        for facet in FACETS:
            assert facet in row["facets"]
        lesson = ROOT / "content/waike/courses" / row["course_id"] / "lesson.md"
        lab = ROOT / "content/waike/courses" / row["course_id"] / "lab.py"
        assert lesson.exists() and lab.exists()


def test_app_runs_course_lab(tmp_path, monkeypatch):
    monkeypatch.setenv("GUNNCHOS_SANDBOX_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("GUNNCHOS_APP_PERMISSIONS", "storage_read,storage_write,ai_interface")
    r1 = run_waike_app(course_id="WIRELESS_6G", lesson_id="WIRELESS_6G")
    r2 = run_waike_app(course_id="WIRELESS_6G", lesson_id="WIRELESS_6G")
    assert r1["ok"] and r2["ok"]
    assert r2["persisted_progress_pct"] > r1["persisted_progress_pct"]
    assert r1["lab"]["ok"] is True
    assert "cyclic prefix" in (r1["lesson_body"] or "").lower() or "OFDM" in (r1["lesson_body"] or "")
    assert r1["full_curriculum_complete"] is False
    assert r1["HUMAN_E6"] is False
    assert (tmp_path / "waike_portfolio.json").exists()
    # Legacy pack still resolves (companion /api/waike/start lesson_id).
    legacy = run_waike_app(lesson_id="wireless_basics_101")
    assert legacy["ok"]
    assert legacy["course_id"] == "WIRELESS_6G"


def test_offline_lessons_include_courses():
    lessons = list_offline_lessons()
    assert "wireless_basics_101" in lessons
    for cid in COURSE_IDS:
        assert cid in lessons


def test_ui_is_not_json_pack_browser():
    html = (ROOT / "apps/waike_learning/index.html").read_text(encoding="utf-8")
    js = (ROOT / "apps/waike_learning/app.js").read_text(encoding="utf-8")
    assert "id=\"lesson-content\"" in html
    assert "JSON.stringify(state.progress" not in js
    assert "/api/waike/start" in js
    assert "RUNTIME_UNAVAILABLE" in js
    catalog = json.loads((ROOT / "apps/waike_learning/courses.json").read_text(encoding="utf-8"))
    assert catalog["full_curriculum_complete"] is False
    assert len(catalog["courses"]) == 18
