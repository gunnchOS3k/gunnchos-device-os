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
# SHA-256 of the single v2 signer certificate inside the checked-in APK.
# Subject and issuer are CN=Android Debug, O=Android, C=US. Not a production key.
DEBUG_PILOT_CERT_SHA256 = "b637ea5f982aa1d3027e346fbfe9f672fdc5dee95407b1608b50b6f1631bd59a"
DEBUG_PILOT_CERT_CN = "Android Debug"
_APK_SIG_MAGIC = b"APK Sig Block 42"
_V2_BLOCK_ID = 0x7109871A
_EOCD_SIG = b"PK\x05\x06"


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
        "debug_pilot_cert_sha256": DEBUG_PILOT_CERT_SHA256,
        "debug_pilot_cert_cn": DEBUG_PILOT_CERT_CN,
        "physical_acceptance": False,
    }


def _u32_prefixed(buf: bytes, offset: int) -> tuple[bytes, int]:
    if offset + 4 > len(buf):
        raise ApkSourceIdentityError("apk_signing_block_truncated")
    length = int.from_bytes(buf[offset : offset + 4], "little")
    offset += 4
    end = offset + length
    if length < 0 or end > len(buf):
        raise ApkSourceIdentityError("apk_signing_block_truncated")
    return buf[offset:end], end


def _signing_block_pairs(apk: bytes) -> list[tuple[int, bytes]]:
    eocd = apk.rfind(_EOCD_SIG)
    if eocd < 0 or eocd + 22 > len(apk):
        raise ApkSourceIdentityError("apk_eocd_missing")
    central_dir = int.from_bytes(apk[eocd + 16 : eocd + 20], "little")
    if central_dir < 32 or central_dir > len(apk) or apk[central_dir - 16 : central_dir] != _APK_SIG_MAGIC:
        raise ApkSourceIdentityError("apk_signing_block_missing")
    size = int.from_bytes(apk[central_dir - 24 : central_dir - 16], "little")
    start = central_dir - (size + 8)
    if start < 0 or int.from_bytes(apk[start : start + 8], "little") != size:
        raise ApkSourceIdentityError("apk_signing_block_size_mismatch")
    pairs = apk[start + 8 : central_dir - 24]
    offset = 0
    found: list[tuple[int, bytes]] = []
    while offset < len(pairs):
        if offset + 12 > len(pairs):
            raise ApkSourceIdentityError("apk_signing_block_truncated")
        pair_len = int.from_bytes(pairs[offset : offset + 8], "little")
        ident = int.from_bytes(pairs[offset + 8 : offset + 12], "little")
        value_end = offset + 8 + pair_len
        if pair_len < 4 or value_end > len(pairs):
            raise ApkSourceIdentityError("apk_signing_block_truncated")
        found.append((ident, pairs[offset + 12 : value_end]))
        offset = value_end
    return found


def v2_signer_certificates(apk: bytes) -> list[bytes]:
    """Return DER certificates from the APK Signature Scheme v2 block."""
    value = next((blob for ident, blob in _signing_block_pairs(apk) if ident == _V2_BLOCK_ID), None)
    if value is None:
        raise ApkSourceIdentityError("apk_v2_signer_missing")
    signers, _ = _u32_prefixed(value, 0)
    certificates: list[bytes] = []
    offset = 0
    while offset < len(signers):
        signer, offset = _u32_prefixed(signers, offset)
        signed, _ = _u32_prefixed(signer, 0)
        _digests, signed_offset = _u32_prefixed(signed, 0)
        cert_seq, _ = _u32_prefixed(signed, signed_offset)
        cert_offset = 0
        while cert_offset < len(cert_seq):
            cert, cert_offset = _u32_prefixed(cert_seq, cert_offset)
            if not cert.startswith(b"\x30"):
                raise ApkSourceIdentityError("signer_cert_not_der")
            certificates.append(cert)
    if not certificates:
        raise ApkSourceIdentityError("apk_v2_signer_cert_missing")
    return certificates


def debug_pilot_cert_sha256(apk: bytes) -> str:
    """SHA-256 fingerprint of the single debug-pilot v2 signer certificate."""
    certificates = v2_signer_certificates(apk)
    if len(certificates) != 1:
        raise ApkSourceIdentityError("apk_v2_signer_cert_count")
    cert = certificates[0]
    if cert.count(DEBUG_PILOT_CERT_CN.encode("ascii")) != 2:
        raise ApkSourceIdentityError("debug_pilot_cert_cn_mismatch")
    return hashlib.sha256(cert).hexdigest()


def check_capsule_apk_identity(manifest: dict[str, Any], apk_bytes: bytes | None = None) -> dict[str, Any]:
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
    if manifest.get("debug_pilot_cert_sha256") != DEBUG_PILOT_CERT_SHA256:
        errors.append("debug_pilot_cert_sha256_mismatch")
    if manifest.get("debug_pilot_cert_cn") != DEBUG_PILOT_CERT_CN:
        errors.append("debug_pilot_cert_cn_mismatch")
    if apk_bytes is not None:
        try:
            derived = debug_pilot_cert_sha256(apk_bytes)
        except ApkSourceIdentityError as exc:
            errors.append(str(exc))
            derived = ""
        if derived != DEBUG_PILOT_CERT_SHA256:
            errors.append("debug_pilot_cert_bytes_mismatch")
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
