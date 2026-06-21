"""Tests for device classes."""
from gunnchos_device_os.device_classes import (
    REQUIRED_FIELDS,
    get_device_class,
    list_device_classes,
    validate_device_class,
)


REQUIRED_CLASSES = {"student_14_5", "handheld_hybrid", "ds_xl_coder", "wearables_arena_set"}


def test_four_device_classes_exist():
    assert REQUIRED_CLASSES.issubset(set(list_device_classes()))


def test_required_fields():
    for cid in list_device_classes():
        missing = validate_device_class(cid)
        assert not missing, f"{cid} missing {missing}"


def test_journey_presets_and_modes():
    for cid in list_device_classes():
        dc = get_device_class(cid)
        assert dc["supported_journey_presets"]
        assert dc["supported_modes"]
        assert dc["accessibility_defaults"]
