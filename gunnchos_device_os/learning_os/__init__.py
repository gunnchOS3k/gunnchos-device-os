"""Learning OS thin-launcher companion — native launch, IPC, package lifecycle."""

from .continuity_policy import continuity_handoff_payload
from .deep_link import parse_deep_link
from .ipc_transport import (
    DeterministicTestTransport,
    FileIpcTransport,
    IpcTransport,
)
from .native_launch import NativeLaunchAdapter, NativeLaunchResult
from .package_lifecycle import LearningOsPackageLifecycle
from .provenance import build_provenance
from .roles import (
    PERMISSIONS_MAPPING,
    PLATFORM_TO_DEVICE_ROLE,
    ROLE_MAPPING_DOC,
    map_permissions_for_platform_role,
)

__all__ = [
    "DeterministicTestTransport",
    "FileIpcTransport",
    "IpcTransport",
    "LearningOsPackageLifecycle",
    "NativeLaunchAdapter",
    "NativeLaunchResult",
    "PERMISSIONS_MAPPING",
    "PLATFORM_TO_DEVICE_ROLE",
    "ROLE_MAPPING_DOC",
    "build_provenance",
    "continuity_handoff_payload",
    "map_permissions_for_platform_role",
    "parse_deep_link",
]
