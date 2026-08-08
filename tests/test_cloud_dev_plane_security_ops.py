"""SAST hook, abuse suite, SBOM/provenance for DEV plane security ops."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEV_OPS = REPO_ROOT / "security" / "dev_ops"
sys.path.insert(0, str(DEV_OPS))

from abuse_suite import run_abuse_suite  # noqa: E402
from gunnchos_device_os.cloud_dev_plane.provenance import build_cyclonedx, write_artifacts


def test_sast_hook_clean():
    proc = subprocess.run(
        [sys.executable, str(DEV_OPS / "sast_hook.py")],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "SAST_HOOK_OK" in proc.stdout


def test_abuse_suite_passes():
    report = run_abuse_suite()
    assert report["ok"] is True
    assert report["passed"] == report["total"]
    assert report["realm"] == "DEV"


def test_sbom_and_provenance(tmp_path):
    cdx = build_cyclonedx()
    assert cdx["bomFormat"] == "CycloneDX"
    names = {c["name"] for c in cdx["components"]}
    assert "gunnchos-dev-plane-identity" in names
    assert "gunnchos-otel-collector-dev" in names
    paths = write_artifacts(tmp_path)
    assert Path(paths["sbom"]).exists()
    assert Path(paths["provenance"]).exists()
    text = Path(paths["provenance"]).read_text(encoding="utf-8")
    assert "DEV" in text
    assert "production_keys_used" in text
