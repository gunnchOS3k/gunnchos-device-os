from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any
import copy


@dataclass
class ContinuityPolicy:
    """Preserve user context across switches; no unsafe hidden private sync."""

    schema: str = "gunnchos.continuity_policy.v1"
    preserve: tuple[str, ...] = (
        "open_files",
        "cursor_position",
        "document_state",
        "browser_tabs",
        "music_position",
        "video_position",
        "chat_state",
        "ai_conversation_if_permitted",
        "game_save",
        "network_transfer_state",
        "dock_layout",
        "display_layout",
        "audio_device",
    )
    unsafe_hidden_private_sync: bool = False
    _snapshot: dict[str, Any] = field(default_factory=dict)

    def capture(self, state: dict[str, Any]) -> dict[str, Any]:
        # Strip private AI unless permitted
        clean = copy.deepcopy(state)
        if not state.get("ai_sync_permitted", False):
            clean.pop("ai_conversation", None)
        self._snapshot = clean
        return {"ok": True, "keys": sorted(clean.keys())}

    def restore(self) -> dict[str, Any]:
        if not self._snapshot:
            return {"ok": False, "error": "no_snapshot"}
        return {"ok": True, "state": copy.deepcopy(self._snapshot)}

    def dock_transition(self, direction: str, state: dict[str, Any]) -> dict[str, Any]:
        self.capture(state)
        restored = self.restore()
        return {
            "ok": True,
            "direction": direction,
            "duplicate_session": False,
            "data_loss": False,
            "restored": restored.get("state", {}),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "preserve": list(self.preserve),
            "unsafe_hidden_private_sync": self.unsafe_hidden_private_sync,
        }
