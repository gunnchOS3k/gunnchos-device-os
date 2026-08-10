"""Adaptive shell profiles for Stage 2."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any


class AdaptiveProfile(str, Enum):
    STUDENT_DESKTOP = "STUDENT_DESKTOP"
    DSXL_DUAL_SCREEN = "DSXL_DUAL_SCREEN"
    HANDHELD_GAMEPAD = "HANDHELD_GAMEPAD"
    HANDHELD_DOCKED = "HANDHELD_DOCKED"
    OFFICE_DOCKED = "OFFICE_DOCKED"
    TOUCH_TABLET = "TOUCH_TABLET"


@dataclass
class ProfileConfig:
    profile: AdaptiveProfile
    device_role: str
    input_modality: list[str]
    chrome: str
    docked: bool = False
    dual_screen: bool = False
    launcher_density: str = "comfortable"
    window_mode: str = "floating"

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["profile"] = self.profile.value
        return d


PROFILE_TABLE: dict[AdaptiveProfile, ProfileConfig] = {
    AdaptiveProfile.STUDENT_DESKTOP: ProfileConfig(
        AdaptiveProfile.STUDENT_DESKTOP,
        device_role="desktop",
        input_modality=["keyboard", "mouse"],
        chrome="desktop",
        window_mode="floating",
    ),
    AdaptiveProfile.DSXL_DUAL_SCREEN: ProfileConfig(
        AdaptiveProfile.DSXL_DUAL_SCREEN,
        device_role="dsxl",
        input_modality=["keyboard", "touch", "stylus"],
        chrome="dual",
        dual_screen=True,
        window_mode="tiled_dual",
    ),
    AdaptiveProfile.HANDHELD_GAMEPAD: ProfileConfig(
        AdaptiveProfile.HANDHELD_GAMEPAD,
        device_role="handheld",
        input_modality=["gamepad", "touch"],
        chrome="handheld",
        launcher_density="compact",
        window_mode="fullscreen",
    ),
    AdaptiveProfile.HANDHELD_DOCKED: ProfileConfig(
        AdaptiveProfile.HANDHELD_DOCKED,
        device_role="handheld",
        input_modality=["keyboard", "mouse", "gamepad"],
        chrome="desktop",
        docked=True,
        window_mode="floating",
    ),
    AdaptiveProfile.OFFICE_DOCKED: ProfileConfig(
        AdaptiveProfile.OFFICE_DOCKED,
        device_role="laptop",
        input_modality=["keyboard", "mouse"],
        chrome="desktop",
        docked=True,
        window_mode="floating",
    ),
    AdaptiveProfile.TOUCH_TABLET: ProfileConfig(
        AdaptiveProfile.TOUCH_TABLET,
        device_role="tablet",
        input_modality=["touch", "stylus"],
        chrome="tablet",
        launcher_density="touch",
        window_mode="maximized",
    ),
}


class ProfileManager:
    def __init__(self, initial: AdaptiveProfile = AdaptiveProfile.HANDHELD_GAMEPAD):
        self.current = initial
        self.history: list[str] = [initial.value]
        self.displays: list[dict[str, Any]] = [{"id": "internal", "role": "primary"}]
        self.dock_connected = False

    def apply(self, profile: AdaptiveProfile) -> ProfileConfig:
        self.current = profile
        self.history.append(profile.value)
        cfg = PROFILE_TABLE[profile]
        self.dock_connected = cfg.docked
        return cfg

    def on_dock_attach(self, *, office: bool = False) -> ProfileConfig:
        self.dock_connected = True
        if office:
            return self.apply(AdaptiveProfile.OFFICE_DOCKED)
        return self.apply(AdaptiveProfile.HANDHELD_DOCKED)

    def on_dock_detach(self) -> ProfileConfig:
        self.dock_connected = False
        return self.apply(AdaptiveProfile.HANDHELD_GAMEPAD)

    def on_external_display(self, attached: bool) -> ProfileConfig:
        if attached:
            self.displays = [
                {"id": "internal", "role": "primary"},
                {"id": "external", "role": "secondary"},
            ]
            return self.apply(AdaptiveProfile.DSXL_DUAL_SCREEN)
        self.displays = [{"id": "internal", "role": "primary"}]
        # Return to student desktop when dual-screen drops
        return self.apply(AdaptiveProfile.STUDENT_DESKTOP)

    def transition_sequence(self, steps: list[str]) -> list[dict[str, Any]]:
        """Run named transitions for E2E tests."""
        log: list[dict[str, Any]] = []
        for step in steps:
            if step == "dock":
                cfg = self.on_dock_attach()
            elif step == "desktop":
                cfg = self.apply(AdaptiveProfile.STUDENT_DESKTOP)
            elif step == "undock":
                cfg = self.on_dock_detach()
            elif step == "office_dock":
                cfg = self.on_dock_attach(office=True)
            elif step == "external_attach":
                cfg = self.on_external_display(True)
            elif step == "external_detach":
                cfg = self.on_external_display(False)
            elif step == "tablet":
                cfg = self.apply(AdaptiveProfile.TOUCH_TABLET)
            elif step == "handheld":
                cfg = self.apply(AdaptiveProfile.HANDHELD_GAMEPAD)
            else:
                raise ValueError(f"unknown transition: {step}")
            log.append(
                {
                    "step": step,
                    "profile": cfg.profile.value,
                    "docked": cfg.docked,
                    "dual_screen": cfg.dual_screen,
                    "displays": list(self.displays),
                }
            )
        return log
