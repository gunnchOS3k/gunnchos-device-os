"""Linux-target provider qualification — never inherit macOS PASS as Linux PASS."""

from __future__ import annotations

import platform
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ProviderQual:
    name: str
    binary: Optional[str] = None
    version: Optional[str] = None
    arch: Optional[str] = None
    pid: Optional[int] = None
    window: Optional[str] = None
    protocol: Optional[str] = None
    failure_mode: Optional[str] = None
    offline_behavior: Optional[str] = None
    evidence_class: str = "BLOCKED"
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "binary": self.binary,
            "version": self.version,
            "architecture": self.arch or platform.machine(),
            "pid": self.pid,
            "graphical_window": self.window,
            "protocol": self.protocol,
            "failure_mode": self.failure_mode,
            "offline_behavior": self.offline_behavior,
            "evidence_class": self.evidence_class,
            "notes": self.notes,
            "host_os": platform.system(),
            "linux_target_required": True,
        }


def _which(names: List[str]) -> Optional[str]:
    for n in names:
        p = shutil.which(n)
        if p:
            return p
    return None


def qualify_linux_providers(*, linux_session_proven: bool = False) -> Dict[str, Any]:
    """Qualify providers for Linux product closure.

    On non-Linux hosts without a proven guest session, every domain stays
    BLOCKED / HUMAN_VALIDATION_PENDING — never copy macOS CX2 results.
    """
    is_linux = platform.system() == "Linux"
    session_ok = bool(linux_session_proven and is_linux)

    def pending(name: str, binary_names: List[str], protocol: str) -> ProviderQual:
        binary = _which(binary_names) if (is_linux or False) else None
        if session_ok and binary:
            return ProviderQual(
                name=name,
                binary=binary,
                protocol=protocol,
                evidence_class="REAL_PROVIDER_CLI_PASS",
                notes="binary present in Linux session; GUI window still required for GUI PASS",
                offline_behavior="provider-specific",
            )
        return ProviderQual(
            name=name,
            binary=binary,
            protocol=protocol,
            evidence_class="BLOCKED",
            failure_mode="linux_gui_session_not_proven",
            notes=(
                "CX2D requires Linux graphical target. Host="
                f"{platform.system()}. linux_session_proven={linux_session_proven}. "
                "macOS CX2 CLI PASS is not inherited."
            ),
            offline_behavior="unproven",
        )

    domains = {
        "browser": pending("browser", ["chromium", "chromium-browser", "google-chrome", "firefox"], "https"),
        "productivity": pending("libreoffice", ["soffice", "libreoffice"], "odf/uno"),
        "app_center": pending("flatpak", ["flatpak"], "flatpak"),
        "printing": pending("cups", ["lp", "lpstat", "cupsd"], "ipp"),
        "portals": pending("xdg-desktop-portal", ["xdg-desktop-portal"], "xdg-desktop-portal"),
        "capture": pending("grim/wlroots", ["grim", "wf-recorder"], "wayland-screenshot"),
        "mail": pending("mail", ["thunderbird", "evolution"], "smtp/imap"),
        "dav": pending("caldav/carddav", ["evolution", "thunderbird"], "caldav/carddav"),
        "chat_video": pending("chat/video", ["element-desktop", "chromium"], "matrix/webrtc"),
        "a11y": pending("at-spi", ["busctl", "orca"], "at-spi"),
    }
    return {
        "schema": "gunnchos.cx2d.linux_provider_qualification.v1",
        "linux_session_proven": session_ok,
        "host_os": platform.system(),
        "host_arch": platform.machine(),
        "domains": {k: v.to_dict() for k, v in domains.items()},
        "claim_boundary": "Do not standardize defaults until Linux matrix green.",
    }
