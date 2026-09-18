"""CX1 CLI — test-safe entry points for ordinary-user foundations."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .evidence import write_evidence
from .home import GunnchHome
from .journeys import JourneyRunner


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="gunnchos-cx1", description="CX1 Ordinary-User Digital Foundations")
    p.add_argument("--root", type=Path, default=Path.home() / ".gunnchos" / "cx1")
    sub = p.add_subparsers(dest="cmd", required=True)

    first = sub.add_parser("first-run", help="Create local owner profile")
    first.add_argument("--name", required=True)
    first.add_argument("--policy", choices=["School", "Developer", "Play"], default="Play")
    first.add_argument("--password", default=None)

    sub.add_parser("status", help="Show Home status")
    sub.add_parser("journeys", help="Run journeys 1–6")
    ev = sub.add_parser("evidence", help="Write CX1 evidence artifacts")
    ev.add_argument("--repo-root", type=Path, required=True)

    vault = sub.add_parser("vault-write", help="Write a Vault file")
    vault.add_argument("--path", required=True)
    vault.add_argument("--text", required=True)

    sub.add_parser("lock", help="Lock active session")
    sub.add_parser("logout", help="Logout active session")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    home = GunnchHome(args.root)
    if args.cmd == "first-run":
        result = home.identity.first_run(args.name, policy_input=args.policy, password=args.password)
        home.rebind_vault_to_active_profile()
        print(json.dumps(result, indent=2))
        return 0
    if args.cmd == "status":
        print(json.dumps(home.status(), indent=2))
        return 0
    if args.cmd == "journeys":
        if not home.identity.first_run_complete:
            home.identity.first_run("CX1 CLI User", policy_input="Play", password="cli-pass")
        home.rebind_vault_to_active_profile()
        print(json.dumps(JourneyRunner(home).run_all(), indent=2))
        return 0
    if args.cmd == "evidence":
        report = write_evidence(args.repo_root, args.root)
        print(json.dumps({"ok": True, "journeys_ok": all(v.get("ok") for v in report["journeys"].values())}, indent=2))
        return 0
    if args.cmd == "vault-write":
        if not home.identity.first_run_complete:
            home.identity.first_run("CX1 CLI User", policy_input="Play")
        home.rebind_vault_to_active_profile()
        entry = home.vault.write(args.path, args.text.encode("utf-8"))
        print(json.dumps({"path": entry.path, "sha256": entry.sha256}, indent=2))
        return 0
    if args.cmd == "lock":
        print(json.dumps(home.identity.lock().to_dict(), indent=2))
        return 0
    if args.cmd == "logout":
        home.identity.logout()
        print(json.dumps({"logged_out": True}, indent=2))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
