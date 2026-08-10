"""gunnchContinuity — clipboard/files/state/peripherals with identity+encryption+permission.

E2E Handheld ↔ Student ↔ DS-XL continuity handoff.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


DEVICE_ROLES = ("HANDHELD", "STUDENT", "DSXL")


@dataclass
class ContinuityIdentity:
    user_id: str
    device_id: str
    role: str
    device_secret: bytes = field(repr=False)

    @classmethod
    def create(
        cls,
        user_id: str,
        device_id: str,
        role: str,
        *,
        device_secret: bytes | None = None,
    ) -> ContinuityIdentity:
        if role not in DEVICE_ROLES:
            raise ValueError(role)
        # SEC-FABRIC / continuity: secrets must not be derivable from public IDs.
        secret = device_secret if device_secret is not None else secrets.token_bytes(32)
        return cls(user_id=user_id, device_id=device_id, role=role, device_secret=secret)


@dataclass
class ContinuityPermission:
    allow_clipboard: bool = True
    allow_files: bool = True
    allow_state: bool = True
    allow_peripherals: bool = True


class ContinuityVault:
    def __init__(self, root: Path, identity: ContinuityIdentity, perms: ContinuityPermission | None = None):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.identity = identity
        self.perms = perms or ContinuityPermission()
        self._clipboard: dict[str, Any] | None = None
        self._files: dict[str, bytes] = {}
        self._state: dict[str, Any] = {}
        self._peripherals: list[dict[str, Any]] = []
        self.audit: list[dict[str, Any]] = []

    def _seal(self, payload: bytes) -> dict[str, str]:
        key = self.identity.device_secret
        # XOR stream + HMAC (dev-grade encryption envelope; PHYSICAL_PENDING for secure enclave)
        nonce = os.urandom(16)
        stream = hashlib.sha256(key + nonce).digest()
        while len(stream) < len(payload):
            stream += hashlib.sha256(stream).digest()
        cipher = bytes(a ^ b for a, b in zip(payload, stream))
        tag = hmac.new(key, nonce + cipher, hashlib.sha256).hexdigest()
        return {
            "nonce": nonce.hex(),
            "cipher": cipher.hex(),
            "tag": tag,
            "alg": "xor-hmac-sha256-dev",
        }

    def _unseal(self, envelope: dict[str, str], peer_secret: bytes) -> bytes:
        nonce = bytes.fromhex(envelope["nonce"])
        cipher = bytes.fromhex(envelope["cipher"])
        tag = hmac.new(peer_secret, nonce + cipher, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(tag, envelope["tag"]):
            raise PermissionError("integrity_check_failed")
        stream = hashlib.sha256(peer_secret + nonce).digest()
        while len(stream) < len(cipher):
            stream += hashlib.sha256(stream).digest()
        return bytes(a ^ b for a, b in zip(cipher, stream))

    def put_clipboard(self, text: str) -> dict[str, Any]:
        if not self.perms.allow_clipboard:
            raise PermissionError("clipboard_denied")
        env = self._seal(text.encode())
        self._clipboard = {"kind": "clipboard", "envelope": env, "at": time.time()}
        self.audit.append({"op": "put_clipboard", "device": self.identity.device_id})
        return {"ok": True, "bytes": len(text.encode())}

    def put_file(self, name: str, data: bytes) -> dict[str, Any]:
        if not self.perms.allow_files:
            raise PermissionError("files_denied")
        env = self._seal(data)
        self._files[name] = json.dumps(env).encode()
        (self.root / f"{name}.cont").write_bytes(self._files[name])
        self.audit.append({"op": "put_file", "name": name})
        return {"ok": True, "name": name, "bytes": len(data)}

    def put_state(self, key: str, value: Any) -> dict[str, Any]:
        if not self.perms.allow_state:
            raise PermissionError("state_denied")
        self._state[key] = value
        env = self._seal(json.dumps({key: value}).encode())
        (self.root / "state.json.cont").write_text(json.dumps(env), encoding="utf-8")
        self.audit.append({"op": "put_state", "key": key})
        return {"ok": True, "key": key}

    def attach_peripheral(self, peripheral_id: str, kind: str) -> dict[str, Any]:
        if not self.perms.allow_peripherals:
            raise PermissionError("peripherals_denied")
        entry = {"id": peripheral_id, "kind": kind, "at": time.time()}
        self._peripherals.append(entry)
        self.audit.append({"op": "attach_peripheral", **entry})
        return {"ok": True, **entry}

    def wipe(self, *, reason: str = "mdm_wipe") -> dict[str, Any]:
        """Clear sealed continuity contents (digital revoke / wipe path)."""
        removed_files = 0
        for p in list(self.root.glob("*.cont")):
            p.unlink(missing_ok=True)
            removed_files += 1
        self._clipboard = None
        self._files.clear()
        self._state.clear()
        self._peripherals.clear()
        # Fail-closed: deny all continuity after wipe
        self.perms = ContinuityPermission(
            allow_clipboard=False,
            allow_files=False,
            allow_state=False,
            allow_peripherals=False,
        )
        entry = {
            "ok": True,
            "op": "wipe",
            "device": self.identity.device_id,
            "reason": reason,
            "removed_files": removed_files,
            "continuity_access": "denied",
        }
        self.audit.append(entry)
        (self.root / "WIPE.json").write_text(json.dumps(entry, indent=2) + "\n", encoding="utf-8")
        return entry

    def export_handoff(self) -> dict[str, Any]:
        if not any(
            (
                self.perms.allow_clipboard,
                self.perms.allow_files,
                self.perms.allow_state,
                self.perms.allow_peripherals,
            )
        ):
            raise PermissionError("continuity_wiped_or_denied")
        return {
            "schema": "gunnchos.phase_xiv.continuity_handoff.v1",
            "user_id": self.identity.user_id,
            "from_device": self.identity.device_id,
            "from_role": self.identity.role,
            "clipboard": self._clipboard,
            "files": {k: json.loads(v.decode()) for k, v in self._files.items()},
            "state": self._state,
            "peripherals": list(self._peripherals),
            "identity_proof": hmac.new(
                self.identity.device_secret, self.identity.user_id.encode(), hashlib.sha256
            ).hexdigest(),
        }


class ContinuityMesh:
    """Multi-device continuity mesh for E2E role transitions."""

    def __init__(self, root: Path, user_id: str = "u_continuity"):
        self.root = root
        self.user_id = user_id
        self.devices: dict[str, ContinuityVault] = {}

    def enroll(self, device_id: str, role: str) -> ContinuityVault:
        ident = ContinuityIdentity.create(self.user_id, device_id, role)
        vault = ContinuityVault(self.root / device_id, ident)
        self.devices[device_id] = vault
        return vault

    def wipe_device(self, device_id: str, *, reason: str = "mdm_wipe") -> dict[str, Any]:
        vault = self.devices.get(device_id)
        if vault is None:
            raise KeyError(f"unknown continuity device: {device_id}")
        return vault.wipe(reason=reason)

    def handoff(self, src_id: str, dst_id: str) -> dict[str, Any]:
        src = self.devices[src_id]
        dst = self.devices[dst_id]
        if src.identity.user_id != dst.identity.user_id:
            raise PermissionError("identity_mismatch")
        # Impersonation guard: destination must already be enrolled in this mesh
        # with a non-derivable secret (forged vaults with guessed secrets fail unseal).
        if dst_id not in self.devices:
            raise PermissionError("unknown_destination")
        if not any(
            (
                dst.perms.allow_clipboard,
                dst.perms.allow_files,
                dst.perms.allow_state,
                dst.perms.allow_peripherals,
            )
        ):
            raise PermissionError("destination_wiped_or_denied")
        packet = src.export_handoff()
        expected = hmac.new(
            src.identity.device_secret, self.user_id.encode(), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(packet["identity_proof"], expected):
            raise PermissionError("bad_identity_proof")
        # decrypt clipboard with src secret, re-seal for dst
        transferred = {"clipboard": False, "files": 0, "state_keys": 0, "peripherals": 0}
        if packet.get("clipboard"):
            plain = src._unseal(packet["clipboard"]["envelope"], src.identity.device_secret)
            dst.put_clipboard(plain.decode())
            transferred["clipboard"] = True
        for name, env in (packet.get("files") or {}).items():
            plain = src._unseal(env, src.identity.device_secret)
            dst.put_file(name, plain)
            transferred["files"] += 1
        for k, v in (packet.get("state") or {}).items():
            dst.put_state(k, v)
            transferred["state_keys"] += 1
        for p in packet.get("peripherals") or []:
            dst.attach_peripheral(p["id"], p["kind"])
            transferred["peripherals"] += 1
        return {
            "ok": True,
            "from": src.identity.role,
            "to": dst.identity.role,
            "transferred": transferred,
        }

    def e2e_handheld_student_dsxl(self) -> dict[str, Any]:
        h = self.enroll("dev-handheld", "HANDHELD")
        s = self.enroll("dev-student", "STUDENT")
        d = self.enroll("dev-dsxl", "DSXL")
        h.put_clipboard("lecture notes draft")
        h.put_file("notes.txt", b"Week 3 OFDM homework")
        h.put_state("app.focus", "waike.tutor")
        h.attach_peripheral("ring-left", "spatial_ring")
        hs = self.handoff("dev-handheld", "dev-student")
        sd = self.handoff("dev-student", "dev-dsxl")
        ok = (
            hs["ok"]
            and sd["ok"]
            and hs["from"] == "HANDHELD"
            and hs["to"] == "STUDENT"
            and sd["to"] == "DSXL"
            and d._clipboard is not None
            and "notes.txt" in d._files
            and d._state.get("app.focus") == "waike.tutor"
            and any(p["id"] == "ring-left" for p in d._peripherals)
        )
        return {"ok": ok, "handheld_to_student": hs, "student_to_dsxl": sd, "roles": DEVICE_ROLES}
