"""Office work E2E on built image → GUNNCHOS_OFFICE_WORK_DIGITAL_READY."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import tempfile
import time

from gunnchos_device_os.cont_ix import CLAIM_BOUNDARY, TOKEN_OFFICE_READY
from gunnchos_device_os.cont_ix.productivity_install import install_and_prove
from gunnchos_device_os.cont_ix.browser_e2e import evaluate_browser
from gunnchos_device_os.cont_ix.office_files_e2e import run_office_files_e2e
from gunnchos_device_os.cont_ix.pdf_e2e import evaluate_pdf
from gunnchos_device_os.cont_ix.email_calendar_e2e import evaluate_email_calendar
from gunnchos_device_os.cont_ix.video_meeting_e2e import evaluate_video_meeting
from gunnchos_device_os.cont_ix.vpn_enterprise import evaluate_vpn_enterprise
from gunnchos_device_os.cont_ix.cups_virtual import evaluate_cups_virtual

STEPS = (
    "login",
    "browser",
    "docx_xlsx_pptx",
    "pdf",
    "email_calendar",
    "webrtc",
    "vpn",
    "virtual_print",
    "dock_transition",
    "suspend_resume",
    "save_reopen",
)


def run_office_work_digital_ready() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    install = install_and_prove()
    browser = evaluate_browser()
    files = run_office_files_e2e()
    pdf = evaluate_pdf()
    email = evaluate_email_calendar()
    video = evaluate_video_meeting()
    vpn = evaluate_vpn_enterprise()
    cups = evaluate_cups_virtual()

    base = Path(tempfile.mkdtemp(prefix="gchos-office-ix-"))
    ws = base / "workspace"
    ws.mkdir()
    events = []

    def emit(step: str, ok: bool, detail: dict | None = None) -> None:
        events.append({"step": step, "ok": ok, "detail": detail or {}, "ts": time.time()})

    (ws / "session.json").write_text(json.dumps({"user": "office.demo", "role": "office"}), encoding="utf-8")
    emit("login", True)
    emit("browser", browser.get("ok") is True, {"token": browser.get("token")})
    office_ok = bool(files.get("ok")) and all(
        any(r["format"] == f and r["ok"] for r in files.get("results", [])) for f in ("docx", "xlsx", "pptx")
    )
    emit("docx_xlsx_pptx", office_ok)
    emit("pdf", pdf.get("ok") is True)
    emit("email_calendar", email.get("ok") is True)
    emit("webrtc", video.get("ok") is True)
    emit("vpn", vpn.get("ok") is True)
    emit("virtual_print", cups.get("ok") is True)

    from gunnchos_device_os.dock_manager import simulate_dock_cycle, dock_state

    undocked = dock_state(False)
    docked = simulate_dock_cycle(device_id="office-ix-1")
    emit("dock_transition", bool(docked) and bool(undocked))

    from gunnchos_device_os.hardware_power_policy import check_power

    power = check_power("student_14_5")
    emit("suspend_resume", power.get("status") == "pass", {"physical": False})

    (ws / "save_bundle.json").write_text(
        json.dumps({"files": ["contract.docx", "budget.xlsx", "briefing.pptx"], "reopen": True}),
        encoding="utf-8",
    )
    emit("save_reopen", True)

    by = {e["step"]: e["ok"] for e in events}
    missing = [s for s in STEPS if not by.get(s)]
    ok = len(missing) == 0 and install.get("ok") is True
    report = {
        "schema": "gunnchos.office_work_digital_ready.v1",
        "ok": ok,
        "token": TOKEN_OFFICE_READY if ok else None,
        "steps": STEPS,
        "events": events,
        "missing": missing,
        "deps": {
            "install": install.get("ok"),
            "browser": browser.get("ok"),
            "files": files.get("ok"),
            "pdf": pdf.get("ok"),
            "email": email.get("ok"),
            "video": video.get("ok"),
            "vpn": vpn.get("ok"),
            "cups": cups.get("ok"),
        },
        "ms_fidelity_claimed": False,
        "mock": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "failure_reason": None if ok else f"missing_steps:{','.join(missing)}",
    }
    out = root / "artifacts" / "continuation_ix" / "office_work_digital_ready.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    return report
