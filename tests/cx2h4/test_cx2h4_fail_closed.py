"""Fail-closed CX2H.4 tests — journey PASSes alone ≠ P0 digital closure."""

from __future__ import annotations

import json
from pathlib import Path

from gunnchos_device_os.cx2h4.audit import (
    build_blocker_register,
    build_developer_audit,
    build_domain_matrix,
    build_media_audit,
    build_no_second_computer,
    build_security_audit,
    pick_next_gate,
)
from gunnchos_device_os.cx2h4.tokens import Cx2h4Tokens

ROOT = Path(__file__).resolve().parents[2]


def _rebind_ok() -> dict:
    return {
        "CX2H4_JOURNEY_REBIND_PASS": True,
        "J1_CLASS": "REAL_USER_JOURNEY_DIGITAL_PASS",
        "J2_CLASS": "REAL_USER_JOURNEY_DIGITAL_PASS",
        "J3_CLASS": "REAL_USER_JOURNEY_DIGITAL_PASS",
        "J5_CLASS": "REAL_USER_JOURNEY_DIGITAL_PASS",
        "J7_CLASS": "REAL_USER_JOURNEY_DIGITAL_PASS",
        "J6_CLASS": "HUMAN_VALIDATION_PENDING",
    }


def test_five_journey_passes_do_not_imply_p0_closure():
    tokens = Cx2h4Tokens(
        CX2H4_JOURNEY_REBIND_PASS=True,
        J1_CLASS="REAL_USER_JOURNEY_DIGITAL_PASS",
        J2_CLASS="REAL_USER_JOURNEY_DIGITAL_PASS",
        J3_CLASS="REAL_USER_JOURNEY_DIGITAL_PASS",
        J5_CLASS="REAL_USER_JOURNEY_DIGITAL_PASS",
        J7_CLASS="REAL_USER_JOURNEY_DIGITAL_PASS",
        J6_CLASS="HUMAN_VALIDATION_PENDING",
        CX2H4_J4_P0_DIGITAL_BLOCKER=True,  # still blocked
        CX2H4_SPREADSHEET_P0_PASS=True,
        CX2H4_PRESENTATION_P0_PASS=True,
        CX2H4_NO_SECOND_COMPUTER_P0_PASS=True,
        CX2H4_SECURITY_REGRESSION_FREE=True,
    )
    assert tokens.digital_closure_eligible() is False
    assert tokens.CX2H4_P0_DIGITAL_CLOSURE_PASS is False


def test_j4_cannot_be_ignored_if_required():
    j4 = {"J4_P0_DIGITAL_BLOCKER": True, "J4_CLASS": "BLOCKED"}
    office = {"ok": True, "CX2H4_SPREADSHEET_P0_PASS": True, "CX2H4_PRESENTATION_P0_PASS": True}
    rebind = _rebind_ok()
    matrix = build_domain_matrix(ROOT, rebind=rebind, j4=j4, office=office, tip="deadbeef")
    security = {"CX2H4_SECURITY_REGRESSION_FREE": True}
    nsc = {"CX2H4_NO_SECOND_COMPUTER_P0_PASS": True}
    blockers = build_blocker_register(matrix, j4, office, security, nsc)
    assert blockers["blocks_cx3_count"] >= 1
    assert any(b.get("domain") == 6 for b in blockers["blocks_cx3"])


def test_installed_calc_impress_binaries_cannot_equal_gui_proof():
    office = {
        "ok": False,
        "CX2H4_SPREADSHEET_P0_PASS": False,
        "CX2H4_PRESENTATION_P0_PASS": False,
        "binaries_present": True,
    }
    assert office["binaries_present"] is True
    assert office["CX2H4_SPREADSHEET_P0_PASS"] is False
    tokens = Cx2h4Tokens(
        CX2H4_JOURNEY_REBIND_PASS=True,
        CX2H4_J4_P0_DIGITAL_BLOCKER=False,
        CX2H4_SPREADSHEET_P0_PASS=False,
        CX2H4_PRESENTATION_P0_PASS=False,
        CX2H4_NO_SECOND_COMPUTER_P0_PASS=True,
        CX2H4_SECURITY_REGRESSION_FREE=True,
        J1_CLASS="REAL_USER_JOURNEY_DIGITAL_PASS",
        J2_CLASS="REAL_USER_JOURNEY_DIGITAL_PASS",
        J3_CLASS="REAL_USER_JOURNEY_DIGITAL_PASS",
        J5_CLASS="REAL_USER_JOURNEY_DIGITAL_PASS",
        J7_CLASS="REAL_USER_JOURNEY_DIGITAL_PASS",
    )
    assert tokens.digital_closure_eligible() is False


def test_media_binary_presence_cannot_equal_playback_pass():
    media = build_media_audit()
    assert media["CX2H4_MEDIA_PLAYBACK_DIGITAL_PASS"] == "not_required"
    assert media.get("p0_required") is False
    fake = {"mpv_installed": True, "pass": True}
    # presence alone is not a digital PASS token
    assert fake["mpv_installed"] is True
    assert media["CX2H4_MEDIA_PLAYBACK_DIGITAL_PASS"] != "true"


