"""Display transport scaffolding for Lab guests (VNC / SPICE / noVNC path).

Not a fake screenshot pipeline — records real QEMU display backend endpoints.
UI polish (noVNC embed) is intentionally deferred.
"""
from __future__ import annotations

from typing import Any


def scaffold_display_transport(
    *,
    kind: str = "vnc",
    host: str = "127.0.0.1",
    display: int = 7,
) -> dict[str, Any]:
    port = 5900 + display
    if kind == "none":
        return {
            "kind": "none_headless",
            "fake_screenshot_only": False,
            "ui_ready": False,
            "note": "Headless; enable vnc/spice for live path",
        }
    if kind == "spice":
        return {
            "kind": "spice",
            "listen": f"{host}:{port}",
            "novnc": {
                "status": "scaffold",
                "path": "/lab/novnc/",
                "note": "Proxy to SPICE/WebSocket in follow-up UI PR",
            },
            "fake_screenshot_only": False,
            "ui_ready": False,
            "localhost_only": host in {"127.0.0.1", "localhost", "::1"},
        }
    return {
        "kind": "vnc",
        "listen": f"{host}:{port}",
        "novnc": {
            "status": "scaffold",
            "path": "/lab/novnc/",
            "upstream": f"vnc://{host}:{port}",
            "note": "noVNC static + websockify wiring deferred; endpoint is real VNC",
        },
        "fake_screenshot_only": False,
        "ui_ready": False,
        "localhost_only": host in {"127.0.0.1", "localhost", "::1"},
    }
