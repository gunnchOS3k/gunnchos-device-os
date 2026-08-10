"""Local/offline game-save authenticated integrity (LOCAL_SAVE_INTEGRITY_DIGITAL=E4).

Binds integrity to user/device/platform secret via HMAC-SHA256 (stdlib + keyed).
Unauthenticated digests are rejected as tamper protection. Online multiplayer
integrity remains AUTHORITATIVE_MULTIPLAYER_INTEGRITY=EXTERNAL_OR_OPERATIONS_PENDING.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


AUTHORITATIVE_MULTIPLAYER_INTEGRITY = "EXTERNAL_OR_OPERATIONS_PENDING"
LOCAL_SAVE_INTEGRITY_DIGITAL = "E4_PREPARED"


def _canonical(payload: dict[str, Any]) -> bytes:
    body = {
        k: v
        for k, v in payload.items()
        if k not in {"mac", "integrity", "_raw", "authenticated"}
    }
    return json.dumps(body, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def derive_platform_secret(
    *,
    user_id: str,
    device_id: str,
    platform_secret: bytes,
) -> bytes:
    return hmac.new(
        platform_secret,
        f"gunnchos-save-v1|{user_id}|{device_id}".encode(),
        hashlib.sha256,
    ).digest()


@dataclass
class GameSaveIntegrityStore:
    """Authenticated local save store with quarantine + backup/recovery."""

    user_id: str
    device_id: str
    platform_secret: bytes
    root: Path | None = None
    saves: dict[str, dict[str, Any]] = field(default_factory=dict)
    quarantine: dict[str, dict[str, Any]] = field(default_factory=dict)
    backups: dict[str, dict[str, Any]] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._key = derive_platform_secret(
            user_id=self.user_id,
            device_id=self.device_id,
            platform_secret=self.platform_secret,
        )
        if self.root is not None:
            self.root.mkdir(parents=True, exist_ok=True)

    def _mac(self, payload: dict[str, Any]) -> str:
        return hmac.new(self._key, _canonical(payload), hashlib.sha256).hexdigest()

    def seal(self, payload: dict[str, Any]) -> dict[str, Any]:
        body = dict(payload)
        body.pop("mac", None)
        body.pop("integrity", None)  # strip unauthenticated digest claims
        body.pop("authenticated", None)
        body["user_id"] = self.user_id
        body["device_id"] = self.device_id
        body["alg"] = "HMAC-SHA256"
        body["mac"] = self._mac(body)
        body["authenticated"] = True
        return body

    def verify(self, sealed: dict[str, Any] | None) -> dict[str, Any]:
        if not sealed:
            return {"ok": False, "reason": "missing"}
        # Reject unauthenticated digest-as-protection
        if sealed.get("integrity") and not sealed.get("mac"):
            return {
                "ok": False,
                "reason": "unauthenticated_digest_rejected",
                "note": "Plain integrity digest is not tamper protection",
            }
        if not sealed.get("mac") or not sealed.get("authenticated"):
            return {"ok": False, "reason": "missing_mac"}
        if sealed.get("user_id") != self.user_id or sealed.get("device_id") != self.device_id:
            return {"ok": False, "reason": "binding_mismatch"}
        expected = self._mac(sealed)
        if not hmac.compare_digest(str(sealed.get("mac")), expected):
            return {"ok": False, "reason": "tamper_detected"}
        return {"ok": True, "reason": "ok"}

    def save(self, slot: str, payload: dict[str, Any]) -> dict[str, Any]:
        # Backup prior good save before overwrite
        prior = self.saves.get(slot)
        if prior and self.verify(prior).get("ok"):
            self.backups[slot] = {"payload": dict(prior), "at": time.time()}
        sealed = self.seal(payload)
        self.saves[slot] = sealed
        # First successful save is also a recovery point until a newer prior exists
        if slot not in self.backups:
            self.backups[slot] = {"payload": dict(sealed), "at": time.time()}
        if self.root is not None:
            (self.root / f"{slot}.json").write_text(
                json.dumps(sealed, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
        return {"ok": True, "slot": slot, "sealed": sealed}

    def load(self, slot: str) -> dict[str, Any]:
        sealed = self.saves.get(slot)
        if sealed is None and self.root is not None:
            path = self.root / f"{slot}.json"
            if path.exists():
                sealed = json.loads(path.read_text(encoding="utf-8"))
                self.saves[slot] = sealed
        check = self.verify(sealed)
        if not check.get("ok"):
            if sealed is not None:
                self.quarantine[slot] = {
                    "payload": sealed,
                    "reason": check.get("reason"),
                    "at": time.time(),
                }
                self.saves.pop(slot, None)
            return {"ok": False, "quarantined": sealed is not None, **check}
        return {"ok": True, "slot": slot, "payload": sealed, **check}

    def recover(self, slot: str) -> dict[str, Any]:
        backup = self.backups.get(slot)
        if not backup:
            return {"ok": False, "reason": "no_backup"}
        check = self.verify(backup["payload"])
        if not check.get("ok"):
            return {"ok": False, "reason": "backup_corrupt", **check}
        self.saves[slot] = dict(backup["payload"])
        self.quarantine.pop(slot, None)
        return {"ok": True, "slot": slot, "recovered_from_backup": True}

    def inject_tamper(self, slot: str, mutator) -> dict[str, Any]:
        """Test helper: mutate stored bytes without valid MAC."""
        sealed = dict(self.saves[slot])
        mutator(sealed)
        self.saves[slot] = sealed
        return sealed


def new_platform_secret() -> bytes:
    return secrets.token_bytes(32)


def run_digital_suite(*, tmp: Path | None = None) -> dict[str, Any]:
    platform = new_platform_secret()
    store = GameSaveIntegrityStore(
        user_id="user-ada",
        device_id="dev-student-1",
        platform_secret=platform,
        root=tmp,
    )
    cases: list[dict[str, Any]] = []

    def add(cid: str, passed: bool, evidence: dict[str, Any]) -> None:
        cases.append({"case_id": cid, "passed": passed, "evidence": evidence})

    store.save("slot1", {"level": 3, "score": 100})
    good = store.load("slot1")
    add(
        "GS-SAVE-001",
        good.get("ok") is True,
        {k: good[k] for k in good if k != "payload"},
    )

    # Tamper score
    store.inject_tamper("slot1", lambda s: s.__setitem__("score", 99999))
    bad = store.load("slot1")
    add(
        "GS-TAMPER-001",
        bad.get("ok") is False
        and bad.get("reason") == "tamper_detected"
        and bad.get("quarantined") is True,
        bad,
    )

    # Recover from backup
    rec = store.recover("slot1")
    loaded = store.load("slot1")
    add(
        "GS-RECOVER-001",
        rec.get("ok") is True and loaded.get("ok") is True and loaded["payload"]["score"] == 100,
        {
            "recover": rec,
            "loaded_ok": loaded.get("ok"),
            "score": (loaded.get("payload") or {}).get("score"),
        },
    )

    # Unauthenticated digest rejected
    other = GameSaveIntegrityStore(
        user_id="user-ada",
        device_id="dev-student-1",
        platform_secret=platform,
    )
    digest_only = {
        "level": 1,
        "score": 1,
        "integrity": hashlib.sha256(b"level:1:score:1").hexdigest(),
        "user_id": "user-ada",
        "device_id": "dev-student-1",
    }
    rejected = other.verify(digest_only)
    add(
        "GS-DIGEST-001",
        rejected.get("reason") == "unauthenticated_digest_rejected",
        rejected,
    )

    # Cross-device binding fail
    foreign = GameSaveIntegrityStore(
        user_id="user-ada",
        device_id="dev-OTHER",
        platform_secret=platform,
    )
    sealed = store.seal({"level": 2, "score": 50})
    cross = foreign.verify(sealed)
    add("GS-BIND-001", cross.get("reason") == "binding_mismatch", cross)

    all_pass = all(c["passed"] for c in cases)
    return {
        "schema": "gunnchos.wp007.local_save_integrity_digital.v1",
        "LOCAL_SAVE_INTEGRITY_DIGITAL": LOCAL_SAVE_INTEGRITY_DIGITAL if all_pass else "FAIL",
        "AUTHORITATIVE_MULTIPLAYER_INTEGRITY": AUTHORITATIVE_MULTIPLAYER_INTEGRITY,
        "passed": all_pass,
        "cases": cases,
        "claim_boundary": (
            "Local/offline authenticated save integrity only. "
            f"AUTHORITATIVE_MULTIPLAYER_INTEGRITY={AUTHORITATIVE_MULTIPLAYER_INTEGRITY}."
        ),
    }
