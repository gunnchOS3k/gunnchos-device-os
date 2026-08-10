"""Lane A — atomic update success + corrupt rollback with user data intact."""
from __future__ import annotations

import shutil
from pathlib import Path

from gunnchos_device_os.stage2.update_manager import UpdateManager


def _sysroot() -> Path:
    root = Path("artifacts/stage2/test_sysroot_update")
    if root.exists():
        shutil.rmtree(root)
    return root


def test_success_update_marks_good():
    root = _sysroot()
    mgr = UpdateManager(root)
    (root / "data" / "appstate.json").write_text('{"ok":true}\n')
    before = (root / "home" / "user" / "KEEPME.txt").read_text()
    result = mgr.run_success_path("0.2.0-test")
    assert result["ok"] is True
    assert result["finalize"]["state"] == "marked_good"
    assert result["finalize"]["user_data_intact"] is True
    assert (root / "home" / "user" / "KEEPME.txt").read_text() == before
    assert mgr.active_slot() in ("A", "B")
    assert (mgr._slot_dir(mgr.active_slot()) / "IMAGE_VERSION").read_text().strip() == "0.2.0-test"


def test_corrupt_update_rolls_back_user_data_intact():
    root = _sysroot()
    mgr = UpdateManager(root)
    (root / "data" / "appstate.json").write_text('{"precious":true}\n')
    keep = root / "home" / "user" / "KEEPME.txt"
    keep.write_text("do-not-lose\n")
    active_before = mgr.active_slot()
    fp_before = mgr.user_data_fingerprint()
    result = mgr.run_failure_rollback_path("0.2.1-bad")
    assert result["ok"] is True
    assert result["finalize"]["rolled_back"] is True
    assert result["finalize"]["active_slot"] == active_before
    assert mgr.active_slot() == active_before
    assert keep.read_text() == "do-not-lose\n"
    assert (root / "data" / "appstate.json").read_text() == '{"precious":true}\n'
    assert mgr.user_data_fingerprint() == fp_before
