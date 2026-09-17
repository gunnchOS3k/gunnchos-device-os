"""CX3.2 CLI — WAIKE career sharing + verifier campaign."""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path
from typing import Any, Dict

from gunnchos_device_os.cx3_2.evidence import write_evidence
from gunnchos_device_os.cx3_2.foundation import run_foundation
from gunnchos_device_os.cx3_2.paths import ensure_lab_tree, evidence_root, repo_root_from_here
from gunnchos_device_os.cx3_2.session import run_career_verifier_gui_journey, start_host_provider, stop_host_provider
from gunnchos_device_os.cx3_2.tokens import Cx32Tokens


def _git_tip(repo: Path) -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    except Exception:
        return "unknown"


def run_cx32(repo: Path, *, try_guest: bool = True) -> Dict[str, Any]:
    tokens = Cx32Tokens()
    facts: Dict[str, Any] = {
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "wave": "CX3.2",
        "tip": _git_tip(repo),
        "certification_claimed": False,
    }
    lab = ensure_lab_tree(repo)

    foundation = run_foundation(repo)
    facts.update(foundation.get("facts") or {})
    for k, v in (foundation.get("token_hints") or {}).items():
        if hasattr(tokens, k):
            setattr(tokens, k, v)

    provider = start_host_provider(repo)
    facts["CX3_2_HOST_PROVIDER"] = {k: provider.get(k) for k in provider if k != "pid"}
    gui = run_career_verifier_gui_journey(repo, provider)
    facts["CX3_2_GUI_JOURNEY"] = gui
    facts["CX3_2_VERIFIER_GUI"] = {
        "ok": bool(gui.get("CX3_REAL_VERIFIER_GUI_PASS")),
        "detail": gui.get("verifier"),
        "certification_claimed": False,
    }
    # Merge career GUI facts
    if "CX3_2_CAREER_PROFILE" in facts:
        facts["CX3_2_CAREER_PROFILE"] = {
            **facts["CX3_2_CAREER_PROFILE"],
            "gui": bool(gui.get("CX3_REAL_CAREER_PROFILE_GUI_PASS")),
        }
    tokens.CX3_REAL_CAREER_PROFILE_GUI_PASS = bool(gui.get("CX3_REAL_CAREER_PROFILE_GUI_PASS"))
    tokens.CX3_REAL_VERIFIER_GUI_PASS = bool(gui.get("CX3_REAL_VERIFIER_GUI_PASS"))
    tokens.CX3_NO_SECOND_COMPUTER_CAREER_PASS = bool(gui.get("CX3_NO_SECOND_COMPUTER_CAREER_PASS"))
    stop_host_provider(provider)

    # Optional single CX QEMU guest — reuse CX3.1 overlay slot with ownership lock; never kill foreign
    guest_info: Dict[str, Any] = {"attempted": False}
    if try_guest:
        guest_info["attempted"] = True
        try:
            from gunnchos_device_os.cx3.qemu import prepare_overlay, start_graphical_guest, stop_guest

            # Point lab overlays via env-compatible reuse of cx3 helpers with cx3_2 lock name
            overlay = prepare_overlay(repo)
            guest_info["overlay"] = {k: overlay.get(k) for k in overlay if k != "qemu_cmd"}
            if overlay.get("ok"):
                graphical = start_graphical_guest(repo)
                guest_info["graphical"] = {k: graphical.get(k) for k in graphical if k != "qemu_cmd"}
                tokens.guest_booted = bool(graphical.get("guest_booted"))
                tokens.guest_is_linux = bool(graphical.get("ok"))
                try:
                    stop_guest(repo)
                except Exception:
                    pass
            else:
                guest_info["blocker"] = overlay.get("blocker")
        except Exception as exc:  # noqa: BLE001
            guest_info["blocker"] = type(exc).__name__
            guest_info["detail"] = str(exc)
    facts["CX3_2_GUEST"] = guest_info

    if not tokens.CX3_REAL_CAREER_PROFILE_GUI_PASS:
        tokens.lab_blocker = tokens.lab_blocker or gui.get("blocker") or "CX3_REAL_CAREER_PROFILE_GUI"
    if not tokens.CX3_INDEPENDENT_VERIFIER_PASS:
        tokens.lab_blocker = tokens.lab_blocker or "CX3_INDEPENDENT_VERIFIER"

    report = write_evidence(repo, tokens, facts)
    (lab / "evidence").mkdir(parents=True, exist_ok=True)
    (lab / "evidence" / "last_report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CX3.2 WAIKE career sharing + verifier")
    parser.add_argument("--repo", type=Path, default=None)
    parser.add_argument("--no-guest", action="store_true")
    parser.add_argument("--print-report", action="store_true")
    args = parser.parse_args(argv)
    repo = args.repo or repo_root_from_here()
    report = run_cx32(repo, try_guest=not args.no_guest)
    if args.print_report:
        print(json.dumps(report, indent=2))
    else:
        tokens = report.get("tokens") or {}
        print(
            json.dumps(
                {
                    "CX3_2_CAREER_VERIFIER_PASS": tokens.get("CX3_2_CAREER_VERIFIER_PASS"),
                    "CX3_WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS": tokens.get(
                        "CX3_WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS"
                    ),
                    "WAIKE_REAL_EARNED_EVIDENCE_AVAILABLE": tokens.get("WAIKE_REAL_EARNED_EVIDENCE_AVAILABLE"),
                    "NEXT_CX_GATE": report.get("NEXT_CX_GATE"),
                    "FULL_COMPLETE_EXPERIENCE_COMPLETE": False,
                    "certification_claimed": False,
                    "evidence": str(evidence_root(repo)),
                },
                indent=2,
            )
        )
    return 0 if (report.get("tokens") or {}).get("CX3_2_CAREER_VERIFIER_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
