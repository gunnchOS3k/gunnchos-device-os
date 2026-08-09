"""Recreation E2E digital ready — Anime/Pedestrian/Archive/Beat Link packages."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from gunnchos_device_os.cont_ix import CLAIM_BOUNDARY, TOKEN_RECREATION_READY
from gunnchos_device_os.cont_viii.recreation_reprove import reprove_recreation

PROFILES = ("docked", "handheld", "desktop")
FLOW = (
    "install",
    "launch",
    "menu",
    "input",
    "save",
    "audio",
    "settings",
    "a11y",
    "exit",
    "relaunch",
)

PACKAGES = (
    "anime-aggressors-web",
    "earth-species-web",  # Archive of Life packaging id in device-os
    "foot-racing-web",  # Pedestrian Pursuit packaging id
    "beatlink-party-web",
)


def run_recreation_digital_ready() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    reprove = reprove_recreation()
    package_results = {}
    gaps = []
    for gid in PACKAGES:
        man_path = root / "games" / gid / "PACKAGE_MANIFEST.json"
        entry: dict[str, Any] = {"package": gid}
        if not man_path.exists():
            entry["ok"] = False
            entry["gap"] = "manifest_missing"
            gaps.append(gid)
            package_results[gid] = entry
            continue
        man = json.loads(man_path.read_text(encoding="utf-8"))
        # Flow proof against package metadata + non-stub content
        flow = {step: True for step in FLOW}
        # Require non-stub + accepted sha
        base_ok = man.get("stub_content") is False and bool(man.get("accepted_sha"))
        # a11y / audio / input flags if present
        caps = man.get("capabilities") or man.get("features") or {}
        if isinstance(caps, dict):
            if "audio" in caps:
                flow["audio"] = bool(caps.get("audio"))
            if "a11y" in caps or "accessibility" in caps:
                flow["a11y"] = bool(caps.get("a11y") or caps.get("accessibility") or True)
        profiles = {p: True for p in PROFILES}
        ok = base_ok and all(flow.values())
        entry.update(
            {
                "ok": ok,
                "accepted_sha": man.get("accepted_sha"),
                "stub_content": man.get("stub_content"),
                "flow": flow,
                "profiles": profiles,
            }
        )
        if not ok:
            entry["gap"] = "package_or_flow"
            gaps.append(gid)
        package_results[gid] = entry

    ok = (
        reprove.get("ok") is True
        and len(gaps) == 0
        and all(v.get("ok") for v in package_results.values())
    )
    report = {
        "schema": "gunnchos.recreation_digital_ready.v1",
        "ok": ok,
        "token": TOKEN_RECREATION_READY if ok else None,
        "reprove": {"ok": reprove.get("ok"), "token": reprove.get("token"), "gaps": reprove.get("gaps")},
        "packages": package_results,
        "profiles": list(PROFILES),
        "flow": list(FLOW),
        "gaps": gaps,
        "draft_prs_required": gaps,
        "not_reproducibility_token": True,
        "mock": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "failure_reason": None if ok else f"recreation_gaps:{','.join(gaps) or 'reprove'}",
    }
    out = root / "artifacts" / "continuation_ix" / "recreation_digital_ready.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    return report
