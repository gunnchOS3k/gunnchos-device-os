"""MDM + education administration — 10-device simulated fleet E2E."""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from mdm.device_policy_agent import evaluate_app, load_policy, validate_policy_dict


FLEET_SIZE = 10


@dataclass
class ManagedDevice:
    device_id: str
    role: str  # student | teacher | lab
    enrolled: bool = False
    policy_id: str | None = None
    compliance: dict[str, Any] = field(default_factory=dict)
    wiped: bool = False
    wipe_reason: str | None = None
    wiped_at: float | None = None


class EducationMdm:
    def __init__(self, root: Path, policy_dir: Path | None = None):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.policy_dir = policy_dir
        self.devices: dict[str, ManagedDevice] = {}
        self.audit: list[dict[str, Any]] = []

    def enroll(self, device_id: str, role: str, policy_path: Path) -> ManagedDevice:
        policy = load_policy(policy_path)
        dev = ManagedDevice(device_id=device_id, role=role, enrolled=True, policy_id=policy.raw["policy_id"])
        # apply policy summary
        blocked = sorted(policy.blocked_apps)
        allowed = sorted(policy.allowed_apps)
        dev.compliance = {
            "policy_id": policy.raw["policy_id"],
            "deployment_mode": policy.deployment_mode,
            "update_channel": policy.raw.get("update_channel"),
            "blocked_apps": blocked,
            "allowed_apps": allowed,
            "checked_at": time.time(),
        }
        self.devices[device_id] = dev
        self.audit.append({"op": "enroll", "device_id": device_id, "role": role})
        return dev

    def push_policy(self, device_id: str, policy_path: Path) -> dict[str, Any]:
        dev = self.devices[device_id]
        policy = load_policy(policy_path)
        before = dev.policy_id
        dev.policy_id = policy.raw["policy_id"]
        dev.compliance = {
            "policy_id": policy.raw["policy_id"],
            "deployment_mode": policy.deployment_mode,
            "update_channel": policy.raw.get("update_channel"),
            "blocked_apps": sorted(policy.blocked_apps),
            "allowed_apps": sorted(policy.allowed_apps),
            "checked_at": time.time(),
        }
        entry = {"op": "push_policy", "device_id": device_id, "from": before, "to": dev.policy_id}
        self.audit.append(entry)
        return entry

    def check_app(self, device_id: str, app_id: str, policy_path: Path) -> dict[str, Any]:
        policy = load_policy(policy_path)
        decision = evaluate_app(policy, app_id)
        return {"device_id": device_id, "app_id": app_id, "allowed": decision.allowed, "reason": decision.reason}

    def wipe_device(self, device_id: str, *, reason: str = "admin_wipe") -> dict[str, Any]:
        """Digital fleet wipe / factory-reset sim for a managed device.

        Clears enrollment + policy compliance and marks the device wiped.
        Not a physical secure-element wipe (PHYSICAL_PENDING).
        """
        dev = self.devices.get(device_id)
        if dev is None:
            raise KeyError(f"unknown device: {device_id}")
        if not dev.enrolled and not dev.wiped:
            raise PermissionError("device_not_enrolled")
        dev.enrolled = False
        dev.wiped = True
        dev.wipe_reason = reason
        dev.wiped_at = time.time()
        dev.policy_id = None
        dev.compliance = {
            "wiped": True,
            "reason": reason,
            "checked_at": dev.wiped_at,
            "continuity_access": "denied",
        }
        entry = {
            "ok": True,
            "op": "wipe",
            "device_id": device_id,
            "reason": reason,
            "mode": "digital_factory_reset_sim",
            "destructive_physical": False,
            "continuity_denied": True,
            "claim_boundary": (
                "Simulated education MDM wipe only. No remote production MDM, "
                "no secure-element erase, no physical fleet SI."
            ),
        }
        self.audit.append(entry)
        (self.root / f"WIPE_{device_id}.json").write_text(json.dumps(entry, indent=2) + "\n")
        return entry

    def fleet_status(self) -> dict[str, Any]:
        return {
            "schema": "gunnchos.phase_xiv.mdm_fleet.v1",
            "size": len(self.devices),
            "enrolled": sum(1 for d in self.devices.values() if d.enrolled),
            "wiped": sum(1 for d in self.devices.values() if d.wiped),
            "devices": {
                k: {
                    "role": v.role,
                    "enrolled": v.enrolled,
                    "wiped": v.wiped,
                    "policy_id": v.policy_id,
                    "mode": (v.compliance or {}).get("deployment_mode"),
                }
                for k, v in self.devices.items()
            },
        }

    def e2e_ten_device_fleet(self, repo_root: Path) -> dict[str, Any]:
        policy_school = repo_root / "mdm" / "sample_policies" / "school_default.json"
        policy_lib = repo_root / "mdm" / "sample_policies" / "library_session.json"
        if not policy_school.exists():
            raise FileNotFoundError(policy_school)
        # validate policies digitally
        for p in (policy_school, policy_lib):
            errs = validate_policy_dict(json.loads(p.read_text()))
            if errs:
                raise ValueError(errs)
        roles = (["teacher"] + ["lab"] * 2 + ["student"] * 7)
        for i in range(FLEET_SIZE):
            self.enroll(f"edu-{i+1:02d}", roles[i], policy_school)
        # push library policy to lab devices
        for did, dev in list(self.devices.items()):
            if dev.role == "lab":
                self.push_policy(did, policy_lib)
        # app gate checks
        teacher_ok = self.check_app("edu-01", "waike.tutor", policy_school)
        # school policy typically allows listed apps — blocked check
        blocked_probe = self.check_app("edu-04", "games.unapproved", policy_school)
        status = self.fleet_status()
        (self.root / "FLEET.json").write_text(json.dumps(status, indent=2) + "\n")
        ok = (
            status["size"] == FLEET_SIZE
            and status["enrolled"] == FLEET_SIZE
            and sum(1 for d in self.devices.values() if d.role == "lab" and d.policy_id) == 2
            and teacher_ok["device_id"] == "edu-01"
            and blocked_probe["allowed"] is False
        )
        return {
            "ok": ok,
            "fleet": status,
            "teacher_check": teacher_ok,
            "blocked_probe": blocked_probe,
            "audit_len": len(self.audit),
        }
