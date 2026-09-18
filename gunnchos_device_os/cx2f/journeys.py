"""CX2F journey re-earn — fail closed unless complete real UI/provider/read-back."""

from __future__ import annotations

from typing import Any, Dict, Optional

CX2E_PRIOR = {
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
        "prior_cx2e_class": prior,
        "cx2f_class": klass,
        "REAL_USER_JOURNEY_DIGITAL_PASS": digital_pass,
        "real_ui": real_ui,
        "real_provider": real_provider,
        "persistence": persistence,
        "missing_condition": "" if digital_pass else missing,
        "blocker": "" if digital_pass else missing,
        "evidence": [],
    }


def upgrade_journeys(facts: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    facts = facts or {}
    shell = bool(facts.get("CX2F_GUNNCH_SHELL_RENDER_PASS") or facts.get("shell_window_rendered"))
    capture = bool(facts.get("CX2F_QEMU_FRAMEBUFFER_CAPTURE_PASS") or facts.get("real_screen_capture_pass"))
    inp = bool(facts.get("CX2F_REAL_INPUT_TO_SHELL_MUTATION_PASS"))
    drm = bool(facts.get("CX2F_WESTON_DRM_PASS"))
    kernel = bool(facts.get("CX2F_NON_CLOUD_KERNEL_BOOT_PASS"))
    base_ui = shell and capture and inp and drm and kernel

    # Full journey DIGITAL_PASS requires complete step evidence flags — not mere provider process probes
    j1_complete = bool(facts.get("j1_complete_ui_provider_readback"))
    j2_complete = bool(facts.get("j2_complete_ui_provider_readback"))
    j3_complete = bool(facts.get("j3_complete_ui_provider_readback"))
    j5_complete = bool(facts.get("j5_complete_ui_provider_readback"))
    j7_complete = bool(facts.get("j7_complete_ui_provider_readback"))

    def need(extra: str) -> str:
        missing = []
        if not kernel:
            missing.append("non_cloud_kernel")
        if not drm:
            missing.append("weston_drm")
        if not shell:
            missing.append("shell_render")
        if not capture:
            missing.append("framebuffer_capture")
        if not inp:
            missing.append("input_to_shell_mutation")
        if extra:
            missing.append(extra)
        return "missing: " + ", ".join(missing)

    results = {
        "J1": _entry(
            "J1",
            prior=CX2E_PRIOR["J1"],
            digital_pass=base_ui and j1_complete,
            missing=need("Writer→PDF→CUPS→Vault backup/restore GUI read-back"),
            real_ui=base_ui,
            real_provider=bool(facts.get("productivity_gui")),
            persistence=j1_complete,
        ),
        "J2": _entry(
            "J2",
            prior=CX2E_PRIOR["J2"],
            digital_pass=base_ui and j2_complete,
            missing=need("browser download→Vault→mail attach/send/receive persistence"),
            real_ui=base_ui,
            real_provider=bool(facts.get("browser_gui") and facts.get("mail_gui")),
        ),
        "J3": _entry(
            "J3",
            prior=CX2E_PRIOR["J3"],
            digital_pass=base_ui and j3_complete,
            missing=need("App Center Flatpak discover/install/launch/update/uninstall GUI"),
            real_ui=base_ui,
            real_provider=bool(facts.get("app_lifecycle_gui")),
        ),
        "J4": _entry(
            "J4",
            prior=CX2E_PRIOR["J4"],
            digital_pass=False,
            missing=need("CalDAV/CardDAV/chat GUI; may remain partial"),
            real_ui=base_ui,
            cls="BLOCKED",
        ),
        "J5": _entry(
            "J5",
            prior=CX2E_PRIOR["J5"],
            digital_pass=base_ui and j5_complete,
            missing=need("offline edit/outbox/reconnect exactly-once GUI evidence"),
            real_ui=base_ui,
            real_provider=bool(facts.get("offline_recovery_gui")),
        ),
        "J6": _entry(
            "J6",
            prior=CX2E_PRIOR["J6"],
            digital_pass=False,
            missing="HUMAN_A11Y_PENDING — AT-SPI/Orca human validation required",
            real_ui=base_ui,
            cls="HUMAN_VALIDATION_PENDING",
        ),
        "J7": _entry(
            "J7",
            prior=CX2E_PRIOR["J7"],
            digital_pass=base_ui and j7_complete,
            missing=need("Care/Vault backup→corrupt→restore→Writer reopen GUI"),
            real_ui=base_ui,
        ),
    }
    any_pass = any(j["REAL_USER_JOURNEY_DIGITAL_PASS"] for j in results.values())
    desired_ids = ["J1", "J2", "J3", "J5", "J7"]
    desired = all(results[i]["REAL_USER_JOURNEY_DIGITAL_PASS"] for i in desired_ids)
    return {
        "schema": "gunnchos.cx2f.journey_upgrade.v1",
        "graphical_truth": base_ui,
        "journeys": results,
        "any_real_user_journey_digital_pass": any_pass,
        "desired_before_cx3_pass": desired,
        "desired_ids": desired_ids,
    }
