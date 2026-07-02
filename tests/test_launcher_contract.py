"""Launcher contract and campus workspace app tests."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from gunnchos_device_os.app_registry import APPS, get_app
from gunnchos_device_os.policy_engine import evaluate

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "apps" / "launcher_mock" / "src" / "generated" / "launcherContract.json"
EXPORT = ROOT / "scripts" / "export_launcher_contract.py"


def test_contract_export_includes_files_and_notes():
    subprocess.check_call([sys.executable, str(EXPORT)], cwd=ROOT)
    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    assert data["version"]
    assert "files" in data["apps"]
    assert "notes" in data["apps"]
    assert "files" in data["campus_native_apps"]
    assert "notes" in data["campus_native_apps"]
    assert data["claim_boundary"].get("workspace_storage")


def test_app_registry_includes_workspace_apps():
    files = get_app("files")
    notes = get_app("notes")
    assert files["offline_supported"] is True
    assert notes["offline_supported"] is True
    assert files["claim_status"] == "browser_workspace_prototype"
    assert "files" in APPS and "notes" in APPS


def test_offline_mode_allows_local_productivity_paths():
    # Offline mode supports local media and lecture; notes/files are native offline apps
    assert evaluate("admin", "Offline", "local_media")["allowed"] is True
    assert evaluate("admin", "Offline", "netflix")["allowed"] is False


def test_library_mode_blocks_streaming_in_policy():
    assert evaluate("student", "Library", "netflix")["allowed"] is False
    assert evaluate("student", "Library", "hulu")["allowed"] is False


def test_contract_missing_file_fails_cleanly(tmp_path: Path):
    missing = tmp_path / "missing.json"
    assert not missing.exists()
