"""Execution-depth classification for journey steps."""
from __future__ import annotations

from typing import Any

# Default depth for Phase XI handlers before Phase XII replacement
PHASE_XI_DEFAULT_DEPTH: dict[str, str] = {
    # L0 generic ok / synthetic
    "wake": "L0_GENERIC_OK",
    "auth": "L1_POLICY_MODEL",
    "browser": "L0_GENERIC_OK",
    "game_play": "L0_GENERIC_OK",
    "game_control": "L0_GENERIC_OK",
    "invite_members": "L0_GENERIC_OK",
    "vpn_connect": "L0_GENERIC_OK",
    "vpn_flap": "L0_GENERIC_OK",
    "print_virtual_pdf": "L0_GENERIC_OK",
    "cups_submit": "L0_GENERIC_OK",
    "waike_search": "L0_GENERIC_OK",
    "waike_open": "L0_GENERIC_OK",
    "ai_capability": "L0_GENERIC_OK",
    "ai_pending": "L0_GENERIC_OK",
    # L1 policy
    "focus_mode_enable": "L1_POLICY_MODEL",
    "memory_pressure": "L1_POLICY_MODEL",
    "audio_focus_policy": "L1_POLICY_MODEL",
    "low_battery_warn": "L1_POLICY_MODEL",
    "storage_pressure": "L1_POLICY_MODEL",
    "multitask_stack": "L1_POLICY_MODEL",
    "block_game_notify": "L1_POLICY_MODEL",
    "mute_noncritical": "L1_POLICY_MODEL",
    "notify": "L1_POLICY_MODEL",
    "notify_receive": "L1_POLICY_MODEL",
    "notify_no_audio_kill": "L1_POLICY_MODEL",
    "session_preserve": "L1_POLICY_MODEL",
    "state_preserve": "L1_POLICY_MODEL",
    "dock": "L1_POLICY_MODEL",
    "undock": "L1_POLICY_MODEL",
    # L2 HTTP protocol simulation
    "lms_open": "L2_PROTOCOL_SIMULATION",
    "lms_upload": "L2_PROTOCOL_SIMULATION",
    "email": "L2_PROTOCOL_SIMULATION",
    "calendar": "L2_PROTOCOL_SIMULATION",
    "calendar_reminder": "L2_PROTOCOL_SIMULATION",
    "message_send": "L2_PROTOCOL_SIMULATION",
    "class_message": "L2_PROTOCOL_SIMULATION",
    "chat": "L2_PROTOCOL_SIMULATION",
    "messaging": "L2_PROTOCOL_SIMULATION",
    "share_folder": "L2_PROTOCOL_SIMULATION",
    "share_link": "L2_PROTOCOL_SIMULATION",
    "share_verify": "L2_PROTOCOL_SIMULATION",
    "share_pdf": "L2_PROTOCOL_SIMULATION",
    "share_files": "L2_PROTOCOL_SIMULATION",
    "share_final": "L2_PROTOCOL_SIMULATION",
    "webrtc_call": "L2_PROTOCOL_SIMULATION",
    "screen_share": "L2_PROTOCOL_SIMULATION",
    "sync_file": "L2_PROTOCOL_SIMULATION",
    "sync_exchange": "L2_PROTOCOL_SIMULATION",
    "flush_queue": "L2_PROTOCOL_SIMULATION",
    "ring_sim_connect": "L2_PROTOCOL_SIMULATION",
    "ring_sim_input": "L2_PROTOCOL_SIMULATION",
    "gesture_packet": "L2_PROTOCOL_SIMULATION",
    "mdm_policy": "L2_PROTOCOL_SIMULATION",
    "push_config": "L2_PROTOCOL_SIMULATION",
    # L0/L1 document in-memory
    "doc_create": "L0_GENERIC_OK",
    "doc_edit": "L0_GENERIC_OK",
    "doc_open": "L0_GENERIC_OK",
    "docx_edit": "L0_GENERIC_OK",
    "docx_open": "L0_GENERIC_OK",
    "xlsx_edit": "L0_GENERIC_OK",
    "pptx_edit": "L0_GENERIC_OK",
    "pptx_open": "L0_GENERIC_OK",
    "pdf_open": "L0_GENERIC_OK",
    "pdf_download": "L2_PROTOCOL_SIMULATION",
    "pdf_export": "L0_GENERIC_OK",
    "music_study": "L1_POLICY_MODEL",
    "music_continue": "L1_POLICY_MODEL",
    "video_local": "L1_POLICY_MODEL",
    "ai_tutor": "L0_GENERIC_OK",
    "ai_privacy_gate": "L1_POLICY_MODEL",
    "ai_code_help": "L0_GENERIC_OK",
    "ai_explain": "L0_GENERIC_OK",
    "ai_summarize": "L0_GENERIC_OK",
    "game_launch": "L0_GENERIC_OK",
    "game_save": "L0_GENERIC_OK",
    "game_break": "L0_GENERIC_OK",
    "beatlink_launch": "L0_GENERIC_OK",
    "archive_launch": "L0_GENERIC_OK",
}

