"""Realm-scoped OS image builder — real rootfs-tarball artifacts.

Honest scope: this builder does NOT compile a fresh kernel per realm (heavy,
out of scope for a digital/CI environment). It builds a real, deterministic
rootfs tarball populated with real files (the actual `scripts/gunnchctl`
entrypoint, real release-engineering source for dev-capable realms, and a
realm-specific service/package manifest), then attaches the shared
reference kernel/initramfs from ``os_build/bootable_reference`` when those
artifacts happen to be present locally (they are gitignored and are not
guaranteed to exist in a fresh checkout).

Every build produces: rootfs/kernel/image hashes, a package manifest, a
CycloneDX-style SBOM derived from actually-installed Python packages plus
the actual rootfs files, source SHAs (git HEAD), the realm config, a
timestamp, reproducibility metadata, and a signing block. Production always
builds unsigned / NOT_RELEASED — see ``image_realms`` validation.
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tarfile
import time
from importlib import metadata as importlib_metadata
from pathlib import Path
from typing import Any

from gunnchos_device_os.release_engineering import dev_keys, image_realms

BUILD_SCHEMA = "gunnchos.os_image_build.manifest.v1"
BUILDER_CLAIM_BOUNDARY = (
    "Digital rootfs-tarball build, not a physical disk image. Kernel/"
    "initramfs are reused from the shared bootable_reference artifacts when "
    "present locally and are never realm-specific compiled binaries. "
    "PRODUCTION_SHIPPING_IMAGE_DEFINITION builds are always unsigned and "
    "stamped NOT_RELEASED regardless of the --unsigned flag."
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _git_source_shas(repo_root: Path) -> dict[str, Any]:
    def _run(args: list[str]) -> str:
        try:
            out = subprocess.run(
                ["git", *args], cwd=str(repo_root), capture_output=True, text=True, check=False
            )
            return out.stdout.strip()
        except Exception:
            return ""

    head = _run(["rev-parse", "HEAD"]) or None
    branch = _run(["rev-parse", "--abbrev-ref", "HEAD"]) or None
    dirty = bool(_run(["status", "--porcelain"]))
    return {"repo_head_sha": head, "branch": branch, "working_tree_dirty": dirty}


def image_build_root(repo_root: Path) -> Path:
    return repo_root / "os_build" / "realm_images"


class RealmImageBuilder:
    """Build / inspect / verify a single image realm's rootfs artifact."""

    def __init__(self, repo_root: Path | None = None) -> None:
        self.repo_root = Path(repo_root or _repo_root())

    def _realm_out_dir(self, realm_id: str) -> Path:
        d = image_build_root(self.repo_root) / realm_id.lower()
        d.mkdir(parents=True, exist_ok=True)
        return d

    # ------------------------------------------------------------------
    # Staging
    # ------------------------------------------------------------------
    def _stage_rootfs(self, realm: dict[str, Any], stage: Path) -> list[Path]:
        if stage.exists():
            shutil.rmtree(stage)
        stage.mkdir(parents=True, exist_ok=True)

        realm_id = realm["realm_id"]
        included = list(realm.get("packages", {}).get("included") or [])
        excluded = set(realm.get("packages", {}).get("excluded") or [])

        etc = stage / "etc"
        etc.mkdir(parents=True, exist_ok=True)
        (etc / "os-release").write_text(
            "\n".join(
                [
                    "NAME=gunnchOS",
                    f'REALM="{realm_id}"',
                    f'UPDATE_CHANNEL="{realm.get("update_channel")}"',
                    f'STATUS="{realm.get("status")}"',
                    "VERSION_ID=0.3.0-dev",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        gunnchos_etc = etc / "gunnchos"
        gunnchos_etc.mkdir(parents=True, exist_ok=True)
        (gunnchos_etc / "realm.json").write_text(
            json.dumps(realm, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )

        services = stage / "opt" / "gunnchos" / "services"
        services.mkdir(parents=True, exist_ok=True)
        for pkg in included:
            if pkg in excluded:
                continue
            unit = "\n".join(
                [
                    "[Unit]",
                    f"Description=gunnchOS service package {pkg}",
                    f"Realm={realm_id}",
                    "",
                    "[Service]",
                    "Type=notify",
                    f"ExecStart=/opt/gunnchos/bin/gunnchos-svc --package {pkg}",
                    "Restart=on-failure",
                    "",
                ]
            )
            (services / f"{pkg}.service").write_text(unit, encoding="utf-8")

        bin_dir = stage / "opt" / "gunnchos" / "bin"
        bin_dir.mkdir(parents=True, exist_ok=True)
        dev_mode = bool((realm.get("developer_mode") or {}).get("enabled"))
        real_gunnchctl = self.repo_root / "scripts" / "gunnchctl"
        if dev_mode and real_gunnchctl.exists():
            shutil.copy2(real_gunnchctl, bin_dir / "gunnchctl")
            src_pkg = self.repo_root / "gunnchos_device_os" / "release_engineering"
            dst_pkg = stage / "opt" / "gunnchos" / "release_engineering"
            if src_pkg.exists():
                shutil.copytree(
                    src_pkg,
                    dst_pkg,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
                )
        else:
            # Non-dev realms carry a manifest reference instead of the full
            # dev toolchain (matches packages.excluded policy).
            (bin_dir / "NO_DEV_TOOLCHAIN.txt").write_text(
                f"{realm_id} excludes gunnchos.dev.* packages per realm definition.\n",
                encoding="utf-8",
            )

        if realm.get("factory_only_services"):
            factory_dir = stage / "opt" / "gunnchos" / "factory"
            factory_dir.mkdir(parents=True, exist_ok=True)
            (factory_dir / "FACTORY_ONLY_SERVICES.json").write_text(
                json.dumps(sorted(realm["factory_only_services"]), indent=2) + "\n",
                encoding="utf-8",
            )

        recovery = realm.get("recovery_behavior") or {}
        if recovery.get("recovery_partition_required"):
            recov_dir = stage / "opt" / "gunnchos" / "recovery"
            recov_dir.mkdir(parents=True, exist_ok=True)
            (recov_dir / "RECOVERY_POLICY.json").write_text(
                json.dumps(recovery, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )

        files = sorted(p for p in stage.rglob("*") if p.is_file())
        return files

    def _make_deterministic_tar(self, stage: Path, dest: Path, files: list[Path]) -> None:
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            dest.unlink()
        with tarfile.open(dest, "w:gz", compresslevel=6) as tar:
            for f in files:
                arcname = str(f.relative_to(stage))
                info = tar.gettarinfo(str(f), arcname=arcname)
                info.mtime = 0
                info.uid = 0
                info.gid = 0
                info.uname = "root"
                info.gname = "root"
                with f.open("rb") as fh:
                    tar.addfile(info, fh)

    def _package_manifest(self, stage: Path, files: list[Path]) -> list[dict[str, Any]]:
        rows = []
        for f in files:
            rel = str(f.relative_to(stage))
            rows.append(
                {
                    "path": rel,
                    "size_bytes": f.stat().st_size,
                    "sha256": _sha256_file(f),
                }
            )
        return rows

    def _sbom(self, realm_id: str, package_manifest: list[dict[str, Any]]) -> dict[str, Any]:
        components: list[dict[str, Any]] = []
        try:
            dists = sorted(
                importlib_metadata.distributions(), key=lambda d: (d.metadata.get("Name") or "")
            )
        except Exception:
            dists = []
        seen: set[str] = set()
        for dist in dists:
            name = dist.metadata.get("Name") or dist.metadata.get("Summary")
            if not name or name in seen:
                continue
            seen.add(name)
            version = dist.version or "0.0.0"
            components.append(
                {
                    "type": "library",
                    "name": name,
                    "version": version,
                    "purl": f"pkg:pypi/{name.lower()}@{version}",
                    "properties": [{"name": "gunnchos:sbom_source", "value": "installed_python_env"}],
                }
            )
        for row in package_manifest:
            components.append(
                {
                    "type": "file",
                    "name": row["path"],
                    "version": row["sha256"][:12],
                    "purl": f"pkg:generic/{realm_id.lower()}/{row['path']}@{row['sha256'][:12]}",
                    "properties": [
                        {"name": "gunnchos:sbom_source", "value": "rootfs_file"},
                        {"name": "gunnchos:sha256", "value": row["sha256"]},
                        {"name": "gunnchos:size_bytes", "value": str(row["size_bytes"])},
                    ],
                }
            )
        return {
            "bomFormat": "CycloneDX",
            "specVersion": "1.5",
            "version": 1,
            "metadata": {
                "component": {"name": f"gunnchos-{realm_id.lower()}-image", "type": "firmware"},
                "properties": [
                    {"name": "gunnchos:realm", "value": realm_id},
                    {"name": "gunnchos:sbom_kind", "value": "real_from_installed_packages_and_rootfs_files"},
                ],
            },
            "components": components,
        }

    def _kernel_reference(self) -> dict[str, Any]:
        ref_dir = self.repo_root / "os_build" / "bootable_reference" / "artifacts"
        kernel = ref_dir / "vmlinuz-virt"
        initramfs = ref_dir / "gunnchos-ref-initramfs.cpio.gz"
        out: dict[str, Any] = {
            "source": "os_build/bootable_reference (shared reference, not realm-specific)",
            "kernel_present": kernel.exists(),
            "initramfs_present": initramfs.exists(),
        }
        if kernel.exists():
            out["kernel_sha256"] = _sha256_file(kernel)
            out["kernel_path"] = str(kernel.relative_to(self.repo_root))
        if initramfs.exists():
            out["initramfs_sha256"] = _sha256_file(initramfs)
            out["initramfs_path"] = str(initramfs.relative_to(self.repo_root))
        return out

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def build(self, realm_name: str, *, unsigned: bool = False) -> dict[str, Any]:
        realm_id = image_realms.resolve_realm_id(realm_name)
        realm = image_realms.load_realm(self.repo_root, realm_id)
        failures = image_realms.validate_realm(realm)
        if failures:
            return {"ok": False, "error": "realm_invalid", "failures": failures, "realm_id": realm_id}

        is_production = realm_id == "PRODUCTION_SHIPPING_IMAGE_DEFINITION"
        # Production ALWAYS builds unsigned, regardless of the flag passed.
        effective_unsigned = True if is_production else unsigned

        out_dir = self._realm_out_dir(realm_id)
        stage = out_dir / "stage"
        artifacts = out_dir / "artifacts"
        artifacts.mkdir(parents=True, exist_ok=True)

        files = self._stage_rootfs(realm, stage)
        rootfs_tar = artifacts / "rootfs.tar.gz"
        self._make_deterministic_tar(stage, rootfs_tar, files)
        rootfs_sha256 = _sha256_file(rootfs_tar)
        package_manifest = self._package_manifest(stage, files)
        sbom = self._sbom(realm_id, package_manifest)
        kernel_ref = self._kernel_reference()
        source_shas = _git_source_shas(self.repo_root)

        manifest: dict[str, Any] = {
            "schema": BUILD_SCHEMA,
            "realm_id": realm_id,
            "status": realm.get("status"),
            "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "config": realm,
            "artifacts": {
                "rootfs_tarball": {
                    "path": str(rootfs_tar.relative_to(self.repo_root)),
                    "sha256": rootfs_sha256,
                    "size_bytes": rootfs_tar.stat().st_size,
                    "file_count": len(files),
                },
                "kernel_reference": kernel_ref,
            },
            "image_hash": _sha256_bytes(
                rootfs_sha256.encode("utf-8")
                + (kernel_ref.get("kernel_sha256", "") or "").encode("utf-8")
            ),
            "package_manifest": package_manifest,
            "sbom": sbom,
            "source_shas": source_shas,
            "reproducibility": {
                "method": "deterministic_tar(sorted_names, mtime=0, uid=gid=0)",
                "rootfs_sha256": rootfs_sha256,
                "file_count": len(files),
                "verifiable_by": "rebuild_and_compare_rootfs_sha256",
            },
            "signing_realm": (realm.get("trust_roots") or {}).get("key_source"),
            "signed": False,
            "signature": None,
            "unsigned_requested": bool(unsigned),
            "production_keys_used": False,
            "claim_boundary": f"{realm.get('claim_boundary', '')} {BUILDER_CLAIM_BOUNDARY}".strip(),
            "PRODUCTION_RELEASE_CLAIMED": False,
        }

        if not effective_unsigned:
            payload = json.dumps(manifest, sort_keys=True, default=str).encode("utf-8")
            signature = dev_keys.sign_bytes(self.repo_root, payload)
            manifest["signed"] = True
            manifest["signature"] = {
                "algorithm": "Ed25519",
                "signature_hex": signature,
                "public_key_fingerprint": dev_keys.dev_public_key_fingerprint(self.repo_root),
                "claim_boundary": dev_keys.CLAIM_BOUNDARY,
            }

        manifest_path = artifacts / "BUILD_MANIFEST.json"
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")

        return {
            "ok": True,
            "realm_id": realm_id,
            "manifest_path": str(manifest_path.relative_to(self.repo_root)),
            "rootfs_sha256": rootfs_sha256,
            "image_hash": manifest["image_hash"],
            "signed": manifest["signed"],
            "PRODUCTION_RELEASE_CLAIMED": False,
        }

    def inspect(self, realm_name: str) -> dict[str, Any]:
        realm_id = image_realms.resolve_realm_id(realm_name)
        manifest_path = self._realm_out_dir(realm_id) / "artifacts" / "BUILD_MANIFEST.json"
        if not manifest_path.exists():
            return {"ok": False, "error": "not_built", "realm_id": realm_id}
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        return {"ok": True, "realm_id": realm_id, "manifest": manifest, "path": str(manifest_path)}

    def verify(self, realm_name: str) -> dict[str, Any]:
        info = self.inspect(realm_name)
        if not info.get("ok"):
            return info
        realm_id = info["realm_id"]
        manifest = info["manifest"]
        failures: list[str] = []

        rootfs_meta = (manifest.get("artifacts") or {}).get("rootfs_tarball") or {}
        rootfs_path = self.repo_root / rootfs_meta.get("path", "")
        if not rootfs_path.exists():
            failures.append("rootfs_tarball_missing")
        elif rootfs_meta.get("sha256") and _sha256_file(rootfs_path) != rootfs_meta["sha256"]:
            failures.append("rootfs_hash_mismatch")

        if manifest.get("production_keys_used") is True:
            failures.append("production_keys_claimed")
        if manifest.get("PRODUCTION_RELEASE_CLAIMED") is True:
            failures.append("production_release_claimed")

        if realm_id == "PRODUCTION_SHIPPING_IMAGE_DEFINITION":
            if manifest.get("status") != "NOT_RELEASED":
                failures.append("production_status_not_not_released")
            if manifest.get("signed") is True:
                failures.append("production_must_be_unsigned")

        if manifest.get("signed"):
            sig = manifest.get("signature") or {}
            unsigned_manifest = dict(manifest)
            unsigned_manifest["signed"] = False
            unsigned_manifest["signature"] = None
            payload = json.dumps(unsigned_manifest, sort_keys=True, default=str).encode("utf-8")
            if not dev_keys.verify_bytes(self.repo_root, payload, sig.get("signature_hex", "")):
                failures.append("signature_verification_failed")

        realm_failures = image_realms.validate_realm(manifest.get("config") or {})
        failures.extend(f"realm_config:{f}" for f in realm_failures)

        return {
            "ok": not failures,
            "realm_id": realm_id,
            "failures": failures,
            "manifest_path": info.get("path"),
        }
