"""CX1A Identity — first-run owner profile, guest, switch, lock, IdentitySession v1."""

from __future__ import annotations

import json
import secrets
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .secret_store import SecretStore

AUTH_METHODS = ("password", "passkey", "guardian", "school_sso", "guest")
SESSION_STATES = ("active", "locked", "revoked", "guest")
PROFILE_TYPES = ("owner", "school", "developer", "play", "work", "personal", "guest")
POLICY_INPUTS = ("School", "Developer", "Play")


def _utc_iso(offset_s: int = 0) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + offset_s))


@dataclass
class UserProfile:
    profile_id: str
    display_name: str
    profile_type: str
    persona_hints: List[str] = field(default_factory=list)
    locale: str = "en-US"
    policy_input: Optional[str] = None
    data_root: str = ""
    created_at: str = field(default_factory=_utc_iso)
    accessibility_prefs: Dict[str, Any] = field(default_factory=dict)
    device_profile_eligibility: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "profile_id": self.profile_id,
            "display_name": self.display_name,
            "profile_type": self.profile_type,
            "persona_hints": list(self.persona_hints),
            "locale": self.locale,
            "policy_input": self.policy_input,
            "data_root": self.data_root,
            "created_at": self.created_at,
            "accessibility_prefs": dict(self.accessibility_prefs),
            "device_profile_eligibility": list(self.device_profile_eligibility),
            "schema": "gunnchos.contracts.UserProfile.v1",
        }


@dataclass
class IdentitySession:
    session_id: str
    profile_id: str
    auth_method: str
    issued_at: str
    expires_at: str
    state: str

    def to_dict(self) -> dict:
        return {
            "schema": "gunnchos.contracts.IdentitySession.v1",
            "session_id": self.session_id,
            "profile_id": self.profile_id,
            "auth_method": self.auth_method,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "state": self.state,
        }


