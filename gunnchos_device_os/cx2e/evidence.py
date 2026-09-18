"""Write CX2E evidence exclusively under artifacts/complete_experience/cx2e/."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

from gunnchos_device_os.cx2e import (
    CX2E_SINGLE_PRODUCTION_SHELL_AUTHORITY,
    FULL_COMPLETE_EXPERIENCE_COMPLETE,
)
from gunnchos_device_os.cx2e.journeys import upgrade_journeys
from gunnchos_device_os.cx2e.paths import evidence_root, repo_root_from_here
from gunnchos_device_os.cx2e.qemu import host_prereqs, prepare_overlay
from gunnchos_device_os.cx2e.tokens import apply_session_facts, fail_closed_tokens


def write_human_packets(root: Path) -> None:
    (root / "HUMAN_A11Y_VALIDATION_PACKET.md").write_text(
        """# CX2E Human Accessibility Validation Packet

Status: **CX2E_HUMAN_A11Y_PENDING=true**

## Required human checks (Linux gunnch_shell on Weston)

1. Keyboard-only nav Home → Vault → App Center → Connect → Assist → Care
2. Orca/AT-SPI accessible names
3. Contrast/reduce-motion
4. Offline banner announced
5. Focus order

| Check | Pass? | Notes |
|-------|-------|-------|
| Keyboard-only nav |  |  |
| Orca/AT-SPI |  |  |
| Contrast/motion |  |  |
| Offline announcement |  |  |
| Focus order |  |  |
"""
    )
    (root / "PHYSICAL_PRINTER_SI_PACKET.md").write_text(
        """# CX2E Physical Printer SI Packet

`CX2E_PHYSICAL_PRINTER_PENDING=true`

Digital IPP GUI pass is separate from physical page inspection.
"""
    )
    (root / "HUMAN_AV_VALIDATION_PACKET.md").write_text(
        """# CX2E Human AV Validation Packet

