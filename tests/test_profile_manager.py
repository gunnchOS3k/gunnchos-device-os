from gunnchos_device_os.profile_manager import get_profile

def test_student_default():
    assert get_profile("student")["default_mode"] == "School"