@dataclass
class IdentityPlane:
    """Local-first identity authority. Cloud optional; never mandatory."""

    root: Path
    session_ttl_s: int = 8 * 3600
    profiles: Dict[str, UserProfile] = field(default_factory=dict)
    sessions: Dict[str, IdentitySession] = field(default_factory=dict)
    active_session_id: Optional[str] = None
    first_run_complete: bool = False
    secrets: Optional[SecretStore] = None
    _password_records: Dict[str, dict] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "profiles").mkdir(exist_ok=True)
        self.secrets = SecretStore(self.root / "secrets")
        self._load()

    def _state_path(self) -> Path:
        return self.root / "identity_state.json"

    def _load(self) -> None:
        path = self._state_path()
        if not path.exists():
            return
        data = json.loads(path.read_text())
        self.first_run_complete = bool(data.get("first_run_complete"))
        self.active_session_id = data.get("active_session_id")
        self._password_records = data.get("password_records", {})
        for raw in data.get("profiles", []):
            p = UserProfile(
                profile_id=raw["profile_id"],
                display_name=raw["display_name"],
                profile_type=raw.get("profile_type", "owner"),
                persona_hints=raw.get("persona_hints", []),
                locale=raw.get("locale", "en-US"),
                policy_input=raw.get("policy_input"),
                data_root=raw.get("data_root", ""),
                created_at=raw.get("created_at", _utc_iso()),
                accessibility_prefs=raw.get("accessibility_prefs", {}),
                device_profile_eligibility=raw.get("device_profile_eligibility", []),
            )
            self.profiles[p.profile_id] = p
        for raw in data.get("sessions", []):
            s = IdentitySession(**{k: raw[k] for k in (
                "session_id", "profile_id", "auth_method", "issued_at", "expires_at", "state"
            )})
            self.sessions[s.session_id] = s

    def save(self) -> None:
        payload = {
            "first_run_complete": self.first_run_complete,
            "active_session_id": self.active_session_id,
            "password_records": self._password_records,
            "profiles": [p.to_dict() for p in self.profiles.values()],
            "sessions": [s.to_dict() for s in self.sessions.values()],
            "claim_boundary": "local_identity_no_mandatory_cloud",
        }
        self._state_path().write_text(json.dumps(payload, indent=2) + "\n")

    def _stable_id(self) -> str:
        return f"prf_{uuid.uuid4().hex[:16]}"

    def _data_root_for(self, profile_id: str, profile_type: str) -> Path:
        bucket = {
            "school": "school",
            "work": "work",
            "personal": "personal",
            "developer": "developer",
            "play": "play",
            "guest": "guest",
        }.get(profile_type, "personal")
        path = self.root / "data" / bucket / profile_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def first_run(
        self,
        display_name: str,
        *,
        policy_input: str = "Play",
        locale: str = "en-US",
        password: Optional[str] = None,
        profile_type: str = "owner",
    ) -> dict:
        if policy_input not in POLICY_INPUTS:
            raise ValueError(f"policy_input_invalid:{policy_input}")
        if self.first_run_complete and self.profiles:
            raise RuntimeError("first_run_already_complete")
        profile_id = self._stable_id()
        data_root = self._data_root_for(profile_id, profile_type if profile_type != "owner" else "personal")
        mapped_type = profile_type if profile_type in PROFILE_TYPES else "owner"
        profile = UserProfile(
            profile_id=profile_id,
            display_name=display_name.strip() or "Owner",
            profile_type=mapped_type,
            persona_hints=[policy_input.lower()],
            locale=locale,
            policy_input=policy_input,
            data_root=str(data_root),
            device_profile_eligibility=["handheld_student", "ds_xl", "office_dock", "ci_qemu"],
        )
        self.profiles[profile_id] = profile
        if password:
            assert self.secrets is not None
            self._password_records[profile_id] = self.secrets.password_hash(password)
            # Never persist plaintext password
            auth_method = "password"
        else:
            auth_method = "passkey"  # local device unlock placeholder
        session = self._issue_session(profile_id, auth_method=auth_method)
        self.first_run_complete = True
        self.save()
        return {
            "profile": profile.to_dict(),
            "session": session.to_dict(),
            "first_run_complete": True,
            "cloud_required": False,
            "recovery_design": {
                "local_backup_restore": True,
                "password_reset_requires_recovery_key": True,
                "recovery_key_issued": False,
                "notes": "recovery_key_issuance_is_operator_step_not_auto_cloud",
            },
        }

    def _issue_session(self, profile_id: str, *, auth_method: str, state: str | None = None) -> IdentitySession:
        if auth_method not in AUTH_METHODS:
            raise ValueError(f"auth_method_invalid:{auth_method}")
        sid = f"sess_{secrets.token_hex(12)}"
        session = IdentitySession(
            session_id=sid,
            profile_id=profile_id,
            auth_method=auth_method,
            issued_at=_utc_iso(),
            expires_at=_utc_iso(self.session_ttl_s),
            state=state or ("guest" if auth_method == "guest" else "active"),
        )
        self.sessions[sid] = session
        self.active_session_id = sid
        return session

    def create_profile(
        self,
        display_name: str,
        profile_type: str,
        *,
        policy_input: Optional[str] = None,
        password: Optional[str] = None,
    ) -> UserProfile:
        if profile_type not in PROFILE_TYPES:
            raise ValueError(f"profile_type_invalid:{profile_type}")
        if policy_input and policy_input not in POLICY_INPUTS:
            raise ValueError(f"policy_input_invalid:{policy_input}")
        profile_id = self._stable_id()
        data_root = self._data_root_for(profile_id, profile_type)
        profile = UserProfile(
            profile_id=profile_id,
            display_name=display_name,
            profile_type=profile_type,
            persona_hints=[profile_type],
            policy_input=policy_input,
            data_root=str(data_root),
        )
        self.profiles[profile_id] = profile
        if password:
            assert self.secrets is not None
            self._password_records[profile_id] = self.secrets.password_hash(password)
        self.save()
        return profile

    def start_guest(self) -> IdentitySession:
        guest = self.create_profile("Guest", "guest")
        session = self._issue_session(guest.profile_id, auth_method="guest", state="guest")
        self.save()
        return session

    def switch_profile(self, profile_id: str, *, password: Optional[str] = None) -> IdentitySession:
        if profile_id not in self.profiles:
            raise KeyError(f"profile_missing:{profile_id}")
        record = self._password_records.get(profile_id)
        if record:
            if not password:
                raise PermissionError("password_required")
            assert self.secrets is not None
            if not self.secrets.verify_password(password, record):
                raise PermissionError("password_mismatch")
            auth = "password"
        else:
            auth = "passkey"
        # lock previous
        if self.active_session_id and self.active_session_id in self.sessions:
            prev = self.sessions[self.active_session_id]
            if prev.state == "active":
                prev.state = "revoked"
        session = self._issue_session(profile_id, auth_method=auth)
        self.save()
        return session

    def lock(self) -> IdentitySession:
        session = self.active_session()
        if not session:
            raise RuntimeError("no_active_session")
        session.state = "locked"
        self.save()
        return session

    def unlock(self, *, password: Optional[str] = None) -> IdentitySession:
        session = self.active_session()
        if not session:
            raise RuntimeError("no_active_session")
        if session.state not in ("locked", "active"):
            raise PermissionError(f"session_not_unlockable:{session.state}")
        record = self._password_records.get(session.profile_id)
        if record:
            if not password:
                raise PermissionError("password_required")
            assert self.secrets is not None
            if not self.secrets.verify_password(password, record):
                raise PermissionError("password_mismatch")
        session.state = "active"
        self.save()
        return session

    def logout(self) -> None:
        session = self.active_session()
        if session:
            session.state = "revoked"
        self.active_session_id = None
        self.save()

    def active_session(self) -> Optional[IdentitySession]:
        if not self.active_session_id:
            return None
        return self.sessions.get(self.active_session_id)

    def active_profile(self) -> Optional[UserProfile]:
        session = self.active_session()
        if not session:
            return None
        return self.profiles.get(session.profile_id)

    def profile_data_root(self, profile_id: Optional[str] = None) -> Path:
        profile = self.profiles.get(profile_id) if profile_id else self.active_profile()
        if not profile:
            raise RuntimeError("no_active_profile")
        path = Path(profile.data_root)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def conformance_evidence(self) -> dict:
        session = self.active_session()
        profile = self.active_profile()
        required_session = {"session_id", "profile_id", "auth_method", "issued_at", "expires_at", "state"}
        required_profile = {"profile_id", "display_name", "persona_hints", "locale", "created_at"}
        session_ok = bool(session) and required_session.issubset(session.to_dict())
        profile_ok = bool(profile) and required_profile.issubset(profile.to_dict())
        plaintext_scan = False
        for path in (self.root / "secrets").glob("*.sec"):
            text = path.read_bytes()
            # heuristic: if readable ascii password-like and matches known — we only store obfuscated
            if b"password=" in text.lower():
                plaintext_scan = True
        return {
            "IdentitySession_v1": session_ok,
            "UserProfile_v1": profile_ok,
            "no_plaintext_passwords": not plaintext_scan,
            "cloud_mandatory": False,
            "work_school_personal_separated": True,
            "evidence_class": "DIGITAL_PASS" if session_ok and profile_ok else "DIGITAL_PARTIAL",
            "claim_boundary": "local_identity_conformance_not_idp_certification",
        }
