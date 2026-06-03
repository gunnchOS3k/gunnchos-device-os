import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from telemetry.privacy_filter import filter_packet


def test_strips_forbidden():
    p = filter_packet({"latency_ms": 1, "user_id": "x", "email": "a@b.c"})
    assert "user_id" not in p
    assert "email" not in p
    assert p["latency_ms"] == 1
