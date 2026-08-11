"""Factory provisioning digital tooling — DEV/TEST dummy identities only.

CLAIM BOUNDARY: every serial, MAC address, device identity, injected key,
and eSIM credential produced by this module is explicitly a DEV/TEST
dummy. MAC addresses are allocated from the IEEE *locally administered*
range (``02:xx:xx:xx:xx:xx``), never a real assigned OUI, so nothing here
can collide with or impersonate a real production MAC pool. No production
signing keys or real carrier/eSIM credentials exist in this repository.
"""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from gunnchos_device_os.release_engineering import dev_keys

STORE_SCHEMA = "gunnchos.factory_provisioning.store.v1"
IDENTITY_SCHEMA = "gunnchos.factory_provisioning.identity_response.v1"
CALIBRATION_SCHEMA = "gunnchos.factory_provisioning.calibration_record.v1"

CLAIM_BOUNDARY = (
    "DEV/TEST dummy factory provisioning tooling. Serials, MACs, identities, "
    "injected keys, and eSIM credentials here are not production data and "
    "must never be treated as real device records."
)


def _checksum_digit(s: str) -> str:
    total = sum((i + 1) * ord(c) for i, c in enumerate(s))
    return "0123456789ABCDEFGHJKLMNPQRSTUVWXYZ"[total % 35]


def generate_serial(sequence: int, *, line_id: str = "L1", product_code: str = "GX1") -> str:
    """DEV/TEST-only serial format: DEVTEST-<product>-<line>-<seq>-<checksum>."""
    if sequence < 0:
        raise ValueError("sequence_must_be_non_negative")
    body = f"{product_code}-{line_id}-{sequence:06d}"
    return f"DEVTEST-{body}-{_checksum_digit(body)}"


class MacAllocator:
    """Allocates MAC addresses from the IEEE locally-administered range
    only (X2:XX:XX:XX:XX:XX where the U/L bit is set) — never a real OUI,
    so this can never collide with or claim a production MAC pool."""

    _LOCAL_PREFIX = 0x02  # first octet: locally administered + unicast

    def __init__(self, store_path: Path) -> None:
        self.store_path = Path(store_path)
        if not self.store_path.exists():
            self._write({"schema": "gunnchos.factory_provisioning.mac_pool.v1", "allocated": {}})

    def _read(self) -> dict[str, Any]:
        return json.loads(self.store_path.read_text(encoding="utf-8"))

    def _write(self, data: dict[str, Any]) -> None:
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self.store_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def allocate(self, device_id: str) -> str:
        data = self._read()
        allocated = data["allocated"]
        for existing_mac, existing_dev in allocated.items():
            if existing_dev == device_id:
                return existing_mac
        used = set(allocated.keys())
        for _ in range(1000):
            rand = uuid.uuid4().bytes[:5]
            mac = ":".join(["02"] + [f"{b:02x}" for b in rand])
            if mac not in used:
                allocated[mac] = device_id
                self._write(data)
                return mac
        raise RuntimeError("mac_pool_exhausted")  # pragma: no cover

    def release(self, mac: str) -> bool:
        data = self._read()
        removed = data["allocated"].pop(mac, None) is not None
        if removed:
            self._write(data)
        return removed

    def is_locally_administered(self, mac: str) -> bool:
        first_octet = int(mac.split(":")[0], 16)
        return bool(first_octet & 0x02) and not bool(first_octet & 0x01)


def build_identity_request(serial: str, mac: str, realm_id: str = "FACTORY_PROVISIONING_IMAGE") -> dict[str, Any]:
    return {
        "schema": "gunnchos.factory_provisioning.identity_request.v1",
        "serial": serial,
        "mac": mac,
        "realm_id": realm_id,
        "requested_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "dummy_identity": True,
    }


def issue_identity_response(repo_root: Path, request: dict[str, Any]) -> dict[str, Any]:
    device_id = f"dev-{uuid.uuid4().hex[:16]}"
    response = {
        "schema": IDENTITY_SCHEMA,
        "device_id": device_id,
        "serial": request["serial"],
        "mac": request["mac"],
        "realm_id": request["realm_id"],
        "issued_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "dummy_identity": True,
        "claim_boundary": CLAIM_BOUNDARY,
    }
    payload = json.dumps(response, sort_keys=True).encode("utf-8")
    response["signature_hex"] = dev_keys.sign_bytes(repo_root, payload)
    response["signing_key_fingerprint"] = dev_keys.dev_public_key_fingerprint(repo_root)
    return response


