"""Re-prove recreation readiness against accepted mains (support lane).

Only reports gaps — does not invent physical/store readiness.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from gunnchos_device_os.cont_viii import CLAIM_BOUNDARY, TOKEN_RECREATION_REPROVE_PASS

# Accepted Cont VII packaging SHAs recorded in device-os game manifests / sibling mains
GAMES = {
    "anime-aggressors": {
        "token": "ANIME_DIGITAL_RC_READY",
        "evidence": "playtest-evidence/digital_rc_validation.json",
        "token_key": "token_earned",
    },
    "pedestrian-pursuit": {
        "token": "PEDESTRIAN_DIGITAL_RC_READY",
        "evidence": "gate1/evidence/out/pp_digital_rc_packaging.json",
        "token_key": "token_earned",
    },
    "archive-of-life-artifact-world": {
        "token": "ARCHIVE_DIGITAL_RC_READY",
        "evidence": "public/data/status/digital_rc_report.json",
        "status_key": "statusToken",
    },
    "beatlink-party": {
        "token": "BEATLINK_DIGITAL_RC_READY",
        "evidence": "docs/BETA_RC_TOKENS.json",
        "tokens_map": True,
    },
}


def _repos_root() -> Path:
    return Path(__file__).resolve().parents[3]


def reprove_recreation(*, repos_root: Path | None = None) -> dict[str, Any]:
    root = repos_root or _repos_root()
    results = {}
    gaps = []
    for name, spec in GAMES.items():
        repo = root / name
        entry: dict[str, Any] = {"repo": name, "present": repo.exists()}
        if not repo.exists():
            entry["ok"] = False
            entry["gap"] = "repo_missing"
            gaps.append(name)
            results[name] = entry
            continue
        evidence = repo / spec["evidence"]
        entry["evidence"] = str(evidence.relative_to(repo)) if evidence.exists() else None
        if not evidence.exists():
            entry["ok"] = False
            entry["gap"] = "evidence_missing"
            gaps.append(name)
            results[name] = entry
            continue
        data = json.loads(evidence.read_text(encoding="utf-8"))
        if spec.get("tokens_map"):
            earned = bool(data.get("tokens", {}).get(spec["token"]))
        elif "status_key" in spec:
            earned = data.get(spec["status_key"]) == spec["token"]
        else:
            earned = bool(data.get(spec["token_key"])) and (
                data.get("token") in (None, spec["token"]) or data.get("token") == spec["token"]
            )
            if "token" in data and data["token"] != spec["token"] and not data.get(spec["token_key"]):
                earned = False
            if data.get("token") == spec["token"] and data.get(spec["token_key"]) is True:
                earned = True
            if data.get(spec["token_key"]) is True and data.get("tokens", {}).get(spec["token"], True):
                # pedestrian style
                if "tokens" in data:
                    earned = bool(data["tokens"].get(spec["token"], data.get(spec["token_key"])))
                else:
                    earned = True
        entry["token"] = spec["token"]
        entry["earned"] = earned
        entry["ok"] = earned
        if not earned:
            entry["gap"] = "token_not_earned"
            gaps.append(name)
        results[name] = entry

    # Also confirm device-os packaged manifests exist + non-stub
    dos = Path(__file__).resolve().parents[2]
    packaged = {}
    for gid in ("anime-aggressors-web", "earth-species-web", "foot-racing-web", "beatlink-party-web"):
        man = dos / f"games/{gid}/PACKAGE_MANIFEST.json"
        if man.exists():
            data = json.loads(man.read_text(encoding="utf-8"))
            packaged[gid] = {
                "ok": data.get("stub_content") is False and bool(data.get("accepted_sha")),
                "accepted_sha": data.get("accepted_sha"),
                "stub_content": data.get("stub_content"),
            }
        else:
            packaged[gid] = {"ok": False, "gap": "manifest_missing"}
            gaps.append(gid)

    ok = len(gaps) == 0 and all(r.get("ok") for r in results.values()) and all(
        p.get("ok") for p in packaged.values()
    )
    return {
        "schema": "gunnchos.recreation_reprove.v1",
        "ok": ok,
        "token": TOKEN_RECREATION_REPROVE_PASS if ok else None,
        "games": results,
        "device_os_packages": packaged,
        "gaps": gaps,
        "draft_prs_required": gaps,
        "mock": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }
