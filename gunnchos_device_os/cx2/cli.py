"""CX2 CLI — surfaces, providers, journeys, evidence."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from gunnchos_device_os.cx2.evidence import write_evidence
from gunnchos_device_os.cx2.journeys import AuthenticJourneyRunner
from gunnchos_device_os.cx2.shell.product_shell import ProductShell


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="gunnchos-cx2", description="CX2 Real Surface Productization")
    p.add_argument("--root", type=Path, default=Path.home() / ".gunnchos" / "cx2")
    sub = p.add_subparsers(dest="cmd", required=True)
    fr = sub.add_parser("first-run")
    fr.add_argument("--name", required=True)
    fr.add_argument("--policy", default="School")
    sub.add_parser("status")
    surf = sub.add_parser("surface")
    surf.add_argument("id", choices=["home", "vault", "app_center", "connect", "assist", "care"])
    sub.add_parser("journeys")
    ev = sub.add_parser("evidence")
    ev.add_argument("--repo-root", type=Path, required=True)
    sub.add_parser("providers")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    shell = ProductShell(args.root)
    if args.cmd == "first-run":
        print(json.dumps(shell.ensure_first_run(args.name, args.policy), indent=2))
        return 0
    if args.cmd == "status":
        shell.ensure_first_run("CX2 CLI")
        print(json.dumps({"nav": shell.nav.snapshot(), "home": shell.home_model()}, indent=2))
        return 0
    if args.cmd == "surface":
        shell.ensure_first_run("CX2 CLI")
        print(json.dumps(shell.surface(args.id), indent=2))
        return 0
    if args.cmd == "journeys":
        shell.ensure_first_run("CX2 CLI")
        print(json.dumps(AuthenticJourneyRunner(shell).run_all(), indent=2))
        return 0
    if args.cmd == "providers":
        shell.ensure_first_run("CX2 CLI")
        print(json.dumps(shell.provider_registry().health(), indent=2, default=str))
        return 0
    if args.cmd == "evidence":
        report = write_evidence(args.repo_root, args.root)
        print(json.dumps({"ok": True, "FULL_COMPLETE_EXPERIENCE_COMPLETE": report["FULL_COMPLETE_EXPERIENCE_COMPLETE"]}, indent=2))
        return 0
    return 2


if __name__ == "__main__":
    sys.stderr.write("use: python -m gunnchos_device_os.cx2.cli ...\n")
    sys.exit(main())
