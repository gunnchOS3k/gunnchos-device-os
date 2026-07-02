"""Media mode policy and metadata tests."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from gunnchos_device_os.media_apps import (
    DRM_DISCLAIMER,
    MEDIA_APPS,
    get_media_app,
    list_media_apps,
    open_route,
)
from gunnchos_device_os.policy_engine import evaluate

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "apps" / "launcher_mock" / "src" / "generated" / "launcherContract.json"


def test_media_mode_allows_streaming_and_browser():
    for app in ("youtube", "netflix", "hulu", "browser", "local_media"):
        r = evaluate("student", "Media", app)
        assert r["allowed"] is True, f"{app} should be allowed in Media mode"


def test_media_mode_blocks_steam_and_vscode():
    assert evaluate("student", "Media", "steam")["allowed"] is False
    assert evaluate("student", "Media", "vscode")["allowed"] is False


def test_school_mode_blocks_netflix_hulu():
    assert evaluate("student", "School", "netflix")["allowed"] is False
    assert evaluate("student", "School", "hulu")["allowed"] is False


def test_offline_mode_blocks_streaming_allows_local_media():
    # admin profile can evaluate Offline mode policy
    assert evaluate("admin", "Offline", "netflix")["allowed"] is False
    assert evaluate("admin", "Offline", "hulu")["allowed"] is False
    assert evaluate("admin", "Offline", "youtube")["allowed"] is False
    assert evaluate("admin", "Offline", "local_media")["allowed"] is True
    assert evaluate("admin", "Offline", "lecture_video")["allowed"] is True


def test_guardian_mode_blocks_streaming():
    assert evaluate("student", "Guardian", "netflix")["allowed"] is False
    assert evaluate("student", "Guardian", "hulu")["allowed"] is False


def test_unknown_media_service_raises():
    with pytest.raises(ValueError, match="Unknown media service"):
        open_route("not_a_service")


def test_media_metadata_has_drm_hdcp_claim_fields():
    required = {
        "id", "name", "category", "route_url", "launch_type",
        "requires_network", "requires_drm", "requires_hdcp_for_external_display",
        "offline_supported", "guardian_controlled", "school_mode_default",
        "claim_status", "notes",
    }
    for app_id in list_media_apps():
        meta = get_media_app(app_id)
        assert required.issubset(meta.keys()), app_id
    netflix = get_media_app("netflix")
    assert netflix["requires_drm"] is True
    assert netflix["requires_hdcp_for_external_display"] is True
    assert netflix["claim_status"] == "browser_route_prototype"
    assert "circumvention" not in netflix["notes"].lower() or "no drm" in netflix["notes"].lower()


def test_open_route_includes_drm_notes():
    route = open_route("netflix")
    assert route["requires_drm"] is True
    assert "certification" in route["notes"].lower() or "certification" in route["drm_note"].lower()
    assert DRM_DISCLAIMER


def test_exported_launcher_contract_is_valid_json():
    assert CONTRACT.exists(), "Run scripts/export_launcher_contract.py first"
    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert data["version"]
    assert "youtube" in data["media_apps"]
    assert data["claim_boundary"]["drm_circumvention_supported"] is False
    assert data["claim_boundary"]["service_certification_claimed"] is False
    assert data["policy_samples"]["media_blocks_steam"] is True
    assert data["policy_samples"]["school_blocks_netflix"] is True
