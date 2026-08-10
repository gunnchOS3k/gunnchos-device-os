"""A/B atomic update manager with health check and rollback (file-backed)."""
from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from gunnchos_device_os.stage2.crypto_dev import sha256_bytes, sign_payload, verify_signature
from gunnchos_device_os.stage2.filesystem import ensure_sysroot


@dataclass
class UpdateResult:
    ok: bool
    state: str
    active_slot: str
    inactive_slot: str
    version: str | None = None
    rolled_back: bool = False
    user_data_intact: bool | None = None
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "state": self.state,
            "active_slot": self.active_slot,
            "inactive_slot": self.inactive_slot,
            "version": self.version,
            "rolled_back": self.rolled_back,
            "user_data_intact": self.user_data_intact,
            "detail": self.detail,
        }


class UpdateManager:
    """RAUC-style A/B updates on a writable sysroot."""

    def __init__(self, sysroot: Path | str):
        self.layout = ensure_sysroot(sysroot)
        self.root = self.layout.root
        self.meta_path = self.root / "data" / "update_state.json"
        self._ensure_baseline()

    def _ensure_baseline(self) -> None:
        a = self.root / "system-a"
        if not (a / "IMAGE_VERSION").exists():
            (a / "IMAGE_VERSION").write_text("0.1.0-baseline\n", encoding="utf-8")
            (a / "usr" / "lib" / "gunnchos").mkdir(parents=True, exist_ok=True)
            (a / "usr" / "lib" / "gunnchos" / "healthcheck").write_text(
                "ok\n", encoding="utf-8"
            )
            self._write_slot_meta("A", "0.1.0-baseline", "good")
        if not self.meta_path.exists():
            self._save_meta(
                {
                    "active": "A",
                    "pending": None,
                    "boot_count": 0,
                    "security_version": 1,
                }
            )
        home = self.root / "home" / "user"
        home.mkdir(parents=True, exist_ok=True)
        keep = home / "KEEPME.txt"
        if not keep.exists():
            keep.write_text("user-data-must-survive-rollback\n", encoding="utf-8")

    def _save_meta(self, meta: dict[str, Any]) -> None:
        self.meta_path.parent.mkdir(parents=True, exist_ok=True)
        self.meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")

    def _load_meta(self) -> dict[str, Any]:
        return json.loads(self.meta_path.read_text(encoding="utf-8"))

    def _write_slot_meta(self, slot: str, version: str, state: str) -> None:
        name = "system-a" if slot == "A" else "system-b"
        path = self.root / name / "slot.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"slot": slot, "version": version, "state": state}, indent=2)
            + "\n",
            encoding="utf-8",
        )

    def active_slot(self) -> str:
        return self._load_meta()["active"]

    def inactive_slot(self) -> str:
        return "B" if self.active_slot() == "A" else "A"

    def _slot_dir(self, slot: str) -> Path:
        return self.root / ("system-a" if slot == "A" else "system-b")

    def user_data_fingerprint(self) -> str:
        keep = self.root / "home" / "user" / "KEEPME.txt"
        data = self.root / "data" / "appstate.json"
        blob = b""
        if keep.exists():
            blob += keep.read_bytes()
        if data.exists():
            blob += data.read_bytes()
        return sha256_bytes(blob)

    def build_update_package(
        self,
        *,
        version: str,
        content: bytes | None = None,
        security_version: int = 2,
        corrupt: bool = False,
    ) -> dict[str, Any]:
        payload = content or f"gunnchos-stage2-image:{version}\n".encode()
        digest = sha256_bytes(payload)
        if corrupt:
            # Claim wrong digest so verify fails OR write bad health later
            digest_for_meta = digest  # hash still matches bytes; corruption via flag
        else:
            digest_for_meta = digest
        pkg = {
            "schema": "gunnchos.stage2.update_package.v1",
            "version": version,
            "security_version": security_version,
            "realm": "gunnchos-stage2-dev-signing-v1",
            "artifact_sha256": digest_for_meta,
            "payload_b64_len": len(payload),
            "corrupt": corrupt,
        }
        pkg["signature"] = sign_payload(pkg)
        # Store payload beside package for apply
        pkg["_payload"] = payload
        return pkg

    def apply_update(self, package: dict[str, Any]) -> UpdateResult:
        meta = self._load_meta()
        active = meta["active"]
        inactive = "B" if active == "A" else "A"

        if not verify_signature(package):
            return UpdateResult(
                ok=False,
                state="signature_rejected",
                active_slot=active,
                inactive_slot=inactive,
                detail={"reason": "invalid signature"},
            )

        # Anti-rollback
        if int(package.get("security_version", 0)) < int(meta.get("security_version", 1)):
            return UpdateResult(
                ok=False,
                state="anti_rollback_rejected",
                active_slot=active,
                inactive_slot=inactive,
                detail={
                    "package_sv": package.get("security_version"),
                    "device_sv": meta.get("security_version"),
                },
            )

        payload: bytes = package["_payload"]
        digest = sha256_bytes(payload)
        if digest != package.get("artifact_sha256"):
            return UpdateResult(
                ok=False,
                state="hash_mismatch",
                active_slot=active,
                inactive_slot=inactive,
            )

        # Write N+1 to inactive slot
        target = self._slot_dir(inactive)
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True)
        (target / "IMAGE_VERSION").write_text(package["version"] + "\n", encoding="utf-8")
        (target / "usr" / "lib" / "gunnchos").mkdir(parents=True)
        health = target / "usr" / "lib" / "gunnchos" / "healthcheck"
        if package.get("corrupt"):
            health.write_text("CORRUPT\n", encoding="utf-8")
            (target / "CORRUPT").write_text("1\n", encoding="utf-8")
        else:
            health.write_text("ok\n", encoding="utf-8")
        (target / "PAYLOAD.sha256").write_text(digest + "\n", encoding="utf-8")
        self._write_slot_meta(inactive, package["version"], "pending")

        meta["pending"] = inactive
        meta["pending_version"] = package["version"]
        meta["pending_security_version"] = package["security_version"]
        self._save_meta(meta)

        return UpdateResult(
            ok=True,
            state="pending_reboot",
            active_slot=active,
            inactive_slot=inactive,
            version=package["version"],
            detail={"written_to": inactive},
        )

    def simulated_reboot(self) -> UpdateResult:
        meta = self._load_meta()
        pending = meta.get("pending")
        if not pending:
            return UpdateResult(
                ok=True,
                state="no_pending",
                active_slot=meta["active"],
                inactive_slot=self.inactive_slot(),
            )
        # Boot into pending slot
        previous = meta["active"]
        meta["active"] = pending
        meta["boot_count"] = int(meta.get("boot_count", 0)) + 1
        meta["previous"] = previous
        self._save_meta(meta)
        return UpdateResult(
            ok=True,
            state="booted_pending",
            active_slot=pending,
            inactive_slot=previous,
            version=meta.get("pending_version"),
        )

    def health_check(self) -> dict[str, Any]:
        slot = self.active_slot()
        health = self._slot_dir(slot) / "usr" / "lib" / "gunnchos" / "healthcheck"
        corrupt = (self._slot_dir(slot) / "CORRUPT").exists()
        ok = health.exists() and health.read_text(encoding="utf-8").strip() == "ok" and not corrupt
        return {"ok": ok, "slot": slot, "path": str(health.relative_to(self.root))}

    def finalize(self) -> UpdateResult:
        """Mark good or rollback based on health check. Preserves user data."""
        before = self.user_data_fingerprint()
        meta = self._load_meta()
        active = meta["active"]
        previous = meta.get("previous") or ("B" if active == "A" else "A")
        health = self.health_check()

        if health["ok"]:
            self._write_slot_meta(active, meta.get("pending_version") or "unknown", "good")
            meta["pending"] = None
            meta["security_version"] = int(
                meta.get("pending_security_version") or meta.get("security_version", 1)
            )
            meta.pop("pending_version", None)
            meta.pop("pending_security_version", None)
            meta.pop("previous", None)
            self._save_meta(meta)
            after = self.user_data_fingerprint()
            return UpdateResult(
                ok=True,
                state="marked_good",
                active_slot=active,
                inactive_slot=previous,
                version=self._slot_dir(active).joinpath("IMAGE_VERSION").read_text().strip(),
                rolled_back=False,
                user_data_intact=(before == after),
            )

        # Rollback to previous slot
        self._write_slot_meta(active, meta.get("pending_version") or "bad", "failed")
        meta["active"] = previous
        meta["pending"] = None
        meta.pop("pending_version", None)
        meta.pop("pending_security_version", None)
        meta.pop("previous", None)
        self._save_meta(meta)
        self._write_slot_meta(previous, self._read_version(previous), "good")
        after = self.user_data_fingerprint()
        return UpdateResult(
            ok=True,
            state="rolled_back",
            active_slot=previous,
            inactive_slot=active,
            version=self._read_version(previous),
            rolled_back=True,
            user_data_intact=(before == after and after != ""),
            detail={"failed_slot": active, "health": health},
        )

    def _read_version(self, slot: str) -> str:
        p = self._slot_dir(slot) / "IMAGE_VERSION"
        return p.read_text(encoding="utf-8").strip() if p.exists() else "unknown"

    def run_success_path(self, version: str = "0.2.0-stage2") -> dict[str, Any]:
        pkg = self.build_update_package(version=version, security_version=2)
        r1 = self.apply_update(pkg)
        r2 = self.simulated_reboot()
        r3 = self.finalize()
        return {
            "path": "success",
            "apply": r1.to_dict(),
            "reboot": r2.to_dict(),
            "finalize": r3.to_dict(),
            "ok": r1.ok and r3.ok and r3.state == "marked_good" and r3.user_data_intact,
        }

    def run_failure_rollback_path(self, version: str = "0.2.1-bad") -> dict[str, Any]:
        before = self.user_data_fingerprint()
        active_before = self.active_slot()
        pkg = self.build_update_package(version=version, security_version=2, corrupt=True)
        r1 = self.apply_update(pkg)
        r2 = self.simulated_reboot()
        r3 = self.finalize()
        after = self.user_data_fingerprint()
        return {
            "path": "failure_rollback",
            "apply": r1.to_dict(),
            "reboot": r2.to_dict(),
            "finalize": r3.to_dict(),
            "user_data_before": before,
            "user_data_after": after,
            "ok": (
                r1.ok
                and r3.rolled_back
                and r3.active_slot == active_before
                and before == after
                and r3.user_data_intact
            ),
        }
