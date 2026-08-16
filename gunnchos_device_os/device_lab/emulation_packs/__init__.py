"""Reusable Device Lab emulation packs (Stream A A3)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gunnchos_device_os.device_lab.profiles import CATALOG, load_profile
from gunnchos_device_os.device_lab.scenarios.catalog import JOURNEY_SCENARIO_MAP, SCENARIO_CATALOG

PACKS_DIR = Path(__file__).resolve().parent
DEFAULT_PACK = "STREAM_A_REUSABLE_LAB_PACK_001.json"


def load_pack(name: str = DEFAULT_PACK) -> dict[str, Any]:
    path = PACKS_DIR / name
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("SILICON_EXACT_EMULATION") is not False:
        raise ValueError("SILICON_EXACT_EMULATION must be false")
    return data


def validate_pack(name: str = DEFAULT_PACK) -> dict[str, Any]:
    pack = load_pack(name)
    missing_profiles: list[str] = []
    silicon_violations: list[str] = []
    for entry in pack.get("profiles") or []:
        pid = entry["profile_id"]
        if pid not in CATALOG:
            missing_profiles.append(pid)
            continue
        profile = load_profile(pid)
        if profile.get("SILICON_EXACT_EMULATION") is not False:
            silicon_violations.append(pid)

    missing_modules: list[str] = []
    scenarios_root = Path(__file__).resolve().parents[1] / "scenarios"
    for mod in pack.get("scenario_modules") or []:
        if not (scenarios_root / f"{mod}.py").exists():
            missing_modules.append(mod)

    journey_coverage = sorted(JOURNEY_SCENARIO_MAP)
    ok = not missing_profiles and not silicon_violations and not missing_modules
    return {
        "ok": ok,
        "pack_id": pack.get("pack_id"),
        "SILICON_EXACT_EMULATION": False,
        "missing_profiles": missing_profiles,
        "silicon_violations": silicon_violations,
        "missing_scenario_modules": missing_modules,
        "scenario_catalog_size": len(SCENARIO_CATALOG),
        "journey_coverage": journey_coverage,
        "profile_count": len(pack.get("profiles") or []),
        "claim_boundary": pack.get("claim_boundary"),
    }
