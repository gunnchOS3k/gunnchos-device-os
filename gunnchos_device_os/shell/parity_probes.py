"""SYS-MISSION-006 non-game parity runtime probes."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from gunnchos_device_os.gunnchai_integration import tutor_session_start, tutor_prompt_guard
from gunnchos_device_os.waike_integration import deploy_lesson, list_offline_lessons


CLAIM_BOUNDARY = (
    "Runtime probes against in-repo gunnchAI/WAIKE integration modules. "
    "Not full product parity, not portal snapshot refresh."
)


def probe_gunnchai_shell(form_factor: str) -> dict[str, Any]:
    session = tutor_session_start(profile=form_factor, topic="wireless_basics")
    guard = tutor_prompt_guard("explain OFDM subcarriers")
    return {
        "app": "gunnchAI",
        "probe": "tutor_session_start + tutor_prompt_guard",
        "session_started": session.get("started") is True,
        "prompt_allowed": guard.get("ok") is True,
        "runtime": session.get("runtime"),
        "mock": session.get("mock"),
        "claim_boundary": CLAIM_BOUNDARY,
    }


def probe_waike_shell(form_factor: str) -> dict[str, Any]:
    lessons = list_offline_lessons()
    deployed = deploy_lesson(lessons[0], profile=form_factor) if lessons else {"deployed": False}
    return {
        "app": "WAIKE",
        "probe": "list_offline_lessons + deploy_lesson",
        "lesson_count": len(lessons),
        "deployed": deployed.get("deployed"),
        "pack_sources": deployed.get("pack_sources"),
        "mock": deployed.get("mock"),
        "claim_boundary": CLAIM_BOUNDARY,
    }


def probe_shell_contract(shell_snapshot: dict[str, Any]) -> dict[str, Any]:
    api = shell_snapshot.get("shell_snapshot", shell_snapshot).get("api") or shell_snapshot.get("api", {})
    return {
        "app": "gunnchOS_shell",
        "probe": "shell_contract_snapshot",
        "has_session": bool(api.get("session")),
        "has_display_topology": bool(api.get("display_topology")),
        "input_modality_count": len(api.get("input_modality") or []),
        "claim_boundary": CLAIM_BOUNDARY,
    }


def run_parity_probes(form_factor: str, shell_snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "SYS-MISSION-006": {
            "form_factor": form_factor,
            "gunnchai": probe_gunnchai_shell(form_factor),
            "waike": probe_waike_shell(form_factor),
            "shell": probe_shell_contract(shell_snapshot),
            "portal_in_scope": False,
            "portal_reason": "Portal is research index; not end-user shell app for Wave 002",
        }
    }


def device_lab_profile_labels(repo_root: Path) -> dict[str, str]:
    """Section 20 — honest Device Lab profile labels."""
    dsxl = repo_root / "artifacts/product_use/journeys/G14_dsxl/DSXL_COMPOSITOR_UX_EVIDENCE.json"
    labels = {
        "student_14_5": "MODELED",
        "handheld": "HOST_OBSERVED",
        "docked": "EMULATED",
        "ds_xl": "EMULATED" if dsxl.exists() else "MODELED",
        "phone": "MODELED",
        "desktop": "HOST_OBSERVED",
        "pixel_client": "TARGET_DEVICE_OBSERVED",
    }
    if dsxl.exists():
        labels["ds_xl_guest_agent"] = "EMULATED"
    return labels
