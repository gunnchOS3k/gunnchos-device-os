"""EVT-1 mode manager — prototype policy bundles."""
from __future__ import annotations

MODES = ("School", "Developer", "Play", "Media", "Research Measurement", "Admin")

MODE_POLICIES: dict[str, dict] = {
    "School": {
        "allowed_apps": ["browser", "waike_offline", "gunnchai3k", "scaly_wings_edu"],
        "blocked_apps": ["steam", "netflix", "hulu", "vscode", "terminal"],
        "telemetry": "aggregated_opt_in",
        "network": "filtered",
        "update": "admin_scheduled",
        "child_safety": "strict",
        "performance": "school",
    },
    "Developer": {
        "allowed_apps": ["vscode", "terminal", "wsl_ubuntu", "browser", "gunnchai3k"],
        "blocked_apps": ["steam"],
        "telemetry": "aggregated_opt_in",
        "network": "standard",
        "update": "user_prompt",
        "child_safety": "standard",
        "performance": "balanced",
    },
    "Play": {
        "allowed_apps": ["steam", "scaly_wings", "edgegesture", "browser"],
        "blocked_apps": [],
        "telemetry": "minimal",
        "network": "standard",
        "update": "user_prompt",
        "child_safety": "standard",
        "performance": "gaming",
    },
    "Media": {
        "allowed_apps": ["browser", "youtube", "netflix", "hulu"],
        "blocked_apps": ["steam", "vscode"],
        "telemetry": "minimal",
        "network": "standard",
        "update": "user_prompt",
        "child_safety": "standard",
        "performance": "balanced",
    },
    "Research Measurement": {
        "allowed_apps": ["field_measurement", "edge_io", "browser"],
        "blocked_apps": ["steam", "netflix"],
        "telemetry": "research_opt_in_only",
        "network": "standard",
        "update": "admin_scheduled",
        "child_safety": "strict",
        "performance": "balanced",
    },
    "Admin": {
        "allowed_apps": ["browser", "terminal", "vscode", "steam"],
        "blocked_apps": [],
        "telemetry": "audit_only",
        "network": "standard",
        "update": "immediate",
        "child_safety": "admin_override",
        "performance": "balanced",
    },
}


def get_mode_policy(mode: str) -> dict:
    if mode not in MODES:
        raise ValueError(f"Unknown mode: {mode}")
    return {"mode": mode, **MODE_POLICIES[mode]}
