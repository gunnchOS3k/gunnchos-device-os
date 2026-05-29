DEVICES = ["student_14_5", "handheld_hybrid", "ds_xl_coder", "arena_wearables"]
MODES = ["school", "developer", "play", "research_measurement"]

def get_profile(device: str, mode: str) -> dict:
    if device not in DEVICES:
        raise ValueError(device)
    if mode not in MODES:
        raise ValueError(mode)
    return {"device": device, "mode": mode, "offline_ready": True}
