"""CX4.0 CLI — guest rebind + non-digital readiness preparation."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any, Dict

from gunnchos_device_os.cx4.blockers import write_master_register
from gunnchos_device_os.cx4.canonical import prepare_campaign_overlay, write_provenance
from gunnchos_device_os.cx4.evidence import write_evidence
from gunnchos_device_os.cx4.paths import evidence_root, ensure_lab_tree, repo_root_from_here
from gunnchos_device_os.cx4.readiness import materialize_all_packets
from gunnchos_device_os.cx4.smoke import run_compact_guest_smoke
from gunnchos_device_os.cx4.tokens import Cx4Tokens


def _git_tip(repo: Path) -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    except Exception:
        return "unknown"


def run_cx4(repo: Path, *, try_guest: bool = True, skip_smoke: bool = False) -> Dict[str, Any]:
    tokens = Cx4Tokens()
    facts: Dict[str, Any] = {
        "tip": _git_tip(repo),
        "wave": "CX4.0",
        "certification_claimed": False,
    }
    ensure_lab_tree(repo)

    prior = repo / "artifacts" / "complete_experience" / "cx3_3" / "CX3_3_TOKENS.json"
    if prior.is_file():
        try:
            p = json.loads(prior.read_text())
            tokens.CX3_EDUCATION_CAREER_DIGITAL_CLOSURE_PASS = bool(
                p.get("CX3_EDUCATION_CAREER_DIGITAL_CLOSURE_PASS", True)
            )
            tokens.CX3_WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS = bool(
                p.get("CX3_WAIKE_EARNED_CREDENTIAL_INTEGRATION_PASS", False)
            )
            tokens.WAIKE_REAL_EARNED_EVIDENCE_AVAILABLE = bool(
                p.get("WAIKE_REAL_EARNED_EVIDENCE_AVAILABLE", False)
            )
        except Exception:
            pass

    overlay = prepare_campaign_overlay(repo)
    write_provenance(repo, overlay)
    facts["overlay"] = {k: overlay.get(k) for k in overlay if k != "create"}
    tokens.CX4_CURRENT_TIP_GUEST_OVERLAY_PASS = bool(overlay.get("ok"))
    if not overlay.get("ok"):
        tokens.lab_blocker = overlay.get("blocker") or "CURRENT_TIP_GUEST_OVERLAY_PASS"

    if try_guest and not skip_smoke and tokens.CX4_CURRENT_TIP_GUEST_OVERLAY_PASS:
        smoke = run_compact_guest_smoke(repo, max_attempts=3)
        facts["smoke"] = {k: smoke.get(k) for k in smoke if k != "attempts"}
        facts["smoke_attempts"] = smoke.get("attempts")
        tokens.CX4_CURRENT_TIP_GUEST_SMOKE_PASS = bool(smoke.get("CX4_CURRENT_TIP_GUEST_SMOKE_PASS"))
        if not tokens.CX4_CURRENT_TIP_GUEST_SMOKE_PASS:
            tokens.lab_blocker = tokens.lab_blocker or smoke.get("blocker") or "CURRENT_TIP_GUEST_SMOKE_PASS"
    elif skip_smoke:
        facts["smoke"] = {"skipped": True}
    else:
        facts["smoke"] = {"skipped": True, "reason": "overlay_failed"}

    packets = materialize_all_packets(repo)
    facts["packets"] = {k: (v.get("ready") if isinstance(v, dict) else None) for k, v in packets.items()}
    tokens.CX4_HUMAN_A11Y_PACKET_READY = bool(packets.get("human_a11y", {}).get("ready"))
    tokens.CX4_PHYSICAL_PRINTER_PACKET_READY = bool(packets.get("printer", {}).get("ready"))
    tokens.CX4_CAMERA_MIC_AV_PACKET_READY = bool(packets.get("av", {}).get("ready"))
    tokens.CX4_PHYSICAL_PERIPHERAL_PACKET_READY = bool(packets.get("peripherals", {}).get("ready"))
    tokens.CX4_EVT_PACKET_READY = bool(packets.get("device_quartet", {}).get("ready"))
    tokens.CX4_DVT_PACKET_READY = bool(packets.get("device_quartet", {}).get("ready"))
    tokens.CX4_PVT_PACKET_READY = bool(packets.get("device_quartet", {}).get("ready"))
    tokens.CX4_FIRMWARE_LIFECYCLE_PACKET_READY = bool(packets.get("firmware", {}).get("ready"))
    tokens.CX4_SUPPORT_BUNDLE_READY = bool(packets.get("support_repair", {}).get("ready"))
    tokens.CX4_REPAIR_RMA_PACKET_READY = bool(packets.get("support_repair", {}).get("ready"))
    tokens.CX4_CHAT_MEETING_PROVIDER_READINESS_PASS = bool(
        packets.get("chat_meeting", {}).get("CX4_CHAT_MEETING_PROVIDER_READINESS_PASS")
    )
    tokens.CX4_EXTERNAL_ISSUER_PACKET_READY = bool(packets.get("issuer", {}).get("ready"))
    tokens.CX4_PRIVACY_REVIEW_PACKET_READY = bool(packets.get("privacy_rights", {}).get("ready"))
    tokens.CX4_RIGHTS_REGISTER_READY = bool(packets.get("privacy_rights", {}).get("ready"))
    tokens.CX4_CERTIFICATION_MATRIX_READY = bool(packets.get("cert_mfg", {}).get("ready"))
    tokens.CX4_MANUFACTURING_PACKET_READY = bool(packets.get("cert_mfg", {}).get("ready"))

    reg = write_master_register(repo)
    facts["blocker_register_path"] = reg.get("register_path")
    facts["edmund"] = reg.get("edmund")
    tokens.CX4_OWNER_ACTION_PACKET_READY = bool(reg.get("edmund", {}).get("ready"))

    tokens.J6_CLASS = "HUMAN_VALIDATION_PENDING"
    tokens.PHYSICAL_PRINTER_PENDING = True
    tokens.PHYSICAL_CAMERA_MIC_AV_PENDING = True
    tokens.EVT_PENDING = True
    tokens.DVT_PENDING = True
    tokens.PVT_PENDING = True
    tokens.FULL_COMPLETE_EXPERIENCE_COMPLETE = False

    report = write_evidence(repo, tokens, facts)
    (ensure_lab_tree(repo) / "evidence" / "last_report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CX4.0 human/physical/external readiness")
    parser.add_argument("--repo", type=Path, default=None)
    parser.add_argument("--no-guest", action="store_true")
    parser.add_argument("--skip-smoke", action="store_true")
    parser.add_argument("--print-report", action="store_true")
    args = parser.parse_args(argv)
    repo = args.repo or repo_root_from_here()
    report = run_cx4(repo, try_guest=not args.no_guest, skip_smoke=args.skip_smoke)
    tokens = report.get("tokens") or {}
    summary = {
        "CX4_CURRENT_TIP_GUEST_OVERLAY_PASS": tokens.get("CX4_CURRENT_TIP_GUEST_OVERLAY_PASS"),
        "CX4_CURRENT_TIP_GUEST_SMOKE_PASS": tokens.get("CX4_CURRENT_TIP_GUEST_SMOKE_PASS"),
        "CX4_ALL_AUTOMATABLE_NON_DIGITAL_PREWORK_PASS": tokens.get(
            "CX4_ALL_AUTOMATABLE_NON_DIGITAL_PREWORK_PASS"
        ),
        "NEXT_CX_GATE": report.get("NEXT_CX_GATE"),
        "FULL_COMPLETE_EXPERIENCE_COMPLETE": False,
        "evidence": str(evidence_root(repo)),
    }
    print(json.dumps(report if args.print_report else summary, indent=2))
    return 0 if tokens.get("CX4_ALL_AUTOMATABLE_NON_DIGITAL_PREWORK_PASS") else 1


if __name__ == "__main__":
    raise SystemExit(main())
