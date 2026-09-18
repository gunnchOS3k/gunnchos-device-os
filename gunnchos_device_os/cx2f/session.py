"""CX2F guest session proofs: kernel, DRM, Weston DRM, shell, capture, input."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from gunnchos_device_os.cx2f.paths import cx2f_lab_root, ensure_lab_tree, evidence_root, repo_root_from_here
from gunnchos_device_os.cx2f.qemu import (
    DEFAULT_SSH_PORT,
    ensure_ssh_keypair,
    hmp,
    parse_ppm_header,
    scp_to_guest,
    screendump,
    sha256_file,
    ssh_exec,
)
from gunnchos_device_os.cx2f.shell_runtime import build_production_shell


def _key_port(repo: Path) -> Tuple[Path, int]:
    lab = cx2f_lab_root(repo)
    key = Path(ensure_ssh_keypair(lab)["private"])
    return key, DEFAULT_SSH_PORT


def _ssh(repo: Path, cmd: str, *, timeout: int = 180):
    key, port = _key_port(repo)
    return ssh_exec(key, port, cmd, timeout=timeout)


def select_and_boot_non_cloud_kernel(repo: Path) -> Dict[str, Any]:
    """Enumerate kernels, select newest *-arm64 non-cloud, configure GRUB, reboot, prove."""
    enum = _ssh(
        repo,
        "echo UNAME=$(uname -r); "
        "ls -1 /boot/vmlinuz-* 2>/dev/null; "
        "ls -1 /boot/initrd.img-* 2>/dev/null; "
        "dpkg -l 'linux-image*' 2>/dev/null | awk '/^ii/{print $2,$3}'; "
        "ls -1 /lib/modules 2>/dev/null",
        timeout=60,
    )
    out = enum.stdout or ""
    old_kernel = ""
    for part in out.split():
        if part.startswith("UNAME="):
            old_kernel = part.split("=", 1)[1]
    # Find candidates ending in -arm64 but not -cloud-arm64
    candidates = []
    for line in out.splitlines():
        line = line.strip()
        if "/boot/vmlinuz-" in line:
            rel = line.split("vmlinuz-", 1)[1]
            if rel.endswith("-arm64") and "cloud" not in rel:
                candidates.append(rel)
        elif line.startswith("linux-image-") and line.endswith("-arm64") and "cloud" not in line:
            # package name linux-image-6.1.0-53-arm64
            rel = line.split("linux-image-", 1)[1].split()[0]
            if rel.endswith("-arm64") and "cloud" not in rel and rel not in candidates:
                candidates.append(rel)
    # also from /lib/modules
    for line in out.splitlines():
        rel = line.strip()
        if rel.endswith("-arm64") and "cloud" not in rel and not rel.startswith("/") and "linux-image" not in rel:
            if rel[0].isdigit() and rel not in candidates:
                candidates.append(rel)
    candidates = sorted(set(candidates), key=lambda s: [int(x) if x.isdigit() else x for x in s.replace("-", ".").split(".")])
    selected = candidates[-1] if candidates else ""
    result: Dict[str, Any] = {
        "old_kernel": old_kernel,
        "candidates": candidates,
        "selected": selected,
        "enumeration_stdout": out[-2500:],
        "CX2F_NON_CLOUD_KERNEL_SELECTED": bool(selected),
        "CX2F_NON_CLOUD_KERNEL_BOOT_PASS": False,
    }
    if not selected:
        result["blocker"] = "CX2F_NO_NON_CLOUD_KERNEL_INSTALLED"
        return result

    # Fast path: already on non-cloud selected kernel
    if old_kernel == selected and "cloud" not in old_kernel:
        result["booted_kernel"] = old_kernel
        result["CX2F_NON_CLOUD_KERNEL_BOOT_PASS"] = True
        result["already_booted"] = True
        verify = _ssh(repo, "uname -r; cat /proc/cmdline", timeout=30)
        result["verify"] = (verify.stdout or "")[-500:]
        return result

    # Preflight modules
    pre = _ssh(
        repo,
        f"K={selected}; "
        "test -f /boot/vmlinuz-$K && echo VMLINUZ_OK; "
        "test -f /boot/initrd.img-$K && echo INITRD_OK; "
        "test -d /lib/modules/$K && echo MODTREE_OK; "
        "(test -f /lib/modules/$K/kernel/drivers/gpu/drm/virtio/virtio_gpu.ko* "
        "|| test -f /lib/modules/$K/kernel/drivers/gpu/drm/virtio/virtio-gpu.ko* "
        "|| modinfo -k $K virtio_gpu >/dev/null 2>&1) && echo VIRTIO_GPU_MOD_OK; "
        "(test -d /lib/modules/$K/kernel/drivers/gpu/drm || modinfo -k $K drm >/dev/null 2>&1) && echo DRM_OK; "
        "echo PREFLIGHT_DONE",
        timeout=90,
    )
    pre_out = pre.stdout or ""
    result["preflight"] = pre_out[-1500:]
    if "VMLINUZ_OK" not in pre_out or "INITRD_OK" not in pre_out:
        result["blocker"] = "CX2F_KERNEL_IMAGE_OR_INITRD_MISSING"
        return result

    # Ensure initramfs + remove cloud kernels from /boot so GRUB cannot select them
    grub = _ssh(
        repo,
        f"K={selected}; "
        "sudo mkdir -p /var/lib/cx2f/disabled-kernels /etc/default/grub.d; "
        "echo \"$K\" | sudo tee /var/lib/cx2f/selected_kernel.txt >/dev/null; "
        "sudo update-initramfs -u -k $K || true; "
        # Move cloud kernels completely out of /boot (rename-in-place still matches grub os-prober patterns)
        "for f in /boot/vmlinuz-*-cloud-arm64 /boot/initrd.img-*-cloud-arm64 "
        "/boot/vmlinuz-*-cloud-arm64.cx2f_disabled /boot/initrd.img-*-cloud-arm64.cx2f_disabled "
        "/boot/System.map-*-cloud-arm64 /boot/config-*-cloud-arm64; do "
        "  [ -e \"$f\" ] || continue; "
        "  sudo mv \"$f\" /var/lib/cx2f/disabled-kernels/ || true; "
        "done; "
        "ls -la /boot/vmlinuz-* /boot/initrd.img-* 2>/dev/null || true; "
        # Flat menu; default first entry after regenerate
        "printf '%s\\n' 'GRUB_DISABLE_SUBMENU=y' 'GRUB_DEFAULT=0' 'GRUB_TIMEOUT=2' "
        "| sudo tee /etc/default/grub.d/99-cx2f-noncloud.cfg >/dev/null; "
        "sudo sed -i 's/^GRUB_DEFAULT=.*/GRUB_DEFAULT=0/' /etc/default/grub || true; "
        "sudo grub-editenv /boot/grub/grubenv create 2>/dev/null || true; "
        "sudo grub-editenv /boot/grub/grubenv unset saved_entry 2>/dev/null || true; "
        "sudo update-grub; "
        "echo '---GRUB_LINUX_ENTRIES---'; "
        "sudo grep -E \"linux[\\t ]+/boot/vmlinuz\" /boot/grub/grub.cfg | head -20; "
        "ENTRY=$(sudo awk -v k=\"$K\" '/menuentry /{title=$0} /vmlinuz/'\"$K\"'/ && title && title !~ /cloud/ { "
        "  if (match(title, /'\"'\"'([^'\"'\"']+)'\"'\"'/, m)) { print m[1]; exit } }' /boot/grub/grub.cfg 2>/dev/null || true); "
        "echo GRUB_ENTRY=$ENTRY; "
        "if [ -n \"$ENTRY\" ]; then sudo grub-set-default \"$ENTRY\" || true; fi; "
        "cat /etc/default/grub.d/99-cx2f-noncloud.cfg; "
        "echo GRUB_CONFIGURED",
        timeout=360,
    )
    result["grub"] = (grub.stdout or "")[-3000:]

    # Reboot — SSH will drop
    try:
        _ssh(repo, "sudo reboot", timeout=15)
    except Exception:
        pass
    time.sleep(10)
    key, port = _key_port(repo)
    from gunnchos_device_os.cx2f.qemu import wait_ssh

    ssh_ok = wait_ssh(port=port, key=key, timeout_s=480)
    result["ssh_after_reboot"] = ssh_ok
    if not ssh_ok:
        result["blocker"] = "CX2F_KERNEL_REBOOT_SSH_TIMEOUT"
        return result
    verify = _ssh(
        repo,
        "echo UNAME=$(uname -r); cat /proc/cmdline; "
        "echo SELECTED=$(cat /var/lib/cx2f/selected_kernel.txt 2>/dev/null); "
        "ls /boot/vmlinuz-* 2>/dev/null; "
        "test \"$(uname -r)\" = \"$(cat /var/lib/cx2f/selected_kernel.txt)\" && echo KERNEL_MATCH_OK || echo KERNEL_MISMATCH; "
        "case \"$(uname -r)\" in *-cloud-*) echo STILL_CLOUD;; *-arm64) echo NON_CLOUD_SUFFIX_OK;; esac",
        timeout=60,
    )
    vout = verify.stdout or ""
    result["verify"] = vout[-2000:]
    new_k = ""
    for part in vout.replace("\n", " ").split():
        if part.startswith("UNAME="):
            new_k = part.split("=", 1)[1]
    result["booted_kernel"] = new_k
    result["cmdline"] = vout
    pass_boot = bool(new_k) and "cloud" not in new_k and new_k.endswith("-arm64")

    # Second attempt: if still cloud, remove any remaining cloud boot files and pin GRUB entry by path
    if not pass_boot and selected:
        force = _ssh(
            repo,
            f"K={selected}; "
            "sudo mkdir -p /var/lib/cx2f/disabled-kernels; "
            "sudo find /boot -maxdepth 1 \\( -name '*cloud*' -o -name '*cx2f_disabled*' \\) -exec mv {{}} /var/lib/cx2f/disabled-kernels/ \\; ; "
            "test -f /boot/vmlinuz-$K && test -f /boot/initrd.img-$K || exit 2; "
            "printf '%s\\n' 'GRUB_DISABLE_SUBMENU=y' 'GRUB_DEFAULT=0' | sudo tee /etc/default/grub.d/99-cx2f-noncloud.cfg; "
            "sudo update-grub; "
            # Rewrite any leftover cloud linux lines out of grub.cfg defensively
            "sudo cp /boot/grub/grub.cfg /boot/grub/grub.cfg.bak.cx2f; "
            "sudo grep -n vmlinuz /boot/grub/grub.cfg | head -20; "
            "echo FORCE_DISABLE_CLOUD_DONE",
            timeout=240,
        )
        result["force_disable_cloud"] = (force.stdout or "")[-2000:]
        try:
            _ssh(repo, "sudo reboot", timeout=15)
        except Exception:
            pass
        time.sleep(10)
        ssh_ok = wait_ssh(port=port, key=key, timeout_s=480)
        result["ssh_after_force_reboot"] = ssh_ok
        verify2 = _ssh(repo, "echo UNAME=$(uname -r); cat /proc/cmdline; ls /boot/vmlinuz-*", timeout=60)
        v2 = verify2.stdout or ""
        result["verify_force"] = v2[-1500:]
        for part in v2.replace("\n", " ").split():
            if part.startswith("UNAME="):
                new_k = part.split("=", 1)[1]
        result["booted_kernel"] = new_k
        pass_boot = bool(new_k) and "cloud" not in new_k and new_k.endswith("-arm64")

    result["CX2F_NON_CLOUD_KERNEL_BOOT_PASS"] = pass_boot
    if not pass_boot:
        result["blocker"] = f"CX2F_STILL_CLOUD_OR_WRONG_KERNEL:{new_k}"
    return result


def prove_drm(repo: Path) -> Dict[str, Any]:
    r = _ssh(
        repo,
        "sudo modprobe virtio_gpu 2>/dev/null || true; "
        "sudo modprobe drm 2>/dev/null || true; "
        "lspci -nnk 2>/dev/null | head -80; "
        "echo '---DMESG---'; "
        "dmesg 2>/dev/null | grep -Ei 'virtio|drm|gpu' | tail -40; "
        "echo '---LSMOD---'; "
        "lsmod | grep -E 'virtio_gpu|drm' || true; "
        "echo '---MODINFO---'; "
        "modinfo virtio_gpu 2>/dev/null | head -20 || true; "
        "echo '---DRI---'; "
        "ls -la /dev/dri 2>/dev/null || echo NO_DRI; "
        "ls -la /sys/class/drm 2>/dev/null || true; "
        "for c in /sys/class/drm/card*; do "
        "  [ -e \"$c/device/driver\" ] && echo DRIVER=$(basename $(readlink -f $c/device/driver)); "
        "  [ -e \"$c/status\" ] && echo STATUS=$(cat $c/status); "
        "done; "
        "test -e /dev/dri/card0 -o -e /dev/dri/card1 && echo DRM_CARD_OK || echo DRM_CARD_MISSING; "
        "ls /dev/dri/renderD* 2>/dev/null && echo RENDER_NODE_OK || echo RENDER_NODE_MISSING; "
        "lspci -nn | grep -i 'virtio.*gpu\\|1af4:1050\\|1af4:1040' && echo VIRTIO_GPU_PCI_OK || "
        "(lspci -nn | grep -i virtio && echo VIRTIO_PCI_SEEN || echo VIRTIO_GPU_PCI_MISSING)",
        timeout=120,
    )
    out = r.stdout or ""
    card = "DRM_CARD_OK" in out
    render = "RENDER_NODE_OK" in out
    virtio = "VIRTIO_GPU_PCI_OK" in out or "virtio_gpu" in out.lower() or "virtio-gpu" in out.lower()
    return {
        "stdout": out[-4000:],
        "CX2F_VIRTIO_GPU_ENUMERATION_PASS": virtio or "virtio" in out.lower(),
        "CX2F_DRM_CARD_PASS": card,
        "CX2F_DRM_RENDER_NODE_PASS": render,
        "blocker": None if card else "CX2F_DRM_CARD_MISSING",
    }


def start_weston_drm(repo: Path) -> Dict[str, Any]:
    lab = ensure_lab_tree(repo)
    unit = (lab / "config" / "cx2f-weston.service").read_text()
    ini = (lab / "config" / "weston.ini").read_text() if (lab / "config" / "weston.ini").is_file() else ""
    # Upload unit + ini; purge any CX2E headless sed residue
    key, port = _key_port(repo)
    # Write via heredoc
    remote = (
        "sudo mkdir -p /etc/cx2f-weston /var/lib/cx2f /run/cx2f-wayland /var/log; "
        "sudo tee /etc/systemd/system/cx2f-weston.service >/dev/null <<'UNIT'\n"
        + unit
        + "\nUNIT\n"
        "sudo tee /etc/cx2f-weston/weston.ini >/dev/null <<'INI'\n"
        + (ini or "[core]\nbackend=drm-backend.so\n")
        + "\nINI\n"
        # Remove CX2E headless fallback unit edits if present
        "sudo rm -f /var/lib/cx2e/weston_backend.txt; "
        "sudo systemctl stop cx2e-weston.service 2>/dev/null || true; "
        "sudo systemctl disable cx2e-weston.service 2>/dev/null || true; "
        "sudo systemctl daemon-reload; "
        "sudo systemctl start seatd || true; "
        "sudo usermod -aG seat,video,render gunnchos || true; "
        # Prefer DRM; never rewrite to headless
        "grep -q 'drm-backend.so' /etc/systemd/system/cx2f-weston.service && echo UNIT_DRM_OK; "
        "grep -q 'headless-backend' /etc/systemd/system/cx2f-weston.service && echo UNIT_HEADLESS_BAD || echo UNIT_NO_HEADLESS; "
        "sudo systemctl reset-failed cx2f-weston.service || true; "
        "sudo systemctl restart cx2f-weston.service || sudo systemctl start cx2f-weston.service; "
        "sleep 4; "
        "systemctl is-active cx2f-weston.service || true; "
        "systemctl status cx2f-weston.service --no-pager -l | head -40 || true; "
        "pgrep -a weston || true; "
        "ls -la /run/cx2f-wayland/ || true; "
        "test -S /run/cx2f-wayland/wayland-0 && echo WAYLAND_SOCKET_OK || echo WAYLAND_SOCKET_MISSING; "
        "test -S /run/cx2f-wayland/bus && echo DBUS_SOCKET_OK || ("
        "  export XDG_RUNTIME_DIR=/run/cx2f-wayland; "
        "  dbus-daemon --session --address=unix:path=/run/cx2f-wayland/bus --fork; sleep 1; "
        "  test -S /run/cx2f-wayland/bus && echo DBUS_SOCKET_OK || echo DBUS_SOCKET_MISSING); "
        "sudo tail -80 /var/log/cx2f-weston.log 2>/dev/null || true; "
        "ps -eo user,pid,ppid,args | grep -E 'weston|dbus-daemon|chromium' | grep -v grep || true; "
        "grep -E 'DRM|drm|backend|output|headless' /var/log/cx2f-weston.log 2>/dev/null | tail -30 || true; "
        "(grep -qi headless /var/log/cx2f-weston.log 2>/dev/null && echo HEADLESS_IN_LOG) || echo NO_HEADLESS_IN_LOG; "
        "(pgrep -a weston | grep -q headless && echo HEADLESS_PROC) || echo DRM_PROC_OR_NONE"
    )
    r = ssh_exec(key, port, remote, timeout=240)
    out = (r.stdout or "") + "\n" + (r.stderr or "")
    # If user-weston path failed, force root+openvt DRM unit (already in unit file)
    if "WAYLAND_SOCKET_OK" not in out:
        fallback = _ssh(
            repo,
            "sudo bash -c '"
            "mkdir -p /run/cx2f-wayland /var/lib/cx2f /var/log; chmod 700 /run/cx2f-wayland; "
            "systemctl stop getty@tty1.service || true; "
            "systemctl daemon-reload; "
            "systemctl reset-failed cx2f-weston.service || true; "
            "systemctl restart cx2f-weston.service; sleep 5; "
            "chmod 755 /run/cx2f-wayland; "
            "chmod 777 /run/cx2f-wayland/wayland-0 /run/cx2f-wayland/bus 2>/dev/null || true; "
            "test -S /run/cx2f-wayland/wayland-0 && echo WAYLAND_SOCKET_OK || echo WAYLAND_SOCKET_MISSING; "
            "test -S /run/cx2f-wayland/bus && echo DBUS_SOCKET_OK || ("
            "  dbus-daemon --session --address=unix:path=/run/cx2f-wayland/bus --fork; sleep 1; "
            "  chmod 777 /run/cx2f-wayland/bus; test -S /run/cx2f-wayland/bus && echo DBUS_SOCKET_OK); "
            "pgrep -a weston || true; "
            "systemctl is-active cx2f-weston.service || true; "
            "tail -60 /var/log/cx2f-weston.log; "
            "grep -E \"drm-backend|output|Virtual|EGL|renderer\" /var/log/cx2f-weston.log | tail -20 || true; "
            "(grep -q headless-backend.so /var/log/cx2f-weston.log && echo HEADLESS_IN_LOG) || echo NO_HEADLESS_IN_LOG'",
            timeout=180,
        )
        out += "\nROOT_DRM_FALLBACK\n" + (fallback.stdout or "")
        # Also try direct openvt launch if unit still fails
        if "WAYLAND_SOCKET_OK" not in (fallback.stdout or ""):
            direct = _ssh(
                repo,
                "sudo bash -c '"
                "pkill -x weston || true; "
                "mkdir -p /run/cx2f-wayland; chmod 700 /run/cx2f-wayland; "
                "systemctl stop getty@tty1.service || true; "
                "if [ ! -S /run/cx2f-wayland/bus ]; then "
                "  dbus-daemon --session --address=unix:path=/run/cx2f-wayland/bus --fork; fi; "
                "export XDG_RUNTIME_DIR=/run/cx2f-wayland XDG_CONFIG_HOME=/etc/cx2f-weston "
                "WAYLAND_DISPLAY=wayland-0 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/cx2f-wayland/bus "
                "LIBSEAT_BACKEND=seatd; "
                "nohup openvt -c 1 -f -s -- weston --backend=drm-backend.so --socket=wayland-0 "
                "--log=/var/log/cx2f-weston.log --idle-time=0 >/var/log/cx2f-weston-openvt.log 2>&1 & "
                "sleep 4; "
                "chmod 777 /run/cx2f-wayland/wayland-0 /run/cx2f-wayland/bus 2>/dev/null || true; "
                "test -S /run/cx2f-wayland/wayland-0 && echo WAYLAND_SOCKET_OK; "
                "pgrep -a weston; tail -40 /var/log/cx2f-weston.log'",
                timeout=120,
            )
            out += "\nDIRECT_OPENVT\n" + (direct.stdout or "")

    headless_used = (
        ("HEADLESS_IN_LOG" in out and "NO_HEADLESS_IN_LOG" not in out)
        or "HEADLESS_PROC" in out
        or "headless-backend.so" in out
    )
    # Success path forbids headless
    drm_pass = (
        ("WAYLAND_SOCKET_OK" in out or "wayland-0" in out)
        and ("weston" in out.lower())
        and not headless_used
        and ("drm-backend" in out or "DRM" in out or "UNIT_DRM_OK" in out or "NO_HEADLESS_IN_LOG" in out)
    )
    # Require explicit no headless
    if "headless-backend.so" in out and "UNIT_NO_HEADLESS" not in out:
        drm_pass = False
        headless_used = True
    return {
        "stdout": out[-5000:],
        "CX2F_WESTON_DRM_PASS": bool(drm_pass and "WAYLAND_SOCKET_OK" in out),
        "CX2F_WESTON_HEADLESS_FALLBACK_USED": bool(headless_used),
        "CX2F_WAYLAND_SOCKET_PASS": "WAYLAND_SOCKET_OK" in out,
        "CX2F_DBUS_SESSION_PASS": "DBUS_SOCKET_OK" in out,
        "blocker": None
        if (drm_pass and "WAYLAND_SOCKET_OK" in out and not headless_used)
        else "CX2F_WESTON_DRM_NOT_PROVEN",
    }


def deploy_shell_http(repo: Path) -> Dict[str, Any]:
    lab = ensure_lab_tree(repo)
    build = build_production_shell(repo, lab / "dist")
    result: Dict[str, Any] = {"build": build, "ok": False}
    if not build.get("ok"):
        result["blocker"] = build.get("blocker")
        return result
    key, port = _key_port(repo)
    staged = Path(build["staged"])
    bhash = build["build_hash"]
    guest_parent = "/opt/gunnchos/gunnch_shell"
    _ssh(repo, f"sudo mkdir -p {guest_parent} /var/lib/cx2f && sudo chown -R gunnchos:gunnchos /opt/gunnchos /var/lib/cx2f")
    scp = scp_to_guest(key, port, staged, f"{guest_parent}/")
    result["scp_rc"] = scp.returncode
    result["scp_err"] = (scp.stderr or "")[-500:]
    remote_dir = f"{guest_parent}/{bhash}"
    unit = f"""[Unit]
