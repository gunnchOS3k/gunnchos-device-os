"""Attestation stub — measurable-boot evidence schema + DEV-realm verification.

DEV realm only. Uses deterministic HMAC with an in-repo ephemeral DEV secret
material derived at runtime (not production keys, not TPM quotes).
Does not claim silicon PCR extension or production attestation.
"""
from __future__ import annotations

import hashlib
import hmac
import json
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any

from gunnchos_device_os.identity import sha256_json, sha256_text, utc_now_iso


CLAIM_BOUNDARY = (
    "DEV-realm measurable-boot evidence only. No TPM quotes, no production "
    "keys, no silicon PCR attestation claim."
)

# Ephemeral DEV realm secret material — intentionally not a production key.
# Derived string is stable for tests; never labeled as a production trust root.
DEV_REALM_LABEL = "gunnchos-dev-attestation-realm-v1"
DEV_REALM_SECRET = sha256_text(f"{DEV_REALM_LABEL}:not-a-production-key")[:64]

SCHEMA_VERSION = "1.0.0"
REQUIRED_EVIDENCE_FIELDS = (
    "schema_version",
    "realm",
    "boot_id",
    "device_id",
    "measurements",
    "pcr_bank",
    "security_version",
    "created_at",
    "signature",
)


class Realm(str, Enum):
    DEV = "dev"
    # Production reserved — verification must reject until real keys exist.
    PROD = "prod"


class MeasurementStage(str, Enum):
    BOOTLOADER = "bootloader"
    KERNEL = "kernel"
    INITRD = "initrd"
    ROOTFS_MANIFEST = "rootfs_manifest"
    LAUNCHER = "launcher"


@dataclass
class Measurement:
    stage: MeasurementStage
    digest_sha256: str
    description: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage.value,
            "digest_sha256": self.digest_sha256,
            "description": self.description,
        }


