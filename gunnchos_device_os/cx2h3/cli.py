"""CX2H.3 CLI — browser/mail/offline J2 + J5."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Dict

from gunnchos_device_os.cx2h3 import host_providers as hp
from gunnchos_device_os.cx2h3.evidence import write_evidence
from gunnchos_device_os.cx2h3.j2_j5 import run_j2_j5
from gunnchos_device_os.cx2h3.paths import ensure_lab_tree, evidence_root, repo_root_from_here
from gunnchos_device_os.cx2h3.qemu import prepare_overlay, start_graphical_guest, stop_guest
from gunnchos_device_os.cx2h3.session import deploy_cx2h3_provider, prerequisite_rebind
from gunnchos_device_os.cx2h3.tokens import Cx2h3Tokens


def run_cx2h3(repo: Path) -> Dict[str, Any]:
    tokens = Cx2h3Tokens()
    facts: Dict[str, Any] = {
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "wave": "CX2H.3",
    }
    lab = ensure_lab_tree(repo)
    captures = Path("/tmp/cx2h3-graphical/captures")
    captures.mkdir(parents=True, exist_ok=True)

    overlay = prepare_overlay(repo)
    facts["overlay"] = overlay
    if not overlay.get("ok"):
        tokens.lab_blocker = overlay.get("blocker") or "CX2H3_OVERLAY_FAIL"
        return write_evidence(repo, tokens, facts)

    # Host providers before guest (guest reaches via 10.0.2.2)
    https = hp.start_https(repo)
    facts["CX2H3_HTTPS_PROVIDER_PROVENANCE"] = https
    tokens.CX2H3_REAL_HTTPS_PROVIDER_PASS = bool(https.get("ok") and not https.get("ignore_certificate_errors"))
    mail = hp.start_mail(repo)
    facts["CX2H3_MAIL_PROVIDER_PROVENANCE"] = mail
    tokens.CX2H3_REAL_SMTP_IMAP_PROVIDER_PASS = bool(mail.get("ok") and not mail.get("json_fixture"))

    graphical = start_graphical_guest(repo)
    facts["graphical"] = {k: graphical.get(k) for k in graphical if k != "qemu_cmd"}
    tokens.guest_booted = bool(graphical.get("guest_booted"))
    if not graphical.get("ok"):
        tokens.lab_blocker = graphical.get("blocker") or "CX2H3_GRAPHICAL_BOOT_FAILED"
        try:
            stop_guest(repo)
        except Exception:
            pass
        hp.stop_https()
        hp.stop_mail()
        return write_evidence(repo, tokens, facts)
    tokens.guest_is_linux = True
    monitor = Path(graphical["runtime"]["monitor"])

    prereq = prerequisite_rebind(repo, monitor, captures)
    facts["CX2H3_PREREQUISITE_REBIND"] = prereq
    tokens.CX2H3_PREREQUISITE_PASS = bool(prereq.get("CX2H3_PREREQUISITE_PASS"))
    tokens.J1_CLASS = prereq.get("J1_CLASS") or "BLOCKED"
    tokens.J3_CLASS = prereq.get("J3_CLASS") or "BLOCKED"
    tokens.J7_CLASS = prereq.get("J7_CLASS") or "BLOCKED"
    tokens.CX2H_SHELL_PREREQ_PASS = bool(prereq.get("CX2H_SHELL_PREREQ_PASS"))
    tokens.CX2H_XDG_PORTAL_SESSION_PASS = bool(prereq.get("CX2H_XDG_PORTAL_SESSION_PASS"))
    tokens.CX2H2_REAL_WRITER_GUI_PASS = bool(prereq.get("CX2H2_REAL_WRITER_GUI_PASS"))
    tokens.CX2H2_REAL_VAULT_FILE_PASS = bool(prereq.get("CX2H2_REAL_VAULT_FILE_PASS"))
    if not tokens.CX2H3_PREREQUISITE_PASS:
        tokens.lab_blocker = prereq.get("blocker") or "CX2H3_PREREQUISITE"
        tokens.J2_CLASS = "REAL_PROVIDER_GUI_PARTIAL"
        tokens.J5_CLASS = "REAL_PROVIDER_GUI_PARTIAL"
        stop_guest(repo)
        hp.stop_https()
        hp.stop_mail()
        return write_evidence(repo, tokens, facts)

    provider = deploy_cx2h3_provider(repo)
    facts["cx2h3_provider"] = provider
    if not provider.get("ok"):
        tokens.lab_blocker = provider.get("blocker") or "CX2H3_PROVIDER"
        tokens.J2_CLASS = "REAL_PROVIDER_GUI_PARTIAL"
        tokens.J5_CLASS = "REAL_PROVIDER_GUI_PARTIAL"
        stop_guest(repo)
        hp.stop_https()
        hp.stop_mail()
        return write_evidence(repo, tokens, facts)

    journey = run_j2_j5(repo, monitor, captures)
    for key, val in (journey.get("facts") or {}).items():
        facts[key] = val
    tok = journey.get("tokens") or {}
    for name, val in tok.items():
        if hasattr(tokens, name):
            setattr(tokens, name, bool(val))
    tokens.J2_CLASS = journey.get("J2_CLASS") or "REAL_PROVIDER_GUI_PARTIAL"
    tokens.J5_CLASS = journey.get("J5_CLASS") or "REAL_PROVIDER_GUI_PARTIAL"
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
    # leave host providers stopped after run
    hp.stop_https()
    hp.stop_mail()
    return report


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="python -m gunnchos_device_os.cx2h3")
    p.add_argument("--repo", type=Path, default=None)
    args = p.parse_args(argv)
    repo = args.repo or repo_root_from_here()
    report = run_cx2h3(repo)
    print(json.dumps({"NEXT_CX_GATE": report.get("NEXT_CX_GATE"), "tokens": report.get("tokens")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
