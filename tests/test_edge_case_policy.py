"""Tests for edge case policy."""
from gunnchos_device_os.edge_case_policy import handle_edge_case, list_edge_cases


def test_edge_cases_have_messages():
    for case_id in list_edge_cases():
        result = handle_edge_case(case_id)
        assert result["user_message"]
        assert result["safe_fallback"]
        assert result["technical_log"]
        assert result["next_action"]


def test_steam_unavailable():
    result = handle_edge_case("steam_unavailable")
    assert "steam" in result["user_message"].lower() or result["safe_fallback"]
