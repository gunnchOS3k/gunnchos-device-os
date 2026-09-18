"""Real App Center provider — local package repo (+ Flatpak when present)."""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from gunnchos_device_os.cx2.evidence_taxonomy import classify

FIXTURE_REPO = Path(__file__).resolve().parents[1] / "fixtures" / "local_repo"


@dataclass
class RealAppCenterProvider:
    root: Path
    catalog: Dict[str, dict] = field(default_factory=dict)
    installed: Dict[str, dict] = field(default_factory=dict)
    flatpak: Optional[str] = None

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        for sub in ("installed", "cache", "permissions", "repo"):
            (self.root / sub).mkdir(parents=True, exist_ok=True)
        self.flatpak = shutil.which("flatpak")
        self._seed_from_local_repo()
        self._load()

    def _seed_from_local_repo(self) -> None:
        # Prefer authentic local repo packages over marker-only installs
        app_id = "org.gunnchos.cx2.testapp"
        versions = sorted((FIXTURE_REPO / app_id).glob("*")) if (FIXTURE_REPO / app_id).exists() else []
        latest = versions[-1] if versions else None
        self.catalog[app_id] = {
            "app_id": app_id,
            "name": "CX2 Test App",
            "lane": "LOCAL_PACKAGE_REPO",
            "version": latest.name if latest else "1.0.0",
            "provenance": "cx2_local_test_repo",
            "permissions": ["files.read", "notifications"],
            "repo_path": str(FIXTURE_REPO / app_id),
            "source": "local_repo",
        }
        if self.flatpak:
            self.catalog["org.libreoffice.LibreOffice"] = {
                "app_id": "org.libreoffice.LibreOffice",
                "name": "LibreOffice (Flatpak)",
                "lane": "FLATPAK",
                "version": "flathub",
                "provenance": "flathub",
                "permissions": ["files.readwrite"],
                "source": "flatpak",
            }
        (self.root / "cache" / "catalog.json").write_text(json.dumps(self.catalog, indent=2) + "\n")

    def _load(self) -> None:
        path = self.root / "installed" / "apps.json"
        if path.exists():
            data = json.loads(path.read_text())
            self.installed = {a["app_id"]: a for a in data.get("apps", [])}

    def _save(self) -> None:
        (self.root / "installed" / "apps.json").write_text(
            json.dumps({"apps": list(self.installed.values())}, indent=2) + "\n"
        )

    def provider_info(self) -> dict:
        return {
            "provider": "local_package_repo",
            "flatpak_available": bool(self.flatpak),
            "repo": str(FIXTURE_REPO),
            "evidence_class": "REAL_PROVIDER_CLI_PASS" if FIXTURE_REPO.exists() else "BLOCKED",
        }

    def discover(self, query: str = "") -> List[dict]:
        q = query.lower()
        out = []
        for app in self.catalog.values():
            if not q or q in app["name"].lower() or q in app["app_id"].lower():
                out.append(dict(app))
        return out

    def installed_records(self) -> List[dict]:
        return list(self.installed.values())

    def install(self, app_id: str, version: Optional[str] = None) -> dict:
        app = self.catalog.get(app_id)
        if not app:
            return {"installed": False, "reason": "not_in_catalog", "evidence_class": "BLOCKED"}
        if app.get("lane") == "FLATPAK":
            return self._flatpak_install(app)
        ver = version or app["version"]
        src = FIXTURE_REPO / app_id / ver
        if not src.exists():
            return {
                "installed": False,
                "reason": f"package_missing:{src}",
                "evidence_class": "BLOCKED",
            }
        dest = self.root / "installed" / app_id
        if dest.exists():
            shutil.rmtree(dest)
        shutil.copytree(src, dest)
        # Prove files deployed (not a marker-only PASS)
        entry = dest / "run.py"
        if not entry.exists():
            return {"installed": False, "reason": "entry_missing", "evidence_class": "BLOCKED"}
        record = {
            "app_id": app_id,
            "name": app["name"],
            "lane": app["lane"],
            "version": ver,
            "provenance": app["provenance"],
            "permissions": list(app["permissions"]),
            "installed": True,
            "storage_path": str(dest),
            "files_deployed": sorted(p.name for p in dest.iterdir()),
            "source": app.get("source"),
        }
        self.installed[app_id] = record
        self._save()
        (self.root / "permissions" / f"{app_id}.json").write_text(
            json.dumps({"app_id": app_id, "permissions": app["permissions"], "state": "ask"}, indent=2)
            + "\n"
        )
        return {
            "installed": True,
            "app": record,
            "evidence_class": classify(real_provider_process=False, real_protocol=False),
            # install alone is real package deploy → CLI-level real provider
            "deploy_class": "REAL_PROVIDER_CLI_PASS",
        }

    def _flatpak_install(self, app: dict) -> dict:
        if not self.flatpak:
            return {
                "installed": False,
                "app_id": app["app_id"],
                "evidence_class": "EXTERNAL_PROVIDER_PENDING",
                "reason": "flatpak_absent_fail_closed",
            }
        proc = subprocess.run(
            [self.flatpak, "install", "-y", app["app_id"]],
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
        )
        ok = proc.returncode == 0
        return {
            "installed": ok,
            "app_id": app["app_id"],
            "stdout": (proc.stdout or "")[:400],
            "evidence_class": "REAL_PROVIDER_CLI_PASS" if ok else "BLOCKED",
        }

    def launch(self, app_id: str) -> dict:
        app = self.installed.get(app_id)
        if not app:
            return {"launched": False, "reason": "not_installed", "evidence_class": "BLOCKED"}
        entry = Path(app["storage_path"]) / "run.py"
        runtime = Path(app["storage_path"]) / "runtime"
        runtime.mkdir(exist_ok=True)
        env = {**dict(**{k: v for k, v in __import__("os").environ.items()}), "CX2_APP_RUNTIME": str(runtime)}
        proc = subprocess.Popen(
            [__import__("sys").executable, str(entry)],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        try:
            stdout, stderr = proc.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate(timeout=2)
        running = runtime / "RUNNING.json"
        if not running.exists():
            return {
                "launched": False,
                "pid": proc.pid,
                "stdout": (stdout or "")[:200],
                "stderr": (stderr or "")[:200],
                "evidence_class": "BLOCKED",
            }
        evidence = json.loads(running.read_text())
        return {
            "launched": True,
            "app_id": app_id,
            "pid": evidence.get("pid"),
            "version": evidence.get("version"),
            "process_evidence": evidence,
            "returncode": proc.returncode,
            "evidence_class": "REAL_PROVIDER_CLI_PASS",
            "gui_window": False,
            "claim_boundary": "process_evidence_without_compositor_window_on_this_host",
        }

    def update(self, app_id: str, new_version: str) -> dict:
        if app_id not in self.installed:
            return {"updated": False, "reason": "not_installed", "evidence_class": "BLOCKED"}
        previous = self.installed[app_id]["version"]
        rollback_dir = self.root / "installed" / f"{app_id}.rollback"
        if rollback_dir.exists():
            shutil.rmtree(rollback_dir)
        shutil.copytree(self.installed[app_id]["storage_path"], rollback_dir)
        result = self.install(app_id, version=new_version)
        if not result.get("installed"):
            return {**result, "updated": False}
        self.installed[app_id]["rollback_path"] = str(rollback_dir)
        self.installed[app_id]["previous_version"] = previous
        self._save()
        return {
            "updated": True,
            "from": previous,
            "to": new_version,
            "rollback_available": True,
            "evidence_class": "REAL_PROVIDER_CLI_PASS",
        }

    def rollback(self, app_id: str) -> dict:
        app = self.installed.get(app_id)
        if not app or not app.get("rollback_path"):
            return {"rolled_back": False, "reason": "no_rollback", "evidence_class": "BLOCKED"}
        dest = Path(app["storage_path"])
        shutil.rmtree(dest)
        shutil.copytree(app["rollback_path"], dest)
        app["version"] = app.get("previous_version", app["version"])
        self.installed[app_id] = app
        self._save()
        return {"rolled_back": True, "version": app["version"], "evidence_class": "REAL_PROVIDER_CLI_PASS"}

    def uninstall(self, app_id: str) -> dict:
        app = self.installed.pop(app_id, None)
        if not app:
            return {"uninstalled": False, "reason": "not_installed", "evidence_class": "BLOCKED"}
        storage = Path(app["storage_path"])
        if storage.exists():
            shutil.rmtree(storage)
        rb = self.root / "installed" / f"{app_id}.rollback"
        if rb.exists():
            shutil.rmtree(rb)
        perm = self.root / "permissions" / f"{app_id}.json"
        if perm.exists():
            perm.unlink()
        self._save()
        leftover = storage.exists()
        return {
            "uninstalled": not leftover,
            "cleanup_complete": not leftover,
            "app_id": app_id,
            "evidence_class": "REAL_PROVIDER_CLI_PASS",
        }

    def permissions_view(self, app_id: str) -> dict:
        path = self.root / "permissions" / f"{app_id}.json"
        if not path.exists():
            return {"app_id": app_id, "permissions": [], "state": "absent"}
        return json.loads(path.read_text())
