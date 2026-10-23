"""Keep the published RC1 tag identity distinct from the capsule APK source.

``v1.0.0-rc.1`` points at ``438aaf2``, which does not contain the Pixel
capsule APK. The checked-in APK bytes (sha256 ``8863d83a…``) are the
historical artifact at ``2218ead``. An earlier manifest recorded
``git_sha`` ``f460ac7`` after those bytes changed; that commit built a
different APK (sha256 ``218ce1cf…``). This module rejects either mix-up.
The tag is not moved.
"""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path
from typing import Any

PUBLISHED_TAG = "v1.0.0-rc.1"
PUBLISHED_TAG_COMMIT = "438aaf2b54d3365d681dd6eeeb73f6ac58663acc"
HISTORICAL_APK_SOURCE_COMMIT = "2218ead0efa0e4b8a622717a0a9bf623ee95ddb0"
HISTORICAL_APK_SHA256 = "8863d83acba11be6bb3ce7a5767499ac2031c564006aceb950f312d8376b5b9d"
SUPERSEDED_CAPSULE_COMMIT = "f460ac7b0e94c98060e7aeafc3ee82fb3c65237d"
SUPERSEDED_CAPSULE_APK_SHA256 = "218ce1cf9883f773234b6f94a8888e0cf14e45461e7f703d54d231a6b82dbf7f"
CAPSULE_APK_RELPATH = "artifacts/android_capsule/release/gunnchOS-Capsule-Pixel6a-pilot.apk"


class ApkSourceIdentityError(ValueError):
    """Raised when tag identity is treated as the APK source, or the stale git_sha is kept."""


def discrepancy_record() -> dict[str, Any]:
    return {
        "published_tag": PUBLISHED_TAG,
        "published_tag_commit": PUBLISHED_TAG_COMMIT,
        "apk_source_commit": HISTORICAL_APK_SOURCE_COMMIT,
        "apk_sha256": HISTORICAL_APK_SHA256,
        "tag_identity_matches_apk_source": False,
        "superseded_git_sha": SUPERSEDED_CAPSULE_COMMIT,
        "superseded_git_sha_apk_sha256": SUPERSEDED_CAPSULE_APK_SHA256,
        "signing": "debug_pilot",
        "physical_acceptance": False,
    }


def check_capsule_apk_identity(manifest: dict[str, Any]) -> dict[str, Any]:
    """Accept a manifest that records the historical split. Reject conflation."""
    errors: list[str] = []
    git_sha = str(manifest.get("git_sha") or "")
    apk_source = str(manifest.get("apk_source_commit") or "")
    tag_commit = str(manifest.get("published_tag_commit") or "")
    sha256 = str(manifest.get("sha256") or "")
    same_identity = bool(manifest.get("tag_identity_is_apk_source"))

    if (
        same_identity
        or git_sha == PUBLISHED_TAG_COMMIT
        or apk_source == PUBLISHED_TAG_COMMIT
        or (tag_commit and apk_source and tag_commit == apk_source)
    ):
        errors.append("published_tag_identity_conflated_with_apk_source")
    if manifest.get("published_tag") != PUBLISHED_TAG:
        errors.append("published_tag_mismatch")
    if tag_commit != PUBLISHED_TAG_COMMIT:
        errors.append("published_tag_commit_mismatch")
    if apk_source != HISTORICAL_APK_SOURCE_COMMIT or git_sha != HISTORICAL_APK_SOURCE_COMMIT:
        errors.append("apk_source_commit_mismatch")
    if sha256 != HISTORICAL_APK_SHA256:
        errors.append("apk_sha256_mismatch")
    if git_sha == SUPERSEDED_CAPSULE_COMMIT and sha256 == HISTORICAL_APK_SHA256:
        errors.append("superseded_capsule_commit_claimed_for_later_apk_bytes")
    if manifest.get("superseded_git_sha") != SUPERSEDED_CAPSULE_COMMIT:
        errors.append("superseded_git_sha_not_recorded")
    if manifest.get("superseded_git_sha_apk_sha256") != SUPERSEDED_CAPSULE_APK_SHA256:
        errors.append("superseded_apk_sha256_not_recorded")
    if manifest.get("signing") != "debug_pilot":
        errors.append("signing_claim_changed")
    if same_identity or manifest.get("tag_identity_is_apk_source") is not False:
        errors.append("tag_identity_is_apk_source_must_be_false")

    if errors:
        raise ApkSourceIdentityError(",".join(errors))

    report = discrepancy_record()
    report["ok"] = True
    return report


def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(repo), *args],
        check=False,
        capture_output=True,
        text=True,
    )


def _blob_sha256(repo: Path, rev_path: str) -> str | None:
    proc = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "blob", rev_path],
        check=False,
        capture_output=True,
    )
    if proc.returncode != 0:
        return None
    return hashlib.sha256(proc.stdout).hexdigest()


def verify_historical_commits(repo: Path) -> dict[str, Any]:
    """Read-only check that the recorded tag and APK source commits still differ."""
    repo = Path(repo)
    tag = _git(repo, "rev-parse", f"{PUBLISHED_TAG}^{{commit}}")
    tag_commit = tag.stdout.strip()
    if tag.returncode != 0 or tag_commit != PUBLISHED_TAG_COMMIT:
        raise ApkSourceIdentityError(f"published_tag_resolve_failed:{tag_commit}")

    tag_blob = _blob_sha256(repo, f"{PUBLISHED_TAG_COMMIT}:{CAPSULE_APK_RELPATH}")
    if tag_blob is not None:
        raise ApkSourceIdentityError("published_tag_commit_contains_apk")

    source_blob = _blob_sha256(repo, f"{HISTORICAL_APK_SOURCE_COMMIT}:{CAPSULE_APK_RELPATH}")
    if source_blob != HISTORICAL_APK_SHA256:
        raise ApkSourceIdentityError("historical_apk_source_bytes_mismatch")

    superseded_blob = _blob_sha256(repo, f"{SUPERSEDED_CAPSULE_COMMIT}:{CAPSULE_APK_RELPATH}")
    if superseded_blob != SUPERSEDED_CAPSULE_APK_SHA256:
        raise ApkSourceIdentityError("superseded_capsule_bytes_mismatch")
    if superseded_blob == source_blob:
        raise ApkSourceIdentityError("superseded_commit_bytes_match_historical_apk")

    report = discrepancy_record()
    report["historical_commits_verified"] = True
    report["published_tag_has_apk"] = False
    return report