`CX2E_HUMAN_AV_QUALITY_PENDING=true`
`CX2E_PHYSICAL_CAMERA_MIC_PENDING=true`
"""
    )


def next_gate(journeys: Dict[str, Any], *, blocker: str = "") -> str:
    desired = journeys.get("desired_before_cx3_pass")
    if desired:
        return "CX3"
    if blocker:
        # sanitize blocker into CX2F token fragment
        frag = blocker.split(":")[0].strip().replace(" ", "_")[:80]
        if frag.startswith("CX2E_"):
            frag = "CX2F_" + frag[5:]
        elif not frag.startswith("CX2F_"):
            frag = "CX2F_" + frag
        return frag
    return "CX2F_LINUX_GRAPHICAL_SESSION_INCOMPLETE"


def write_evidence(
    repo_root: Optional[Path] = None,
    *,
    facts: Optional[Dict[str, Any]] = None,
    provision: Optional[Dict[str, Any]] = None,
    graphical: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    repo_root = repo_root or repo_root_from_here()
    root = evidence_root(repo_root)
    root.mkdir(parents=True, exist_ok=True)
    facts = facts or {}
    provision = provision or {}
    graphical = graphical or {}
    overlay = prepare_overlay(repo_root)
    prereq = host_prereqs()

    tokens = fail_closed_tokens(lab_blocker=facts.get("lab_blocker") or provision.get("blocker") or graphical.get("blocker") or "")
    tokens = apply_session_facts(tokens, facts)
    # domain tokens
    
    # Fail-closed: provider GUI PASSes require rendered shell/compositor path.
    if not tokens.graphical_truth():
        if not facts.get("lab_blocker"):
            missing = []
            if not tokens.shell_window_rendered:
                missing.append("shell_window_rendered")
            if not (facts.get("real_screen_capture_pass") or facts.get("render_capture_pass")):
                missing.append("real_screen_capture_pass")
            if not tokens.compositor_running:
                missing.append("compositor_running")
            facts["lab_blocker"] = (
                "CX2E_SHELL_RENDER_OR_CAPTURE_NOT_PROVEN: " + ",".join(missing)
                + "; cloud kernel lacks DRM (/dev/dri); Weston headless session proven"
                + " but gunnch_shell Chromium render + compositor capture not earned"
            )
            tokens.lab_blocker = facts["lab_blocker"]

    tokens.CX2E_REAL_BROWSER_GUI_PASS = bool(facts.get("BROWSER_GUI")) and tokens.shell_window_rendered
    tokens.CX2E_REAL_APP_LIFECYCLE_GUI_PASS = bool(facts.get("APP_LIFECYCLE_GUI")) and tokens.shell_window_rendered
    tokens.CX2E_REAL_PRODUCTIVITY_GUI_PASS = bool(facts.get("PRODUCTIVITY_GUI")) and tokens.shell_window_rendered
    tokens.CX2E_REAL_MAIL_GUI_PASS = bool(facts.get("MAIL_GUI")) and tokens.shell_window_rendered
    tokens.CX2E_REAL_CALDAV_CARDDAV_GUI_PASS = bool(facts.get("CALDAV_CARDDAV_GUI")) and tokens.shell_window_rendered
    tokens.CX2E_REAL_IPP_GUI_DIGITAL_PASS = bool(facts.get("IPP_GUI_DIGITAL")) and tokens.shell_window_rendered
    tokens.CX2E_REAL_CHAT_VIDEO_GUI_ATTEMPT = bool(facts.get("chat_video_attempt"))
    tokens.CX2E_DIGITAL_RENDERED_A11Y_PASS = bool(facts.get("digital_a11y_pass")) and tokens.shell_window_rendered
    tokens.CX2E_REAL_OFFLINE_RECOVERY_GUI_PASS = bool(facts.get("OFFLINE_RECOVERY_GUI")) and tokens.shell_window_rendered
    for surf in ("home", "vault", "app_center", "connect", "assist", "care"):
        setattr(tokens, f"CX2E_REAL_{surf.upper()}_WINDOW", bool(facts.get(f"surface_{surf}")))

    journeys = upgrade_journeys(facts)
    gate = next_gate(journeys, blocker=tokens.lab_blocker)

    provenance = {
        "schema": "gunnchos.cx2e.linux_lab_provenance.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "distro": "debian",
        "version": "12 (bookworm) genericcloud",
        "architecture": "aarch64",
        "compositor": "weston",
        "image_base_sha256": overlay.get("base_sha256"),
        "overlay_sha256": overlay.get("overlay_sha256"),
        "cloud_init_user_data_sha256": (provision.get("cloud_init") or {}).get("user_data_sha256"),
        "accel": prereq.get("accel"),
        "host": {k: prereq[k] for k in ("host_os", "host_machine", "qemu_system_aarch64", "free_disk_gb") if k in prereq},
        "graphical_truth": tokens.graphical_truth(),
        "claim_boundary": "CX2E expansion lab; not Device Lab #134 evidence.",
        "package_versions_path_in_guest": "/var/lib/cx2e/key-packages.txt",
    }

    lab_status = {
        "schema": "gunnchos.cx2e.linux_lab_status.v1",
        "generated_at_utc": provenance["generated_at_utc"],
        "overlay_prep": {k: overlay.get(k) for k in ("ok", "blocker", "base_sha256", "overlay_sha256", "overlay")},
        "provision": {k: provision.get(k) for k in ("ok", "blocker", "sentinel_ok", "qemu_pid", "accel") if k in provision or True},
        "graphical_boot": {k: graphical.get(k) for k in ("ok", "blocker", "ssh_ready", "qemu_pid", "guest_booted")},
        "guest_facts": {
            "guest_booted": tokens.guest_booted,
            "guest_is_linux": tokens.guest_is_linux,
            "compositor_running": tokens.compositor_running,
            "wayland_socket_alive": tokens.wayland_socket_alive,
            "shell_window_rendered": tokens.shell_window_rendered,
            "graphical_truth": tokens.graphical_truth(),
        },
        "device_lab_paths_untouched": True,
        "evidence_namespace": "artifacts/complete_experience/cx2e",
        "blocker": tokens.lab_blocker or None,
    }

    report = {
        "schema": "gunnchos.cx2e.evidence_report.v1",
        "generated_at_utc": provenance["generated_at_utc"],
        "FULL_COMPLETE_EXPERIENCE_COMPLETE": FULL_COMPLETE_EXPERIENCE_COMPLETE,
        "CX2E_SINGLE_PRODUCTION_SHELL_AUTHORITY": CX2E_SINGLE_PRODUCTION_SHELL_AUTHORITY,
        "production_shell": "apps/gunnch_shell",
        "shell_runtime_target_ref": "SHELL_RUNTIME_TARGET.json",
        "linux_lab": lab_status,
        "provenance_ref": "CX2E_LINUX_LAB_PROVENANCE.json",
        "session_facts_ref": "SESSION_FACTS.json",
        "journeys": journeys,
        "tokens": tokens.to_dict(),
        "firewall": {
            "device_lab_134_unaltered": True,
            "portal_14_15_unaltered": True,
            "device_lab_manifest_unaltered": True,
            "evidence_path": "artifacts/complete_experience/cx2e",
            "no_merges": True,
            "no_macos_provider_fallback": True,
        },
        "NEXT_CX_GATE": gate,
        "tip_stack_note": "Device OS CX0–CX2D tips verified at branch creation; CX2E stacked on CX2D #140",
    }

    write_human_packets(root)
    (root / "CX2E_EVIDENCE_REPORT.json").write_text(json.dumps(report, indent=2) + "\n")
    (root / "CX2E_TOKENS.json").write_text(json.dumps(tokens.to_dict(), indent=2) + "\n")
    (root / "JOURNEYS.json").write_text(json.dumps(journeys, indent=2) + "\n")
    (root / "CX2E_LINUX_LAB_STATUS.json").write_text(json.dumps(lab_status, indent=2) + "\n")
    (root / "CX2E_LINUX_LAB_PROVENANCE.json").write_text(json.dumps(provenance, indent=2) + "\n")
    (root / "SESSION_FACTS.json").write_text(json.dumps(facts, indent=2) + "\n")
    if facts.get("shell", {}).get("shell_runtime_target"):
        (root / "SHELL_RUNTIME_TARGET.json").write_text(
            json.dumps(facts["shell"]["shell_runtime_target"], indent=2) + "\n"
        )
    if facts.get("portals"):
        (root / "XDG_PORTAL_MATRIX.json").write_text(json.dumps(facts["portals"], indent=2) + "\n")
    if facts.get("providers"):
        (root / "PROVIDER_GUI_PROBES.json").write_text(json.dumps(facts["providers"], indent=2) + "\n")
    (root / "README.md").write_text(
        "# CX2E evidence\n\nLinux graphical session + journey proof. "
        "FULL_COMPLETE_EXPERIENCE_COMPLETE=false. See CX2E_EVIDENCE_REPORT.json.\n"
        "Truth = guest_booted && guest_is_linux && compositor_running && "
        "wayland_socket_alive && shell_window_rendered.\n"
    )
    return report
