"""CX3.1 CLI — Credential Wallet + Signed Portfolio Foundation."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path
from typing import Any, Dict

from gunnchos_device_os.cx3.evidence import write_evidence
from gunnchos_device_os.cx3.foundation import run_foundation
from gunnchos_device_os.cx3.paths import ensure_lab_tree, evidence_root, repo_root_from_here
from gunnchos_device_os.cx3.qemu import prepare_overlay, start_graphical_guest, stop_guest
from gunnchos_device_os.cx3.session import (
    retain_journey_classes,
    run_gui_signed_credential_journey,
    start_host_provider,
    stop_host_provider,
)
from gunnchos_device_os.cx3.tokens import Cx3Tokens


def _git_tip(repo: Path) -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    except Exception:
        return "unknown"


def run_cx3(repo: Path, *, try_guest: bool = True) -> Dict[str, Any]:
    tokens = Cx3Tokens()
    facts: Dict[str, Any] = {
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "wave": "CX3.1",
        "tip": _git_tip(repo),
        "certification_claimed": False,
    }
    lab = ensure_lab_tree(repo)

    # Retain journey classes from CX2H4
    retained = retain_journey_classes(repo)
    facts["CX3_JOURNEY_RETAIN"] = retained
    tokens.CX2H4_P0_DIGITAL_CLOSURE_PASS = bool(retained.get("CX2H4_P0_DIGITAL_CLOSURE_PASS"))
    for j in ("J1_CLASS", "J2_CLASS", "J3_CLASS", "J4_CLASS", "J5_CLASS", "J6_CLASS", "J7_CLASS"):
        if retained.get(j):
            setattr(tokens, j, retained[j])
    tokens.J6_CLASS = "HUMAN_VALIDATION_PENDING"
    if not tokens.CX2H4_P0_DIGITAL_CLOSURE_PASS:
        tokens.lab_blocker = "CX2H4_P0_DIGITAL_CLOSURE_PASS_FALSE"
        return _finalize(repo, tokens, facts)

    # Host foundation proofs
    foundation = run_foundation(repo)
    facts.update(foundation.get("facts") or {})
    for k, v in (foundation.get("token_hints") or {}).items():
        if hasattr(tokens, k):
            setattr(tokens, k, v)

    # Host provider + GUI API journey (Wallet/Portfolio surfaces required)
    provider = start_host_provider(repo)
    facts["CX3_HOST_PROVIDER"] = {k: provider.get(k) for k in provider if k != "pid"}
    gui = run_gui_signed_credential_journey(repo, provider)
    facts["CX3_GUI_SIGNED_CREDENTIAL_JOURNEY"] = gui
    tokens.CX3_WALLET_GUI_PASS = bool(gui.get("CX3_WALLET_GUI_PASS"))
    tokens.CX3_PORTFOLIO_GUI_PASS = bool(gui.get("CX3_PORTFOLIO_GUI_PASS"))
    tokens.CX3_SIGNED_CREDENTIAL_JOURNEY_PASS = bool(gui.get("CX3_SIGNED_CREDENTIAL_JOURNEY_PASS"))
    stop_host_provider(provider)

    # Optional single CX QEMU guest (never kill foreign)
    guest_info: Dict[str, Any] = {"attempted": False}
    if try_guest:
        guest_info["attempted"] = True
        overlay = prepare_overlay(repo)
        guest_info["overlay"] = overlay
        if overlay.get("ok"):
            graphical = start_graphical_guest(repo)
            guest_info["graphical"] = {k: graphical.get(k) for k in graphical if k != "qemu_cmd"}
            tokens.guest_booted = bool(graphical.get("guest_booted"))
            tokens.guest_is_linux = bool(graphical.get("ok"))
            if graphical.get("ok"):
                # Deploy provider into guest and smoke health via SSH if possible
                try:
                    from gunnchos_device_os.cx3.qemu import scp_to_guest, ssh_exec

                    key = Path("/tmp/cx3-graphical/ssh/id_ed25519")
                    port = int(graphical.get("ssh_port") or 2222)
                    script = lab / "scripts" / "cx3_provider.py"
                    ssh_exec(
                        key,
                        port,
                        "sudo mkdir -p /var/lib/cx3/bin /var/lib/cx3/wallet /var/lib/cx3/portfolio; "
                        "sudo chown -R gunnchos:gunnchos /var/lib/cx3",
                        timeout=60,
                    )
                    scp_to_guest(key, port, script, "/var/lib/cx3/bin/cx3_provider.py")
                    guest_info["provider_deployed"] = True
                except Exception as exc:  # noqa: BLE001
                    guest_info["provider_deploy_error"] = type(exc).__name__
                stop_guest(repo)
            else:
                guest_info["blocker"] = graphical.get("blocker")
                try:
                    stop_guest(repo)
                except Exception:
                    pass
        else:
            guest_info["blocker"] = overlay.get("blocker")
    facts["CX3_GUEST"] = guest_info

    # Host GUI journey is canonical for WALLET/PORTFOLIO GUI tokens in CX3.1;
    # guest deploy is additive evidence when the CX slot is free.
    if not tokens.CX3_WALLET_GUI_PASS:
        tokens.lab_blocker = tokens.lab_blocker or gui.get("blocker") or "CX3_WALLET_GUI"
    if not tokens.CX3_SIGNED_CREDENTIAL_JOURNEY_PASS:
        tokens.lab_blocker = tokens.lab_blocker or "CX3_SIGNED_CREDENTIAL_JOURNEY"

    report = write_evidence(repo, tokens, facts)
    # Mirror captures note
    (lab / "evidence").mkdir(parents=True, exist_ok=True)
    (lab / "evidence" / "last_report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def _finalize(repo: Path, tokens: Cx3Tokens, facts: Dict[str, Any]) -> Dict[str, Any]:
    return write_evidence(repo, tokens, facts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CX3.1 Credential Wallet + Portfolio Foundation")
    parser.add_argument("--repo", type=Path, default=None)
    parser.add_argument("--no-guest", action="store_true", help="Skip QEMU guest attempt")
    parser.add_argument("--print-report", action="store_true")
    args = parser.parse_args(argv)
    repo = args.repo or repo_root_from_here()
    report = run_cx3(repo, try_guest=not args.no_guest)
    if args.print_report:
        print(json.dumps(report, indent=2))
    else:
        tokens = report.get("tokens") or {}
        print(
            json.dumps(
                {
                    "CX3_1_WALLET_PORTFOLIO_FOUNDATION_PASS": tokens.get(
                        "CX3_1_WALLET_PORTFOLIO_FOUNDATION_PASS"
                    ),
                    "WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS": tokens.get(
                        "WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS"
                    ),
                    "NEXT_CX_GATE": report.get("NEXT_CX_GATE"),
                    "FULL_COMPLETE_EXPERIENCE_COMPLETE": False,
                    "certification_claimed": False,
                    "evidence": str(evidence_root(repo)),
                },
                indent=2,
            )
        )
    return 0 if (report.get("tokens") or {}).get("CX3_1_WALLET_PORTFOLIO_FOUNDATION_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
