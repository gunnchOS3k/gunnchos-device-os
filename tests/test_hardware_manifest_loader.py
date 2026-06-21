"""Tests for hardware manifest loader."""
from gunnchos_device_os.hardware_manifest_loader import list_device_ids, load_device_profile, validate_profile


def test_four_profiles():
    assert len(list_device_ids()) >= 4


def test_load_student():
    p = load_device_profile("student_14_5")
    assert p.device_id == "student_14_5"
    assert "School" in p.supported_modes


def test_validate_clean():
    for did in list_device_ids():
        assert not validate_profile(did), did