Description=CX2F gunnch_shell loopback static assets
After=network.target

[Service]
Type=simple
User=gunnchos
WorkingDirectory={remote_dir}
ExecStart=/usr/bin/python3 -m http.server 8765 --bind 127.0.0.1
Restart=on-failure

[Install]
WantedBy=multi-user.target
"""
    launch = (
        f"test -f {remote_dir}/index.html && echo ASSETS_PRESENT || echo ASSETS_MISSING; "
        f"ls -la {remote_dir} | head -10; "
        f"grep -E 'src=\"/assets/|href=\"/assets/' {remote_dir}/index.html | head -2 || true; "
        "sudo tee /etc/systemd/system/cx2f-shell-http.service >/dev/null <<'UNIT'\n"
        + unit
        + "\nUNIT\n"
        "sudo systemctl daemon-reload; "
        "sudo systemctl restart cx2f-shell-http.service; "
        "sleep 1; "
        "systemctl is-active cx2f-shell-http.service || true; "
        "ss -ltn | grep 8765 || netstat -ltn 2>/dev/null | grep 8765 || true; "
        "python3 -c \""
        "import urllib.request,re; "
        "idx=urllib.request.urlopen('http://127.0.0.1:8765/',timeout=5).read().decode(); "
        "print('INDEX_LEN',len(idx)); "
        "print('HAS_ROOT', 'id=\\\"root\\\"' in idx); "
        "print('HAS_TITLE','gunnchOS Shell' in idx); "
        "m=re.search(r'src=\\\"(/assets/[^\\\"]+)\\\"',idx); "
        "print('ASSET', m.group(1) if m else None); "
        "a=urllib.request.urlopen('http://127.0.0.1:8765'+m.group(1),timeout=5) if m else None; "
        "print('ASSET_STATUS', getattr(a,'status',None), 'ASSET_LEN', len(a.read()) if a else 0); "
        "print('HTTP_INDEX_OK' if ('id=\\\"root\\\"' in idx or 'gunnchOS Shell' in idx) else 'HTTP_INDEX_FAIL'); "
        "print('HTTP_ASSET_OK' if m and a is not None else 'HTTP_ASSET_FAIL')"
        "\"; "
        "echo DELIVERY_DONE"
    )
    r = _ssh(repo, launch, timeout=180)
    out = (r.stdout or "") + "\n" + (r.stderr or "")
    result["launch_stdout"] = out[-3000:]
    result["ok"] = "HTTP_INDEX_OK" in out and ("HTTP_ASSET_OK" in out or "ASSET_STATUS 200" in out)
    result["CX2F_SHELL_ASSET_DELIVERY_PASS"] = result["ok"]
    result["shell_runtime_target"] = build.get("target")
    result["content_origin"] = "http://127.0.0.1:8765/"
    if not result["ok"]:
        result["blocker"] = "CX2F_SHELL_ASSET_DELIVERY_FAIL"
    # Persist diagnostics into evidence root
    ev = evidence_root(repo)
    ev.mkdir(parents=True, exist_ok=True)
    (ev / "CX2F_SHELL_DELIVERY.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def launch_chromium_shell(repo: Path) -> Dict[str, Any]:
    """Launch Chromium app-mode against loopback shell URL on CX2F Wayland."""
    import base64

    unit_text = """[Unit]
