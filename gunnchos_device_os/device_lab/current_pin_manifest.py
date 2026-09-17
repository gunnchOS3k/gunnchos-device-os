"""Current-pin ACCEPTED_MAIN_PIN_MANIFEST authority helpers.

Device Lab re-earn must bind package builds and lifecycle evidence to the
frozen pin manifest — not stale hardcoded ACCEPTED_MAINS tables.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

FOUR_GAME_REPOS = (
    "anime-aggressors",
    "pedestrian-pursuit",
    "archive-of-life-artifact-world",
    "beatlink-party",
)

LIFECYCLE_PRODUCTS = (
    "anime-aggressors",
    "pedestrian-pursuit",
    "archive-of-life-artifact-world",
    "beatlink-party",
    "gunnchos-waike-learning-platform",
    "gunnchAI3k",
    "gunnchos-device-os",
)

LIFECYCLE_STEPS = (
    "clean_launch",
    "first_run",
    "save_persist",
    "restart",
    "restore",
    "suspend_resume",
    "offline",
    "reconnect",
    "sync",
    "failure_recovery",
    "reinstall_reset",
    "crash_fatal_scan",
)

DEFAULT_MANIFEST_REL = Path("artifacts/device_lab_current_pin/ACCEPTED_MAIN_PIN_MANIFEST.json")
DEFAULT_SHA_REL = Path("artifacts/device_lab_current_pin/ACCEPTED_MAIN_PIN_MANIFEST.sha256")


class PinManifestError(ValueError):
    """Fail-closed pin authority error."""


def pin_manifest_path(repo_root: Path) -> Path:
    return repo_root / DEFAULT_MANIFEST_REL


def pin_sha256_path(repo_root: Path) -> Path:
    return repo_root / DEFAULT_SHA_REL


def canonical_manifest_payload(doc: dict[str, Any]) -> bytes:
    payload = {k: v for k, v in doc.items() if k != "manifest_sha256"}
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def compute_manifest_sha256(doc: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_manifest_payload(doc)).hexdigest()


def load_pin_manifest(repo_root: Path, *, require_sha_file: bool = True) -> dict[str, Any]:
    path = pin_manifest_path(repo_root)
    if not path.is_file():
        raise PinManifestError(f"pin_manifest_missing:{path}")
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PinManifestError(f"pin_manifest_invalid_json:{exc}") from exc
    if doc.get("schema") != "gunnchos.device_lab.current_pin_manifest.v1":
        raise PinManifestError(f"pin_manifest_bad_schema:{doc.get('schema')}")
    computed = compute_manifest_sha256(doc)
    declared = str(doc.get("manifest_sha256") or "")
    if not declared:
        raise PinManifestError("pin_manifest_sha256_missing")
    if computed != declared:
        raise PinManifestError(
            f"pin_manifest_sha256_mismatch:declared={declared}:computed={computed}"
        )
    if require_sha_file:
        sha_path = pin_sha256_path(repo_root)
        if not sha_path.is_file():
            raise PinManifestError(f"pin_sha256_file_missing:{sha_path}")
        file_sha = sha_path.read_text(encoding="utf-8").strip().split()[0]
        if file_sha != declared:
            raise PinManifestError(
                f"pin_sha256_file_mismatch:file={file_sha}:declared={declared}"
            )
    return doc


def pin_index(doc: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for row in doc.get("pins") or []:
        name = row.get("repository")
        if name:
            out[str(name)] = row
    return out


def pin_sha_for(doc: dict[str, Any], repository: str) -> str:
    row = pin_index(doc).get(repository)
    if not row or not row.get("sha"):
        raise PinManifestError(f"pin_sha_missing:{repository}")
    return str(row["sha"])


def four_game_pin_shas(doc: dict[str, Any]) -> dict[str, str]:
    return {name: pin_sha_for(doc, name) for name in FOUR_GAME_REPOS}


def require_build_sha_matches_pin(
    *,
    repository: str,
    build_sha: str,
    pin_sha: str,
) -> None:
    if not build_sha or not pin_sha or build_sha != pin_sha:
        raise PinManifestError(
            f"build_sha_mismatch:{repository}:build={build_sha}:pin={pin_sha}"
        )


def overlay_accepted_mains_from_pin(
    accepted_mains: dict[str, dict[str, str]],
    doc: dict[str, Any],
    *,
    reject_stale_hardcoded: bool = True,
) -> dict[str, Any]:
    """Rewrite four-game accepted_main_sha fields from pin manifest authority.

    Returns a report. Mutates accepted_mains in place.
    """
    pins = four_game_pin_shas(doc)
    report: dict[str, Any] = {
        "ok": True,
        "pin_manifest_sha256": doc.get("manifest_sha256"),
        "games": {},
        "stale_hardcoded_rejected": [],
    }
    for key, pin_sha in pins.items():
        if key not in accepted_mains:
            report["ok"] = False
            report["games"][key] = {"ok": False, "error": "accepted_mains_key_missing"}
            continue
        prior = accepted_mains[key].get("accepted_main_sha")
        stale = bool(prior and prior != pin_sha)
        if stale and reject_stale_hardcoded:
            report["stale_hardcoded_rejected"].append(
                {"repository": key, "hardcoded": prior, "pin": pin_sha}
            )
        accepted_mains[key]["accepted_main_sha"] = pin_sha
        accepted_mains[key]["pin_authority"] = "ACCEPTED_MAIN_PIN_MANIFEST"
        report["games"][key] = {
            "ok": True,
            "prior_hardcoded_sha": prior,
            "pin_sha": pin_sha,
            "overlaid": True,
            "stale_hardcoded": stale,
        }
    return report
