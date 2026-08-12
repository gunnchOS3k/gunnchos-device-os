"""A/B update slots, signed update metadata, rollback, anti-rollback,
interrupted-update recovery, factory reset, recovery mode, and the
lost/revoked device path.

All state is a plain JSON file so tests can run fully virtually (tmp_path)
with no real disk partitions. Signing reuses the WP-013 DEV Ed25519 keypair
(``dev_keys``) — never production keys.
"""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any

from gunnchos_device_os.release_engineering import dev_keys

STATE_SCHEMA = "gunnchos.ab_update.device_state.v1"
UPDATE_METADATA_SCHEMA = "gunnchos.ab_update.metadata.v1"
SLOTS = ("A", "B")
MAX_BOOT_ATTEMPTS = 3


class ABUpdateError(RuntimeError):
    pass


def build_update_metadata(
    repo_root: Path,
    *,
    realm_id: str,
    from_version: str,
    to_version: str,
    image_hash: str,
    anti_rollback_counter: int,
) -> dict[str, Any]:
    """Build and sign an update-metadata payload with the DEV trust root."""
    metadata = {
        "schema": UPDATE_METADATA_SCHEMA,
        "realm_id": realm_id,
        "from_version": from_version,
        "to_version": to_version,
        "image_hash": image_hash,
        "anti_rollback_counter": anti_rollback_counter,
        "issued_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "signing_key_fingerprint": dev_keys.dev_public_key_fingerprint(repo_root),
    }
    payload = json.dumps(metadata, sort_keys=True).encode("utf-8")
    metadata["signature_hex"] = dev_keys.sign_bytes(repo_root, payload)
    return metadata


def _verify_update_metadata(repo_root: Path, metadata: dict[str, Any]) -> bool:
    unsigned = {k: v for k, v in metadata.items() if k != "signature_hex"}
    payload = json.dumps(unsigned, sort_keys=True).encode("utf-8")
    return dev_keys.verify_bytes(repo_root, payload, metadata.get("signature_hex", ""))


def _empty_slot() -> dict[str, Any]:
    return {
        "version": None,
        "image_hash": None,
        "status": "empty",
        "boot_attempts": 0,
        "anti_rollback_counter": 0,
        "in_progress": False,
    }


