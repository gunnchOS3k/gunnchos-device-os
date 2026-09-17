"""CX2H session: re-prove CX2G shell stack without reopening kernel architecture."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, Tuple

from gunnchos_device_os.cx2g import session as cx2g_session
from gunnchos_device_os.cx2g.qemu import screendump
from gunnchos_device_os.cx2g.session import ppm_diff
from gunnchos_device_os.cx2h.paths import cx2h_lab_root, ensure_lab_tree
from gunnchos_device_os.cx2h.qemu import DEFAULT_SSH_PORT, ensure_ssh_keypair, scp_to_guest, ssh_exec


def _key_port(repo: Path) -> Tuple[Path, int]:
    # Prefer CX2H keys; fall back works because we copy from CX2G
    lab = cx2h_lab_root(repo)
    key = Path(ensure_ssh_keypair(lab)["private"])
    return key, DEFAULT_SSH_PORT


def _ssh(repo: Path, cmd: str, *, timeout: int = 180):
    key, port = _key_port(repo)
    return ssh_exec(key, port, cmd, timeout=timeout)


def re_prove_shell_prereqs(repo: Path, monitor: Path, captures: Path) -> Dict[str, Any]:
    """Re-prove Chromium/Wayland/shell/FB/input/App Center without kernel redo."""
    ensure_lab_tree(repo)
    facts: Dict[str, Any] = {}

    # Kernel: accept already-booted non-cloud (no GRUB rewrite unless cloud)
    kuname = _ssh(repo, "uname -r; cat /proc/cmdline | head -c 200", timeout=30)
    kout = kuname.stdout or ""
    non_cloud = "cloud" not in kout.split()[0] and "arm64" in kout
    facts["kernel_uname"] = kout[-500:]
    facts["non_cloud_already"] = non_cloud
    if not non_cloud:
        # Only then call CX2G selector (architecture reopen only if regression)
        kernel = cx2g_session.select_and_boot_non_cloud_kernel(repo)
        facts["kernel_repair"] = kernel
        non_cloud = bool(kernel.get("CX2G_NON_CLOUD_KERNEL_BOOT_PASS"))
    if not non_cloud:
        return {**facts, "ok": False, "blocker": "CX2H_SHELL_PREREQ_KERNEL_REGRESSION"}

    drm = cx2g_session.prove_drm(repo)
    facts["drm"] = drm
    if not drm.get("CX2G_DRM_CARD_PASS"):
        return {**facts, "ok": False, "blocker": "CX2H_SHELL_PREREQ_DRM_REGRESSION"}

    weston = cx2g_session.start_weston_drm(repo)
    facts["weston"] = {k: weston.get(k) for k in weston if k != "stdout"}
    facts["weston_tail"] = (weston.get("stdout") or "")[-1500:]
    if not weston.get("CX2G_WESTON_DRM_PASS") or weston.get("CX2G_WESTON_HEADLESS_FALLBACK_USED"):
        return {**facts, "ok": False, "blocker": "CX2H_SHELL_PREREQ_WESTON_REGRESSION"}

    baseline = screendump(monitor, captures / "01_weston_baseline.ppm")
    facts["baseline"] = {k: baseline.get(k) for k in ("ok", "sha256", "width", "height")}

    delivery = cx2g_session.deploy_shell_http(repo)
    facts["delivery"] = {
        "ok": delivery.get("ok"),
        "hash": (delivery.get("build") or {}).get("build_hash"),
        "blocker": delivery.get("blocker"),
    }
    if not delivery.get("CX2G_SHELL_ASSET_DELIVERY_PASS"):
        return {**facts, "ok": False, "blocker": "CX2H_SHELL_ASSET_DELIVERY_FAIL"}

    chrome = cx2g_session.launch_chromium_shell(repo)
    facts["chromium"] = {
        k: chrome.get(k)
        for k in ("process_alive", "debug_json_ok", "CX2G_CHROMIUM_RUNTIME_PASS", "used_no_sandbox")
    }
    runtime_ok = bool(chrome.get("process_alive") and chrome.get("debug_json_ok"))
    if not runtime_ok:
        return {**facts, "ok": False, "blocker": "CX2H_SHELL_PREREQ_CHROMIUM_REGRESSION"}

    time.sleep(2)
    home_cap = screendump(monitor, captures / "02_shell_home.ppm")
    diff_home = ppm_diff(
        Path(baseline["path"]) if baseline.get("path") else captures / "01_weston_baseline.ppm",
        Path(home_cap["path"]) if home_cap.get("path") else captures / "02_shell_home.ppm",
        min_changed_pct=0.2,
    )
    facts["home_diff"] = diff_home
    frames = cx2g_session.navigate_surfaces_and_capture(repo, monitor, captures)
    facts["frames"] = {k: bool(v.get("ok")) for k, v in frames.items()}
    app_center_ok = bool((frames.get("04_shell_app_center") or {}).get("ok"))

    shell_render = bool(
        delivery.get("CX2G_SHELL_ASSET_DELIVERY_PASS")
        and runtime_ok
        and weston.get("CX2G_WAYLAND_SOCKET_PASS")
        and home_cap.get("ok")
        and diff_home.get("ok")
    )
    fb_ok = bool(baseline.get("ok") and home_cap.get("ok") and diff_home.get("ok"))

    inp = cx2g_session.prove_input_to_shell(repo, monitor, captures, Path(home_cap["path"]))
    facts["input"] = {
        "pass": inp.get("CX2G_REAL_INPUT_TO_SHELL_MUTATION_PASS"),
        "diff": inp.get("diff"),
        "blocker": inp.get("blocker"),
    }
    if not inp.get("CX2G_REAL_INPUT_TO_SHELL_MUTATION_PASS"):
        return {**facts, "ok": False, "blocker": "CX2H_SHELL_PREREQ_INPUT_REGRESSION"}

    ok = shell_render and fb_ok and app_center_ok and runtime_ok
    return {
        **facts,
        "ok": ok,
        "CX2H_CHROMIUM_RUNTIME_PASS": runtime_ok,
        "CX2H_WAYLAND_SURFACE_PASS": bool(weston.get("CX2G_WAYLAND_SOCKET_PASS") and runtime_ok),
        "CX2H_GUNNCH_SHELL_RENDER_PASS": shell_render,
        "CX2H_QEMU_FRAMEBUFFER_CAPTURE_PASS": fb_ok,
        "CX2H_REAL_INPUT_TO_SHELL_MUTATION_PASS": bool(inp.get("CX2G_REAL_INPUT_TO_SHELL_MUTATION_PASS")),
        "CX2H_REAL_APP_CENTER_WINDOW": app_center_ok and shell_render,
        "CX2H_SHELL_PREREQ_PASS": ok,
        "blocker": None if ok else "CX2H_SHELL_PREREQ_FAILED",
    }


def deploy_app_center_provider(repo: Path) -> Dict[str, Any]:
    lab = ensure_lab_tree(repo)
    key, port = _key_port(repo)
    script = lab / "scripts" / "cx2h_app_center_provider.py"
    _ssh(repo, "sudo mkdir -p /var/lib/cx2h/bin && sudo chown -R gunnchos:gunnchos /var/lib/cx2h", timeout=30)
    scp = scp_to_guest(key, port, script, "/var/lib/cx2h/bin/cx2h_app_center_provider.py")
    unit = """[Unit]
