"""CX2D truth tokens — fail closed unless Linux GUI evidence is proven."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict


@dataclass
class Cx2dTokens:
    CX2D_SINGLE_PRODUCTION_SHELL_AUTHORITY: bool = True
    CX2D_REAL_HOME_WINDOW: bool = False
    CX2D_REAL_VAULT_WINDOW: bool = False
    CX2D_REAL_APP_CENTER_WINDOW: bool = False
    CX2D_REAL_CONNECT_WINDOW: bool = False
    CX2D_REAL_ASSIST_WINDOW: bool = False
    CX2D_REAL_CARE_WINDOW: bool = False
    CX2D_REAL_BROWSER_GUI_PASS: bool = False
    CX2D_REAL_APP_LIFECYCLE_GUI_PASS: bool = False
    CX2D_REAL_PRODUCTIVITY_GUI_PASS: bool = False
    CX2D_REAL_MAIL_GUI_PASS: bool = False
    CX2D_REAL_CALDAV_CARDDAV_GUI_PASS: bool = False
    CX2D_REAL_IPP_GUI_DIGITAL_PASS: bool = False
    CX2D_REAL_XDG_PORTAL_PASS: bool = False
    CX2D_REAL_SCREEN_CAPTURE_PASS: bool = False
    CX2D_DIGITAL_RENDERED_A11Y_PASS: bool = False
    CX2D_REAL_OFFLINE_RECOVERY_GUI_PASS: bool = False
    CX2D_HUMAN_A11Y_PENDING: bool = True
    CX2D_PHYSICAL_PRINTER_PENDING: bool = True
    CX2D_HUMAN_AV_QUALITY_PENDING: bool = True
    CX2D_PHYSICAL_CAMERA_MIC_PENDING: bool = True
    CX2D_DEVICE_LAB_134_UNALTERED: bool = True
    CX2D_PORTAL_14_UNALTERED: bool = True
    CX2D_PORTAL_15_UNALTERED: bool = True
    CX2D_DEVICE_LAB_MANIFEST_UNALTERED: bool = True
    CX2D_NO_MERGES: bool = True
    FULL_COMPLETE_EXPERIENCE_COMPLETE: bool = False
    lab_blocker: str = ""
    notes: str = ""

    def as_env_lines(self) -> str:
        lines = []
        for k, v in asdict(self).items():
            if k in ("lab_blocker", "notes"):
                continue
            if isinstance(v, bool):
                lines.append(f"{k}={'true' if v else 'false'}")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def fail_closed_tokens(*, lab_blocker: str = "", **overrides) -> Cx2dTokens:
    t = Cx2dTokens(lab_blocker=lab_blocker)
    for k, v in overrides.items():
        if hasattr(t, k):
            setattr(t, k, v)
    return t
