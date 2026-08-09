"""API compatibility — current + previous supported versions."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import json

from gunnchos_device_os.cont_ix import CLAIM_BOUNDARY, TOKEN_API_COMPAT
from gunnchos_device_os.cont_viii.api_abi_policy import (
    ApiAbiNegotiator,
    CURRENT,
    DEPRECATED,
    MIN_SUPPORTED,
    SURFACES,
)


def evaluate_api_compat() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    nego = ApiAbiNegotiator()
    cases = []
    # current
    for surface, ver in CURRENT.items():
        r = nego.negotiate(surface, ver)
        cases.append({"case": "current", "surface": surface, "requested": ver, **r})
    # previous/deprecated accepted
    for surface, vers in DEPRECATED.items():
        for ver in vers:
            r = nego.negotiate(surface, ver)
            cases.append({"case": "deprecated", "surface": surface, "requested": ver, **r})
    # unsupported below floor
    unsupported = nego.negotiate("app_manifest", "0.0.1")
    cases.append({"case": "unsupported", "surface": "app_manifest", "requested": "0.0.1", **unsupported})
    # migration hint
    migration = {
        "from": "1.0.0",
        "to": CURRENT["app_manifest"],
        "surface": "app_manifest",
        "steps": ["update manifest schema", "re-run negotiate", "repackage"],
    }
    ok_current = all(c["ok"] for c in cases if c["case"] == "current")
    ok_depr = all(c["ok"] and c.get("compatibility") == "deprecated_accepted" for c in cases if c["case"] == "deprecated")
    ok_unsup = unsupported.get("ok") is False
    ok = ok_current and ok_depr and ok_unsup and set(SURFACES) == set(CURRENT)
    report = {
        "schema": "gunnchos.api_compat.v1",
        "ok": ok,
        "token": TOKEN_API_COMPAT if ok else None,
        "current": CURRENT,
        "deprecated": DEPRECATED,
        "min_supported": MIN_SUPPORTED,
        "cases": cases,
        "migration": migration,
        "mock": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "failure_reason": None if ok else "api_compat_negotiation_gap",
    }
    out = root / "artifacts" / "continuation_ix" / "api_compat.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    return report
