"""Ecosystem package — topology, runtime, ECO-001..010, games."""
from gunnchos_device_os.device_lab.ecosystem.eco001_smoke import run_eco001_smoke
from gunnchos_device_os.device_lab.ecosystem.manager import (
    active_ecosystem,
    get_ecosystem,
    list_ecosystems,
    start_ecosystem,
    stop_ecosystem,
)
from gunnchos_device_os.device_lab.ecosystem.scenarios import run_all_eco, run_eco_scenario
from gunnchos_device_os.device_lab.ecosystem.topology import ecosystem_topology

__all__ = [
    "ecosystem_topology",
    "run_eco001_smoke",
    "start_ecosystem",
    "stop_ecosystem",
    "get_ecosystem",
    "list_ecosystems",
    "active_ecosystem",
    "run_eco_scenario",
    "run_all_eco",
]
