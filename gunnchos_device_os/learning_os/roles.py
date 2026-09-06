"""Platform ↔ Device OS role mapping for Learning OS."""
from __future__ import annotations

from typing import Any

from gunnchos_device_os.permissions_manager import ROLE_ALLOWLIST, Permission, PermissionsManager

# Documented mapping — grader is least-privileged Device OS role supporting
# grader workflows (read/network/identity/notifications only; no educator AV).
PLATFORM_TO_DEVICE_ROLE = {
    "learner": "student",
    "grader": "grader",
    "instructor": "educator",
    "site_admin": "admin",
    "guardian": "guardian",
    "guest": "guest",
}

PERMISSIONS_MAPPING: dict[str, dict[str, Any]] = {
    "student": {
        "platform_roles": ["learner"],
        "permissions": sorted(p.value for p in ROLE_ALLOWLIST["student"]),
        "notes": "Learner baseline; files write + sensors for local coursework.",
    },
    "grader": {
        "platform_roles": ["grader"],
        "permissions": sorted(p.value for p in ROLE_ALLOWLIST["grader"]),
        "notes": (
            "Least privilege for grader workflows: read/network/identity/"
            "notifications only. Not educator (no camera/mic). Not admin."
        ),
    },
    "educator": {
        "platform_roles": ["instructor"],
        "permissions": sorted(p.value for p in ROLE_ALLOWLIST["educator"]),
        "notes": "Instructor-side teaching tools including AV capture.",
    },
    "admin": {
        "platform_roles": ["site_admin"],
        "permissions": sorted(p.value for p in ROLE_ALLOWLIST["admin"]),
        "notes": "Site administration — full Device OS permission set.",
    },
    "guardian": {
        "platform_roles": ["guardian"],
        "permissions": sorted(p.value for p in ROLE_ALLOWLIST["guardian"]),
        "notes": "Guardian oversight — read/network/notifications/identity.",
    },
    "guest": {
        "platform_roles": ["guest"],
        "permissions": sorted(p.value for p in ROLE_ALLOWLIST["guest"]),
        "notes": "Unauthenticated/guest discovery surface.",
    },
}

ROLE_MAPPING_DOC = {
    "learner": {
        "platform_role": "learner",
        "device_os_role": "student",
        "rationale": "Standard student allowlist for coursework.",
    },
    "grader": {
        "platform_role": "grader",
        "device_os_role": "grader",
        "rationale": (
            "Instructor-side grading without educator AV privileges; "
            "least privilege that still supports grader hub workflows."
        ),
    },
    "instructor": {
        "platform_role": "instructor",
        "device_os_role": "educator",
        "rationale": "Teaching workflows needing camera/microphone.",
    },
    "site_admin": {
        "platform_role": "site_admin",
        "device_os_role": "admin",
        "rationale": "Site-wide administration.",
    },
    "guardian": {
        "platform_role": "guardian",
        "device_os_role": "guardian",
        "rationale": "Parental/guardian oversight.",
    },
}


def map_permissions_for_platform_role(platform_role: str) -> dict[str, Any]:
    device_role = PLATFORM_TO_DEVICE_ROLE.get(platform_role, "student")
    if device_role not in ROLE_ALLOWLIST:
        device_role = "student"
    mapping = PERMISSIONS_MAPPING.get(device_role, PERMISSIONS_MAPPING["student"])
    pm = PermissionsManager(role=device_role)
    return {
        "platform_role": platform_role,
        "device_os_role": device_role,
        "allowlist": sorted(p.value for p in pm.allowlist()),
        "mapping": mapping,
        "documentation": ROLE_MAPPING_DOC.get(platform_role),
        "authority": "device_os_permissions_manager",
    }
