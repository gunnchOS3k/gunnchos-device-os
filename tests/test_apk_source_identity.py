"""Regression: published tag identity must not be reused as the capsule APK source."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from gunnchos_device_os.release_engineering.apk_source_identity import (
    HISTORICAL_APK_SHA256,
    HISTORICAL_APK_SOURCE_COMMIT,
    PUBLISHED_TAG_COMMIT,
    SUPERSEDED_CAPSULE_COMMIT,
    ApkSourceIdentityError,
    check_capsule_apk_identity,
    verify_historical_commits,
)

REPO = Path(__file__).resolve().parents[1]
MANIFEST_PATH = REPO / "artifacts/android_capsule/release/BUILD_MANIFEST.json"
APK_PATH = REPO / "artifacts/android_capsule/release/gunnchOS-Capsule-Pixel6a-pilot.apk"


def test_published_tag_is_not_the_capsule_apk_source() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    report = check_capsule_apk_identity(manifest)

    assert report["tag_identity_matches_apk_source"] is False
    assert report["published_tag_commit"] == PUBLISHED_TAG_COMMIT
    assert report["apk_source_commit"] == HISTORICAL_APK_SOURCE_COMMIT
    assert report["published_tag_commit"] != report["apk_source_commit"]
    assert hashlib.sha256(APK_PATH.read_bytes()).hexdigest() == manifest["sha256"] == HISTORICAL_APK_SHA256

    history = verify_historical_commits(REPO)
    assert history["historical_commits_verified"] is True
    assert history["published_tag_has_apk"] is False

    conflated = dict(manifest)
    conflated["git_sha"] = PUBLISHED_TAG_COMMIT
    conflated["apk_source_commit"] = PUBLISHED_TAG_COMMIT
    conflated["tag_identity_is_apk_source"] = True
    with pytest.raises(ApkSourceIdentityError, match="published_tag_identity_conflated_with_apk_source"):
        check_capsule_apk_identity(conflated)

    stale = dict(manifest)
    stale["git_sha"] = SUPERSEDED_CAPSULE_COMMIT
    with pytest.raises(ApkSourceIdentityError, match="apk_source_commit_mismatch"):
        check_capsule_apk_identity(stale)
