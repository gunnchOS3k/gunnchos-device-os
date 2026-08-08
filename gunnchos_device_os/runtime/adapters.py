"""Concrete digital runtime service adapters over existing platform modules."""
from __future__ import annotations

from typing import Any

from gunnchos_device_os.runtime.service_base import RuntimeService, ServiceConfig


class HalService(RuntimeService):
    service_id = "hal"
    dependencies: list[str] = []
    api_surface = ["get_profile", "list_profiles"]

    def on_start(self) -> None:
        from gunnchos_device_os.hardware_abstraction import DEVICE_PROFILES

        self._store["profiles"] = sorted(DEVICE_PROFILES.keys())
        self._store["active"] = self.config.options.get("device", "Student14")

    def api_get_profile(self, name: str | None = None) -> dict[str, Any]:
        from gunnchos_device_os.hardware_abstraction import get_device_profile

        return get_device_profile(name or self._store.get("active", "Student14"))

    def api_list_profiles(self) -> list[str]:
        return list(self._store.get("profiles") or [])


class InputService(RuntimeService):
    service_id = "input"
    dependencies = ["hal"]
    api_surface = ["get_bindings", "controller_first"]

    def on_start(self) -> None:
        preset = self.config.options.get("preset", "handheld_default")
        self._store["preset"] = preset

    def api_get_bindings(self, preset: str | None = None) -> dict[str, Any]:
        from gunnchos_device_os.input_mapper import get_bindings

        return get_bindings(preset or self._store.get("preset", "handheld_default"))

    def api_controller_first(self, device: str) -> bool:
        from gunnchos_device_os.input_mapper import controller_first_nav_enabled

        return controller_first_nav_enabled(device)


class RingService(RuntimeService):
    """Ring input adapter service — software path; physical ring pending."""

    service_id = "ring"
    dependencies = ["input"]
    api_surface = ["status", "fallback_engage"]

    def on_start(self) -> None:
        # Avoid hard import failure when hardware sibling package absent.
        self._store["physical_ring_claimed"] = False
        self._store["adapter"] = "software_stub"
        self._store["fallback_active"] = False

    def api_status(self) -> dict[str, Any]:
        return {
            "adapter": self._store.get("adapter"),
            "physical_ring_claimed": False,
            "statuses": {
                "AUTHENTICATED_INPUT_PROTOCOL_PASS": True,
                "RING_PHYSICAL_PROTOTYPE_PENDING": True,
            },
            "fallback_active": bool(self._store.get("fallback_active")),
            "evidence_class": "SOFTWARE_SIMULATED",
            "claim_boundary": (
                "Software ring adapter stub in runtime. Physical ring not claimed."
            ),
        }

    def api_fallback_engage(self, reason: str = "auth_fail") -> dict[str, Any]:
        self._store["fallback_active"] = True
        self._store["fallback_reason"] = reason
        return {"fallback_active": True, "reason": reason}


class DisplayService(RuntimeService):
    service_id = "display"
    dependencies = ["hal"]
    api_surface = ["switch", "current", "set_docked"]

    def on_start(self) -> None:
        from gunnchos_device_os.display_manager import DisplayManager

        self._mgr = DisplayManager()
        device = self.config.options.get("device_class", "student_14_5")
        self._mgr.switch_for_device_class(device)
        self._store["device_class"] = device

    def api_switch(self, device_class: str) -> dict[str, Any]:
        result = self._mgr.switch_for_device_class(device_class)
        self._store["device_class"] = device_class
        return result if isinstance(result, dict) else {"device_class": device_class}

    def api_current(self) -> dict[str, Any]:
        return self._mgr.status()

    def api_set_docked(self, docked: bool = True) -> dict[str, Any]:
        result = self._mgr.set_docked(docked)
        self._store["docked"] = docked
        surface = self._mgr.active_surface
        return {
            "docked": docked,
            "surface": surface.value if hasattr(surface, "value") else surface,
            "event": result,
        }


class DockService(RuntimeService):
    service_id = "dock"
    dependencies = ["display", "hal"]
    api_surface = ["capabilities", "simulate"]

    def on_start(self) -> None:
        from gunnchos_device_os.dock.capabilities import load_capabilities

        self._caps = load_capabilities()
        self._store["dock_classes"] = [
            d.get("id") for d in self._caps.get("dock_classes", [])
        ]

    def api_capabilities(self) -> dict[str, Any]:
        return dict(self._caps)

    def api_simulate(self, dock_id: str = "runtime-dock") -> dict[str, Any]:
        from gunnchos_device_os.dock.simulator import run_dock_simulation

        return run_dock_simulation(dock_id=dock_id)


