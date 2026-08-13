"""Privacy controller — enforceable minimization, permissions, DSAR, youth gates.

Wires accounts, telemetry, AI context/memory, voice/vision/screen, Ring,
WAIKE/minors, games, and diagnostics. Software enforcement only.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from gunnchos_device_os.diagnostics_log import redact
from gunnchos_device_os.permissions_manager import Permission, PermissionsManager
from gunnchos_device_os.privacy.policies import (
    CLAIM_BOUNDARY,
    SENSITIVE_SENSORS,
    SURFACES,
    minimization_rules,
    profile_family,
    requires_guardian,
    retention_days,
)
from gunnchos_device_os.privacy.store import PrivacyStore
from gunnchos_device_os.privacy_security_model import get_telemetry_policy
from gunnchos_device_os.unified_identity import UnifiedIdentityService


SENSOR_TO_PERMISSION = {
    "voice": Permission.MICROPHONE,
    "vision": Permission.CAMERA,
    "screen": Permission.SCREEN_CAPTURE,
    "ring": Permission.RING_INPUT,
}


class PrivacyController:
    """Local privacy enforcement for a device profile."""

    def __init__(
        self,
        *,
        store: PrivacyStore | None = None,
        identity: UnifiedIdentityService | None = None,
        permissions: PermissionsManager | None = None,
        persist_path: Path | None = None,
    ) -> None:
        self.store = store or PrivacyStore(path=persist_path)
        self.identity = identity or UnifiedIdentityService()
        self.permissions = permissions or PermissionsManager(role="student")
        self.claim_boundary = CLAIM_BOUNDARY

    def create_profile(
        self,
        user_id: str,
        profile_type: str = "adult",
        *,
        display_name: str = "local-user",
    ) -> dict[str, Any]:
        family = profile_family(profile_type)
        role = "child" if family == "child" else ("minor" if family == "minor" else "student")
        self.permissions.set_role(role if role in ("child", "minor", "student", "guest") else "student")
        user = self.store.ensure_user(user_id, profile_type)
        user["profile_type"] = profile_type
        user["display_name"] = display_name if family == "adult" else "youth-local"
        if family == "child":
            user["consent_state"] = "denied"
        self.store.persist()
        return {
            "user_id": user_id,
            "profile_type": profile_type,
            "family": family,
            "consent_state": user["consent_state"],
            "minimization": minimization_rules(),
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }

    def set_consent(self, user_id: str, state: str, profile_type: str | None = None) -> dict[str, Any]:
        user = self.store.ensure_user(user_id, profile_type or "adult")
        profile = profile_type or str(user.get("profile_type") or "adult")
        family = profile_family(profile)
        if family == "child" and state.startswith("opt_in"):
            return {
                "user_id": user_id,
                "consent_state": "denied",
                "denied": True,
                "reason": "child_cannot_opt_in_telemetry",
                "telemetry": get_telemetry_policy("child", "denied"),
                "mock": False,
            }
        if requires_guardian(profile, "telemetry_opt_in") and state.startswith("opt_in"):
            return {
                "user_id": user_id,
                "consent_state": user.get("consent_state"),
                "denied": True,
                "reason": "guardian_required",
                "mock": False,
            }
        user["consent_state"] = state
        self.store.persist()
        telemetry = get_telemetry_policy(profile, state)
        return {
            "user_id": user_id,
            "consent_state": state,
            "telemetry": telemetry,
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }

    def record_telemetry(self, user_id: str, event: dict[str, Any]) -> dict[str, Any]:
        user = self.store.ensure_user(user_id)
        profile = str(user.get("profile_type") or "adult")
        policy = get_telemetry_policy(profile, str(user.get("consent_state") or "not_asked"))
        if not policy.get("enabled"):
            return {"accepted": False, "reason": "telemetry_disabled", "policy": policy, "mock": False}
        if "private_payload" in event or "message_content" in event or "keystroke" in event:
            return {"accepted": False, "reason": "minimization_blocked", "mock": False}
        safe = redact(event)
        self.store.append(user_id, "telemetry", {"event": safe}, profile_type=profile)
        return {"accepted": True, "policy": policy, "mock": False}

    def store_ai_memory(self, user_id: str, memory: dict[str, Any], *, cloud: bool = False) -> dict[str, Any]:
        user = self.store.ensure_user(user_id)
        profile = str(user.get("profile_type") or "adult")
        if cloud:
            reason = (
                "youth_hard_deny_ai_cloud"
                if profile_family(profile) != "adult"
                else "ai_cloud_denied_local_controller"
            )
            return {"stored": False, "denied": True, "reason": reason, "mock": False}
        safe = redact(memory)
        item = self.store.append(user_id, "ai_memory", {"memory": safe, "cloud": False}, profile_type=profile)
        self.store.append(user_id, "ai_context", {"turn": safe}, profile_type=profile)
        return {"stored": True, "cloud": False, "item_ts": item["ts_ms"], "mock": False}

    def request_sensor(
        self,
        user_id: str,
        sensor: str,
        *,
        explicit_user_grant: bool = False,
        guardian_grant: bool = False,
        app_id: str = "privacy",
    ) -> dict[str, Any]:
        if sensor not in SENSITIVE_SENSORS:
            raise ValueError(f"unknown sensor: {sensor}")
        user = self.store.ensure_user(user_id)
        profile = str(user.get("profile_type") or "adult")
        if requires_guardian(profile, sensor) and not guardian_grant:
            self.store.set_permission(user_id, sensor, False, reason="guardian_required")
            return {
                "sensor": sensor,
                "decision": "deny",
                "reason": "guardian_required",
                "mock": False,
            }
        perm = SENSOR_TO_PERMISSION[sensor]
        result = self.permissions.request(
            app_id,
            perm,
            role=self.permissions.role,
            explicit_user_grant=explicit_user_grant or guardian_grant,
        )
        granted = result.get("decision") == "allow"
        self.store.set_permission(
            user_id,
            sensor,
            granted,
            reason=str(result.get("reason")),
            guardian=guardian_grant,
        )
        if granted:
            self.store.append(user_id, sensor, {"app_id": app_id, "grant": result}, profile_type=profile)
        return {**result, "sensor": sensor, "mock": False}

    def pair_ring(
        self,
        user_id: str,
        ring_id: str,
        *,
        guardian_grant: bool = False,
        authenticated: bool = False,
    ) -> dict[str, Any]:
        user = self.store.ensure_user(user_id)
        profile = str(user.get("profile_type") or "adult")
        if requires_guardian(profile, "ring") and not guardian_grant:
            return {"paired": False, "denied": True, "reason": "guardian_required", "mock": False}
        if not authenticated:
            return {"paired": False, "denied": True, "reason": "not_authenticated", "mock": False}
        self.store.append(
            user_id,
            "ring",
            {"ring_id": ring_id, "paired": True, "authenticated": True},
            profile_type=profile,
        )
        return {"paired": True, "ring_id": ring_id, "physical_ring_claimed": False, "mock": False}

    def waike_progress(self, user_id: str, lesson_id: str, score: int | None = None) -> dict[str, Any]:
        user = self.store.ensure_user(user_id)
        profile = str(user.get("profile_type") or "adult")
        record = {
            "lesson_id": lesson_id,
            "score": score,
            "pii": False,
            "student_name": None,
        }
        self.store.append(user_id, "waike", record, profile_type=profile)
        return {"recorded": True, "pii": False, "mock": False}

    def game_save(self, user_id: str, game_id: str, save: dict[str, Any], *, social: bool = False) -> dict[str, Any]:
        user = self.store.ensure_user(user_id)
        profile = str(user.get("profile_type") or "adult")
        if social and profile_family(profile) != "adult":
            return {"saved": False, "denied": True, "reason": "youth_hard_deny_game_social", "mock": False}
        self.store.append(
            user_id,
            "games",
            {"game_id": game_id, "save": redact(save), "social": False},
            profile_type=profile,
        )
        return {"saved": True, "social": False, "mock": False}

    def log_diagnostic(self, user_id: str, event_type: str, details: dict[str, Any]) -> dict[str, Any]:
        safe = redact(details)
        self.store.append(user_id, "diagnostics", {"event_type": event_type, "details": safe})
        return {"logged": True, "details": safe, "mock": False}

    def revoke_permission(self, user_id: str, name: str, app_id: str = "privacy") -> dict[str, Any]:
        if name in SENSOR_TO_PERMISSION:
            self.permissions.revoke(app_id, SENSOR_TO_PERMISSION[name])
        grant = self.store.set_permission(user_id, name, False, reason="revoked")
        return {"revoked": True, "name": name, "grant": grant, "mock": False}

    def export(self, user_id: str, dest: Path) -> dict[str, Any]:
        payload = self.store.export_user(user_id)
        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        import json

        dest.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return {
            "user_id": user_id,
            "status": "exported",
            "path": str(dest),
            "found": payload.get("found"),
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }

    def delete(self, user_id: str, dest: Path | None = None) -> dict[str, Any]:
        result = self.store.delete_user(user_id)
        # Revoke any identity sessions for this account id if present.
        for sid, sess in list(self.identity.sessions.items()):
            if sess.account_id == user_id and sess.state.value == "active":
                self.identity.revoke_session(sid)
        if dest is not None:
            import json

            dest = Path(dest)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
            result["path"] = str(dest)
        else:
            result["path"] = f"deleted:{user_id}"
        result["status"] = "deleted"
        result["claim_boundary"] = CLAIM_BOUNDARY
        return result

    def apply_retention(self, user_id: str) -> dict[str, Any]:
        user = self.store.ensure_user(user_id)
        profile = str(user.get("profile_type") or "adult")
        dropped: dict[str, int] = {}
        for surface in SURFACES:
            days = retention_days(profile, surface)
            if days == 0:
                # Session-only: applying retention clears the surface.
                n = len(user["surfaces"].get(surface) or [])
                user["surfaces"][surface] = []
                dropped[surface] = n
                continue
            max_age_ms = days * 86_400_000
            dropped[surface] = self.store.apply_retention(user_id, surface, max_age_ms)
        self.store.persist()
        return {"user_id": user_id, "dropped": dropped, "mock": False}
