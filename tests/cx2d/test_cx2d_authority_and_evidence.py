"""CX2D — shell authority, lab isolation, fail-closed tokens."""

from __future__ import annotations

import json
from pathlib import Path

from gunnchos_device_os.cx2d import (
    CX2D_SINGLE_PRODUCTION_SHELL_AUTHORITY,
    FULL_COMPLETE_EXPERIENCE_COMPLETE,
)
from gunnchos_device_os.cx2d.evidence import write_evidence
from gunnchos_device_os.cx2d.journeys import upgrade_journeys
from gunnchos_device_os.cx2d.tokens import fail_closed_tokens


REPO = Path(__file__).resolve().parents[2]


def test_single_production_shell_authority_token():
    assert CX2D_SINGLE_PRODUCTION_SHELL_AUTHORITY is True
    decision = (REPO / "docs/complete-experience/CX2D_SHELL_AUTHORITY_DECISION.md").read_text()
    assert "Path B" in decision
    assert "apps/gunnch_shell" in decision
    assert (REPO / "apps/gunnch_shell/src/CompleteExperienceShell.tsx").is_file()
    adapter = (REPO / "apps/launcher_mock/src/cx2/CompleteExperienceShell.tsx").read_text()
    assert "DEPRECATED" in adapter
    assert "gunnch_shell" in adapter


def test_evidence_fail_closed(tmp_path: Path):
    # Write into a temp copy of artifact namespace via monkeypatch-like repo stub
    # Use real repo for lab paths that read cache; evidence writer uses repo_root.
    report = write_evidence(REPO)
    assert report["FULL_COMPLETE_EXPERIENCE_COMPLETE"] is False
    assert FULL_COMPLETE_EXPERIENCE_COMPLETE is False
    assert report["CX2D_SINGLE_PRODUCTION_SHELL_AUTHORITY"] is True
    tokens = report["tokens"]
    assert tokens["CX2D_REAL_HOME_WINDOW"] is False
    assert tokens["CX2D_REAL_BROWSER_GUI_PASS"] is False
    assert tokens["CX2D_HUMAN_A11Y_PENDING"] is True
    assert tokens["CX2D_PHYSICAL_PRINTER_PENDING"] is True
    root = REPO / "artifacts/complete_experience/cx2d"
    assert (root / "CX2D_EVIDENCE_REPORT.json").exists()
    assert (root / "CX2D_LINUX_LAB_PROVENANCE.json").exists()
    assert (root / "HUMAN_A11Y_VALIDATION_PACKET.md").exists()
    journeys = report["journeys"]["journeys"]
    for jid, j in journeys.items():
        assert j["REAL_USER_JOURNEY_DIGITAL_PASS"] is False
        assert j["cx2d_class"] in ("BLOCKED", "HUMAN_VALIDATION_PENDING", "REAL_PROVIDER_PARTIAL", "HARNESS_ONLY")


def test_upgrade_journeys_never_inflate():
    up = upgrade_journeys(linux_gui_proven=False)
    assert up["any_real_user_journey_digital_pass"] is False
    for j in up["journeys"].values():
        assert j["REAL_USER_JOURNEY_DIGITAL_PASS"] is False


def test_fail_closed_tokens_defaults():
    t = fail_closed_tokens()
    assert t.CX2D_SINGLE_PRODUCTION_SHELL_AUTHORITY is True
    assert t.CX2D_REAL_HOME_WINDOW is False
    assert t.FULL_COMPLETE_EXPERIENCE_COMPLETE is False


def test_device_lab_artifacts_not_required_mutated():
    # CX2D evidence namespace must not live under device lab paths
    report = json.loads((REPO / "artifacts/complete_experience/cx2d/CX2D_EVIDENCE_REPORT.json").read_text())
    assert report["firewall"]["device_lab_134_unaltered"] is True
    assert "device_lab" not in report["firewall"]["evidence_path"]
