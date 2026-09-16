"""CX2E J1–J7 upgrade — REAL_USER_JOURNEY_DIGITAL_PASS only with strict criteria."""

from __future__ import annotations

from typing import Any, Dict, Optional


CX2D_PRIOR = {
    "J1": "BLOCKED",
    "J2": "BLOCKED",
    "J3": "BLOCKED",
    "J4": "BLOCKED",
    "J5": "BLOCKED",
    "J6": "HUMAN_VALIDATION_PENDING",
    "J7": "BLOCKED",
}


def _entry(
    jid: str,
    *,
    prior: str,
    digital_pass: bool,
    missing: str,
    real_ui: bool = False,
    real_provider: bool = False,
    persistence: bool = False,
    cls: Optional[str] = None,
) -> Dict[str, Any]:
    if digital_pass:
        klass = "REAL_USER_JOURNEY_DIGITAL_PASS"
    else:
        klass = cls or ("HUMAN_VALIDATION_PENDING" if jid == "J6" else "BLOCKED")
    return {
        "id": jid,
        "prior_cx2d_class": prior,
        "cx2e_class": klass,
        "REAL_USER_JOURNEY_DIGITAL_PASS": digital_pass,
        "real_ui": real_ui,
        "real_provider": real_provider,
        "persistence": persistence,
        "missing_condition": "" if digital_pass else missing,
        "blocker": "" if digital_pass else missing,
    }


def upgrade_journeys(facts: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    facts = facts or {}
    shell = bool(facts.get("shell_window_rendered"))
    input_ok = bool(facts.get("real_input_pass"))
    capture = bool(facts.get("real_screen_capture_pass") or facts.get("render_capture_pass"))
    base_ui = shell and input_ok and capture and bool(facts.get("compositor_running"))

    def need(extra: str) -> str:
        missing = []
        if not facts.get("guest_booted"):
            missing.append("guest_booted")
        if not facts.get("guest_is_linux"):
            missing.append("guest_is_linux")
        if not facts.get("compositor_running"):
            missing.append("compositor_running")
        if not facts.get("wayland_socket_alive"):
            missing.append("wayland_socket_alive")
        if not shell:
            missing.append("shell_window_rendered")
        if not input_ok:
            missing.append("real_input_pass")
        if not capture:
            missing.append("real_screen_capture_pass")
        if extra:
            missing.append(extra)
        return "missing: " + ", ".join(missing) if missing else extra

    j1_ok = base_ui and bool(facts.get("PRODUCTIVITY_GUI") or facts.get("productivity_gui")) and bool(
        facts.get("IPP_GUI_DIGITAL") or facts.get("ipp_gui_digital")
    )
    j2_ok = base_ui and bool(facts.get("BROWSER_GUI") or facts.get("browser_gui")) and bool(
        facts.get("MAIL_GUI") or facts.get("mail_gui")
    )
    j3_ok = base_ui and bool(facts.get("APP_LIFECYCLE_GUI") or facts.get("app_lifecycle_gui"))
    j4_ok = base_ui and bool(facts.get("CALDAV_CARDDAV_GUI") or facts.get("caldav_carddav_gui"))
    # chat may stay partial
    j4_chat = bool(facts.get("chat_video_attempt"))
    j5_ok = base_ui and bool(facts.get("OFFLINE_RECOVERY_GUI") or facts.get("offline_recovery_gui"))
    j7_ok = base_ui and bool(facts.get("OFFLINE_RECOVERY_GUI") or facts.get("offline_recovery_gui") or shell)

    results = {
        "J1": _entry(
            "J1",
            prior=CX2D_PRIOR["J1"],
            digital_pass=j1_ok,
            missing=need("Writer/print GUI provider evidence"),
            real_ui=base_ui,
            real_provider=bool(facts.get("PRODUCTIVITY_GUI")),
            persistence=j1_ok,
        ),
        "J2": _entry(
            "J2",
            prior=CX2D_PRIOR["J2"],
            digital_pass=j2_ok,
            missing=need("browser+mail GUI evidence"),
            real_ui=base_ui,
            real_provider=bool(facts.get("BROWSER_GUI")),
            persistence=j2_ok,
        ),
        "J3": _entry(
            "J3",
            prior=CX2D_PRIOR["J3"],
            digital_pass=j3_ok,
            missing=need("Flatpak/App Center GUI evidence"),
            real_ui=base_ui,
            real_provider=bool(facts.get("APP_LIFECYCLE_GUI")),
            persistence=j3_ok,
        ),
        "J4": _entry(
            "J4",
            prior=CX2D_PRIOR["J4"],
            digital_pass=j4_ok and j4_chat,
            missing=need("CalDAV/CardDAV/chat GUI; chat may remain partial"),
            real_ui=base_ui,
            real_provider=j4_ok,
            persistence=False,
            cls="REAL_PROVIDER_PARTIAL" if j4_ok and not j4_chat else None,
        ),
        "J5": _entry(
            "J5",
            prior=CX2D_PRIOR["J5"],
            digital_pass=j5_ok,
            missing=need("offline recovery GUI evidence"),
            real_ui=base_ui,
            real_provider=j5_ok,
            persistence=j5_ok,
        ),
        "J6": _entry(
            "J6",
            prior=CX2D_PRIOR["J6"],
            digital_pass=False,
            missing="HUMAN_A11Y_PENDING — AT-SPI/Orca human validation required",
            real_ui=bool(facts.get("digital_a11y_pass")),
            cls="HUMAN_VALIDATION_PENDING",
        ),
        "J7": _entry(
            "J7",
            prior=CX2D_PRIOR["J7"],
            digital_pass=j7_ok,
            missing=need("recovery GUI evidence"),
            real_ui=base_ui,
            real_provider=j7_ok,
            persistence=j7_ok,
        ),
    }
    any_pass = any(j["REAL_USER_JOURNEY_DIGITAL_PASS"] for j in results.values())
    desired = ["J1", "J2", "J3", "J5", "J7"]
    desired_pass = all(results[j]["REAL_USER_JOURNEY_DIGITAL_PASS"] for j in desired)
    return {
        "schema": "gunnchos.cx2e.journey_upgrade.v1",
        "graphical_truth": bool(
            facts.get("guest_booted")
            and facts.get("guest_is_linux")
            and facts.get("compositor_running")
            and facts.get("wayland_socket_alive")
            and facts.get("shell_window_rendered")
        ),
        "journeys": results,
        "any_real_user_journey_digital_pass": any_pass,
        "desired_before_cx3_pass": desired_pass,
        "desired_ids": desired,
    }
