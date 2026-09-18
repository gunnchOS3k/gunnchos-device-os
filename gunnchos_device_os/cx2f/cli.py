"""CX2F CLI — full lifecycle orchestrator."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from typing import Any, Dict

from gunnchos_device_os.cx2f.evidence import write_evidence
from gunnchos_device_os.cx2f.paths import cx2f_lab_root, evidence_root, repo_root_from_here
from gunnchos_device_os.cx2f.qemu import (
    DEFAULT_SSH_PORT,
    prepare_overlay,
    screendump,
    start_graphical_guest,
    stop_guest,
)
from gunnchos_device_os.cx2f.session import (
    deploy_shell_http,
    launch_chromium_shell,
    navigate_surfaces_and_capture,
    ppm_diff,
    probe_portals,
    prove_drm,
    prove_input_to_shell,
    run_provider_gui_if_gated,
    select_and_boot_non_cloud_kernel,
    start_weston_drm,
)
from gunnchos_device_os.cx2f.tokens import Cx2fTokens


def run_full_lifecycle(repo: Path) -> Dict[str, Any]:
    tokens = Cx2fTokens()
    facts: Dict[str, Any] = {
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    lab = cx2f_lab_root(repo)
    captures = Path("/tmp/cx2f-graphical/captures")
    captures.mkdir(parents=True, exist_ok=True)

    overlay = prepare_overlay(repo)
    facts["overlay"] = overlay
    if not overlay.get("ok"):
        tokens.lab_blocker = overlay.get("blocker") or "CX2F_OVERLAY_FAIL"
        return write_evidence(repo, tokens, facts)

    graphical = start_graphical_guest(repo, ssh_port=DEFAULT_SSH_PORT)
    facts["graphical"] = graphical
    facts["CX2F_QEMU_GRAPHICS"] = graphical.get("graphics") or {}
    tokens.CX2F_QEMU_GRAPHICS_SURFACE_PASS = bool(graphical.get("CX2F_QEMU_GRAPHICS_SURFACE_PASS"))
    tokens.guest_booted = bool(graphical.get("guest_booted"))
    if not graphical.get("ok"):
        tokens.lab_blocker = graphical.get("blocker") or "CX2F_GRAPHICAL_BOOT_FAILED"
        try:
            stop_guest(repo)
        except Exception:
            pass
        return write_evidence(repo, tokens, facts)

    tokens.guest_is_linux = True
    monitor = Path(graphical["runtime"]["monitor"])

    # 4. Non-cloud kernel
    kernel = select_and_boot_non_cloud_kernel(repo)
    facts["CX2F_KERNEL_SELECTION"] = kernel
    tokens.CX2F_NON_CLOUD_KERNEL_SELECTED = bool(kernel.get("CX2F_NON_CLOUD_KERNEL_SELECTED"))
    tokens.CX2F_NON_CLOUD_KERNEL_BOOT_PASS = bool(kernel.get("CX2F_NON_CLOUD_KERNEL_BOOT_PASS"))
    if not tokens.CX2F_NON_CLOUD_KERNEL_BOOT_PASS:
        tokens.lab_blocker = kernel.get("blocker") or "CX2F_NON_CLOUD_KERNEL_BOOT"
        stop_guest(repo)
        return write_evidence(repo, tokens, facts)

    # 5. DRM
    drm = prove_drm(repo)
    facts["CX2F_DRM_PROBE"] = drm
    tokens.CX2F_VIRTIO_GPU_ENUMERATION_PASS = bool(drm.get("CX2F_VIRTIO_GPU_ENUMERATION_PASS"))
    tokens.CX2F_DRM_CARD_PASS = bool(drm.get("CX2F_DRM_CARD_PASS"))
    tokens.CX2F_DRM_RENDER_NODE_PASS = bool(drm.get("CX2F_DRM_RENDER_NODE_PASS"))
    if not tokens.CX2F_DRM_CARD_PASS:
        tokens.lab_blocker = drm.get("blocker") or "CX2F_DRM_CARD_MISSING"
        stop_guest(repo)
        return write_evidence(repo, tokens, facts)

    # 7. Weston DRM only
    weston = start_weston_drm(repo)
    facts["CX2F_WESTON_DRM_SESSION"] = weston
    tokens.CX2F_WESTON_DRM_PASS = bool(weston.get("CX2F_WESTON_DRM_PASS"))
    tokens.CX2F_WESTON_HEADLESS_FALLBACK_USED = bool(weston.get("CX2F_WESTON_HEADLESS_FALLBACK_USED"))
    tokens.CX2F_WAYLAND_SOCKET_PASS = bool(weston.get("CX2F_WAYLAND_SOCKET_PASS"))
    tokens.CX2F_DBUS_SESSION_PASS = bool(weston.get("CX2F_DBUS_SESSION_PASS"))
    if not tokens.CX2F_WESTON_DRM_PASS or tokens.CX2F_WESTON_HEADLESS_FALLBACK_USED:
        tokens.lab_blocker = weston.get("blocker") or "CX2F_WESTON_DRM_NOT_PROVEN"
        stop_guest(repo)
        return write_evidence(repo, tokens, facts)

    # Baseline framebuffer (Weston only)
    baseline = screendump(monitor, captures / "01_weston_baseline.ppm")
    facts["baseline_capture"] = baseline

    # 8–9. Shell assets + Chromium
    delivery = deploy_shell_http(repo)
    facts["shell_delivery"] = delivery
    facts["CX2F_SHELL_RUNTIME_TARGET"] = delivery.get("shell_runtime_target")
    tokens.CX2F_SHELL_ASSET_DELIVERY_PASS = bool(delivery.get("CX2F_SHELL_ASSET_DELIVERY_PASS"))
    if not tokens.CX2F_SHELL_ASSET_DELIVERY_PASS:
        tokens.lab_blocker = delivery.get("blocker") or "CX2F_SHELL_ASSET_DELIVERY_FAIL"
        stop_guest(repo)
        return write_evidence(repo, tokens, facts)

    chrome = launch_chromium_shell(repo)
    facts["chromium"] = chrome
    time.sleep(2)
    home_cap = screendump(monitor, captures / "02_shell_home.ppm")
    diff_home = ppm_diff(
        Path(baseline["path"]) if baseline.get("path") else captures / "01_weston_baseline.ppm",
        Path(home_cap["path"]) if home_cap.get("path") else captures / "02_shell_home.ppm",
        min_changed_pct=0.2,
    )
    facts["FRAMEBUFFER_DIFF_REPORT"] = {"baseline_to_home": diff_home}

    # Navigate surfaces
    frames = navigate_surfaces_and_capture(repo, monitor, captures)
    facts["frames"] = {k: {kk: vv for kk, vv in v.items() if kk != "hmp_tail"} for k, v in frames.items()}

    render_criteria = {
        "asset_hash_matches": bool(delivery.get("build", {}).get("build_hash")),
        "asset_server_serves": tokens.CX2F_SHELL_ASSET_DELIVERY_PASS,
        "chromium_alive": bool(chrome.get("process_alive")),
        "wayland_session": tokens.CX2F_WAYLAND_SOCKET_PASS,
        "top_level_surface_inferred": bool(chrome.get("process_alive") and tokens.CX2F_WESTON_DRM_PASS),
        "framebuffer_after_launch": bool(home_cap.get("ok")),
        "framebuffer_differs_from_baseline": bool(diff_home.get("ok")),
        "second_channel_debug_or_atspi": bool(chrome.get("debug_json_ok")),
        "home_interactive_pending_input": True,
        "process_survives": bool(chrome.get("process_alive")),
    }
    shell_render = all(
        [
            render_criteria["asset_server_serves"],
            render_criteria["chromium_alive"],
            render_criteria["wayland_session"],
            render_criteria["framebuffer_after_launch"],
            render_criteria["framebuffer_differs_from_baseline"],
            render_criteria["second_channel_debug_or_atspi"] or render_criteria["framebuffer_differs_from_baseline"],
        ]
    )
    tokens.CX2F_GUNNCH_SHELL_RENDER_PASS = shell_render
    tokens.CX2F_REAL_HOME_WINDOW = shell_render
    # Independent surface evidence from nav frames vs baseline
    for surf, label in (
        ("VAULT", "03_shell_vault"),
        ("APP_CENTER", "04_shell_app_center"),
        ("CONNECT", "05_shell_connect"),
        ("ASSIST", "06_shell_assist"),
        ("CARE", "07_shell_care"),
    ):
        fr = frames.get(label) or {}
        ok = bool(fr.get("ok")) and shell_render
        setattr(tokens, f"CX2F_REAL_{surf}_WINDOW", ok)

    facts["CX2F_SHELL_RENDER_PROOF"] = {
        "criteria": render_criteria,
        "CX2F_GUNNCH_SHELL_RENDER_PASS": shell_render,
        "chromium": {k: chrome.get(k) for k in ("process_alive", "debug_json_ok", "used_no_sandbox")},
        "home_capture": {k: home_cap.get(k) for k in ("ok", "width", "height", "sha256", "size", "valid_ppm")},
        "diff_home": diff_home,
    }

    fb_ok = bool(baseline.get("ok") and home_cap.get("ok") and diff_home.get("ok"))
    tokens.CX2F_QEMU_FRAMEBUFFER_CAPTURE_PASS = fb_ok
    tokens.CX2F_RENDER_CAPTURE_PASS = fb_ok
    tokens.CX2F_REAL_SCREEN_CAPTURE_PASS = fb_ok
    facts["CX2F_FRAMEBUFFER_CAPTURE_MANIFEST"] = {
        "primary": "qemu_hmp_screendump_ppm",
        "frames": {
            "01_weston_baseline": baseline,
            "02_shell_home": home_cap,
            **{k: frames.get(k) for k in frames},
        },
        "note": "browser-only screenshot is not sole compositor proof",
    }

    if not shell_render or not fb_ok:
        tokens.lab_blocker = "CX2F_SHELL_RENDER_OR_CAPTURE_NOT_PROVEN"
        stop_guest(repo)
        return write_evidence(repo, tokens, facts)

    # 13. Input to shell
    inp = prove_input_to_shell(repo, monitor, captures, Path(home_cap["path"]))
    facts["CX2F_INPUT_TO_SHELL_PROOF"] = inp
    facts["ATSPI_SHELL_TREE"] = inp.get("atspi") or {}
    tokens.CX2F_REAL_INPUT_TO_SHELL_MUTATION_PASS = bool(inp.get("CX2F_REAL_INPUT_TO_SHELL_MUTATION_PASS"))
    if tokens.CX2F_REAL_INPUT_TO_SHELL_MUTATION_PASS:
        tokens.CX2F_REAL_VAULT_WINDOW = True
        tokens.CX2F_DIGITAL_RENDERED_A11Y_PASS = bool(
            isinstance(inp.get("atspi"), dict) and (inp["atspi"].get("nodes") or inp["atspi"].get("children", 0) > 0)
        )

    if not tokens.CX2F_REAL_INPUT_TO_SHELL_MUTATION_PASS:
        tokens.lab_blocker = inp.get("blocker") or "CX2F_INPUT_TO_SHELL_MUTATION_NOT_PROVEN"
        stop_guest(repo)
        return write_evidence(repo, tokens, facts)

    # 15. Portals
    portals = probe_portals(repo)
    facts["CX2F_XDG_PORTAL_MATRIX"] = portals
    tokens.CX2F_XDG_PORTAL_SESSION_PASS = bool(portals.get("CX2F_XDG_PORTAL_SESSION_PASS"))

    # 16+. Provider GUI only if gate passes
    gate_ok = tokens.gate_shell_stack()
    providers = run_provider_gui_if_gated(repo, gate_ok=gate_ok)
    facts["CX2F_PROVIDER_GUI_PROBES"] = providers
    if gate_ok and not providers.get("skipped"):
        tokens.CX2F_REAL_BROWSER_GUI_PASS = bool(providers.get("browser_gui")) and shell_render
        tokens.CX2F_REAL_APP_LIFECYCLE_GUI_PASS = bool(providers.get("app_lifecycle_gui")) and shell_render
        tokens.CX2F_REAL_PRODUCTIVITY_GUI_PASS = bool(providers.get("productivity_gui")) and shell_render
        tokens.CX2F_REAL_MAIL_GUI_PASS = bool(providers.get("mail_gui")) and shell_render
        tokens.CX2F_REAL_IPP_GUI_DIGITAL_PASS = bool(providers.get("ipp_gui_digital")) and shell_render
        tokens.CX2F_REAL_OFFLINE_RECOVERY_GUI_PASS = bool(providers.get("offline_recovery_gui")) and shell_render

    # Journey complete flags intentionally false unless full step evidence recorded
    facts.update(
        {
            "CX2F_NON_CLOUD_KERNEL_BOOT_PASS": tokens.CX2F_NON_CLOUD_KERNEL_BOOT_PASS,
            "CX2F_WESTON_DRM_PASS": tokens.CX2F_WESTON_DRM_PASS,
            "CX2F_GUNNCH_SHELL_RENDER_PASS": tokens.CX2F_GUNNCH_SHELL_RENDER_PASS,
            "CX2F_QEMU_FRAMEBUFFER_CAPTURE_PASS": tokens.CX2F_QEMU_FRAMEBUFFER_CAPTURE_PASS,
            "CX2F_REAL_INPUT_TO_SHELL_MUTATION_PASS": tokens.CX2F_REAL_INPUT_TO_SHELL_MUTATION_PASS,
            "productivity_gui": tokens.CX2F_REAL_PRODUCTIVITY_GUI_PASS,
            "browser_gui": tokens.CX2F_REAL_BROWSER_GUI_PASS,
            "mail_gui": tokens.CX2F_REAL_MAIL_GUI_PASS,
            "app_lifecycle_gui": tokens.CX2F_REAL_APP_LIFECYCLE_GUI_PASS,
            "offline_recovery_gui": tokens.CX2F_REAL_OFFLINE_RECOVERY_GUI_PASS,
            "j1_complete_ui_provider_readback": False,
            "j2_complete_ui_provider_readback": False,
            "j3_complete_ui_provider_readback": False,
            "j5_complete_ui_provider_readback": False,
            "j7_complete_ui_provider_readback": False,
        }
    )

    if not tokens.lab_blocker:
        tokens.lab_blocker = "CX2F_JOURNEY_DIGITAL_PASS_INCOMPLETE"

    report = write_evidence(repo, tokens, facts)
    stop_guest(repo)
    return report


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="python -m gunnchos_device_os.cx2f")
    p.add_argument("--repo", type=Path, default=None)
    p.add_argument("--prepare-only", action="store_true")
    p.add_argument("--full-lifecycle", action="store_true")
    p.add_argument("--shutdown", action="store_true")
    p.add_argument("--evidence-only", action="store_true")
    args = p.parse_args(argv)
    repo = args.repo or repo_root_from_here()

    if args.shutdown:
        print(json.dumps(stop_guest(repo), indent=2))
        return 0

    if args.prepare_only:
        ov = prepare_overlay(repo)
        print(json.dumps(ov, indent=2))
        return 0 if ov.get("ok") else 1

    if args.evidence_only:
        tokens = Cx2fTokens(lab_blocker="evidence_only")
        report = write_evidence(repo, tokens, {})
        print("NEXT_CX_GATE=", report["NEXT_CX_GATE"])
        return 0

    if args.full_lifecycle:
        report = run_full_lifecycle(repo)
        print("NEXT_CX_GATE=", report.get("NEXT_CX_GATE"))
        print("FULL_COMPLETE_EXPERIENCE_COMPLETE=", report.get("FULL_COMPLETE_EXPERIENCE_COMPLETE"))
        tok = report.get("tokens") or {}
        for k in (
            "CX2F_NON_CLOUD_KERNEL_BOOT_PASS",
            "CX2F_DRM_CARD_PASS",
            "CX2F_WESTON_DRM_PASS",
            "CX2F_GUNNCH_SHELL_RENDER_PASS",
            "CX2F_QEMU_FRAMEBUFFER_CAPTURE_PASS",
            "CX2F_REAL_INPUT_TO_SHELL_MUTATION_PASS",
        ):
            print(f"{k}={tok.get(k)}")
        return 0

    p.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
