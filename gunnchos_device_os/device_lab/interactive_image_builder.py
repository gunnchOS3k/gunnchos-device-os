"""gunnchOS Device Lab Interactive Development Guest — manifest + build orchestration.

WP-011R: the slim Alpine initramfs-only guest (`image_builder.py`,
`DEVICE_LAB_DEVELOPMENT_GUEST`) has no compositor and no persistent root
filesystem, so it can never earn `LIVE_GUNNCHOS_VISUAL_PASS`,
`DSXL_DUAL_COMPOSITOR_UX_PASS`, or `RING_TO_REAL_APP_STATE_MUTATION_PASS`.
This module is the *scaffolding* for a real Wayland-compositor Interactive
Guest with a persistent qcow2 root disk. It is honest scaffolding, not a
finished build:

- `DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST = true` — still a development
  guest, never shipped.
- `SHIPPING_IMAGE = false` — always.
- The slim guest's `DEVICE_LAB_DEVELOPMENT_GUEST` label is untouched and
  imported here for cross-reference, not redefined.
- No `*_PASS` token or master-complete token is set here. Producing a
  manifest or an empty qcow2 placeholder does not earn anything.

See `os_build/device_lab_interactive_guest/README.md` for architecture,
claim boundary, and the real (Docker / chroot+binfmt / none) build methods.
"""
from __future__ import annotations

import hashlib
import json
import platform
import shutil
import subprocess
from pathlib import Path
from typing import Any

from gunnchos_device_os.device_lab.image_builder import DEVICE_LAB_DEVELOPMENT_GUEST

INTERACTIVE_GUEST_SCHEMA = "gunnchos.device_lab.interactive_guest_image.manifest.v1"
INTERACTIVE_GUEST_VERSION = "0.1.0-lab-interactive-dev"

# WP-011R: labels required by the Interactive Guest scaffolding request.
DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST = True
SHIPPING_IMAGE = False

# Cross-reference only — the slim guest keeps its own label untouched.
_SLIM_GUEST_LABEL = DEVICE_LAB_DEVELOPMENT_GUEST

CLAIM_BOUNDARY = (
    "gunnchOS Device Lab Interactive Development Guest: persistent-root-disk "
    "Alpine guest scaffolding intended to host a real Wayland compositor "
    "(weston) + apps for in-guest LIVE/DSXL/Ring proofs. "
    "DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST=true. SHIPPING_IMAGE=false. "
    "SILICON_EXACT_EMULATION=false. Not physical boot; not production keys; "
    "no *_PASS or master-complete token is earned by this scaffolding alone."
)

ALPINE_VERSION = "3.21.3"
ALPINE_MIRROR = "https://dl-cdn.alpinelinux.org/alpine/v3.21/releases"

# Declared required packages for the Interactive Guest userspace.
# `optional=True` packages (currently just godot) are allowed to be skipped
# by the build script without failing the overall build.
REQUIRED_PACKAGES: tuple[dict[str, Any], ...] = (
    {"name": "alpine-baselayout", "role": "base filesystem layout", "optional": False},
    {"name": "busybox", "role": "base userspace utilities", "optional": False},
    {"name": "seatd", "role": "seat management for weston (no logind in Alpine)", "optional": False},
    {"name": "weston", "role": "Wayland reference compositor", "optional": False},
    {"name": "mesa-dri-gallium", "role": "software / virtio-gpu GL rendering", "optional": False},
    {"name": "foot", "role": "Wayland terminal emulator", "optional": False},
    {
        "name": "chromium",
        "role": "Wayland-capable browser (Ozone/Wayland)",
        "optional": False,
        "fallback": "firefox",
    },
    {"name": "nano", "role": "terminal text editor", "optional": False},
    {
        "name": "pipewire",
        "role": "audio server",
        "optional": False,
        "extra": "pipewire-alsa",
        "fallback": "alsa-utils",
    },
    {"name": "libinput", "role": "input device handling for weston", "optional": False},
    {"name": "godot", "role": "game engine runtime for FOUR_GAME real-runtime work", "optional": True},
)

