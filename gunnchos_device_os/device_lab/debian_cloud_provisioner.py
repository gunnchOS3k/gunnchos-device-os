"""gunnchOS Device Lab Interactive Development Guest — guest-native provisioner.

Cycle 3B WP-011R. Provisions the Interactive Development Guest by booting the
**official Debian 12 (bookworm) `genericcloud-arm64` cloud image inside QEMU**
and letting **cloud-init** (running natively inside the aarch64 guest kernel)
install and configure real packages. This is guest-native provisioning: no
Mac foreign-arch chroot, no binfmt_misc, no Docker cross-build required. The
only foreign-arch code that ever executes is the guest's own aarch64 Linux
kernel/userspace, run by QEMU (HVF-accelerated on Apple Silicon).

Why Debian genericcloud instead of the Alpine `setup-alpine` ISO path
(`scripts/provision_interactive_guest_qemu_native.py`, evaluated first):

- cloud-init is a **declarative** provisioning contract (YAML `user-data`)
  with no serial-console prompt-timing to get right. The Alpine ISO path
  requires scripting `setup-alpine`'s interactive Q&A over a raw serial pty,
  which is brittle against boot-message/prompt-timing drift across Alpine
  point releases.
- Debian's `weston`, `chromium`, `mousepad`, `pipewire`/`wireplumber`,
  `libinput-tools`, `wayland-utils`, `python3-evdev`, and `godot3` packages
  are all present in the bookworm archive with real dependency resolution;
  the Alpine apk equivalents exist too, but pulling them requires either a
  Docker linux/arm64 VM or a Linux binfmt_misc host to run apk's post-install
  trigger scripts — neither is available on this Mac (see
  `os_build/device_lab_interactive_guest/scripts/build_interactive_rootfs_alpine_aarch64.sh`
  and its honest non-zero-exit history). Cloud-init sidesteps that problem
  entirely because *the guest's own aarch64 dpkg* runs the install, inside
  QEMU, natively — no cross-arch package-manager trick needed.
- Trade-off, stated honestly: the Debian cloud image is larger (~340MB vs
  Alpine's ~200MB ISO) and glibc-based (bigger footprint than musl), and this
  module is therefore the *chosen* primary path, not the *only theoretically
  possible* one. The Alpine ISO path remains in the repo, evaluated, for
  future refinement.

Claim boundary: DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST=true,
SHIPPING_IMAGE=false, SILICON_EXACT_EMULATION=false always. Producing a
provisioned disk does not, by itself, earn any `*_PASS` token — see
`os_build/device_lab_interactive_guest/README.md`.
"""
from __future__ import annotations

import hashlib
import http.server
import json
import os
import platform
import shutil
import socketserver
import subprocess
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "gunnchos.device_lab.interactive_guest_debian_cloud_provision.v1"
PROVISION_VERSION = "1.0.0-debian-cloud-init"

DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST = True
SHIPPING_IMAGE = False
SILICON_EXACT_EMULATION = False

DEBIAN_RELEASE = "bookworm"
DEBIAN_IMAGE_VARIANT = "genericcloud"
DEBIAN_ARCH = "arm64"
IMAGE_NAME = f"debian-12-{DEBIAN_IMAGE_VARIANT}-{DEBIAN_ARCH}.qcow2"
IMAGE_BASE_URL = f"https://cloud.debian.org/images/cloud/{DEBIAN_RELEASE}/latest"
IMAGE_URL = f"{IMAGE_BASE_URL}/{IMAGE_NAME}"
CHECKSUMS_URL = f"{IMAGE_BASE_URL}/SHA512SUMS"

DEFAULT_DISK_SIZE_GB = 16
DEFAULT_MEMORY_MB = 4096
DEFAULT_SMP = 4
DEFAULT_PROVISION_TIMEOUT_S = 2700  # 45 min honest ceiling for first-boot apt install over slirp NAT
PROVISION_OK_SENTINEL = "GUNNCHOS_INTERACTIVE_GUEST_PROVISION_OK"
PROVISION_FAIL_SENTINEL = "GUNNCHOS_INTERACTIVE_GUEST_PROVISION_FAILED"

