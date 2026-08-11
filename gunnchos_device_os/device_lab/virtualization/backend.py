"""Honest virtualization / emulation backend selection.

CI default is hybrid: real gunnchOS APIs + compositor/services with
BEHAVIORAL_DEVICE_PROFILE and SILICON_EXACT_EMULATION=false.
Full QEMU guest is preferred when tooling/images are present; never claim
generic QEMU ARM equals SoC silicon.
"""
from __future__ import annotations

import os
import platform
import shutil
from dataclasses import dataclass, field
from typing import Any


@dataclass
class VirtualizationBackend:
    name: str
    available: bool
    host: str
    notes: str
    silicon_exact_emulation: bool = False
    behavioral_device_profile: bool = True
    extras: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "available": self.available,
            "host": self.host,
            "notes": self.notes,
            "SILICON_EXACT_EMULATION": self.silicon_exact_emulation,
            "BEHAVIORAL_DEVICE_PROFILE": self.behavioral_device_profile,
            **self.extras,
        }


def Path_exists(p: str) -> bool:
    from pathlib import Path
    return Path(p).exists()


def kvm_usable() -> bool:
    from pathlib import Path
    import os

    kvm = Path("/dev/kvm")
    if not kvm.exists():
        return False
    try:
        fd = os.open(str(kvm), os.O_RDWR)
        os.close(fd)
        return True
    except OSError:
        return False


def describe_backends() -> dict[str, Any]:
    host = platform.system()
    machine = platform.machine()
    qemu_x86 = shutil.which("qemu-system-x86_64")
    qemu_arm = shutil.which("qemu-system-aarch64")
    backends = [
        VirtualizationBackend(
            "HYBRID_BEHAVIORAL",
            True,
            f"{host}/{machine}",
            "Real gunnchOS Python/services + WaylandSession/compositor APIs; "
            "no full guest required. Default for CI.",
        ),
        VirtualizationBackend(
            "QEMU_HVF",
            host == "Darwin" and bool(qemu_arm or qemu_x86),
            f"{host}/{machine}",
            "macOS Hypervisor.framework acceleration when QEMU present. "
            "Not silicon-exact SoC replica.",
            extras={"qemu_arm": bool(qemu_arm), "qemu_x86": bool(qemu_x86)},
        ),
        VirtualizationBackend(
            "QEMU_KVM",
            host == "Linux" and kvm_usable() and bool(qemu_arm or qemu_x86),
            f"{host}/{machine}",
            "Linux KVM acceleration when /dev/kvm is usable. Not silicon-exact.",
            extras={"qemu_arm": bool(qemu_arm), "qemu_x86": bool(qemu_x86), "kvm_usable": kvm_usable()},
        ),
        VirtualizationBackend(
            "QEMU_TCG",
            bool(qemu_arm or qemu_x86),
            f"{host}/{machine}",
            "TCG software emulation fallback for cross-arch or denied KVM. Slow; not silicon-exact.",
        ),
        VirtualizationBackend(
            "OCI_CONTAINER",
            bool(shutil.which("docker") or shutil.which("podman")),
            f"{host}/{machine}",
            "OCI for service-only components. Not a full device VM.",
        ),
    ]
    return {
        "schema": "gunnchos.device_lab.virtualization.v1",
        "backends": [b.to_dict() for b in backends],
        "default": os.environ.get("GUNNCHDEVICE_LAB_BACKEND", "HYBRID_BEHAVIORAL"),
        "prefer_real_guest_env": os.environ.get("GUNNCHDEVICE_LAB_FORCE_REAL_GUEST", ""),
        "claim_boundary": (
            "Generic QEMU machine != transistor-level Radxa/RK3588. "
            "SILICON_EXACT_EMULATION=false unless actually supported."
        ),
    }

def select_backend(prefer: str | None = None) -> dict[str, Any]:
    prefer = prefer or os.environ.get("GUNNCHDEVICE_LAB_BACKEND", "HYBRID_BEHAVIORAL")
    catalog = describe_backends()
    # Prefer real QEMU guest when explicitly requested or when FORCE_REAL_GUEST=1
    force_real = os.environ.get("GUNNCHDEVICE_LAB_FORCE_REAL_GUEST", "").lower() in {
        "1",
        "true",
        "yes",
    }
    if force_real and prefer == "HYBRID_BEHAVIORAL":
        for name in ("QEMU_HVF", "QEMU_KVM", "QEMU_TCG"):
            for b in catalog["backends"]:
                if b["name"] == name and b["available"]:
                    prefer = name
                    break
            else:
                continue
            break
    for b in catalog["backends"]:
        if b["name"] == prefer and b["available"]:
            return {
                "selected": b,
                "catalog": catalog,
                "prefer_real_guest": force_real or prefer.startswith("QEMU_"),
            }
    # fallback hybrid always available
    hybrid = next(b for b in catalog["backends"] if b["name"] == "HYBRID_BEHAVIORAL")
    return {
        "selected": hybrid,
        "requested": prefer,
        "fallback": True,
        "catalog": catalog,
        "prefer_real_guest": False,
    }
