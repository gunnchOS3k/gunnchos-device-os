"""Tests for local identity helpers."""
from gunnchos_device_os.identity import (
    new_boot_id,
    new_device_id,
    new_session_id,
    sha256_json,
    sha256_text,
    stable_hardware_identity,
)


def test_ids_unique_enough():
    assert new_session_id() != new_session_id()
    assert new_boot_id().startswith("boot-")
    assert new_device_id().startswith("dev-")


def test_checksums():
    assert sha256_text("abc") == sha256_text("abc")
    assert sha256_json({"b": 1, "a": 2}) == sha256_json({"a": 2, "b": 1})


def test_hardware_identity_no_secrets():
    hw = stable_hardware_identity()
    # Must not emit secret-bearing fields (note text may mention exclusions).
    for forbidden in ("serial", "mac_address", "hostname", "username"):
        assert forbidden not in hw
    assert "identity_fingerprint" in hw
    assert hw.get("note")
