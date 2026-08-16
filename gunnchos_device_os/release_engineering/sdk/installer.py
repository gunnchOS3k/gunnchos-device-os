"""gunnchSDK package installer — install / update / uninstall lifecycle,
sandbox profile materialization, and the installed-package registry.

The API compatibility gate (`sdk.compat`) is consulted before any package
is unpacked; incompatible packages are rejected outright.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import time
import zipfile
from pathlib import Path
from typing import Any

from gunnchos_device_os.release_engineering import dev_keys
from gunnchos_device_os.release_engineering.sdk import compat
from gunnchos_device_os.release_engineering.sdk.manifest import validate_manifest

REGISTRY_SCHEMA = "gunnchos.sdk.installed_registry.v1"


class InstallError(RuntimeError):
    pass


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class PackageInstaller:
    """Manages `<install_root>/apps/<app_id>/<version>/` payload trees plus
    `<install_root>/registry.json`. Fully virtual — install_root is any
    directory (tests use tmp_path; CLI defaults to a repo-local runtime dir)."""

    def __init__(self, repo_root: Path, install_root: Path) -> None:
        self.repo_root = Path(repo_root)
        self.install_root = Path(install_root)
        self.install_root.mkdir(parents=True, exist_ok=True)

    @property
    def registry_path(self) -> Path:
        return self.install_root / "registry.json"

    def _read_registry(self) -> dict[str, Any]:
        if not self.registry_path.exists():
            return {"schema": REGISTRY_SCHEMA, "apps": {}}
        return json.loads(self.registry_path.read_text(encoding="utf-8"))

    def _write_registry(self, reg: dict[str, Any]) -> None:
        self.registry_path.write_text(json.dumps(reg, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def list_installed(self) -> dict[str, Any]:
        return self._read_registry()

    def _open_and_verify(self, package_path: Path) -> tuple[dict, dict, dict | None, zipfile.ZipFile]:
        zf = zipfile.ZipFile(package_path, "r")
        manifest = json.loads(zf.read("manifest.json"))
        package_manifest = json.loads(zf.read("PACKAGE_MANIFEST.json"))
        signature_raw = zf.read("SIGNATURE.json").decode("utf-8")
        signature = json.loads(signature_raw) if signature_raw.strip() != "null" else None

        manifest_failures = validate_manifest(manifest)
        if manifest_failures:
            zf.close()
            raise InstallError(f"manifest_invalid:{manifest_failures}")

        # Recompute the digest from the files actually inside the archive —
        # protects against a tampered PACKAGE_MANIFEST.json.
        recomputed = []
        for entry in package_manifest["files"]:
            data = zf.read(f"payload/{entry['path']}")
            actual_sha = _sha256_bytes(data)
            if actual_sha != entry["sha256"]:
                zf.close()
                raise InstallError(f"file_hash_mismatch:{entry['path']}")
            recomputed.append({"path": entry["path"], "sha256": actual_sha})
        digest_source = "".join(f"{e['path']}:{e['sha256']}" for e in sorted(recomputed, key=lambda e: e["path"]))
        recomputed_digest = _sha256_bytes(digest_source.encode("utf-8"))
        if recomputed_digest != package_manifest["package_digest"]:
            zf.close()
            raise InstallError("package_digest_mismatch")

        if signature is not None:
            valid = dev_keys.verify_bytes(
                self.repo_root, package_manifest["package_digest"].encode("utf-8"), signature["signature_hex"]
            )
            if not valid:
                zf.close()
                raise InstallError("signature_verification_failed")

        return manifest, package_manifest, signature, zf

    def install(
        self, package_path: Path, *, os_version: str = compat.CURRENT_OS_VERSION, force: bool = False
    ) -> dict[str, Any]:
        package_path = Path(package_path)
        manifest, package_manifest, signature, zf = self._open_and_verify(package_path)
        try:
            gate = compat.check_compatibility(manifest, os_version=os_version)
            if not gate["ok"] and not force:
                return {"ok": False, "error": "api_compatibility_gate_rejected", "gate": gate}

            reg = self._read_registry()
            app_id = manifest["app_id"]
            existing = reg["apps"].get(app_id)
            if existing and existing["version"] == manifest["version"] and not force:
                return {"ok": False, "error": "already_installed", "app_id": app_id, "version": manifest["version"]}

            app_root = self.install_root / "apps" / app_id
            version_dir = app_root / manifest["version"]
            if version_dir.exists():
                shutil.rmtree(version_dir)
            version_dir.mkdir(parents=True, exist_ok=True)
            for entry in package_manifest["files"]:
                dest = version_dir / entry["path"]
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(zf.read(f"payload/{entry['path']}"))

            sandbox_dir = app_root / "sandbox"
            for sub in ("data", "logs", "crash_reports"):
                (sandbox_dir / sub).mkdir(parents=True, exist_ok=True)
            (sandbox_dir / "SANDBOX_PROFILE.json").write_text(
                json.dumps(manifest.get("sandbox_profile", {}), indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            previous_version = existing["version"] if existing else None
            reg["apps"][app_id] = {
                "app_id": app_id,
                "version": manifest["version"],
                "previous_version": previous_version,
                "installed_path": str(version_dir.relative_to(self.install_root)),
                "manifest": manifest,
                "signed": signature is not None,
                "signing_tier": (signature or {}).get("signing_tier", "UNSIGNED"),
                "gate": gate,
                "status": "installed",
                "installed_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            self._write_registry(reg)
            return {
                "ok": True,
                "app_id": app_id,
                "version": manifest["version"],
                "action": "updated" if existing else "installed",
                "previous_version": previous_version,
                "gate_warnings": gate.get("warnings", []),
            }
        finally:
            zf.close()


    def install_interrupted(
        self,
        package_path: Path,
        *,
        interrupt_after_files: int = 1,
        os_version: str = compat.CURRENT_OS_VERSION,
    ) -> dict[str, Any]:
        """Begin an install and stop mid-extract — leaves INCOMPLETE, never success.

        Used by A-PKT-003 J-R1. Caller must recover via detect_incomplete / rollback.
        """
        package_path = Path(package_path)
        manifest, package_manifest, signature, zf = self._open_and_verify(package_path)
        try:
            gate = compat.check_compatibility(manifest, os_version=os_version)
            if not gate["ok"]:
                return {"ok": False, "error": "api_compatibility_gate_rejected", "gate": gate}
            reg = self._read_registry()
            app_id = manifest["app_id"]
            existing = reg["apps"].get(app_id)
            previous_version = existing["version"] if existing else None
            app_root = self.install_root / "apps" / app_id
            staging = app_root / ".staging" / manifest["version"]
            if staging.exists():
                shutil.rmtree(staging)
            staging.mkdir(parents=True, exist_ok=True)
            written = 0
            for entry in package_manifest["files"]:
                if written >= max(0, interrupt_after_files):
                    break
                dest = staging / entry["path"]
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(zf.read(f"payload/{entry['path']}"))
                written += 1
            marker = {
                "schema": "gunnchos.sdk.install_incomplete.v1",
                "app_id": app_id,
                "target_version": manifest["version"],
                "previous_version": previous_version,
                "files_written": written,
                "files_total": len(package_manifest["files"]),
                "status": "INCOMPLETE",
                "package_digest": package_manifest["package_digest"],
                "interrupted_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            }
            (app_root / "INCOMPLETE_INSTALL.json").write_text(
                json.dumps(marker, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
            # Registry must NOT claim installed success for the target version.
            if existing:
                existing["status"] = "installed"
                existing["update_pending_incomplete"] = True
                reg["apps"][app_id] = existing
            self._write_registry(reg)
            return {
                "ok": False,
                "interrupted": True,
                "half_installed_success": False,
                "app_id": app_id,
                "target_version": manifest["version"],
                "previous_version": previous_version,
                "files_written": written,
                "incomplete_marker": marker,
                "working_version_usable": previous_version is not None,
            }
        finally:
            zf.close()

    def detect_incomplete(self, app_id: str) -> dict[str, Any]:
        marker = self.install_root / "apps" / app_id / "INCOMPLETE_INSTALL.json"
        if not marker.exists():
            return {"ok": True, "incomplete": False, "app_id": app_id}
        data = json.loads(marker.read_text(encoding="utf-8"))
        return {"ok": True, "incomplete": True, "app_id": app_id, "marker": data}

    def rollback_app(self, app_id: str) -> dict[str, Any]:
        """Discard incomplete staging and keep/restore the prior installed version."""
        app_root = self.install_root / "apps" / app_id
        marker_path = app_root / "INCOMPLETE_INSTALL.json"
        staging = app_root / ".staging"
        reg = self._read_registry()
        entry = reg["apps"].get(app_id)
        if staging.exists():
            shutil.rmtree(staging)
        incomplete = None
        if marker_path.exists():
            incomplete = json.loads(marker_path.read_text(encoding="utf-8"))
            marker_path.unlink()
        if entry is None:
            return {
                "ok": False,
                "error": "not_installed",
                "app_id": app_id,
                "cleared_incomplete": incomplete is not None,
            }
        entry.pop("update_pending_incomplete", None)
        entry["status"] = "installed"
        prior = entry.get("previous_version") or entry.get("version")
        # Prefer previous_version tree if present after a failed update attempt.
        if incomplete and incomplete.get("previous_version"):
            prior = incomplete["previous_version"]
            prior_dir = app_root / prior
            if prior_dir.exists():
                entry["version"] = prior
                entry["installed_path"] = str(prior_dir.relative_to(self.install_root))
        # Remove any half-written target version dir that is not the active one.
        if incomplete and incomplete.get("target_version"):
            bad = app_root / incomplete["target_version"]
            if bad.exists() and incomplete["target_version"] != entry.get("version"):
                shutil.rmtree(bad)
        reg["apps"][app_id] = entry
        self._write_registry(reg)
        active_path = self.install_root / entry["installed_path"]
        digest = None
        if active_path.exists():
            h = hashlib.sha256()
            for f in sorted(active_path.rglob("*")):
                if f.is_file():
                    h.update(f.read_bytes())
            digest = h.hexdigest()
        return {
            "ok": True,
            "app_id": app_id,
            "restored_version": entry.get("version"),
            "cleared_incomplete": incomplete is not None,
            "active_tree_sha256": digest,
            "half_installed_success": False,
        }


    def update(self, package_path: Path, **kwargs: Any) -> dict[str, Any]:
        kwargs["force"] = True
        result = self.install(package_path, **kwargs)
        return result

    def uninstall(self, app_id: str, *, keep_logs: bool = False) -> dict[str, Any]:
        reg = self._read_registry()
        entry = reg["apps"].pop(app_id, None)
        if entry is None:
            return {"ok": False, "error": "not_installed", "app_id": app_id}
        app_root = self.install_root / "apps" / app_id
        if app_root.exists():
            if keep_logs:
                logs_dir = app_root / "sandbox" / "logs"
                preserved = None
                if logs_dir.exists():
                    preserved = self.install_root / "uninstalled_logs" / app_id
                    preserved.mkdir(parents=True, exist_ok=True)
                    for f in logs_dir.iterdir():
                        shutil.move(str(f), str(preserved / f.name))
            shutil.rmtree(app_root)
        self._write_registry(reg)
        return {"ok": True, "app_id": app_id, "removed_version": entry["version"]}