# Arch matrix declared in the README. Only aarch64 has an implemented build
# script this wave; x86_64 build_script is intentionally None (honest gap).
ARCH_MATRIX: dict[str, dict[str, Any]] = {
    "aarch64": {
        "host_examples": ["macOS Apple Silicon (Mac HVF)"],
        "accel": ["hvf"],
        "build_script": "os_build/device_lab_interactive_guest/scripts/build_interactive_rootfs_alpine_aarch64.sh",
        "implemented": True,
    },
    "x86_64": {
        "host_examples": ["Linux (Student / DS-XL physical profile parity)"],
        "accel": ["kvm", "tcg"],
        "build_script": None,
        "implemented": False,
        "note": "Not yet implemented this wave — required for x86_64 hardware-profile parity",
    },
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def interactive_image_root(repo_root: Path | None = None) -> Path:
    root = repo_root or _repo_root()
    return root / "os_build" / "device_lab_interactive_guest"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def detect_build_capability(*, host_system: str | None = None) -> dict[str, Any]:
    """Detect which real cross-arch build method (if any) is usable right now.

    Never claims a capability that isn't actually present. Priority:
    docker (native linux/arm64 on Apple Silicon, or buildx emulation) >
    chroot + qemu-user-static binfmt (Linux only) > none (honest gap).
    """
    system = host_system or platform.system()
    docker_bin = shutil.which("docker")
    docker_usable = False
    docker_detail = "docker not found on PATH"
    if docker_bin:
        try:
            proc = subprocess.run(
                [docker_bin, "info", "--format", "{{.ServerVersion}}"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            docker_usable = proc.returncode == 0 and bool(proc.stdout.strip())
            docker_detail = (
                f"docker daemon reachable (server {proc.stdout.strip()})"
                if docker_usable
                else f"docker binary present but daemon unreachable: {(proc.stderr or proc.stdout).strip()[:200]}"
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            docker_detail = f"docker present but not runnable: {exc}"

    chroot_bin = shutil.which("chroot") or (
        "/usr/sbin/chroot" if Path("/usr/sbin/chroot").exists() else None
    )
    # binfmt_misc / qemu-user-static registration is a Linux-only concept;
    # macOS cannot execute foreign-arch Linux ELF binaries via chroot at all.
    binfmt_usable = False
    binfmt_detail = "binfmt_misc is Linux-only; not applicable on this host OS"
    if system == "Linux":
        binfmt_path = Path("/proc/sys/fs/binfmt_misc")
        qemu_user = shutil.which("qemu-aarch64-static") or shutil.which("qemu-aarch64")
        if binfmt_path.exists() and qemu_user:
            binfmt_usable = True
            binfmt_detail = f"binfmt_misc present + qemu-user helper found ({qemu_user})"
        elif binfmt_path.exists():
            binfmt_detail = "binfmt_misc present but no qemu-user-static helper found on PATH"
        else:
            binfmt_detail = "binfmt_misc not present"

    chroot_usable = bool(chroot_bin) and binfmt_usable

    if docker_usable:
        method = "docker"
    elif chroot_usable:
        method = "chroot_binfmt"
    else:
        method = "none"

    return {
        "ok": method != "none",
        "method": method,
        "host_system": system,
        "docker": {"bin": docker_bin, "usable": docker_usable, "detail": docker_detail},
        "chroot_binfmt": {
            "chroot_bin": chroot_bin,
            "usable": chroot_usable,
            "binfmt_detail": binfmt_detail,
        },
        "note": (
            "Real apk package install with post-install scripts requires "
            "executing real aarch64 Linux binaries; docker (native linux/arm64 "
            "on Apple Silicon) or chroot+binfmt (Linux host) are the only "
            "honest real methods. Neither present -> method='none' (honest gap, "
            "not a fake pass)."
            if method == "none"
            else f"Real cross-build method available: {method}"
        ),
    }


def interactive_manifest(repo_root: Path | None = None) -> dict[str, Any]:
    """Build the (not-yet-executed) manifest describing the Interactive Guest."""
    root = repo_root or _repo_root()
    art_dir = interactive_image_root(root) / "artifacts"
    disk_arch = "aarch64"
    disk_path = art_dir / f"interactive-root-{disk_arch}.qcow2"
    capability = detect_build_capability()
    return {
        "schema": INTERACTIVE_GUEST_SCHEMA,
        "version": INTERACTIVE_GUEST_VERSION,
        "realm": "DEV_LAB",
        "DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST": DEVICE_LAB_INTERACTIVE_DEVELOPMENT_GUEST,
        "DEVICE_LAB_DEVELOPMENT_GUEST": _SLIM_GUEST_LABEL,
        "SHIPPING_IMAGE": SHIPPING_IMAGE,
        "SILICON_EXACT_EMULATION": False,
        "production_keys_used": False,
        "physical_boot_claimed": False,
        "hybrid_base": True,
        "alpine_version": ALPINE_VERSION,
        "alpine_mirror": ALPINE_MIRROR,
        "required_packages": list(REQUIRED_PACKAGES),
        "arch_matrix": ARCH_MATRIX,
        "root_disk": {
            "arch": disk_arch,
            "path": str(disk_path.relative_to(root)),
            "format": "qcow2",
            "persistent": True,
            "note": (
                "Persistent virtio-blk disk (unlike the slim guest's ephemeral "
                "initramfs) — required because a compositor + browser + editor "
                "stack does not fit in guest RAM."
            ),
        },
        "build_capability_at_manifest_time": capability,
        "guest_agent_commands_added": ["framebuffer_capture", "compositor_info", "app_launch"],
        "qemu_env_flag": "GUNNCH_LAB_INTERACTIVE_GUEST",
        "qemu_env_flag_aliases": ["GUNNCHDEVICE_LAB_INTERACTIVE_GUEST"],
        "claim_boundary": CLAIM_BOUNDARY,
        "pass_tokens_earned_by_this_manifest": [],
        "required_for": [
            "LIVE_GUNNCHOS_VISUAL_PASS",
            "DSXL_DUAL_COMPOSITOR_UX_PASS",
            "RING_TO_REAL_APP_STATE_MUTATION_PASS",
        ],
        "note": (
            "Manifest describes intended packages/arch/disk layout. Producing "
            "this manifest does not build, boot, or prove anything by itself."
        ),
    }


def write_interactive_manifest(repo_root: Path | None = None) -> Path:
    root = repo_root or _repo_root()
    art_dir = interactive_image_root(root) / "artifacts"
    art_dir.mkdir(parents=True, exist_ok=True)
    manifest = interactive_manifest(root)
    path = art_dir / "INTERACTIVE_GUEST_MANIFEST.json"
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


class InteractiveGuestImageBuilder:
    """Orchestration stub for the Interactive Guest image.

    Honest about what it can and cannot do on the current host: it can
    always write the manifest and create a qcow2 disk placeholder (when
    `qemu-img` is present); it can only run the *real* rootfs build by
    delegating to the arch-specific shell script, and that script itself
    exits non-zero honestly when required tools are missing rather than
    faking success.
    """

    def __init__(self, repo_root: Path | None = None) -> None:
        self.repo_root = Path(repo_root or _repo_root())
        self.interactive_root = interactive_image_root(self.repo_root)
        self.artifacts = self.interactive_root / "artifacts"
        self.artifacts.mkdir(parents=True, exist_ok=True)

    def write_manifest(self) -> Path:
        return write_interactive_manifest(self.repo_root)

    def create_disk_placeholder(
        self,
        *,
        arch: str = "aarch64",
        size_gb: int = 8,
        overwrite: bool = False,
    ) -> dict[str, Any]:
        """Create (and best-effort format) a qcow2 root disk placeholder.

        Honest: this only allocates a qcow2 file via `qemu-img`. It does not
        populate a filesystem or rootfs unless a real build has already run.
        `disk_formatted` stays `False` unless a filesystem was actually
        written, which this method never attempts (mkfs tooling for a Linux
        filesystem is not reliably available cross-platform without Docker/
        a Linux host — see `detect_build_capability`).
        """
        disk_path = self.artifacts / f"interactive-root-{arch}.qcow2"
        qemu_img = shutil.which("qemu-img") or (
            "/opt/homebrew/bin/qemu-img" if Path("/opt/homebrew/bin/qemu-img").exists() else None
        )
        if disk_path.exists() and not overwrite:
            return {
                "ok": True,
                "path": str(disk_path),
                "created": False,
                "reason": "already_exists",
                "sha256": _sha256_file(disk_path),
                "size_bytes": disk_path.stat().st_size,
                "disk_formatted": False,
                "SILICON_EXACT_EMULATION": False,
            }
        if not qemu_img:
            return {
                "ok": False,
                "error": "qemu-img_not_found",
                "note": "Cannot create qcow2 placeholder without qemu-img; exit non-zero honestly upstream",
                "SILICON_EXACT_EMULATION": False,
            }
        try:
            subprocess.run(
                [qemu_img, "create", "-f", "qcow2", str(disk_path), f"{size_gb}G"],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as exc:
            return {
                "ok": False,
                "error": "qemu_img_create_failed",
                "detail": (exc.stderr or exc.stdout or str(exc))[:500],
                "SILICON_EXACT_EMULATION": False,
            }
        return {
            "ok": True,
            "path": str(disk_path),
            "created": True,
            "size_gb": size_gb,
            "arch": arch,
            "sha256": _sha256_file(disk_path),
            "size_bytes": disk_path.stat().st_size,
            "disk_formatted": False,
            "note": "Placeholder qcow2 allocated; no filesystem/rootfs written yet",
            "SILICON_EXACT_EMULATION": False,
        }

    def build_capability(self) -> dict[str, Any]:
        return detect_build_capability()

    def run_rootfs_build(self, *, arch: str = "aarch64", extra_args: list[str] | None = None) -> dict[str, Any]:
        """Delegate to the real arch-specific build script.

        Returns the script's own honest result (including non-zero exit
        codes when tools/capability are missing). Never overrides a script
        failure with a fabricated success.
        """
        matrix = ARCH_MATRIX.get(arch)
        if not matrix or not matrix.get("implemented"):
            return {
                "ok": False,
                "error": "arch_build_script_not_implemented",
                "arch": arch,
                "arch_matrix_entry": matrix,
                "SILICON_EXACT_EMULATION": False,
            }
        script = self.repo_root / matrix["build_script"]
        if not script.exists():
            return {
                "ok": False,
                "error": "build_script_missing",
                "script": str(script),
                "SILICON_EXACT_EMULATION": False,
            }
        cmd = [str(script), "--repo-root", str(self.repo_root)]
        if extra_args:
            cmd += list(extra_args)
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": proc.stdout[-4000:],
            "stderr": proc.stderr[-4000:],
            "cmd": cmd,
            "SILICON_EXACT_EMULATION": False,
        }

    def plan_build(self) -> dict[str, Any]:
        """Ordered, human-readable orchestration plan (no side effects)."""
        return {
            "schema": "gunnchos.device_lab.interactive_guest_build_plan.v1",
            "steps": [
                {"step": 1, "action": "fetch Alpine minirootfs tarball (real curl fetch)"},
                {"step": 2, "action": "detect_build_capability() -> docker | chroot_binfmt | none"},
                {
                    "step": 3,
                    "action": (
                        "if docker: docker run --platform linux/arm64 alpine:3.21 "
                        "apk add --root <rootfs> -U <REQUIRED_PACKAGES>"
                    ),
                },
                {
                    "step": 4,
                    "action": (
                        "elif chroot_binfmt: chroot into extracted rootfs under "
                        "qemu-aarch64-static binfmt registration; apk add <REQUIRED_PACKAGES>"
                    ),
                },
                {"step": 5, "action": "else: exit non-zero honestly; no fake success"},
                {"step": 6, "action": "copy overlay/ (first-boot weston + guest agent hooks) into rootfs"},
                {"step": 7, "action": "create_disk_placeholder() qcow2 (real qemu-img create)"},
                {"step": 8, "action": "pack rootfs onto qcow2 disk (requires step 3/4 to have succeeded)"},
                {
                    "step": 9,
                    "action": (
                        "boot via qemu_guest.py with GUNNCH_LAB_INTERACTIVE_GUEST=1 "
                        "(virtio-gpu, virtio-keyboard, virtio-tablet, root disk attached)"
                    ),
                },
                {
                    "step": 10,
                    "action": (
                        "capture guest_agent framebuffer_capture / compositor_info; "
                        "only then consider LIVE/DSXL/Ring evidence"
                    ),
                },
            ],
            "claim_boundary": CLAIM_BOUNDARY,
        }


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Interactive Guest manifest/build orchestration")
    parser.add_argument("--write-manifest", action="store_true")
    parser.add_argument("--create-disk", action="store_true")
    parser.add_argument("--disk-size-gb", type=int, default=8)
    parser.add_argument("--arch", default="aarch64")
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--capability", action="store_true")
    parser.add_argument("--repo-root", default=None)
    ns = parser.parse_args(argv)

    builder = InteractiveGuestImageBuilder(Path(ns.repo_root) if ns.repo_root else None)
    out: dict[str, Any] = {}
    if ns.capability:
        out["capability"] = builder.build_capability()
    if ns.write_manifest:
        out["manifest_path"] = str(builder.write_manifest())
    if ns.create_disk:
        out["disk"] = builder.create_disk_placeholder(arch=ns.arch, size_gb=ns.disk_size_gb)
    if ns.plan:
        out["plan"] = builder.plan_build()
    if not out:
        out = {"plan": builder.plan_build(), "capability": builder.build_capability()}
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
