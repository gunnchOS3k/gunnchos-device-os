"""Shell contract APIs for gunnchShell Stage 2."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from gunnchos_device_os.stage2.shell.profiles import AdaptiveProfile, ProfileManager


COMPOSITOR_FOUNDATION = "weston"


@dataclass
class ShellAPI:
    """Named contract surfaces — digitally exercised, not a full GUI."""

    launcher: dict[str, Any] = field(default_factory=dict)
    window_management: dict[str, Any] = field(default_factory=dict)
    quick_settings: dict[str, Any] = field(default_factory=dict)
    notifications: list[dict[str, Any]] = field(default_factory=list)
    media: dict[str, Any] = field(default_factory=dict)
    search: dict[str, Any] = field(default_factory=dict)
    file_share: dict[str, Any] = field(default_factory=dict)
    session: dict[str, Any] = field(default_factory=dict)
    display_topology: list[dict[str, Any]] = field(default_factory=list)
    input_modality: list[str] = field(default_factory=list)
    dock_state: dict[str, Any] = field(default_factory=dict)
    device_role: str = "unknown"
    accessibility: dict[str, Any] = field(default_factory=dict)


class ShellContract:
    def __init__(self, profile: AdaptiveProfile = AdaptiveProfile.STUDENT_DESKTOP):
        self.profiles = ProfileManager(profile)
        self.api = ShellAPI()
        self.compositor = COMPOSITOR_FOUNDATION
        self._sync_from_profile()

    def _sync_from_profile(self) -> None:
        cfg = self.profiles.current
        from gunnchos_device_os.stage2.shell.profiles import PROFILE_TABLE

        p = PROFILE_TABLE[cfg]
        self.api.device_role = p.device_role
        self.api.input_modality = list(p.input_modality)
        self.api.dock_state = {"connected": p.docked}
        self.api.display_topology = list(self.profiles.displays)
        self.api.session = {
            "compositor": self.compositor,
            "profile": p.profile.value,
            "chrome": p.chrome,
        }
        self.api.window_management = {"mode": p.window_mode}
        self.api.launcher = {"density": p.launcher_density, "open": False}
        self.api.quick_settings = {"wifi": True, "bluetooth": True, "brightness": 80}
        self.api.media = {"playing": False, "title": None}
        self.api.search = {"query": "", "results": []}
        self.api.file_share = {"pending": []}
        self.api.accessibility = {
            "screen_reader": False,
            "high_contrast": False,
            "reduce_motion": False,
        }

    # --- contract methods ---
    def open_launcher(self) -> dict[str, Any]:
        self.api.launcher["open"] = True
        return self.api.launcher

    def manage_window(self, action: str, window_id: str = "app1") -> dict[str, Any]:
        self.api.window_management["last_action"] = {"action": action, "id": window_id}
        return self.api.window_management

    def set_quick_setting(self, key: str, value: Any) -> dict[str, Any]:
        self.api.quick_settings[key] = value
        return self.api.quick_settings

    def notify(self, title: str, body: str = "") -> dict[str, Any]:
        n = {"id": len(self.api.notifications) + 1, "title": title, "body": body}
        self.api.notifications.append(n)
        return n

    def media_control(self, action: str, title: str | None = None) -> dict[str, Any]:
        if action == "play":
            self.api.media = {"playing": True, "title": title or "track"}
        elif action == "pause":
            self.api.media["playing"] = False
        elif action == "stop":
            self.api.media = {"playing": False, "title": None}
        return self.api.media

    def search(self, query: str) -> dict[str, Any]:
        self.api.search = {
            "query": query,
            "results": [{"title": f"Result for {query}", "score": 1.0}] if query else [],
        }
        return self.api.search

    def file_share_action(self, path: str, action: str = "share") -> dict[str, Any]:
        item = {"path": path, "action": action}
        self.api.file_share["pending"].append(item)
        return item

    def session_info(self) -> dict[str, Any]:
        return dict(self.api.session)

    def set_accessibility(self, **kwargs: Any) -> dict[str, Any]:
        self.api.accessibility.update(kwargs)
        return self.api.accessibility

    def apply_profile(self, profile: AdaptiveProfile) -> dict[str, Any]:
        self.profiles.apply(profile)
        self._sync_from_profile()
        return self.session_info()

    def run_transition(self, steps: list[str]) -> list[dict[str, Any]]:
        log = self.profiles.transition_sequence(steps)
        self._sync_from_profile()
        return log

    def snapshot(self) -> dict[str, Any]:
        return {
            "compositor": self.compositor,
            "profile": self.profiles.current.value,
            "api": {
                "launcher": self.api.launcher,
                "window_management": self.api.window_management,
                "quick_settings": self.api.quick_settings,
                "notifications": self.api.notifications,
                "media": self.api.media,
                "search": self.api.search,
                "file_share": self.api.file_share,
                "session": self.api.session,
                "display_topology": self.api.display_topology,
                "input_modality": self.api.input_modality,
                "dock_state": self.api.dock_state,
                "device_role": self.api.device_role,
                "accessibility": self.api.accessibility,
            },
        }
