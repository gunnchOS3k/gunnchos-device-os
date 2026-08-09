"""Phase XI real-user journey harness — CI-safe representative suite."""
from __future__ import annotations

import json
from pathlib import Path

from gunnchos_device_os.phase_xi.campaign import REPRESENTATIVE_CI, run_campaign
from gunnchos_device_os.phase_xi.evt_companions import map_physical_followups
from gunnchos_device_os.phase_xi.harness import JourneyHarness
from gunnchos_device_os.phase_xi.policies import MultitaskingPolicy, NotificationPolicy
from gunnchos_device_os.phase_xi.services import LocalServiceStack


ROOT = Path(__file__).resolve().parents[1]


def test_journey_catalog_complete():
    catalog = json.loads((ROOT / "user_journeys" / "journeys" / "CATALOG.json").read_text(encoding="utf-8"))
    assert catalog["count"] == 79
    for item in catalog["journeys"]:
        path = ROOT / "user_journeys" / "journeys" / f"{item['id']}.json"
        assert path.exists(), item["id"]
        data = json.loads(path.read_text(encoding="utf-8"))
        for key in ("id", "persona", "goal", "devices", "steps", "required_apps", "required_services"):
            assert key in data


def test_local_services_no_cloud_creds():
    stack = LocalServiceStack(ROOT)
    info = stack.start()
    assert info["ok"]
    health = stack.request("GET", "/health")
    assert health["ok"] is True
    mail = stack.request("POST", "/smtp/send", {"subject": "t", "body": "b"})
    assert mail["ok"] is True
    stack.stop()
    discovery = json.loads((ROOT / "user_journeys" / "services" / "DISCOVERY.json").read_text(encoding="utf-8"))
    assert discovery["commercial_cloud_creds_required"] is False
    assert discovery["bind"] == "127.0.0.1"
    assert "/Users/gunnchos" not in json.dumps(discovery)


def test_policies_never_silent_kill_or_destroy_media():
    mt = MultitaskingPolicy()
    r = mt.admit("document_music", 99.0)
    assert r["kill_user_work"] is False
    n = NotificationPolicy()
    n.set_focus_mode(True)
    blocked = n.push("game", "x")
    assert blocked["delivered"] is False


def test_student_day_journey_passes():
    h = JourneyHarness(ROOT)
    ev = h.run_journey("J-STU-001")
    h.stack.stop()
    assert ev["status"] == "PASS", ev.get("fail_reason")
    assert "/Users/gunnchos" not in json.dumps(ev)


def test_representative_ci_suite_passes():
    report = run_campaign(root=ROOT, representative=True, write=False)
    assert report["totals"]["FAIL"] == 0, report["results"]
    for jid in REPRESENTATIVE_CI:
        row = next(r for r in report["results"] if r["id"] == jid)
        assert row["status"] == "PASS", row
    assert report["open_digital_u0_u1"] == []


def test_evt_companions_mapped():
    payload = map_physical_followups(ROOT)
    assert payload["count"] >= 1
    assert all(c["not_in_digital_backlog"] for c in payload["companions"])


def test_missing_handler_regressions_fixed():
    """UJ-DEFECT-0001..0006: previously missing step handlers must PASS."""
    h = JourneyHarness(ROOT)
    for jid in ("J-OFF-004", "J-OFF-008", "J-GAME-006", "J-NET-004", "J-REC-002", "J-HAND-001"):
        ev = h.run_journey(jid)
        assert ev["status"] == "PASS", (jid, ev.get("fail_reason"))
    h.stack.stop()
