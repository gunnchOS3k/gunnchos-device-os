"""First-use software flow — language through student profile.

Physical Ring pairing and physical dock discovery are EXTERNAL. Network may
be skipped; remaining offline-capable steps continue. Privacy/AI/youth gates
are software-enforced and are not legal certification.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from gunnchos_device_os.accessibility_manager import SUPPORTED_FEATURES, apply_settings
from gunnchos_device_os.consent_policy import CONSENT_STATES, set_consent
from gunnchos_device_os.dock_manager import dock_state
from gunnchos_device_os.guardian_policy import get_age_band_policy
from gunnchos_device_os.localization import LocalizationCatalog
from gunnchos_device_os.onboarding_wizard import run_onboarding
from gunnchos_device_os.ops.claim import CLAIM_BOUNDARY
from gunnchos_device_os.privacy_security_model import get_telemetry_policy

STEPS = (
    "language",
    "accessibility",
    "network",
    "offline_continuation",
    "privacy",
    "ai_choice",
    "ring_pairing",
    "dock_discovery",
    "update",
    "recovery_help",
    "student_profile",
)

A11Y_ALIASES = {
    "screen_reader": "screen_reader_labels",
    "reduce_motion": "reduced_motion",
    "captions": "captions_preference",
}

YOUTH_PROFILES = ("child", "pre_k", "elementary")
AI_CHOICES = ("local_only", "ask_later", "cloud")


class FirstUseFlow:
    def __init__(self, store_path: Path) -> None:
        self.store_path = Path(store_path)
        self.i18n = LocalizationCatalog()
        if not self.store_path.exists():
            self._write(
                {
                    "schema": "gunnchos.ops.first_use.v1",
                    "sessions": {},
                    "claim_boundary": CLAIM_BOUNDARY,
                }
            )

    def _read(self) -> dict[str, Any]:
        return json.loads(self.store_path.read_text(encoding="utf-8"))

    def _write(self, data: dict[str, Any]) -> dict[str, Any]:
        self.store_path.parent.mkdir(parents=True, exist_ok=True)
        self.store_path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return data

    def start(self, session_id: str, *, user_id: str = "new-user") -> dict[str, Any]:
        session = {
            "session_id": session_id,
            "user_id": user_id,
            "online": False,
            "completed": [],
            "deferred": [],
            "results": {},
            "status": "IN_PROGRESS",
            "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        data = self._read()
        data["sessions"][session_id] = session
        self._write(data)
        return {"ok": True, "session_id": session_id, "next": STEPS[0]}

    def _session(self, session_id: str) -> tuple[dict[str, Any], dict[str, Any]]:
        data = self._read()
        session = data["sessions"].get(session_id)
        if session is None:
            raise KeyError(session_id)
        return data, session

    def _finish_step(self, data: dict[str, Any], session: dict[str, Any], step: str, result: dict[str, Any]) -> dict[str, Any]:
        session["results"][step] = result
        if result.get("deferred"):
            session["deferred"].append(step)
        else:
            session["completed"].append(step)
        remaining = [s for s in STEPS if s not in session["completed"] and s not in session["deferred"]]
        if not remaining:
            session["status"] = "COMPLETE"
        self._write(data)
        return {
            "ok": True,
            "step": step,
            "result": result,
            "next": remaining[0] if remaining else None,
            "status": session["status"],
            "offline": not session["online"],
        }

    def apply_language(self, session_id: str, language: str) -> dict[str, Any]:
        data, session = self._session(session_id)
        primary = language.lower().split("-", 1)[0]
        known = set(self.i18n.catalogs) | {"zh", "ko", "ar", "hi"}
        if primary not in known:
            return {"ok": False, "error": "unsupported_language", "language": language}
        negotiated = self.i18n.negotiate(language)
        welcome, _ = self.i18n.translate("first_run.welcome", negotiated)
        return self._finish_step(
            data,
            session,
            "language",
            {
                "language": language,
                "negotiated": negotiated,
                "welcome": welcome,
                "offline_ok": True,
                "certified_translation": False,
            },
        )

    def apply_accessibility(self, session_id: str, needs: list[str]) -> dict[str, Any]:
        data, session = self._session(session_id)
        resolved = []
        unknown = []
        for need in needs:
            mapped = A11Y_ALIASES.get(need, need)
            if mapped in SUPPORTED_FEATURES:
                resolved.append(mapped)
            else:
                unknown.append(need)
        if unknown:
            return {"ok": False, "error": "unknown_a11y_need", "unknown": unknown}
        settings = apply_settings({n: True for n in resolved})
        return self._finish_step(
            data, session, "accessibility", {"needs": resolved, "settings": settings, "offline_ok": True}
        )

    def apply_network(self, session_id: str, *, online: bool, ssid: str | None = None) -> dict[str, Any]:
        data, session = self._session(session_id)
        session["online"] = bool(online)
        result = {
            "online": bool(online),
            "ssid": ssid if online else None,
            "deferred": not online,
            "offline_ok": True,
            "continuation": "remaining_steps_proceed_offline",
        }
        return self._finish_step(data, session, "network", result)

    def apply_offline_continuation(self, session_id: str) -> dict[str, Any]:
        data, session = self._session(session_id)
        return self._finish_step(
            data,
            session,
            "offline_continuation",
            {
                "offline_ok": True,
                "blocked_steps": [],
                "note": "Offline is not an error; first-use continues.",
            },
        )

    def apply_privacy(self, session_id: str, *, profile_type: str, consent: str) -> dict[str, Any]:
        data, session = self._session(session_id)
        if consent not in CONSENT_STATES:
            return {"ok": False, "error": "unknown_consent_state", "consent": consent}
        if profile_type in YOUTH_PROFILES and consent.startswith("opt_in"):
            consent_result = set_consent(session["user_id"], "denied", profile_type)
            consent_result["denied"] = True
            consent_result["reason"] = "child_cannot_opt_in_telemetry"
        else:
            consent_result = set_consent(session["user_id"], consent, profile_type)
        telemetry = get_telemetry_policy(profile_type, consent_result["consent_state"])
        return self._finish_step(
            data,
            session,
            "privacy",
            {
                "profile_type": profile_type,
                "family": "youth" if profile_type in YOUTH_PROFILES else "adult",
                "consent": consent_result,
                "telemetry": telemetry,
                "legal_certification": "HUMAN/EXTERNAL",
                "offline_ok": True,
            },
        )

    def apply_ai_choice(self, session_id: str, choice: str) -> dict[str, Any]:
        data, session = self._session(session_id)
        if choice not in AI_CHOICES:
            return {"ok": False, "error": "unknown_ai_choice", "choice": choice}
        family = (session.get("results", {}).get("privacy") or {}).get("family") or "adult"
        if choice == "cloud" and family == "youth":
            return self._finish_step(
                data,
                session,
                "ai_choice",
                {
                    "choice": "local_only",
                    "requested": "cloud",
                    "denied": True,
                    "reason": "youth_hard_deny_ai_cloud",
                    "offline_ok": True,
                },
            )
        if choice == "cloud":
            return self._finish_step(
                data,
                session,
                "ai_choice",
                {
                    "choice": "local_only",
                    "requested": "cloud",
                    "denied": True,
                    "reason": "ai_cloud_EXTERNAL_no_production_endpoint",
                    "offline_ok": True,
                },
            )
        return self._finish_step(
            data, session, "ai_choice", {"choice": choice, "cloud": False, "offline_ok": True}
        )

    def apply_ring_pairing(self, session_id: str, *, ring_present: bool, guardian_grant: bool = False) -> dict[str, Any]:
        data, session = self._session(session_id)
        family = (session.get("results", {}).get("privacy") or {}).get("family") or "adult"
        if not ring_present:
            return self._finish_step(
                data,
                session,
                "ring_pairing",
                {
                    "paired": False,
                    "skipped": True,
                    "physical_ring_claimed": False,
                    "status": "SKIPPED_NO_HARDWARE",
                    "offline_ok": True,
                },
            )
        if family == "youth" and not guardian_grant:
            return self._finish_step(
                data,
                session,
                "ring_pairing",
                {
                    "paired": False,
                    "denied": True,
                    "reason": "guardian_required",
                    "physical_ring_claimed": False,
                    "offline_ok": True,
                },
            )
        return self._finish_step(
            data,
            session,
            "ring_pairing",
            {
                "paired": True,
                "ring_id": "ring-dev-001",
                "physical_ring_claimed": False,
                "physical_pairing": "EXTERNAL",
                "offline_ok": True,
            },
        )

    def apply_dock_discovery(self, session_id: str, *, docks_on_lan: list[str] | None = None) -> dict[str, Any]:
        data, session = self._session(session_id)
        found = list(docks_on_lan or [])
        state = dock_state(connected=bool(found))
        return self._finish_step(
            data,
            session,
            "dock_discovery",
            {
                "discovered": found,
                "physical_dock_claimed": False,
                "status": "DIGITAL_SCAN_ONLY" if found else "NONE_FOUND",
                "physical_discovery": "EXTERNAL",
                "dock_state": state,
                "offline_ok": True,
            },
        )

    def apply_update(self, session_id: str) -> dict[str, Any]:
        data, session = self._session(session_id)
        if not session["online"]:
            return self._finish_step(
                data,
                session,
                "update",
                {
                    "deferred": True,
                    "reason": "offline",
                    "offline_ok": True,
                    "recovery_still_available": True,
                },
            )
        return self._finish_step(
            data,
            session,
            "update",
            {
                "checked": True,
                "applied": False,
                "note": "Digital check only; no production update channel claimed.",
                "offline_ok": True,
            },
        )

    def apply_recovery_help(self, session_id: str) -> dict[str, Any]:
        data, session = self._session(session_id)
        return self._finish_step(
            data,
            session,
            "recovery_help",
            {
                "offline_ok": True,
                "recovery_image_realm": "RECOVERY_IMAGE",
                "actions": ["safe_mode", "rollback", "diagnostic_bundle", "secure_wipe"],
                "physical_recovery_media": "EXTERNAL",
            },
        )

    def apply_student_profile(self, session_id: str, answers: dict[str, Any]) -> dict[str, Any]:
        data, session = self._session(session_id)
        onboard = run_onboarding({"who": "student", "goal": "learn", "control": "guided", **answers})
        guardian = get_age_band_policy("high_school")
        return self._finish_step(
            data,
            session,
            "student_profile",
            {
                "profile": onboard["profile_json"],
                "preset": onboard["recommended_journey_preset"],
                "guardian_policy": {"age_band": guardian.get("age_band"), "mock": guardian.get("mock")},
                "offline_ok": True,
            },
        )

    def run_default_offline_student(self, session_id: str, user_id: str = "student-1") -> dict[str, Any]:
        """Happy path used by tests: offline first-use still completes."""
        self.start(session_id, user_id=user_id)
        self.apply_language(session_id, "en")
        self.apply_accessibility(session_id, ["large_text"])
        self.apply_network(session_id, online=False)
        self.apply_offline_continuation(session_id)
        self.apply_privacy(session_id, profile_type="student", consent="not_asked")
        self.apply_ai_choice(session_id, "local_only")
        self.apply_ring_pairing(session_id, ring_present=False)
        self.apply_dock_discovery(session_id, docks_on_lan=[])
        self.apply_update(session_id)
        self.apply_recovery_help(session_id)
        last = self.apply_student_profile(session_id, {"user_id": user_id, "display_name": "Student"})
        data, session = self._session(session_id)
        return {
            "ok": session["status"] == "COMPLETE" and last["ok"],
            "session": session,
            "claim_boundary": CLAIM_BOUNDARY,
        }