REQUIRED_APT_PACKAGES: tuple[str, ...] = (
    # Cloud kernel (linux-image-*-cloud-arm64) ships WITHOUT DRM/virtio-gpu and
    # often WITHOUT uinput — which makes LIVE compositor proofs impossible.
    # Install the standard arm64 kernel so /dev/dri and /dev/uinput exist after reboot.
    "linux-image-arm64",
    "weston",
    "seatd",
    "libseat1",
    "kbd",  # openvt — required for DRM VT claim when logind session is absent
    "libgl1-mesa-dri",
    "mesa-utils",
    "libinput-tools",
    "evtest",
    "python3",
    "python3-evdev",
    "python3-pip",
    "wayland-utils",
    "chromium",
    "mousepad",
    "pipewire",
    "pipewire-pulse",
    "pipewire-alsa",
    "wireplumber",
    "openssh-server",
    "foot",
    "grim",
    "libreoffice-writer",
    "libreoffice-gtk3",
)
# Best-effort only — Pedestrian Pursuit needs Godot 4.x (bundled separately);
# Debian godot3 remains optional legacy, never enough for FOUR_GAME alone.
OPTIONAL_APT_PACKAGES: tuple[str, ...] = ("godot3", "labwc", "wlr-randr")

CLAIM_BOUNDARY = (
    "gunnchOS Device Lab Interactive Development Guest: Debian 12 genericcloud "
    "arm64 cloud image, provisioned guest-natively inside QEMU via cloud-init "
    "(no Mac foreign-arch chroot/binfmt/Docker). "
    "DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST=true. SHIPPING_IMAGE=false. "
    "SILICON_EXACT_EMULATION=false. A successful provision run means packages "
    "installed and the guest reported readiness over its own serial console — "
    "it does not by itself earn LIVE_GUNNCHOS_VISUAL_PASS, "
    "DSXL_DUAL_COMPOSITOR_UX_PASS, or RING_TO_REAL_APP_STATE_MUTATION_PASS; "
    "those require a live guest-agent session with real evidence."
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def interactive_root(repo_root: Path | None = None) -> Path:
    return (repo_root or _repo_root()) / "os_build" / "device_lab_interactive_guest"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha512_file(path: Path) -> str:
    h = hashlib.sha512()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


# --------------------------------------------------------------------------
# Pure / testable helpers (no network, no subprocess side effects)
# --------------------------------------------------------------------------


def parse_sha512sums(text: str, filename: str) -> str | None:
    """Parse a BSD/coreutils-style SHA512SUMS listing for one filename."""
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        digest, name = parts[0], parts[-1]
        name = name.lstrip("*")
        if name == filename or name.endswith("/" + filename):
            return digest.lower()
    return None


def find_edk2_firmware() -> Path | None:
    for cand in (
        "/opt/homebrew/share/qemu/edk2-aarch64-code.fd",
        "/opt/homebrew/opt/qemu/share/qemu/edk2-aarch64-code.fd",
        "/usr/share/qemu/edk2-aarch64-code.fd",
        "/usr/share/AAVMF/AAVMF_CODE.fd",
    ):
        p = Path(cand)
        if p.is_file():
            return p
    return None


def find_qemu_img() -> str | None:
    return shutil.which("qemu-img") or (
        "/opt/homebrew/bin/qemu-img" if Path("/opt/homebrew/bin/qemu-img").exists() else None
    )


def find_qemu_system_aarch64() -> str | None:
    return shutil.which("qemu-system-aarch64") or (
        "/opt/homebrew/bin/qemu-system-aarch64"
        if Path("/opt/homebrew/bin/qemu-system-aarch64").exists()
        else None
    )


def render_guest_agent_service(*, agent_script_path: str = "/opt/gunnchos/bin/gunnchos_guest_agent.py") -> str:
    tmpl = (interactive_root() / "debian_cloud" / "systemd" / "gunnchos-guest-agent.service").read_text(
        encoding="utf-8"
    )
    return tmpl.replace("/opt/gunnchos/bin/gunnchos_guest_agent.py", agent_script_path)


def build_cloud_init_user_data(
    *,
    guest_agent_script: str,
    guest_agent_service: str,
    weston_service: str,
    weston_ini: str,
    root_password: str = "gunnchos-lab",
    extra_packages: tuple[str, ...] = (),
) -> str:
    """Build the `user-data` cloud-config text. Pure function — testable without QEMU/network."""
    packages = list(REQUIRED_APT_PACKAGES) + list(extra_packages)
    packages_yaml = "\n".join(f"  - {p}" for p in packages)

    def _indent_block(text: str, spaces: int = 6) -> str:
        pad = " " * spaces
        return "\n".join(pad + line if line.strip() else pad.rstrip() for line in text.splitlines())

    optional_installs = " ".join(OPTIONAL_APT_PACKAGES)
    lab_doc = "gunnchOS Device Lab Interactive Guest — Ring app-state mutation target.\n"

    return f"""#cloud-config
hostname: gunnchos-interactive-guest
manage_etc_hosts: true
ssh_pwauth: true
chpasswd:
  expire: false
  list: |
    root:{root_password}
package_update: true
package_upgrade: false
packages:
{packages_yaml}
write_files:
  - path: /opt/gunnchos/bin/gunnchos_guest_agent.py
    permissions: '0755'
    encoding: b64
    content: {_b64(guest_agent_script)}
  - path: /etc/systemd/system/gunnchos-guest-agent.service
    permissions: '0644'
    content: |
{_indent_block(guest_agent_service)}
  - path: /etc/systemd/system/gunnchos-weston.service
    permissions: '0644'
    content: |
{_indent_block(weston_service)}
  - path: /etc/xdg/weston/weston.ini
    permissions: '0644'
    content: |
{_indent_block(weston_ini)}
  - path: /root/gunnchos-lab-document.txt
    permissions: '0644'
    content: |
      {lab_doc.strip()}
  - path: /etc/modules-load.d/gunnchos-lab.conf
    permissions: '0644'
    content: |
      uinput
      virtio_gpu
      virtio_input
  - path: /etc/ssh/sshd_config.d/99-gunnchos-lab.conf
    permissions: '0644'
    content: |
      PermitRootLogin yes
      PasswordAuthentication yes
  - path: /usr/local/sbin/gunnchos-post-provision.sh
    permissions: '0755'
    content: |
      #!/bin/bash
      set -eux
      ls -1 /boot/vmlinuz-* 2>/dev/null | tee /var/log/gunnchos-kernels.txt || true
      # Cloud kernel lacks DRM/uinput — remove it so GRUB boots linux-image-arm64.
      export DEBIAN_FRONTEND=noninteractive
      apt-get remove -y 'linux-image-*-cloud-arm64' 'linux-image-cloud-arm64' || true
      if grep -qv cloud /var/log/gunnchos-kernels.txt 2>/dev/null; then
        sed -i 's/^GRUB_DEFAULT=.*/GRUB_DEFAULT=0/' /etc/default/grub || true
        sed -i 's/^GRUB_CMDLINE_LINUX_DEFAULT=.*/GRUB_CMDLINE_LINUX_DEFAULT="console=ttyAMA0 console=tty0"/' /etc/default/grub || true
        update-grub || true
      fi
      sleep 5
      dpkg -l linux-image-arm64 weston seatd libseat1 kbd chromium mousepad pipewire wireplumber libinput-tools python3-evdev wayland-utils godot3 grim > /var/log/gunnchos-provision-packages.txt 2>&1 || true
      (command -v weston-screenshooter >/dev/null 2>&1 && echo weston-screenshooter=present || echo weston-screenshooter=absent) >> /var/log/gunnchos-provision-packages.txt
runcmd:
  - [ bash, -c, "mkdir -p /etc/gunnchos-weston /var/lib/gunnchos/screenshots /var/log && cp /etc/xdg/weston/weston.ini /etc/gunnchos-weston/weston.ini" ]
  - [ bash, -c, "modprobe uinput || true; modprobe virtio_gpu || true" ]
  - [ bash, -c, "apt-get install -y --no-install-recommends {optional_installs} > /var/log/gunnchos-optional-install.log 2>&1 || true" ]
  - [ systemctl, daemon-reload ]
  - [ systemctl, enable, --now, seatd.service ]
  - [ systemctl, enable, --now, gunnchos-guest-agent.service ]
  - [ systemctl, enable, gunnchos-weston.service ]
  - [ /usr/local/sbin/gunnchos-post-provision.sh ]
  - [ bash, -c, "echo {PROVISION_OK_SENTINEL} $(date -u +%Y-%m-%dT%H:%M:%SZ) | tee /dev/console /dev/ttyS0 2>/dev/null || echo {PROVISION_OK_SENTINEL} $(date -u +%Y-%m-%dT%H:%M:%SZ) > /dev/console" ]
  - [ bash, -c, "touch /etc/cloud/cloud-init.disabled" ]
power_state:
  mode: poweroff
  message: gunnchos interactive guest provisioning complete
  timeout: 90
  condition: true
"""


def _b64(text: str) -> str:
    import base64

    return base64.b64encode(text.encode("utf-8")).decode("ascii")


def build_cloud_init_meta_data(*, instance_id: str) -> str:
    return f"instance-id: {instance_id}\nlocal-hostname: gunnchos-interactive-guest\n"


def build_qemu_provision_cmd(
    *,
    qemu_bin: str,
    edk2_code: Path,
    edk2_vars: Path,
    disk: Path,
    boot_log: Path,
    pidfile: Path,
    monitor_sock: Path,
    smbios_url: str,
    memory_mb: int = DEFAULT_MEMORY_MB,
    smp: int = DEFAULT_SMP,
    accel: str = "hvf",
    cpu: str = "host",
) -> list[str]:
    """Build the provisioning-boot QEMU command line. Pure — testable without executing it."""
    return [
        qemu_bin,
        "-machine",
        f"virt,accel={accel}",
        "-cpu",
        cpu,
        "-smp",
        str(smp),
        "-m",
        str(memory_mb),
        "-drive",
        f"if=pflash,format=raw,readonly=on,file={edk2_code}",
        "-drive",
        f"if=pflash,format=raw,file={edk2_vars}",
        "-drive",
        f"file={disk},if=virtio,format=qcow2",
        "-netdev",
        "user,id=n0",
        "-device",
        "virtio-net-pci,netdev=n0",
        "-device",
        "virtio-rng-pci",
        "-smbios",
        f"type=1,serial=ds=nocloud-net;s={smbios_url}",
        "-serial",
        f"file:{boot_log}",
        "-display",
        "none",
        "-pidfile",
        str(pidfile),
        "-monitor",
        f"unix:{monitor_sock},server,nowait",
        "-daemonize",
        "-no-reboot",
    ]


def select_provision_accel() -> dict[str, str]:
    if platform.system() == "Darwin" and platform.machine() == "arm64":
        return {"accel": "hvf", "cpu": "host"}
    if Path("/dev/kvm").exists():
        return {"accel": "kvm", "cpu": "host"}
    return {"accel": "tcg", "cpu": "max"}


# --------------------------------------------------------------------------
# Cloud-init seed HTTP server (NoCloud net datasource)
# --------------------------------------------------------------------------


class _QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        pass


@dataclass
class SeedHttpServer:
    directory: Path
    port: int = 0
    _httpd: socketserver.TCPServer | None = field(default=None, repr=False)
    _thread: threading.Thread | None = field(default=None, repr=False)

    def start(self) -> int:
        handler = lambda *a, **kw: _QuietHandler(*a, directory=str(self.directory), **kw)  # noqa: E731
        self._httpd = socketserver.TCPServer(("127.0.0.1", self.port), handler)
        self.port = self._httpd.server_address[1]
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        return self.port

    def stop(self) -> None:
        if self._httpd is not None:
            self._httpd.shutdown()
            self._httpd.server_close()


# --------------------------------------------------------------------------
# Download + verify
# --------------------------------------------------------------------------


def download_and_verify_image(cache_dir: Path, *, timeout_s: int = 900) -> dict[str, Any]:
    """Fetch the Debian genericcloud arm64 qcow2 (cached) and verify its sha512 + record sha256."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    image_path = cache_dir / IMAGE_NAME
    checksums_path = cache_dir / "SHA512SUMS"
    result: dict[str, Any] = {
        "image_url": IMAGE_URL,
        "image_path": str(image_path),
        "cached": image_path.is_file(),
    }
    try:
        subprocess.run(
            ["curl", "-fsSL", "--max-time", str(timeout_s), "-o", str(checksums_path), CHECKSUMS_URL],
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout_s,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        return {**result, "ok": False, "error": f"checksums_fetch_failed:{exc}"}
    expected_sha512 = parse_sha512sums(checksums_path.read_text(encoding="utf-8"), IMAGE_NAME)
    if not expected_sha512:
        return {**result, "ok": False, "error": "image_not_found_in_checksums_file"}

    need_download = True
    if image_path.is_file() and image_path.stat().st_size > 10_000_000:
        if _sha512_file(image_path) == expected_sha512:
            need_download = False
        else:
            image_path.unlink()

    if need_download:
        partial = cache_dir / f"{IMAGE_NAME}.partial"
        try:
            subprocess.run(
                ["curl", "-fsSL", "--max-time", str(timeout_s), "-o", str(partial), IMAGE_URL],
                check=True,
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
            if partial.exists():
                partial.unlink()
            return {**result, "ok": False, "error": f"image_download_failed:{exc}"}
        actual_sha512 = _sha512_file(partial)
        if actual_sha512 != expected_sha512:
            partial.unlink()
            return {
                **result,
                "ok": False,
                "error": "sha512_mismatch",
                "expected_sha512": expected_sha512,
                "actual_sha512": actual_sha512,
            }
        partial.rename(image_path)

    return {
        **result,
        "ok": True,
        "cached": not need_download,
        "downloaded_this_run": need_download,
        "expected_sha512": expected_sha512,
        "sha512": expected_sha512,
        "sha256": _sha256_file(image_path),
        "size_bytes": image_path.stat().st_size,
    }


# --------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------


@dataclass
class ProvisionResult:
    ok: bool
    evidence: dict[str, Any]


class DebianCloudInteractiveGuestProvisioner:
    def __init__(self, repo_root: Path | None = None) -> None:
        self.repo_root = repo_root or _repo_root()
        self.root = interactive_root(self.repo_root)
        self.cache = self.root / "cache"
        self.work = self.root / "work" / "debian_cloud_provision"
        self.artifacts = self.root / "artifacts"
        self.artifacts.mkdir(parents=True, exist_ok=True)
        self.work.mkdir(parents=True, exist_ok=True)

    def _evidence_path(self) -> Path:
        return self.artifacts / "INTERACTIVE_GUEST_PROVISION_EVIDENCE.json"

    def _disk_path(self) -> Path:
        return self.artifacts / f"interactive-root-{DEBIAN_ARCH.replace('arm64', 'aarch64')}.qcow2"

    def environment_check(self) -> dict[str, Any]:
        qemu_img = find_qemu_img()
        qemu_bin = find_qemu_system_aarch64()
        edk2 = find_edk2_firmware()
        curl_bin = shutil.which("curl")
        missing = [
            name
            for name, present in (
                ("qemu-img", qemu_img),
                ("qemu-system-aarch64", qemu_bin),
                ("edk2-aarch64-code.fd", edk2),
                ("curl", curl_bin),
            )
            if not present
        ]
        return {
            "ok": not missing,
            "missing": missing,
            "qemu_img": qemu_img,
            "qemu_bin": qemu_bin,
            "edk2_code": str(edk2) if edk2 else None,
            "curl": curl_bin,
        }

    def _write_cloud_init_seed(self) -> Path:
        seed_dir = self.work / "seed"
        seed_dir.mkdir(parents=True, exist_ok=True)
        debian_cloud_dir = self.root / "debian_cloud"
        agent_script = (debian_cloud_dir / "guest_agent" / "gunnchos_guest_agent.py").read_text(encoding="utf-8")
        agent_service = (debian_cloud_dir / "systemd" / "gunnchos-guest-agent.service").read_text(encoding="utf-8")
        weston_service = (debian_cloud_dir / "systemd" / "gunnchos-weston.service").read_text(encoding="utf-8")
        weston_ini = (debian_cloud_dir / "config" / "weston.ini").read_text(encoding="utf-8")
        user_data = build_cloud_init_user_data(
            guest_agent_script=agent_script,
            guest_agent_service=agent_service,
            weston_service=weston_service,
            weston_ini=weston_ini,
        )
        (seed_dir / "user-data").write_text(user_data, encoding="utf-8")
        (seed_dir / "meta-data").write_text(
            build_cloud_init_meta_data(instance_id=f"gunnchos-lab-{int(time.time())}"), encoding="utf-8"
        )
        return seed_dir

    def _prepare_disk(self, base_image: Path, *, size_gb: int, overwrite: bool) -> Path:
        disk = self._disk_path()
        if disk.exists() and not overwrite:
            return disk
        if disk.exists():
            disk.unlink()
        qemu_img = find_qemu_img()
        assert qemu_img
        subprocess.run(
            [qemu_img, "create", "-f", "qcow2", "-F", "qcow2", "-b", str(base_image), str(disk)],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run([qemu_img, "resize", str(disk), f"{size_gb}G"], check=True, capture_output=True, text=True)
        return disk

    def _prepare_vars_flash(self, edk2_code: Path) -> Path:
        vars_path = self.work / "edk2-aarch64-vars.fd"
        template_candidates = [
            Path("/opt/homebrew/share/qemu/edk2-arm-vars.fd"),
            Path("/opt/homebrew/opt/qemu/share/qemu/edk2-arm-vars.fd"),
            Path("/usr/share/qemu/edk2-arm-vars.fd"),
        ]
        # Always refresh from the nvram template so a prior UEFI-shell session
        # cannot stick BootOrder on the wrong device.
        for tmpl in template_candidates:
            if tmpl.is_file():
                import shutil

                shutil.copyfile(tmpl, vars_path)
                return vars_path
        size = edk2_code.stat().st_size
        with vars_path.open("wb") as fh:
            fh.truncate(size)
        return vars_path

    def run(
        self,
        *,
        disk_size_gb: int = DEFAULT_DISK_SIZE_GB,
        memory_mb: int = DEFAULT_MEMORY_MB,
        smp: int = DEFAULT_SMP,
        timeout_s: int = DEFAULT_PROVISION_TIMEOUT_S,
        overwrite_disk: bool = False,
        dry_run_download_only: bool = False,
    ) -> ProvisionResult:
        started = datetime.now(timezone.utc)
        evidence: dict[str, Any] = {
            "schema": SCHEMA,
            "version": PROVISION_VERSION,
            "started_at_utc": started.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST": DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST,
            "SHIPPING_IMAGE": SHIPPING_IMAGE,
            "SILICON_EXACT_EMULATION": SILICON_EXACT_EMULATION,
            "method": "qemu_debian_genericcloud_cloud_init_guest_native",
            "image": {"url": IMAGE_URL, "release": DEBIAN_RELEASE, "variant": DEBIAN_IMAGE_VARIANT, "arch": DEBIAN_ARCH},
            "required_packages": list(REQUIRED_APT_PACKAGES),
            "optional_packages": list(OPTIONAL_APT_PACKAGES),
            "host": {"system": platform.system(), "machine": platform.machine()},
            "ok": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        env = self.environment_check()
        evidence["environment"] = env
        if not env["ok"]:
            evidence["error"] = f"missing_host_tools:{env['missing']}"
            self._finish(evidence, ok=False)
            return ProvisionResult(False, evidence)

        dl = download_and_verify_image(self.cache, timeout_s=1200)
        evidence["download"] = dl
        if not dl.get("ok"):
            evidence["error"] = f"image_download_or_verify_failed:{dl.get('error')}"
            self._finish(evidence, ok=False)
            return ProvisionResult(False, evidence)

        if dry_run_download_only:
            evidence["dry_run"] = True
            evidence["note"] = "Real network fetch + sha512 verification only; no boot attempted."
            self._finish(evidence, ok=True, dry_run=True)
            return ProvisionResult(True, evidence)

        seed_dir = self._write_cloud_init_seed()
        base_image = self.cache / IMAGE_NAME
        disk = self._prepare_disk(base_image, size_gb=disk_size_gb, overwrite=overwrite_disk)
        edk2_code = Path(env["edk2_code"])
        edk2_vars = self._prepare_vars_flash(edk2_code)
        accel_info = select_provision_accel()

        seed_server = SeedHttpServer(directory=seed_dir)
        port = seed_server.start()
        smbios_url = f"http://10.0.2.2:{port}/"

        boot_log = self.work / "provision_serial.log"
        pidfile = self.work / "qemu.pid"
        # macOS UNIX socket paths are capped at ~104 bytes; the repo's own
        # work/ path is often longer than that. Keep the monitor socket under
        # a short /tmp prefix (mirrors qemu_guest.py's existing convention).
        sock_dir = Path(f"/tmp/gdlp-{os.getpid()}-{abs(hash(str(self.work))) % 10_000_000:x}")
        sock_dir.mkdir(parents=True, exist_ok=True)
        monitor_sock = sock_dir / "mon.sock"
        for p in (boot_log, pidfile):
            if p.exists():
                p.unlink()

        cmd = build_qemu_provision_cmd(
            qemu_bin=env["qemu_bin"],
            edk2_code=edk2_code,
            edk2_vars=edk2_vars,
            disk=disk,
            boot_log=boot_log,
            pidfile=pidfile,
            monitor_sock=monitor_sock,
            smbios_url=smbios_url,
            memory_mb=memory_mb,
            smp=smp,
            accel=accel_info["accel"],
            cpu=accel_info["cpu"],
        )
        evidence["qemu_cmd"] = cmd
        evidence["accel"] = accel_info
        (self.work / "qemu_provision_cmd.json").write_text(json.dumps(cmd, indent=2) + "\n", encoding="utf-8")

        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if proc.returncode != 0:
            seed_server.stop()
            evidence["error"] = "qemu_start_failed"
            evidence["qemu_stderr"] = proc.stderr[-4000:]
            evidence["qemu_stdout"] = proc.stdout[-4000:]
            self._finish(evidence, ok=False)
            return ProvisionResult(False, evidence)

        pid = None
        for _ in range(50):
            if pidfile.exists():
                try:
                    pid = int(pidfile.read_text(encoding="utf-8").strip())
                    break
                except ValueError:
                    pass
            time.sleep(0.1)
        evidence["qemu_pid"] = pid

        deadline = time.time() + timeout_s
        sentinel_seen = False
        fail_seen = False
        while time.time() < deadline:
            if boot_log.exists():
                text = boot_log.read_text(encoding="utf-8", errors="replace")
                if PROVISION_OK_SENTINEL in text:
                    sentinel_seen = True
                    break
                if PROVISION_FAIL_SENTINEL in text:
                    fail_seen = True
                    break
            if pid is not None and not _pid_alive(pid):
                break
            time.sleep(2.0)

        qemu_exited = pid is None or not _pid_alive(pid)
        if not qemu_exited and pid is not None:
            # Timeout with QEMU still running — wait briefly for the ACPI
            # poweroff cloud-init triggers, then kill honestly if it hangs.
            for _ in range(30):
                if not _pid_alive(pid):
                    qemu_exited = True
                    break
                time.sleep(1.0)
            if not qemu_exited:
                try:
                    os.kill(pid, 15)
                except OSError:
                    pass

        seed_server.stop()
        tail = boot_log.read_text(encoding="utf-8", errors="replace")[-8000:] if boot_log.exists() else ""
        evidence["boot_log_tail"] = tail
        evidence["sentinel_seen"] = sentinel_seen
        evidence["qemu_exited_cleanly"] = qemu_exited
        ok = sentinel_seen and qemu_exited and not fail_seen
        if not ok:
            if fail_seen:
                evidence["error"] = "provision_fail_sentinel_observed"
            elif not sentinel_seen:
                evidence["error"] = "provision_timeout_no_sentinel"
            elif not qemu_exited:
                evidence["error"] = "qemu_did_not_exit_after_poweroff"

        if ok and disk.exists():
            evidence["disk"] = {
                "path": str(disk),
                "size_bytes": disk.stat().st_size,
                "sha256": _sha256_file(disk),
                "backing_file": str(base_image),
                "note": "qcow2 with backing_file=base cloud image; base image cached separately, never committed to git",
            }
        self._finish(evidence, ok=ok)
        return ProvisionResult(ok, evidence)

    def _finish(self, evidence: dict[str, Any], *, ok: bool, dry_run: bool = False) -> None:
        evidence["ok"] = ok
        evidence["finished_at_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        evidence_path = self._evidence_path()
        evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        manifest = {
            "schema": "gunnchos.device_lab.interactive_guest_image.manifest.v1",
            "version": PROVISION_VERSION,
            "DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST": DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST,
            "SHIPPING_IMAGE": SHIPPING_IMAGE,
            "SILICON_EXACT_EMULATION": SILICON_EXACT_EMULATION,
            "provision_method": "qemu_debian_genericcloud_cloud_init_guest_native",
            "arch": "aarch64",
            "base_image": evidence.get("image"),
            "download": evidence.get("download"),
            "disk": evidence.get("disk"),
            "required_packages": list(REQUIRED_APT_PACKAGES),
            "optional_packages": list(OPTIONAL_APT_PACKAGES),
            "guest_agent_commands": [
                "ping",
                "boot_status",
                "process_list",
                "process_start",
                "process_stop",
                "package_ops",
                "display_info",
                "input_inject",
                "input_observe",
                "logs",
                "metrics",
                "shutdown",
                "reboot",
                "framebuffer_capture",
                "compositor_info",
                "app_launch",
            ],
            "provision_ok": ok,
            "dry_run": dry_run,
            "pass_tokens_earned_by_this_manifest": [],
            "claim_boundary": CLAIM_BOUNDARY,
        }
        (self.artifacts / "INTERACTIVE_GUEST_MANIFEST.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )


def _pid_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Provision the Interactive Development Guest (Debian cloud-init)")
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--disk-size-gb", type=int, default=DEFAULT_DISK_SIZE_GB)
    parser.add_argument("--memory-mb", type=int, default=DEFAULT_MEMORY_MB)
    parser.add_argument("--smp", type=int, default=DEFAULT_SMP)
    parser.add_argument("--timeout-s", type=int, default=DEFAULT_PROVISION_TIMEOUT_S)
    parser.add_argument("--overwrite-disk", action="store_true")
    parser.add_argument("--dry-run-download-only", action="store_true")
    ns = parser.parse_args(argv)

    provisioner = DebianCloudInteractiveGuestProvisioner(Path(ns.repo_root) if ns.repo_root else None)
    result = provisioner.run(
        disk_size_gb=ns.disk_size_gb,
        memory_mb=ns.memory_mb,
        smp=ns.smp,
        timeout_s=ns.timeout_s,
        overwrite_disk=ns.overwrite_disk,
        dry_run_download_only=ns.dry_run_download_only,
    )
    print(json.dumps({"ok": result.ok, "evidence_path": str(provisioner._evidence_path())}, indent=2))
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