Description=CX2H App Center Flatpak provider API
After=network.target

[Service]
Type=simple
User=gunnchos
Environment=FLATPAK_USER_DIR=/var/lib/cx2h/flatpak-user
Environment=CX2H_PROVIDER_PORT=8766
Environment=XDG_RUNTIME_DIR=/run/user/1000
Environment=WAYLAND_DISPLAY=wayland-0
Environment=GDK_BACKEND=wayland
Environment=XKB_CONFIG_ROOT=/usr/share/X11/xkb
Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
ExecStart=/usr/bin/python3 /var/lib/cx2h/bin/cx2h_app_center_provider.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
"""
    start = _ssh(
        repo,
        "sudo tee /etc/systemd/system/cx2h-app-center-provider.service >/dev/null <<'UNIT'\n"
        + unit
        + "\nUNIT\n"
        "sudo systemctl daemon-reload; "
        "sudo systemctl restart cx2h-app-center-provider.service; "
        "sleep 1; "
        "systemctl is-active cx2h-app-center-provider.service; "
        "curl -sf http://127.0.0.1:8766/api/health || echo HEALTH_FAIL",
        timeout=60,
    )
    out = (start.stdout or "") + (start.stderr or "")
    return {
        "scp_rc": scp.returncode,
        "stdout": out[-1500:],
        "ok": "active" in out and "HEALTH_FAIL" not in out and '"ok"' in out,
    }


def restart_shell_for_persistence(repo: Path) -> Dict[str, Any]:
    r = _ssh(
        repo,
        "sudo systemctl restart cx2g-gunnch-shell.service 2>/dev/null || "
        "sudo systemctl restart cx2h-gunnch-shell.service 2>/dev/null || true; "
        "sleep 3; "
        "curl -sf http://127.0.0.1:9222/json >/dev/null && echo DEBUG_OK || echo DEBUG_FAIL; "
        "curl -sf http://127.0.0.1:8766/api/state || echo STATE_FAIL",
        timeout=90,
    )
    out = r.stdout or ""
    return {"stdout": out[-1500:], "ok": "DEBUG_OK" in out or "STATE_FAIL" not in out}