class ABUpdateManager:
    """Manages one virtual device's A/B slot state on top of a JSON file."""

    def __init__(self, repo_root: Path, state_path: Path) -> None:
        self.repo_root = Path(repo_root)
        self.state_path = Path(state_path)

    # -- persistence ----------------------------------------------------
    def _read(self) -> dict[str, Any]:
        if not self.state_path.exists():
            raise ABUpdateError("device_not_initialized")
        return json.loads(self.state_path.read_text(encoding="utf-8"))

    def _write(self, state: dict[str, Any]) -> dict[str, Any]:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return state

    # -- lifecycle --------------------------------------------------------
    def init_device(self, device_id: str | None = None, *, initial_version: str = "1.0.0") -> dict[str, Any]:
        state = {
            "schema": STATE_SCHEMA,
            "device_id": device_id or f"dev-ab-{uuid.uuid4().hex[:12]}",
            "active_slot": "A",
            "slots": {"A": {**_empty_slot(), "version": initial_version, "status": "active"}, "B": _empty_slot()},
            "anti_rollback_floor": 0,
            "revoked_key_fingerprints": [],
            "device_lost": False,
            "remote_wipe_requested": False,
            "recovery_mode": False,
            "user_data": {"apps": ["seed-app"], "settings": {"locale": "en-US"}, "accounts": ["dev-owner"]},
            "history": [{"event": "init", "slot": "A", "version": initial_version, "ts": time.time()}],
        }
        return self._write(state)

    def status(self) -> dict[str, Any]:
        return self._read()

    # -- staging / applying updates --------------------------------------
    def stage_update(self, metadata: dict[str, Any], *, simulate_crash_before_commit: bool = False) -> dict[str, Any]:
        state = self._read()
        if state.get("device_lost"):
            return {"ok": False, "error": "device_marked_lost_updates_refused"}

        fingerprint = metadata.get("signing_key_fingerprint")
        if fingerprint in (state.get("revoked_key_fingerprints") or []):
            return {"ok": False, "error": "signing_key_revoked"}

        if not _verify_update_metadata(self.repo_root, metadata):
            return {"ok": False, "error": "signature_verification_failed"}

        counter = metadata.get("anti_rollback_counter", -1)
        if counter < state.get("anti_rollback_floor", 0):
            return {
                "ok": False,
                "error": "anti_rollback_violation",
                "attempted_counter": counter,
                "floor": state["anti_rollback_floor"],
            }

        active = state["active_slot"]
        target = "B" if active == "A" else "A"

        # Staging is written first with in_progress=True (models the write
        # phase). A crash simulated here leaves in_progress=True forever,
        # which `recover_from_interrupted_update` detects on next boot.
        state["slots"][target] = {
            "version": metadata["to_version"],
            "image_hash": metadata["image_hash"],
            "status": "staged",
            "boot_attempts": 0,
            "anti_rollback_counter": counter,
            "in_progress": True,
        }
        state["history"].append(
            {"event": "stage_update", "slot": target, "to_version": metadata["to_version"], "ts": time.time()}
        )
        self._write(state)

        if simulate_crash_before_commit:
            return {"ok": False, "error": "simulated_crash_during_apply", "target_slot": target, "interrupted": True}

        # Finalize the staged write (models "fsync + mark complete").
        state["slots"][target]["in_progress"] = False
        state["slots"][target]["status"] = "staged_complete"
        self._write(state)
        return {"ok": True, "target_slot": target, "status": "staged_complete"}

    def recover_from_interrupted_update(self) -> dict[str, Any]:
        """Detect and clean up a slot left `in_progress` by a crash."""
        state = self._read()
        recovered: list[str] = []
        for slot_id, slot in state["slots"].items():
            if slot.get("in_progress"):
                slot["status"] = "corrupt_recovered"
                slot["in_progress"] = False
                slot["version"] = None
                slot["image_hash"] = None
                recovered.append(slot_id)
        if recovered:
            state["history"].append({"event": "interrupted_update_recovered", "slots": recovered, "ts": time.time()})
            self._write(state)
        return {"ok": True, "recovered_slots": recovered, "active_slot": state["active_slot"]}

    def commit_boot(self, slot: str, *, boot_succeeds: bool) -> dict[str, Any]:
        """Simulate first boot of a staged (or currently active) slot."""
        state = self._read()
        if slot not in state["slots"]:
            raise ABUpdateError(f"unknown_slot:{slot}")
        entry = state["slots"][slot]
        if entry.get("in_progress"):
            return {"ok": False, "error": "slot_incomplete_run_recovery_first"}
        entry["boot_attempts"] = entry.get("boot_attempts", 0) + 1

        if boot_succeeds:
            for other_id, other in state["slots"].items():
                if other_id != slot and other.get("status") == "active":
                    other["status"] = "previous"
            entry["status"] = "active"
            state["active_slot"] = slot
            state["anti_rollback_floor"] = max(state["anti_rollback_floor"], entry.get("anti_rollback_counter", 0))
            state["history"].append({"event": "boot_success", "slot": slot, "ts": time.time()})
            self._write(state)
            return {"ok": True, "active_slot": slot, "boot_attempts": entry["boot_attempts"]}

        entry["status"] = "unbootable" if entry["boot_attempts"] >= MAX_BOOT_ATTEMPTS else "boot_failed_retrying"
        auto_rollback_triggered = False
        if entry["boot_attempts"] >= MAX_BOOT_ATTEMPTS:
            other_id = "B" if slot == "A" else "A"
            other = state["slots"][other_id]
            if other.get("status") in ("active", "previous") and other.get("version"):
                other["status"] = "active"
                state["active_slot"] = other_id
                auto_rollback_triggered = True
                state["history"].append(
                    {"event": "auto_rollback", "from_slot": slot, "to_slot": other_id, "ts": time.time()}
                )
            else:
                state["recovery_mode"] = True
                state["history"].append({"event": "enter_recovery_mode", "reason": "both_slots_unbootable", "ts": time.time()})
        self._write(state)
        return {
            "ok": auto_rollback_triggered,
            "slot": slot,
            "status": entry["status"],
            "boot_attempts": entry["boot_attempts"],
            "auto_rollback_triggered": auto_rollback_triggered,
            "recovery_mode": state["recovery_mode"],
        }

    def manual_rollback(self) -> dict[str, Any]:
        state = self._read()
        active = state["active_slot"]
        other_id = "B" if active == "A" else "A"
        other = state["slots"][other_id]
        if not other.get("version") or other.get("status") == "corrupt_recovered":
            return {"ok": False, "error": "no_bootable_previous_slot"}
        state["slots"][active]["status"] = "previous"
        other["status"] = "active"
        state["active_slot"] = other_id
        state["history"].append({"event": "manual_rollback", "from_slot": active, "to_slot": other_id, "ts": time.time()})
        self._write(state)
        return {"ok": True, "active_slot": other_id}

    # -- factory reset / user data ----------------------------------------
    def factory_reset(self, *, preserve_keys: list[str] | None = None) -> dict[str, Any]:
        state = self._read()
        preserve_keys = preserve_keys or []
        old_user_data = state.get("user_data", {})
        preserved = {k: v for k, v in old_user_data.items() if k in preserve_keys}
        state["user_data"] = preserved
        state["recovery_mode"] = False
        state["history"].append(
            {"event": "factory_reset", "preserved_keys": sorted(preserve_keys), "ts": time.time()}
        )
        self._write(state)
        return {"ok": True, "preserved_keys": sorted(preserved.keys()), "wiped_keys": sorted(set(old_user_data) - set(preserved))}

    # -- recovery mode ------------------------------------------------------
    def enter_recovery_mode(self, *, reason: str) -> dict[str, Any]:
        from gunnchos_device_os.release_engineering import image_realms

        state = self._read()
        state["recovery_mode"] = True
        state["history"].append({"event": "enter_recovery_mode", "reason": reason, "ts": time.time()})
        self._write(state)
        realm = image_realms.load_realm(self.repo_root, "RECOVERY_IMAGE")
        return {
            "ok": True,
            "recovery_mode": True,
            "allowed_capabilities": realm.get("production_restrictions"),
            "recovery_behavior": realm.get("recovery_behavior"),
        }

    def exit_recovery_mode(self) -> dict[str, Any]:
        state = self._read()
        state["recovery_mode"] = False
        state["history"].append({"event": "exit_recovery_mode", "ts": time.time()})
        self._write(state)
        return {"ok": True, "recovery_mode": False}

    # -- key revocation / lost device path ---------------------------------
    def revoke_key(self, fingerprint: str, *, reason: str) -> dict[str, Any]:
        state = self._read()
        if fingerprint not in state["revoked_key_fingerprints"]:
            state["revoked_key_fingerprints"].append(fingerprint)
        state["history"].append({"event": "revoke_key", "fingerprint": fingerprint, "reason": reason, "ts": time.time()})
        self._write(state)
        return {"ok": True, "revoked_key_fingerprints": state["revoked_key_fingerprints"]}

    def mark_device_lost(self, *, reason: str) -> dict[str, Any]:
        state = self._read()
        state["device_lost"] = True
        state["remote_wipe_requested"] = True
        state["history"].append({"event": "mark_device_lost", "reason": reason, "ts": time.time()})
        self._write(state)
        return {"ok": True, "device_lost": True, "remote_wipe_requested": True}

    def execute_remote_wipe(self) -> dict[str, Any]:
        state = self._read()
        if not state.get("remote_wipe_requested"):
            return {"ok": False, "error": "no_pending_remote_wipe"}
        result = self.factory_reset(preserve_keys=[])
        state = self._read()
        state["remote_wipe_requested"] = False
        state["history"].append({"event": "remote_wipe_executed", "ts": time.time()})
        self._write(state)
        return {"ok": True, "wipe_result": result}

    def recover_lost_device(self, *, ownership_proof: str) -> dict[str, Any]:
        """Un-mark a device as lost once ownership is re-verified (simulated)."""
        if not ownership_proof:
            return {"ok": False, "error": "ownership_proof_required"}
        state = self._read()
        state["device_lost"] = False
        state["remote_wipe_requested"] = False
        state["history"].append({"event": "recover_lost_device", "ownership_proof_provided": True, "ts": time.time()})
        self._write(state)
        return {"ok": True, "device_lost": False}
