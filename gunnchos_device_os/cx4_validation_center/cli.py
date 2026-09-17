"""CLI for Validation Center — host-side, no QEMU by default."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from gunnchos_device_os.cx4.paths import repo_root_from_here
from gunnchos_device_os.cx4_validation_center.service import ValidationCenter


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cx4-validation-center")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_qual = sub.add_parser("qualify", help="Run host-side software qualification")
    p_qual.add_argument("--out", type=Path, default=None)

    p_lib = sub.add_parser("library", help="Print task library JSON")
    p_dash = sub.add_parser("dashboard", help="Print dashboard buckets")
    p_ed = sub.add_parser("edmund", help="Print Edmund action mapping")

    p_serve = sub.add_parser("serve-static", help="Serve Validation Center UI on loopback")
    p_serve.add_argument("--port", type=int, default=8765)

    args = parser.parse_args(argv)
    repo = repo_root_from_here()
    evidence = repo / "artifacts" / "complete_experience" / "cx4_1"
    vc = ValidationCenter(evidence / "runtime", repo)

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
        import socketserver
        from gunnchos_device_os.cx4_validation_center.security import lan_bind_allowed

        host, _ = lan_bind_allowed(False)
        port = args.port
        os_chdir = vc.app_dir
        handler = http.server.SimpleHTTPRequestHandler
        # Bind loopback only
        class Reusable(socketserver.TCPServer):
            allow_reuse_address = True

        print(json.dumps({"serving": str(os_chdir), "host": host, "port": port, "lan_opt_in": False}))
        import os

        os.chdir(os_chdir)
        with Reusable((host, port), handler) as httpd:
            httpd.serve_forever()
        return 0
    if args.cmd == "qualify":
        report = vc.qualify_software()
        out = args.out or evidence
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
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
