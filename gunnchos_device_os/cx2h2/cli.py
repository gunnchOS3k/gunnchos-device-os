"""CX2H.2 CLI — document/print/recovery J1 + J7."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Dict

from gunnchos_device_os.cx2h2.evidence import write_evidence
from gunnchos_device_os.cx2h2.j1_j7 import run_j1_j7
from gunnchos_device_os.cx2h2.paths import ensure_lab_tree, evidence_root, repo_root_from_here
from gunnchos_device_os.cx2h2.qemu import prepare_overlay, start_graphical_guest, stop_guest
from gunnchos_device_os.cx2h2.session import deploy_vault_provider, re_prove_shell_and_j3_tokens
from gunnchos_device_os.cx2h2.tokens import Cx2h2Tokens


def run_cx2h2(repo: Path) -> Dict[str, Any]:
    tokens = Cx2h2Tokens()
    facts: Dict[str, Any] = {
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "wave": "CX2H.2",
    }
    lab = ensure_lab_tree(repo)
    captures = Path("/tmp/cx2h2-graphical/captures")
    captures.mkdir(parents=True, exist_ok=True)

    overlay = prepare_overlay(repo)
    facts["overlay"] = overlay
    if not overlay.get("ok"):
        tokens.lab_blocker = overlay.get("blocker") or "CX2H2_OVERLAY_FAIL"
        return write_evidence(repo, tokens, facts)

    graphical = start_graphical_guest(repo)
    facts["graphical"] = {k: graphical.get(k) for k in graphical if k != "qemu_cmd"}
    tokens.guest_booted = bool(graphical.get("guest_booted"))
    if not graphical.get("ok"):
        tokens.lab_blocker = graphical.get("blocker") or "CX2H2_GRAPHICAL_BOOT_FAILED"
        try:
            stop_guest(repo)
        except Exception:
            pass
        return write_evidence(repo, tokens, facts)
    tokens.guest_is_linux = True
    monitor = Path(graphical["runtime"]["monitor"])

    prereq = re_prove_shell_and_j3_tokens(repo, monitor, captures)
    facts["CX2H2_SHELL_J3_PREREQ"] = prereq
    tokens.CX2H_SHELL_PREREQ_PASS = bool(prereq.get("CX2H_SHELL_PREREQ_PASS"))
    tokens.CX2H_CHROMIUM_RUNTIME_PASS = bool(prereq.get("CX2H_CHROMIUM_RUNTIME_PASS"))
    tokens.CX2H_WAYLAND_SURFACE_PASS = bool(prereq.get("CX2H_WAYLAND_SURFACE_PASS"))
    tokens.CX2H_GUNNCH_SHELL_RENDER_PASS = bool(prereq.get("CX2H_GUNNCH_SHELL_RENDER_PASS"))
    tokens.CX2H_QEMU_FRAMEBUFFER_CAPTURE_PASS = bool(prereq.get("CX2H_QEMU_FRAMEBUFFER_CAPTURE_PASS"))
    tokens.CX2H_REAL_INPUT_TO_SHELL_MUTATION_PASS = bool(prereq.get("CX2H_REAL_INPUT_TO_SHELL_MUTATION_PASS"))
    tokens.CX2H_REAL_APP_CENTER_WINDOW = bool(prereq.get("CX2H_REAL_APP_CENTER_WINDOW"))
    tokens.CX2H_XDG_PORTAL_SESSION_PASS = bool(prereq.get("CX2H_XDG_PORTAL_SESSION_PASS"))
    tokens.J3_CLASS = prereq.get("J3_CLASS") or "BLOCKED"
    if not tokens.gate_shell_prereq():
        tokens.lab_blocker = prereq.get("blocker") or "CX2H2_SHELL_OR_J3_REGRESSION"
        tokens.J1_CLASS = "REAL_PROVIDER_GUI_PARTIAL"
        tokens.J7_CLASS = "REAL_PROVIDER_GUI_PARTIAL"
        stop_guest(repo)
        return write_evidence(repo, tokens, facts)

    provider = deploy_vault_provider(repo)
    facts["vault_provider"] = provider
    if not provider.get("ok"):
        tokens.lab_blocker = provider.get("blocker") or "CX2H2_VAULT_PROVIDER_API"
        tokens.J1_CLASS = "REAL_PROVIDER_GUI_PARTIAL"
        tokens.J7_CLASS = "REAL_PROVIDER_GUI_PARTIAL"
        stop_guest(repo)
        return write_evidence(repo, tokens, facts)

    journey = run_j1_j7(repo, monitor, captures)
    for key in (
        "CX2H2_WRITER_GUI_PROOF",
        "CX2H2_VAULT_FILE_PROVIDER_PROOF",
        "CX2H2_PDF_EXPORT_GUI_PROOF",
        "CX2H2_IPP_PRINTER_PROVENANCE",
        "CX2H2_PRINT_GUI_JOURNEY",
        "CX2H2_BACKUP_GUI_PROOF",
        "CX2H2_DESTRUCTIVE_EVENT",
        "CX2H2_RESTORE_GUI_PROOF",
        "CX2H2_PERSISTENCE_READBACK",
        "CX2H2_A11Y_NOTES",
        "CX2H2_J1_JOURNEY",
        "CX2H2_J7_JOURNEY",
    ):
        if key in journey:
            facts[key] = journey[key]

    tok = journey.get("tokens") or {}
    tokens.CX2H2_REAL_WRITER_GUI_PASS = bool(tok.get("CX2H2_REAL_WRITER_GUI_PASS"))
    tokens.CX2H2_REAL_VAULT_FILE_PASS = bool(tok.get("CX2H2_REAL_VAULT_FILE_PASS"))
    tokens.CX2H2_REAL_PDF_EXPORT_GUI_PASS = bool(tok.get("CX2H2_REAL_PDF_EXPORT_GUI_PASS"))
    tokens.CX2H2_REAL_IPP_PROVIDER_PASS = bool(tok.get("CX2H2_REAL_IPP_PROVIDER_PASS"))
    tokens.CX2H2_REAL_IPP_PRINT_GUI_PASS = bool(tok.get("CX2H2_REAL_IPP_PRINT_GUI_PASS"))
    tokens.CX2H2_REAL_BACKUP_GUI_PASS = bool(tok.get("CX2H2_REAL_BACKUP_GUI_PASS"))
    tokens.CX2H2_REAL_RESTORE_GUI_PASS = bool(tok.get("CX2H2_REAL_RESTORE_GUI_PASS"))
    tokens.CX2H2_PERSISTENCE_PASS = bool(tok.get("CX2H2_PERSISTENCE_PASS"))
    tokens.J1_CLASS = journey.get("J1_CLASS") or "REAL_PROVIDER_GUI_PARTIAL"
    tokens.J7_CLASS = journey.get("J7_CLASS") or "REAL_PROVIDER_GUI_PARTIAL"
    if journey.get("blocker"):
        tokens.lab_blocker = journey["blocker"]

    report = write_evidence(repo, tokens, facts)
    lab_cap = lab / "captures"
    lab_cap.mkdir(parents=True, exist_ok=True)
    for ppm in captures.glob("*.ppm"):
        try:
            (lab_cap / ppm.name).write_bytes(ppm.read_bytes())
        except Exception:
            pass
    stop_guest(repo)
    return report


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="python -m gunnchos_device_os.cx2h2")
    p.add_argument("--repo", type=Path, default=None)
    p.add_argument("--prepare-only", action="store_true")
    p.add_argument("--cx2h2", action="store_true", help="Run CX2H.2 J1+J7 journeys")
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
    if args.cx2h2:
        report = run_cx2h2(repo)
        tok = report.get("tokens") or {}
        print("NEXT_CX_GATE=", report.get("NEXT_CX_GATE"))
        print("FULL_COMPLETE_EXPERIENCE_COMPLETE=", report.get("FULL_COMPLETE_EXPERIENCE_COMPLETE"))
        for k in (
            "CX2H2_REAL_WRITER_GUI_PASS",
            "CX2H2_REAL_VAULT_FILE_PASS",
            "CX2H2_REAL_PDF_EXPORT_GUI_PASS",
            "CX2H2_REAL_IPP_PROVIDER_PASS",
            "CX2H2_REAL_IPP_PRINT_GUI_PASS",
            "CX2H2_REAL_BACKUP_GUI_PASS",
            "CX2H2_REAL_RESTORE_GUI_PASS",
            "CX2H2_PHYSICAL_PRINTER_PENDING",
            "J1_CLASS",
            "J3_CLASS",
            "J7_CLASS",
            "J2_CLASS",
            "J5_CLASS",
            "J6_CLASS",
        ):
            print(f"{k}={tok.get(k)}")
        print("lab_blocker=", tok.get("lab_blocker") or report.get("lab_blocker"))
        print("evidence=", evidence_root(repo))
        j1 = tok.get("J1_CLASS") == "REAL_USER_JOURNEY_DIGITAL_PASS"
        j7 = tok.get("J7_CLASS") == "REAL_USER_JOURNEY_DIGITAL_PASS"
        return 0 if j1 and j7 else 1

    p.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
