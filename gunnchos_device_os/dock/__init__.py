"""Gate 1 dock continuity (software simulation + physical collector)."""
from .continuity import DockContinuityEngine
from .simulator import STATUS_SIM_PASS, run_dock_simulation
from .validator import run_dock_validation

STATUS_PHYSICAL_PENDING = "PHYSICAL_DOCK_EVIDENCE_PENDING"

__all__ = [
    "DockContinuityEngine",
    "STATUS_PHYSICAL_PENDING",
    "STATUS_SIM_PASS",
    "run_dock_simulation",
    "run_dock_validation",
]
