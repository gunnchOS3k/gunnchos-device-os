from __future__ import annotations

import json
from pathlib import Path

from gunnchos_device_os.app_registry import get_app, list_apps
from gunnchos_launcher.mlv_bridge import journey_preset_access, parse_mlv_deep_link
from gunnchos_launcher.mlv_continuity import (
    CANONICAL_CAMPUSES,
    REAL_ACTUATION_ENABLED,
    WAIKE_PR25_HEAD,
    actuation_policy,
    authorize_role,
    build_journey_matrix,
    canonicalize_campus,
    convergence_gates,
    learning_telemetry_join_state,
    load_waike_contract,
    open_network_twin,
    open_waike_from_campus,
    parse_mlv_product_link,
    parse_waike_deep_link,
    return_from_surface,
    seven_campus_route_proof,
    validate_intent,
    waike_readiness_truth,
)

ROOT = Path(__file__).resolve().parents[1]
MATRIX_PATH = ROOT / "artifacts" / "integration" / "MLV_WAIKE_7GC_AIRAN_JOURNEY_MATRIX.json"
GATES_PATH = ROOT / "artifacts" / "integration" / "MLV_WAIKE_7GC_AIRAN_CONVERGENCE_GATES.json"
SHARE_TOKEN = "abcdefghijklmnopqrstuvwxyz0123"


def test_foundation_home_and_share_still_work():
    home = parse_mlv_product_link("gunnchos://mlv/home")
    assert home["ok"] is True
    assert home["route_kind"] == "home"
    assert home["visibility_context"] == "private"
    assert home["canonical"] == "gunnchos://mlv/home"
    foundation = parse_mlv_deep_link("gunnchos://mlv/home")
    assert foundation["valid"] is True
    share = parse_mlv_product_link(f"gunnchos://mlv/share/{SHARE_TOKEN}")
    assert share["ok"] is True
    assert share["token_present"] is True
    assert SHARE_TOKEN not in str(share)


def test_mlv_campus_and_gallery_routes():
    campus = parse_mlv_product_link("gunnchos://mlv/campus")
    assert campus["ok"] is True
    assert campus["route_kind"] == "campus"
    gallery = parse_mlv_product_link("gunnchos://mlv/gallery")
    assert gallery["ok"] is True
    assert gallery["visibility_context"] == "gallery_public"
    assert parse_mlv_product_link("https://evil.example/mlv")["ok"] is False
    assert parse_mlv_product_link("gunnchos://mlv/unknown")["reason"] == "unknown_route_kind"


def test_seven_campus_and_network_twin_routes():
    proof = seven_campus_route_proof()
    assert proof["MLV_7GC_CAMPUS_ROUTE_PASS"] == "7/7"
    assert proof["MLV_NETWORK_TWIN_ROUTE_PASS"] == "7/7"
    assert canonicalize_campus("graham-land") == "graham_land"
    landing = parse_mlv_product_link("gunnchos://mlv/campus/network-twin")
    assert landing["ok"] is True
    run = parse_mlv_product_link("gunnchos://mlv/campus/network-twin/gary/run/demo-run-01")
    assert run["ok"] is True
    assert run["route_kind"] == "network_twin_run"
    assert run["ric_actuation"] is False
    shadow = parse_mlv_product_link("gunnchos://mlv/campus/network-twin/germany/shadow/demo-run-01")
    assert shadow["ok"] is True
    assert shadow["route_kind"] == "digital_shadow"
    assert shadow["actuation_mode"] == "SHADOW"


def test_waike_deeplinks_and_return_context():
    assignment = parse_waike_deep_link("waike://assignment/asg-demo-1")
    assert assignment["ok"] is True
    assert assignment["shadow_lms"] is False
    assert assignment["canonical"] == "waike://assignment/asg-demo-1"
    opened = open_waike_from_campus("gary", "assignment", "asg-demo-1")
    assert opened["ok"] is True
    assert opened["return_to"] == "gunnchos://mlv/campus/gary"
    returned = return_from_surface(opened)
    assert returned["ok"] is True
    assert returned["canonical"] == "gunnchos://mlv/campus/gary"
    study = open_waike_from_campus("ghana", "study", "lesson-demo-1")
    assert study["return_to"] == "gunnchos://mlv/campus/ghana"
    offline = open_waike_from_campus("geelong", "home", waike_available=False)
    assert offline["labeled_state"] == "OFFLINE DEMO"
    assert offline["fabricate_live_connectivity"] is False


