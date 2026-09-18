"""Host-side CalDAV/CardDAV provider for CX2H.4."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict, Optional

from gunnchos_device_os.cx2h4.paths import ensure_lab_tree, repo_root_from_here

CALDAV_PORT = 18580
CALDAV_ROOT = Path("/tmp/cx2h4-caldav")
GUEST_HOST = "10.0.2.2"


def _pidfile_alive(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        pid = int(path.read_text().strip())
        os.kill(pid, 0)
        return True
    except Exception:
        return False


def start_caldav(repo: Optional[Path] = None) -> Dict[str, Any]:
    repo = repo or repo_root_from_here()
    lab = ensure_lab_tree(repo)
    script = lab / "scripts" / "cx2h4_host_caldav.py"
    if not script.is_file():
        return {"ok": False, "blocker": "CX2H4_CALDAV_SCRIPT_MISSING"}
    CALDAV_ROOT.mkdir(parents=True, exist_ok=True)
    pidfile = CALDAV_ROOT / "server.pid"
    if _pidfile_alive(pidfile):
        return {
            "ok": True,
            "reused": True,
            "port": CALDAV_PORT,
            "guest_url": f"http://{GUEST_HOST}:{CALDAV_PORT}/",
            "host_url": f"http://127.0.0.1:{CALDAV_PORT}/",
            "implementation": "cx2h4_minimal_caldav_carddav",
            "json_fixture": False,
        }
    env = os.environ.copy()
    env.update(
        {
            "CX2H4_CALDAV_BIND": "0.0.0.0",
            "CX2H4_CALDAV_PORT": str(CALDAV_PORT),
            "CX2H4_CALDAV_ROOT": str(CALDAV_ROOT),
        }
    )
    log = CALDAV_ROOT / "server.stdout.log"
    proc = subprocess.Popen(
        ["python3", str(script)],
        env=env,
        stdout=log.open("w"),
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    deadline = time.time() + 15
    ready = False
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{CALDAV_PORT}/api/health", timeout=1) as r:
                body = json.loads(r.read().decode())
                if body.get("ok"):
                    ready = True
                    break
        except Exception:
            time.sleep(0.3)
    return {
        "ok": ready,
        "pid": proc.pid,
        "port": CALDAV_PORT,
        "guest_url": f"http://{GUEST_HOST}:{CALDAV_PORT}/",
        "host_url": f"http://127.0.0.1:{CALDAV_PORT}/",
        "implementation": "cx2h4_minimal_caldav_carddav",
        "json_fixture": False,
        "log": str(log),
        "blocker": None if ready else "CX2H4_CALDAV_START_FAILED",
    }


def stop_caldav() -> None:
    pidfile = CALDAV_ROOT / "server.pid"
    if not pidfile.is_file():
        return
    try:
        pid = int(pidfile.read_text().strip())
        os.kill(pid, signal.SIGTERM)
    except Exception:
        pass
    try:
        pidfile.unlink(missing_ok=True)
    except OSError:
        pass


def verify_server_objects(*, event_uid: str = "cx2h4-evt-1", contact_uid: str = "cx2h4-c1") -> Dict[str, Any]:
    event_path = CALDAV_ROOT / "caldav" / "user" / "calendar" / f"{event_uid}.ics"
    contact_path = CALDAV_ROOT / "carddav" / "user" / "contacts" / f"{contact_uid}.vcf"
    event_body = event_path.read_text() if event_path.is_file() else ""
    contact_body = contact_path.read_text() if contact_path.is_file() else ""
    # Also confirm via HTTP GET (authoritative protocol path)
    http_event = ""
    http_contact = ""
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{CALDAV_PORT}/caldav/user/calendar/{event_uid}.ics", timeout=3
        ) as r:
            http_event = r.read().decode()
    except Exception as exc:
        http_event = f"ERR:{exc}"
    try:
        with urllib.request.urlopen(
            f"http://127.0.0.1:{CALDAV_PORT}/carddav/user/contacts/{contact_uid}.vcf", timeout=3
        ) as r:
            http_contact = r.read().decode()
    except Exception as exc:
        http_contact = f"ERR:{exc}"
    event_ok = "BEGIN:VEVENT" in event_body and "CX2H4-P0-CAL-EVENT" in event_body and "BEGIN:VEVENT" in http_event
    contact_ok = "BEGIN:VCARD" in contact_body and "peer@cx2h4.test" in contact_body and "BEGIN:VCARD" in http_contact
    return {
        "ok": bool(event_ok and contact_ok),
        "event_ok": event_ok,
        "contact_ok": contact_ok,
        "event_path": str(event_path),
        "contact_path": str(contact_path),
        "event_bytes": len(event_body),
        "contact_bytes": len(contact_body),
        "http_event_prefix": http_event[:120],
        "http_contact_prefix": http_contact[:120],
    }
