from __future__ import annotations

from gunnchos_device_os.ops.first_use import FirstUseFlow, STEPS


def test_offline_first_use_completes_all_steps(tmp_path):
    flow = FirstUseFlow(tmp_path / "first_use.json")
    result = flow.run_default_offline_student("s1", user_id="student-1")
    assert result["ok"] is True
    session = result["session"]
    assert session["status"] == "COMPLETE"
    assert session["online"] is False
    assert "update" in session["deferred"]
    for step in STEPS:
        assert step in session["completed"] or step in session["deferred"]
    assert session["results"]["ring_pairing"]["physical_ring_claimed"] is False
    assert session["results"]["dock_discovery"]["physical_dock_claimed"] is False
    assert session["results"]["privacy"]["legal_certification"] == "HUMAN/EXTERNAL"
    assert session["results"]["student_profile"]["profile"]["user_id"] == "student-1"


def test_youth_cloud_ai_is_denied(tmp_path):
    flow = FirstUseFlow(tmp_path / "first_use.json")
    flow.start("s2", user_id="kid-1")
    flow.apply_language("s2", "en")
    flow.apply_accessibility("s2", [])
    flow.apply_network("s2", online=True, ssid="school")
    flow.apply_offline_continuation("s2")
    flow.apply_privacy("s2", profile_type="child", consent="opt_in_research")
    ai = flow.apply_ai_choice("s2", "cloud")
    assert ai["ok"] is True
    assert ai["result"]["denied"] is True
    assert ai["result"]["choice"] == "local_only"


def test_unsupported_language_rejected(tmp_path):
    flow = FirstUseFlow(tmp_path / "first_use.json")
    flow.start("s3")
    bad = flow.apply_language("s3", "xx")
    assert bad["ok"] is False
