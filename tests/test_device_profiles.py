from gunnchos_launcher.device_profile import get_profile

def test_student_school():
    p = get_profile("student_14_5", "school")
    assert p["offline_ready"]
