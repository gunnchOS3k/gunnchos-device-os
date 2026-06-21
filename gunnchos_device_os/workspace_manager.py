"""Workspace manager — focused layouts for tasks."""
from __future__ import annotations

from typing import Any

from .user_config_loader import load_workspaces


def list_workspaces() -> list[str]:
    return list(load_workspaces().get("workspaces", {}).keys())


def get_workspace(workspace_id: str) -> dict[str, Any]:
    workspaces = load_workspaces().get("workspaces", {})
    if workspace_id not in workspaces:
        raise ValueError(f"Unknown workspace: {workspace_id}")
    return {"id": workspace_id, **workspaces[workspace_id]}
