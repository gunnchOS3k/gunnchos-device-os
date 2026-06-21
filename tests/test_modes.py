"""Tests for OS modes."""
from gunnchos_device_os.mode_manager import get_mode_policy, list_modes


REQUIRED = {
    "School", "Developer", "Research Measurement", "Play", "Media",
    "Studio", "Workshop", "Laboratory", "Guardian", "Library", "Offline", "Admin",
}


def test_modes_exist():
    assert REQUIRED.issubset(set(list_modes()))


def test_school_mode():
    p = get_mode_policy("School")
    assert p.get("simplified_home") is True
    assert "steam" in p["blocked_apps"]
    assert p.get("no_invasive_surveillance") is True


def test_developer_mode():
    p = get_mode_policy("Developer")
    assert "vscode" in p["allowed_apps"]
    assert p.get("wsl_path") is True


def test_research_mode():
    p = get_mode_policy("Research Measurement")
    assert p.get("no_private_packet_capture") is True
    assert p.get("consent_prompts") is True
