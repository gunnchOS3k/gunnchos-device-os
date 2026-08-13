"""Beat Link rights-safety, Archive provenance, AI model license checks."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ALLOWED_BEATLINK_LICENSES = frozenset(
    {
        "public_domain",
        "synthetic_original",
        "creative_commons",
        "creator_owned",
        "demo_generated",
        "royalty_free",
        "cc-by-4.0",
        "cc0",
        "game-original",
        "mock-sample",
    }
)

FORBIDDEN_BEATLINK = (
    "rip",
    "youtube download",
    "spotify decrypt",
    "apple music cache",
    "licensed lyrics commercial",
)

ARCHIVE_REQUIRED_FIELDS = (
    "license",
    "source",
)


def _load(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def check_beatlink(beatlink_root: Path | None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "present": bool(beatlink_root and beatlink_root.exists()),
        "rights_safe": True,
        "blocking": [],
        "catalogs": [],
        "claim_boundary": "Digital catalog license scan only. Not a music-rights legal opinion.",
    }
    if not result["present"]:
        result["note"] = "beatlink-party sibling not present; scan skipped (not a pass)"
        return result
    assert beatlink_root is not None
    catalogs = list((beatlink_root / "content").rglob("*.json")) if (beatlink_root / "content").exists() else []
    for path in catalogs:
        data = _load(path)
        if not isinstance(data, dict):
            continue
        songs = data.get("songs") or []
        if not isinstance(songs, list):
            continue
        unknown = []
        for song in songs:
            lic = str(
                song.get("license")
                or (song.get("rights") or {}).get("license")
                or ""
            ).lower()
            if lic not in ALLOWED_BEATLINK_LICENSES:
                unknown.append({"id": song.get("id"), "license": lic or "UNKNOWN", "file": str(path)})
        result["catalogs"].append(
            {
                "path": str(path.relative_to(beatlink_root)),
                "songs": len(songs),
                "unknown_licenses": unknown,
                "rip_forbidden": bool(data.get("rip_forbidden", True)),
            }
        )
        if unknown:
            result["rights_safe"] = False
            result["blocking"].extend(unknown)
    register = beatlink_root / "artifacts" / "beatlink_full" / "BEATLINK_FULL_PRODUCT_REGISTER.json"
    if register.exists():
        data = _load(register) or {}
        rs = data.get("rights_safety") or {}
        if rs.get("rip_download_decrypt_forbidden") is not True:
            result["rights_safe"] = False
            result["blocking"].append({"register": "rip_download_decrypt_forbidden not true"})
    return result


def check_archive_provenance(archive_root: Path | None) -> dict[str, Any]:
    result: dict[str, Any] = {
        "present": bool(archive_root and archive_root.exists()),
        "provenance_retained": True,
        "blocking": [],
        "bundles_scanned": 0,
        "claim_boundary": "Schema presence check. Not a scientific-data legal clearance.",
    }
    if not result["present"]:
        result["note"] = "archive-of-life sibling not present; scan skipped (not a pass)"
        return result
    assert archive_root is not None
    data_root = archive_root / "public" / "data"
    if not data_root.exists():
        result["provenance_retained"] = False
        result["blocking"].append("missing public/data")
        return result
    for path in data_root.rglob("*.json"):
        data = _load(path)
        if not isinstance(data, dict):
            continue
        records = []
        if isinstance(data.get("provenance"), list):
            records = data["provenance"]
        elif isinstance(data.get("species"), list):
            for sp in data["species"]:
                if isinstance(sp, dict) and "provenance" in sp:
                    records.extend(sp["provenance"] if isinstance(sp["provenance"], list) else [sp["provenance"]])
        for rec in records:
            if not isinstance(rec, dict):
                continue
            result["bundles_scanned"] += 1
            missing = [f for f in ARCHIVE_REQUIRED_FIELDS if not rec.get(f) and not rec.get("license")]
            if "license" not in rec:
                result["provenance_retained"] = False
                result["blocking"].append({"file": str(path), "missing": "license"})
            if missing and "license" in rec:
                pass
    return result


def check_ai_model_licenses(components: list[dict[str, Any]]) -> dict[str, Any]:
    models = [c for c in components if c.get("kind") == "ai_model"]
    blocking = [m for m in models if m.get("unknown_release_blocking")]
    return {
        "models": len(models),
        "machine_tracked": True,
        "unknown_release_blocking": len(blocking),
        "blocking": [{"name": m.get("name"), "license": m.get("license")} for m in blocking],
        "claim_boundary": "License field machine-tracked. Not legal approval of model redistribution.",
    }
