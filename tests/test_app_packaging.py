"""Tests for first-party app/game packaging manifests."""
from __future__ import annotations

from gunnchos_device_os.app_packaging import (
    TOKEN_APP_PACKAGING_PASS,
    PackageManifestBuilder,
    build_and_validate_packaging,
)


def test_app_and_game_packaging_pass():
    report = build_and_validate_packaging()
    assert report["ok"] is True
    assert report["token"] == TOKEN_APP_PACKAGING_PASS
    assert report["production_keys_used"] is False
    assert len(report["apps"]) >= 2
    assert len(report["games"]) >= 4
    assert all(g["controller_first"] for g in report["games"])


def test_manifest_digests_stable():
    b = PackageManifestBuilder()
    a1 = b.build_app_manifest()
    a2 = b.build_app_manifest()
    assert a1["digest_sha256"] == a2["digest_sha256"]
    assert "production" in a1["claim_boundary"].lower() or "not production" in a1["claim_boundary"].lower()
