"""Image prototype packaging smoke tests."""
from __future__ import annotations

import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "os_build" / "image_prototype" / "build_kiosk_package.sh"
HEALTH = ROOT / "os_build" / "image_prototype" / "healthcheck.sh"
MANIFEST_DOC = ROOT / "os_build" / "image_prototype" / "ARTIFACT_MANIFEST.md"
VERSION_MANIFEST = ROOT / "release_artifacts" / "version_manifest.example.json"


def test_build_kiosk_package_runs():
    rc = subprocess.call(["bash", str(BUILD)], cwd=ROOT, timeout=300)
    assert rc == 0


def test_healthcheck_passes_after_build():
    subprocess.call(["bash", str(BUILD)], cwd=ROOT, timeout=300)
    rc = subprocess.call(["bash", str(HEALTH)], cwd=ROOT)
    assert rc == 0


def test_artifact_manifest_no_bootable_claim():
    subprocess.call(["bash", str(BUILD)], cwd=ROOT, timeout=300)
    data = json.loads((ROOT / "os_build/image_prototype/artifact/MANIFEST.json").read_text())
    assert data["bootable_os_claim"] is False
    assert data["hardware_validated"] is False


def test_manifest_doc_exists():
    assert MANIFEST_DOC.exists()
    text = MANIFEST_DOC.read_text(encoding="utf-8")
    assert "not" in text.lower()


def test_version_manifest_draft():
    data = json.loads(VERSION_MANIFEST.read_text(encoding="utf-8"))
    assert data["claims"]["beta"] is False
    assert data["claims"]["ga"] is False
