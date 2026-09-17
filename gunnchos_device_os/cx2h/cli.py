"""CX2H.1 CLI — portal session + J3 App Center lifecycle."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Dict

from gunnchos_device_os.cx2h.evidence import write_evidence
from gunnchos_device_os.cx2h.flatpak_repo import build_flatpak_repo
from gunnchos_device_os.cx2h.j3 import run_j3_journey
from gunnchos_device_os.cx2h.paths import ensure_lab_tree, evidence_root, repo_root_from_here
from gunnchos_device_os.cx2h.portals import diagnose_portal_gap, repair_and_prove_portals
from gunnchos_device_os.cx2h.qemu import prepare_overlay, start_graphical_guest, stop_guest
from gunnchos_device_os.cx2h.session import deploy_app_center_provider, re_prove_shell_prereqs
from gunnchos_device_os.cx2h.tokens import Cx2hTokens


def run_cx2h1(repo: Path) -> Dict[str, Any]:
    tokens = Cx2hTokens()
    facts: Dict[str, Any] = {
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "wave": "CX2H.1",
    }
    lab = ensure_lab_tree(repo)
    captures = Path("/tmp/cx2h-graphical/captures")
    captures.mkdir(parents=True, exist_ok=True)

    overlay = prepare_overlay(repo)
    facts["overlay"] = overlay
    if not overlay.get("ok"):
        tokens.lab_blocker = overlay.get("blocker") or "CX2H_OVERLAY_FAIL"
        return write_evidence(repo, tokens, facts)

    graphical = start_graphical_guest(repo)
    facts["graphical"] = {k: graphical.get(k) for k in graphical if k != "qemu_cmd"}
    tokens.guest_booted = bool(graphical.get("guest_booted"))
    if not graphical.get("ok"):
        tokens.lab_blocker = graphical.get("blocker") or "CX2H_GRAPHICAL_BOOT_FAILED"
        try:
            stop_guest(repo)
        except Exception:
            pass
        return write_evidence(repo, tokens, facts)
    tokens.guest_is_linux = True
    monitor = Path(graphical["runtime"]["monitor"])

    # 1. Shell prereqs
    prereq = re_prove_shell_prereqs(repo, monitor, captures)
    facts["CX2H_SHELL_PREREQ"] = prereq
    tokens.CX2H_SHELL_PREREQ_PASS = bool(prereq.get("CX2H_SHELL_PREREQ_PASS"))
    tokens.CX2H_CHROMIUM_RUNTIME_PASS = bool(prereq.get("CX2H_CHROMIUM_RUNTIME_PASS"))
    tokens.CX2H_WAYLAND_SURFACE_PASS = bool(prereq.get("CX2H_WAYLAND_SURFACE_PASS"))
    tokens.CX2H_GUNNCH_SHELL_RENDER_PASS = bool(prereq.get("CX2H_GUNNCH_SHELL_RENDER_PASS"))
    tokens.CX2H_QEMU_FRAMEBUFFER_CAPTURE_PASS = bool(prereq.get("CX2H_QEMU_FRAMEBUFFER_CAPTURE_PASS"))
    tokens.CX2H_REAL_INPUT_TO_SHELL_MUTATION_PASS = bool(prereq.get("CX2H_REAL_INPUT_TO_SHELL_MUTATION_PASS"))
    tokens.CX2H_REAL_APP_CENTER_WINDOW = bool(prereq.get("CX2H_REAL_APP_CENTER_WINDOW"))
    if not tokens.gate_shell_prereq():
        tokens.lab_blocker = prereq.get("blocker") or "CX2H_SHELL_PREREQ_FAILED"
        stop_guest(repo)
        return write_evidence(repo, tokens, facts)

    # 2. Portal repair
    portals = repair_and_prove_portals(repo)
    facts["CX2H_PORTAL_ROOT_CAUSE"] = portals.get("diagnosis") or diagnose_portal_gap(repo)
    facts["CX2H_XDG_PORTAL_MATRIX"] = portals
    tokens.CX2H_XDG_PORTAL_SESSION_PASS = bool(portals.get("CX2H_XDG_PORTAL_SESSION_PASS"))
    if not tokens.CX2H_XDG_PORTAL_SESSION_PASS:
        tokens.lab_blocker = portals.get("blocker") or "CX2H_XDG_PORTAL_SESSION_NOT_PROVEN"
        stop_guest(repo)
        return write_evidence(repo, tokens, facts)

    # 3. Flatpak repo
    provenance = build_flatpak_repo(repo)
    facts["CX2H_FLATPAK_REPO_PROVENANCE"] = provenance
    if not provenance.get("build_ok"):
        tokens.lab_blocker = provenance.get("blocker") or "CX2H_FLATPAK_REPO_BUILD_FAILED"
        stop_guest(repo)
        return write_evidence(repo, tokens, facts)

    # 4. Provider API
    provider = deploy_app_center_provider(repo)
    facts["app_center_provider"] = provider
    if not provider.get("ok"):
        tokens.lab_blocker = "CX2H_APP_CENTER_PROVIDER_API"
        stop_guest(repo)
        return write_evidence(repo, tokens, facts)

    # 5–6. J3 journey
    j3 = run_j3_journey(repo, monitor, captures)
    facts["CX2H_J3_APP_CENTER_JOURNEY"] = j3
    tok = j3.get("tokens") or {}
    tokens.CX2H_REAL_APP_CENTER_PROVIDER_PASS = bool(tok.get("CX2H_REAL_APP_CENTER_PROVIDER_PASS"))
    tokens.CX2H_REAL_APP_INSTALL_GUI_PASS = bool(tok.get("CX2H_REAL_APP_INSTALL_GUI_PASS"))
    tokens.CX2H_REAL_APP_LAUNCH_GUI_PASS = bool(tok.get("CX2H_REAL_APP_LAUNCH_GUI_PASS"))
    tokens.CX2H_REAL_APP_UPDATE_GUI_PASS = bool(tok.get("CX2H_REAL_APP_UPDATE_GUI_PASS"))
    tokens.CX2H_REAL_APP_ROLLBACK_GUI_PASS = bool(tok.get("CX2H_REAL_APP_ROLLBACK_GUI_PASS"))
    tokens.CX2H_REAL_APP_UNINSTALL_GUI_PASS = bool(tok.get("CX2H_REAL_APP_UNINSTALL_GUI_PASS"))
    tokens.CX2H_J3_PERSISTENCE_PASS = bool(tok.get("CX2H_J3_PERSISTENCE_PASS"))
    tokens.J3_CLASS = j3.get("J3_CLASS") or "BLOCKED"

    facts["FRAMEBUFFER_DIFF_REPORT"] = {
        "v1": (j3.get("steps") or {}).get("diff_v1"),
        "v1_v2": (j3.get("steps") or {}).get("diff_v1_v2"),
        "noise_calibration": {
            "v1_min_changed_pct": 0.5,
            "v1_v2_min_changed_pct": 0.5,
            "baseline_pair": "after_install_vs_launch_v1 (not app_center_vs_launch)",
            "note": "Thresholds not lowered; compare against same App Center chrome so install UI churn cannot fake a window",
        },
    }
    facts["CX2H_FRAMEBUFFER_CAPTURE_MANIFEST"] = {
        "dir": str(captures),
        "frames": sorted(p.name for p in captures.glob("j3_*.ppm")),
    }
    facts["CX2H1B_WINDOW_PROOF_V1"] = (j3.get("steps") or {}).get("window_proof_v1")
    facts["CX2H1B_WINDOW_PROOF_V2"] = (j3.get("steps") or {}).get("window_proof_v2")
    facts["CX2H1B_PROVIDER_LAUNCH_RESULT"] = {
        "v1": (j3.get("steps") or {}).get("provider_launch_v1"),
        "v2": (j3.get("steps") or {}).get("provider_launch_v2"),
    }
    review_path = evidence_root(repo) / "CX2H1B_J3_EVIDENCE_REVIEW.json"
    if review_path.is_file():
        try:
            facts["CX2H1B_J3_EVIDENCE_REVIEW"] = json.loads(review_path.read_text())
        except Exception:
            pass
    rc_path = evidence_root(repo) / "CX2H1B_FLATPAK_LAUNCH_ROOT_CAUSE.json"
    if rc_path.is_file():
        try:
            facts["CX2H1B_FLATPAK_LAUNCH_ROOT_CAUSE"] = json.loads(rc_path.read_text())
        except Exception:
            pass

    if tokens.J3_CLASS != "REAL_USER_JOURNEY_DIGITAL_PASS":
        tokens.lab_blocker = j3.get("blocker") or "CX2H_J3_INCOMPLETE"

    report = write_evidence(repo, tokens, facts)
    # Copy captures into lab
    lab_cap = lab / "captures"
    lab_cap.mkdir(parents=True, exist_ok=True)
    for ppm in captures.glob("*.ppm"):
        dest = lab_cap / ppm.name
        try:
            dest.write_bytes(ppm.read_bytes())
        except Exception:
            pass
    stop_guest(repo)
    return report


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="python -m gunnchos_device_os.cx2h")
    p.add_argument("--repo", type=Path, default=None)
    p.add_argument("--prepare-only", action="store_true")
    p.add_argument("--cx2h1", action="store_true", help="Run CX2H.1 portal + J3 lifecycle")
    p.add_argument("--shutdown", action="store_true")
    args = p.parse_args(argv)
    repo = args.repo or repo_root_from_here()

    if args.shutdown:
        print(json.dumps(stop_guest(repo), indent=2))
        return 0
    if args.prepare_only:
        ov = prepare_overlay(repo)
        print(json.dumps(ov, indent=2))
        return 0 if ov.get("ok") else 1
    if args.cx2h1:
        report = run_cx2h1(repo)
        tok = report.get("tokens") or {}
        print("NEXT_CX_GATE=", report.get("NEXT_CX_GATE"))
        print("FULL_COMPLETE_EXPERIENCE_COMPLETE=", report.get("FULL_COMPLETE_EXPERIENCE_COMPLETE"))
        for k in (
            "CX2H_XDG_PORTAL_SESSION_PASS",
            "CX2H_REAL_APP_CENTER_PROVIDER_PASS",
            "CX2H_REAL_APP_INSTALL_GUI_PASS",
            "CX2H_REAL_APP_UPDATE_GUI_PASS",
            "CX2H_REAL_APP_ROLLBACK_GUI_PASS",
            "CX2H_REAL_APP_UNINSTALL_GUI_PASS",
            "J3_CLASS",
        ):
            print(f"{k}={tok.get(k)}")
        print("evidence=", evidence_root(repo))
        return 0 if tok.get("J3_CLASS") == "REAL_USER_JOURNEY_DIGITAL_PASS" else 1

    p.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
