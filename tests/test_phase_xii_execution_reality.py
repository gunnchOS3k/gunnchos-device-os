from __future__ import annotations

import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_depth_ledger_script_imports():
    from gunnchos_device_os.phase_xii.depth import classify_action, depth_rank

    assert depth_rank(classify_action("game_launch", phase="xi")) < 4
    assert depth_rank(classify_action("game_launch", phase="xii")) >= 4


def test_real_mail_smtp_imap_roundtrip(tmp_path):
    from gunnchos_device_os.phase_xii.protocols.mail import MailStack

    m = MailStack()
    info = m.start()
    assert info["ok"]
    sent = m.send_message("a@localhost", "b@localhost", "t", "body")
    assert sent["ok"]
    recv = m.receive_latest()
    assert recv["ok"]
    assert recv["count"] >= 1
    m.stop()


def test_webdav_put_get(tmp_path):
    from gunnchos_device_os.phase_xii.protocols.webdav import WebDAVStack

    s = WebDAVStack(tmp_path / "dav")
    assert s.start()["ok"]
    put = s.put("f.txt", b"hello-phase-xii", 1)
    assert put["ok"]
    got = s.get("f.txt")
    assert got["ok"]
    assert b"hello-phase-xii" in got["content"]
    s.stop()


def test_matrix_send():
    from gunnchos_device_os.phase_xii.protocols.matrix import MatrixHomeserver

    hs = MatrixHomeserver()
    assert hs.start()["ok"]
    r = hs.send_text("!x:localhost", "hi")
    assert r["ok"]
    hs.stop()


def test_games_adapter_refuses_fixture_as_default_under_real_mode(monkeypatch):
    monkeypatch.setenv("REAL_APP_EXECUTION_MODE", "ACTIVE")
    from gunnchos_device_os.phase_xi.adapters import games

    # Missing sibling still must not invent fixture gameplay proof as real
    res = games.play_short_session(ROOT, "no-such-game-xyz")
    assert res.get("fixture_json_used") is False or res.get("NOT_YET_REAL_APP_PROVEN") is True or res.get("ok") is False


def test_claim_scope_writer(tmp_path, monkeypatch):
    # Use real root artifacts if present after ledger build
    from gunnchos_device_os.phase_xii.claim_scope import write_claim_scope

    if not (ROOT / "artifacts" / "phase_xi" / "JOURNEY_TOKENS.json").exists():
        pytest.skip("phase xi tokens missing")
    scope = write_claim_scope(ROOT)
    assert scope["firewall"]["reject_REAL_DAY_DIGITAL_PASS_below_L4_L5"] is True
    assert scope["firewall"]["PHASE_XI_BEHAVIORAL_JOURNEY_HARNESS_PASS"] is True
