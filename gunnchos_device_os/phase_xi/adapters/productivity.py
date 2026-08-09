
from __future__ import annotations
import shutil
from pathlib import Path
from typing import Any


def detect_stack(root: Path) -> dict[str, Any]:
    """Audit mature productivity/comms/media binaries + staged rootfs."""
    apps = {
        "browser": ["chromium", "chromium-browser", "google-chrome", "firefox", "firefox-esr"],
        "office": ["libreoffice", "soffice"],
        "pdf": ["evince", "okular", "atril", "libreoffice"],
        "email": ["thunderbird", "evolution"],
        "terminal": ["gnome-terminal", "konsole", "xterm", "kitty", "alacritty"],
        "editor": ["code", "code-oss", "nvim", "vim", "gedit"],
        "music": ["celluloid", "vlc", "mpv", "rhythmbox"],
        "video": ["mpv", "vlc", "celluloid"],
        "cups": ["lp", "lpstat"],
        "vpn": ["wg", "openvpn"],
        "git": ["git"],
    }
    found: dict[str, Any] = {}
    for role, names in apps.items():
        hit = None
        for n in names:
            p = shutil.which(n)
            if p:
                hit = {"name": n, "path": p}
                break
        found[role] = hit
    rootfs = root / "os_build" / "productivity_rootfs" / "root"
    ledger = rootfs / "opt" / "gunnchos" / "productivity" / "INSTALL_LEDGER.json"
    stack_yaml = root / "config" / "productivity" / "stack.yaml"
    # Prefer one app per job (documented in stack.yaml)
    one_per_job = {
        "office_documents": "libreoffice",
        "browser_x86_64": "chromium",
        "browser_aarch64": "firefox-esr",
        "print": "cups_virtual_pdf",
        "vpn": "wireguard_primary_openvpn_alt",
    }
    return {
        "schema": "gunnchos.productivity_stack_audit.v1",
        "host_binaries": found,
        "rootfs_staged": rootfs.exists(),
        "install_ledger_present": ledger.exists(),
        "stack_config": str(stack_yaml.relative_to(root)) if stack_yaml.exists() else None,
        "one_app_per_job": one_per_job,
        "commercial_cloud_creds_required": False,
        "path_home_dependency_forbidden": True,
    }
