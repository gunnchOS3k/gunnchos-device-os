"""Continuation IX — Final Digital Release Lock tests.

Default suite stays honest without host productivity packages.
Set GUNNCHOS_CONT_IX_REQUIRE_READY=1 (CI Cont IX job after apt install)
to require READY/PASS tokens.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from gunnchos_device_os.cont_viii.recreation_reprove import reprove_recreation
from gunnchos_device_os.cont_viii import TOKEN_RECREATION_REPROVE_PASS
from gunnchos_device_os.cont_ix.digital_lock import evaluate_digital_lock
from gunnchos_device_os.cont_ix import (
    TOKEN_DIGITAL_LOCK,
    TOKEN_RECREATION_READY,
    TOKEN_ADOPTER_READY,
    TOKEN_REPRO_READY,
    TOKEN_STUDENT_READY,
    TOKEN_OFFICE_READY,
)


REQUIRE_READY = os.environ.get("GUNNCHOS_CONT_IX_REQUIRE_READY") == "1"


def test_gate1_recreation_reprove_ci_safe_without_siblings(tmp_path: Path):
    """Gate 1 fix: vendored fixtures earn Cont VIII recreation pass without siblings."""
    r = reprove_recreation(repos_root=tmp_path)
    assert r["ok"] is True
    assert r["token"] == TOKEN_RECREATION_REPROVE_PASS
    assert r["gaps"] == []
    assert r["ci_safe_without_siblings"] is True
    assert all(v.get("evidence_source") == "vendored_fixture" for v in r["games"].values())


def test_cont_ix_digital_lock_structure():
    r = evaluate_digital_lock(write=True)
    assert r["schema"] == "gunnchos.digital_release_lock.v1"
    assert r["continuation"] == "IX"
    assert r["physical_execution_freeze"] is True
    assert r["merge_forbidden"] is True
    assert r["recreation_ready_neq_reproducible_ready"] is True
    assert "DIGITAL" in r["blockers"]
    assert "PHYSICAL" in r["blockers"]
    assert "EXTERNAL" in r["blockers"]
    assert Path("artifacts/continuation_ix/DIGITAL_RELEASE_LOCK.json").exists()
    assert Path("artifacts/continuation_ix/REMAINING_BLOCKERS.json").exists()
    # DIGITAL blockers empty OR exact failure reasons
    for b in r["blockers"]["DIGITAL"]:
        assert b.get("lane")
        assert b.get("reason")
    if REQUIRE_READY:
        assert r["ok"] is True
        assert r["token"] == TOKEN_DIGITAL_LOCK
        assert r["blockers"]["DIGITAL"] == []
        for tok in (
            TOKEN_STUDENT_READY,
            TOKEN_OFFICE_READY,
            TOKEN_RECREATION_READY,
            TOKEN_ADOPTER_READY,
            TOKEN_REPRO_READY,
        ):
            assert tok in r["earned_tokens"]


@pytest.mark.skipif(not REQUIRE_READY, reason="set GUNNCHOS_CONT_IX_REQUIRE_READY=1 after package install")
def test_cont_ix_ready_tokens_in_clean_env():
    r = evaluate_digital_lock(write=True)
    assert r["ok"] and r["token"] == TOKEN_DIGITAL_LOCK
    assert TOKEN_STUDENT_READY in r["earned_tokens"]
    assert TOKEN_OFFICE_READY in r["earned_tokens"]
    assert TOKEN_RECREATION_READY in r["earned_tokens"]
    assert TOKEN_ADOPTER_READY in r["earned_tokens"]
    assert TOKEN_REPRO_READY in r["earned_tokens"]
