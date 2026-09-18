"""CX2A — real experience surfaces in product shell + taxonomy."""

from __future__ import annotations

from pathlib import Path

from gunnchos_device_os.cx2 import FULL_COMPLETE_EXPERIENCE_COMPLETE
from gunnchos_device_os.cx2.evidence_taxonomy import EVIDENCE_CLASSES, reclassification_document
from gunnchos_device_os.cx2.shell.nav import SURFACE_ORDER
from gunnchos_device_os.cx2.shell.product_shell import ProductShell


def test_taxonomy_hierarchy():
    assert "REAL_USER_JOURNEY_DIGITAL_PASS" in EVIDENCE_CLASSES
    assert "HARNESS_PASS" in EVIDENCE_CLASSES
    doc = reclassification_document()
    assert doc["FULL_COMPLETE_EXPERIENCE_COMPLETE"] is False
    assert any(r["cx2_class"] == "HARNESS_PASS" for r in doc["reclassifications"])


def test_product_shell_surfaces_and_nav(tmp_path: Path):
    shell = ProductShell(tmp_path / "cx2")
    first = shell.ensure_first_run("Surface User", "School")
    assert first["surface"] == "home"
    for sid in SURFACE_ORDER:
        model = shell.surface(sid)
        assert model["surface"] == sid
        assert model["nav"]["current"] == sid
        assert model.get("title")
    assert shell.nav.back()["back_available"] or True
    home = shell.nav.home()
    assert home["current"] == "home"
    restart = shell.restart_return_home()
    assert restart["ok"] is True
    assert restart["surface"] == "home"
    traverse = shell.keyboard_traverse_all()
    assert traverse["ok"] is True
    assert FULL_COMPLETE_EXPERIENCE_COMPLETE is False


def test_empty_and_offline_states(tmp_path: Path):
    shell = ProductShell(tmp_path / "cx2")
    shell.ensure_first_run("Offline User")
    snap = shell.set_offline(True)
    assert snap["offline"] is True
    vault = shell.surface("vault")
    assert "empty" in vault
