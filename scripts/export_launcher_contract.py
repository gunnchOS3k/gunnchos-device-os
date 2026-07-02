#!/usr/bin/env python3
"""Export Python policy/app data for the React launcher shell."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.app_registry import APPS, CATEGORIES, list_apps  # noqa: E402
from gunnchos_device_os.media_apps import DRM_DISCLAIMER, MEDIA_APPS, list_media_apps  # noqa: E402
from gunnchos_device_os.mode_manager import list_modes, get_mode_policy  # noqa: E402
from gunnchos_device_os.policy_engine import evaluate  # noqa: E402

OUT = ROOT / "apps" / "launcher_mock" / "src" / "generated" / "launcherContract.json"


def build_contract() -> dict:
    modes = {}
    for mode in list_modes():
        pol = get_mode_policy(mode)
        modes[mode] = {
            "allowed_apps": pol.get("allowed_apps", []),
            "blocked_apps": pol.get("blocked_apps", []),
            "media_mode": bool(pol.get("media_mode")),
            "streaming_priority": bool(pol.get("streaming_priority")),
            "library_login_warning": bool(pol.get("library_login_warning")),
            "no_saved_passwords_default": bool(pol.get("no_saved_passwords_default")),
        }

    return {
        "version": "1.1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "claim_boundary": {
            "drm_circumvention_supported": False,
            "service_certification_claimed": False,
            "drm_disclaimer": DRM_DISCLAIMER,
            "workspace_storage": "browser_local_storage_prototype",
        },
        "apps": APPS,
        "categories": list(CATEGORIES),
        "campus_native_apps": ["files", "notes", "browser", "settings", "game-mode", "media-mode"],
        "media_apps": MEDIA_APPS,
        "media_app_ids": list_media_apps(),
        "modes": modes,
        "policy_samples": {
            "media_allows_youtube": evaluate("student", "Media", "youtube")["allowed"],
            "media_blocks_steam": not evaluate("student", "Media", "steam")["allowed"],
            "school_blocks_netflix": not evaluate("student", "School", "netflix")["allowed"],
            "offline_blocks_netflix": not evaluate("admin", "Offline", "netflix")["allowed"],
            "offline_allows_local_media": evaluate("admin", "Offline", "local_media")["allowed"],
        },
    }


def main() -> int:
    contract = build_contract()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} ({len(json.dumps(contract))} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