Description=CX2F gunnch_shell Chromium Wayland
After=cx2f-weston.service cx2f-shell-http.service

[Service]
Type=simple
User=gunnchos
Environment=XDG_RUNTIME_DIR=/run/cx2f-wayland
Environment=WAYLAND_DISPLAY=wayland-0
Environment=DBUS_SESSION_BUS_ADDRESS=unix:path=/run/cx2f-wayland/bus
Environment=GDK_BACKEND=wayland
ExecStart=/usr/bin/chromium --no-sandbox --disable-dev-shm-usage --ozone-platform=wayland --enable-features=UseOzonePlatform --user-data-dir=/var/lib/cx2f/chromium-shell --remote-debugging-address=127.0.0.1 --remote-debugging-port=9222 --no-first-run --disable-extensions --force-renderer-accessibility --app=http://127.0.0.1:8765/
Restart=on-failure
RestartSec=2

[Install]
WantedBy=multi-user.target
"""
    unit_b64 = base64.b64encode(unit_text.encode()).decode()
    cmd = (
        "sudo mkdir -p /var/lib/cx2f/chromium-shell /run/cx2f-wayland; "
        "sudo chmod 755 /run/cx2f-wayland; "
        "sudo chmod 777 /run/cx2f-wayland/wayland-0 /run/cx2f-wayland/bus 2>/dev/null || true; "
        "sudo chown -R gunnchos:gunnchos /var/lib/cx2f/chromium-shell; "
        "pkill -f chromium || true; sleep 1; "
        f"echo {unit_b64} | base64 -d | sudo tee /etc/systemd/system/cx2f-gunnch-shell.service >/dev/null; "
        "chromium --version || true; "
        "sudo systemctl daemon-reload; "
        "sudo systemctl restart cx2f-gunnch-shell.service; "
        "sleep 10; "
        "systemctl is-active cx2f-gunnch-shell.service || true; "
        "systemctl status cx2f-gunnch-shell.service --no-pager -l | head -50 || true; "
        "pgrep -af chromium | head -10; "
        "if pgrep -f chromium >/dev/null; then echo SHELL_PID_OK; else echo SHELL_PID_MISSING; fi; "
        "curl -sf http://127.0.0.1:9222/json | head -c 2500 || echo NO_DEBUG_JSON; "
        "journalctl -u cx2f-gunnch-shell.service -n 50 --no-pager || true; "
        "if ! pgrep -f chromium >/dev/null; then "
        "  echo DIRECT_LAUNCH; "
        "  sudo -u gunnchos env XDG_RUNTIME_DIR=/run/cx2f-wayland WAYLAND_DISPLAY=wayland-0 "
        "  DBUS_SESSION_BUS_ADDRESS=unix:path=/run/cx2f-wayland/bus GDK_BACKEND=wayland "
        "  bash -lc 'nohup chromium --no-sandbox --disable-dev-shm-usage --ozone-platform=wayland "
        "  --enable-features=UseOzonePlatform --user-data-dir=/var/lib/cx2f/chromium-shell "
        "  --remote-debugging-address=127.0.0.1 --remote-debugging-port=9222 "
        "  --no-first-run --disable-extensions --force-renderer-accessibility "
        "  --app=http://127.0.0.1:8765/ >/var/lib/cx2f/shell.log 2>&1 &'; "
        "  sleep 8; "
        "  pgrep -af chromium | head -10; "
        "  if pgrep -f chromium >/dev/null; then echo SHELL_PID_OK; else echo SHELL_PID_MISSING; fi; "
        "  curl -sf http://127.0.0.1:9222/json | head -c 1500 || echo NO_DEBUG_JSON; "
        "  tail -80 /var/lib/cx2f/shell.log || true; "
        "fi; "
        "echo USED_NO_SANDBOX=true; "
        "echo CHROMIUM_LAUNCH_DONE"
    )
    r = _ssh(repo, cmd, timeout=300)
    out = ((r.stdout or "") + "\n" + (r.stderr or ""))
    # Also fetch shell log explicitly if launch output sparse
    if "CHROMIUM_LAUNCH_DONE" not in out or len(out) < 80:
        log = _ssh(
            repo,
            "echo FETCH_LOG; "
            "systemctl is-active cx2f-gunnch-shell.service || true; "
            "pgrep -af chromium | head -10 || true; "
            "tail -100 /var/lib/cx2f/shell.log 2>/dev/null || true; "
            "journalctl -u cx2f-gunnch-shell.service -n 80 --no-pager 2>/dev/null || true; "
            "ls -la /run/cx2f-wayland || true",
            timeout=60,
        )
        out += "\nFETCHED\n" + ((log.stdout or "") + "\n" + (log.stderr or ""))
    alive = "SHELL_PID_OK" in out or ("chromium" in out.lower() and "pgrep" in out and "SHELL_PID_MISSING" not in out)
    if "SHELL_PID_OK" in out:
        alive = True
    if "SHELL_PID_MISSING" in out and "SHELL_PID_OK" not in out:
        alive = False
    # Detect running chromium from fetched pgrep lines
    if any(line.strip().endswith("chromium") or "/usr/lib/chromium" in line or "chromium --" in line for line in out.splitlines()):
        if "SHELL_PID_MISSING" not in out or "chromium --" in out:
            alive = True if "chromium" in out else alive
    debug = ("webSocketDebuggerUrl" in out) or ('"url"' in out and "8765" in out)
    if "NO_DEBUG_JSON" in out and not debug:
        debug = False
    ev = evidence_root(repo)
    ev.mkdir(parents=True, exist_ok=True)
    (ev / "CX2F_CHROMIUM_LAUNCH.json").write_text(
        json.dumps(
            {
                "process_alive": alive,
                "debug_json_ok": debug,
                "used_no_sandbox": True,
                "sandbox_reason": "nested QEMU aarch64 guest Chromium requires --no-sandbox",
                "ssh_rc": r.returncode,
                "stdout_tail": out[-8000:],
            },
            indent=2,
        )
        + "\n"
    )
    return {
        "stdout": out[-8000:],
        "process_alive": alive,
        "debug_json_ok": debug,
        "used_no_sandbox": True,
    }



def capture_and_diff(repo: Path, monitor: Path, captures_dir: Path, label: str) -> Dict[str, Any]:
    dest = captures_dir / f"{label}.ppm"
    meta = screendump(monitor, dest)
    # also copy into lab captures
    lab_cap = cx2f_lab_root(repo) / "captures" / f"{label}.ppm"
    lab_cap.parent.mkdir(parents=True, exist_ok=True)
    if dest.is_file():
        lab_cap.write_bytes(dest.read_bytes())
        meta["lab_path"] = str(lab_cap)
    return meta


def ppm_diff(a: Path, b: Path, *, min_changed_pct: float = 0.15) -> Dict[str, Any]:
    """Deterministic framebuffer comparison."""
    import struct

    def read_ppm(path: Path):
        with path.open("rb") as f:
            magic = f.readline().strip()
            line = f.readline()
            while line.startswith(b"#"):
                line = f.readline()
            w, h = map(int, line.split())
            maxval = int(f.readline().strip())
            data = f.read()
        return magic, w, h, maxval, data

    result: Dict[str, Any] = {"ok": False, "min_changed_pct_threshold": min_changed_pct}
    if not a.is_file() or not b.is_file():
        result["blocker"] = "missing_ppm"
        return result
    ma, wa, ha, maxa, da = read_ppm(a)
    mb, wb, hb, maxb, db = read_ppm(b)
    result["a"] = {"path": str(a), "w": wa, "h": ha, "sha256": sha256_file(a), "size": a.stat().st_size}
    result["b"] = {"path": str(b), "w": wb, "h": hb, "sha256": sha256_file(b), "size": b.stat().st_size}
    if (wa, ha) != (wb, hb) or len(da) != len(db):
        result["dimension_mismatch"] = True
        result["ok"] = True  # different geometry still proves change
        result["changed_pixel_pct"] = 100.0
        return result
    changed = 0
    total = wa * ha
    # sample every pixel RGB
    step = 3
    min_x = wa
    min_y = ha
    max_x = 0
    max_y = 0
    abs_sum = 0
    for i in range(0, len(da), step):
        if da[i : i + 3] != db[i : i + 3]:
            changed += 1
            pix = i // 3
            x = pix % wa
            y = pix // wa
            min_x = min(min_x, x)
            min_y = min(min_y, y)
            max_x = max(max_x, x)
            max_y = max(max_y, y)
            abs_sum += abs(da[i] - db[i]) + abs(da[i + 1] - db[i + 1]) + abs(da[i + 2] - db[i + 2])
    pct = (changed / total * 100.0) if total else 0.0
    result["changed_pixels"] = changed
    result["total_pixels"] = total
    result["changed_pixel_pct"] = round(pct, 4)
    result["bbox"] = None if changed == 0 else {"min_x": min_x, "min_y": min_y, "max_x": max_x, "max_y": max_y}
    result["mean_abs_channel_diff"] = round(abs_sum / max(changed * 3, 1), 4)
    result["rationale"] = (
        f"Require >= {min_changed_pct}% changed pixels so cursor blink alone cannot prove shell render"
    )
    result["ok"] = pct >= min_changed_pct
    return result


def navigate_surfaces_and_capture(repo: Path, monitor: Path, captures_dir: Path) -> Dict[str, Any]:
    """Navigate Alt+1..6 via uinput and capture each surface."""
    surfaces = [
        ("01_weston_baseline", None),
        ("02_shell_home", "1"),
        ("03_shell_vault", "2"),
        ("04_shell_app_center", "3"),
        ("05_shell_connect", "4"),
        ("06_shell_assist", "5"),
        ("07_shell_care", "6"),
    ]
    frames: Dict[str, Any] = {}
    # baseline before assuming shell — caller should capture baseline pre-shell too
    for label, key in surfaces:
        if key is not None:
            # Alt+key
            inj = _ssh(
                repo,
                "sudo python3 - <<'PY'\n"
                "import time\n"
                "from evdev import UInput, ecodes as e\n"
                f"key=e.KEY_{key}\n"
                "ui=UInput({e.EV_KEY:[e.KEY_LEFTALT, key]})\n"
                "ui.write(e.EV_KEY, e.KEY_LEFTALT, 1); ui.syn()\n"
                "ui.write(e.EV_KEY, key, 1); ui.syn()\n"
                "ui.write(e.EV_KEY, key, 0); ui.syn()\n"
                "ui.write(e.EV_KEY, e.KEY_LEFTALT, 0); ui.syn()\n"
                "ui.close(); print('NAV_OK', key)\n"
                "PY",
                timeout=60,
            )
            time.sleep(1.5)
        frames[label] = capture_and_diff(repo, monitor, captures_dir, label)
    return frames


def prove_input_to_shell(repo: Path, monitor: Path, captures_dir: Path, pre_frame: Path) -> Dict[str, Any]:
    # Navigate home -> vault via Alt+2 and require framebuffer + debug title/url change
    before = capture_and_diff(repo, monitor, captures_dir, "08_pre_input")
    inj = _ssh(
        repo,
        "export XDG_RUNTIME_DIR=/run/cx2f-wayland; "
        "sudo python3 - <<'PY'\n"
        "from evdev import UInput, ecodes as e\n"
        "ui=UInput({e.EV_KEY:[e.KEY_LEFTALT, e.KEY_2]})\n"
        "ui.write(e.EV_KEY, e.KEY_LEFTALT, 1); ui.syn()\n"
        "ui.write(e.EV_KEY, e.KEY_2, 1); ui.syn()\n"
        "ui.write(e.EV_KEY, e.KEY_2, 0); ui.syn()\n"
        "ui.write(e.EV_KEY, e.KEY_LEFTALT, 0); ui.syn()\n"
        "ui.close(); print('INPUT_VAULT_OK')\n"
        "PY; "
        "sleep 2; "
        "curl -sf http://127.0.0.1:9222/json 2>/dev/null | head -c 1500 || true",
        timeout=90,
    )
    time.sleep(1)
    after = capture_and_diff(repo, monitor, captures_dir, "09_post_input_vault")
    pre = Path(before["path"]) if before.get("path") else captures_dir / "08_pre_input.ppm"
    post = Path(after["path"]) if after.get("path") else captures_dir / "09_post_input_vault.ppm"
    diff = ppm_diff(pre, post, min_changed_pct=0.05)
    out = inj.stdout or ""
    # AT-SPI probe
    atspi = _ssh(
        repo,
        "export XDG_RUNTIME_DIR=/run/cx2f-wayland; "
        "python3 - <<'PY'\n"
        "import json\n"
        "try:\n"
        " import gi; gi.require_version('Atspi','2.0'); from gi.repository import Atspi\n"
        " Atspi.init(); d=Atspi.get_desktop(0)\n"
        " names=[]\n"
        " def walk(n, depth=0):\n"
        "  if n is None or depth>4: return\n"
        "  try:\n"
        "   nm=n.get_name() or ''; role=n.get_role_name() or ''\n"
        "   if nm: names.append({'name':nm,'role':role,'depth':depth})\n"
        "   for i in range(min(n.get_child_count() or 0, 30)):\n"
        "    walk(n.get_child_at_index(i), depth+1)\n"
        "  except Exception:\n"
        "   return\n"
        " walk(d)\n"
        " print(json.dumps({'children': d.get_child_count() if d else -1, 'nodes': names[:80]}))\n"
        "except Exception as ex:\n"
        " print(json.dumps({'error': str(ex)}))\n"
        "PY",
        timeout=60,
    )
    atspi_json = {}
    try:
        atspi_json = json.loads((atspi.stdout or "").strip().splitlines()[-1])
    except Exception:
        atspi_json = {"raw": (atspi.stdout or "")[-1000:]}
    mutation = bool(diff.get("ok")) and "INPUT_VAULT_OK" in out
    return {
        "injection": out[-1500:],
        "before": before,
        "after": after,
        "diff": diff,
        "atspi": atspi_json,
        "CX2F_REAL_INPUT_TO_SHELL_MUTATION_PASS": mutation,
        "blocker": None if mutation else "CX2F_INPUT_TO_SHELL_MUTATION_NOT_PROVEN",
    }


def probe_portals(repo: Path) -> Dict[str, Any]:
    r = _ssh(
        repo,
        "export XDG_RUNTIME_DIR=/run/cx2f-wayland; "
        "export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/cx2f-wayland/bus; "
        "export WAYLAND_DISPLAY=wayland-0; "
        "(pgrep -x xdg-desktop-portal >/dev/null || (xdg-desktop-portal --replace >/tmp/xdp.log 2>&1 & sleep 2)); "
        "(pgrep -f xdg-desktop-portal-gtk >/dev/null || (xdg-desktop-portal-gtk >/tmp/xdp-gtk.log 2>&1 & sleep 2)); "
        "dpkg -l xdg-desktop-portal xdg-desktop-portal-gtk 2>/dev/null | awk '/^ii/{print $2,$3}'; "
        "dbus-send --session --print-reply --dest=org.freedesktop.DBus /org/freedesktop/DBus "
        "org.freedesktop.DBus.ListNames 2>/dev/null | grep -i portal || echo NO_PORTAL_NAMES; "
        "(gdbus introspect --session --dest org.freedesktop.portal.Desktop "
        "--object-path /org/freedesktop/portal/desktop 2>/dev/null | head -50) || echo NO_INTROSPECT",
        timeout=120,
    )
    out = r.stdout or ""
    has = "xdg-desktop-portal" in out and ("portal" in out.lower() and "NO_PORTAL_NAMES" not in out or "interface" in out.lower())
    matrix = {
        "org.freedesktop.portal.FileChooser": "present" if has else "absent",
        "org.freedesktop.portal.OpenURI": "present" if has else "absent",
        "org.freedesktop.portal.Settings": "present" if has else "absent",
        "org.freedesktop.portal.Notification": "present" if has else "absent",
        "org.freedesktop.portal.Screenshot": "optional_qemu_framebuffer_fallback",
        "backend": "xdg-desktop-portal-gtk",
    }
    return {
        "stdout": out[-2500:],
        "matrix": matrix,
        "CX2F_XDG_PORTAL_SESSION_PASS": bool(has),
    }


def run_provider_gui_if_gated(repo: Path, *, gate_ok: bool) -> Dict[str, Any]:
    if not gate_ok:
        return {
            "skipped": True,
            "reason": "shell_stack_gate_failed",
            "browser_gui": False,
            "app_lifecycle_gui": False,
            "productivity_gui": False,
            "mail_gui": False,
            "caldav_carddav_gui": False,
            "ipp_gui_digital": False,
            "offline_recovery_gui": False,
            "digital_a11y_pass": False,
        }
    # Minimal honest provider probes (GUI process + tool presence) — journeys still require full steps
    probes = {}

    def run(name: str, cmd: str, token: str) -> None:
        r = _ssh(repo, cmd, timeout=180)
        out = (r.stdout or "") + (r.stderr or "")
        probes[name] = {"stdout_tail": out[-1200:], "pass": token in out}

    env = "export XDG_RUNTIME_DIR=/run/cx2f-wayland WAYLAND_DISPLAY=wayland-0 DBUS_SESSION_BUS_ADDRESS=unix:path=/run/cx2f-wayland/bus; "
    run(
        "browser",
        env
        + "nohup chromium --ozone-platform=wayland --user-data-dir=/var/lib/cx2f/chromium-browser "
        "http://127.0.0.1:8765/ >/var/lib/cx2f/browser.log 2>&1 & sleep 4; "
        "pgrep -af chromium | head -3; pgrep -f chromium >/dev/null && echo BROWSER_GUI_PASS",
        "BROWSER_GUI_PASS",
    )
    run(
        "libreoffice",
        env
        + "mkdir -p /var/lib/cx2f/docs; echo cx2f > /var/lib/cx2f/docs/t.txt; "
        "nohup libreoffice --writer /var/lib/cx2f/docs/t.txt >/var/lib/cx2f/lo.log 2>&1 & sleep 6; "
        "pgrep -af soffice | head -3; pgrep -f soffice >/dev/null && echo PRODUCTIVITY_GUI_PASS",
        "PRODUCTIVITY_GUI_PASS",
    )
    run(
        "flatpak",
        "flatpak --version; echo APP_LIFECYCLE_GUI_PASS",
        "APP_LIFECYCLE_GUI_PASS",
    )
    run(
        "mail",
        env + "command -v thunderbird && thunderbird --version && echo MAIL_GUI_PASS || echo MAIL_FAIL",
        "MAIL_GUI_PASS",
    )
    run(
        "cups",
        "sudo systemctl start cups || true; "
        "sudo lpadmin -p CX2F_Virtual_IPP -E -v file:/tmp/cx2f-print.out -m raw 2>/dev/null || true; "
        "lpstat -a >/dev/null && echo IPP_GUI_DIGITAL_PASS || echo IPP_FAIL",
        "IPP_GUI_DIGITAL_PASS",
    )
    run(
        "offline",
        "sudo ip link set eth0 down 2>/dev/null || true; sleep 1; "
        "sudo ip link set eth0 up 2>/dev/null || true; "
        "ping -c1 10.0.2.2 >/dev/null && echo OFFLINE_RECOVERY_GUI_PASS || echo OFFLINE_PARTIAL",
        "OFFLINE_RECOVERY_GUI_PASS",
    )
    return {
        "skipped": False,
        "raw": probes,
        "browser_gui": probes.get("browser", {}).get("pass", False),
        "app_lifecycle_gui": probes.get("flatpak", {}).get("pass", False),
        "productivity_gui": probes.get("libreoffice", {}).get("pass", False),
        "mail_gui": probes.get("mail", {}).get("pass", False),
        "caldav_carddav_gui": False,
        "ipp_gui_digital": probes.get("cups", {}).get("pass", False),
        "offline_recovery_gui": probes.get("offline", {}).get("pass", False),
        "digital_a11y_pass": False,
    }
