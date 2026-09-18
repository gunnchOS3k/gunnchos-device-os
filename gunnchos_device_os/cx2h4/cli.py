"""CX2H.4 CLI — P0 digital closure audit (+ smallest remediations)."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path
from typing import Any, Dict

from gunnchos_device_os.cx2h4 import host_providers as hp
from gunnchos_device_os.cx2h4.audit import (
    build_blocker_register,
    build_developer_audit,
    build_domain_matrix,
    build_media_audit,
    build_no_second_computer,
    build_security_audit,
)
from gunnchos_device_os.cx2h4.evidence import write_evidence
from gunnchos_device_os.cx2h4.j4_collab import run_j4_gap_audit
from gunnchos_device_os.cx2h4.office_breadth import run_office_breadth
from gunnchos_device_os.cx2h4.paths import ensure_lab_tree, evidence_root, repo_root_from_here
from gunnchos_device_os.cx2h4.qemu import prepare_overlay, start_graphical_guest, stop_guest
from gunnchos_device_os.cx2h4.session import (
    deploy_cx2h4_provider,
    ensure_accepted_ssh_key,
    journey_provenance_rebind,
)
from gunnchos_device_os.cx2h4.tokens import Cx2h4Tokens


def _git_tip(repo: Path) -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    except Exception:
        return "unknown"


def run_cx2h4(repo: Path, *, resume_running: bool = False) -> Dict[str, Any]:
    tokens = Cx2h4Tokens()
    facts: Dict[str, Any] = {
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "wave": "CX2H.4",
        "tip": _git_tip(repo),
        "resume_running": resume_running,
    }
    lab = ensure_lab_tree(repo)
    captures = Path("/tmp/cx2h4-graphical/captures")
    captures.mkdir(parents=True, exist_ok=True)

    try:
        facts["ssh_key"] = str(ensure_accepted_ssh_key(repo))
    except FileNotFoundError as exc:
        tokens.lab_blocker = str(exc)
        return _finalize_blocked(repo, tokens, facts)

    caldav = hp.start_caldav(repo)
    facts["CX2H4_CALDAV_PROVIDER_PROVENANCE"] = caldav
    if not caldav.get("ok"):
        tokens.lab_blocker = caldav.get("blocker") or "CX2H4_CALDAV"
        hp.stop_caldav()
        return _finalize_blocked(repo, tokens, facts)

    monitor = Path("/tmp/cx2h4-graphical/monitor.sock")
    if resume_running:
        pidfile = Path("/tmp/cx2h4-graphical/qemu.pid")
        alive = False
        if pidfile.is_file():
            try:
                import os as _os

                alive = True
                _os.kill(int(pidfile.read_text().strip()), 0)
            except Exception:
                alive = False
        if not (alive and monitor.exists()):
            tokens.lab_blocker = "CX2H4_RESUME_NO_RUNNING_GUEST"
            hp.stop_caldav()
            return _finalize_blocked(repo, tokens, facts)
        tokens.guest_booted = True
        tokens.guest_is_linux = True
        facts["graphical"] = {"ok": True, "resumed": True, "runtime": {"monitor": str(monitor)}}
    else:
        overlay = prepare_overlay(repo)
        facts["overlay"] = overlay
        if not overlay.get("ok"):
            tokens.lab_blocker = overlay.get("blocker") or "CX2H4_OVERLAY_FAIL"
            hp.stop_caldav()
            return _finalize_blocked(repo, tokens, facts)

        graphical = start_graphical_guest(repo)
        facts["graphical"] = {k: graphical.get(k) for k in graphical if k != "qemu_cmd"}
        tokens.guest_booted = bool(graphical.get("guest_booted"))
        if not graphical.get("ok"):
            tokens.lab_blocker = graphical.get("blocker") or "CX2H4_GRAPHICAL_BOOT_FAILED"
            try:
                stop_guest(repo)
            except Exception:
                pass
            hp.stop_caldav()
            return _finalize_blocked(repo, tokens, facts)
        tokens.guest_is_linux = True
        monitor = Path(graphical["runtime"]["monitor"])

    rebind = journey_provenance_rebind(repo, monitor, captures)
    facts["CX2H4_JOURNEY_PROVENANCE_REBIND"] = rebind
    tokens.CX2H4_JOURNEY_REBIND_PASS = bool(rebind.get("CX2H4_JOURNEY_REBIND_PASS"))
    for j in ("J1_CLASS", "J2_CLASS", "J3_CLASS", "J5_CLASS", "J7_CLASS", "J6_CLASS"):
        if rebind.get(j):
            setattr(tokens, j, rebind[j])
    if not tokens.CX2H4_JOURNEY_REBIND_PASS:
        tokens.lab_blocker = rebind.get("blocker") or "CX2H4_JOURNEY_REBIND"
        if not resume_running:
            stop_guest(repo)
        hp.stop_caldav()
        return _finalize_blocked(repo, tokens, facts, rebind=rebind)

    provider = deploy_cx2h4_provider(repo)
    facts["cx2h4_provider"] = provider
    if not provider.get("ok"):
        tokens.lab_blocker = provider.get("blocker") or "CX2H4_PROVIDER"
        if not resume_running:
            stop_guest(repo)
        hp.stop_caldav()
        return _finalize_blocked(repo, tokens, facts, rebind=rebind)

    office = run_office_breadth(repo, monitor, captures)
    facts["CX2H4_OFFICE_BREADTH_AUDIT"] = office
    tokens.CX2H4_SPREADSHEET_P0_PASS = bool(office.get("CX2H4_SPREADSHEET_P0_PASS"))
    tokens.CX2H4_PRESENTATION_P0_PASS = bool(office.get("CX2H4_PRESENTATION_P0_PASS"))

    j4 = run_j4_gap_audit(repo, monitor, captures, caldav)
    facts["CX2H4_J4_GAP_AUDIT"] = j4
    tokens.CX2H4_J4_P0_DIGITAL_BLOCKER = bool(j4.get("J4_P0_DIGITAL_BLOCKER", True))
    tokens.J4_CLASS = j4.get("J4_CLASS") or "BLOCKED"

    media = build_media_audit()
    developer = build_developer_audit()
    security = build_security_audit(repo)
    nsc = build_no_second_computer(office, j4, rebind)
    matrix = build_domain_matrix(repo, rebind=rebind, j4=j4, office=office, tip=facts["tip"])
    blockers = build_blocker_register(matrix, j4, office, security, nsc)

    tokens.CX2H4_MEDIA_PLAYBACK_DIGITAL_PASS = media["CX2H4_MEDIA_PLAYBACK_DIGITAL_PASS"]
    tokens.CX2H4_DEVELOPER_BASELINE_PASS = developer["CX2H4_DEVELOPER_BASELINE_PASS"]
    tokens.CX2H4_NO_SECOND_COMPUTER_P0_PASS = bool(nsc.get("CX2H4_NO_SECOND_COMPUTER_P0_PASS"))
    tokens.CX2H4_SECURITY_REGRESSION_FREE = bool(security.get("CX2H4_SECURITY_REGRESSION_FREE"))

    report = write_evidence(
        repo,
        tokens,
        facts,
        matrix=matrix,
        rebind=rebind,
        j4=j4,
        office=office,
        media=media,
        developer=developer,
        nsc=nsc,
        security=security,
        blockers=blockers,
    )

    lab_cap = lab / "captures"
    lab_cap.mkdir(parents=True, exist_ok=True)
    for ppm in captures.glob("*.ppm"):
        try:
            (lab_cap / ppm.name).write_bytes(ppm.read_bytes())
        except Exception:
            pass

    stop_guest(repo)
    hp.stop_caldav()
    return report


def _finalize_blocked(
    repo: Path,
    tokens: Cx2h4Tokens,
    facts: Dict[str, Any],
    *,
    rebind: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    rebind = rebind or {
        "ok": False,
        "CX2H4_JOURNEY_REBIND_PASS": False,
        "J1_CLASS": tokens.J1_CLASS,
        "J2_CLASS": tokens.J2_CLASS,
        "J3_CLASS": tokens.J3_CLASS,
        "J5_CLASS": tokens.J5_CLASS,
        "J7_CLASS": tokens.J7_CLASS,
        "J6_CLASS": "HUMAN_VALIDATION_PENDING",
        "blocker": tokens.lab_blocker,
    }
    office = {
        "ok": False,
        "CX2H4_SPREADSHEET_P0_PASS": False,
        "CX2H4_PRESENTATION_P0_PASS": False,
        "blocker": tokens.lab_blocker,
    }
    j4 = {
        "ok": False,
        "J4_P0_DIGITAL_BLOCKER": True,
        "J4_CLASS": "BLOCKED",
        "calendar": {"ok": False, "evidence_class": "BLOCKED"},
        "contacts": {"ok": False, "evidence_class": "BLOCKED"},
        "chat_messaging": {"evidence_class": "EXTERNAL_PROVIDER_PENDING"},
        "meeting_video_entry": {"evidence_class": "EXTERNAL_PROVIDER_PENDING"},
        "blocker": tokens.lab_blocker,
    }
    media = build_media_audit()
    developer = build_developer_audit()
    security = build_security_audit(repo)
    nsc = build_no_second_computer(office, j4, rebind)
    matrix = build_domain_matrix(repo, rebind=rebind, j4=j4, office=office, tip=facts.get("tip", "unknown"))
    blockers = build_blocker_register(matrix, j4, office, security, nsc)
    return write_evidence(
        repo,
        tokens,
        facts,
        matrix=matrix,
        rebind=rebind,
        j4=j4,
        office=office,
        media=media,
        developer=developer,
        nsc=nsc,
        security=security,
        blockers=blockers,
    )


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="python -m gunnchos_device_os.cx2h4")
    p.add_argument("--repo", type=Path, default=None)
    p.add_argument(
        "--resume-running",
        action="store_true",
        help="Continue audit against already-running CX2H4 guest (do not reboot).",
    )
    args = p.parse_args(argv)
    repo = args.repo or repo_root_from_here()
    try:
        report = run_cx2h4(repo, resume_running=bool(args.resume_running))
    except Exception as exc:
        # Fail-closed evidence still required
        tokens = Cx2h4Tokens(lab_blocker=f"CX2H4_UNCAUGHT:{exc}")
        facts = {"uncaught": str(exc), "tip": _git_tip(repo)}
        report = _finalize_blocked(repo, tokens, facts)
        try:
            stop_guest(repo)
        except Exception:
            pass
        try:
            hp.stop_caldav()
        except Exception:
            pass
    print(
        json.dumps(
            {
                "NEXT_CX_GATE": report.get("NEXT_CX_GATE"),
                "CX2H4_P0_DIGITAL_CLOSURE_PASS": (report.get("tokens") or {}).get("CX2H4_P0_DIGITAL_CLOSURE_PASS"),
                "tokens": report.get("tokens"),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