def test_waike_contract_pin_and_readiness_truth():
    contract = load_waike_contract()
    assert contract["consumed_from"]["waike_head"] == WAIKE_PR25_HEAD
    assert contract["consumer_summary"]["endpoint"] == "/api/v1/mlv/consumer-summary"
    truth = waike_readiness_truth()
    assert truth["ready"] == 16
    assert truth["partial"] == 2
    assert truth["partial_ids"] == ["DIGITAL_CONFIDENCE", "IT_SUPPORT_HARDWARE"]
    assert truth["upgraded_to_18_ready"] is False
    assert truth["NO_SHADOW_LMS_PASS"] is True
    assert "answer_keys" in contract["must_not_expose"]


def test_network_twin_return_and_no_ric_actuation():
    opened = open_network_twin("guyana", "demo-run-01")
    assert opened["ok"] is True
    assert opened["return_to"] == "gunnchos://mlv/campus/guyana"
    assert opened["holds_e2_credentials"] is False
    returned = return_from_surface(opened)
    assert returned["canonical"] == "gunnchos://mlv/campus/guyana"
    shadow = open_network_twin("germany", "demo-run-01", shadow=True, role="planner")
    assert shadow["route_kind"] == "digital_shadow"
    degraded = open_network_twin("gaza", backend_available=False)
    assert degraded["labeled_state"] == "SYNTHETIC"
    assert degraded["live_ric_wording"] is False
    policy = actuation_policy()
    assert policy["REAL_ACTUATION_ENABLED"] is False
    assert REAL_ACTUATION_ENABLED is False
    assert parse_mlv_product_link("gunnchos://mlv/campus/network-twin/gary/production")["reason"] == (
        "ric_actuation_rejected"
    )
    assert validate_intent(
        {
            "intent_version": "v2",
            "target_app": "mlv_world_workspace",
            "route_kind": "network_twin",
            "actuation_mode": "PRODUCTION",
        }
    )["reason"] == "ric_actuation_rejected"


def test_privacy_home_gallery_gaza_graham_and_join():
    home = parse_mlv_product_link("gunnchos://mlv/home")
    assert home["visibility_context"] == "private"
    assert validate_intent(
        {
            "intent_version": "v2",
            "target_app": "mlv_world_workspace",
            "route_kind": "home",
            "visibility_context": "public",
        }
    )["reason"] == "privilege_escalation_rejected"
    gaza_ok = parse_mlv_product_link("gunnchos://mlv/campus/gaza")
    assert gaza_ok["ok"] is True
    assert gaza_ok["campus_truth"]["precise_protected_location"] is False
    assert parse_mlv_product_link("gunnchos://mlv/campus/gaza?lat=31.5&lon=34.4")["reason"] == (
        "gaza_precise_location_rejected"
    )
    assert parse_mlv_product_link("gunnchos://mlv/campus/gaza/public-vulnerability")["reason"] == (
        "gaza_route_redaction"
    )
    graham = parse_mlv_product_link("gunnchos://mlv/campus/graham_land")
    assert graham["ok"] is True
    assert graham["campus_truth"]["fake_waike_station"] is False
    assert graham["campus_truth"]["ownership_implied"] is False
    assert open_waike_from_campus("graham_land", "lab", "owned_station")["reason"] == "graham_truth_rejected"
    assert learning_telemetry_join_state(
        {"grades": "A", "signal_telemetry": {"rsrp": -90}}
    )["NO_LEARNING_TELEMETRY_JOIN_PASS"] is False
    assert learning_telemetry_join_state({"campus_id": "gary"})["NO_LEARNING_TELEMETRY_JOIN_PASS"] is True
    assert parse_mlv_product_link(f"gunnchos://mlv/campus?token={SHARE_TOKEN}")["ok"] is False


