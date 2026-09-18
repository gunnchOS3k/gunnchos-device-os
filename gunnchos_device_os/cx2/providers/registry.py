"""Provider registry — binds App Center / browser / productivity / connect / print / portals."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from gunnchos_device_os.cx1.home import GunnchHome

from .app_center_real import RealAppCenterProvider
from .browser_real import RealBrowserProvider
from .productivity_real import RealProductivityProvider
from .connect_real import RealConnectProvider
from .capture_real import RealCaptureProvider
from .printing_real import RealPrintingProvider
from .portals_real import RealPortalProvider


@dataclass
class ProviderRegistry:
    root: Path
    app_center: Any = field(init=False)
    browser: Any = field(init=False)
    productivity: Any = field(init=False)
    connect: Any = field(init=False)
    capture: Any = field(init=False)
    printing: Any = field(init=False)
    portals: Any = field(init=False)

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        self.root.mkdir(parents=True, exist_ok=True)

    def attach_defaults(self, cx1: GunnchHome) -> None:
        self.app_center = RealAppCenterProvider(self.root / "app_center")
        self.browser = RealBrowserProvider(self.root / "browser", vault=cx1.vault)
        self.productivity = RealProductivityProvider(self.root / "productivity", vault=cx1.vault)
        self.connect = RealConnectProvider(self.root / "connect", vault=cx1.vault)
        self.capture = RealCaptureProvider(self.root / "capture", vault=cx1.vault)
        self.printing = RealPrintingProvider(self.root / "printing")
        self.portals = RealPortalProvider(self.root / "portals")

    def health(self) -> dict:
        return {
            "app_center": self.app_center.provider_info(),
            "browser": self.browser.qualify_summary(),
            "productivity": self.productivity.status(),
            "connect": self.connect.overall_status(),
            "capture": self.capture.status(),
            "printing": self.printing.status(),
            "portals": self.portals.status(),
        }
