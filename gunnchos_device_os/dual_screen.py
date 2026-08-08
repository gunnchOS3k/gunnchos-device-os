"""Dual-screen framework API for DS-XL top/bottom roles.

Software window/role assignment model for dual surfaces. Not a compositor
and not a claim of dual-screen OS shell proven on hardware.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any


CLAIM_BOUNDARY = (
    "Software dual-screen role framework only. Not a Wayland/X11 compositor "
    "and not a claim that dual-screen OS shell is proven on hardware."
)


class ScreenId(str, Enum):
    TOP = "top"
    BOTTOM = "bottom"


class ScreenRole(str, Enum):
    CODE = "code"
    PREVIEW = "preview"
    TERMINAL = "terminal"
    DOCS = "docs"
    DEBUG = "debug"
    CHAT = "chat"
    EMPTY = "empty"


class Orientation(str, Enum):
    TOP_BOTTOM = "top_bottom"
    BOTTOM_TOP = "bottom_top"  # swapped roles orientation label


DEFAULT_WORKFLOWS: dict[str, dict[str, ScreenRole]] = {
    "coder": {ScreenId.TOP.value: ScreenRole.CODE, ScreenId.BOTTOM.value: ScreenRole.PREVIEW},
    "debug": {ScreenId.TOP.value: ScreenRole.CODE, ScreenId.BOTTOM.value: ScreenRole.DEBUG},
    "docs": {ScreenId.TOP.value: ScreenRole.DOCS, ScreenId.BOTTOM.value: ScreenRole.CODE},
    "terminal": {ScreenId.TOP.value: ScreenRole.CODE, ScreenId.BOTTOM.value: ScreenRole.TERMINAL},
    "pair": {ScreenId.TOP.value: ScreenRole.CODE, ScreenId.BOTTOM.value: ScreenRole.CHAT},
}


@dataclass
class ScreenSurface:
    screen_id: ScreenId
    role: ScreenRole = ScreenRole.EMPTY
    app_id: str | None = None
    focused: bool = False
    width: int = 1280
    height: int = 720

    def to_dict(self) -> dict[str, Any]:
        return {
            "screen_id": self.screen_id.value,
            "role": self.role.value,
            "app_id": self.app_id,
            "focused": self.focused,
            "width": self.width,
            "height": self.height,
        }


@dataclass
class DualScreenFramework:
    """Assign and swap DS-XL top/bottom roles with workflow presets."""

    device_class: str = "ds_xl_coder"
    orientation: Orientation = Orientation.TOP_BOTTOM
    screens: dict[str, ScreenSurface] = field(default_factory=dict)
    active_workflow: str | None = None
    history: list[dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.device_class != "ds_xl_coder":
            raise ValueError(
                "dual_screen framework is defined for ds_xl_coder only "
                f"(got {self.device_class})"
            )
        if not self.screens:
            self.screens = {
                ScreenId.TOP.value: ScreenSurface(screen_id=ScreenId.TOP, focused=True),
                ScreenId.BOTTOM.value: ScreenSurface(screen_id=ScreenId.BOTTOM),
            }

    def _snapshot(self, action: str, **extra: Any) -> dict[str, Any]:
        snap = {
            "action": action,
            "orientation": self.orientation.value,
            "active_workflow": self.active_workflow,
            "screens": {k: v.to_dict() for k, v in self.screens.items()},
            **extra,
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        self.history.append(snap)
        return snap

    def list_workflows(self) -> list[str]:
        return sorted(DEFAULT_WORKFLOWS.keys())

    def get_screen(self, screen: ScreenId | str) -> ScreenSurface:
        key = screen.value if isinstance(screen, ScreenId) else screen
        if key not in self.screens:
            raise KeyError(f"unknown screen: {key}")
        return self.screens[key]

    def assign_role(
        self,
        screen: ScreenId | str,
        role: ScreenRole | str,
        *,
        app_id: str | None = None,
    ) -> dict[str, Any]:
        key = screen.value if isinstance(screen, ScreenId) else screen
        role_e = role if isinstance(role, ScreenRole) else ScreenRole(role)
        surface = self.get_screen(key)
        surface.role = role_e
        if app_id is not None:
            surface.app_id = app_id
        self.active_workflow = None  # custom assignment clears named workflow
        return self._snapshot("assign_role", screen=key, role=role_e.value, app_id=app_id)

    def focus(self, screen: ScreenId | str) -> dict[str, Any]:
        key = screen.value if isinstance(screen, ScreenId) else screen
        self.get_screen(key)  # validate
        for sid, surface in self.screens.items():
            surface.focused = sid == key
        return self._snapshot("focus", focused=key)

    def apply_workflow(self, name: str) -> dict[str, Any]:
        if name not in DEFAULT_WORKFLOWS:
            raise ValueError(f"unknown workflow: {name}")
        mapping = DEFAULT_WORKFLOWS[name]
        for sid, role in mapping.items():
            self.screens[sid].role = role
        self.active_workflow = name
        # Keep focus on top by default for coder workflows
        for sid, surface in self.screens.items():
            surface.focused = sid == ScreenId.TOP.value
        return self._snapshot("apply_workflow", workflow=name)

    def swap_screens(self) -> dict[str, Any]:
        top = self.screens[ScreenId.TOP.value]
        bottom = self.screens[ScreenId.BOTTOM.value]
        top.role, bottom.role = bottom.role, top.role
        top.app_id, bottom.app_id = bottom.app_id, top.app_id
        top.focused, bottom.focused = bottom.focused, top.focused
        self.orientation = (
            Orientation.BOTTOM_TOP
            if self.orientation == Orientation.TOP_BOTTOM
            else Orientation.TOP_BOTTOM
        )
        self.active_workflow = None
        return self._snapshot("swap_screens")

    def place_app(self, app_id: str, screen: ScreenId | str, role: ScreenRole | str) -> dict[str, Any]:
        result = self.assign_role(screen, role, app_id=app_id)
        focus_result = self.focus(screen)
        return {**result, "focus": focus_result["screens"]}

    def layout(self) -> dict[str, Any]:
        return {
            "device_class": self.device_class,
            "orientation": self.orientation.value,
            "active_workflow": self.active_workflow,
            "top": self.screens[ScreenId.TOP.value].to_dict(),
            "bottom": self.screens[ScreenId.BOTTOM.value].to_dict(),
            "workflows": self.list_workflows(),
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }

    def validate_roles(self) -> list[str]:
        """Return warnings for awkward dual-screen configurations."""
        warnings: list[str] = []
        roles = {s.role for s in self.screens.values()}
        if roles == {ScreenRole.EMPTY}:
            warnings.append("both_screens_empty")
        if all(s.role == ScreenRole.EMPTY for s in self.screens.values()):
            pass
        focused = [s for s in self.screens.values() if s.focused]
        if len(focused) != 1:
            warnings.append("focus_must_be_exactly_one")
        return warnings
