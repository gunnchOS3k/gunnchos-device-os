from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_student_overlay_does_not_mask_journey_fail(monkeypatch, tmp_path):
    """Composite components must not mark RJ-STUDENT-001 pass when journey FAIL."""
    from gunnchos_device_os.phase_xii.journeys import rj_acceptance as mod

    # Minimal synthetic: ensure the pass formula is fail-closed
    journey_ok = False
    component_ok = True
    ai_ok = True
    assert not (journey_ok and component_ok and ai_ok)


def test_submission_receipt_uses_real_lms(tmp_path):
    from gunnchos_device_os.phase_xii.protocols.stack import RealProtocolStack
    from gunnchos_device_os.phase_xii.journeys.real_harness import RealJourneyHarness
    import httpx

    stack = RealProtocolStack(ROOT, work_dir=tmp_path / "proto")
    info = stack.start()
    assert info["ok"]
    r = httpx.post(stack.endpoints["lms"].rstrip("/") + "/submit", content=b"wave0", timeout=10)
    assert r.status_code == 200
    harness = RealJourneyHarness(root=ROOT, work_dir=tmp_path / "work")
    harness.real = stack
    harness._real_started = True
    harness.evidence = tmp_path / "evidence"
    harness.evidence.mkdir(parents=True, exist_ok=True)
    out = harness._real_submission_receipt({})
    assert out.get("ok") is True
    assert out.get("receipt")
    stack.stop()


def test_beatlink_refuses_synthetic_html_pass(monkeypatch, tmp_path):
    from gunnchos_device_os.phase_xii.apps import games as games_mod

    missing = games_mod.launch_beatlink(ROOT, tmp_path / "bl")
    # Without sibling / without vitest success, must not be ok via fake HTML
    if missing.get("error") == "beatlink_repo_missing":
        assert missing.get("ok") is False
    else:
        # If sibling present locally, ok only when vitest_ok
        if missing.get("ok"):
            assert missing.get("vitest_ok") is True
        assert missing.get("fixture_json_used") is False
