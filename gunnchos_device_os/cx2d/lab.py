"""Isolated CX2D Linux lab — distinct from Device Lab interactive guest."""

from __future__ import annotations

import hashlib
import textwrap
import json
import os
import platform
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Optional

# Never write into Device Lab release evidence paths.
DEVICE_LAB_FORBIDDEN = (
    "os_build/device_lab_interactive_guest/artifacts",
    "os_build/device_lab_interactive_guest/pipeline",
)


def repo_root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


def cx2d_lab_root(repo: Optional[Path] = None) -> Path:
    return (repo or repo_root_from_here()) / "os_build" / "cx2d_linux_lab"


def evidence_root(repo: Optional[Path] = None) -> Path:
    return (repo or repo_root_from_here()) / "artifacts" / "complete_experience" / "cx2d"


def sha256_file(path: Path) -> Optional[str]:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def host_capabilities() -> Dict[str, Any]:
    qemu_a = shutil.which("qemu-system-aarch64")
    qemu_x = shutil.which("qemu-system-x86_64")
    return {
        "host_os": platform.system(),
        "host_machine": platform.machine(),
        "host_release": platform.release(),
        "qemu_system_aarch64": qemu_a,
        "qemu_system_x86_64": qemu_x,
        "weston_on_host": shutil.which("weston"),
        "flatpak_on_host": shutil.which("flatpak"),
        "display": os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"),
        "xdg_runtime_dir": os.environ.get("XDG_RUNTIME_DIR"),
    }


def ensure_lab_tree(repo: Optional[Path] = None) -> Path:
    root = cx2d_lab_root(repo)
    for sub in ("config", "cloud-init", "scripts", "work", "images", "overlays", "evidence"):
        (root / sub).mkdir(parents=True, exist_ok=True)
    return root


def base_image_candidates(repo: Path) -> Dict[str, Path]:
    """Reference Device Lab *cache* only as a read-only source; never mutate it."""
    cache = repo / "os_build" / "device_lab_interactive_guest" / "cache" / "debian-12-genericcloud-arm64.qcow2"
    return {"debian12_genericcloud_arm64_cache_ro": cache}


def prepare_cx2d_overlay(repo: Optional[Path] = None) -> Dict[str, Any]:
    """Create a CX2D-owned qcow2 overlay pointing at a *copied* base in CX2D namespace.

    Does not modify Device Lab artifacts/pipeline. If base cache is unavailable,
    records an honest blocker.
    """
    repo = repo or repo_root_from_here()
    lab = ensure_lab_tree(repo)
    caps = host_capabilities()
    candidates = base_image_candidates(repo)
    src = candidates["debian12_genericcloud_arm64_cache_ro"]
    dest_base = lab / "images" / "debian-12-genericcloud-arm64.qcow2"
    overlay = lab / "overlays" / "cx2d-aarch64.qcow2"
    result: Dict[str, Any] = {
        "ok": False,
        "arch": "aarch64",
        "distro": "debian",
        "version": "12 (bookworm) genericcloud",
        "compositor_target": "weston",
        "base_source_ro": str(src),
        "base_copy": str(dest_base),
        "overlay": str(overlay),
        "host": caps,
        "blocker": None,
    }
    if not src.is_file():
        result["blocker"] = (
            "CX2D_BASE_IMAGE_MISSING: debian-12-genericcloud-arm64.qcow2 not present "
            "under Device Lab cache (read-only reference). Cannot provision CX2D lab."
        )
        return result
    if not caps.get("qemu_system_aarch64"):
        result["blocker"] = "CX2D_QEMU_AARCH64_MISSING: qemu-system-aarch64 not on PATH."
        return result

    # Copy base into CX2D namespace if needed (distinct from Device Lab artifacts).
    if not dest_base.is_file():
        # Prefer hardlink then copy to avoid mutating source.
        try:
            os.link(src, dest_base)
        except OSError:
            shutil.copy2(src, dest_base)

    # Create overlay via qemu-img if missing
    if not overlay.is_file():
        cmd = ["qemu-img", "create", "-f", "qcow2", "-F", "qcow2", "-b", str(dest_base), str(overlay)]
        try:
            subprocess.run(cmd, check=True, capture_output=True, text=True)
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            result["blocker"] = f"CX2D_OVERLAY_CREATE_FAILED: {exc}"
            return result

    result["ok"] = True
    result["base_sha256"] = sha256_file(dest_base)
    result["overlay_sha256"] = sha256_file(overlay)
    return result


