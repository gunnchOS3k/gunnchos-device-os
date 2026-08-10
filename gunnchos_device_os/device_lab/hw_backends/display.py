"""Display backend — compositor multi-output via WaylandSession when available."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DisplayBackend:
    outputs: list[dict[str, Any]] = field(default_factory=list)
    session: Any = None
    backend_name: str = "wayland_session_or_logical"

    def start(self, profile: dict[str, Any]) -> dict[str, Any]:
        outs = list(profile.get("display_outputs") or [])
        # Prefer real compositor session
        try:
            from gunnchos_device_os.phase_xiv.compositor import WaylandSession
            from gunnchos_device_os.stage2.shell.profiles import AdaptiveProfile

            pid = profile.get("profile_id")
            if pid == "dsxl_coder":
                ap = AdaptiveProfile.DSXL_DUAL_SCREEN
            elif pid == "handheld_docked":
                ap = AdaptiveProfile.HANDHELD_DOCKED
            elif pid == "handheld_hybrid":
                ap = AdaptiveProfile.HANDHELD_GAMEPAD
            else:
                ap = AdaptiveProfile.STUDENT_DESKTOP
            self.session = WaylandSession(ap)
            self.outputs = [
                {
                    "id": d.id,
                    "role": d.role.value if hasattr(d.role, "value") else str(d.role),
                    "width": d.width,
                    "height": d.height,
                    "connected": d.connected,
                    "source": "WaylandSession",
                }
                for d in self.session.displays
            ]
            # Ensure DS-XL has two outputs
            if pid == "dsxl_coder" and len([o for o in self.outputs if o.get("connected")]) < 2:
                raise RuntimeError("dsxl_one_output_fail")
        except Exception as exc:
            # Logical fallback still records outputs from profile (honest)
            self.outputs = []
            for o in outs:
                if o.get("id") == "none":
                    continue
                self.outputs.append({**o, "connected": o.get("role") != "external", "source": "profile_logical", "fallback_reason": str(exc)})
            if profile.get("profile_id") == "dsxl_coder":
                # Force two logical outputs for dual-screen profile
                if len(self.outputs) < 2:
                    self.outputs = [
                        {"id": "dsxl_top", "role": "primary", "resolution": "1280x720", "connected": True, "source": "profile_logical"},
                        {"id": "dsxl_bottom", "role": "secondary", "resolution": "1280x720", "connected": True, "source": "profile_logical"},
                    ]
        return {"ok": True, "outputs": self.outputs, "count": len(self.outputs)}

    def connected_count(self) -> int:
        return sum(1 for o in self.outputs if o.get("connected"))

    def disconnect(self, output_id: str) -> dict[str, Any]:
        for o in self.outputs:
            if o["id"] == output_id:
                o["connected"] = False
                if self.session:
                    for d in self.session.displays:
                        if d.id == output_id:
                            d.connected = False
                return {"ok": True, "output_id": output_id, "connected": False}
        return {"ok": False, "error": "unknown_output"}

    def reconnect(self, output_id: str) -> dict[str, Any]:
        for o in self.outputs:
            if o["id"] == output_id:
                o["connected"] = True
                if self.session:
                    for d in self.session.displays:
                        if d.id == output_id:
                            d.connected = True
                return {"ok": True, "output_id": output_id, "connected": True}
        return {"ok": False, "error": "unknown_output"}

    def appear_external(self, output: dict[str, Any] | None = None) -> dict[str, Any]:
        ext = output or {"id": "external-dock", "role": "external", "connected": True, "source": "dock_attach"}
        ext = {**ext, "connected": True}
        # replace or append
        for i, o in enumerate(self.outputs):
            if o["id"] == ext["id"] or o.get("role") == "external":
                self.outputs[i] = ext
                return {"ok": True, "outputs": self.outputs}
        self.outputs.append(ext)
        return {"ok": True, "outputs": self.outputs}

    def disappear_external(self) -> dict[str, Any]:
        kept = []
        removed = []
        for o in self.outputs:
            if o.get("role") in {"external", "EXTERNAL"} or str(o.get("id", "")).startswith("external"):
                removed.append(o["id"])
            else:
                kept.append(o)
        self.outputs = kept
        return {"ok": True, "removed": removed, "outputs": self.outputs}
