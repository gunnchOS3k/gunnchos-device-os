from gunnchos_launcher.mode_manager import switch_mode, validate_mode


def test_switch_school():
    r = switch_mode("student_14_5", "school")
    assert "WAIKE Classroom" in r["allowed_apps"]


def test_validate_mode():
    assert validate_mode("fleet_admin")
