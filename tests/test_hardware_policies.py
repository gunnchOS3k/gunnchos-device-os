"""Tests for hardware policy modules."""
from gunnchos_device_os.hardware_input_policy import check_input
from gunnchos_device_os.hardware_mode_policy import check_mode
from gunnchos_device_os.hardware_thermal_policy import check_thermal


def test_mode_blocked_wearables():
    r = check_mode("wearables_arena_set", "Developer")
    assert r["status"] == "fail"


def test_thermal_wearables_dev():
    r = check_thermal("wearables_arena_set", "Developer")
    assert r["status"] == "fail"


def test_input_developer_student():
    r = check_input("student_14_5", "Developer")
    assert r["status"] == "pass"
