"""Versioned device profiles for gunnchDevice Lab."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

PROFILES_DIR = Path(__file__).resolve().parent
CATALOG = (
    "student_14_5",
    "dsxl_coder",
    "handheld_hybrid",
    "handheld_docked",
    "edge_io_rings",
    "full_ecosystem",
)


def list_profiles() -> list[str]:
    return list(CATALOG)


def load_profile(profile_id: str) -> dict[str, Any]:
    path = PROFILES_DIR / f"{profile_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"unknown profile: {profile_id}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("profile_id") != profile_id:
        raise ValueError(f"profile_id mismatch in {path}")
    if data.get("SILICON_EXACT_EMULATION") is not False:
        raise ValueError("SILICON_EXACT_EMULATION must be false")
    if data.get("BEHAVIORAL_DEVICE_PROFILE") is not True:
        raise ValueError("BEHAVIORAL_DEVICE_PROFILE must be true for v0.1")
    return data


def compare_profiles(a: str, b: str) -> dict[str, Any]:
    pa, pb = load_profile(a), load_profile(b)
    keys = sorted(set(pa) | set(pb))
    diffs = {}
    for k in keys:
        if pa.get(k) != pb.get(k):
            diffs[k] = {"a": pa.get(k), "b": pb.get(k)}
    return {
        "schema": "gunnchos.device_lab.profile_compare.v1",
        "a": a,
        "b": b,
        "diff_keys": sorted(diffs),
        "diffs": diffs,
    }
