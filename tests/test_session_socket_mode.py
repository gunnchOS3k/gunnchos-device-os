"""Session sockets must not be world-writable."""

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SOCKET_SOURCES = (
    REPO / "gunnchos_device_os/cx2f/session.py",
    REPO / "gunnchos_device_os/cx2g/session.py",
    REPO / "os_build/cx2h_linux_lab/scripts/repair_xdg_portal.sh",
)


def test_lab_session_scripts_do_not_chmod_world_writable():
    for path in SOCKET_SOURCES:
        text = path.read_text(encoding="utf-8")
        assert "chmod 777" not in text, path
        assert "chmod 1777" not in text, path
        assert "chmod 600" in text, path
