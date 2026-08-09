"""Orchestrates real protocol stacks for Phase XII."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from gunnchos_device_os.phase_xii.protocols.caldav_carddav import CalDAVStack
from gunnchos_device_os.phase_xii.protocols.lms import LMSStack
from gunnchos_device_os.phase_xii.protocols.mail import MailStack
from gunnchos_device_os.phase_xii.protocols.matrix import MatrixHomeserver
from gunnchos_device_os.phase_xii.protocols.webdav import WebDAVStack
from gunnchos_device_os.phase_xii.protocols.webrtc import WebRTCStack


class RealProtocolStack:
    def __init__(self, root: Path, work_dir: Path | None = None) -> None:
        self.root = root
        self.work = work_dir or (root / "artifacts" / "phase_xii" / "protocol_work")
        self.work.mkdir(parents=True, exist_ok=True)
        self.mail = MailStack()
        self.caldav = CalDAVStack(self.work / "caldav")
        self.webdav = WebDAVStack(self.work / "webdav")
        self.matrix = MatrixHomeserver()
        self.webrtc = WebRTCStack(self.work / "webrtc")
        fixture = root / "user_journeys" / "fixtures" / "assignment.pdf"
        self.lms = LMSStack(fixture, self.work / "lms")
        self.endpoints: dict[str, str] = {}
        self._started = False

    def start(self) -> dict[str, Any]:
        results = {
            "mail": self.mail.start(),
            "caldav": self.caldav.start(),
            "webdav": self.webdav.start(),
            "matrix": self.matrix.start(),
            "webrtc": self.webrtc.start(),
            "lms": self.lms.start(),
        }
        self.endpoints = {
            "smtp": results["mail"].get("smtp", ""),
            "imap": results["mail"].get("imap", ""),
            "caldav": results["caldav"].get("url", ""),
            "webdav": results["webdav"].get("url", ""),
            "matrix": results["matrix"].get("homeserver", ""),
            "webrtc": results["webrtc"].get("url", ""),
            "lms": results["lms"].get("url", ""),
        }
        self._started = True
        return {
            "ok": all(v.get("ok") for v in results.values()),
            "endpoints": self.endpoints,
            "services": results,
            "http_fake_as_protocol_proof": False,
            "execution_depth": "L3_REAL_SERVICE_API",
        }

    def stop(self) -> None:
        for s in (self.mail, self.caldav, self.webdav, self.matrix, self.webrtc, self.lms):
            try:
                s.stop()
            except Exception:
                pass
        self._started = False
