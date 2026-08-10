"""Package management + app distribution — DEV/beta/stable, sign, install/update/rollback/revoke."""
from __future__ import annotations

import hashlib
import hmac
import json
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

CHANNELS = ("dev", "beta", "stable")


def _dev_key() -> bytes:
    return hashlib.sha256(b"gunnchos-phase-xiv-dev-signing-v1").digest()


@dataclass
class PackageArtifact:
    app_id: str
    version: str
    channel: str
    payload_sha256: str
    signature: str
    revoked: bool = False


class PackageManager:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.store = self.root / "store"
        self.store.mkdir(exist_ok=True)
        self.installed: dict[str, dict[str, Any]] = {}
        self.history: list[dict[str, Any]] = []
        self.revocations: set[str] = set()
        self._load()

    def _load(self) -> None:
        state = self.root / "state.json"
        if state.exists():
            data = json.loads(state.read_text())
            self.installed = data.get("installed", {})
            self.revocations = set(data.get("revocations", []))
            self.history = data.get("history", [])

    def _save(self) -> None:
        (self.root / "state.json").write_text(
            json.dumps(
                {
                    "installed": self.installed,
                    "revocations": sorted(self.revocations),
                    "history": self.history[-100:],
                },
                indent=2,
            )
            + "\n"
        )

    def sign_payload(self, app_id: str, version: str, channel: str, payload: bytes) -> PackageArtifact:
        if channel not in CHANNELS:
            raise ValueError(channel)
        digest = hashlib.sha256(payload).hexdigest()
        msg = f"{app_id}:{version}:{channel}:{digest}".encode()
        sig = hmac.new(_dev_key(), msg, hashlib.sha256).hexdigest()
        return PackageArtifact(app_id, version, channel, digest, sig)

    def verify(self, art: PackageArtifact, payload: bytes) -> bool:
        if art.app_id in self.revocations or art.revoked:
            return False
        digest = hashlib.sha256(payload).hexdigest()
        if digest != art.payload_sha256:
            return False
        msg = f"{art.app_id}:{art.version}:{art.channel}:{digest}".encode()
        expected = hmac.new(_dev_key(), msg, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, art.signature)

    def publish(self, art: PackageArtifact, payload: bytes) -> Path:
        if not self.verify(art, payload):
            raise PermissionError("bad_signature")
        dest = self.store / art.channel / art.app_id / art.version
        dest.mkdir(parents=True, exist_ok=True)
        (dest / "payload.bin").write_bytes(payload)
        (dest / "META.json").write_text(
            json.dumps(art.__dict__, indent=2) + "\n", encoding="utf-8"
        )
        return dest

    def install(self, app_id: str, version: str, channel: str = "stable") -> dict[str, Any]:
        meta_path = self.store / channel / app_id / version / "META.json"
        payload_path = self.store / channel / app_id / version / "payload.bin"
        if not meta_path.exists():
            raise FileNotFoundError(meta_path)
        meta = json.loads(meta_path.read_text())
        art = PackageArtifact(**meta)
        payload = payload_path.read_bytes()
        if not self.verify(art, payload):
            raise PermissionError("verify_failed")
        prev = self.installed.get(app_id)
        install_dir = self.root / "apps" / app_id
        if install_dir.exists():
            shutil.rmtree(install_dir)
        install_dir.mkdir(parents=True)
        (install_dir / "payload.bin").write_bytes(payload)
        (install_dir / "INSTALLED.json").write_text(
            json.dumps({"app_id": app_id, "version": version, "channel": channel, "prev": prev}, indent=2)
            + "\n"
        )
        self.installed[app_id] = {"version": version, "channel": channel, "prev": prev}
        self.history.append({"op": "install", "app_id": app_id, "version": version, "at": time.time()})
        self._save()
        return {"ok": True, "app_id": app_id, "version": version, "channel": channel}

    def update(self, app_id: str, version: str, channel: str = "stable") -> dict[str, Any]:
        if app_id not in self.installed:
            return self.install(app_id, version, channel)
        return self.install(app_id, version, channel)

    def rollback(self, app_id: str) -> dict[str, Any]:
        cur = self.installed.get(app_id)
        if not cur or not cur.get("prev"):
            return {"ok": False, "error": "no_previous"}
        prev = cur["prev"]
        result = self.install(app_id, prev["version"], prev["channel"])
        self.history.append({"op": "rollback", "app_id": app_id, "to": prev, "at": time.time()})
        self._save()
        return {"ok": True, "rolled_back_to": prev, "install": result}

    def revoke(self, app_id: str) -> dict[str, Any]:
        self.revocations.add(app_id)
        install_dir = self.root / "apps" / app_id
        if install_dir.exists():
            shutil.rmtree(install_dir)
        self.installed.pop(app_id, None)
        self.history.append({"op": "revoke", "app_id": app_id, "at": time.time()})
        self._save()
        return {"ok": True, "revoked": app_id}

    def e2e(self) -> dict[str, Any]:
        # Fresh channel for deterministic digital proof (ignore prior revoke state)
        self.revocations.clear()
        self.installed.clear()
        self.history.clear()
        self._save()
        results = {}
        for channel, ver in (("dev", "0.1.0-dev"), ("beta", "0.1.0-beta"), ("stable", "1.0.0")):
            payload = f"demo-app-{channel}-{ver}".encode()
            art = self.sign_payload("demo.app", ver, channel, payload)
            self.publish(art, payload)
            results[channel] = self.install("demo.app", ver, channel)
        # update stable then rollback
        payload2 = b"demo-app-stable-1.0.1"
        art2 = self.sign_payload("demo.app", "1.0.1", "stable", payload2)
        self.publish(art2, payload2)
        upd = self.update("demo.app", "1.0.1", "stable")
        rb = self.rollback("demo.app")
        rev = self.revoke("demo.app")
        # revoked install must fail
        denied = False
        try:
            self.install("demo.app", "1.0.0", "stable")
        except PermissionError:
            denied = True
        ok = (
            all(results[c]["ok"] for c in CHANNELS)
            and upd["ok"]
            and rb["ok"]
            and rev["ok"]
            and denied
        )
        return {
            "ok": ok,
            "channels": results,
            "update": upd,
            "rollback": rb,
            "revoke": rev,
            "revoked_install_denied": denied,
        }
