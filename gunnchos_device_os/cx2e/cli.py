"""CX2E CLI — full lifecycle or evidence-only."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from gunnchos_device_os.cx2e.evidence import write_evidence
from gunnchos_device_os.cx2e.paths import repo_root_from_here
from gunnchos_device_os.cx2e.qemu import (
    host_prereqs,
    prepare_overlay,
    run_first_boot_provision,
    start_graphical_guest,
    stop_guest,
)
from gunnchos_device_os.cx2e.session import collect_session_facts


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="python -m gunnchos_device_os.cx2e")
    p.add_argument("--repo", type=Path, default=None)
    p.add_argument("--prepare-only", action="store_true")
    p.add_argument("--provision-only", action="store_true")
    p.add_argument("--full-lifecycle", action="store_true")
    p.add_argument("--evidence-only", action="store_true")
    p.add_argument("--force-provision", action="store_true")
    p.add_argument("--shutdown", action="store_true")
    args = p.parse_args(argv)
    repo = args.repo or repo_root_from_here()

    if args.shutdown:
        print(json.dumps(stop_guest(repo), indent=2))
        return 0

    overlay = prepare_overlay(repo)
    print("overlay_ok=", overlay.get("ok"), "blocker=", overlay.get("blocker"))
    print("prereqs=", json.dumps(host_prereqs(), indent=2))
    if args.prepare_only:
        write_evidence(repo, provision={"ok": False, "blocker": "prepare_only"}, facts={})
        return 0 if overlay.get("ok") else 1

    provision = {}
    graphical = {}
    facts = {}

    if args.provision_only or args.full_lifecycle:
        provision = run_first_boot_provision(repo, force=args.force_provision)
        print("provision_ok=", provision.get("ok"), "blocker=", provision.get("blocker"))

    if args.full_lifecycle and provision.get("ok"):
        graphical = start_graphical_guest(repo)
        print("graphical_ok=", graphical.get("ok"), "blocker=", graphical.get("blocker"))
        if graphical.get("ok"):
            facts = collect_session_facts(repo)
            print("graphical_truth keys=", {k: facts.get(k) for k in (
                "guest_booted", "guest_is_linux", "compositor_running",
                "wayland_socket_alive", "shell_window_rendered", "lab_blocker")})
        else:
            facts = {"lab_blocker": graphical.get("blocker") or "CX2E_GRAPHICAL_BOOT_FAILED",
                     "guest_booted": False}
        # Always shut down after lifecycle evidence collection
        stop_guest(repo)
    elif args.evidence_only:
        facts = {}
        provision = provision or {"ok": False, "blocker": "evidence_only_no_guest"}

    if not args.provision_only or args.full_lifecycle or args.evidence_only or args.prepare_only:
        report = write_evidence(repo, facts=facts, provision=provision, graphical=graphical)
        print("NEXT_CX_GATE=", report["NEXT_CX_GATE"])
        print("FULL_COMPLETE_EXPERIENCE_COMPLETE=", report["FULL_COMPLETE_EXPERIENCE_COMPLETE"])
        return 0 if (not args.full_lifecycle or provision.get("ok")) else 1
    return 0 if provision.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
