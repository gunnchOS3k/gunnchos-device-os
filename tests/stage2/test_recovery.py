"""Lane A — recovery environment operations."""
from __future__ import annotations

import shutil
from pathlib import Path

from gunnchos_device_os.stage2.image_build import build_image
from gunnchos_device_os.stage2.recovery import RecoveryEnv
from gunnchos_device_os.stage2.update_manager import UpdateManager


def test_recovery_inspect_verify_select_repair_reinstall_reset():
    repo = Path(__file__).resolve().parents[2]
    build_image(repo_root=repo)
    root = Path("artifacts/stage2/test_sysroot_recovery")
    if root.exists():
        shutil.rmtree(root)
    mgr = UpdateManager(root)
    # Make B corrupt pending scenario
    pkg = mgr.build_update_package(version="bad", corrupt=True)
    mgr.apply_update(pkg)
    mgr.simulated_reboot()

    rec = RecoveryEnv(root, image_dir=repo / "artifacts" / "stage2" / "image")
    slots = rec.inspect_slots()
    assert "A" in slots["slots"] and "B" in slots["slots"]
    # Active may be on corrupt slot after simulated bad reboot; select_prior repairs.
    sel = rec.select_prior_slot()
    assert sel["ok"] is True
    assert rec.verify_slot(sel["selected"])["ok"] is True
    repair = rec.repair_metadata()
    assert repair["ok"] is True

    manifest = repo / "artifacts" / "stage2" / "image" / "MANIFEST.json"
    reinstall = rec.reinstall_approved_image(manifest)
    assert reinstall["ok"] is True

    denied = rec.factory_reset_user_data(confirm=False)
    assert denied["ok"] is False
    (root / "home" / "user" / "x.txt").parent.mkdir(parents=True, exist_ok=True)
    (root / "home" / "user" / "x.txt").write_text("wipe-me\n")
    reset = rec.factory_reset_user_data(confirm=True)
    assert reset["ok"] is True
    assert not (root / "home" / "user" / "x.txt").exists()
    # system slots remain
    assert (root / "system-a").is_dir()

    diag = rec.export_diagnostics(Path("artifacts/stage2/test_recovery_diag.json"))
    assert diag["ok"] is True
    assert "/Users/" not in Path("artifacts/stage2/test_recovery_diag.json").read_text()
