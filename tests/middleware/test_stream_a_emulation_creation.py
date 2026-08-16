"""Stream A A3/A4 emulation pack + creation host chain tests."""
from __future__ import annotations

from pathlib import Path

from gunnchos_device_os.creation_enablement.host_chain import run_host_creator_chain
from gunnchos_device_os.device_lab.emulation_packs import validate_pack

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_reusable_lab_pack_silicon_exact_false():
    report = validate_pack()
    assert report["SILICON_EXACT_EMULATION"] is False
    assert report["ok"] is True, report
    assert report["profile_count"] >= 6


def test_stream_a_sample_memo_host_chain(tmp_path):
    result = run_host_creator_chain(REPO_ROOT, tmp_path / "creation_work")
    assert result["ok_host_chain"] is True, result
    assert result["CREATOR_END_TO_END_DIGITAL_PASS"] is False
    assert result["ok_guest_install_run"] is False
    assert result["SILICON_EXACT_EMULATION"] is False
