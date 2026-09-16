"""XDG Desktop Portal mediation probes — honest classification when absent."""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


PORTALS = (
    "org.freedesktop.portal.FileChooser",
    "org.freedesktop.portal.OpenURI",
    "org.freedesktop.portal.Notification",
    "org.freedesktop.portal.Settings",
    "org.freedesktop.portal.Screenshot",
    "org.freedesktop.portal.ScreenCast",
    "org.freedesktop.portal.Camera",
)


@dataclass
class RealPortalProvider:
    root: Path

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        self.root.mkdir(parents=True, exist_ok=True)

    def status(self) -> dict:
        return self.probe()

    def probe(self) -> dict:
        dbus_send = shutil.which("dbus-send")
        gdbus = shutil.which("gdbus")
        backend = None
        available = False
        results = {}
        if dbus_send or gdbus:
            backend = "gdbus" if gdbus else "dbus-send"
            # Introspect portal bus name
            cmd = [
                gdbus or dbus_send,
            ]
            if gdbus:
                cmd = [
                    "gdbus",
                    "call",
                    "--session",
                    "--dest",
                    "org.freedesktop.portal.Desktop",
                    "--object-path",
                    "/org/freedesktop/portal/desktop",
                    "--method",
                    "org.freedesktop.DBus.Peer.Ping",
                ]
            else:
                cmd = [
                    "dbus-send",
                    "--session",
                    "--dest=org.freedesktop.portal.Desktop",
                    "--print-reply",
                    "/org/freedesktop/portal/desktop",
                    "org.freedesktop.DBus.Peer.Ping",
                ]
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=5, check=False)
                available = proc.returncode == 0
            except (OSError, subprocess.TimeoutExpired):
                available = False
        for name in PORTALS:
            results[name] = {
                "available": available,
                "exercised": False,
                "user_response": None,
                "revoked": None,
                "evidence_class": "REAL_PROVIDER_PARTIAL" if available else "NOT_APPLICABLE",
                "notes": "linux_session_portal" if available else "host_without_xdg_desktop_portal",
            }
        report = {
            "backend": backend,
            "portal_bus_available": available,
            "portals": results,
            "evidence_class": "REAL_PROVIDER_PARTIAL" if available else "NOT_APPLICABLE",
            "claim_boundary": "no_fabricated_portal_success_on_unsupported_hosts",
        }
        (self.root / "PORTAL_PROBE.json").write_text(__import__("json").dumps(report, indent=2) + "\n")
        return report
