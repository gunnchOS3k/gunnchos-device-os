"""Digital SBOM/HBOM/AI-BOM inventory. UNKNOWN_RELEASE_BLOCKING if provenance unknown."""

from gunnchos_device_os.digital_inventory.bom import build_inventory, write_inventory

__all__ = ["build_inventory", "write_inventory"]