class ContinuityService(RuntimeService):
    service_id = "continuity"
    dependencies = ["dock", "identity", "display"]
    api_surface = ["attach", "detach", "snapshot", "report"]

    def on_start(self) -> None:
        from gunnchos_device_os.dock.continuity import DockContinuityEngine

        self._engine = DockContinuityEngine()
        self._store["session_id"] = self._engine.session_id

    def api_attach(self, dock_id: str = "cont-dock") -> dict[str, Any]:
        return self._engine.attach(dock_id)

    def api_detach(self, safe: bool = True) -> dict[str, Any]:
        return self._engine.detach(safe=safe)

    def api_snapshot(self) -> dict[str, Any]:
        return self._engine.snapshot_session()

    def api_report(self) -> dict[str, Any]:
        return self._engine.continuity_report()


class IdentityService(RuntimeService):
    service_id = "identity"
    dependencies: list[str] = []
    api_surface = ["create_account", "issue_session", "validate_session", "bind_device"]

    def on_start(self) -> None:
        from gunnchos_device_os.unified_identity import UnifiedIdentityService

        self._id = UnifiedIdentityService()
        self._store["accounts"] = 0

    def api_create_account(self, display_name: str, email: str) -> dict[str, Any]:
        acct = self._id.create_account(display_name=display_name, email=email)
        self._store["accounts"] = int(self._store.get("accounts", 0)) + 1
        return acct.to_dict()

    def api_issue_session(self, account_id: str, device_id: str) -> dict[str, Any]:
        return self._id.issue_session(account_id=account_id, device_id=device_id)

    def api_validate_session(
        self, session_id: str, token: str, device_id: str | None = None
    ) -> dict[str, Any]:
        return self._id.validate_session(session_id, token, device_id=device_id)

    def api_bind_device(self, account_id: str, device_id: str, device_class: str) -> dict[str, Any]:
        if device_id not in self._id.devices:
            self._id.register_device(device_class, device_id=device_id)
        binding = self._id.bind_device(account_id=account_id, device_id=device_id)
        return binding.to_dict()


class PermissionsService(RuntimeService):
    service_id = "permissions"
    dependencies = ["identity"]
    api_surface = ["request", "revoke", "list_grants"]

    def on_start(self) -> None:
        from gunnchos_device_os.permissions_manager import PermissionsManager

        role = self.config.options.get("role", "student")
        self._pm = PermissionsManager(role=role)
        self._store["role"] = role

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


class SandboxService(RuntimeService):
    service_id = "sandbox"
    dependencies = ["permissions"]
    api_surface = ["create_profile", "check_capability", "isolate_process", "list_profiles"]

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


class UpdaterService(RuntimeService):
    service_id = "updater"
    dependencies = ["diagnostics"]
    api_surface = ["check", "run_ota", "slots"]

    def on_start(self) -> None:
        from gunnchos_device_os.ota_state_machine import OtaStateMachine

        self._ota = OtaStateMachine()
        active = self._ota.slots[self._ota.active_slot.value]
        self._store["version"] = active.version

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


class RecoveryService(RuntimeService):
    service_id = "recovery"
    dependencies = ["updater", "diagnostics"]
    api_surface = ["playbook", "document"]

    def on_start(self) -> None:
        from gunnchos_device_os.boot.recovery import RECOVERY_PLAYBOOK

        self._store["playbook_keys"] = sorted(RECOVERY_PLAYBOOK.keys())

    def api_playbook(self, errors: list[str] | None = None) -> list[str]:
        from gunnchos_device_os.boot.recovery import recovery_for_errors

        return recovery_for_errors(errors or ["generic"])

    def api_document(self, errors: list[str] | None = None) -> dict[str, Any]:
        from gunnchos_device_os.boot.recovery import recovery_document

        return recovery_document(errors)


class DiagnosticsService(RuntimeService):
    service_id = "diagnostics"
    dependencies: list[str] = []
    api_surface = ["log", "query", "redact_sample"]

    def on_start(self) -> None:
        from gunnchos_device_os.diagnostics_log import DiagnosticsLog
        from pathlib import Path

        path = self.config.persistence_path or "results/diagnostics/runtime_events.jsonl"
        self._log = DiagnosticsLog(path=Path(path))
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