# Phase XII target depths for key user-facing actions
PHASE_XII_TARGET_DEPTH: dict[str, str] = {
    "browser": "L5_REAL_GUI_INTERACTION",
    "lms_open": "L5_REAL_GUI_INTERACTION",
    "lms_upload": "L5_REAL_GUI_INTERACTION",
    "pdf_download": "L4_REAL_APPLICATION_PROCESS",
    "pdf_open": "L5_REAL_GUI_INTERACTION",
    "doc_create": "L4_REAL_APPLICATION_PROCESS",
    "doc_edit": "L4_REAL_APPLICATION_PROCESS",
    "doc_open": "L4_REAL_APPLICATION_PROCESS",
    "docx_edit": "L4_REAL_APPLICATION_PROCESS",
    "xlsx_edit": "L4_REAL_APPLICATION_PROCESS",
    "pptx_edit": "L4_REAL_APPLICATION_PROCESS",
    "pdf_export": "L4_REAL_APPLICATION_PROCESS",
    "email": "L4_REAL_APPLICATION_PROCESS",
    "calendar": "L3_REAL_SERVICE_API",
    "message_send": "L3_REAL_SERVICE_API",
    "messaging": "L3_REAL_SERVICE_API",
    "chat": "L3_REAL_SERVICE_API",
    "class_message": "L3_REAL_SERVICE_API",
    "share_folder": "L3_REAL_SERVICE_API",
    "share_link": "L3_REAL_SERVICE_API",
    "share_verify": "L3_REAL_SERVICE_API",
    "webrtc_call": "L5_REAL_GUI_INTERACTION",
    "screen_share": "L5_REAL_GUI_INTERACTION",
    "ai_tutor": "L4_REAL_APPLICATION_PROCESS",
    "ai_code_help": "L4_REAL_APPLICATION_PROCESS",
    "ai_explain": "L4_REAL_APPLICATION_PROCESS",
    "ai_summarize": "L4_REAL_APPLICATION_PROCESS",
    "game_launch": "L4_REAL_APPLICATION_PROCESS",
    "game_save": "L4_REAL_APPLICATION_PROCESS",
    "game_break": "L4_REAL_APPLICATION_PROCESS",
    "game_play": "L4_REAL_APPLICATION_PROCESS",
    "beatlink_launch": "L5_REAL_GUI_INTERACTION",
    "archive_launch": "L4_REAL_APPLICATION_PROCESS",
    "music_study": "L4_REAL_APPLICATION_PROCESS",
    "video_local": "L4_REAL_APPLICATION_PROCESS",
    "waike_open": "L4_REAL_APPLICATION_PROCESS",
    "waike_search": "L4_REAL_APPLICATION_PROCESS",
    "print_virtual_pdf": "L4_REAL_APPLICATION_PROCESS",
    "cups_submit": "L4_REAL_APPLICATION_PROCESS",
    "vpn_connect": "L4_REAL_APPLICATION_PROCESS",
    "ring_sim_input": "L4_REAL_APPLICATION_PROCESS",
    "gesture_packet": "L4_REAL_APPLICATION_PROCESS",
    "terminal": "L4_REAL_APPLICATION_PROCESS",
    "ide_open": "L4_REAL_APPLICATION_PROCESS",
    "run_tests": "L4_REAL_APPLICATION_PROCESS",
    "git_commit": "L4_REAL_APPLICATION_PROCESS",
    "creator_tools": "L4_REAL_APPLICATION_PROCESS",
    "navigate_launcher": "L5_REAL_GUI_INTERACTION",
    "a11y_enable": "L5_REAL_GUI_INTERACTION",
    "kb_nav": "L5_REAL_GUI_INTERACTION",
}


