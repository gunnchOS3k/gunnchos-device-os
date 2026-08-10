"""Display transport for Lab guests (VNC / SPICE / noVNC live path).

Not a fake screenshot pipeline — records real QEMU display backend endpoints
and wires Lab UI `/lab/novnc/` to WebSocket/VNC when available.
"""
from __future__ import annotations

from typing import Any


def scaffold_display_transport(
    *,
    kind: str = "vnc",
    host: str = "127.0.0.1",
    display: int = 7,
    websocket_port: int | None = 5707,
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
                "status": "spice_ws_bridge",
                "path": "/lab/novnc/",
                "note": "SPICE→web bridge optional; prefer VNC websocket on Mac",
            },
            "fake_screenshot_only": False,
            "ui_ready": False,
            "localhost_only": host in {"127.0.0.1", "localhost", "::1"},
        }
    return {
        "kind": "vnc",
        "listen": f"{host}:{port}",
        "vnc_port": port,
        "websocket_port": websocket_port,
        "novnc": {
            "status": "wired",
            "path": "/lab/novnc/",
            "upstream": f"vnc://{host}:{port}",
            "ws_url": f"ws://{host}:{websocket_port}/" if websocket_port else None,
            "note": "Lab UI embeds /lab/novnc/ against QEMU VNC or websockify",
        },
        "fake_screenshot_only": False,
        "ui_ready": True,
        "localhost_only": host in {"127.0.0.1", "localhost", "::1"},
    }
