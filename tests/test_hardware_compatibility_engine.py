"""Tests for hardware compatibility engine."""
from gunnchos_device_os.hardware_compatibility_engine import evaluate_compatibility


def test_student_car_compatible():
    r = evaluate_compatibility("student_14_5", persona="high_school_student", journey_preset="car", mode="School")
    assert r.compatible
    assert r.status in ("pass", "warn")


def test_wearables_rejects_developer():
    r = evaluate_compatibility("wearables_arena_set", mode="Developer")
    assert not r.compatible
    assert r.recommended_fallbacks


def test_research_needs_consent():
    r = evaluate_compatibility("student_14_5", mode="Research Measurement", consent=False)
    assert not r.compatible
