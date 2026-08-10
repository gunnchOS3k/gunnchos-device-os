"""SEC-LAB regression: host escape denied; approved pytest work roots allowed."""
from __future__ import annotations

from pathlib import Path

import pytest

from gunnchos_device_os.device_lab.session import (
    clear_lab_work_roots,
    instances_root,
    register_lab_work_root,
    start_session,
    stop_session,
    work_path_allowed,
)


ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(autouse=True)
def _clear_approved_roots():
    clear_lab_work_roots()
    yield
    clear_lab_work_roots()


def test_host_escape_outside_instances_denied():
    with pytest.raises(PermissionError, match="device_lab_work_path_escape"):
        start_session("handheld_docked", repo_root=ROOT, work=ROOT / "artifacts" / "ESCAPE_TEST")


def test_absolute_tmp_escape_denied():
    with pytest.raises(PermissionError, match="device_lab_work_path_escape"):
        start_session("handheld_docked", repo_root=ROOT, work=Path("/tmp/evil-lab-escape"))


def test_instances_prefix_sibling_denied():
    """startswith-style bugs must not allow instances_evil sibling paths."""
    evil = ROOT / "artifacts" / "device_lab" / "instances_evil" / "x"
    assert not work_path_allowed(evil, repo_root=ROOT)
    with pytest.raises(PermissionError, match="device_lab_work_path_escape"):
        start_session("handheld_docked", repo_root=ROOT, work=evil)


def test_unregistered_pytest_tmp_denied(tmp_path):
    with pytest.raises(PermissionError, match="device_lab_work_path_escape"):
        start_session("handheld_docked", repo_root=ROOT, work=tmp_path / "inst")


def test_registered_pytest_tmp_allowed(tmp_path):
    register_lab_work_root(tmp_path, repo_root=ROOT)
    started = start_session("handheld_docked", repo_root=ROOT, work=tmp_path / "inst")
    assert started["ok"] is True
    stop_session(started["instance_id"])


def test_default_instances_root_still_allowed():
    work = instances_root(ROOT) / "ci-default-inst"
    started = start_session("handheld_docked", repo_root=ROOT, work=work)
    assert started["ok"] is True
    stop_session(started["instance_id"])


def test_cannot_register_host_sensitive_root():
    with pytest.raises(PermissionError, match="device_lab_work_root_not_approvable"):
        register_lab_work_root(Path("/etc"), repo_root=ROOT)
