"""Bootable gunnchOS reference image builder + QEMU evidence harness.

Produces a genuinely bootable DEV/VM initramfs image for QEMU aarch64
(linux direct-kernel boot) with bootloader path metadata, kernel, rootfs,
init, long-lived supervised services with local IPC, shell, networking, app runtime manifests,
updater A/B markers, and recovery self-check.

Honest token: GUNNCHOS_BOOTABLE_REFERENCE_IMAGE_DIGITAL_PASS only when QEMU
boot log contains required markers. Never claims physical device boot or
production keys / FULL_OPERATIONAL_PRODUCT.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import gzip
import hashlib
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
import time


CLAIM_BOUNDARY = (
    "Bootable *reference* image for QEMU/emulation only. Captures serial "
    "console evidence from a DEV-realm guest. Does NOT claim physical device "
    "boot, production secure boot keys, carrier networking, or "
    "FULL_OPERATIONAL_PRODUCT."
)

TOKEN_DIGITAL_PASS = "GUNNCHOS_BOOTABLE_REFERENCE_IMAGE_DIGITAL_PASS"
TOKEN_PHYSICAL_PENDING = "GUNNCHOS_PHYSICAL_BOOT_PENDING"

ALPINE_VERSION = "3.21.3"
ALPINE_ARCH = "aarch64"
ALPINE_MIRROR = "https://dl-cdn.alpinelinux.org/alpine/v3.21/releases/aarch64"

REQUIRED_BOOT_MARKERS = (
    "GUNNCHOS_BOOT_MARKER=OK",
    "GUNNCHOS_BOOT_COMPLETE=true",
    "GUNNCHOS_PRODUCTION_KEYS=false",
    "GUNNCHOS_PHYSICAL_BOOT_CLAIMED=false",
    "GUNNCHOS_NETWORKING=loopback_up",
    "GUNNCHOS_SHELL=ok",
    "GUNNCHOS_UPDATER_AB",
    "GUNNCHOS_RECOVERY_SELF_CHECK=ok",
    "GUNNCHOS_SERVICES_KIND=supervised_real",
    "GUNNCHOS_IPC=ok",
    "GUNNCHOS_IPC_CROSS_CALL=true",
    "GUNNCHOS_APP_MANIFEST=ok",
    "GUNNCHOS_GAME_MANIFEST=ok",
    "FULL_GUNNCHOS_PLATFORM_DIGITAL_COMPLETE=true",  # Cont VII §27: digital token; physical remains separate
)

REQUIRED_SERVICES = (
    "hal",
    "input",
    "ring",
    "display",
    "dock",
    "continuity",
    "identity",
    "permissions",
    "sandbox",
    "connectivity",
    "ai_interface",
    "profile_manager",
    "a11y",
    "diagnostics",
    "updater",
    "recovery",
    "fleet_agent",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _track_root() -> Path:
    return _repo_root() / "os_build" / "bootable_reference"


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _canonical_json(data: Any) -> bytes:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


@dataclass
class BootableImagePaths:
    track: Path = field(default_factory=_track_root)
    cache: Path = field(init=False)
    work: Path = field(init=False)
    artifacts: Path = field(init=False)
    overlay: Path = field(init=False)
    evidence_dir: Path = field(init=False)

    def __post_init__(self) -> None:
        self.cache = self.track / "cache"
        self.work = self.track / "work"
        self.artifacts = self.track / "artifacts"
        self.overlay = self.track / "overlay"
        self.evidence_dir = _repo_root() / "results" / "full_product" / "bootable_reference"


class BootableReferenceBuilder:
    """Assemble Alpine minirootfs + overlay into a bootable initramfs."""

    def __init__(self, paths: BootableImagePaths | None = None) -> None:
        self.paths = paths or BootableImagePaths()
        self.paths.cache.mkdir(parents=True, exist_ok=True)
        self.paths.work.mkdir(parents=True, exist_ok=True)
        self.paths.artifacts.mkdir(parents=True, exist_ok=True)
        self.paths.evidence_dir.mkdir(parents=True, exist_ok=True)

    @property
    def minirootfs_tarball(self) -> Path:
        return self.paths.cache / f"alpine-minirootfs-{ALPINE_ARCH}.tar.gz"

    @property
    def kernel_path(self) -> Path:
        return self.paths.cache / "vmlinuz-virt"

    @property
    def alpine_initramfs_virt(self) -> Path:
        """Alpine netboot initramfs-virt — source of DRM/virtio-gpu modules for Lab dual."""
        return self.paths.cache / "initramfs-virt"

    def ensure_cache(self, *, fetch: bool = True) -> dict[str, Any]:
        needed = {
            "minirootfs": (
                self.minirootfs_tarball,
                f"{ALPINE_MIRROR}/alpine-minirootfs-{ALPINE_VERSION}-{ALPINE_ARCH}.tar.gz",
            ),
            "kernel": (
                self.kernel_path,
                f"{ALPINE_MIRROR}/netboot/vmlinuz-virt",
            ),
            "initramfs_virt": (
                self.alpine_initramfs_virt,
                f"{ALPINE_MIRROR}/netboot/initramfs-virt",
            ),
        }
        status = {}
        for name, (dest, url) in needed.items():
            if dest.exists() and dest.stat().st_size > 0:
                status[name] = {"path": str(dest), "fetched": False, "sha256": _sha256_file(dest)}
                continue
            if not fetch:
                raise FileNotFoundError(f"missing cache artifact {dest}; fetch required")
            dest.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(
                ["curl", "-fsSL", "-o", str(dest), url],
                check=True,
            )
            status[name] = {"path": str(dest), "fetched": True, "sha256": _sha256_file(dest)}
        return status

    def stage_drm_modules(self, rootfs: Path) -> dict[str, Any]:
        """Copy Alpine virt DRM/virtio-gpu modules into Lab rootfs for guest dual proof.

        Lab minirootfs alone has no /lib/modules — virtio-gpu PCI attach without a
        guest driver cannot earn GUEST_DUAL_OUTPUT_PASS. Modules come from the same
        Alpine netboot initramfs-virt paired with vmlinuz-virt.
        """
        src_initrd = self.alpine_initramfs_virt
        if not src_initrd.exists():
            return {"ok": False, "error": "initramfs_virt_missing", "staged": 0}
        wanted_suffixes = (
            "virtio/virtio-gpu.ko",
            "drm/drm.ko",
            "drm/drm_kms_helper.ko",
            "drm/drm_shmem_helper.ko",
            "drm/drm_panel_orientation_quirks.ko",
            "virtio/virtio_dma_buf.ko",
            "fbdev/core/fb.ko",
            "fbdev/core/syscopyarea.ko",
            "fbdev/core/sysfillrect.ko",
            "fbdev/core/sysimgblt.ko",
            "fbdev/core/fb_sys_fops.ko",
            "backlight/backlight.ko",
            "i2c/i2c-core.ko",
        )
        meta_names = (
            "modules.dep",
            "modules.alias",
            "modules.builtin",
            "modules.order",
            "modules.symbols",
            "modules.devname",
        )
        staged: list[str] = []
        with tempfile.TemporaryDirectory() as td:
            extract = Path(td) / "initrd"
            extract.mkdir()
            # Alpine initramfs-virt is gzip+cpio
            raw = Path(td) / "initrd.cpio"
            with gzip.open(src_initrd, "rb") as src, raw.open("wb") as dst:
                shutil.copyfileobj(src, dst)
            proc = subprocess.run(
                ["cpio", "-idm"],
                cwd=extract,
                stdin=raw.open("rb"),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                check=False,
            )
            if proc.returncode != 0:
                return {
                    "ok": False,
                    "error": "cpio_extract_failed",
                    "detail": (proc.stderr or b"").decode("utf-8", errors="replace")[:400],
                    "staged": 0,
                }
            mod_roots = list((extract / "lib" / "modules").glob("*"))
            if not mod_roots:
                return {"ok": False, "error": "no_modules_tree", "staged": 0}
            mod_root = mod_roots[0]
            kver = mod_root.name
            dest_root = rootfs / "lib" / "modules" / kver
            for path in mod_root.rglob("*.ko"):
                rel = path.relative_to(mod_root).as_posix()
                if not any(rel.endswith(suf) or suf in rel for suf in wanted_suffixes):
                    continue
                dst = dest_root / path.relative_to(mod_root)
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, dst)
                staged.append(rel)
            for name in meta_names:
                src = mod_root / name
                if src.exists():
                    dest_root.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dest_root / name)
                    staged.append(name)
            # Narrow modules.dep to staged modules only (faster + honest).
            dep_src = mod_root / "modules.dep"
            if dep_src.exists():
                lines = []
                for line in dep_src.read_text(encoding="utf-8", errors="replace").splitlines():
                    head = line.split(":", 1)[0].strip()
                    if any(head.endswith(suf) or suf in head for suf in wanted_suffixes):
                        lines.append(line)
                (dest_root / "modules.dep").write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
        return {
            "ok": bool(staged),
            "kernel_release": kver if staged else None,
            "staged": len(staged),
            "modules": staged[:40],
            "note": "DRM/virtio-gpu modules staged for guest-proven dual outputs",
        }

    def _copy_overlay(self, rootfs: Path) -> None:
        overlay = self.paths.overlay
        if not overlay.exists():
            raise FileNotFoundError(f"overlay missing: {overlay}")
        for src in overlay.rglob("*"):
            rel = src.relative_to(overlay)
            dst = rootfs / rel
            if src.is_dir():
                dst.mkdir(parents=True, exist_ok=True)
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
                # Preserve executable bits for scripts.
                mode = src.stat().st_mode
                dst.chmod(mode)

    def assemble_rootfs(self) -> Path:
        rootfs = self.paths.work / "rootfs"
        if rootfs.exists():
            shutil.rmtree(rootfs)
        rootfs.mkdir(parents=True)
        with tarfile.open(self.minirootfs_tarball, "r:gz") as tar:
            tar.extractall(rootfs)
        # Ensure mount points exist.
        for d in ("proc", "sys", "dev", "tmp", "run", "var/lib/gunnchos/state"):
            (rootfs / d).mkdir(parents=True, exist_ok=True)
        self._copy_overlay(rootfs)
        # Stage DRM/virtio-gpu modules so guest display_info can prove dual outputs.
        self._last_drm_stage = self.stage_drm_modules(rootfs)
        # Make /init executable.
        init = rootfs / "init"
        if not init.exists():
            raise FileNotFoundError("overlay did not provide /init")
        init.chmod(0o755)
        return rootfs

    def pack_initramfs(self, rootfs: Path) -> Path:
        out = self.paths.artifacts / "gunnchos-ref-initramfs.cpio.gz"
        # Use BSD/macOS-compatible cpio via find | cpio.
        with tempfile.TemporaryDirectory() as td:
            staging = Path(td)
            # Create cpio from within rootfs so paths are relative.
            list_file = staging / "filelist.txt"
            files = []
            for p in sorted(rootfs.rglob("*")):
                rel = p.relative_to(rootfs).as_posix()
                if rel in (".",):
                    continue
                files.append(rel)
            # Ensure init is first-ish; cpio order doesn't matter for kernel.
            list_file.write_text("\n".join(files) + "\n", encoding="utf-8")
            cpio_raw = staging / "rootfs.cpio"
            with list_file.open() as lf, cpio_raw.open("wb") as out_cpio:
                proc = subprocess.run(
                    ["cpio", "-o", "-H", "newc"],
                    cwd=rootfs,
                    stdin=lf,
                    stdout=out_cpio,
                    stderr=subprocess.PIPE,
                    check=False,
                )
            if proc.returncode != 0:
                raise RuntimeError(f"cpio failed: {proc.stderr.decode()}")
            with cpio_raw.open("rb") as src, gzip.open(out, "wb", compresslevel=6) as dst:
                shutil.copyfileobj(src, dst)
        # Also copy kernel next to artifact for boot convenience.
        kdest = self.paths.artifacts / "vmlinuz-virt"
        shutil.copy2(self.kernel_path, kdest)
        return out

    def write_manifest(self, *, initramfs: Path, cache_status: dict[str, Any]) -> Path:
        manifest = {
            "schema": "gunnchos.bootable_reference_image.manifest.v1",
            "product": "gunnchOS",
            "realm": "DEV",
            "version": "0.3.0-dev",
            "bootable": True,
            "target": {
                "emulator": "qemu-system-aarch64",
                "machine": "virt",
                "cpu": "max",
                "firmware": "linux_direct_kernel",
                "arch": ALPINE_ARCH,
            },
            "components": {
                "bootloader": "linux_direct_kernel (QEMU -kernel/-initrd)",
                "kernel": "Alpine linux-virt (netboot vmlinuz-virt)",
                "rootfs": "Alpine minirootfs + gunnchos overlay",
                "init": "/init",
                "services": list(REQUIRED_SERVICES),
                "shell": "/opt/gunnchos/bin/gunnchos-shell",
                "networking": "loopback",
                "app_runtime": "/opt/gunnchos/apps/manifest.json",
                "updater": "A/B slot markers + ab_status.sh",
                "recovery": "self_check.sh + factory reset path marker",
            },
            "artifacts": {
                "initramfs": {
                    "path": str(initramfs.relative_to(_repo_root())),
                    "sha256": _sha256_file(initramfs),
                    "size_bytes": initramfs.stat().st_size,
                },
                "kernel": {
                    "path": "os_build/bootable_reference/artifacts/vmlinuz-virt",
                    "sha256": _sha256_file(self.paths.artifacts / "vmlinuz-virt"),
                },
            },
            "cache": cache_status,
            "production_keys_used": False,
            "physical_boot_claimed": False,
            "claim_boundary": CLAIM_BOUNDARY,
            "tokens_pending_boot_evidence": [TOKEN_DIGITAL_PASS, TOKEN_PHYSICAL_PENDING],
        }
        path = self.paths.artifacts / "MANIFEST.json"
        path.write_bytes(_canonical_json(manifest) + b"\n")
        # Human-readable copy under results for evidence browsing.
        evidence_copy = self.paths.evidence_dir / "MANIFEST.json"
        evidence_copy.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")
        return path

    def build(self, *, fetch: bool = True) -> dict[str, Any]:
        cache_status = self.ensure_cache(fetch=fetch)
        self._last_drm_stage = {"ok": False, "staged": 0}
        rootfs = self.assemble_rootfs()
        initramfs = self.pack_initramfs(rootfs)
        manifest_path = self.write_manifest(initramfs=initramfs, cache_status=cache_status)
        return {
            "ok": True,
            "initramfs": str(initramfs),
            "kernel": str(self.paths.artifacts / "vmlinuz-virt"),
            "manifest": str(manifest_path),
            "rootfs": str(rootfs),
            "bootable": True,
            "drm_modules": getattr(self, "_last_drm_stage", {}),
            "production_keys_used": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }


class QemuBootHarness:
    """Boot the reference image under QEMU and capture serial evidence."""

    def __init__(self, paths: BootableImagePaths | None = None) -> None:
        self.paths = paths or BootableImagePaths()
        self.paths.evidence_dir.mkdir(parents=True, exist_ok=True)
        self.paths.artifacts.mkdir(parents=True, exist_ok=True)

    def qemu_bin(self) -> str:
        env = os.environ.get("GUNNCHOS_QEMU_BIN")
        if env:
            return env
        which = shutil.which("qemu-system-aarch64")
        if which:
            return which
        brew = Path("/opt/homebrew/bin/qemu-system-aarch64")
        if brew.exists():
            return str(brew)
        raise FileNotFoundError("qemu-system-aarch64 not found on PATH")

    def boot(
        self,
        *,
        timeout_sec: float = 240.0,
        memory_mb: int = 512,
    ) -> dict[str, Any]:
        kernel = self.paths.artifacts / "vmlinuz-virt"
        initrd = self.paths.artifacts / "gunnchos-ref-initramfs.cpio.gz"
        if not kernel.exists() or not initrd.exists():
            raise FileNotFoundError("build artifacts missing; run BootableReferenceBuilder.build first")

        log_path = self.paths.evidence_dir / "qemu_serial_boot.log"
        artifact_log_path = self.paths.artifacts / "qemu_serial_boot.log"
        evidence_path = self.paths.evidence_dir / "BOOT_EVIDENCE.json"
        artifact_evidence = self.paths.artifacts / "BOOT_EVIDENCE.json"

        cmd = [
            self.qemu_bin(),
            "-M",
            "virt",
            "-cpu",
            "max",
            "-smp",
            "4",
            "-m",
            str(memory_mb),
            "-nographic",
            "-no-reboot",
            "-kernel",
            str(kernel),
            "-initrd",
            str(initrd),
            "-append",
            "console=ttyAMA0 earlyprintk=serial rdinit=/init panic=1",
            "-serial",
            "stdio",
            "-monitor",
            "none",
        ]

        t0 = time.time()
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            text=True,
            bufsize=1,
        )
        lines: list[str] = []
        assert proc.stdout is not None
        deadline = t0 + timeout_sec
        completed_marker = False
        try:
            while True:
                if time.time() > deadline:
                    proc.kill()
                    break
                line = proc.stdout.readline()
                if not line:
                    if proc.poll() is not None:
                        break
                    time.sleep(0.05)
                    continue
                lines.append(line.rstrip("\n"))
                if "GUNNCHOS_BOOT_MARKER=OK" in line:
                    completed_marker = True
                # Once we see boot complete, wait briefly then stop.
                if "GUNNCHOS_BOOT_COMPLETE=true" in line:
                    # Give guest a moment to halt; then kill if still running.
                    time.sleep(1.5)
                    if proc.poll() is None:
                        proc.kill()
                    break
        finally:
            if proc.poll() is None:
                proc.kill()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

        elapsed = time.time() - t0
        log_text = "\n".join(lines) + ("\n" if lines else "")
        log_path.write_text(log_text, encoding="utf-8")
        artifact_log_path.write_text(log_text, encoding="utf-8")

        missing = [m for m in REQUIRED_BOOT_MARKERS if m not in log_text]
        service_ok = all(f"svc={s} ok=true" in log_text for s in REQUIRED_SERVICES)
        ok = completed_marker and not missing and service_ok and ("GUNNCHOS_PRODUCTION_KEYS=false" in log_text)

        # Prefer the committed artifacts path for PR evidence browsing.
        committed_log = str(artifact_log_path.relative_to(_repo_root()))
        evidence = {
            "schema": "gunnchos.bootable_reference_image.boot_evidence.v1",
            "ok": ok,
            "bootable_under_qemu": ok,
            "target": "qemu-system-aarch64",
            "machine": "virt",
            "elapsed_sec": round(elapsed, 3),
            "qemu_bin": self.qemu_bin(),
            "log_path": committed_log,
            "log_path_results": str(log_path.relative_to(_repo_root())),
            "markers_required": list(REQUIRED_BOOT_MARKERS),
            "markers_missing": missing,
            "services_required": list(REQUIRED_SERVICES),
            "services_all_started": service_ok,
            "production_keys_used": False,
            "physical_boot_claimed": False,
            "token": TOKEN_DIGITAL_PASS if ok else None,
            "status_tokens": (
                [TOKEN_DIGITAL_PASS, TOKEN_PHYSICAL_PENDING]
                if ok
                else [TOKEN_PHYSICAL_PENDING]
            ),
            "claim_boundary": CLAIM_BOUNDARY,
            "full_operational_product_claimed": False,
            "command": cmd,
        }
        payload = _canonical_json(evidence) + b"\n"
        evidence_path.write_bytes(payload)
        artifact_evidence.write_bytes(payload)
        return evidence


def build_and_boot(*, fetch: bool = True, timeout_sec: float = 240.0) -> dict[str, Any]:
    builder = BootableReferenceBuilder()
    build = builder.build(fetch=fetch)
    harness = QemuBootHarness(builder.paths)
    evidence = harness.boot(timeout_sec=timeout_sec)
    return {
        "build": build,
        "evidence": evidence,
        "token": evidence.get("token"),
        "ok": bool(evidence.get("ok")),
        "claim_boundary": CLAIM_BOUNDARY,
    }


def validate_boot_evidence(evidence: dict[str, Any] | None = None) -> dict[str, Any]:
    paths = BootableImagePaths()
    if evidence is None:
        path = paths.evidence_dir / "BOOT_EVIDENCE.json"
        if not path.exists():
            path = paths.artifacts / "BOOT_EVIDENCE.json"
        if not path.exists():
            return {
                "ok": False,
                "token": None,
                "error": "BOOT_EVIDENCE.json missing",
                "claim_boundary": CLAIM_BOUNDARY,
            }
        evidence = json.loads(path.read_text(encoding="utf-8"))
    ok = bool(evidence.get("ok")) and evidence.get("token") == TOKEN_DIGITAL_PASS
    return {
        "ok": ok,
        "token": TOKEN_DIGITAL_PASS if ok else None,
        "status_tokens": evidence.get("status_tokens") or [TOKEN_PHYSICAL_PENDING],
        "log_path": evidence.get("log_path"),
        "claim_boundary": CLAIM_BOUNDARY,
        "physical_boot_claimed": False,
        "production_keys_used": False,
        "full_operational_product_claimed": False,
    }
