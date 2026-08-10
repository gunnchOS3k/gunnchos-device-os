"""WP-002 handheld storage policy Outcome A."""
from gunnchos_device_os.hardware_storage_policy import check_storage
from gunnchos_device_os.hardware_manifest_loader import load_device_profile


def test_handheld_profile_is_emmc_32_not_invented_nvme():
    p = load_device_profile("handheld_hybrid")
    assert p.storage.storage_class == "emmc"
    assert p.storage.min_gb == 32


def test_handheld_game_pack_requires_expansion():
    denied = check_storage("handheld_hybrid", "game_pack", expansion_mounted=False)
    assert denied["status"] == "fail"
    allowed = check_storage("handheld_hybrid", "game_pack", expansion_mounted=True)
    assert allowed["status"] == "pass"


def test_handheld_system_only_ok():
    r = check_storage("handheld_hybrid", "")
    assert r["status"] == "pass"
