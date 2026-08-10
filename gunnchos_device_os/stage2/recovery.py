"""Recovery environment: inspect, verify, select, repair, reinstall, factory reset."""
from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from gunnchos_device_os.stage2.crypto_dev import sha256_file, verify_signature
from gunnchos_device_os.stage2.filesystem import ensure_sysroot
from gunnchos_device_os.stage2.update_manager import UpdateManager


class RecoveryEnv:
    def __init__(self, sysroot: Path | str, image_dir: Path | str | None = None):
        self.layout = ensure_sysroot(sysroot)
        self.root = self.layout.root
        self.image_dir = Path(image_dir) if image_dir else None
        self.mgr = UpdateManager(self.root)

    def inspect_slots(self) -> dict[str, Any]:
        slots = {}
        for name, label in (("system-a", "A"), ("system-b", "B")):
            d = self.root / name
            ver = d / "IMAGE_VERSION"
            meta = d / "slot.json"
            slots[label] = {
                "path": name,
                "exists": d.is_dir(),
                "version": ver.read_text().strip() if ver.exists() else None,
                "meta": json.loads(meta.read_text()) if meta.exists() else None,
                "corrupt": (d / "CORRUPT").exists(),
            }
        meta = json.loads((self.root / "data" / "update_state.json").read_text())
        return {"slots": slots, "active": meta.get("active"), "pending": meta.get("pending")}

    def verify_slot(self, slot: str) -> dict[str, Any]:
        d = self.root / ("system-a" if slot == "A" else "system-b")
        health = d / "usr" / "lib" / "gunnchos" / "healthcheck"
        ok = (
            d.is_dir()
            and (d / "IMAGE_VERSION").exists()
            and health.exists()
            and health.read_text().strip() == "ok"
            and not (d / "CORRUPT").exists()
        )
        return {"slot": slot, "ok": ok}

    def select_prior_slot(self) -> dict[str, Any]:
        info = self.inspect_slots()
        active = info["active"]
        other = "B" if active == "A" else "A"
        # Prefer verified prior
        for candidate in (other, active):
            if self.verify_slot(candidate)["ok"]:
                meta_path = self.root / "data" / "update_state.json"
                meta = json.loads(meta_path.read_text())
                meta["active"] = candidate
                meta["pending"] = None
                meta_path.write_text(json.dumps(meta, indent=2) + "\n")
                return {"ok": True, "selected": candidate, "reason": "verified_prior"}
        return {"ok": False, "selected": None, "reason": "no_verified_slot"}

    def repair_metadata(self) -> dict[str, Any]:
        meta_path = self.root / "data" / "update_state.json"
        meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
        active = meta.get("active") or "A"
        if not self.verify_slot(active)["ok"]:
            sel = self.select_prior_slot()
            active = sel.get("selected") or "A"
        meta = {
            "active": active,
            "pending": None,
            "boot_count": int(meta.get("boot_count", 0)),
            "security_version": int(meta.get("security_version", 1)),
            "repaired_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        meta_path.parent.mkdir(parents=True, exist_ok=True)
        meta_path.write_text(json.dumps(meta, indent=2) + "\n")
        for slot in ("A", "B"):
            d = self.root / ("system-a" if slot == "A" else "system-b")
            slot_json = d / "slot.json"
            ver = (d / "IMAGE_VERSION").read_text().strip() if (d / "IMAGE_VERSION").exists() else None
            state = "good" if self.verify_slot(slot)["ok"] else ("failed" if ver else "empty")
            slot_json.write_text(
                json.dumps({"slot": slot, "version": ver, "state": state}, indent=2) + "\n"
            )
        return {"ok": True, "meta": meta}

    def reinstall_approved_image(self, manifest_path: Path) -> dict[str, Any]:
        manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
        if not verify_signature(manifest):
            return {"ok": False, "reason": "manifest_signature_invalid"}
        image_dir = Path(manifest_path).parent
        system_img = image_dir / manifest["system_image"]
        if not system_img.exists():
            return {"ok": False, "reason": "system_image_missing"}
        digest = sha256_file(system_img)
        if digest != manifest.get("system_sha256"):
            return {"ok": False, "reason": "hash_mismatch"}
        # Reinstall into inactive then promote — keep user data
        inactive = self.mgr.inactive_slot()
        target = self.root / ("system-a" if inactive == "A" else "system-b")
        if target.exists():
            shutil.rmtree(target)
        target.mkdir(parents=True)
        version = manifest["version"]
        (target / "IMAGE_VERSION").write_text(version + "\n")
        (target / "usr" / "lib" / "gunnchos").mkdir(parents=True)
        (target / "usr" / "lib" / "gunnchos" / "healthcheck").write_text("ok\n")
        (target / "REINSTALLED_FROM").write_text(manifest["system_sha256"] + "\n")
        meta = json.loads((self.root / "data" / "update_state.json").read_text())
        meta["pending"] = inactive
        meta["pending_version"] = version
        meta["pending_security_version"] = manifest.get("security_version", 1)
        (self.root / "data" / "update_state.json").write_text(json.dumps(meta, indent=2) + "\n")
        self.mgr.simulated_reboot()
        fin = self.mgr.finalize()
        return {"ok": fin.ok and fin.state == "marked_good", "finalize": fin.to_dict()}

    def factory_reset_user_data(self, *, confirm: bool = False) -> dict[str, Any]:
        if not confirm:
            return {
                "ok": False,
                "reason": "explicit_flag_required",
                "hint": "pass confirm=True / --factory-reset-user-data",
            }
        # Capture slot metadata before wiping mutable layers
        try:
            active = self.mgr.active_slot()
            meta = json.loads((self.root / "data" / "update_state.json").read_text())
            security_version = int(meta.get("security_version", 1))
        except Exception:
            active = "A"
            security_version = 1
        # Wipe mutable user layers only — keep system slots
        wiped = []
        for layer in ("home", "data", "apps", "games", "models", "dev-environments"):
            p = self.root / layer
            if p.exists():
                shutil.rmtree(p)
            p.mkdir(parents=True)
            (p / ".gunnchos_layout").write_text(f"layout={layer}\n")
            wiped.append(layer)
        # Restore update_state skeleton; preserve anti-rollback floor
        (self.root / "data" / "update_state.json").write_text(
            json.dumps(
                {
                    "active": active,
                    "pending": None,
                    "boot_count": 0,
                    "security_version": security_version,
                    "factory_reset_at": datetime.now(timezone.utc).strftime(
                        "%Y-%m-%dT%H:%M:%SZ"
                    ),
                },
                indent=2,
            )
            + "\n"
        )
        return {"ok": True, "wiped": wiped, "system_slots_preserved": True}

    def export_diagnostics(self, out_path: Path | str) -> dict[str, Any]:
        out = Path(out_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        report = {
            "schema": "gunnchos.stage2.recovery_diagnostics.v1",
            "exported_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "slots": self.inspect_slots(),
            "verify_a": self.verify_slot("A"),
            "verify_b": self.verify_slot("B"),
            "sysroot_rel": "artifacts/stage2/sysroot",
        }
        out.write_text(json.dumps(report, indent=2) + "\n")
        text = out.read_text()
        if "/Users/" in text:
            raise RuntimeError("host path leaked into diagnostics")
        return {"ok": True, "path": str(out.name), "report": report}
