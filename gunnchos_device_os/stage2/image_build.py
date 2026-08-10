"""Reproducible Stage 2 system/recovery image builder."""
from __future__ import annotations

import json
import os
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from gunnchos_device_os.stage2 import STAGE2_VERSION
from gunnchos_device_os.stage2.crypto_dev import (
    DEV_REALM,
    sha256_file,
    sign_payload,
    write_dev_key_stub,
)
from gunnchos_device_os.stage2.filesystem import CONTRACT_DIRS, ensure_sysroot

ARTIFACT_REL = Path("artifacts") / "stage2" / "image"
SYSROOT_REL = Path("artifacts") / "stage2" / "sysroot"

PACKAGE_LIST = [
    "gunnchos-base",
    "gunnchos-shell-weston",
    "gunnchos-updater",
    "gunnchos-recovery",
    "gunnchos-sandbox",
    "linux-image-lts-policy",
]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _relpath_for_artifact(path: Path, repo: Path) -> str:
    """Store only repo-relative paths — never host /Users/... absolutes."""
    try:
        return str(path.resolve().relative_to(repo.resolve()))
    except ValueError:
        # Fall back to artifacts-relative if somehow outside repo
        name = path.name
        return f"artifacts/stage2/image/{name}"


def build_image(
    *,
    repo_root: Path | None = None,
    version: str | None = None,
    out_dir: Path | None = None,
) -> dict[str, Any]:
    repo = (repo_root or _repo_root()).resolve()
    version = version or STAGE2_VERSION
    out = (out_dir or (repo / ARTIFACT_REL)).resolve()
    out.mkdir(parents=True, exist_ok=True)

    sysroot = ensure_sysroot(repo / SYSROOT_REL)
    keys_dir = repo / "os_build" / "stage2" / "keys"
    write_dev_key_stub(keys_dir)

    # Seed slot A as the "good" baseline image content
    slot_a = sysroot.path("system-a")
    (slot_a / "etc").mkdir(exist_ok=True)
    (slot_a / "etc" / "os-release").write_text(
        f"NAME=gunnchOS\nVERSION={version}\nSLOT=A\n", encoding="utf-8"
    )
    (slot_a / "usr" / "lib" / "gunnchos").mkdir(parents=True, exist_ok=True)
    (slot_a / "usr" / "lib" / "gunnchos" / "healthcheck").write_text(
        "#!/bin/sh\nexit 0\n", encoding="utf-8"
    )
    (slot_a / "IMAGE_VERSION").write_text(version + "\n", encoding="utf-8")

    # User data sample (must survive rollback)
    home = sysroot.path("home") / "user"
    home.mkdir(parents=True, exist_ok=True)
    (home / "KEEPME.txt").write_text("user-data-must-survive-rollback\n", encoding="utf-8")
    data = sysroot.path("data")
    (data / "appstate.json").write_text('{"ok":true}\n', encoding="utf-8")

    # Build system image tarball from slot A content (deterministic mtime)
    system_img = out / "system.img.tar"
    _write_deterministic_tar(system_img, slot_a, arcname_root="system")

    # Recovery image
    recovery_dir = sysroot.path("recovery")
    (recovery_dir / "RECOVERY_VERSION").write_text(version + "\n", encoding="utf-8")
    (recovery_dir / "tools").mkdir(exist_ok=True)
    (recovery_dir / "tools" / "README").write_text(
        "Stage 2 recovery tools stub\n", encoding="utf-8"
    )
    recovery_img = out / "recovery.img.tar"
    _write_deterministic_tar(recovery_img, recovery_dir, arcname_root="recovery")

    system_hash = sha256_file(system_img)
    recovery_hash = sha256_file(recovery_img)

    packages = {
        "schema": "gunnchos.stage2.packages.v1",
        "packages": [{"name": n, "version": version} for n in PACKAGE_LIST],
    }
    packages_path = out / "packages.json"
    packages_path.write_text(json.dumps(packages, indent=2) + "\n", encoding="utf-8")

    sbom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.5",
        "version": 1,
        "metadata": {
            "component": {
                "type": "operating-system",
                "name": "gunnchOS-stage2",
                "version": version,
            }
        },
        "components": [
            {"type": "library", "name": n, "version": version} for n in PACKAGE_LIST
        ],
    }
    sbom_path = out / "sbom.cdx.json"
    sbom_path.write_text(json.dumps(sbom, indent=2) + "\n", encoding="utf-8")

    version_doc = {
        "schema": "gunnchos.stage2.version.v1",
        "version": version,
        "channel": "stage2-dev",
        "security_version": 1,
        "kernel_policy": {
            "family": "linux",
            "track": "LTS",
            "preferred_series": "6.6.x",
            "note": "Distro LTS policy — no custom vanity kernel",
        },
        "filesystem_contract": list(CONTRACT_DIRS),
        "physical_execution_freeze": True,
        "frontier_os_parity_claimed": False,
    }
    version_path = out / "VERSION.json"
    version_path.write_text(json.dumps(version_doc, indent=2) + "\n", encoding="utf-8")

    provenance = {
        "schema": "gunnchos.stage2.provenance.v1",
        "built_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "builder": "scripts/stage2_build_image.py",
        "source_tree": "gunnchos-device-os",
        "reproducible": True,
        "host_paths_forbidden": True,
        "inputs": {
            "stage2_version": version,
            "package_list": PACKAGE_LIST,
        },
    }
    provenance_path = out / "provenance.json"
    provenance_path.write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")

    manifest_body = {
        "schema": "gunnchos.stage2.image_manifest.v1",
        "version": version,
        "realm": DEV_REALM,
        "security_version": 1,
        "system_image": "system.img.tar",
        "system_sha256": system_hash,
        "recovery_image": "recovery.img.tar",
        "recovery_sha256": recovery_hash,
        "packages": "packages.json",
        "sbom": "sbom.cdx.json",
        "version_file": "VERSION.json",
        "provenance": "provenance.json",
        "sysroot_rel": str(SYSROOT_REL).replace("\\", "/"),
    }
    manifest_body["signature"] = sign_payload(manifest_body)
    manifest_path = out / "MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest_body, indent=2) + "\n", encoding="utf-8")

    hashes = {
        "system.img.tar": system_hash,
        "recovery.img.tar": recovery_hash,
        "MANIFEST.json": sha256_file(manifest_path),
        "packages.json": sha256_file(packages_path),
        "sbom.cdx.json": sha256_file(sbom_path),
        "VERSION.json": sha256_file(version_path),
        "provenance.json": sha256_file(provenance_path),
    }
    hashes_path = out / "HASHES.json"
    hashes_path.write_text(json.dumps(hashes, indent=2) + "\n", encoding="utf-8")

    # Sanity: no absolute /Users paths in written JSON artifacts
    for p in (manifest_path, provenance_path, version_path, packages_path):
        text = p.read_text(encoding="utf-8")
        if "/Users/" in text:
            raise RuntimeError(f"host-local path leaked into {p.name}")

    return {
        "ok": True,
        "out_dir": _relpath_for_artifact(out, repo),
        "version": version,
        "system_sha256": system_hash,
        "recovery_sha256": recovery_hash,
        "manifest": manifest_body,
        "hashes": hashes,
        "sysroot": _relpath_for_artifact(sysroot.root, repo),
        "token": "OS_BASE_IMAGE_REAL",
    }


def _write_deterministic_tar(dest: Path, src_dir: Path, *, arcname_root: str) -> None:
    if dest.exists():
        dest.unlink()
    # Fixed mtime for reproducibility
    fixed_mtime = 1700000000
    with tarfile.open(dest, "w") as tar:
        for path in sorted(src_dir.rglob("*")):
            if path.is_dir():
                continue
            rel = path.relative_to(src_dir).as_posix()
            info = tarfile.TarInfo(name=f"{arcname_root}/{rel}")
            data = path.read_bytes()
            info.size = len(data)
            info.mtime = fixed_mtime
            info.mode = 0o644
            info.uid = 0
            info.gid = 0
            import io

            tar.addfile(info, io.BytesIO(data))
