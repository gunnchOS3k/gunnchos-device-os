"""Tests for workspace manager."""
from gunnchos_device_os.workspace_manager import get_workspace, list_workspaces


def test_workspaces_have_quick_actions():
    for ws_id in list_workspaces():
        ws = get_workspace(ws_id)
        assert ws.get("quick_actions"), f"{ws_id} missing quick_actions"