def classify_action(action: str, *, phase: str = "xi") -> str:
    if phase == "xii" and action in PHASE_XII_TARGET_DEPTH:
        return PHASE_XII_TARGET_DEPTH[action]
    if action in PHASE_XI_DEFAULT_DEPTH:
        return PHASE_XI_DEFAULT_DEPTH[action]
    # Phase XI generic handler list → L0
    return "L0_GENERIC_OK"


def depth_rank(level: str) -> int:
    order = {
        "L0_GENERIC_OK": 0,
        "L1_POLICY_MODEL": 1,
        "L2_PROTOCOL_SIMULATION": 2,
        "L3_REAL_SERVICE_API": 3,
        "L4_REAL_APPLICATION_PROCESS": 4,
        "L5_REAL_GUI_INTERACTION": 5,
        "L6_REAL_CROSS_APP_END_TO_END": 6,
        "L7_PHYSICAL_DEVICE": 7,
    }
    return order.get(level, 0)


def journey_min_depth(steps: list[dict[str, Any]], *, phase: str = "xi") -> str:
    if not steps:
        return "L0_GENERIC_OK"
    infra = {
        "wake", "auth", "wifi_campus", "wifi_home", "wifi_switch", "ethernet",
        "net_loss", "net_restore", "go_offline", "campus_net_fail",
    }
    key_names = {
        "browser", "lms_open", "doc_edit", "docx_edit", "xlsx_edit", "pptx_edit",
        "email", "message_send", "game_launch", "ai_tutor", "webrtc_call",
        "waike_open", "beatlink_launch", "archive_launch", "pdf_open", "share_folder",
        "music_study", "creator_tools", "ide_open",
    }
    key = []
    for s in steps:
        a = s.get("action", "")
        if a in infra:
            continue
        if a in key_names or phase == "xi":
            key.append(depth_rank(classify_action(a, phase=phase)))
    use = key or [0]
    mn = min(use)
    for name, r in [
        ("L0_GENERIC_OK", 0), ("L1_POLICY_MODEL", 1), ("L2_PROTOCOL_SIMULATION", 2),
        ("L3_REAL_SERVICE_API", 3), ("L4_REAL_APPLICATION_PROCESS", 4),
        ("L5_REAL_GUI_INTERACTION", 5), ("L6_REAL_CROSS_APP_END_TO_END", 6),
        ("L7_PHYSICAL_DEVICE", 7),
    ]:
        if r == mn:
            return name
    return "L0_GENERIC_OK"


def key_steps_meet(steps: list[dict[str, Any]], min_level: str = "L4_REAL_APPLICATION_PROCESS") -> bool:
    need = depth_rank(min_level)
    key_actions = {
        "browser", "lms_open", "doc_edit", "docx_edit", "xlsx_edit", "pptx_edit",
        "email", "message_send", "game_launch", "ai_tutor", "webrtc_call",
        "waike_open", "beatlink_launch", "archive_launch", "pdf_open",
    }
    relevant = [s for s in steps if s.get("action") in key_actions]
    if not relevant:
        return False
    return all(depth_rank(classify_action(s["action"], phase="xii")) >= need for s in relevant)
