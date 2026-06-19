"""Dock manager stub — EVT-1 alpha."""
def dock_state(connected: bool = False) -> dict:
    return {"docked": connected, "external_display": connected, "performance": "docked_performance" if connected else "balanced"}
