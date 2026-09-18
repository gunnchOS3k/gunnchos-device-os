"""CLI for Validation Center — host-side, no QEMU by default. CX4.1 + CX4.2."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from gunnchos_device_os.cx4.paths import repo_root_from_here
from gunnchos_device_os.cx4_validation_center.freeze import freeze_check
from gunnchos_device_os.cx4_validation_center.materiality import compare_freeze, current_build_snapshot
from gunnchos_device_os.cx4_validation_center.rehearsal import run_rehearsal
from gunnchos_device_os.cx4_validation_center.service import ValidationCenter
from gunnchos_device_os.cx4_validation_center.store import StoreError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cx4-validation-center")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_qual = sub.add_parser("qualify", help="Run host-side CX4.1 software qualification")
    p_qual.add_argument("--out", type=Path, default=None)

    p_pilot = sub.add_parser("qualify-pilot", help="Run CX4.2 pilot-readiness qualification")
    p_pilot.add_argument("--out", type=Path, default=None)

    p_lib = sub.add_parser("library", help="Print task library JSON")
    p_dash = sub.add_parser("dashboard", help="Print dashboard buckets")
    p_ed = sub.add_parser("edmund", help="Print Edmund action mapping")

    p_serve = sub.add_parser("serve-static", help="Serve Validation Center UI")
    p_serve.add_argument("--port", type=int, default=8765)
    p_serve.add_argument("--lan", action="store_true", help="Explicit LAN bind (warns; default is loopback)")

    p_freeze = sub.add_parser("freeze-check", help="Emit HumanValidationFreezeManifest / eligibility")
    p_freeze.add_argument("--portal-commit", default="")
    p_freeze.add_argument(
        "--freeze-build",
        action="store_true",
        help="Record build as frozen when HEAD is on accepted main and the worktree is clean",
    )
    p_freeze.add_argument("--target-commit", default="", help="Explicit RC/main target SHA")
    p_freeze.add_argument(
        "--hardware-prerequisites-real",
        action="store_true",
        help="Owner attestation that real hardware prerequisites exist (never invent)",
    )

    p_cmp = sub.add_parser("compare-freeze", help="Compare submission freeze vs current build")
    p_cmp.add_argument("submission", type=Path)
    p_cmp.add_argument("current_build", type=Path, nargs="?", default=None)

    p_reh = sub.add_parser("rehearsal", help="Run REHEARSAL_NON_GATING automated flow")
    p_reh.add_argument("--reset", action="store_true")

    p_val = sub.add_parser("validate-session", help="Refuse incomplete human-validation evidence")
    p_val.add_argument("session", type=Path)

    p_loop = sub.add_parser("refinement-loop", help="Defect intake/triage/revalidation automation")
    p_loop.add_argument("sessions", nargs="+", type=Path, help="Session JSON paths")
    p_loop.add_argument("--out", type=Path, default=None)

    args = parser.parse_args(argv)
    repo = repo_root_from_here()
    evidence_41 = repo / "artifacts" / "complete_experience" / "cx4_1"
    evidence_42 = repo / "artifacts" / "complete_experience" / "cx4_2"
    vc = ValidationCenter(evidence_41 / "runtime", repo)

    if args.cmd == "library":
        print(json.dumps(vc.library(), indent=2))
        return 0
    if args.cmd == "dashboard":
        print(json.dumps(vc.dashboard(), indent=2))
        return 0
    if args.cmd == "edmund":
        print(json.dumps(vc.edmund(), indent=2))
        return 0
    if args.cmd == "serve-static":
        import http.server
        import os
        import socketserver

        from gunnchos_device_os.cx4_validation_center.security import discover_lan_ips, lan_bind_allowed

        host, _ = lan_bind_allowed(bool(args.lan))
        port = args.port
        os_chdir = vc.app_dir

        class Reusable(socketserver.TCPServer):
            allow_reuse_address = True

        info = {
            "serving": str(os_chdir),
            "host": host,
            "port": port,
            "lan_opt_in": bool(args.lan),
            "participant_url": f"http://127.0.0.1:{port}/#participant",
            "moderator_url": f"http://127.0.0.1:{port}/#moderator",
            "reviewer_url": f"http://127.0.0.1:{port}/#reviewer",
        }
        if args.lan:
            info["warning"] = "LAN mode exposes Validation Center on the local network. Use high-entropy session tokens; revoke access when done."
            info["lan_ips"] = discover_lan_ips()
            for ip in info["lan_ips"]:
                info.setdefault("lan_urls", []).append(f"http://{ip}:{port}/")
        print(json.dumps(info, indent=2))
        os.chdir(os_chdir)
        with Reusable((host, port), http.server.SimpleHTTPRequestHandler) as httpd:
            httpd.serve_forever()
        return 0
    if args.cmd == "freeze-check":
        report = freeze_check(
            repo,
            portal_control_commit=args.portal_commit,
            freeze_build=bool(args.freeze_build),
            target_release_or_main_commit=args.target_commit,
            hardware_prerequisites_real=bool(args.hardware_prerequisites_real),
        )
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report.get("CX4_HUMAN_VALIDATION_FREEZE_CHECK_PASS") else 2
    if args.cmd == "compare-freeze":
        submission = json.loads(Path(args.submission).read_text(encoding="utf-8"))
        if args.current_build:
            current = json.loads(Path(args.current_build).read_text(encoding="utf-8"))
            result = compare_freeze(submission, current)
        else:
            result = compare_freeze(submission, repo_root=repo)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    if args.cmd == "rehearsal":
        out = evidence_42 / "runtime" / "rehearsal"
        if args.reset:
            (out / ".rehearsal_reset_allowed").parent.mkdir(parents=True, exist_ok=True)
            (out / ".rehearsal_reset_allowed").write_text("ok\n", encoding="utf-8")
        try:
            report = run_rehearsal(out, repo_root=repo, reset=bool(args.reset))
        except StoreError as exc:
            print(json.dumps({"error": exc.code, "detail": exc.detail}), file=sys.stderr)
            return 2
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report.get("CX4_VALIDATION_REHEARSAL_FLOW_PASS") else 2
    if args.cmd == "validate-session":
        from gunnchos_device_os.cx4_validation_center.evidence_validator import (
            validate_submission_bundle,
        )

        session = json.loads(Path(args.session).read_text(encoding="utf-8"))
        report = validate_submission_bundle(session)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report.get("ok") else 2
    if args.cmd == "refinement-loop":
        from gunnchos_device_os.cx4_validation_center.refinement_loop import run_refinement_loop

        sessions = [json.loads(p.read_text(encoding="utf-8")) for p in args.sessions]
        out = args.out or (evidence_42 / "refinement_loop")
        report = run_refinement_loop(sessions, out_dir=out)
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0 if report.get("HUMAN_REFINEMENT_LOOP_READY") else 2
    if args.cmd == "qualify":
        report = vc.qualify_software()
        out = args.out or evidence_41
        out.mkdir(parents=True, exist_ok=True)
        (out / "CX4_1_TOKENS.json").write_text(json.dumps(report["tokens"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (out / "CX4_1_EVIDENCE_REPORT.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (out / "README.md").write_text(
            "# CX4.1 Validation Center evidence\n\n"
            "Software qualification only. Real human sessions count starts at 0.\n"
            "Human/physical gates remain pending.\n",
            encoding="utf-8",
        )
        print(json.dumps(report["tokens"], indent=2, sort_keys=True))
        return 0 if report["tokens"].get("CX4_VALIDATION_CENTER_GUI_PASS") else 2
    if args.cmd == "qualify-pilot":
        report = vc.qualify_pilot_readiness()
        out = args.out or evidence_42
        out.mkdir(parents=True, exist_ok=True)
        (out / "CX4_2_TOKENS.json").write_text(json.dumps(report["tokens"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (out / "CX4_2_EVIDENCE_REPORT.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        (out / "README.md").write_text(
            "# CX4.2 Validation Center pilot readiness evidence\n\n"
            "Pilot readiness / freeze prep only. "
            "CX4_FINAL_HUMAN_VALIDATION_ELIGIBLE=false. "
            "Rehearsal sessions are not real human sessions.\n",
            encoding="utf-8",
        )
        print(json.dumps(report["tokens"], indent=2, sort_keys=True))
        return 0 if report["tokens"].get("CX4_VALIDATION_CENTER_ONE_CLICK_LAUNCH_PASS") else 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
