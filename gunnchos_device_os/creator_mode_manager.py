"""Creator mode manager — artist, writer, musician workflows."""
from __future__ import annotations

from typing import Any

CREATOR_WORKFLOWS: dict[str, dict[str, Any]] = {
    "artist": {
        "default_workspace": "art_table",
        "app_pack": "art_pack",
        "file_templates": ["sketch.canvas", "palette.gpalette"],
        "export_formats": ["png", "svg", "pdf"],
        "collaboration": ["share_link_placeholder"],
        "offline_support": True,
    },
    "writer": {
        "default_workspace": "essay_studio",
        "app_pack": "write_pack",
        "file_templates": ["essay.md", "outline.md"],
        "export_formats": ["md", "docx", "pdf"],
        "collaboration": ["comment_placeholder"],
        "offline_support": True,
    },
    "musician": {
        "default_workspace": "music_studio",
        "app_pack": "music_pack",
        "file_templates": ["song.project", "notes.txt"],
        "export_formats": ["wav", "mp3", "midi"],
        "collaboration": ["jam_session_placeholder"],
        "offline_support": True,
    },
    "video_creator": {
        "default_workspace": "art_table",
        "app_pack": "art_pack",
        "file_templates": ["storyboard.md", "clip.project"],
        "export_formats": ["mp4", "webm"],
        "collaboration": ["review_link_placeholder"],
        "offline_support": False,
    },
    "game_designer": {
        "default_workspace": "coding_lab",
        "app_pack": "game_dev_pack",
        "file_templates": ["game.design", "level.tmx"],
        "export_formats": ["json", "zip"],
        "collaboration": ["playtest_placeholder"],
        "offline_support": True,
    },
    "photographer": {
        "default_workspace": "art_table",
        "app_pack": "art_pack",
        "file_templates": ["album.album"],
        "export_formats": ["jpg", "raw", "png"],
        "collaboration": ["gallery_placeholder"],
        "offline_support": True,
    },
    "streamer": {
        "default_workspace": "game_room",
        "app_pack": "game_pack",
        "file_templates": ["stream.overlay"],
        "export_formats": ["mp4"],
        "collaboration": ["chat_moderation_placeholder"],
        "offline_support": False,
    },
}


def list_creator_modes() -> list[str]:
    return list(CREATOR_WORKFLOWS.keys())


def get_creator_workflow(mode: str) -> dict[str, Any]:
    if mode not in CREATOR_WORKFLOWS:
        raise ValueError(f"Unknown creator mode: {mode}")
    return {"mode": mode, **CREATOR_WORKFLOWS[mode]}
