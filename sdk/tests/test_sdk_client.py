"""Adopter SDK client tests."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from gunnchos_adopter_sdk import AdopterClient


def test_negotiate_compatible():
    c = AdopterClient()
    r = c.negotiate("device_role", "1.0.0")
    assert r["ok"] is True


def test_negotiate_major_mismatch():
    c = AdopterClient()
    r = c.negotiate("device_role", "2.0.0")
    assert r["ok"] is False
    assert r["reason"] == "major_mismatch"


def test_samples():
    c = AdopterClient()
    assert c.sample_ring_input()["ok"] is True
    assert c.sample_ai("hi")["cloud_export"] is False
    assert "wifi" in c.sample_connectivity()["bearers"]
    assert c.sample_telemetry()["pii"] is False
