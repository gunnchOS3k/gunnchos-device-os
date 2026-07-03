"""Installable OS image prototype packaging smoke tests."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "scripts" / "build_installable_image.sh"
HEALTH = ROOT / "os_build" / "installable_image" / "healthcheck.sh"
VALIDATE = ROOT / "scripts" / "validate_installable_image_artifacts.py"
MANIFEST_DOC = ROOT / "os_build" / "installable_image" / "ARTIFACT_MANIFEST.md"
VERSION_MANIFEST = ROOT / "release_artifacts" / "version_manifest.example.json"
ARTIFACT = ROOT / "os_build" / "installable_image" / "artifact"


@pytest.fixture(scope="module")
def built_installable_image() -> None:
    rc = subprocess.call(["bash", str(BUILD)], cwd=ROOT, timeout=300)
    assert rc == 0


def test_build_installable_image_runs(built_installable_image: None):
    assert (ARTIFACT / "MANIFEST.json").exists()


def test_validate_installable_image_artifacts_passes(built_installable_image: None):
    rc = subprocess.call(["python3", str(VALIDATE)], cwd=ROOT)
    assert rc == 0


def test_healthcheck_passes_after_build(built_installable_image: None):
    rc = subprocess.call(["bash", str(HEALTH)], cwd=ROOT)
    assert rc == 0


def test_artifact_manifest_no_bootable_claim(built_installable_image: None):
    data = json.loads((ARTIFACT / "MANIFEST.json").read_text(encoding="utf-8"))
    assert data["bootable_os_claim"] is False
    assert data["iso_built"] is False
    assert data["hardware_validated"] is False
    assert data["artifact_type"] == "installable_os_image_prototype"


def test_bundle_and_checksums_exist(built_installable_image: None):
    assert (ARTIFACT / "gunnchos-installable-image-prototype.tar.gz").exists()
    checksums = (ARTIFACT / "CHECKSUMS.sha256").read_text(encoding="utf-8")
    assert "gunnchos-installable-image-prototype.tar.gz" in checksums
    assert "MANIFEST.json" in checksums


def test_manifest_doc_exists():
    assert MANIFEST_DOC.exists()
    text = MANIFEST_DOC.read_text(encoding="utf-8")
    assert "not" in text.lower()


def test_version_manifest_installable_track_prototype():
    data = json.loads(VERSION_MANIFEST.read_text(encoding="utf-8"))
    installable = data["artifact_types"]["installable_os_image"]
    assert installable["status"] == "prototype"
    assert installable["bootable"] is False
    assert data["claims"]["beta"] is False
    assert data["claims"]["ga"] is False