def _sign_payload(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hmac.new(
        DEV_REALM_SECRET.encode("utf-8"),
        canonical.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


@dataclass
class MeasurableBootEvidence:
    """Structured measurable-boot evidence document."""

    boot_id: str
    device_id: str
    measurements: list[Measurement]
    security_version: int = 1
    realm: Realm = Realm.DEV
    schema_version: str = SCHEMA_VERSION
    created_at: str = field(default_factory=utc_now_iso)
    pcr_bank: dict[str, str] = field(default_factory=dict)
    signature: str = ""

    def compute_pcr_bank(self) -> dict[str, str]:
        """Software PCR-style bank: extend digests in stage order."""
        order = [
            MeasurementStage.BOOTLOADER,
            MeasurementStage.KERNEL,
            MeasurementStage.INITRD,
            MeasurementStage.ROOTFS_MANIFEST,
            MeasurementStage.LAUNCHER,
        ]
        by_stage = {m.stage: m for m in self.measurements}
        bank: dict[str, str] = {}
        acc = "0" * 64
        for i, stage in enumerate(order, start=1):
            m = by_stage.get(stage)
            dig = m.digest_sha256 if m else ("f" * 64)
            acc = sha256_text(f"{acc}:{dig}")
            bank[f"pcr{i}"] = acc
        return bank

    def unsigned_body(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "realm": self.realm.value,
            "boot_id": self.boot_id,
            "device_id": self.device_id,
            "measurements": [m.to_dict() for m in self.measurements],
            "pcr_bank": dict(self.pcr_bank),
            "security_version": self.security_version,
            "created_at": self.created_at,
        }

    def sign_dev(self) -> "MeasurableBootEvidence":
        if self.realm != Realm.DEV:
            raise ValueError("only DEV realm may be signed by this stub")
        if not self.pcr_bank:
            self.pcr_bank = self.compute_pcr_bank()
        body = self.unsigned_body()
        self.signature = _sign_payload(body)
        return self

    def to_dict(self) -> dict[str, Any]:
        body = self.unsigned_body()
        body["signature"] = self.signature
        body["claim_boundary"] = CLAIM_BOUNDARY
        body["mock"] = False
        return body


@dataclass
class ExpectedMeasurements:
    """Golden measurement set for verification."""

    digests: dict[str, str] = field(default_factory=dict)
    min_security_version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AttestationVerifier:
    """Verify measurable-boot evidence in DEV realm."""

    expected: ExpectedMeasurements = field(default_factory=ExpectedMeasurements)
    allow_prod: bool = False  # must stay False — no fake prod keys

    def validate_schema(self, doc: dict[str, Any]) -> list[str]:
        errors: list[str] = []
        for key in REQUIRED_EVIDENCE_FIELDS:
            if key not in doc:
                errors.append(f"missing_field:{key}")
        if doc.get("schema_version") != SCHEMA_VERSION:
            errors.append("unsupported_schema_version")
        if doc.get("realm") not in (Realm.DEV.value, Realm.PROD.value):
            errors.append("invalid_realm")
        measurements = doc.get("measurements")
        if not isinstance(measurements, list) or not measurements:
            errors.append("measurements_empty")
        else:
            for i, m in enumerate(measurements):
                if not isinstance(m, dict):
                    errors.append(f"measurement_{i}_not_object")
                    continue
                if "stage" not in m or "digest_sha256" not in m:
                    errors.append(f"measurement_{i}_incomplete")
                dig = m.get("digest_sha256", "")
                if not isinstance(dig, str) or len(dig) != 64:
                    errors.append(f"measurement_{i}_bad_digest")
        return errors

    def verify(self, doc: dict[str, Any]) -> dict[str, Any]:
        errors = self.validate_schema(doc)
        if errors:
            return {
                "valid": False,
                "errors": errors,
                "realm": doc.get("realm"),
                "mock": False,
                "claim_boundary": CLAIM_BOUNDARY,
            }

        realm = doc["realm"]
        if realm == Realm.PROD.value and not self.allow_prod:
            return {
                "valid": False,
                "errors": ["prod_realm_rejected_no_production_keys"],
                "realm": realm,
                "mock": False,
                "claim_boundary": CLAIM_BOUNDARY,
            }

        body = {k: doc[k] for k in (
            "schema_version", "realm", "boot_id", "device_id",
            "measurements", "pcr_bank", "security_version", "created_at",
        )}
        expected_sig = _sign_payload(body)
        if not hmac.compare_digest(expected_sig, doc.get("signature", "")):
            errors.append("bad_signature")

        if int(doc["security_version"]) < self.expected.min_security_version:
            errors.append("security_version_too_low")

        for m in doc["measurements"]:
            stage = m["stage"]
            if stage in self.expected.digests and self.expected.digests[stage] != m["digest_sha256"]:
                errors.append(f"measurement_mismatch:{stage}")

        # Recompute PCR bank and compare
        measurements = [
            Measurement(
                stage=MeasurementStage(m["stage"]),
                digest_sha256=m["digest_sha256"],
                description=m.get("description", ""),
            )
            for m in doc["measurements"]
        ]
        recomputed = MeasurableBootEvidence(
            boot_id=doc["boot_id"],
            device_id=doc["device_id"],
            measurements=measurements,
            security_version=int(doc["security_version"]),
            realm=Realm(realm),
            created_at=doc["created_at"],
        ).compute_pcr_bank()
        if recomputed != doc.get("pcr_bank"):
            errors.append("pcr_bank_mismatch")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "realm": realm,
            "boot_id": doc["boot_id"],
            "device_id": doc["device_id"],
            "evidence_hash": sha256_json(body),
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }


def build_dev_evidence(
    boot_id: str,
    device_id: str,
    stage_digests: dict[str, str],
    *,
    security_version: int = 1,
) -> dict[str, Any]:
    """Helper: build and sign DEV measurable-boot evidence."""
    measurements = [
        Measurement(
            stage=MeasurementStage(stage),
            digest_sha256=digest,
            description=f"dev measurement for {stage}",
        )
        for stage, digest in stage_digests.items()
    ]
    evidence = MeasurableBootEvidence(
        boot_id=boot_id,
        device_id=device_id,
        measurements=measurements,
        security_version=security_version,
        realm=Realm.DEV,
    )
    evidence.sign_dev()
    return evidence.to_dict()
