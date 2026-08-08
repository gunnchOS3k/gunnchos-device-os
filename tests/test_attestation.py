"""Attestation — measurable-boot evidence schema + DEV verification."""
from __future__ import annotations

import copy

from gunnchos_device_os.attestation import (
    AttestationVerifier,
    ExpectedMeasurements,
    Measurement,
    MeasurementStage,
    MeasurableBootEvidence,
    Realm,
    SCHEMA_VERSION,
    build_dev_evidence,
)
from gunnchos_device_os.identity import sha256_text


DIGESTS = {
    MeasurementStage.BOOTLOADER.value: sha256_text("bl"),
    MeasurementStage.KERNEL.value: sha256_text("k"),
    MeasurementStage.INITRD.value: sha256_text("i"),
    MeasurementStage.ROOTFS_MANIFEST.value: sha256_text("r"),
    MeasurementStage.LAUNCHER.value: sha256_text("l"),
}


def test_build_dev_evidence_has_required_fields():
    doc = build_dev_evidence("boot-1", "dev-1", DIGESTS, security_version=2)
    assert doc["schema_version"] == SCHEMA_VERSION
    assert doc["realm"] == Realm.DEV.value
    assert doc["signature"]
    assert len(doc["pcr_bank"]) == 5
    assert doc["mock"] is False
    assert "production" not in doc["claim_boundary"].lower() or "no production" in doc["claim_boundary"].lower()


def test_verify_valid_dev_evidence():
    doc = build_dev_evidence("boot-1", "dev-1", DIGESTS)
    v = AttestationVerifier(
        expected=ExpectedMeasurements(digests=DIGESTS, min_security_version=1)
    )
    result = v.verify(doc)
    assert result["valid"] is True
    assert result["errors"] == []
    assert result["mock"] is False


def test_tampered_measurement_fails():
    doc = build_dev_evidence("boot-1", "dev-1", DIGESTS)
    doc["measurements"][0]["digest_sha256"] = sha256_text("evil")
    # signature and pcr will also mismatch
    v = AttestationVerifier(expected=ExpectedMeasurements(digests=DIGESTS))
    result = v.verify(doc)
    assert result["valid"] is False
    assert any("bad_signature" in e or "mismatch" in e for e in result["errors"])


def test_bad_signature_fails():
    doc = build_dev_evidence("boot-1", "dev-1", DIGESTS)
    doc["signature"] = "0" * 64
    result = AttestationVerifier().verify(doc)
    assert result["valid"] is False
    assert "bad_signature" in result["errors"]


def test_prod_realm_rejected_without_keys():
    doc = build_dev_evidence("boot-1", "dev-1", DIGESTS)
    doc["realm"] = Realm.PROD.value
    # resign would fail; just set realm — signature won't match either,
    # but prod rejection should be explicit
    result = AttestationVerifier().verify(doc)
    assert result["valid"] is False
    assert "prod_realm_rejected_no_production_keys" in result["errors"]


def test_security_version_floor():
    doc = build_dev_evidence("boot-1", "dev-1", DIGESTS, security_version=1)
    v = AttestationVerifier(expected=ExpectedMeasurements(min_security_version=3))
    result = v.verify(doc)
    assert result["valid"] is False
    assert "security_version_too_low" in result["errors"]


def test_schema_missing_field():
    doc = build_dev_evidence("boot-1", "dev-1", DIGESTS)
    del doc["pcr_bank"]
    errors = AttestationVerifier().validate_schema(doc)
    assert "missing_field:pcr_bank" in errors


def test_pcr_bank_recomputed():
    evidence = MeasurableBootEvidence(
        boot_id="b",
        device_id="d",
        measurements=[
            Measurement(stage=MeasurementStage(s), digest_sha256=d)
            for s, d in DIGESTS.items()
        ],
    )
    bank = evidence.compute_pcr_bank()
    assert bank["pcr1"] != bank["pcr5"]
    evidence.pcr_bank = bank
    evidence.sign_dev()
    # Mutate pcr after sign
    doc = evidence.to_dict()
    doc["pcr_bank"] = copy.deepcopy(doc["pcr_bank"])
    doc["pcr_bank"]["pcr1"] = "a" * 64
    # Need valid signature for body — force body mismatch via pcr
    # Re-sign won't happen; verification catches pcr or signature
    result = AttestationVerifier().verify(doc)
    assert result["valid"] is False


def test_measurement_mismatch_against_expected():
    doc = build_dev_evidence("boot-1", "dev-1", DIGESTS)
    expected = ExpectedMeasurements(
        digests={**DIGESTS, MeasurementStage.KERNEL.value: sha256_text("other")}
    )
    result = AttestationVerifier(expected=expected).verify(doc)
    assert result["valid"] is False
    assert any(e.startswith("measurement_mismatch:kernel") for e in result["errors"])


def test_cannot_sign_prod_with_dev_stub():
    evidence = MeasurableBootEvidence(
        boot_id="b",
        device_id="d",
        measurements=[
            Measurement(stage=MeasurementStage.KERNEL, digest_sha256=sha256_text("k"))
        ],
        realm=Realm.PROD,
    )
    try:
        evidence.sign_dev()
        assert False, "should have raised"
    except ValueError as exc:
        assert "DEV" in str(exc) or "dev" in str(exc).lower()