def write_cloud_init_payload(lab: Path) -> Dict[str, str]:
    """Write CX2D-specific cloud-init (packages for graphical ordinary-computer lab)."""
    user_data = textwrap.dedent(
        """        #cloud-config
        hostname: cx2d-linux-lab
        manage_etc_hosts: true
        users:
          - name: gunnchos
            sudo: ALL=(ALL) NOPASSWD:ALL
            shell: /bin/bash
            groups: [sudo, video, render, audio]
        package_update: true
        packages:
          - weston
          - seatd
          - dbus-user-session
          - xdg-desktop-portal
          - xdg-desktop-portal-wlr
          - flatpak
          - cups
          - cups-bsd
          - chromium
          - libreoffice
          - at-spi2-core
          - orca
          - grim
          - pipewire
          - wireplumber
          - python3
          - python3-gi
          - gir1.2-atspi-2.0
        runcmd:
          - [ bash, -c, "mkdir -p /run/user/1000 /var/lib/cx2d && chown gunnchos:gunnchos /run/user/1000 /var/lib/cx2d" ]
          - [ bash, -c, "echo CX2D_LAB_PROVISIONED=1 > /var/lib/cx2d/PROVISIONED" ]
        power_state:
          mode: poweroff
          timeout: 30
          condition: true
        """
    )
    meta = "instance-id: cx2d-linux-lab-1\nlocal-hostname: cx2d-linux-lab\n"
    ud_path = lab / "cloud-init" / "user-data"
    md_path = lab / "cloud-init" / "meta-data"
    ud_path.write_text(user_data)
    md_path.write_text(meta)
    return {
        "user_data": str(ud_path),
        "meta_data": str(md_path),
        "user_data_sha256": sha256_text(user_data),
        "meta_data_sha256": sha256_text(meta),
    }


# fix textwrap reference
def attempt_lab_status(repo: Optional[Path] = None) -> Dict[str, Any]:
    """Prepare CX2D lab assets and report whether a full graphical session is proven.

    Honest rule: preparing overlay/cloud-init is NOT a rendered GUI PASS.
    Full guest provision is optional/long-running; agent records blocker when
    host cannot complete Linux graphical session in this environment.
    """
    repo = repo or repo_root_from_here()
    lab = ensure_lab_tree(repo)
    cloud = write_cloud_init_payload(lab)
    overlay = prepare_cx2d_overlay(repo)
    caps = host_capabilities()
    script = lab / "scripts" / "provision_cx2d_linux_lab.py"
    provision_hash = sha256_file(script) if script.is_file() else None

    # Darwin host without nested Linux Wayland session cannot claim Linux GUI.
    graphical_session_proven = False
    blocker = overlay.get("blocker")
    if platform.system() != "Linux" and not graphical_session_proven:
        blocker = blocker or (
            "CX2D_LINUX_GUI_SESSION_NOT_PROVEN_ON_HOST: agent host is "
            f"{platform.system()}/{platform.machine()}; CX2D overlay/cloud-init "
            "scaffolding is ready under os_build/cx2d_linux_lab/, but a real "
            "Weston/Wayland + DBus + portal session inside the guest was not "
            "completed/captured as rendered journey evidence in this run. "
            "Fail closed on REAL_USER_JOURNEY_DIGITAL_PASS and CX2D_REAL_*_WINDOW."
        )

    status = {
        "schema": "gunnchos.cx2d.linux_lab_status.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "lab_root": str(lab),
        "overlay_prep": overlay,
        "cloud_init": cloud,
        "host": caps,
        "graphical_session_proven": graphical_session_proven,
        "provision_script_sha256": provision_hash,
        "blocker": blocker,
        "device_lab_paths_untouched": True,
        "evidence_namespace": "artifacts/complete_experience/cx2d",
    }
    ev = evidence_root(repo)
    ev.mkdir(parents=True, exist_ok=True)
    (ev / "CX2D_LINUX_LAB_STATUS.json").write_text(json.dumps(status, indent=2) + "\n")
    return status


def build_provenance(repo: Optional[Path] = None, status: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    repo = repo or repo_root_from_here()
    status = status or attempt_lab_status(repo)
    try:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
        branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo, text=True).strip()
    except Exception:
        head, branch = "unknown", "unknown"
    overlay = status.get("overlay_prep") or {}
    prov = {
        "schema": "gunnchos.cx2d.linux_lab_provenance.v1",
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "distro": overlay.get("distro", "debian"),
        "version": overlay.get("version", "12"),
        "architecture": overlay.get("arch", "aarch64"),
        "kernel": "guest_kernel_pending_boot_proof",
        "compositor": "weston (target; session not proven this run)",
        "package_versions": {
            "weston": "pending_guest_dpkg",
            "chromium": "pending_guest_dpkg",
            "libreoffice": "pending_guest_dpkg",
            "flatpak": "pending_guest_dpkg",
            "cups": "pending_guest_dpkg",
            "xdg-desktop-portal": "pending_guest_dpkg",
            "at-spi2-core": "pending_guest_dpkg",
            "orca": "pending_guest_dpkg",
        },
        "image_base_sha256": overlay.get("base_sha256"),
        "overlay_sha256": overlay.get("overlay_sha256"),
        "provisioning_script_sha256": status.get("provision_script_sha256"),
        "cloud_init_user_data_sha256": (status.get("cloud_init") or {}).get("user_data_sha256"),
        "runtime_resources": {
            "target_ram_mb": 4096,
            "target_cpus": 4,
            "host": status.get("host"),
        },
        "source_branch": branch,
        "source_head": head,
        "graphical_session_proven": status.get("graphical_session_proven", False),
        "blocker": status.get("blocker"),
        "claim_boundary": "Expansion lab scaffolding; not Software Pilot / Device Lab #134 evidence.",
    }
    out = evidence_root(repo) / "CX2D_LINUX_LAB_PROVENANCE.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(prov, indent=2) + "\n")
    return prov
