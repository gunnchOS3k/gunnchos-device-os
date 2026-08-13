"""Lab development guest image builder — hybrid Alpine base + gunnchOS services.

Honest: not a full production OS image; uses bootable_reference overlay where present.
No production keys. SILICON_EXACT_EMULATION remains false.
"""
from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

from gunnchos_device_os.bootable_image.builder import BootableImagePaths, BootableReferenceBuilder, CLAIM_BOUNDARY

LAB_IMAGE_SCHEMA = "gunnchos.device_lab.guest_image.manifest.v1"
LAB_IMAGE_VERSION = "0.1.0-lab-dev"
# WP-011R: this guest is a Lab development image, not the shipping OS image.
DEVICE_LAB_DEVELOPMENT_GUEST = True
SHIPPING_IMAGE = False


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def lab_image_root(repo_root: Path | None = None) -> Path:
    root = repo_root or _repo_root()
    return root / "os_build" / "device_lab_guest"


class LabGuestImageBuilder:
    """Build / inspect / verify the Lab development guest (reuses bootable_reference)."""

    def __init__(self, repo_root: Path | None = None) -> None:
        self.repo_root = Path(repo_root or _repo_root())
        self.lab_root = lab_image_root(self.repo_root)
        self.lab_root.mkdir(parents=True, exist_ok=True)
        self.artifacts = self.lab_root / "artifacts"
        self.artifacts.mkdir(parents=True, exist_ok=True)
        # Reuse official bootable_reference cache/overlay/artifacts pipeline.
        self.ref = BootableReferenceBuilder(
            BootableImagePaths(track=self.repo_root / "os_build" / "bootable_reference")
        )

    def build(self, *, fetch: bool = True) -> dict[str, Any]:
        built = self.ref.build(fetch=fetch)
        # Symlink/copy into Lab guest artifact tree for stable Lab paths.
        for name in ("gunnchos-ref-initramfs.cpio.gz", "vmlinuz-virt", "MANIFEST.json"):
            src = self.ref.paths.artifacts / name
            if not src.exists():
                continue
            dst = self.artifacts / name
            if dst.exists() or dst.is_symlink():
                dst.unlink()
            try:
                dst.symlink_to(src.resolve())
            except OSError:
                shutil.copy2(src, dst)
        manifest = self.write_lab_manifest(built)
        return {
            "ok": True,
            "schema": LAB_IMAGE_SCHEMA,
            "version": LAB_IMAGE_VERSION,
            "hybrid_base": "alpine_minirootfs + gunnchOS overlay",
            "DEVICE_LAB_DEVELOPMENT_GUEST": DEVICE_LAB_DEVELOPMENT_GUEST,
            "SHIPPING_IMAGE": SHIPPING_IMAGE,
            "initramfs": str(self.artifacts / "gunnchos-ref-initramfs.cpio.gz"),
            "kernel": str(self.artifacts / "vmlinuz-virt"),
            "manifest": str(manifest),
            "production_keys_used": False,
            "SILICON_EXACT_EMULATION": False,
            "claim_boundary": CLAIM_BOUNDARY,
            "GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE": False,
        }

    def write_lab_manifest(self, built: dict[str, Any]) -> Path:
        initrd = self.artifacts / "gunnchos-ref-initramfs.cpio.gz"
        kernel = self.artifacts / "vmlinuz-virt"
        payload = {
            "schema": LAB_IMAGE_SCHEMA,
            "version": LAB_IMAGE_VERSION,
            "realm": "DEV_LAB",
            "hybrid_base": True,
            "real_gunnchos_services": True,
            "production_keys_used": False,
            "physical_boot_claimed": False,
            "SILICON_EXACT_EMULATION": False,
            "artifacts": {
                "initramfs": {
                    "path": str(initrd.relative_to(self.repo_root)) if initrd.exists() else None,
                    "sha256": _sha256_file(initrd) if initrd.exists() else None,
                    "size_bytes": initrd.stat().st_size if initrd.exists() else None,
                },
                "kernel": {
                    "path": str(kernel.relative_to(self.repo_root)) if kernel.exists() else None,
                    "sha256": _sha256_file(kernel) if kernel.exists() else None,
                },
            },
            "upstream_bootable_reference": {
                "initramfs": built.get("initramfs"),
                "kernel": built.get("kernel"),
                "manifest": built.get("manifest"),
            },
            "claim_boundary": (
                "Lab development guest: hybrid Alpine userspace + real gunnchOS service "
                "overlay. Not silicon-exact; not production keys; not physical boot."
            ),
            "GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE": False,
            "GUNNCHDEVICE_LAB_GUEST_IMAGE_PREPARED": True,
        }
        path = self.artifacts / "LAB_GUEST_MANIFEST.json"
        path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return path

    def inspect(self) -> dict[str, Any]:
        path = self.artifacts / "LAB_GUEST_MANIFEST.json"
        if not path.exists():
            # Fall back to bootable_reference artifacts
            ref_initrd = self.ref.paths.artifacts / "gunnchos-ref-initramfs.cpio.gz"
            ref_kernel = self.ref.paths.artifacts / "vmlinuz-virt"
            return {
                "ok": ref_initrd.exists() and ref_kernel.exists(),
                "lab_manifest_present": False,
                "ref_initramfs_present": ref_initrd.exists(),
                "ref_kernel_present": ref_kernel.exists(),
                "note": "Run gunnchctl image build to materialize Lab guest manifest",
                "SILICON_EXACT_EMULATION": False,
            }
        data = json.loads(path.read_text(encoding="utf-8"))
        return {"ok": True, "manifest": data, "path": str(path)}

    def verify(self) -> dict[str, Any]:
        info = self.inspect()
        if not info.get("ok"):
            return {
                "ok": False,
                "error": "lab_or_ref_artifacts_missing",
                "inspect": info,
                "SILICON_EXACT_EMULATION": False,
            }
        manifest = info.get("manifest")
        if not manifest:
            # Reference-only presence
            return {
                "ok": True,
                "mode": "bootable_reference_fallback",
                "inspect": info,
                "SILICON_EXACT_EMULATION": False,
                "GUNNCHDEVICE_LAB_GUEST_IMAGE_PREPARED": False,
                "GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE": False,
            }
        arts = manifest.get("artifacts") or {}
        initrd_meta = arts.get("initramfs") or {}
        kernel_meta = arts.get("kernel") or {}
        initrd = self.artifacts / "gunnchos-ref-initramfs.cpio.gz"
        kernel = self.artifacts / "vmlinuz-virt"
        failures: list[str] = []
        if not initrd.exists():
            failures.append("initramfs_missing")
        elif initrd_meta.get("sha256") and _sha256_file(initrd) != initrd_meta.get("sha256"):
            failures.append("initramfs_hash_mismatch")
        if not kernel.exists():
            failures.append("kernel_missing")
        elif kernel_meta.get("sha256") and _sha256_file(kernel) != kernel_meta.get("sha256"):
            failures.append("kernel_hash_mismatch")
        if manifest.get("production_keys_used") is True:
            failures.append("production_keys_claimed")
        if manifest.get("SILICON_EXACT_EMULATION") is True:
            failures.append("silicon_exact_claimed")
        return {
            "ok": not failures,
            "failures": failures,
            "manifest_path": info.get("path"),
            "SILICON_EXACT_EMULATION": False,
            "GUNNCHDEVICE_LAB_GUEST_IMAGE_PREPARED": bool(not failures),
            "GUNNCHDEVICE_LAB_FULL_ECOSYSTEM_DIGITAL_COMPLETE": False,
        }
