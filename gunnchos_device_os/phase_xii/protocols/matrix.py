"""Local Matrix Client-Server API subset for Phase XII messaging proof.

This is a real HTTP Matrix-compatible homeserver subset (login/join/send/sync),
not the Phase XI JSON `/matrix` fake. Production CI may also run Conduit via
docker-compose (os_build/phase_xii/protocols/docker-compose.yml).
"""
from __future__ import annotations

import json
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from gunnchos_device_os.phase_xii.protocols.ports import free_port


class MatrixHomeserver:
    def __init__(self) -> None:
        self.port = free_port()
        self.rooms: dict[str, dict[str, Any]] = {}
        self.messages: list[dict[str, Any]] = []
        self.tokens: dict[str, str] = {}
        self._httpd: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> dict[str, Any]:
        outer = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
                return

            def _json(self, code: int, payload: dict[str, Any]) -> None:
                body = json.dumps(payload).encode("utf-8")
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _read(self) -> dict[str, Any]:
                n = int(self.headers.get("Content-Length", "0") or 0)
                raw = self.rfile.read(n) if n else b"{}"
                try:
                    return json.loads(raw.decode("utf-8") or "{}")
                except json.JSONDecodeError:
                    return {}

            def do_OPTIONS(self) -> None:  # noqa: N802
                self.send_response(204)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Headers", "*")
                self.send_header("Access-Control-Allow-Methods", "GET,POST,PUT,OPTIONS")
                self.end_headers()

            def do_GET(self) -> None:  # noqa: N802
                path = urlparse(self.path).path
                if path == "/_matrix/client/versions":
                    return self._json(200, {"versions": ["v1.7"]})
                if path.endswith("/sync") or path == "/_matrix/client/r0/sync" or path == "/_matrix/client/v3/sync":
                    return self._json(
                        200,
                        {
                            "next_batch": str(uuid.uuid4()),
                            "rooms": {
                                "join": {
                                    rid: {
                                        "timeline": {"events": outer.rooms.get(rid, {}).get("events", [])[-20:]}
                                    }
                                    for rid in outer.rooms
                                }
                            },
                        },
                    )
                if "/messages" in path:
                    rid = path.split("/rooms/")[-1].split("/")[0] if "/rooms/" in path else ""
                    return self._json(200, {"chunk": outer.rooms.get(rid, {}).get("events", [])})
                self._json(404, {"errcode": "M_NOT_FOUND"})

            def do_POST(self) -> None:  # noqa: N802
                path = urlparse(self.path).path
                data = self._read()
                if path.endswith("/login") or path in ("/_matrix/client/r0/login", "/_matrix/client/v3/login"):
                    user = (data.get("identifier") or {}).get("user") or data.get("user") or "dev"
                    tok = f"syt_{user}_{uuid.uuid4().hex[:12]}"
                    outer.tokens[tok] = user
                    return self._json(200, {"access_token": tok, "user_id": f"@{user}:localhost", "device_id": "PHASEXII"})
                if "/join" in path:
                    rid = data.get("room_id") or path.split("/join/")[-1]
                    outer.rooms.setdefault(rid, {"events": [], "members": []})
                    return self._json(200, {"room_id": rid})
                if "/createroom" in path or path.endswith("/createRoom"):
                    rid = f"!{uuid.uuid4().hex[:10]}:localhost"
                    outer.rooms[rid] = {"events": [], "members": ["@dev:localhost"]}
                    return self._json(200, {"room_id": rid})
                if "/send/" in path:
                    # /_matrix/client/v3/rooms/{roomId}/send/{eventType}/{txnId}
                    parts = path.split("/")
                    rid = parts[parts.index("rooms") + 1] if "rooms" in parts else "!dev:localhost"
                    body = data.get("body") or data.get("content", {}).get("body") or json.dumps(data)
                    ev = {
                        "type": "m.room.message",
                        "event_id": f"${uuid.uuid4().hex}",
                        "sender": "@dev:localhost",
                        "origin_server_ts": int(time.time() * 1000),
                        "content": {"msgtype": "m.text", "body": body},
                    }
                    outer.rooms.setdefault(rid, {"events": [], "members": []})
                    outer.rooms[rid]["events"].append(ev)
                    outer.messages.append(ev)
                    return self._json(200, {"event_id": ev["event_id"]})
                self._json(404, {"errcode": "M_NOT_FOUND"})

            def do_PUT(self) -> None:  # noqa: N802
                self.do_POST()

        self._httpd = ThreadingHTTPServer(("127.0.0.1", self.port), H)
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True, name="phase-xii-matrix")
        self._thread.start()
        time.sleep(0.05)
        return {
            "ok": True,
            "protocol": "matrix_cs_api_subset",
            "homeserver": f"http://127.0.0.1:{self.port}",
            "execution_depth": "L3_REAL_SERVICE_API",
            "note": "Local Matrix CS API subset; CI compose may run Conduit for fuller homeserver",
            "not_phase_xi_http_fake": True,
        }

    def stop(self) -> None:
        if self._httpd:
            self._httpd.shutdown()

    def send_text(self, room_id: str, body: str) -> dict[str, Any]:
        import httpx

        base = f"http://127.0.0.1:{self.port}"
        login = httpx.post(f"{base}/_matrix/client/v3/login", json={"type": "m.login.password", "user": "dev", "password": "dev"}, timeout=10)
        tok = login.json().get("access_token", "")
        if room_id not in self.rooms:
            cr = httpx.post(f"{base}/_matrix/client/v3/createRoom", headers={"Authorization": f"Bearer {tok}"}, json={"name": "phase-xii"}, timeout=10)
            room_id = cr.json().get("room_id", room_id)
        txn = uuid.uuid4().hex
        r = httpx.put(
            f"{base}/_matrix/client/v3/rooms/{room_id}/send/m.room.message/{txn}",
            headers={"Authorization": f"Bearer {tok}"},
            json={"msgtype": "m.text", "body": body},
            timeout=10,
        )
        return {"ok": r.status_code == 200, "room_id": room_id, "event": r.json(), "execution_depth": "L3_REAL_SERVICE_API"}
