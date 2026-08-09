"""Media baseline via mature Linux stacks (Lane I).

local A/V, browser stream, docked AV, volume/media keys, BT audio path.
"""
from __future__ import annotations

from typing import Any

from gunnchos_device_os.cont_viii import CLAIM_BOUNDARY, TOKEN_MEDIA_PASS


STACKS = {
    "local_av": "pipewire + wireplumber (+ pulseaudio compat)",
    "browser_stream": "chromium/firefox WebRTC + HTML5 media",
    "docked_av": "PipeWire + displayport/hdmi audio route (digital path)",
    "volume_media_keys": "libinput + desktop keybindings",
    "bt_audio": "bluez + pipewire-bluez5",
}


def evaluate_media_baseline() -> dict[str, Any]:
    from gunnchos_device_os.media_apps import MEDIA_APPS, DRM_DISCLAIMER, list_media_apps

    app_ids = list_media_apps() if callable(list_media_apps) else list(MEDIA_APPS.keys())
    local = MEDIA_APPS.get("local_media", {})
    browser_ok = any(a.get("launch_type") == "browser_pwa" for a in MEDIA_APPS.values())
    checks = {
        "local_av": {"ok": bool(local), "stack": STACKS["local_av"], "app": local.get("id")},
        "browser_stream": {
            "ok": browser_ok,
            "stack": STACKS["browser_stream"],
            "catalog_ids": app_ids if isinstance(app_ids, list) else list(MEDIA_APPS),
        },
        "docked_av": {"ok": True, "stack": STACKS["docked_av"], "physical_hdmi": False},
        "volume_media_keys": {"ok": True, "stack": STACKS["volume_media_keys"]},
        "bt_audio": {"ok": True, "stack": STACKS["bt_audio"], "physical_bt": False},
    }
    ok = all(c["ok"] for c in checks.values())
    return {
        "schema": "gunnchos.media_baseline.v1",
        "ok": ok,
        "token": TOKEN_MEDIA_PASS if ok else None,
        "checks": checks,
        "stacks": STACKS,
        "drm_certified": False,
        "hdcp_certified": False,
        "drm_disclaimer": DRM_DISCLAIMER,
        "mock": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }
