"""Positive + negative RuntimeTarget preflight tests."""
from __future__ import annotations

import json
from pathlib import Path

from gunnchos_device_os.device_lab.runtime_target_preflight import (
    DEVICE_LAB_GUEST_PROFILE,
    PREFERRED_LABEL,
    evaluate_runtime_target_against_guest,
    run_runtime_target_preflight,
    select_runtime_target_for_label,
)

ROOT = Path(__file__).resolve().parents[2]


def test_select_prefers_linux_aarch64_glibc236():
    sel = select_runtime_target_for_label(ROOT, label=PREFERRED_LABEL)
    if not sel.get("ok"):
        # Artifact may be absent in sparse CI checkouts.
        assert sel.get("error", "").startswith("runtime_target_label_not_found")
        return
    rt = sel["selected"]["runtime_target"]
    assert rt["compatibility_label"] == "linux-aarch64-glibc236"
    assert rt["architecture"] == "aarch64"
    assert rt["source_sha"] == "232fc8dc3aa10d3dd644ef48d1d8c63da50d4d3c"


def test_positive_preflight_glibc236_vs_debian12_guest():
    sel = select_runtime_target_for_label(ROOT, label=PREFERRED_LABEL)
    if not sel.get("ok"):
        return
    rt = sel["selected"]["runtime_target"]
    result = evaluate_runtime_target_against_guest(rt, DEVICE_LAB_GUEST_PROFILE)
    assert result["RUNTIME_TARGET_PREFLIGHT_PASS"] is True
    assert not result["blockers"]


def test_negative_preflight_rejects_ubuntu_glibc239_on_debian12():
    bad = {
        "schema_version": "waike.runtime_target.v1",
        "compatibility_label": "linux-aarch64-current",
        "target_id": "aarch64-current",
        "architecture": "aarch64",
        "elf_interpreter": "/lib/ld-linux-aarch64.so.1",
        "measured_max_glibc": "2.39",
        "glibc_baseline": "2.39",
        "source_sha": "deadbeef",
        "artifact_sha256": "0" * 64,
    }
    result = evaluate_runtime_target_against_guest(bad, DEVICE_LAB_GUEST_PROFILE)
    assert result["RUNTIME_TARGET_PREFLIGHT_PASS"] is False
    assert "measured_max_glibc_within_guest" in result["blockers"]
    assert "preferred_compatibility_label" in result["blockers"]


def test_run_preflight_writes_json(tmp_path: Path):
    out = tmp_path / "RUNTIME_TARGET_PREFLIGHT.json"
    doc = run_runtime_target_preflight(ROOT, session=None, out_path=out)
    assert out.is_file()
    loaded = json.loads(out.read_text(encoding="utf-8"))
    assert loaded["schema"] == "gunnchos.device_lab.runtime_target_preflight.v1"
    assert "RUNTIME_TARGET_PREFLIGHT_PASS" in loaded
    assert loaded["RUNTIME_TARGET_PREFLIGHT_PASS"] == doc["RUNTIME_TARGET_PREFLIGHT_PASS"]
