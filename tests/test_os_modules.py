from gunnchos_device_os.device_health import get_health_snapshot
from gunnchos_device_os.input_mapper import get_bindings, controller_first_nav_enabled
from gunnchos_device_os.waike_integration import list_offline_lessons
from gunnchos_device_os.gunnchai_integration import tutor_session_start

def test_health_mock():
    h = get_health_snapshot("Student14")
    assert "battery_percent" in h

def test_input_mapper():
    b = get_bindings()
    assert "bindings" in b

def test_controller_first():
    assert controller_first_nav_enabled("HandheldHybrid") is True

def test_waike_lessons():
    assert len(list_offline_lessons()) >= 1

def test_gunnchai_tutor():
    assert tutor_session_start("student", "math")["pii_collection"] is False
