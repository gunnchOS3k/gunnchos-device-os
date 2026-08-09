"""Detect real executables without home-path PASS dependency."""
from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Any


CANDIDATES = {
    "browser": ["chromium", "chromium-browser", "google-chrome", "google-chrome-stable", "firefox", "firefox-esr", "msedge"],
    "office": ["soffice", "libreoffice"],
    "pdf": ["evince", "okular", "atril", "pdftotext", "soffice"],
    "file_manager": ["nautilus", "dolphin", "thunar", "pcmanfm", "nemo"],
    "terminal": ["gnome-terminal", "konsole", "xterm", "kitty", "alacritty", "xfce4-terminal"],
    "editor": ["code", "code-oss", "nvim", "vim", "gedit", "kate"],
    "media": ["ffplay", "mpv", "vlc", "ffmpeg"],
    "git": ["git"],
    "cups": ["lp", "lpstat"],
    "vpn": ["wg", "wg-quick", "openvpn"],
    "compositor": ["weston", "sway", "kwin_wayland", "gnome-shell", "xfwm4"],
    "display": ["Xvfb", "weston", "Xorg"],
    "godot": ["godot", "godot4", "Godot_v4"],
    "llama": ["llama-server", "llama-cli", "llama-completion"],
}


def which_first(names: list[str]) -> dict[str, str] | None:
    for n in names:
        p = shutil.which(n)
        if p:
            return {"name": n, "path": p}
    # also search PATH extras without depending on /Users/gunnchos for PASS
    extras = os.environ.get("PATH", "").split(os.pathsep)
    for n in names:
        for d in extras:
            cand = Path(d) / n
            if cand.is_file() and os.access(cand, os.X_OK):
                return {"name": n, "path": str(cand)}
    return None


def version_of(path: str) -> str:
    for args in ([path, "--version"], [path, "-v"], [path, "version"]):
        try:
            r = subprocess.run(args, capture_output=True, text=True, timeout=8)
            out = (r.stdout or r.stderr or "").strip().splitlines()
            if out:
                return out[0][:200]
        except Exception:
            continue
    return "unknown"


def audit_host() -> dict[str, Any]:
    found: dict[str, Any] = {}
    for role, names in CANDIDATES.items():
        hit = which_first(names)
        if hit:
            hit["version"] = version_of(hit["path"])
        found[role] = hit
    return {
        "schema": "gunnchos.phase_xii.host_audit.v1",
        "binaries": found,
        "path_home_dependency_forbidden": True,
        "pass_requires_no_users_gunnchos_path": True,
    }
