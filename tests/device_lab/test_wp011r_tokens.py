import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def test_master_complete_false():
    gaps = json.loads((ROOT / "artifacts/wp011r/DEVICE_LAB_REMAINING_DIGITAL_GAPS.json").read_text())
    assert gaps["master_token"]["GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE"] is False
    assert gaps["tokens"]["FOUR_GAME_REAL_RUNTIME_DEVICE_LAB_PASS"] is False

def test_independent_score_exists():
    p = ROOT / "artifacts/wp011r/DEVICE_LAB_SCORE_INDEPENDENT.json"
    assert p.is_file()
    data = json.loads(p.read_text())
    assert data["GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE"] is False
    assert data["hardcoded_tens_forbidden"] is True

def test_development_guest_labeled():
    from gunnchos_device_os.device_lab.image_builder import DEVICE_LAB_DEVELOPMENT_GUEST, SHIPPING_IMAGE
    assert DEVICE_LAB_DEVELOPMENT_GUEST is True
    assert SHIPPING_IMAGE is False
