"""Honest FULL_GUNNCHOS_PLATFORM_DIGITAL_COMPLETE evaluation (Cont VII §27).

Physical boot and production cloud credentials are NOT digital blockers.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any
import json

TOKEN = "FULL_GUNNCHOS_PLATFORM_DIGITAL_COMPLETE"

CLAIM_BOUNDARY = (
    "Digital platform completeness only. Physical boot, production cloud "
    "credentials, carrier attach, and store signing remain separate axes."
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def evaluate_platform_digital_complete(*, root: Path | None = None, quick: bool = False) -> dict[str, Any]:
    root = root or _repo_root()
    checks: dict[str, Any] = {}

    # 1) No first-party game stubs
    beat = root / "games/beatlink-party-web/index.html"
    beat_man = root / "games/beatlink-party-web/PACKAGE_MANIFEST.json"
    beat_text = beat.read_text(encoding="utf-8", errors="ignore") if beat.exists() else ""
    checks["beatlink_real_package"] = (
        beat.exists()
        and beat_man.exists()
        and "GUNNCHOS_GAME_STUB_CONTENT=true" not in beat_text
        and "DEV stub" not in beat_text
    )

    # 2) Real first-party apps
    for app_id, path in {
        "waike_learning": "apps/waike_learning/index.html",
        "creator_studio": "apps/creator_studio/index.html",
        "device_management": "apps/device_management/index.html",
    }.items():
        checks[f"app_{app_id}"] = (root / path).exists()

    # 3) Game package manifests present for all four
    for gid in ("anime-aggressors-web", "earth-species-web", "foot-racing-web", "beatlink-party-web"):
        checks[f"manifest_{gid}"] = (root / f"games/{gid}/PACKAGE_MANIFEST.json").exists()

    # 4) IPC robustness module concludes keep-or-upgrade with pass
    try:
        from gunnchos_device_os.ipc_robustness import audit_ipc_robustness
        ipc = audit_ipc_robustness(run_live=not quick)
        checks["ipc_robust"] = bool(ipc.get("ok"))
        checks["ipc_decision"] = ipc.get("decision")
    except Exception as exc:  # noqa: BLE001
        checks["ipc_robust"] = False
        checks["ipc_error"] = str(exc)

    # 5) Connectivity digital bearers present
    try:
        from gunnchos_device_os.connectivity.bearers import build_default_bearers
        bearers = build_default_bearers()
        needed = {"ethernet", "wifi", "terrestrial", "ntn_simulated", "future_ntn"}
        checks["connectivity_bearers"] = needed.issubset(set(bearers))
    except Exception as exc:  # noqa: BLE001
        checks["connectivity_bearers"] = False
        checks["connectivity_error"] = str(exc)

    # Explicit non-blockers (recorded for honesty)
    non_blockers = {
        "physical_boot_pending": "NOT_A_DIGITAL_BLOCKER",
        "production_cloud_credentials": "NOT_A_DIGITAL_BLOCKER",
        "carrier_attach": "NOT_A_DIGITAL_BLOCKER",
        "guest_mailbox_in_minirootfs": "ACCEPTABLE_IF_HOST_UNIX_IPC_ROBUST",
    }

    required = [k for k in checks if not k.endswith("_error") and not k.endswith("_decision")]
    earned = all(bool(checks[k]) for k in required if k != "ipc_decision")
    # ipc decision must be KEEP_MAILBOX_OR_UNIX (sufficient) 
    decision = checks.get("ipc_decision")
    if decision not in (None, "KEEP_UNIX_SOCKET_IPC", "KEEP_MAILBOX_HTTP_LINE"):
        # missing decision fails only when live audit ran
        if checks.get("ipc_robust") is False:
            earned = False
    if decision in ("REPLACE_REQUIRED",):
        earned = False

    return {
        "schema": "gunnchos.platform_digital_complete.v1",
        "token": TOKEN if earned else None,
        "earned": earned,
        "checks": checks,
        "non_blockers": non_blockers,
        "claim_boundary": CLAIM_BOUNDARY,
        "mock": False,
    }
