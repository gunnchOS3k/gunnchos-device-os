#!/usr/bin/env python3
"""Validate streaming_certification/SERVICE_CERTIFICATION_TRACKER.yaml."""
from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

ROOT = Path(__file__).resolve().parents[1]
TRACKER = ROOT / "streaming_certification" / "SERVICE_CERTIFICATION_TRACKER.yaml"
REQUIRED_SERVICE_FIELDS = (
    "display_name",
    "launch_route",
    "browser_requirement",
    "drm_cdm_required",
    "hdcp_external_display_required",
    "tested_browser",
    "tested_os_image",
    "tested_hardware",
    "max_confirmed_resolution",
    "audio_captions_status",
    "login_session_notes",
    "certification_status",
    "evidence_path",
    "claim_boundary",
)
ALLOWED_CERT_STATUS = {
    "not_started",
    "browser_route_prototype",
    "readiness_prototype",
    "tested_unverified",
    "certified",
}
REQUIRED_SERVICES = {
    "youtube",
    "netflix",
    "hulu",
    "disney_plus",
    "max",
    "prime_video",
    "peacock",
    "paramount_plus",
    "crunchyroll",
    "twitch",
    "local_media",
}
FORBIDDEN_PHRASES = (
    "drm circumvention",
    "bypass drm",
    "crack widevine",
    "strip hdcp",
)


def main() -> int:
    if yaml is None:
        print("PyYAML required: pip install pyyaml")
        return 1
    if not TRACKER.exists():
        print(f"Missing {TRACKER}")
        return 1

    data = yaml.safe_load(TRACKER.read_text(encoding="utf-8"))
    errors: list[str] = []
    raw_text = TRACKER.read_text(encoding="utf-8").lower()

    for phrase in FORBIDDEN_PHRASES:
        if phrase in raw_text and "not supported" not in raw_text:
            # allow "DRM circumvention is not supported" style negation at doc level
            if phrase == "drm circumvention" and "not supported" in raw_text:
                continue
            errors.append(f"Forbidden phrase in tracker: {phrase!r}")

    services = data.get("services")
    if not isinstance(services, dict):
        errors.append("Missing services map")
        return report(errors)

    missing = REQUIRED_SERVICES - set(services)
    if missing:
        errors.append(f"Missing required services: {sorted(missing)}")

    for service_id, entry in services.items():
        if not isinstance(entry, dict):
            errors.append(f"{service_id}: entry must be a map")
            continue
        for field in REQUIRED_SERVICE_FIELDS:
            if field not in entry:
                errors.append(f"{service_id}: missing field {field}")

        status = entry.get("certification_status")
        if status not in ALLOWED_CERT_STATUS:
            errors.append(f"{service_id}: invalid certification_status {status!r}")

        evidence = entry.get("evidence_path")
        if status == "certified":
            if not evidence:
                errors.append(f"{service_id}: certified requires evidence_path")
            elif not (ROOT / evidence).exists():
                errors.append(f"{service_id}: evidence_path does not exist: {evidence}")

        claim = str(entry.get("claim_boundary", "")).lower()
        for phrase in FORBIDDEN_PHRASES:
            if phrase in claim and "not" not in claim:
                errors.append(f"{service_id}: claim_boundary contains forbidden phrase {phrase!r}")

        if service_id == "local_media" and entry.get("drm_cdm_required") is True:
            errors.append("local_media must remain separate from DRM streaming (drm_cdm_required=false)")

    for doc_name in (
        "STREAMING_COMPATIBILITY_MATRIX.md",
        "CDM_READINESS_CHECKLIST.md",
        "HDCP_EXTERNAL_DISPLAY_CHECKLIST.md",
    ):
        if not (ROOT / "streaming_certification" / doc_name).exists():
            errors.append(f"Missing streaming_certification/{doc_name}")

    return report(errors)


def report(errors: list[str]) -> int:
    if errors:
        for e in errors:
            print(f"ERROR: {e}")
        return 1
    print("SERVICE_CERTIFICATION_TRACKER.yaml is valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
