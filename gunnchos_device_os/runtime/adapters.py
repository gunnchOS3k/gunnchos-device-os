"""Concrete digital runtime service adapters over existing platform modules."""
from __future__ import annotations

from typing import Any
import time

from gunnchos_device_os.runtime.service_base import RuntimeService, ServiceConfig


class HalService(RuntimeService):
    service_id = "hal"
    dependencies: list[str] = []
    api_surface = [
        "get_profile", "list_profiles", "inventory", "capabilities",
        "power_state", "driver_state", "set_power_state",
    ]

    def on_start(self) -> None:
        from gunnchos_device_os.hardware_abstraction import DEVICE_PROFILES

        self._store["profiles"] = sorted(DEVICE_PROFILES.keys())
        self._store["active"] = self.config.options.get("device", "Student14")
        self._store["power_state"] = "on"
        self._store["drivers"] = {
            "display": "ready", "input": "ready", "wifi": "ready",
            "modem": "simulated_ready", "dock": "ready",
        }
        self._store["inventory"] = [
            {"id": "cpu", "class": "soc", "state": "ok"},
            {"id": "display0", "class": "display", "state": "ok"},
            {"id": "wifi0", "class": "net", "state": "ok"},
            {"id": "modem0", "class": "wwan", "sku": "RM520N-GL", "state": "simulated"},
            {"id": "dock0", "class": "dock", "state": "undocked"},
        ]

    def api_get_profile(self, name: str | None = None) -> dict[str, Any]:
        from gunnchos_device_os.hardware_abstraction import get_device_profile

        return get_device_profile(name or self._store.get("active", "Student14"))

    def api_list_profiles(self) -> list[str]:
        return list(self._store.get("profiles") or [])

    def api_inventory(self) -> dict[str, Any]:
        return {
            "device": self._store.get("active"),
            "items": list(self._store.get("inventory") or []),
            "count": len(self._store.get("inventory") or []),
        }

    def api_capabilities(self, name: str | None = None) -> dict[str, Any]:
        profile = self.api_get_profile(name)
        return {
            "device": profile.get("device"),
            "displays": profile.get("displays"),
            "controllers": profile.get("controllers"),
            "dock": profile.get("dock"),
            "ram_gb": profile.get("ram_gb"),
            "thermal": profile.get("thermal"),
            "modes": profile.get("modes"),
            "modem_sku": "RM520N-GL",
            "ntn_claimed": False,
        }

    def api_power_state(self) -> dict[str, Any]:
        return {"power_state": self._store.get("power_state", "on"), "device": self._store.get("active")}

    def api_set_power_state(self, state: str = "on") -> dict[str, Any]:
        if state not in ("on", "sleep", "off", "thermal_throttle"):
            raise ValueError(f"unsupported power state: {state}")
        self._store["power_state"] = state
        self.persist()
        return self.api_power_state()

    def api_driver_state(self) -> dict[str, Any]:
        return {"drivers": dict(self._store.get("drivers") or {}), "claim": "software_path_only"}


