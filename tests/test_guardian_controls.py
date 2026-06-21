"""Tests for guardian controls stub."""
from gunnchos_device_os.guardian_controls import apply_guardian_defaults, enable_guardian_controls


def test_no_private_inspection():
    d = apply_guardian_defaults("elementary")
    assert d["private_content_inspection"] is False


def test_enable():
    r = enable_guardian_controls("p1", "pre_k")
    assert r["mock"] is True
