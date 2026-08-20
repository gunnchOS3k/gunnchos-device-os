"""Persistent signed package lifecycle — inspect, verify, install, upgrade, uninstall."""
from __future__ import annotations

import json
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from gunnchos_device_os.platform.secure_packaging import (
    build_signed_app_package,
    verify_signed_manifest,
)

SCHEMA_VERSION = 1
CLAIM_BOUNDARY = (
    "DEV Ed25519 trust root (WP-013 dev_keys). Persistent install registry only; "
    "not production signing or app-store notarization."
)


def _safe_component(value: str) -> str:
    if not value or value in {".", ".."} or "/" in value or "\\" in value or ".." in value:
        raise ValueError("unsafe_package_path_component")
    if value.startswith(".") or "\x00" in value:
        raise ValueError("unsafe_package_path_component")
    return value


@dataclass
class PackageLifecycleManager:
    root: Path
    repo_root: Path
    registry_path: Path = field(init=False)
    installs_dir: Path = field(init=False)
    registry: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        self.repo_root = Path(self.repo_root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.registry_path = self.root / "registry.json"
        self.installs_dir = self.root / "installed"
        self.installs_dir.mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self) -> None:
        if self.registry_path.exists():
            self.registry = json.loads(self.registry_path.read_text(encoding="utf-8"))
        else:
            self.registry = {
                "schema_version": SCHEMA_VERSION,
                "packages": {},
                "history": [],
            }

    def _persist(self) -> None:
        self.registry_path.write_text(json.dumps(self.registry, indent=2) + "\n", encoding="utf-8")

    def inspect(self) -> dict[str, Any]:
        return {
            "ok": True,
            "schema_version": self.registry.get("schema_version"),
            "installed_count": len(self.registry.get("packages", {})),
            "registry_path": str(self.registry_path),
            "claim_boundary": CLAIM_BOUNDARY,
        }

    def verify(self, signed: dict[str, Any]) -> bool:
        return verify_signed_manifest(self.repo_root, signed)

    def _record(self, op: str, app_id: str, **extra: Any) -> None:
        self.registry.setdefault("history", []).append(
            {"op": op, "app_id": app_id, "at_ms": int(time.time() * 1000), **extra}
        )
        self.registry["history"] = self.registry["history"][-200:]
        self._persist()

    def install(
        self,
        app_id: str,
        *,
        app_class: str = "first_party",
        version: str = "1.0.0",
    ) -> dict[str, Any]:
        app_id = _safe_component(app_id)
        pkg = build_signed_app_package(self.repo_root)
        signed = pkg.get("signed_apps") or {}
        if not pkg.get("ok") or not self.verify(signed):
            return {"ok": False, "error": "signature_verify_failed", "app_id": app_id}
        install_dir = self.installs_dir / app_id
        if install_dir.exists():
            shutil.rmtree(install_dir)
        install_dir.mkdir(parents=True)
        manifest_path = install_dir / "signed_manifest.json"
        manifest_path.write_text(json.dumps(signed, indent=2) + "\n", encoding="utf-8")
        record = {
            "app_id": app_id,
            "app_class": app_class,
            "version": version,
            "installed_at_ms": int(time.time() * 1000),
            "signature_valid": True,
            "trust_root": "local_dev",
            "manifest_path": str(manifest_path),
        }
        self.registry.setdefault("packages", {})[app_id] = record
        self._record("install", app_id, version=version)
        return {"ok": True, **record}

    def list_installed(self) -> dict[str, Any]:
        return {"ok": True, "packages": dict(self.registry.get("packages", {}))}

    def get(self, app_id: str) -> dict[str, Any]:
        app_id = _safe_component(app_id)
        rec = self.registry.get("packages", {}).get(app_id)
        if rec is None:
            return {"ok": False, "error": "not_installed", "app_id": app_id}
        manifest_path = Path(rec["manifest_path"])
        if not manifest_path.exists():
            return {"ok": False, "error": "manifest_missing", "app_id": app_id}
        signed = json.loads(manifest_path.read_text(encoding="utf-8"))
        valid = self.verify(signed)
        return {"ok": valid, "app_id": app_id, "record": rec, "signature_valid": valid}

    def upgrade(self, app_id: str, *, version: str = "1.0.1") -> dict[str, Any]:
        app_id = _safe_component(app_id)
        prev = self.registry.get("packages", {}).get(app_id)
        if not prev:
            return {"ok": False, "error": "not_installed", "app_id": app_id}
        result = self.install(app_id, app_class=prev.get("app_class", "first_party"), version=version)
        if result.get("ok"):
            result["previous_version"] = prev.get("version")
            self._record("upgrade", app_id, from_version=prev.get("version"), to_version=version)
        return result

    def uninstall(self, app_id: str) -> dict[str, Any]:
        app_id = _safe_component(app_id)
        rec = self.registry.get("packages", {}).pop(app_id, None)
        install_dir = self.installs_dir / app_id
        if install_dir.exists():
            shutil.rmtree(install_dir)
        if rec is None:
            return {"ok": False, "error": "not_installed", "app_id": app_id}
        self._record("uninstall", app_id)
        return {"ok": True, "app_id": app_id, "removed": rec}

    @classmethod
    def from_storage(cls, root: Path, repo_root: Path) -> "PackageLifecycleManager":
        """Fresh-process reload for restart persistence tests."""
        return cls(root=root, repo_root=repo_root)
