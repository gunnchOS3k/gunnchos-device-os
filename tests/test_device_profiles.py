from gunnchos_device_os.hardware_abstraction import get_device_profile

def test_student14():
    p = get_device_profile("Student14")
    assert p["keyboard"] is True