def test_roles_do_not_invent_physical_radio():
    learner = authorize_role("learner", "network_twin_run")
    assert learner["allowed"] is True
    assert learner["physical_control"] is False
    planner = authorize_role("planner", "digital_shadow")
    assert planner["may_approve_digital_shadow"] is True
    assert planner["physical_radio_permission"] is False
    admin = authorize_role("admin", "network_twin")
    assert admin["physical_ric_authority"] is False
    blocked = authorize_role("admin", "network_twin", "PRODUCTION")
    assert blocked["allowed"] is False


def test_intent_schema_rejects_unknown_and_tokens():
    good = validate_intent(
        {
            "intent_version": "v2",
            "target_app": "mlv_world_workspace",
            "route_kind": "campus_site",
            "campus_id": "gary",
            "return_to": "gunnchos://mlv/campus",
            "visibility_context": "campus",
            "role": "learner",
        }
    )
    assert good["ok"] is True
    assert validate_intent(
        {
            "intent_version": "v2",
            "target_app": "mlv_world_workspace",
            "route_kind": "mystery",
        }
    )["reason"] == "unknown_route_kind"
    assert validate_intent(
        {
            "intent_version": "v2",
            "target_app": "mlv_world_workspace",
            "route_kind": "campus",
            "campus_id": "atlantis",
        }
    )["reason"] == "unsupported_campus_id"
    assert validate_intent(
        {
            "intent_version": "v2",
            "target_app": "mlv_world_workspace",
            "route_kind": "home",
            "token": SHARE_TOKEN,
        }
    )["reason"] == "secrets_in_fields_rejected"


def test_one_mlv_app_not_seven_campus_apps():
    app = get_app("mlv_world_workspace")
    assert app["name"] == "My Little Vicinity"
    assert app["default_visibility"] == "private"
    assert app["subroute_policy"] == "one_mlv_app_not_seven_campus_apps"
    names = set(list_apps())
    for campus in CANONICAL_CAMPUSES:
        assert campus not in names
        assert f"campus_{campus}" not in names
    assert "waike_learning_os" in list_apps("education")
    assert get_app("waike_learning_os")["role"] == "canonical_learning_os"


def test_journey_preset_policy_not_weakened():
    assert journey_preset_access("studio")["allowed"] is True
    assert journey_preset_access("offline")["posture"] == "cached owner subset only"
    assert journey_preset_access("library")["private_nodes"] is False
    assert journey_preset_access("guardian")["allowed"] is False
    assert journey_preset_access("classroom")["allowed"] is False
    assert journey_preset_access("scooter")["allowed"] is False


def test_journey_matrix_and_gates_artifacts():
    matrix = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    generated = build_journey_matrix()
    assert matrix["rows"] == generated["rows"]
    names = {row["name"] for row in matrix["rows"]}
    assert "Home private artifact" in names
    assert "Campus landing" in names
    assert "WAIKE summary" in names
    assert "WAIKE assignment deep link" in names
    assert "WAIKE study deep link" in names
    assert "Network Twin landing" in names
    assert "Network Twin run" in names
    assert "Digital shadow recommendation" in names
    assert "Gallery" in names
    assert "Offline WAIKE degraded" in names
    assert "Offline Network Twin degraded" in names
    for campus in CANONICAL_CAMPUSES:
        assert f"Campus {campus}" in names
        assert f"Network Twin {campus}" in names
    for row in matrix["rows"]:
        assert row["human_status"] is False
        assert row["pixel_status"] is False
    gates = json.loads(GATES_PATH.read_text(encoding="utf-8"))
    expected = convergence_gates()
    assert gates["gates"] == expected
    assert gates["gates"]["HUMAN_CONVERGENCE_USABILITY_PASS"] is False
    assert gates["gates"]["PIXEL_CONVERGENCE_PASS"] is False
    assert gates["gates"]["MERGE_AUTHORIZED"] is False
    assert gates["gates"]["GUNNCHOS_7GC_ROUTE_PASS"] == "7/7"
    assert gates["gates"]["GUNNCHOS_NETWORK_TWIN_DEEPLINK_PASS"] == "7/7"
