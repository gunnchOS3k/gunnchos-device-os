from gunnchos_launcher.app_registry import validate_app
from gunnchos_launcher.mlv_bridge import (
    MLV_APP_NAME,
    get_recent_nodes,
    ingest_artifact_intent,
    journey_preset_access,
    launch_app_for_node,
    open_home,
    open_node,
    open_public_node,
    open_share,
    parse_mlv_deep_link,
)
from gunnchos_device_os.app_registry import get_app


NODE = "11111111-1111-4111-8111-111111111111"


def test_registry_includes_my_little_vicinity():
    assert validate_app(MLV_APP_NAME)
    app = get_app("mlv_world_workspace")
    assert app["name"] == "My Little Vicinity"
    assert app["default_visibility"] == "private"


def test_open_home_and_node_routes():
    home = open_home()
    assert home["ok"] is True
    assert home["route"] == "gunnchos://mlv/home"
    node = open_node(NODE)
    assert node["ok"] is True
    assert node["node_id"] == NODE
    public = open_public_node(NODE)
    assert public["ok"] is True
    assert parse_mlv_deep_link("gunnchos://mlv/node/not-a-uuid")["valid"] is False


def test_share_token_is_not_echoed():
    result = open_share("abcdefghijklmnopqrstuvwxyz0123")
    assert result["ok"] is True
    assert result["token_present"] is True
    assert "abcdefghijklmnopqrstuvwxyz0123" not in str(result)


def test_launch_rejects_unauthorized_private_node():
    denied = launch_app_for_node({"mime_type": "text/plain", "visibility": "private"})
    assert denied["ok"] is False
    allowed = launch_app_for_node(
        {"mime_type": "text/plain", "visibility": "private", "owner_authorized": True}
    )
    assert allowed["ok"] is True


def test_recent_nodes_prototype_empty():
    assert get_recent_nodes() == []


def test_journey_presets_do_not_weaken_youth_rules():
    assert journey_preset_access("studio")["allowed"] is True
    assert journey_preset_access("offline")["posture"] == "cached owner subset only"
    assert journey_preset_access("library")["private_nodes"] is False
    assert journey_preset_access("guardian")["allowed"] is False
    assert journey_preset_access("classroom")["allowed"] is False
    assert journey_preset_access("scooter")["allowed"] is False


def test_artifact_intent_rejects_public_default():
    bad = ingest_artifact_intent(
        {
            "artifact_id": "a",
            "owner_id": "b",
            "title": "report.pdf",
            "mime_type": "application/pdf",
            "app_id": "waike_learning_os",
            "default_visibility": "public",
        }
    )
    assert bad["ok"] is False
    good = ingest_artifact_intent(
        {
            "artifact_id": "a",
            "owner_id": "b",
            "title": "report.pdf",
            "mime_type": "application/pdf",
            "app_id": "waike_learning_os",
            "default_visibility": "private",
        }
    )
    assert good["ok"] is True
    assert good["visibility"] == "private"
    assert good["placement_room"] == "home.desk"
