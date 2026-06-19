"""Legacy gunnchos_launcher mode manager tests."""
from gunnchos_launcher.mode_manager import switch_mode, validate_mode


def test_validate_mode_school():
    assert validate_mode("school") is True


def test_switch_mode_returns_apps():
    r = switch_mode("student_14_5", "school")
    assert "allowed_apps" in r