class KeyInjectionInterface:
    """Generates a per-device DUMMY Ed25519 keypair — never a shared or
    production key. This models the *interface* a real HSM-backed key
    ceremony would sit behind; no real key ceremony happens here."""

    def inject(self, device_id: str) -> dict[str, Any]:
        key = Ed25519PrivateKey.generate()
        pub_pem = key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return {
            "schema": "gunnchos.factory_provisioning.key_injection.v1",
            "device_id": device_id,
            "dummy_key": True,
            "production_key": False,
            "public_key_pem": pub_pem.decode("utf-8"),
            "injected_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "claim_boundary": "Per-device DUMMY dev-tier key; not a production key ceremony.",
        }


class EsimProvisioningInterface:
    """Stub interface only — real eSIM/carrier credentials are always
    EXTERNAL_PENDING in this repository and are never generated here."""

    def request_provisioning(self, device_id: str) -> dict[str, Any]:
        return {
            "schema": "gunnchos.factory_provisioning.esim_provisioning.v1",
            "device_id": device_id,
            "status": "EXTERNAL_PENDING",
            "iccid": None,
            "activation_code": None,
            "requested_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "claim_boundary": "Real eSIM/carrier credentials are issued externally and are out of this repo's scope.",
        }


def validate_calibration_record(record: dict[str, Any]) -> list[str]:
    failures = []
    for field in ("device_id", "test_station_id", "measurements", "result", "timestamp_utc"):
        if field not in record:
            failures.append(f"missing_field:{field}")
    if record.get("result") not in ("PASS", "FAIL"):
        failures.append("bad_result_value")
    if not isinstance(record.get("measurements"), dict) or not record.get("measurements"):
        failures.append("measurements_must_be_nonempty_dict")
    return failures


