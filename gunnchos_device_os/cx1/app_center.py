"""CX1C App Center — discover/install/launch/update/remove across lanes."""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from gunnchos_device_os.cx0.app_provider import discover_portal_capabilities


@dataclass
class AppRecord:
    app_id: str
    name: str
    lane: str
    version: str
    provenance: str
    permissions: List[str] = field(default_factory=list)
    installed: bool = False
    storage_path: str = ""
    offline_metadata: Dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "app_id": self.app_id,
            "name": self.name,
            "lane": self.lane,
            "version": self.version,
            "provenance": self.provenance,
            "permissions": list(self.permissions),
            "installed": self.installed,
            "storage_path": self.storage_path,
            "offline_metadata": dict(self.offline_metadata),
        }


@dataclass
class AppCenter:
    root: Path
    catalog: Dict[str, AppRecord] = field(default_factory=dict)
    installed: Dict[str, AppRecord] = field(default_factory=dict)
    flatpak_available: bool = False
    flatpak_binary: Optional[str] = None

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        for sub in ("catalog", "installed", "pwa", "cache", "permissions"):
            (self.root / sub).mkdir(parents=True, exist_ok=True)
        self.flatpak_binary = shutil.which("flatpak")
        self.flatpak_available = self.flatpak_binary is not None
        self._seed_catalog()
        self._load()

    def _seed_catalog(self) -> None:
        seeds = [
            AppRecord(
                app_id="org.gunnchos.cx1.testapp",
                name="CX1 Test App",
                lane="GUNNCH_NATIVE",
                version="1.0.0",
                provenance="local_test_repo",
                permissions=["files.read", "notifications"],
                offline_metadata={"summary": "Deterministic CI test application"},
            ),
            AppRecord(
                app_id="org.gunnchos.cx1.testapp.web",
                name="CX1 Test PWA",
                lane="WEB_PWA",
                version="1.0.0",
                provenance="local_pwa_manifest",
                permissions=["network", "storage"],
                offline_metadata={"start_url": "offline://cx1-test-pwa", "display": "standalone"},
            ),
            AppRecord(
                app_id="org.libreoffice.LibreOffice",
                name="LibreOffice",
                lane="LINUX_NATIVE",
                version="system",
                provenance="host_package_or_homebrew",
                permissions=["files.readwrite"],
                offline_metadata={"binary_candidates": ["soffice", "libreoffice"]},
            ),
        ]
        for app in seeds:
            self.catalog[app.app_id] = app
        # persist catalog cache for offline
        (self.root / "cache" / "catalog.json").write_text(
            json.dumps({k: v.to_dict() for k, v in self.catalog.items()}, indent=2) + "\n"
        )

    def _load(self) -> None:
        path = self.root / "installed" / "apps.json"
        if not path.exists():
            return
        data = json.loads(path.read_text())
        for raw in data.get("apps", []):
            rec = AppRecord(**{k: raw[k] for k in AppRecord.__dataclass_fields__ if k in raw})
            self.installed[rec.app_id] = rec

    def _save(self) -> None:
        path = self.root / "installed" / "apps.json"
        path.write_text(
            json.dumps({"apps": [a.to_dict() for a in self.installed.values()]}, indent=2) + "\n"
        )

    def discover(self, query: str = "") -> List[dict]:
        q = query.lower()
        out = []
        for app in self.catalog.values():
            if not q or q in app.name.lower() or q in app.app_id.lower():
                out.append(app.to_dict())
        return out

    def metadata(self, app_id: str) -> dict:
        app = self.catalog.get(app_id) or self.installed.get(app_id)
        if not app:
            raise KeyError(app_id)
        return app.to_dict()

    def install(self, app_id: str) -> dict:
        if app_id not in self.catalog:
            raise KeyError(app_id)
        app = self.catalog[app_id]
        if app.lane == "FLATPAK":
            return self._flatpak_install(app)
        storage = self.root / "installed" / app_id
        storage.mkdir(parents=True, exist_ok=True)
        marker = storage / "INSTALLED.json"
        record = AppRecord(
            app_id=app.app_id,
            name=app.name,
            lane=app.lane,
            version=app.version,
            provenance=app.provenance,
            permissions=list(app.permissions),
            installed=True,
            storage_path=str(storage),
            offline_metadata=dict(app.offline_metadata),
        )
        marker.write_text(json.dumps(record.to_dict(), indent=2) + "\n")
        if app.lane == "WEB_PWA":
            (self.root / "pwa" / f"{app_id}.json").write_text(
                json.dumps(
                    {
                        "app_id": app_id,
                        "isolation": "profile_scoped",
                        "offline_metadata": app.offline_metadata,
                        "installed_at": time.time(),
                    },
                    indent=2,
                )
                + "\n"
            )
        self.installed[app_id] = record
        self._save()
        (self.root / "permissions" / f"{app_id}.json").write_text(
            json.dumps({"app_id": app_id, "permissions": app.permissions, "state": "ask"}, indent=2)
            + "\n"
        )
        return {
            "installed": True,
            "app": record.to_dict(),
            "evidence_class": "DIGITAL_PASS",
        }

    def _flatpak_install(self, app: AppRecord) -> dict:
        if not self.flatpak_available:
            return {
                "installed": False,
                "app_id": app.app_id,
                "evidence_class": "DIGITAL_PARTIAL",
                "reason": "flatpak_absent_fail_closed",
            }
        assert self.flatpak_binary
        proc = subprocess.run(
            [self.flatpak_binary, "install", "-y", app.app_id],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        ok = proc.returncode == 0
        return {
            "installed": ok,
            "app_id": app.app_id,
            "stdout": (proc.stdout or "")[:500],
            "evidence_class": "DIGITAL_PASS" if ok else "DIGITAL_PARTIAL",
        }

    def flatpak_health(self) -> dict:
        if not self.flatpak_available:
            return {
                "available": False,
                "remotes": [],
                "evidence_class": "DIGITAL_PARTIAL",
                "claim_boundary": "flatpak_absent_fail_closed",
            }
        assert self.flatpak_binary
        remotes = subprocess.run(
            [self.flatpak_binary, "remotes"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        return {
            "available": True,
            "remotes": [ln.strip() for ln in (remotes.stdout or "").splitlines() if ln.strip()],
            "evidence_class": "DIGITAL_PASS",
        }

    def launch(self, app_id: str) -> dict:
        app = self.installed.get(app_id)
        if not app:
            raise RuntimeError(f"not_installed:{app_id}")
        if app.lane == "LINUX_NATIVE" and app.app_id.endswith("LibreOffice"):
            binary = shutil.which("soffice") or shutil.which("libreoffice")
            if not binary:
                return {
                    "launched": False,
                    "app_id": app_id,
                    "evidence_class": "DIGITAL_PARTIAL",
                    "reason": "libreoffice_binary_absent",
                }
            # dry launch --version is authentic probe without GUI requirement
            proc = subprocess.run([binary, "--version"], capture_output=True, text=True, timeout=30)
            return {
                "launched": proc.returncode == 0,
                "app_id": app_id,
                "mode": "version_probe",
                "version": (proc.stdout or "").strip()[:200],
                "evidence_class": "DIGITAL_PASS" if proc.returncode == 0 else "DIGITAL_PARTIAL",
            }
        launch_marker = Path(app.storage_path) / "LAST_LAUNCH.json"
        launch_marker.write_text(json.dumps({"launched_at": time.time(), "app_id": app_id}) + "\n")
        return {
            "launched": True,
            "app_id": app_id,
            "lane": app.lane,
            "evidence_class": "DIGITAL_PASS",
        }

    def update(self, app_id: str, new_version: str) -> dict:
        app = self.installed.get(app_id)
        if not app:
            raise RuntimeError(f"not_installed:{app_id}")
        previous = app.version
        rollback = Path(app.storage_path) / "ROLLBACK.json"
        rollback.write_text(json.dumps({"previous_version": previous, "app_id": app_id}) + "\n")
        app.version = new_version
        self.installed[app_id] = app
        self._save()
        return {
            "updated": True,
            "app_id": app_id,
            "from": previous,
            "to": new_version,
            "rollback_available": True,
            "evidence_class": "DIGITAL_PASS",
        }

    def rollback(self, app_id: str) -> dict:
        app = self.installed.get(app_id)
        if not app:
            raise RuntimeError(f"not_installed:{app_id}")
        rollback = Path(app.storage_path) / "ROLLBACK.json"
        if not rollback.exists():
            raise RuntimeError("no_rollback")
        data = json.loads(rollback.read_text())
        app.version = data["previous_version"]
        self.installed[app_id] = app
        self._save()
        return {"rolled_back": True, "app_id": app_id, "version": app.version}

    def uninstall(self, app_id: str) -> dict:
        app = self.installed.pop(app_id, None)
        if not app:
            raise RuntimeError(f"not_installed:{app_id}")
        storage = Path(app.storage_path)
        if storage.exists():
            shutil.rmtree(storage)
        pwa = self.root / "pwa" / f"{app_id}.json"
        if pwa.exists():
            pwa.unlink()
        perm = self.root / "permissions" / f"{app_id}.json"
        if perm.exists():
            perm.unlink()
        self._save()
        return {"uninstalled": True, "app_id": app_id, "evidence_class": "DIGITAL_PASS"}

    def permissions_view(self, app_id: str) -> dict:
        path = self.root / "permissions" / f"{app_id}.json"
        if not path.exists():
            return {"app_id": app_id, "permissions": [], "state": "absent"}
        return json.loads(path.read_text())

    def portal_inventory(self) -> dict:
        return discover_portal_capabilities().to_dict()
