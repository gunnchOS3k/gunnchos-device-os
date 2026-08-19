"""Display and dock manager with DS-XL evidence linkage (Wave 002 / OS-PLATFORM-006)."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from gunnchos_device_os.display_manager import DisplayManager, DeviceSurface
from gunnchos_device_os.dock.continuity import DockContinuityEngine


DSXL_EVIDENCE_REL = Path("artifacts/product_use/journeys/G14_dsxl/DSXL_COMPOSITOR_UX_EVIDENCE.json")


@dataclass
class DisplayDockManager:
    display: DisplayManager = field(default_factory=DisplayManager)
    dock: DockContinuityEngine = field(default_factory=DockContinuityEngine)
    repo_root: Path | None = None
    hotplug_events: list[dict[str, Any]] = field(default_factory=list)

    def _dsxl_evidence(self) -> dict[str, Any]:
        if self.repo_root is None:
            return {"present": False, "reason": "repo_root_unset"}
        path = self.repo_root / DSXL_EVIDENCE_REL
        if not path.exists():
            return {"present": False, "path": str(path)}
        data = json.loads(path.read_text(encoding="utf-8"))
        return {
            "present": True,
            "path": str(path),
            "DSXL_DUAL_COMPOSITOR_UX_PASS": data.get("DSXL_DUAL_COMPOSITOR_UX_PASS"),
            "measurement_class": data.get("compositor_info", {}).get("measurement_class"),
            "outputs": data.get("compositor_info", {}).get("detail", {}).get("wayland_info_output_globals"),
            "claim_boundary": data.get("claim_boundary"),
        }

    def topology(self) -> dict[str, Any]:
        prof = self.display.get_profile(self.display.active_surface)
        return {
            "active_surface": self.display.active_surface.value,
            "displays": prof.get("displays", []),
            "primary": prof.get("primary"),
            "docked": self.dock.docked,
            "layout_profile": self.dock.layout_profile,
            "dsxl_evidence": self._dsxl_evidence(),
        }

    def hotplug(self, *, external_attached: bool) -> dict[str, Any]:
        if external_attached:
            ev = self.display.set_docked(True)
            self.dock.attach("generic-display-dock")
        else:
            ev = self.display.apply_surface(DeviceSurface.HANDHELD_HYBRID)
            self.dock.detach(safe=True)
        row = {
            "external_attached": external_attached,
            "display_event": ev,
            "topology": self.topology(),
        }
        self.hotplug_events.append(row)
        return row

    def connect_dsxl_path(self) -> dict[str, Any]:
        """Apply DS-XL display profile and link existing guest evidence."""
        ev = self.display.apply_surface(DeviceSurface.DS_XL_CODER)
        evidence = self._dsxl_evidence()
        return {
            "display_event": ev,
            "dsxl_evidence": evidence,
            "dual_screen_modeled": True,
            "PHYSICAL_DUAL_PANEL": False,
        }

    def status(self) -> dict[str, Any]:
        return {
            "topology": self.topology(),
            "hotplug_events": len(self.hotplug_events),
            "dock_session": self.dock.session_id,
        }