class FactoryProvisioningStation:
    """Aggregates one line station's DEV/TEST provisioning state in a
    single JSON store: serials issued, MAC allocations, identities,
    injected keys, eSIM requests, calibration imports, flashing events,
    device records, and repair traceability."""

    def __init__(self, repo_root: Path, store_path: Path) -> None:
        self.repo_root = Path(repo_root)
        self.store_path = Path(store_path)
        self.mac_allocator = MacAllocator(self.store_path.parent / "mac_pool.json")
        self.key_injector = KeyInjectionInterface()
        self.esim = EsimProvisioningInterface()
        if not self.store_path.exists():
            self._write(
                {
                    "schema": STORE_SCHEMA,
                    "next_serial_sequence": 1,
                    "devices": {},
                    "repair_log": [],
                }
            )

    def _read(self) -> dict[str, Any]:
        return json.loads(self.store_path.read_text(encoding="utf-8"))

    def _write(self, data: dict[str, Any]) -> dict[str, Any]:
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self.store_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return data

    def provision_new_device(self, *, line_id: str = "L1", product_code: str = "GX1") -> dict[str, Any]:
        data = self._read()
        seq = data["next_serial_sequence"]
        serial = generate_serial(seq, line_id=line_id, product_code=product_code)
        data["next_serial_sequence"] = seq + 1
        self._write(data)

        request = build_identity_request(serial, mac="pending")
        temp_device_marker = f"pending-{serial}"
        mac = self.mac_allocator.allocate(temp_device_marker)
        request["mac"] = mac
        identity = issue_identity_response(self.repo_root, request)
        device_id = identity["device_id"]

        self.mac_allocator.release(temp_device_marker)
        self.mac_allocator.allocate(device_id)
        key_injection = self.key_injector.inject(device_id)
        esim = self.esim.request_provisioning(device_id)

        data = self._read()
        data["devices"][device_id] = {
            "device_id": device_id,
            "serial": serial,
            "mac": mac,
            "identity": identity,
            "key_injection": key_injection,
            "esim": esim,
            "calibration_records": [],
            "flash_events": [],
            "status": "PROVISIONED",
        }
        self._write(data)
        return {"ok": True, "device_id": device_id, "serial": serial, "mac": mac}

    def import_calibration(self, device_id: str, record: dict[str, Any]) -> dict[str, Any]:
        failures = validate_calibration_record(record)
        if failures:
            return {"ok": False, "error": "calibration_record_invalid", "failures": failures}
        data = self._read()
        device = data["devices"].get(device_id)
        if device is None:
            return {"ok": False, "error": "device_not_found"}
        device["calibration_records"].append(record)
        if record["result"] == "FAIL":
            device["status"] = "CALIBRATION_FAILED"
        self._write(data)
        return {"ok": True, "device_id": device_id, "result": record["result"]}

    def pre_flash_check(self, device_id: str, image_manifest: dict[str, Any]) -> dict[str, Any]:
        data = self._read()
        device = data["devices"].get(device_id)
        if device is None:
            return {"ok": False, "error": "device_not_found"}
        if device["status"] == "CALIBRATION_FAILED":
            return {"ok": False, "error": "device_failed_calibration_refusing_flash"}
        if image_manifest.get("PRODUCTION_RELEASE_CLAIMED") is True:
            return {"ok": False, "error": "refusing_to_flash_production_release_claim"}
        return {"ok": True, "device_id": device_id}

    def flash(self, device_id: str, image_manifest: dict[str, Any]) -> dict[str, Any]:
        check = self.pre_flash_check(device_id, image_manifest)
        if not check["ok"]:
            return check
        data = self._read()
        device = data["devices"][device_id]
        event = {
            "ts": time.time(),
            "realm_id": image_manifest.get("realm_id"),
            "image_hash": image_manifest.get("image_hash"),
            "rootfs_sha256": (image_manifest.get("artifacts", {}).get("rootfs_tarball") or {}).get("sha256"),
        }
        device["flash_events"].append(event)
        device["status"] = "FLASHED"
        self._write(data)
        return {"ok": True, "device_id": device_id, "flash_event": event}

    def post_flash_verify(self, device_id: str) -> dict[str, Any]:
        data = self._read()
        device = data["devices"].get(device_id)
        if device is None:
            return {"ok": False, "error": "device_not_found"}
        if not device["flash_events"]:
            return {"ok": False, "error": "no_flash_event_recorded"}
        return {"ok": True, "device_id": device_id, "last_flash_event": device["flash_events"][-1]}

    def export_device_record(self, device_id: str) -> dict[str, Any]:
        data = self._read()
        device = data["devices"].get(device_id)
        if device is None:
            return {"ok": False, "error": "device_not_found"}
        import hashlib

        record = {"schema": "gunnchos.factory_provisioning.device_record_export.v1", "device": device}
        digest = hashlib.sha256(json.dumps(record, sort_keys=True, default=str).encode("utf-8")).hexdigest()
        record["export_sha256"] = digest
        return {"ok": True, "record": record}

    def record_repair_event(
        self, device_id: str, *, component: str, technician_id: str, reason: str
    ) -> dict[str, Any]:
        data = self._read()
        if device_id not in data["devices"]:
            return {"ok": False, "error": "device_not_found"}
        event = {
            "device_id": device_id,
            "component": component,
            "technician_id": technician_id,
            "reason": reason,
            "ts": time.time(),
        }
        data["repair_log"].append(event)
        self._write(data)
        return {"ok": True, "event": event}

    def repair_history(self, device_id: str) -> list[dict[str, Any]]:
        data = self._read()
        return [e for e in data["repair_log"] if e["device_id"] == device_id]

    def wipe_and_rework(self, device_id: str, *, reason: str) -> dict[str, Any]:
        """Wipe a defective device's provisioning state so it can be
        re-provisioned under a fresh device_id (identity + keys + eSIM +
        calibration + flash history are all cleared; the serial/MAC are
        released back to their respective pools)."""
        data = self._read()
        device = data["devices"].pop(device_id, None)
        if device is None:
            return {"ok": False, "error": "device_not_found"}
        self.mac_allocator.release(device["mac"])
        data["repair_log"].append(
            {"device_id": device_id, "event": "wipe_and_rework", "reason": reason, "ts": time.time()}
        )
        self._write(data)
        return {"ok": True, "wiped_device_id": device_id, "released_serial": device["serial"], "released_mac": device["mac"]}
