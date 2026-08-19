"""Device-aware shell UI profiles (Wave 002 / OS-PLATFORM-003)."""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any

from gunnchos_device_os.display_manager import DeviceSurface, DisplayManager
from gunnchos_device_os.stage2.shell.contract import ShellContract
from gunnchos_device_os.stage2.shell.profiles import AdaptiveProfile


WAVE002_FORM_FACTORS = (
    "student_14_5",
    "handheld",
    "docked",
    "ds_xl",
    "phone",
    "desktop",
)

FORM_FACTOR_TO_ADAPTIVE: dict[str, AdaptiveProfile] = {
    "student_14_5": AdaptiveProfile.STUDENT_DESKTOP,
    "handheld": AdaptiveProfile.HANDHELD_GAMEPAD,
    "docked": AdaptiveProfile.HANDHELD_DOCKED,
    "ds_xl": AdaptiveProfile.DSXL_DUAL_SCREEN,
    "phone": AdaptiveProfile.TOUCH_TABLET,
    "desktop": AdaptiveProfile.OFFICE_DOCKED,
}

FORM_FACTOR_TO_DISPLAY: dict[str, str] = {
    "student_14_5": DeviceSurface.STUDENT_14_5.value,
    "handheld": DeviceSurface.HANDHELD_HYBRID.value,
    "docked": DeviceSurface.DOCK.value,
    "ds_xl": DeviceSurface.DS_XL_CODER.value,
    "phone": DeviceSurface.HANDHELD_HYBRID.value,
    "desktop": DeviceSurface.DS_XL_CODER.value,
}


@dataclass
class ShellProfileService:
    display: DisplayManager = field(default_factory=DisplayManager)
    shell: ShellContract = field(default_factory=lambda: ShellContract(AdaptiveProfile.HANDHELD_GAMEPAD))
    active_form_factor: str = "handheld"
    history: list[dict[str, Any]] = field(default_factory=list)

    def apply_form_factor(self, form_factor: str) -> dict[str, Any]:
        if form_factor not in WAVE002_FORM_FACTORS:
            raise ValueError(f"unknown form factor: {form_factor}")
        adaptive = FORM_FACTOR_TO_ADAPTIVE[form_factor]
        display_surface = FORM_FACTOR_TO_DISPLAY[form_factor]
        self.shell.apply_profile(adaptive)
        display_event = self.display.apply_surface(display_surface)
        self.active_form_factor = form_factor
        row = {
            "form_factor": form_factor,
            "adaptive_profile": adaptive.value,
            "display_surface": display_surface,
            "input_modality": list(self.shell.api.input_modality),
            "display_topology": list(self.shell.api.display_topology),
            "display_event": display_event,
            "session": self.shell.session_info(),
        }
        self.history.append(row)
        return row

    def list_profiles(self) -> list[str]:
        return list(WAVE002_FORM_FACTORS)

    def status(self) -> dict[str, Any]:
        return {
            "active_form_factor": self.active_form_factor,
            "profiles": self.list_profiles(),
            "display": self.display.status(),
            "shell_snapshot": self.shell.snapshot(),
        }

    def to_dict(self) -> dict[str, Any]:
        return asdict(self) if False else self.status()  # status is JSON-safe
