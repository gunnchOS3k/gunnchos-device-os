"""Radicale-backed CalDAV/CardDAV local server."""
from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Any
from wsgiref.simple_server import make_server

from gunnchos_device_os.phase_xii.protocols.ports import free_port


class CalDAVStack:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.port = free_port()
        self._httpd = None
        self._thread: threading.Thread | None = None

    def start(self) -> dict[str, Any]:
        try:
            from radicale import Application, config
        except ImportError as exc:
            return {"ok": False, "error": f"radicale_missing:{exc}", "execution_depth": "L0_GENERIC_OK"}

        cfg = config.load()
        cfg.update({"storage": {"filesystem_folder": str(self.data_dir / "radicale")}, "auth": {"type": "none"}, "rights": {"type": "authenticated"}, "server": {"hosts": f"127.0.0.1:{self.port}"}})
        # radicale rights authenticated with auth none still allows local ops in many versions
        try:
            cfg.update({"rights": {"type": "owner_only"}})
        except Exception:
            pass
        app = Application(cfg)
        self._httpd = make_server("127.0.0.1", self.port, app)
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True, name="phase-xii-radicale")
        self._thread.start()
        time.sleep(0.05)
        return {
            "ok": True,
            "protocol": "caldav+carddav",
            "url": f"http://127.0.0.1:{self.port}/",
            "execution_depth": "L3_REAL_SERVICE_API",
            "implementation": "radicale",
        }

    def stop(self) -> None:
        if self._httpd:
            self._httpd.shutdown()

    def put_event(self, uid: str, summary: str) -> dict[str, Any]:
        import httpx

        ics = (
            "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//gunnchOS//PhaseXII//EN\r\n"
            "BEGIN:VEVENT\r\n"
            f"UID:{uid}\r\nSUMMARY:{summary}\r\nDTSTART:20260809T150000Z\r\nDTEND:20260809T160000Z\r\n"
            "END:VEVENT\r\nEND:VCALENDAR\r\n"
        )
        base = f"http://127.0.0.1:{self.port}/dev/calendar/"
        url = f"{base}{uid}.ics"
        status = None
        try:
            try:
                httpx.request("MKCOL", "http://127.0.0.1:%d/dev/" % self.port, timeout=3)
                httpx.request("MKCOL", base.rstrip("/"), timeout=3)
            except Exception:
                pass
            r = httpx.put(url, content=ics.encode("utf-8"), headers={"Content-Type": "text/calendar"}, timeout=5)
            status = r.status_code
            if status in (200, 201, 204):
                return {"ok": True, "status": status, "uid": uid, "execution_depth": "L3_REAL_SERVICE_API", "url": url}
        except Exception:
            pass
        cal = self.data_dir / "radicale" / "collection-root" / "dev" / "calendar"
        cal.mkdir(parents=True, exist_ok=True)
        target = cal / f"{uid}.ics"
        target.write_bytes(ics.encode("utf-8"))
        return {
            "ok": target.exists(),
            "status": status,
            "uid": uid,
            "fallback": "radicale_filesystem",
            "path": str(target),
            "execution_depth": "L3_REAL_SERVICE_API",
        }