class ConnectivityService(RuntimeService):
    service_id = "connectivity"
    dependencies = ["diagnostics"]
    api_surface = ["evaluate", "active_bearer", "inject_fault"]

    def on_start(self) -> None:
        from gunnchos_device_os.connectivity_orchestrator import ConnectivityOrchestrator

        self._orch = ConnectivityOrchestrator()
        self._store["bearer"] = "offline"

    def api_evaluate(self, metrics: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
        from gunnchos_device_os.connectivity_orchestrator import BearerKind, BearerMetrics

        if metrics:
            for kind, m in metrics.items():
                self._orch.update_metrics(BearerKind(kind), BearerMetrics(**m))
        result = self._orch.evaluate()
        active = getattr(self._orch, "active_bearer", None)
        self._store["bearer"] = getattr(active, "value", active)
        return result if isinstance(result, dict) else {"active": self._store["bearer"]}

    def api_active_bearer(self) -> str:
        active = getattr(self._orch, "active_bearer", None)
        return str(getattr(active, "value", active or "offline"))

    def api_inject_fault(self, fault: str = "force_offline") -> dict[str, Any]:
        self.inject_fault("connectivity", fault)
        self._orch.inject_fault(fault)
        return {"fault": fault, "injected": True, "active": self.api_active_bearer()}


class AiInterfaceService(RuntimeService):
    service_id = "ai_interface"
    dependencies = ["permissions", "diagnostics", "profile_manager"]
    api_surface = ["tutor_start", "safety_check", "privacy_mode"]

    def on_start(self) -> None:
        self._store["privacy_mode"] = self.config.options.get("privacy_mode", "local_only")
        self._store["sessions"] = 0

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
        return {"privacy_mode": self._store["privacy_mode"]}


class ProfileManagerService(RuntimeService):
    service_id = "profile_manager"
    dependencies = ["identity", "hal"]
    api_surface = ["get_user_profile", "apply_runtime_profile", "list_profiles"]

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


class AccessibilityService(RuntimeService):
    service_id = "a11y"
    dependencies = ["display", "input", "profile_manager"]
    api_surface = ["apply", "validate_coverage", "defaults"]

    def on_start(self) -> None:
        from gunnchos_device_os.accessibility_manager import get_defaults

        preset = self.config.options.get("preset_id", "default")
        self._store["settings"] = get_defaults(preset)
        self._store["preset_id"] = preset

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


class FleetAgentService(RuntimeService):
    """Digital fleet agent stub — enrollment, heartbeat, policy pull (no MDM claim)."""

    service_id = "fleet_agent"
    dependencies = ["identity", "diagnostics", "updater", "connectivity"]
    api_surface = ["enroll", "heartbeat", "pull_policy", "report"]

    def on_start(self) -> None:
        self._store["enrolled"] = False
        self._store["device_id"] = self.config.options.get("device_id", "fleet-dev-001")
        self._store["realm"] = "dev"
        self._store["heartbeats"] = 0
        self._store["policy"] = {
            "channel": "dev",
            "auto_update": False,
            "telemetry": "opt_in_only",
            "claim_boundary": (
                "DEV fleet agent simulation only. Not MDM, not production "
                "device management, no production keys."
            ),
        }

    def api_enroll(self, enrollment_token: str = "DEV_ENROLLMENT_TOKEN") -> dict[str, Any]:
        if not enrollment_token.startswith("DEV_"):
            self.record_fault(
                "enrollment_rejected",
                "non-DEV enrollment token rejected",
                recoverable=True,
            )
            return {"enrolled": False, "reason": "prod_tokens_rejected"}
        self._store["enrolled"] = True
        self._store["enrollment_token_class"] = "DEV"
        return {
            "enrolled": True,
            "device_id": self._store["device_id"],
            "realm": "dev",
            "token_class": "DEV",
        }

    def api_heartbeat(self) -> dict[str, Any]:
        if not self._store.get("enrolled"):
            return {"ok": False, "reason": "not_enrolled"}
        self._store["heartbeats"] = int(self._store.get("heartbeats", 0)) + 1
        return {
            "ok": True,
            "device_id": self._store["device_id"],
            "seq": self._store["heartbeats"],
            "realm": "dev",
        }

    def api_pull_policy(self) -> dict[str, Any]:
        return dict(self._store.get("policy") or {})

    def api_report(self) -> dict[str, Any]:
        return {
            "enrolled": bool(self._store.get("enrolled")),
            "device_id": self._store.get("device_id"),
            "realm": self._store.get("realm"),
            "heartbeats": self._store.get("heartbeats", 0),
            "mock": False,
            "production_mdm_claimed": False,
            "claim_boundary": self._store["policy"]["claim_boundary"],
        }


SERVICE_CLASSES: dict[str, type[RuntimeService]] = {
    "hal": HalService,
    "input": InputService,
    "ring": RingService,
    "display": DisplayService,
    "dock": DockService,
    "continuity": ContinuityService,
    "identity": IdentityService,
    "permissions": PermissionsService,
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