class InputService(RuntimeService):
    service_id = "input"
    dependencies = ["hal"]
    api_surface = [
        "get_bindings", "controller_first", "enumerate_sources", "route_event",
        "set_focus", "remap", "device_ownership",
    ]

    def on_start(self) -> None:
        preset = self.config.options.get("preset", "handheld_default")
        self._store["preset"] = preset
        self._store["sources"] = [
            {"id": "kbd0", "type": "keyboard", "owner": None},
            {"id": "touch0", "type": "touch", "owner": None},
            {"id": "pad0", "type": "gamepad", "owner": None},
            {"id": "ring0", "type": "ring_fallback", "owner": None},
        ]
        self._store["focus"] = "launcher"
        self._store["remap"] = {}
        self._store["events"] = []

    def api_get_bindings(self, preset: str | None = None) -> dict[str, Any]:
        from gunnchos_device_os.input_mapper import get_bindings

        return get_bindings(preset or self._store.get("preset", "handheld_default"))

    def api_controller_first(self, device: str) -> bool:
        from gunnchos_device_os.input_mapper import controller_first_nav_enabled

        return controller_first_nav_enabled(device)

    def api_enumerate_sources(self) -> list[dict[str, Any]]:
        return list(self._store.get("sources") or [])

    def api_route_event(self, source_id: str, event: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        focus = self._store.get("focus", "launcher")
        remapped = (self._store.get("remap") or {}).get(event, event)
        record = {
            "source_id": source_id, "event": event, "remapped": remapped,
            "focus": focus, "payload": payload or {}, "at": time.time(),
        }
        events = list(self._store.get("events") or [])
        events.append(record)
        self._store["events"] = events[-100:]
        self.persist()
        return {"routed": True, **record}

    def api_set_focus(self, target: str) -> dict[str, Any]:
        self._store["focus"] = target
        self.persist()
        return {"focus": target}

    def api_remap(self, event: str, to_event: str) -> dict[str, Any]:
        remap = dict(self._store.get("remap") or {})
        remap[event] = to_event
        self._store["remap"] = remap
        self.persist()
        return {"remap": remap}

    def api_device_ownership(self, source_id: str, owner: str | None = None) -> dict[str, Any]:
        sources = list(self._store.get("sources") or [])
        found = False
        for s in sources:
            if s["id"] == source_id:
                s["owner"] = owner
                found = True
        if not found:
            raise KeyError(f"unknown source: {source_id}")
        self._store["sources"] = sources
        self.persist()
        return {"source_id": source_id, "owner": owner, "sources": sources}


class RingService(RuntimeService):
    """Ring input adapter service — software path; physical ring pending."""

    service_id = "ring"
    dependencies = ["input"]
    api_surface = [
        "status", "fallback_engage", "pair", "auth", "calibrate",
        "event_stream", "confidence", "set_target_device",
    ]

    def on_start(self) -> None:
        self._store["physical_ring_claimed"] = False
        self._store["adapter"] = "software_path"
        self._store["fallback_active"] = False
        self._store["paired"] = False
        self._store["authenticated"] = False
        self._store["calibration"] = {"status": "uncalibrated", "samples": 0}
        self._store["events"] = []
        self._store["confidence"] = 0.0
        self._store["target_device"] = None

    def api_status(self) -> dict[str, Any]:
        return {
            "adapter": self._store.get("adapter"),
            "physical_ring_claimed": False,
            "paired": bool(self._store.get("paired")),
            "authenticated": bool(self._store.get("authenticated")),
            "calibration": dict(self._store.get("calibration") or {}),
            "confidence": float(self._store.get("confidence") or 0.0),
            "target_device": self._store.get("target_device"),
            "statuses": {
                "AUTHENTICATED_INPUT_PROTOCOL_PASS": bool(self._store.get("authenticated")),
                "RING_PHYSICAL_PROTOTYPE_PENDING": True,
            },
            "fallback_active": bool(self._store.get("fallback_active")),
            "evidence_class": "SOFTWARE_SIMULATED",
            "claim_boundary": "Software ring adapter. Physical ring not claimed.",
        }

    def api_fallback_engage(self, reason: str = "auth_fail") -> dict[str, Any]:
        self._store["fallback_active"] = True
        self._store["fallback_reason"] = reason
        self.persist()
        return {"fallback_active": True, "reason": reason}

    def api_pair(self, ring_id: str = "ring-dev-001") -> dict[str, Any]:
        self._store["paired"] = True
        self._store["ring_id"] = ring_id
        self._store["confidence"] = 0.2
        self.persist()
        return {"paired": True, "ring_id": ring_id, "physical_ring_claimed": False}

    def api_auth(self, token: str = "DEV_RING_TOKEN") -> dict[str, Any]:
        if not self._store.get("paired"):
            return {"authenticated": False, "reason": "not_paired"}
        if not str(token).startswith("DEV_"):
            self.record_fault("ring_auth_rejected", "non-DEV token", recoverable=True)
            return {"authenticated": False, "reason": "prod_tokens_rejected"}
        self._store["authenticated"] = True
        self._store["confidence"] = max(float(self._store.get("confidence") or 0), 0.6)
        self.persist()
        return {"authenticated": True, "token_class": "DEV", "physical_ring_claimed": False}

    def api_calibrate(self, samples: int = 8) -> dict[str, Any]:
        cal = {"status": "calibrated", "samples": int(samples), "at": time.time()}
        self._store["calibration"] = cal
        self._store["confidence"] = min(1.0, float(self._store.get("confidence") or 0) + 0.2)
        self.persist()
        return cal

    def api_event_stream(self, gesture: str = "tap", limit: int = 20) -> dict[str, Any]:
        # SEC-RING: unauthenticated rings must not inject OS input events.
        if not self._store.get("authenticated"):
            self.api_fallback_engage("not_authenticated")
            return {
                "events": [],
                "count": 0,
                "denied": True,
                "reason": "not_authenticated",
                "fallback_active": True,
            }
        confidence = float(self._store.get("confidence") or 0)
        destructive = gesture in {
            "destructive_confirm",
            "confirm_destructive",
            "delete",
            "factory_reset",
        }
        if destructive and confidence < 0.85:
            self.api_fallback_engage("low_confidence_destructive")
            return {
                "events": list(self._store.get("events") or [])[-limit:],
                "count": len(self._store.get("events") or []),
                "denied": True,
                "reason": "low_confidence_destructive",
                "fallback_active": True,
            }
        events = list(self._store.get("events") or [])
        events.append({
            "gesture": gesture,
            "confidence": confidence,
            "target_device": self._store.get("target_device"),
            "at": time.time(),
            "authenticated": True,
        })
        self._store["events"] = events[-200:]
        self.persist()
        return {"events": self._store["events"][-limit:], "count": len(self._store["events"])}

    def api_confidence(self) -> dict[str, Any]:
        return {
            "confidence": float(self._store.get("confidence") or 0.0),
            "calibrated": (self._store.get("calibration") or {}).get("status") == "calibrated",
        }

    def api_set_target_device(self, device_id: str) -> dict[str, Any]:
        if not self._store.get("authenticated"):
            return {
                "ok": False,
                "denied": True,
                "reason": "not_authenticated",
                "target_device": self._store.get("target_device"),
            }
        self._store["target_device"] = device_id
        self.persist()
        return {"ok": True, "target_device": device_id}


class DisplayService(RuntimeService):
    service_id = "display"
    dependencies = ["hal"]
    api_surface = [
        "switch", "current", "set_docked", "outputs", "modes", "layouts",
        "set_brightness", "set_orientation",
    ]

    def on_start(self) -> None:
        from gunnchos_device_os.display_manager import DisplayManager

        self._mgr = DisplayManager()
        device = self.config.options.get("device_class", "student_14_5")
        self._mgr.switch_for_device_class(device)
        self._store["device_class"] = device
        self._store["brightness"] = 0.7
        self._store["orientation"] = "landscape"
        self._store["layout"] = "single"

    def api_switch(self, device_class: str) -> dict[str, Any]:
        result = self._mgr.switch_for_device_class(device_class)
        self._store["device_class"] = device_class
        return result if isinstance(result, dict) else {"device_class": device_class}

    def api_current(self) -> dict[str, Any]:
        return self._mgr.status()

    def api_set_docked(self, docked: bool = True) -> dict[str, Any]:
        result = self._mgr.set_docked(docked)
        self._store["docked"] = docked
        self._store["layout"] = "extended" if docked else "single"
        surface = self._mgr.active_surface
        self.persist()
        return {
            "docked": docked,
            "surface": surface.value if hasattr(surface, "value") else surface,
            "layout": self._store["layout"],
            "event": result,
        }

    def api_outputs(self) -> dict[str, Any]:
        outputs = [{"id": "internal", "active": True}]
        if self._store.get("docked"):
            outputs.append({"id": "dock_hdmi", "active": True})
        return {"outputs": outputs, "current": self.api_current()}

    def api_modes(self) -> list[dict[str, Any]]:
        return [
            {"id": "handheld", "refresh_hz": 60},
            {"id": "laptop", "refresh_hz": 60},
            {"id": "docked_external", "refresh_hz": 60},
            {"id": "dual_screen", "refresh_hz": 60},
        ]

    def api_layouts(self) -> dict[str, Any]:
        return {"active": self._store.get("layout", "single"), "available": ["single", "extended", "mirror", "dual"]}

    def api_set_brightness(self, level: float = 0.7) -> dict[str, Any]:
        level = max(0.0, min(1.0, float(level)))
        self._store["brightness"] = level
        self.persist()
        return {"brightness": level}

    def api_set_orientation(self, orientation: str = "landscape") -> dict[str, Any]:
        if orientation not in ("landscape", "portrait", "landscape_flipped", "portrait_flipped"):
            raise ValueError(orientation)
        self._store["orientation"] = orientation
        self.persist()
        return {"orientation": orientation}


class DockService(RuntimeService):
    service_id = "dock"
    dependencies = ["display", "hal"]
    api_surface = [
        "capabilities", "simulate", "state", "power", "display_link",
        "ethernet", "usb", "continuity_events",
    ]

    def on_start(self) -> None:
        from gunnchos_device_os.dock.capabilities import load_capabilities

        self._caps = load_capabilities()
        self._store["dock_classes"] = [
            d.get("id") for d in self._caps.get("dock_classes", [])
        ]
        self._store["docked"] = False
        self._store["power_w"] = 0.0
        self._store["ethernet_up"] = False
        self._store["usb_devices"] = []
        self._store["continuity_events"] = []

    def api_capabilities(self) -> dict[str, Any]:
        return dict(self._caps)

    def api_simulate(self, dock_id: str = "runtime-dock") -> dict[str, Any]:
        from gunnchos_device_os.dock.simulator import run_dock_simulation

        result = run_dock_simulation(dock_id=dock_id)
        self._store["docked"] = True
        self._store["power_w"] = 65.0
        self._store["ethernet_up"] = True
        self._store["usb_devices"] = ["hub0", "kbd0"]
        events = list(self._store.get("continuity_events") or [])
        events.append({"type": "dock_attach", "dock_id": dock_id, "at": time.time()})
        self._store["continuity_events"] = events[-50:]
        self.persist()
        return result if isinstance(result, dict) else {"dock_id": dock_id, "ok": True}

    def api_state(self) -> dict[str, Any]:
        return {
            "docked": bool(self._store.get("docked")),
            "power_w": self._store.get("power_w"),
            "ethernet_up": self._store.get("ethernet_up"),
            "usb_devices": list(self._store.get("usb_devices") or []),
        }

    def api_power(self, watts: float | None = None) -> dict[str, Any]:
        if watts is not None:
            self._store["power_w"] = float(watts)
            self.persist()
        return {"power_w": self._store.get("power_w", 0.0), "docked": bool(self._store.get("docked"))}

    def api_display_link(self) -> dict[str, Any]:
        return {"display_link": "active" if self._store.get("docked") else "inactive", "docked": bool(self._store.get("docked"))}

    def api_ethernet(self, up: bool | None = None) -> dict[str, Any]:
        if up is not None:
            self._store["ethernet_up"] = bool(up)
            self.persist()
        return {"ethernet_up": bool(self._store.get("ethernet_up")), "bearer_hint": "ethernet"}

    def api_usb(self) -> dict[str, Any]:
        return {"devices": list(self._store.get("usb_devices") or [])}

    def api_continuity_events(self) -> list[dict[str, Any]]:
        return list(self._store.get("continuity_events") or [])


class ContinuityService(RuntimeService):
    service_id = "continuity"
    dependencies = ["dock", "identity", "display"]
    api_surface = [
        "attach", "detach", "snapshot", "report", "sessions",
        "app_handoff", "file_state", "save_state", "resume",
    ]

    def on_start(self) -> None:
        from gunnchos_device_os.dock.continuity import DockContinuityEngine

        self._engine = DockContinuityEngine()
        self._store["session_id"] = self._engine.session_id
        self._store["sessions"] = []
        self._store["files"] = {}
        self._store["saves"] = {}
        self._store["handoffs"] = []

    def api_attach(self, dock_id: str = "cont-dock") -> dict[str, Any]:
        result = self._engine.attach(dock_id)
        sessions = list(self._store.get("sessions") or [])
        sessions.append({"session_id": self._engine.session_id, "dock_id": dock_id, "at": time.time()})
        self._store["sessions"] = sessions[-20:]
        self.persist()
        return result

    def api_detach(self, safe: bool = True) -> dict[str, Any]:
        return self._engine.detach(safe=safe)

    def api_snapshot(self) -> dict[str, Any]:
        return self._engine.snapshot_session()

    def api_report(self) -> dict[str, Any]:
        return self._engine.continuity_report()

    def api_sessions(self) -> list[dict[str, Any]]:
        return list(self._store.get("sessions") or [])

    def api_app_handoff(self, app_id: str, from_device: str, to_device: str) -> dict[str, Any]:
        record = {"app_id": app_id, "from_device": from_device, "to_device": to_device, "at": time.time(), "status": "handed_off"}
        handoffs = list(self._store.get("handoffs") or [])
        handoffs.append(record)
        self._store["handoffs"] = handoffs[-50:]
        self.persist()
        return record

    def api_file_state(self, path: str, content_hash: str | None = None) -> dict[str, Any]:
        files = dict(self._store.get("files") or {})
        if content_hash is not None:
            files[path] = {"hash": content_hash, "at": time.time()}
            self._store["files"] = files
            self.persist()
        return {"path": path, "state": files.get(path), "tracked": path in files}

    def _save_integrity_store(self):
        from gunnchos_device_os.security.wp007.game_save_integrity import (
            GameSaveIntegrityStore,
        )

        store = getattr(self, "_save_integrity", None)
        if store is None:
            secret = self._store.get("_platform_save_secret")
            if not isinstance(secret, str) or len(secret) < 32:
                import secrets as _secrets

                secret = _secrets.token_hex(32)
                self._store["_platform_save_secret"] = secret
            store = GameSaveIntegrityStore(
                user_id=str(self._store.get("save_user_id") or "local-user"),
                device_id=str(self._store.get("save_device_id") or "local-device"),
                platform_secret=bytes.fromhex(secret)
                if all(c in "0123456789abcdef" for c in secret)
                else secret.encode(),
            )
            # Rehydrate prior sealed saves
            for slot, rec in (self._store.get("saves") or {}).items():
                payload = rec.get("payload") if isinstance(rec, dict) else None
                if isinstance(payload, dict):
                    store.saves[slot] = payload
            self._save_integrity = store
        return store

    def api_save_state(self, save_id: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        saves = dict(self._store.get("saves") or {})
        if payload is not None:
            store = self._save_integrity_store()
            sealed = store.save(save_id, payload)
            saves[save_id] = {
                "payload": sealed["sealed"],
                "at": time.time(),
                "authenticated": True,
            }
            self._store["saves"] = saves
            self.persist()
            return {
                "save_id": save_id,
                "state": saves.get(save_id),
                "found": True,
                "authenticated": True,
                "LOCAL_SAVE_INTEGRITY_DIGITAL": "E4_PREPARED",
                "AUTHORITATIVE_MULTIPLAYER_INTEGRITY": "EXTERNAL_OR_OPERATIONS_PENDING",
            }
        return {"save_id": save_id, "state": saves.get(save_id), "found": save_id in saves}

    def api_resume(self, save_id: str | None = None) -> dict[str, Any]:
        snap = self.api_snapshot()
        if not save_id:
            return {
                "resumed": True,
                "snapshot": snap,
                "save": None,
                "session_id": self._store.get("session_id"),
            }
        store = self._save_integrity_store()
        loaded = store.load(save_id)
        if not loaded.get("ok"):
            return {
                "resumed": False,
                "snapshot": snap,
                "save": None,
                "session_id": self._store.get("session_id"),
                "integrity": loaded,
                "quarantined": loaded.get("quarantined"),
            }
        return {
            "resumed": True,
            "snapshot": snap,
            "save": {"payload": loaded.get("payload"), "at": time.time()},
            "session_id": self._store.get("session_id"),
            "integrity": {"ok": True},
        }


class IdentityService(RuntimeService):
    service_id = "identity"
    dependencies: list[str] = []
    api_surface = [
        "create_account", "issue_session", "validate_session", "bind_device",
        "local_account", "device_identity", "session", "role", "set_role",
        "revoke_session", "delete_account",
    ]

    def on_start(self) -> None:
        from gunnchos_device_os.unified_identity import UnifiedIdentityService

        self._id = UnifiedIdentityService()
        self._store["accounts"] = 0
        self._store["role"] = self.config.options.get("role", "student")
        self._store["device_id"] = self.config.options.get("device_id", "dev-device-001")

    def api_create_account(self, display_name: str, email: str) -> dict[str, Any]:
        acct = self._id.create_account(display_name=display_name, email=email)
        self._store["accounts"] = int(self._store.get("accounts", 0)) + 1
        data = acct.to_dict()
        self._store["last_account_id"] = data.get("account_id")
        self.persist()
        return data

    def api_issue_session(self, account_id: str, device_id: str) -> dict[str, Any]:
        result = self._id.issue_session(account_id=account_id, device_id=device_id)
        self._store["last_session"] = result
        self.persist()
        return result

    def api_validate_session(
        self, session_id: str, token: str, device_id: str | None = None
    ) -> dict[str, Any]:
        return self._id.validate_session(session_id, token, device_id=device_id)

    def api_bind_device(self, account_id: str, device_id: str, device_class: str) -> dict[str, Any]:
        if device_id not in self._id.devices:
            self._id.register_device(device_class, device_id=device_id)
        binding = self._id.bind_device(account_id=account_id, device_id=device_id)
        return binding.to_dict()

    def api_local_account(self) -> dict[str, Any]:
        return {
            "accounts": int(self._store.get("accounts", 0)),
            "last_account_id": self._store.get("last_account_id"),
            "role": self._store.get("role"),
        }

    def api_device_identity(self) -> dict[str, Any]:
        return {"device_id": self._store.get("device_id"), "realm": "DEV"}

    def api_session(self) -> dict[str, Any]:
        return dict(self._store.get("last_session") or {"session": None})

    def api_role(self) -> dict[str, Any]:
        return {"role": self._store.get("role", "student")}

    def api_set_role(
        self,
        role: str,
        *,
        break_glass: bool = False,
        session_valid: bool = False,
    ) -> dict[str, Any]:
        allowed = ("student", "educator", "developer", "admin", "guest", "guardian")
        if role not in allowed:
            raise ValueError(role)
        current = str(self._store.get("role") or "student")
        privileged = {"admin", "developer"}
        # SEC-OS: block silent privilege escalation / guest escape.
        if current == "guest" and role != "guest":
            raise PermissionError("guest_cannot_escalate")
        if role in privileged and current not in privileged:
            if not (break_glass and session_valid):
                raise PermissionError("privilege_escalation_denied")
        self._store["role"] = role
        self.persist()
        return {"role": role, "escalation": role in privileged and current not in privileged}

    def api_revoke_session(self, session_id: str) -> dict[str, Any]:
        return self._id.revoke_session(session_id)

    def api_delete_account(self, account_id: str) -> dict[str, Any]:
        acct = self._id.accounts.get(account_id)
        if acct is None:
            return {"deleted": False, "reason": "unknown_account"}
        from gunnchos_device_os.unified_identity import AccountStatus, SessionState

        acct.status = AccountStatus.DELETED
        for sess in self._id.sessions.values():
            if sess.account_id == account_id and sess.state == SessionState.ACTIVE:
                sess.state = SessionState.REVOKED
        self.persist()
        return {"deleted": True, "account_id": account_id, "sessions_revoked": True}


class PrivacyService(RuntimeService):
    """Local privacy DSAR + youth/sensor gates. Not legal certification."""

    service_id = "privacy"
    dependencies = ["identity", "permissions", "diagnostics"]
    api_surface = [
        "create_profile", "consent", "export", "delete", "retention",
        "sensor", "ring_pair", "ai_memory", "waike", "game_save", "revoke",
    ]

    def on_start(self) -> None:
        from gunnchos_device_os.privacy.controller import PrivacyController

        root = self.config.options.get("privacy_root")
        self._ctrl = PrivacyController()
        self._store["claim_boundary"] = self._ctrl.claim_boundary
        self._store["legal_approval"] = "HUMAN/EXTERNAL"
        self._root = root

    def api_create_profile(self, user_id: str, profile_type: str = "adult") -> dict[str, Any]:
        return self._ctrl.create_profile(user_id, profile_type)

    def api_consent(self, user_id: str, state: str, profile_type: str = "adult") -> dict[str, Any]:
        return self._ctrl.set_consent(user_id, state, profile_type)

    def api_export(self, user_id: str, path: str | None = None) -> dict[str, Any]:
        from pathlib import Path

        dest = Path(path) if path else Path("results/privacy") / f"{user_id}_export.json"
        return self._ctrl.export(user_id, dest)

    def api_delete(self, user_id: str) -> dict[str, Any]:
        return self._ctrl.delete(user_id)

    def api_retention(self, user_id: str) -> dict[str, Any]:
        return self._ctrl.apply_retention(user_id)

    def api_sensor(
        self,
        user_id: str,
        sensor: str,
        *,
        explicit_user_grant: bool = False,
        guardian_grant: bool = False,
    ) -> dict[str, Any]:
        return self._ctrl.request_sensor(
            user_id, sensor, explicit_user_grant=explicit_user_grant, guardian_grant=guardian_grant
        )

    def api_ring_pair(self, user_id: str, ring_id: str = "ring-dev-001", *, guardian_grant: bool = False) -> dict[str, Any]:
        return self._ctrl.pair_ring(user_id, ring_id, guardian_grant=guardian_grant, authenticated=True)

    def api_ai_memory(self, user_id: str, memory: dict[str, Any] | None = None, *, cloud: bool = False) -> dict[str, Any]:
        return self._ctrl.store_ai_memory(user_id, memory or {"note": "local"}, cloud=cloud)

    def api_waike(self, user_id: str, lesson_id: str = "wireless_basics_101") -> dict[str, Any]:
        return self._ctrl.waike_progress(user_id, lesson_id)

    def api_game_save(self, user_id: str, game_id: str = "beatlink-party", save: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._ctrl.game_save(user_id, game_id, save or {"progress": 1})

    def api_revoke(self, user_id: str, name: str) -> dict[str, Any]:
        return self._ctrl.revoke_permission(user_id, name)


class PermissionsService(RuntimeService):
    service_id = "permissions"
    dependencies = ["identity"]
    api_surface = ["request", "revoke", "list_grants", "app_permissions", "consent", "check"]

    def on_start(self) -> None:
        from gunnchos_device_os.permissions_manager import PermissionsManager

        role = self.config.options.get("role", "student")
        self._pm = PermissionsManager(role=role)
        self._store["role"] = role
        self._store["consents"] = {}

    def api_request(self, app_id: str, permission: str, explicit_user_grant: bool = False) -> dict[str, Any]:
        from gunnchos_device_os.permissions_manager import Permission

        return self._pm.request(
            app_id, Permission(permission), explicit_user_grant=explicit_user_grant
        )

    def api_revoke(self, app_id: str, permission: str) -> dict[str, Any]:
        from gunnchos_device_os.permissions_manager import Permission

        return self._pm.revoke(app_id, Permission(permission))

    def api_list_grants(self) -> list[dict[str, Any]]:
        return [g.to_dict() for g in self._pm.grants.values()]

    def api_app_permissions(self, app_id: str) -> dict[str, Any]:
        return self._pm.least_privilege_report(app_id)

    def api_consent(self, app_id: str, purpose: str, granted: bool = True) -> dict[str, Any]:
        consents = dict(self._store.get("consents") or {})
        consents[f"{app_id}:{purpose}"] = {
            "granted": granted, "at": time.time(), "purpose": purpose, "app_id": app_id,
        }
        self._store["consents"] = consents
        self.persist()
        return consents[f"{app_id}:{purpose}"]

    def api_check(self, app_id: str, permission: str) -> dict[str, Any]:
        from gunnchos_device_os.permissions_manager import Permission

        return self._pm.check(app_id, Permission(permission))


class SandboxService(RuntimeService):
    service_id = "sandbox"
    dependencies = ["permissions"]
    api_surface = [
        "create_profile", "check_capability", "isolate_process", "list_profiles",
        "launch_policy", "filesystem", "network", "device_access",
    ]

    def on_start(self) -> None:
        from gunnchos_device_os.sandbox_policy import SandboxPolicyEngine

        self._engine = SandboxPolicyEngine()
        self._store["engine"] = "sandbox_policy"

    def api_create_profile(self, app_id: str, app_class: str = "third_party") -> dict[str, Any]:
        profile = self._engine.create_profile(app_id, app_class=app_class)
        return profile.to_dict()

    def api_check_capability(self, app_id: str, capability: str) -> dict[str, Any]:
        return self._engine.check_capability(app_id, capability)

    def api_isolate_process(self, app_id: str, process_name: str) -> dict[str, Any]:
        return self._engine.isolate_process(app_id, process_name)

    def api_list_profiles(self) -> list[str]:
        return sorted(self._engine.profiles.keys())

    def api_launch_policy(self, app_id: str, app_class: str = "first_party") -> dict[str, Any]:
        profile = self._engine.create_profile(app_id, app_class=app_class)
        return {
            "app_id": app_id,
            "policy": profile.to_dict(),
            "filesystem": self.api_filesystem(app_id),
            "network": self.api_network(app_id),
            "device_access": self.api_device_access(app_id),
        }

    def api_filesystem(self, app_id: str) -> dict[str, Any]:
        return {
            "home_read": self._engine.check_capability(app_id, "fs_home_read"),
            "home_write": self._engine.check_capability(app_id, "fs_home_write"),
            "shared_read": self._engine.check_capability(app_id, "fs_shared_read"),
        }

    def api_network(self, app_id: str) -> dict[str, Any]:
        return {
            "connect": self._engine.check_capability(app_id, "net_connect"),
            "bind": self._engine.check_capability(app_id, "net_bind"),
        }

    def api_device_access(self, app_id: str) -> dict[str, Any]:
        return {
            "camera": self._engine.check_capability(app_id, "device_camera"),
            "mic": self._engine.check_capability(app_id, "device_mic"),
            "gpu": self._engine.check_capability(app_id, "device_gpu"),
        }


class UpdaterService(RuntimeService):
    service_id = "updater"
    dependencies = ["diagnostics"]
    api_surface = [
        "check", "run_ota", "slots", "channel", "metadata", "download",
        "verify", "stage", "commit", "rollback",
    ]

    def on_start(self) -> None:
        from gunnchos_device_os.ota_state_machine import OtaStateMachine

        self._ota = OtaStateMachine()
        active = self._ota.slots[self._ota.active_slot.value]
        self._store["version"] = active.version
        self._store["channel"] = self.config.options.get("channel", "dev")
        self._store["package"] = None
        self._store["verified"] = False
        self._store["staged"] = False

    def api_check(self) -> dict[str, Any]:
        from gunnchos_device_os.updater import check_for_update

        return check_for_update(self._store.get("version", "0.1.0"))

    def api_run_ota(self, target_version: str = "0.1.1") -> dict[str, Any]:
        from gunnchos_device_os.ota_state_machine import Slot, UpdatePackage

        digest = "a" * 64  # deterministic DEV digest placeholder — not a production signature
        package = UpdatePackage(
            version=target_version,
            target_slot=self._ota.inactive_slot(),
            digest_sha256=digest,
            signature_valid=True,
            security_version=1,
        )
        result = self._ota.run_happy_path(package)
        self._store["version"] = target_version
        return result

    def api_slots(self) -> dict[str, Any]:
        return self._ota.status()

    def api_channel(self, channel: str | None = None) -> dict[str, Any]:
        if channel is not None:
            self._store["channel"] = channel
            self.persist()
        return {"channel": self._store.get("channel", "dev")}

    def api_metadata(self, version: str = "0.1.1") -> dict[str, Any]:
        from gunnchos_device_os.security.wp007 import update_trust

        digest = "a" * 64
        security_version = int(self._store.get("security_version") or 1)
        meta_body = {
            "channel": self._store.get("channel", "dev"),
            "size_bytes": 1024 * 1024,
        }
        signed = update_trust.sign_update_package(
            version=version,
            security_version=security_version,
            digest_sha256=digest,
            metadata=meta_body,
        )
        meta = {
            **signed,
            "signature_valid_dev": True,
            "production_keys_used": False,
            "PRODUCTION_TRUST_ROOT": update_trust.PRODUCTION_TRUST_STATUS,
            "trust_metadata": update_trust.trust_metadata(),
        }
        self._store["metadata"] = meta
        self.persist()
        return meta

    def api_download(self, version: str = "0.1.1") -> dict[str, Any]:
        meta = self.api_metadata(version)
        pkg = {
            "version": version,
            "path": f"/var/lib/gunnchos/ota/{version}.pkg",
            "downloaded": True,
            **meta,
        }
        self._store["package"] = pkg
        self._store["verified"] = False
        self.persist()
        return pkg

    def api_verify(self, force_verified: bool | None = None) -> dict[str, Any]:
        from gunnchos_device_os.security.wp007 import update_trust

        pkg = self._store.get("package")
        active_sv = 1
        try:
            active = self._ota.slots[self._ota.active_slot.value]
            active_sv = int(active.security_version)
        except Exception:
            active_sv = int(self._store.get("security_version") or 1)
        result = update_trust.verify_update_package(
            pkg if isinstance(pkg, dict) else None,
            active_security_version=active_sv,
            force_verified=force_verified,
        )
        out = result.to_dict()
        self._store["verified"] = bool(result.verified)
        self.persist()
        if isinstance(pkg, dict) and result.verified:
            out["digest_sha256"] = pkg.get("digest_sha256")
        return out

    def api_stage(self) -> dict[str, Any]:
        if not self._store.get("verified"):
            return {"staged": False, "reason": "not_verified"}
        self._store["staged"] = True
        self.persist()
        return {"staged": True, "target_slot": self._ota.inactive_slot().value}

    def api_commit(self) -> dict[str, Any]:
        if not self._store.get("staged"):
            return {"committed": False, "reason": "not_staged"}
        version = (self._store.get("package") or {}).get("version", "0.1.1")
        return self.api_run_ota(target_version=version)

    def api_rollback(self) -> dict[str, Any]:
        status = self._ota.status()
        self._store["rollback"] = {"at": time.time(), "from_version": self._store.get("version")}
        self.persist()
        return {"rollback": True, "slots": status, "note": "DEV simulation only"}


class RecoveryService(RuntimeService):
    service_id = "recovery"
    dependencies = ["updater", "diagnostics"]
    api_surface = [
        "playbook", "document", "enter_recovery", "repair", "reset",
        "data_preservation_policy",
    ]

    def on_start(self) -> None:
        from gunnchos_device_os.boot.recovery import RECOVERY_PLAYBOOK

        self._store["playbook_keys"] = sorted(RECOVERY_PLAYBOOK.keys())
        self._store["in_recovery"] = False
        self._store["preserve_user_data"] = True

    def api_playbook(self, errors: list[str] | None = None) -> list[str]:
        from gunnchos_device_os.boot.recovery import recovery_for_errors

        return recovery_for_errors(errors or ["generic"])

    def api_document(self, errors: list[str] | None = None) -> dict[str, Any]:
        from gunnchos_device_os.boot.recovery import recovery_document

        return recovery_document(errors)

    def api_enter_recovery(self, reason: str = "manual") -> dict[str, Any]:
        self._store["in_recovery"] = True
        self._store["recovery_reason"] = reason
        self.persist()
        return {"in_recovery": True, "reason": reason}

    def api_repair(self, target: str = "system") -> dict[str, Any]:
        return {
            "repaired": True,
            "target": target,
            "in_recovery": bool(self._store.get("in_recovery")),
            "preserve_user_data": bool(self._store.get("preserve_user_data")),
        }

    def api_reset(self, preserve_user_data: bool = True) -> dict[str, Any]:
        self._store["preserve_user_data"] = preserve_user_data
        self._store["in_recovery"] = False
        self.persist()
        return {"reset": True, "preserve_user_data": preserve_user_data, "factory": not preserve_user_data}

    def api_data_preservation_policy(self) -> dict[str, Any]:
        return {
            "preserve_user_data_default": True,
            "preserve_user_data": bool(self._store.get("preserve_user_data", True)),
            "preserved": ["profiles", "saves", "waike_progress"],
            "wiped_on_factory": ["apps_cache", "ota_staging"],
        }


class DiagnosticsService(RuntimeService):
    service_id = "diagnostics"
    dependencies: list[str] = []
    api_surface = ["log", "query", "redact_sample", "health", "hardware", "network", "update"]

    def on_start(self) -> None:
        from gunnchos_device_os.diagnostics_log import DiagnosticsLog
        from pathlib import Path

        # Keep event JSONL distinct from supervisor persistence JSON.
        if self.config.persistence_path:
            path = Path(self.config.persistence_path).with_suffix(".events.jsonl")
        else:
            path = Path("results/diagnostics/runtime_events.jsonl")
        self._log = DiagnosticsLog(path=path)
        self._store["entries"] = 0
        self._store["log_path"] = str(path)

    def api_log(self, level: str = "info", message: str = "", **fields: Any) -> dict[str, Any]:
        rec = self._log.log(
            event_type=fields.pop("event_type", "runtime"),
            details={"message": message, **fields},
            level=level,
        )
        self._store["entries"] = int(self._store.get("entries", 0)) + 1
        return rec

    def api_query(self, limit: int = 20) -> list[dict[str, Any]]:
        return self._log.read(limit=limit)

    def api_redact_sample(self, payload: dict[str, Any]) -> dict[str, Any]:
        from gunnchos_device_os.diagnostics_log import redact

        return redact(payload)

    def api_health(self) -> dict[str, Any]:
        return {
            "health": self.health_check(),
            "entries": self._store.get("entries", 0),
            "log_path": self._store.get("log_path"),
        }

    def api_hardware(self) -> dict[str, Any]:
        return {"cpu_ok": True, "mem_ok": True, "storage_ok": True, "thermal": "nominal"}

    def api_network(self) -> dict[str, Any]:
        return {"loopback": True, "carrier_claimed": False}

    def api_update(self) -> dict[str, Any]:
        return {"slot_a": "ok", "slot_b": "ok", "pending": False}


class ConnectivityService(RuntimeService):
    service_id = "connectivity"
    dependencies = ["diagnostics"]
    api_surface = [
        "evaluate", "active_bearer", "inject_fault", "interfaces", "bearer_metrics",
        "route_choice", "failover", "degraded_offline", "modem_rm520n", "list_bearers",
        "airplane", "reconnect", "cellular_manager", "ntn_taxonomy", "honest_tokens",
    ]

    def on_start(self) -> None:
        from gunnchos_device_os.connectivity_orchestrator import ConnectivityOrchestrator
        from gunnchos_device_os.connectivity.bearers import build_default_bearers
        from gunnchos_device_os.connectivity.cellular_manager import CellularManager
        from gunnchos_device_os.connectivity.modem_rm520n import ModemManagerFacade
        from gunnchos_device_os.connectivity.policy import MultiBearerPolicy

        self._orch = ConnectivityOrchestrator()
        self._bearers = build_default_bearers()
        self._modem = ModemManagerFacade()
        self._cellular = CellularManager(modem=self._modem.modem)
        self._policy = MultiBearerPolicy(orch=self._orch)
        self._store["bearer"] = "offline"

    def api_list_bearers(self) -> dict[str, Any]:
        from gunnchos_device_os.connectivity.honest_tokens import honest_tokens

        return {
            "bearers": {k: v.to_dict() for k, v in self._bearers.items()},
            "future_ntn_fake_current": False,
            "bluetooth_wan": False,
            **honest_tokens(),
        }

    def api_honest_tokens(self) -> dict[str, Any]:
        from gunnchos_device_os.connectivity.honest_tokens import honest_tokens

        return honest_tokens()

    def api_ntn_taxonomy(self) -> dict[str, Any]:
        from gunnchos_device_os.connectivity.bearers import ntn_taxonomy

        return ntn_taxonomy(self._bearers)

    def api_airplane(self, enabled: bool = True) -> dict[str, Any]:
        self._cellular.set_airplane(enabled)
        result = self._policy.set_airplane(enabled)
        if enabled:
            self.api_degraded_offline()
        self._store["airplane"] = enabled
        self.persist()
        return result

    def api_reconnect(self) -> dict[str, Any]:
        cellular = self._cellular.recover()
        policy = self._policy.reconnect()
        return {"cellular": cellular, "policy": policy}

    def api_cellular_manager(self, action: str = "snapshot") -> dict[str, Any]:
        if action == "bringup":
            return self._cellular.full_bringup()
        if action == "esim":
            return self._cellular.esim.list_profiles()
        if action == "recover":
            return self._cellular.recover()
        return self._cellular.snapshot()

    def api_interfaces(self) -> list[dict[str, Any]]:
        return [v.probe() for v in self._bearers.values()]

    def api_bearer_metrics(self) -> dict[str, Any]:
        return {k: v.metrics.to_dict() for k, v in self._bearers.items()}

    def api_route_choice(self) -> dict[str, Any]:
        from gunnchos_device_os.connectivity.bearers import select_bearer

        choice = select_bearer(self._bearers)
        self._store["bearer"] = choice.get("active", "offline")
        self.persist()
        return choice

    def api_failover(self, prefer: str = "wifi") -> dict[str, Any]:
        for b in self._bearers.values():
            if b.metrics.available:
                b.disconnect()
        target = self._bearers.get(prefer) or self._bearers["wifi"]
        connected = target.connect()
        choice = self.api_route_choice()
        return {"failover": True, "connected": connected, "choice": choice}

    def api_degraded_offline(self) -> dict[str, Any]:
        for b in self._bearers.values():
            b.disconnect()
            b.metrics.offline = True
            b.metrics.available = False
        self._store["bearer"] = "offline"
        self.persist()
        return {"active": "offline", "degraded": True, "offline": True}

    def api_modem_rm520n(self, action: str = "full_attach") -> dict[str, Any]:
        if action == "enumerate":
            return self._modem.modem.enumerate()
        if action == "diagnostics":
            return self._modem.modem.diagnostics()
        if action == "reconnect":
            return self._modem.modem.reconnect()
        if action == "gnss":
            return self._modem.modem.enable_gnss(True)
        result = self._modem.full_attach()
        self._bearers["terrestrial"].connect()
        self._bearers["terrestrial"].update_metrics(
            available=True,
            signal_dbm=self._modem.modem.state.signal_dbm,
            latency_ms=45.0,
            loss_pct=1.0,
        )
        self.api_route_choice()
        return result

    def api_evaluate(self, metrics: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
        from gunnchos_device_os.connectivity_orchestrator import BearerKind, BearerMetrics

        if metrics:
            for kind, m in metrics.items():
                self._orch.update_metrics(BearerKind(kind), BearerMetrics(**m))
        else:
            mapping = {
                "ethernet": BearerKind.ETHERNET,
                "wifi": BearerKind.WIFI,
                "bluetooth": BearerKind.BLUETOOTH,
                "terrestrial": BearerKind.CELLULAR,
                "ntn_simulated": BearerKind.NTN_SIMULATED,
            }
            for name, kind in mapping.items():
                b = self._bearers.get(name)
                if b is None:
                    continue
                self._orch.update_metrics(kind, BearerMetrics(**b.metrics.to_orchestrator_kwargs()))
        result = self._orch.evaluate()
        active = getattr(self._orch, "active_bearer", None)
        self._store["bearer"] = getattr(active, "value", active)
        self.persist()
        return result if isinstance(result, dict) else {"active": self._store["bearer"]}

    def api_active_bearer(self) -> str:
        active = getattr(self._orch, "active_bearer", None)
        return str(getattr(active, "value", active or self._store.get("bearer") or "offline"))

    def api_inject_fault(self, fault: str = "force_offline") -> dict[str, Any]:
        self.inject_fault("connectivity", fault)
        self._orch.inject_fault(fault)
        if fault == "force_offline":
            self.api_degraded_offline()
        return {"fault": fault, "injected": True, "active": self.api_active_bearer()}


class AiInterfaceService(RuntimeService):
    service_id = "ai_interface"
    dependencies = ["permissions", "diagnostics", "profile_manager"]
    api_surface = [
        "tutor_start", "safety_check", "privacy_mode", "local_request",
        "capability_route", "permission", "provenance",
    ]

    def on_start(self) -> None:
        self._store["privacy_mode"] = self.config.options.get("privacy_mode", "local_only")
        self._store["sessions"] = 0
        self._store["requests"] = []

    def api_tutor_start(self, profile: str = "student", topic: str = "intro") -> dict[str, Any]:
        from gunnchos_device_os.gunnchai_integration import tutor_session_start

        result = tutor_session_start(profile, topic)
        self._store["sessions"] = int(self._store.get("sessions", 0)) + 1
        result = dict(result)
        result["privacy_mode"] = self._store["privacy_mode"]
        result["runtime_service"] = True
        return result

    def api_safety_check(self, response: str) -> dict[str, Any]:
        from gunnchos_device_os.gunnchai_integration import tutor_safety_check

        return tutor_safety_check(response)

    def api_privacy_mode(self, mode: str | None = None) -> dict[str, Any]:
        if mode is not None:
            if mode not in ("local_only", "cloud_allowed_with_consent"):
                raise ValueError(f"unsupported privacy mode: {mode}")
            self._store["privacy_mode"] = mode
            self.persist()
        return {"privacy_mode": self._store["privacy_mode"]}

    def api_local_request(
        self,
        prompt: str,
        capability: str = "tutor",
        *,
        approval_token: str | None = None,
    ) -> dict[str, Any]:
        route = self.api_capability_route(capability)
        if not route.get("allowed"):
            return {"ok": False, "reason": route.get("reason"), "permission": route}
        # SEC-AI: block obvious prompt/tool injection and unapproved computer use.
        lowered = (prompt or "").lower()
        injection_markers = (
            "ignore previous instructions",
            "ignore all previous",
            "system:",
            "<tool>",
            "</tool>",
            "exfiltrate",
            "send secrets to",
            "disable safety",
        )
        if any(m in lowered for m in injection_markers):
            return {
                "ok": False,
                "denied": True,
                "reason": "prompt_injection_suspected",
                "capability": capability,
            }
        if capability in ("computer_use", "shell_exec", "file_write_system"):
            if approval_token != "APPROVED_LOCAL_ACTION":
                return {
                    "ok": False,
                    "denied": True,
                    "reason": "approval_required",
                    "capability": capability,
                }
        answer = {
            "ok": True,
            "capability": capability,
            "prompt_chars": len(prompt),
            "response": f"[local-dev] acknowledged: {prompt[:80]}",
            "privacy_mode": self._store.get("privacy_mode"),
            "provenance": self.api_provenance(capability),
        }
        reqs = list(self._store.get("requests") or [])
        reqs.append({"capability": capability, "at": time.time(), "ok": True})
        self._store["requests"] = reqs[-50:]
        self.persist()
        return answer

    def api_capability_route(self, capability: str = "tutor") -> dict[str, Any]:
        local_ok = {
            "tutor",
            "code_help",
            "troubleshoot",
            "connectivity_diag",
            "a11y_support",
        }
        approval_required = {"computer_use", "shell_exec", "file_write_system"}
        if capability in local_ok:
            allowed, reason, route = True, None, "local_gunnchai"
        elif capability in approval_required:
            allowed, reason, route = True, "approval_required", "gated_computer_use"
        else:
            allowed, reason, route = False, "unknown_capability", "unavailable"
        return {
            "capability": capability,
            "allowed": allowed,
            "route": route,
            "reason": reason,
            "privacy_mode": self._store.get("privacy_mode"),
        }

    def api_permission(self, app_id: str = "ai_interface", permission: str = "ai_cloud_export") -> dict[str, Any]:
        if self._store.get("privacy_mode") == "local_only" and permission == "ai_cloud_export":
            return {"app_id": app_id, "permission": permission, "decision": "deny", "reason": "local_only_privacy"}
        return {"app_id": app_id, "permission": permission, "decision": "allow", "reason": "local_capability"}

    def api_provenance(self, capability: str = "tutor") -> dict[str, Any]:
        return {
            "capability": capability,
            "model": "local-dev-stub",
            "sources": ["gunnchos_device_os.gunnchai_integration"],
            "privacy_mode": self._store.get("privacy_mode"),
            "production_model_claimed": False,
        }


class ProfileManagerService(RuntimeService):
    service_id = "profile_manager"
    dependencies = ["identity", "hal"]
    api_surface = [
        "get_user_profile", "apply_runtime_profile", "list_profiles",
        "device_profiles", "role_profiles",
    ]

    def on_start(self) -> None:
        from gunnchos_device_os.profile_manager import PROFILES
        from gunnchos_device_os.runtime_profiles import RuntimeProfileController

        self._runtime = RuntimeProfileController()
        self._store["user_profiles"] = list(PROFILES)
        self._store["active_runtime"] = None

    def api_get_user_profile(self, name: str) -> dict[str, Any]:
        from gunnchos_device_os.profile_manager import get_profile

        return get_profile(name)

    def api_apply_runtime_profile(self, device_class: str) -> dict[str, Any]:
        result = self._runtime.apply(device_class)
        self._store["active_runtime"] = device_class
        return result if isinstance(result, dict) else {"device_class": device_class}

    def api_list_profiles(self) -> dict[str, Any]:
        return {
            "user_profiles": list(self._store.get("user_profiles") or []),
            "active_runtime": self._store.get("active_runtime"),
        }

    def api_device_profiles(self) -> dict[str, Any]:
        return {
            "Student": "student_14_5",
            "DS-XL": "dsxl",
            "Handheld": "handheld",
            "docked": "docked_external",
        }

    def api_role_profiles(self) -> dict[str, Any]:
        return {
            "student": {"modes": ["School", "Play"]},
            "educator": {"modes": ["School", "Admin"]},
            "developer": {"modes": ["Developer", "Coder"]},
        }


class AccessibilityService(RuntimeService):
    service_id = "a11y"
    dependencies = ["display", "input", "profile_manager"]
    api_surface = [
        "apply", "validate_coverage", "defaults", "global_preferences",
        "input_alternatives", "set_reduced_motion", "set_captions", "set_scaling",
    ]

    def on_start(self) -> None:
        from gunnchos_device_os.accessibility_manager import get_defaults

        preset = self.config.options.get("preset_id", "default")
        self._store["settings"] = get_defaults(preset)
        self._store["preset_id"] = preset
        self._store["reduced_motion"] = False
        self._store["captions"] = True
        self._store["scaling"] = 1.0
        self._store["input_alternatives"] = ["keyboard", "controller", "switch"]

    def api_apply(self, overrides: dict[str, Any] | None = None) -> dict[str, Any]:
        from gunnchos_device_os.accessibility_manager import apply_settings

        settings = apply_settings(overrides)
        self._store["settings"] = settings
        return settings

    def api_validate_coverage(self) -> list[str]:
        from gunnchos_device_os.accessibility_manager import validate_coverage

        return validate_coverage(dict(self._store.get("settings") or {}))

    def api_defaults(self, preset_id: str = "default") -> dict[str, Any]:
        from gunnchos_device_os.accessibility_manager import get_defaults

        return get_defaults(preset_id)

    def api_global_preferences(self) -> dict[str, Any]:
        return {
            "settings": dict(self._store.get("settings") or {}),
            "reduced_motion": self._store.get("reduced_motion"),
            "captions": self._store.get("captions"),
            "scaling": self._store.get("scaling"),
            "input_alternatives": list(self._store.get("input_alternatives") or []),
        }

    def api_input_alternatives(self) -> list[str]:
        return list(self._store.get("input_alternatives") or [])

    def api_set_reduced_motion(self, enabled: bool = True) -> dict[str, Any]:
        self._store["reduced_motion"] = bool(enabled)
        self.persist()
        return {"reduced_motion": bool(enabled)}

    def api_set_captions(self, enabled: bool = True) -> dict[str, Any]:
        self._store["captions"] = bool(enabled)
        self.persist()
        return {"captions": bool(enabled)}

    def api_set_scaling(self, scale: float = 1.0) -> dict[str, Any]:
        scale = max(0.75, min(2.0, float(scale)))
        self._store["scaling"] = scale
        self.persist()
        return {"scaling": scale}


class FleetAgentService(RuntimeService):
    """Digital fleet agent stub — enrollment, heartbeat, policy pull (no MDM claim)."""

    service_id = "fleet_agent"
    dependencies = ["identity", "diagnostics", "updater", "connectivity"]
    api_surface = [
        "enroll", "heartbeat", "pull_policy", "report", "inventory",
        "command", "update_cohort", "revoke",
    ]

    def on_start(self) -> None:
        self._store.setdefault("enrolled", False)
        self._store.setdefault("revoked", False)
        self._store.setdefault("device_id", self.config.options.get("device_id", "fleet-dev-001"))
        self._store.setdefault("realm", "dev")
        self._store.setdefault("heartbeats", 0)
        self._store.setdefault("commands", [])
        self._store.setdefault("cohort", "dev-default")
        self._store.setdefault("inventory", {
            "device_id": self._store["device_id"],
            "services": 17,
            "apps": ["waike", "creator_studio", "device_dashboard"],
            "games": 4,
            "modem": "RM520N-GL",
            "ntn_claimed": False,
        })
        self._store.setdefault("policy", {
            "channel": "dev",
            "auto_update": False,
            "telemetry": "opt_in_only",
            "claim_boundary": (
                "DEV fleet agent simulation only. Not MDM, not production "
                "device management, no production keys."
            ),
        })

    def api_enroll(self, enrollment_token: str = "DEV_ENROLLMENT_TOKEN") -> dict[str, Any]:
        if self._store.get("revoked"):
            return {"enrolled": False, "reason": "revoked"}
        if not enrollment_token.startswith("DEV_"):
            self.record_fault(
                "enrollment_rejected",
                "non-DEV enrollment token rejected",
                recoverable=True,
            )
            return {"enrolled": False, "reason": "prod_tokens_rejected"}
        self._store["enrolled"] = True
        self._store["enrollment_token_class"] = "DEV"
        self.persist()
        return {
            "enrolled": True,
            "device_id": self._store["device_id"],
            "realm": "dev",
            "token_class": "DEV",
        }

    def api_heartbeat(self) -> dict[str, Any]:
        if self._store.get("revoked"):
            return {"ok": False, "reason": "revoked"}
        if not self._store.get("enrolled"):
            return {"ok": False, "reason": "not_enrolled"}
        self._store["heartbeats"] = int(self._store.get("heartbeats", 0)) + 1
        self.persist()
        return {
            "ok": True,
            "device_id": self._store["device_id"],
            "seq": self._store["heartbeats"],
            "realm": "dev",
            "cohort": self._store.get("cohort"),
        }

    def api_pull_policy(self) -> dict[str, Any]:
        return dict(self._store.get("policy") or {})

    def api_report(self) -> dict[str, Any]:
        return {
            "enrolled": bool(self._store.get("enrolled")),
            "revoked": bool(self._store.get("revoked")),
            "device_id": self._store.get("device_id"),
            "realm": self._store.get("realm"),
            "heartbeats": self._store.get("heartbeats", 0),
            "cohort": self._store.get("cohort"),
            "mock": False,
            "production_mdm_claimed": False,
            "claim_boundary": self._store["policy"]["claim_boundary"],
        }

    def api_inventory(self) -> dict[str, Any]:
        inv = dict(self._store.get("inventory") or {})
        inv["enrolled"] = bool(self._store.get("enrolled"))
        inv["revoked"] = bool(self._store.get("revoked"))
        return inv

    def api_command(self, command: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self._store.get("enrolled") or self._store.get("revoked"):
            return {"ok": False, "reason": "not_enrolled_or_revoked"}
        record = {"command": command, "args": args or {}, "at": time.time(), "status": "accepted_dev"}
        cmds = list(self._store.get("commands") or [])
        cmds.append(record)
        self._store["commands"] = cmds[-50:]
        self.persist()
        return record

    def api_update_cohort(self, cohort: str) -> dict[str, Any]:
        self._store["cohort"] = cohort
        self.persist()
        return {"cohort": cohort, "device_id": self._store.get("device_id")}

    def api_revoke(self, reason: str = "admin_revoke") -> dict[str, Any]:
        self._store["revoked"] = True
        self._store["enrolled"] = False
        self._store["revoke_reason"] = reason
        self.persist()
        return {"revoked": True, "reason": reason, "device_id": self._store.get("device_id")}


SERVICE_CLASSES: dict[str, type[RuntimeService]] = {
    "hal": HalService,
    "input": InputService,
    "ring": RingService,
    "display": DisplayService,
    "dock": DockService,
    "continuity": ContinuityService,
    "identity": IdentityService,
    "permissions": PermissionsService,
    "privacy": PrivacyService,
    "sandbox": SandboxService,
    "updater": UpdaterService,
    "recovery": RecoveryService,
    "diagnostics": DiagnosticsService,
    "connectivity": ConnectivityService,
    "ai_interface": AiInterfaceService,
    "profile_manager": ProfileManagerService,
    "a11y": AccessibilityService,
    "fleet_agent": FleetAgentService,
}


def build_service(service_id: str, config: ServiceConfig | None = None) -> RuntimeService:
    cls = SERVICE_CLASSES[service_id]
    cfg = config or ServiceConfig(service_id=service_id)
    return cls(cfg)
