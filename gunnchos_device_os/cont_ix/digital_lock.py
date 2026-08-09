"""Continuation IX digital release lock scorecard + blockers."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable
import json
import time

from gunnchos_device_os.cont_ix import (
    CLAIM_BOUNDARY,
    TOKEN_A11Y,
    TOKEN_ADOPTER_READY,
    TOKEN_API_COMPAT,
    TOKEN_BATTERY_THERMAL,
    TOKEN_BROWSER,
    TOKEN_CUPS,
    TOKEN_DIGITAL_LOCK,
    TOKEN_DOCS,
    TOKEN_EMAIL_CAL,
    TOKEN_FACTORY,
    TOKEN_OFFICE_FILES,
    TOKEN_OFFICE_READY,
    TOKEN_PDF,
    TOKEN_PRODUCTIVITY_INSTALL,
    TOKEN_RECREATION_READY,
    TOKEN_REPRO_READY,
    TOKEN_RING_APP,
    TOKEN_SECURITY,
    TOKEN_STORAGE_PERF,
    TOKEN_STUDENT_READY,
    TOKEN_SUPPORT,
    TOKEN_VIDEO,
    TOKEN_VPN,
)


def _runners() -> list[tuple[str, str, Callable[[], dict[str, Any]]]]:
    from gunnchos_device_os.cont_ix.productivity_install import install_and_prove
    from gunnchos_device_os.cont_ix.browser_e2e import evaluate_browser
    from gunnchos_device_os.cont_ix.office_files_e2e import run_office_files_e2e
    from gunnchos_device_os.cont_ix.pdf_e2e import evaluate_pdf
    from gunnchos_device_os.cont_ix.email_calendar_e2e import evaluate_email_calendar
    from gunnchos_device_os.cont_ix.video_meeting_e2e import evaluate_video_meeting
    from gunnchos_device_os.cont_ix.cups_virtual import evaluate_cups_virtual
    from gunnchos_device_os.cont_ix.vpn_enterprise import evaluate_vpn_enterprise
    from gunnchos_device_os.cont_ix.student_digital_ready import run_student_digital_ready
    from gunnchos_device_os.cont_ix.office_work_digital_ready import run_office_work_digital_ready
    from gunnchos_device_os.cont_ix.recreation_digital_ready import run_recreation_digital_ready
    from gunnchos_device_os.cont_ix.ring_app_e2e import run_ring_app_e2e
    from gunnchos_device_os.cont_ix.adopter_external_sample import run_adopter_external_sample
    from gunnchos_device_os.cont_ix.api_compat import evaluate_api_compat
    from gunnchos_device_os.cont_ix.third_party_repro import evaluate_third_party_repro
    from gunnchos_device_os.cont_ix.factory_line import run_factory_line
    from gunnchos_device_os.cont_ix.security_hardening import evaluate_security_hardening
    from gunnchos_device_os.cont_ix.a11y_hardening import evaluate_a11y_hardening
    from gunnchos_device_os.cont_ix.storage_perf_models import evaluate_storage_perf_models
    from gunnchos_device_os.cont_ix.battery_thermal_handoff import evaluate_battery_thermal_handoff
    from gunnchos_device_os.cont_ix.support_self_service import evaluate_support_self_service
    from gunnchos_device_os.cont_ix.docs_guides import evaluate_docs_guides

    return [
        ("productivity_install", TOKEN_PRODUCTIVITY_INSTALL, install_and_prove),
        ("browser", TOKEN_BROWSER, evaluate_browser),
        ("office_files", TOKEN_OFFICE_FILES, run_office_files_e2e),
        ("pdf", TOKEN_PDF, evaluate_pdf),
        ("email_calendar", TOKEN_EMAIL_CAL, evaluate_email_calendar),
        ("video_meeting", TOKEN_VIDEO, evaluate_video_meeting),
        ("cups_virtual", TOKEN_CUPS, evaluate_cups_virtual),
        ("vpn_enterprise", TOKEN_VPN, evaluate_vpn_enterprise),
        ("student_digital_ready", TOKEN_STUDENT_READY, run_student_digital_ready),
        ("office_work_digital_ready", TOKEN_OFFICE_READY, run_office_work_digital_ready),
        ("recreation_digital_ready", TOKEN_RECREATION_READY, run_recreation_digital_ready),
        ("ring_app", TOKEN_RING_APP, run_ring_app_e2e),
        ("adopter_digital_ready", TOKEN_ADOPTER_READY, run_adopter_external_sample),
        ("api_compat", TOKEN_API_COMPAT, evaluate_api_compat),
        ("reproducibility_digital_ready", TOKEN_REPRO_READY, evaluate_third_party_repro),
        ("factory_line", TOKEN_FACTORY, run_factory_line),
        ("security_hardening", TOKEN_SECURITY, evaluate_security_hardening),
        ("a11y_hardening", TOKEN_A11Y, evaluate_a11y_hardening),
        ("storage_perf_models", TOKEN_STORAGE_PERF, evaluate_storage_perf_models),
        ("battery_thermal_handoff", TOKEN_BATTERY_THERMAL, evaluate_battery_thermal_handoff),
        ("support_self_service", TOKEN_SUPPORT, evaluate_support_self_service),
        ("docs_guides", TOKEN_DOCS, evaluate_docs_guides),
    ]


def evaluate_digital_lock(*, write: bool = True) -> dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    lanes: dict[str, Any] = {}
    for key, expected, fn in _runners():
        report = fn()
        earned = bool(report.get("ok")) and report.get("token") == expected
        lanes[key] = {
            "ok": bool(report.get("ok")),
            "token": report.get("token"),
            "expected_token": expected,
            "earned": earned,
            "failure_reason": report.get("failure_reason"),
        }

    earned_tokens = sorted({v["token"] for v in lanes.values() if v["earned"] and v["token"]})
    digital_blockers = [
        {"lane": k, "reason": v.get("failure_reason") or "token_not_earned"}
        for k, v in lanes.items()
        if not v["earned"]
    ]
    physical_blockers = [
        "PHYSICAL_EXECUTION_FREEZE",
        "physical_boot_on_EVT_hardware",
        "physical_printer_CUPS",
        "physical_BT_audio_lab",
        "physical_dock_display_lab",
        "battery_lab_measurements",
        "thermal_lab_measurements",
        "physical_ring_hardware",
    ]
    external_blockers = [
        "MS_Office_perfect_fidelity_not_claimed",
        "carrier_certification",
        "store_submission_HSM_signing",
        "production_cloud_credentials",
        "restricted_vendor_hw_reproduction",
    ]
    ok = len(digital_blockers) == 0
    report = {
        "schema": "gunnchos.digital_release_lock.v1",
        "continuation": "IX",
        "ok": ok,
        "token": TOKEN_DIGITAL_LOCK if ok else None,
        "lanes": lanes,
        "earned_tokens": earned_tokens,
        "blockers": {
            "DIGITAL": digital_blockers,
            "PHYSICAL": physical_blockers,
            "EXTERNAL": external_blockers,
        },
        "gate1_recreation_ci_safe": True,
        "physical_execution_freeze": True,
        "merge_forbidden": True,
        "recreation_ready_neq_reproducible_ready": True,
        "generated_at": time.time(),
        "mock": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    if write:
        art = root / "artifacts" / "continuation_ix"
        art.mkdir(parents=True, exist_ok=True)
        (art / "DIGITAL_RELEASE_LOCK.json").write_text(
            json.dumps(report, indent=2, default=str), encoding="utf-8"
        )
        (art / "REMAINING_BLOCKERS.json").write_text(
            json.dumps(report["blockers"], indent=2), encoding="utf-8"
        )
        rel = root / "docs" / "release" / "CONTINUATION_IX_DIGITAL_LOCK.md"
        rel.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            "# Continuation IX — Final Digital Release Lock",
            "",
            f"- lock_ok: `{ok}`",
            f"- token: `{report['token']}`",
            f"- earned_tokens: {len(earned_tokens)}",
            f"- DIGITAL blockers: {len(digital_blockers)}",
            "",
            "## Honesty",
            "",
            "- PHYSICAL_EXECUTION_FREEZE active (no purchase/merge).",
            "- RECREATION_DIGITAL_READY ≠ REPRODUCIBILITY_DIGITAL_READY.",
            "- Adopter digital readiness does not require open hardware.",
            "",
            "## Earned tokens",
            "",
        ]
        for t in earned_tokens:
            lines.append(f"- `{t}`")
        if digital_blockers:
            lines.extend(["", "## DIGITAL blockers", ""])
            for b in digital_blockers:
                lines.append(f"- `{b['lane']}`: {b['reason']}")
        rel.write_text("\n".join(lines) + "\n", encoding="utf-8")
        fp = root / "docs" / "full_product" / "CONTINUATION_IX_DIGITAL_RELEASE_LOCK.md"
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(rel.read_text(encoding="utf-8"), encoding="utf-8")
    return report
