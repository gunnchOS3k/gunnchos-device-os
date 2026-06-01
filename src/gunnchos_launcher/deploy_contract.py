"""Deploy package contract (DS-XL → target device mock)."""
from __future__ import annotations

from dataclasses import dataclass, asdict


@dataclass
class DeployPackage:
    source_device: str
    target_device: str
    transport: str
    package_id: str
    verified: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


def simulate_deploy(source: str = "ds_xl_coder", target: str = "handheld_hybrid") -> dict:
    pkg = DeployPackage(
        source_device=source,
        target_device=target,
        transport="usb_c_or_wifi",
        package_id="gunnchos-build-once-mock-v0",
    )
    return {"status": "deploy_simulated", "package": pkg.to_dict()}
