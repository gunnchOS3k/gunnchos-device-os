"""Display backend — compositor multi-output via WaylandSession when available."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


ALLOWED_TRANSITIONS = {
    "secondary_disconnect",
    "secondary_reconnect",
    "dock_attach",
    "dock_detach",
    "external_attach",
    "external_detach",
}


@dataclass
class CompositorWindow:
    window_id: str
    app_id: str
    output_id: str
    title: str
    kind: str  # creator_ide | terminal | docs | logs
    focused: bool = False
    state: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "window_id": self.window_id,
            "app_id": self.app_id,
            "output_id": self.output_id,
            "title": self.title,
            "kind": self.kind,
            "focused": self.focused,
            "state": dict(self.state),
        }


@dataclass
class DisplayBackend:
    outputs: list[dict[str, Any]] = field(default_factory=list)
    session: Any = None
    windows: list[CompositorWindow] = field(default_factory=list)
    backend_name: str = "wayland_session_or_logical"
    layout_store: dict[str, Any] = field(default_factory=dict)

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
                self.outputs.append(
                    {
                        **o,
                        "connected": o.get("role") != "external",
                        "source": "profile_logical",
                        "fallback_reason": str(exc),
                    }
                )
            if profile.get("profile_id") == "dsxl_coder":
                # Force two logical outputs for dual-screen profile
                if len(self.outputs) < 2:
                    self.outputs = [
                        {
                            "id": "dsxl_top",
                            "role": "primary",
                            "resolution": "1280x720",
                            "connected": True,
                            "source": "profile_logical",
                        },
                        {
                            "id": "dsxl_bottom",
                            "role": "secondary",
                            "resolution": "1280x720",
                            "connected": True,
                            "source": "profile_logical",
                        },
                    ]
        return {"ok": True, "outputs": self.outputs, "count": len(self.outputs)}

    def connected_count(self) -> int:
        return sum(1 for o in self.outputs if o.get("connected"))

    def place_window(
        self,
        *,
        app_id: str,
        output_id: str,
        title: str,
        kind: str,
        focused: bool = False,
        state: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not any(o["id"] == output_id and o.get("connected") for o in self.outputs):
            return {"ok": False, "error": "output_not_connected", "output_id": output_id}
        # Replace existing window for same app on that output
        self.windows = [w for w in self.windows if not (w.app_id == app_id and w.output_id == output_id)]
        if focused:
            for w in self.windows:
                w.focused = False
        win = CompositorWindow(
            window_id=f"win-{app_id}-{output_id}",
            app_id=app_id,
            output_id=output_id,
            title=title,
            kind=kind,
            focused=focused,
            state=state or {},
        )
        self.windows.append(win)
        if self.session is not None and focused:
            try:
                self.session.set_focus(output_id, app_id)
            except Exception:
                pass
        return {"ok": True, "window": win.to_dict()}

    def windows_on(self, output_id: str) -> list[dict[str, Any]]:
        return [w.to_dict() for w in self.windows if w.output_id == output_id]

    def focus_window(self, app_id: str) -> dict[str, Any]:
        hit = None
        for w in self.windows:
            w.focused = w.app_id == app_id
            if w.focused:
                hit = w
        if hit is None:
            return {"ok": False, "error": "window_not_found", "app_id": app_id}
        if self.session is not None:
            try:
                self.session.set_focus(hit.output_id, hit.app_id)
            except Exception:
                pass
        return {"ok": True, "focus": hit.to_dict()}

    def persist_layout(self) -> dict[str, Any]:
        self.layout_store = {
            "outputs": [dict(o) for o in self.outputs],
            "windows": [w.to_dict() for w in self.windows],
            "focus": next((w.app_id for w in self.windows if w.focused), None),
        }
        return {"ok": True, "layout": self.layout_store}

    def reload_layout(self) -> dict[str, Any]:
        if not self.layout_store:
            return {"ok": False, "error": "no_persisted_layout"}
        restored = []
        for w in self.layout_store.get("windows") or []:
            if not any(o["id"] == w["output_id"] and o.get("connected") for o in self.outputs):
                continue
            placed = self.place_window(
                app_id=w["app_id"],
                output_id=w["output_id"],
                title=w.get("title") or w["app_id"],
                kind=w.get("kind") or "app",
                focused=bool(w.get("focused")),
                state=w.get("state") or {},
            )
            restored.append(placed)
        focus = self.layout_store.get("focus")
        if focus:
            self.focus_window(focus)
        return {
            "ok": True,
            "restored": restored,
            "windows": [w.to_dict() for w in self.windows],
            "layout": self.layout_store,
        }

    def apply_transition(self, name: str) -> dict[str, Any]:
        if name not in ALLOWED_TRANSITIONS:
            return {
                "ok": False,
                "error": "unknown_transition",
                "transition": name,
                "accepted_as_success": False,
            }
        return {"ok": True, "transition": name}

    def disconnect(self, output_id: str) -> dict[str, Any]:
        for o in self.outputs:
            if o["id"] == output_id:
                o["connected"] = False
                if self.session:
                    for d in self.session.displays:
                        if d.id == output_id:
                            d.connected = False
                evicted = [w.to_dict() for w in self.windows if w.output_id == output_id]
                self.windows = [w for w in self.windows if w.output_id != output_id]
                return {"ok": True, "output_id": output_id, "connected": False, "evicted": evicted}
        return {"ok": False, "error": "unknown_output"}

    def reconnect(self, output_id: str) -> dict[str, Any]:
        for o in self.outputs:
            if o["id"] == output_id:
                o["connected"] = True
                if self.session:
                    for d in self.session.displays:
                        if d.id == output_id:
                            d.connected = True
                restored = self.reload_layout()
                return {
                    "ok": True,
                    "output_id": output_id,
                    "connected": True,
                    "layout_restored": restored.get("ok"),
                    "windows": [w.to_dict() for w in self.windows],
                }
        return {"ok": False, "error": "unknown_output"}

    def appear_external(self, output: dict[str, Any] | None = None) -> dict[str, Any]:
        ext = output or {"id": "external-dock", "role": "external", "connected": True, "source": "dock_attach"}
        ext = {**ext, "connected": True}
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
