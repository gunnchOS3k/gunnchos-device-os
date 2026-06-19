"""Mock media app routes — DRM/HDCP caveats in docs."""
from __future__ import annotations

ROUTES = {
    "youtube": "https://www.youtube.com/",
    "netflix": "https://www.netflix.com/",
    "hulu": "https://www.hulu.com/",
}


def open_route(service: str) -> dict:
    if service not in ROUTES:
        raise ValueError(service)
    return {
        "service": service,
        "url": ROUTES[service],
        "drm_note": "Requires licensed browser/HDCP — no circumvention",
        "mock": True,
    }