def test_human_physical_pending_does_not_become_digital_pass():
    does_not = build_blocker_register(
        {"domains": []},
        {"J4_P0_DIGITAL_BLOCKER": False},
        {"CX2H4_SPREADSHEET_P0_PASS": True, "CX2H4_PRESENTATION_P0_PASS": True},
        {"CX2H4_SECURITY_REGRESSION_FREE": True},
        {"CX2H4_NO_SECOND_COMPUTER_P0_PASS": True},
    )["does_not_block_cx3"]
    human = [x for x in does_not if x["blocker_id"] == "HUMAN_A11Y"][0]
    assert human["blocks_cx3"] is False
    assert human["evidence_class"] == "HUMAN_VALIDATION_PENDING"


def test_later_cx3_domains_not_incorrectly_fail():
    rebind = _rebind_ok()
    j4 = {"J4_P0_DIGITAL_BLOCKER": False, "J4_CLASS": "REAL_PROVIDER_GUI_PARTIAL"}
    office = {"ok": True, "CX2H4_SPREADSHEET_P0_PASS": True, "CX2H4_PRESENTATION_P0_PASS": True}
    matrix = build_domain_matrix(ROOT, rebind=rebind, j4=j4, office=office, tip="deadbeef")
    d10 = next(d for d in matrix["domains"] if d["domain"] == 10)
    assert d10["evidence_class"] == "NOT_APPLICABLE"
    assert d10["p0_digital_blocker"] is False


def test_no_second_computer_fails_if_host_mutation_required():
    office = {"CX2H4_SPREADSHEET_P0_PASS": False, "CX2H4_PRESENTATION_P0_PASS": True}
    j4 = {"J4_P0_DIGITAL_BLOCKER": False}
    nsc = build_no_second_computer(office, j4, _rebind_ok())
    assert nsc["CX2H4_NO_SECOND_COMPUTER_P0_PASS"] is False
    assert nsc["user_workflow_host_mutation_required"] is True


def test_security_regressions_prevent_digital_closure():
    tokens = Cx2h4Tokens(
        CX2H4_JOURNEY_REBIND_PASS=True,
        CX2H4_J4_P0_DIGITAL_BLOCKER=False,
        CX2H4_SPREADSHEET_P0_PASS=True,
        CX2H4_PRESENTATION_P0_PASS=True,
        CX2H4_NO_SECOND_COMPUTER_P0_PASS=True,
        CX2H4_SECURITY_REGRESSION_FREE=False,
        J1_CLASS="REAL_USER_JOURNEY_DIGITAL_PASS",
        J2_CLASS="REAL_USER_JOURNEY_DIGITAL_PASS",
        J3_CLASS="REAL_USER_JOURNEY_DIGITAL_PASS",
        J5_CLASS="REAL_USER_JOURNEY_DIGITAL_PASS",
        J7_CLASS="REAL_USER_JOURNEY_DIGITAL_PASS",
    )
    assert tokens.digital_closure_eligible() is False


def test_full_eligible_tokens_and_empty_blockers_point_cx3():
    tokens = Cx2h4Tokens(
        CX2H4_JOURNEY_REBIND_PASS=True,
        CX2H4_J4_P0_DIGITAL_BLOCKER=False,
        CX2H4_SPREADSHEET_P0_PASS=True,
        CX2H4_PRESENTATION_P0_PASS=True,
        CX2H4_MEDIA_PLAYBACK_DIGITAL_PASS="not_required",
        CX2H4_DEVELOPER_BASELINE_PASS="not_required",
        CX2H4_NO_SECOND_COMPUTER_P0_PASS=True,
        CX2H4_SECURITY_REGRESSION_FREE=True,
        J1_CLASS="REAL_USER_JOURNEY_DIGITAL_PASS",
        J2_CLASS="REAL_USER_JOURNEY_DIGITAL_PASS",
        J3_CLASS="REAL_USER_JOURNEY_DIGITAL_PASS",
        J5_CLASS="REAL_USER_JOURNEY_DIGITAL_PASS",
        J7_CLASS="REAL_USER_JOURNEY_DIGITAL_PASS",
        J6_CLASS="HUMAN_VALIDATION_PENDING",
    )
    assert tokens.digital_closure_eligible() is True
    tok = tokens.to_dict()
    tok["CX2H4_P0_DIGITAL_CLOSURE_PASS"] = True
    blockers = {"blocks_cx3": [], "blocks_cx3_count": 0}
    assert pick_next_gate(tok, blockers) == "CX3_EDUCATION_CREDENTIALS_PORTFOLIO"


def test_developer_baseline_not_required_by_default():
    assert build_developer_audit()["CX2H4_DEVELOPER_BASELINE_PASS"] == "not_required"


def test_full_complete_experience_remains_false():
    tokens = Cx2h4Tokens()
    assert tokens.FULL_COMPLETE_EXPERIENCE_COMPLETE is False
