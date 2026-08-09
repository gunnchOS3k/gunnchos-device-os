from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class MediaFocusPolicy:
    """Audio focus: notifications must not destroy media sessions."""

    schema: str = "gunnchos.media_focus_policy.v1"
    duck_on_notification_db: float = -6.0
    pause_on_call: bool = True
    resume_after_call: bool = True
    ai_tts_obeys_focus: bool = True
    screen_blank_prevent_during_video: bool = True
    media_keys: tuple[str, ...] = ("play_pause", "next", "prev", "stop", "mute", "volume_up", "volume_down")
    active_session: dict[str, Any] | None = None
    position_ms: int = 0

    def start(self, kind: str, source: str) -> dict[str, Any]:
        self.active_session = {"kind": kind, "source": source, "playing": True}
        self.position_ms = 0
        return {"ok": True, "session": dict(self.active_session)}

    def media_key(self, key: str) -> dict[str, Any]:
        if key not in self.media_keys:
            return {"ok": False, "error": f"unsupported_key:{key}"}
        if not self.active_session:
            return {"ok": False, "error": "no_session"}
        if key == "play_pause":
            self.active_session["playing"] = not self.active_session.get("playing", False)
        elif key == "stop":
            self.active_session["playing"] = False
        elif key == "mute":
            self.active_session["muted"] = not self.active_session.get("muted", False)
        return {"ok": True, "session": dict(self.active_session), "key": key}

    def on_notification(self) -> dict[str, Any]:
        if not self.active_session:
            return {"ok": True, "destroyed": False}
        # Duck, never destroy
        self.active_session["ducked_db"] = self.duck_on_notification_db
        return {"ok": True, "destroyed": False, "ducked_db": self.duck_on_notification_db}

    def suspend_resume(self) -> dict[str, Any]:
        pos = self.position_ms
        return {"ok": True, "restored_position_ms": pos, "session": self.active_session}

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "duck_on_notification_db": self.duck_on_notification_db,
            "pause_on_call": self.pause_on_call,
            "resume_after_call": self.resume_after_call,
            "ai_tts_obeys_focus": self.ai_tts_obeys_focus,
            "screen_blank_prevent_during_video": self.screen_blank_prevent_during_video,
            "media_keys": list(self.media_keys),
        }
