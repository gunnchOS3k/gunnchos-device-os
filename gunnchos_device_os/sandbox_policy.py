"""Sandboxing policy engine — process/app isolation model.

Software policy layer that decides isolation boundaries, capability drops,
filesystem/network namespaces (logical), and IPC rules. Not a kernel
seccomp/AppArmor enforcer and not a native OS sandbox.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any


CLAIM_BOUNDARY = (
    "Software sandbox policy only. Does not claim kernel namespaces, "
    "seccomp, AppArmor/SELinux, or hardware isolation."
)


class IsolationLevel(str, Enum):
    NONE = "none"
    APP = "app"
    PROCESS = "process"
    STRICT = "strict"


class Capability(str, Enum):
    NET_CONNECT = "net_connect"
    NET_BIND = "net_bind"
    FS_HOME_READ = "fs_home_read"
    FS_HOME_WRITE = "fs_home_write"
    FS_SHARED_READ = "fs_shared_read"
    FS_SHARED_WRITE = "fs_shared_write"
    IPC_BUS = "ipc_bus"
    DEVICE_CAMERA = "device_camera"
    DEVICE_MIC = "device_mic"
    DEVICE_GPU = "device_gpu"
    EXEC_CHILD = "exec_child"
    SYSTEM_SERVICE = "system_service"


class Decision(str, Enum):
    ALLOW = "allow"
    DENY = "deny"


# Profiles define maximum capabilities per isolation tier.
ISOLATION_CAPS: dict[IsolationLevel, set[Capability]] = {
    IsolationLevel.NONE: set(Capability),
    IsolationLevel.APP: {
        Capability.NET_CONNECT,
        Capability.FS_HOME_READ,
        Capability.FS_HOME_WRITE,
        Capability.FS_SHARED_READ,
        Capability.IPC_BUS,
        Capability.DEVICE_GPU,
    },
    IsolationLevel.PROCESS: {
        Capability.NET_CONNECT,
        Capability.FS_HOME_READ,
        Capability.FS_SHARED_READ,
        Capability.IPC_BUS,
    },
    IsolationLevel.STRICT: {
        Capability.FS_HOME_READ,
        Capability.IPC_BUS,
    },
}

APP_CLASS_DEFAULTS: dict[str, IsolationLevel] = {
    "system": IsolationLevel.NONE,
    "first_party": IsolationLevel.APP,
    "third_party": IsolationLevel.PROCESS,
    "untrusted": IsolationLevel.STRICT,
    "browser": IsolationLevel.PROCESS,
    "game": IsolationLevel.APP,
    "ai_worker": IsolationLevel.PROCESS,
}


@dataclass
class SandboxProfile:
    app_id: str
    app_class: str
    isolation: IsolationLevel
    granted: set[Capability] = field(default_factory=set)
    dropped: set[Capability] = field(default_factory=set)
    fs_root: str = "/sandbox"
    net_policy: str = "filtered"
    ipc_peers: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "app_id": self.app_id,
            "app_class": self.app_class,
            "isolation": self.isolation.value,
            "granted": sorted(c.value for c in self.granted),
            "dropped": sorted(c.value for c in self.dropped),
            "fs_root": self.fs_root,
            "net_policy": self.net_policy,
            "ipc_peers": list(self.ipc_peers),
        }


@dataclass
class SandboxPolicyEngine:
    """Decide and enforce (in-process) sandbox policy for apps/processes."""

    profiles: dict[str, SandboxProfile] = field(default_factory=dict)
    audit: list[dict[str, Any]] = field(default_factory=list)
    # Logical namespace tags: app_id -> namespace id
    namespaces: dict[str, str] = field(default_factory=dict)

    def _audit(self, action: str, details: dict[str, Any]) -> None:
        self.audit.append({"action": action, **details, "claim_boundary": CLAIM_BOUNDARY})

    def create_profile(
        self,
        app_id: str,
        app_class: str = "third_party",
        *,
        extra_caps: set[Capability] | None = None,
        drop_caps: set[Capability] | None = None,
        ipc_peers: list[str] | None = None,
    ) -> SandboxProfile:
        if app_class not in APP_CLASS_DEFAULTS:
            raise ValueError(f"unknown app_class: {app_class}")
        isolation = APP_CLASS_DEFAULTS[app_class]
        base = set(ISOLATION_CAPS[isolation])
        if extra_caps:
            # extras only allowed if isolation is not STRICT
            if isolation == IsolationLevel.STRICT:
                raise PermissionError("strict isolation cannot grant extra capabilities")
            base |= set(extra_caps)
        if drop_caps:
            base -= set(drop_caps)
        # Never let untrusted hold SYSTEM_SERVICE / EXEC_CHILD / NET_BIND
        if app_class in ("untrusted", "third_party", "browser"):
            base -= {Capability.SYSTEM_SERVICE, Capability.EXEC_CHILD, Capability.NET_BIND}
        dropped = set(Capability) - base
        profile = SandboxProfile(
            app_id=app_id,
            app_class=app_class,
            isolation=isolation,
            granted=base,
            dropped=dropped,
            fs_root=f"/sandbox/{app_id}",
            net_policy="deny" if isolation == IsolationLevel.STRICT else "filtered",
            ipc_peers=list(ipc_peers or []),
        )
        self.profiles[app_id] = profile
        self.namespaces[app_id] = f"ns-{isolation.value}-{app_id}"
        self._audit("create_profile", profile.to_dict())
        return profile

    def check_capability(self, app_id: str, cap: Capability | str) -> dict[str, Any]:
        capability = cap if isinstance(cap, Capability) else Capability(cap)
        profile = self.profiles.get(app_id)
        if profile is None:
            return {
                "app_id": app_id,
                "capability": capability.value,
                "decision": Decision.DENY.value,
                "reason": "no_sandbox_profile",
                "mock": False,
                "claim_boundary": CLAIM_BOUNDARY,
            }
        allowed = capability in profile.granted
        return {
            "app_id": app_id,
            "capability": capability.value,
            "decision": Decision.ALLOW.value if allowed else Decision.DENY.value,
            "reason": "granted" if allowed else "capability_dropped",
            "isolation": profile.isolation.value,
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }

    def assert_capability(self, app_id: str, cap: Capability | str) -> None:
        result = self.check_capability(app_id, cap)
        if result["decision"] != Decision.ALLOW.value:
            raise PermissionError(f"{app_id} denied {cap}: {result['reason']}")

    def may_ipc(self, src: str, dst: str) -> dict[str, Any]:
        src_p = self.profiles.get(src)
        dst_p = self.profiles.get(dst)
        if not src_p or not dst_p:
            decision, reason = Decision.DENY, "missing_profile"
        elif Capability.IPC_BUS not in src_p.granted:
            decision, reason = Decision.DENY, "src_no_ipc"
        elif dst in src_p.ipc_peers or src_p.app_class == "system":
            decision, reason = Decision.ALLOW, "peer_allowlist_or_system"
        elif src_p.isolation == IsolationLevel.NONE:
            decision, reason = Decision.ALLOW, "no_isolation"
        else:
            decision, reason = Decision.DENY, "not_in_ipc_peers"
        result = {
            "src": src,
            "dst": dst,
            "decision": decision.value,
            "reason": reason,
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        self._audit("may_ipc", result)
        return result

    def isolate_process(self, app_id: str, process_name: str) -> dict[str, Any]:
        """Logical process isolation record (software model)."""
        profile = self.profiles.get(app_id)
        if profile is None:
            raise KeyError(f"no profile for {app_id}")
        if profile.isolation in (IsolationLevel.NONE, IsolationLevel.APP):
            ns = self.namespaces[app_id]
        else:
            ns = f"{self.namespaces[app_id]}::{process_name}"
        record = {
            "app_id": app_id,
            "process_name": process_name,
            "namespace": ns,
            "isolation": profile.isolation.value,
            "fs_root": profile.fs_root,
            "net_policy": profile.net_policy,
            "granted": sorted(c.value for c in profile.granted),
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }
        self._audit("isolate_process", record)
        return record

    def escalate(
        self,
        app_id: str,
        capability: Capability | str,
        *,
        approved_by: str | None = None,
    ) -> dict[str, Any]:
        """Temporary escalation requires explicit approver (admin/guardian)."""
        cap = capability if isinstance(capability, Capability) else Capability(capability)
        profile = self.profiles.get(app_id)
        if profile is None:
            raise KeyError(f"no profile for {app_id}")
        if approved_by not in ("admin", "guardian"):
            result = {
                "app_id": app_id,
                "capability": cap.value,
                "decision": Decision.DENY.value,
                "reason": "escalation_requires_admin_or_guardian",
                "mock": False,
            }
            self._audit("escalate_denied", result)
            return result
        if profile.isolation == IsolationLevel.STRICT and cap in (
            Capability.SYSTEM_SERVICE,
            Capability.EXEC_CHILD,
            Capability.FS_SHARED_WRITE,
        ):
            result = {
                "app_id": app_id,
                "capability": cap.value,
                "decision": Decision.DENY.value,
                "reason": "strict_blocks_dangerous_escalation",
                "mock": False,
            }
            self._audit("escalate_denied", result)
            return result
        profile.granted.add(cap)
        profile.dropped.discard(cap)
        result = {
            "app_id": app_id,
            "capability": cap.value,
            "decision": Decision.ALLOW.value,
            "reason": f"escalated_by_{approved_by}",
            "mock": False,
        }
        self._audit("escalate_allowed", result)
        return result

    def status(self) -> dict[str, Any]:
        return {
            "profiles": {k: v.to_dict() for k, v in self.profiles.items()},
            "namespaces": dict(self.namespaces),
            "audit_len": len(self.audit),
            "mock": False,
            "claim_boundary": CLAIM_BOUNDARY,
        }
