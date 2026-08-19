"""Explicit gunnchAI3k ↔ device-os compatibility contract (no hidden coupling)."""
from gunnchos_device_os.cross_repo_gunnchai.contract import (
    CONTRACT_PATH,
    load_contract,
    validate_contract,
    verify_owner_artifacts,
)

__all__ = [
    "CONTRACT_PATH",
    "load_contract",
    "validate_contract",
    "verify_owner_artifacts",
]
