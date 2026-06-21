"""Tests for app pack manager."""
from gunnchos_device_os.app_pack_manager import get_app_pack, list_app_packs


REQUIRED_FIELDS = ("apps", "why_it_exists", "required_mode", "offline_support", "beginner_friendly_description")


def test_app_packs_count():
    assert len(list_app_packs()) >= 14


def test_app_pack_required_fields():
    for pack_id in list_app_packs():
        pack = get_app_pack(pack_id)
        for field in REQUIRED_FIELDS:
            assert field in pack, f"{pack_id} missing {field}"
