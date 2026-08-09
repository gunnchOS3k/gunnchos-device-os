"""Resource / media / notification / continuity / power policies for Phase XI."""
from gunnchos_device_os.phase_xi.policies.multitasking import MultitaskingPolicy
from gunnchos_device_os.phase_xi.policies.media_focus import MediaFocusPolicy
from gunnchos_device_os.phase_xi.policies.notifications import NotificationPolicy
from gunnchos_device_os.phase_xi.policies.continuity import ContinuityPolicy
from gunnchos_device_os.phase_xi.policies.power import PowerPolicy

__all__ = [
    "MultitaskingPolicy",
    "MediaFocusPolicy",
    "NotificationPolicy",
    "ContinuityPolicy",
    "PowerPolicy",
]
