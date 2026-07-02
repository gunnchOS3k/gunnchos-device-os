"""Media app routes and metadata — honest DRM/HDCP claim boundary."""
from __future__ import annotations

from typing import Any

# claim_status values:
#   browser_route_prototype — opens via browser/PWA shell; not certified
#   local_placeholder — local player not implemented
#   future_placeholder — planned route; not available

MEDIA_APPS: dict[str, dict[str, Any]] = {
    "youtube": {
        "id": "youtube",
        "name": "YouTube",
        "category": "video_streaming",
        "route_url": "https://www.youtube.com/",
        "launch_type": "browser_pwa",
        "requires_network": True,
        "requires_drm": False,
        "requires_hdcp_for_external_display": False,
        "offline_supported": False,
        "guardian_controlled": True,
        "school_mode_default": "policy_dependent",
        "claim_status": "browser_route_prototype",
        "notes": (
            "Browser route prototype. Some premium/rental content may require DRM. "
            "Service certification not claimed."
        ),
    },
    "netflix": {
        "id": "netflix",
        "name": "Netflix",
        "category": "video_streaming",
        "route_url": "https://www.netflix.com/",
        "launch_type": "browser_pwa",
        "requires_network": True,
        "requires_drm": True,
        "requires_hdcp_for_external_display": True,
        "offline_supported": False,
        "guardian_controlled": True,
        "school_mode_default": "blocked",
        "claim_status": "browser_route_prototype",
        "notes": (
            "Browser route prototype. DRM/CDM support required. HDCP may be required for "
            "external display. Service certification not claimed. No DRM circumvention."
        ),
    },
    "hulu": {
        "id": "hulu",
        "name": "Hulu",
        "category": "video_streaming",
        "route_url": "https://www.hulu.com/",
        "launch_type": "browser_pwa",
        "requires_network": True,
        "requires_drm": True,
        "requires_hdcp_for_external_display": True,
        "offline_supported": False,
        "guardian_controlled": True,
        "school_mode_default": "blocked",
        "claim_status": "browser_route_prototype",
        "notes": (
            "Browser route prototype. DRM/CDM support required. HDCP may be required for "
            "external display. Service certification not claimed. No DRM circumvention."
        ),
    },
    "local_media": {
        "id": "local_media",
        "name": "Local Media",
        "category": "local_media",
        "route_url": "gunnchos://local-media",
        "launch_type": "local_media",
        "requires_network": False,
        "requires_drm": False,
        "requires_hdcp_for_external_display": False,
        "offline_supported": True,
        "guardian_controlled": False,
        "school_mode_default": "allowed",
        "claim_status": "local_placeholder",
        "notes": "Local file playback placeholder. Offline supported where rights permit.",
    },
    "lecture_video": {
        "id": "lecture_video",
        "name": "Lecture Video",
        "category": "education_video",
        "route_url": "gunnchos://lecture-video",
        "launch_type": "local_media",
        "requires_network": False,
        "requires_drm": False,
        "requires_hdcp_for_external_display": False,
        "offline_supported": True,
        "guardian_controlled": False,
        "school_mode_default": "allowed",
        "claim_status": "local_placeholder",
        "notes": "School lecture and course video placeholder. Downloaded content where rights permit.",
    },
    "music_audio": {
        "id": "music_audio",
        "name": "Music & Audio",
        "category": "music_audio",
        "route_url": "gunnchos://music-audio",
        "launch_type": "future_placeholder",
        "requires_network": True,
        "requires_drm": False,
        "requires_hdcp_for_external_display": False,
        "offline_supported": False,
        "guardian_controlled": True,
        "school_mode_default": "policy_dependent",
        "claim_status": "future_placeholder",
        "notes": "Spotify, Apple Music, and local audio — future route. Service certification not claimed.",
    },
    "future_streaming_service": {
        "id": "future_streaming_service",
        "name": "More Streaming",
        "category": "video_streaming",
        "route_url": "",
        "launch_type": "future_placeholder",
        "requires_network": True,
        "requires_drm": True,
        "requires_hdcp_for_external_display": True,
        "offline_supported": False,
        "guardian_controlled": True,
        "school_mode_default": "blocked",
        "claim_status": "future_placeholder",
        "notes": (
            "Future: Disney+, Max, Prime Video, Peacock, Paramount+, Crunchyroll, Twitch. "
            "DRM/CDM and service certification required. Not available in Phase 1."
        ),
    },
}

DRM_DISCLAIMER = (
    "Playback quality depends on browser, hardware, network, codec, DRM, and service policy. "
    "DRM circumvention is not supported. Service certification not claimed."
)


def list_media_apps() -> list[str]:
    return sorted(MEDIA_APPS)


def get_media_app(service: str) -> dict[str, Any]:
    if service not in MEDIA_APPS:
        raise ValueError(f"Unknown media service: {service}")
    return dict(MEDIA_APPS[service])


def open_route(service: str) -> dict[str, Any]:
    app = get_media_app(service)
    return {
        "service": service,
        "url": app["route_url"],
        "launch_type": app["launch_type"],
        "requires_drm": app["requires_drm"],
        "requires_hdcp_for_external_display": app["requires_hdcp_for_external_display"],
        "claim_status": app["claim_status"],
        "drm_note": DRM_DISCLAIMER if app["requires_drm"] else (
            "Some content may require DRM. Service certification not claimed."
        ),
        "mock": app["claim_status"] != "browser_route_prototype" or service in ("netflix", "hulu"),
        "notes": app["notes"],
    }
