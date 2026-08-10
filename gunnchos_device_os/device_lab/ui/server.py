"""Local Device Lab web UI at 127.0.0.1 — controls + fidelity panel.

Framebuffer path: exposes session display topology and optional VNC URL when
configured. Does not fake a screenshot-only VM.
"""
from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from gunnchos_device_os.device_lab.fidelity import FidelityDashboard
from gunnchos_device_os.device_lab.profiles import list_profiles, load_profile
from gunnchos_device_os.device_lab.session import get_session, list_sessions, start_session, stop_session
from gunnchos_device_os.device_lab.virtualization.backend import describe_backends

INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>gunnchDevice Lab</title>
<style>
:root { --bg:#0f1419; --panel:#1a222c; --text:#e7eef7; --accent:#3d9cfd; --muted:#8aa0b5; }
body { margin:0; font-family: "IBM Plex Sans", "Segoe UI", sans-serif; background:
  radial-gradient(1200px 600px at 10% -10%, #1b3a55 0%, transparent 50%),
  linear-gradient(160deg, #0f1419, #121a22 40%, #0c1015); color:var(--text); }
header { padding:1.25rem 1.5rem; border-bottom:1px solid #243041; }
h1 { margin:0; font-size:1.35rem; letter-spacing:.02em; }
.sub { color:var(--muted); font-size:.9rem; margin-top:.35rem; }
main { display:grid; grid-template-columns: 280px 1fr 320px; gap:1rem; padding:1rem; min-height:80vh; }
section { background:var(--panel); border:1px solid #273445; border-radius:10px; padding:1rem; }
button, select { background:#243041; color:var(--text); border:1px solid #35506c; border-radius:8px; padding:.5rem .75rem; margin:.2rem; cursor:pointer; }
button.primary { background:var(--accent); color:#041018; border:none; font-weight:600; }
pre { white-space:pre-wrap; font-size:.8rem; background:#0c1117; padding:.75rem; border-radius:8px; max-height:50vh; overflow:auto; }
.fb { min-height:280px; display:flex; align-items:center; justify-content:center; background:
  repeating-linear-gradient(45deg,#15202b,#15202b 10px,#182533 10px,#182533 20px); border-radius:8px; color:var(--muted); text-align:center; padding:1rem; }
.tag { display:inline-block; padding:.15rem .45rem; border-radius:999px; background:#243041; font-size:.75rem; margin:.1rem; }
</style>
</head>
<body>
<header>
  <h1>gunnchDevice Lab</h1>
  <div class="sub">Foundation v0.1 · 127.0.0.1 only · SILICON_EXACT_EMULATION=false · VF4/5/6 PHYSICAL_PENDING</div>
</header>
<main>
  <section>
    <h2>Choose Device</h2>
    <select id="device"></select>
    <div>
      <button class="primary" onclick="startDev()">START</button>
      <button onclick="stopDev()">STOP</button>
    </div>
    <h3>Dock</h3>
    <button onclick="api('/api/dock?op=attach')">ATTACH DOCK</button>
    <button onclick="api('/api/dock?op=detach')">DETACH DOCK</button>
    <h3>Network</h3>
    <button onclick="api('/api/net?op=offline')">offline</button>
    <button onclick="api('/api/net?op=bad_wifi')">bad_wifi</button>
    <button onclick="api('/api/net?op=network_restore')">restore</button>
    <h3>Storage</h3>
    <button onclick="api('/api/storage?op=remove')">remove removable</button>
    <h3>Rings</h3>
    <button onclick="api('/api/ring?op=click')">inject click</button>
    <button onclick="api('/api/ring?op=low')">low confidence</button>
  </section>
  <section>
    <h2>Session / Framebuffer</h2>
    <div class="fb" id="fb">No fake screenshot VM.<br/>Real display topology + optional VNC/WebRTC when configured.<br/>Instance: <span id="inst">none</span></div>
    <h3>Evidence / status</h3>
    <pre id="out">{}</pre>
  </section>
  <section>
    <h2>Fidelity panel</h2>
    <div id="fid"></div>
    <h3>Backends</h3>
    <pre id="backends"></pre>
  </section>
</main>
<script>
let instanceId = null;
async function refreshDevices(){
  const r = await fetch('/api/devices'); const j = await r.json();
  const sel = document.getElementById('device');
  sel.innerHTML = j.devices.map(d => `<option value="${d.profile_id}">${d.product}</option>`).join('');
}
async function startDev(){
  const profile = document.getElementById('device').value;
  const r = await fetch('/api/start?profile='+encodeURIComponent(profile));
  const j = await r.json(); instanceId = j.instance_id; show(j);
  document.getElementById('inst').textContent = instanceId || 'none';
  renderFid(j.fidelity);
}
async function stopDev(){
  if(!instanceId) return; const r = await fetch('/api/stop?instance='+instanceId); show(await r.json()); instanceId=null;
  document.getElementById('inst').textContent='none';
}
async function api(path){
  if(!instanceId){ show({ok:false,error:'no_instance'}); return; }
  const r = await fetch(path + (path.includes('?')?'&':'?') + 'instance='+instanceId);
  show(await r.json());
}
function show(j){ document.getElementById('out').textContent = JSON.stringify(j,null,2); }
function renderFid(f){
  if(!f) return;
  const el = document.getElementById('fid');
  el.innerHTML = (f.subsystems||[]).map(s => `<div><span class="tag">${s.level}</span> <b>${s.name}</b> — ${s.status}</div>`).join('');
}
refreshDevices();
fetch('/api/fidelity').then(r=>r.json()).then(renderFid);
fetch('/api/backends').then(r=>r.json()).then(j => document.getElementById('backends').textContent=JSON.stringify(j,null,2));
</script>
</body>
</html>
"""


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


class Handler(BaseHTTPRequestHandler):
    def _json(self, code: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, indent=2, default=str).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _html(self, body: str) -> None:
        data = body.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        path = parsed.path
        q = parse_qs(parsed.query)
        root = _repo_root()
        try:
            if path in {"/", "/index.html"}:
                return self._html(INDEX_HTML)
            if path == "/api/devices":
                rows = [
                    {
                        "profile_id": pid,
                        "product": load_profile(pid).get("product"),
                    }
                    for pid in list_profiles()
                ]
                return self._json(200, {"ok": True, "devices": rows})
            if path == "/api/fidelity":
                return self._json(200, FidelityDashboard().to_dict())
            if path == "/api/backends":
                return self._json(200, describe_backends())
            if path == "/api/start":
                profile = (q.get("profile") or ["student_14_5"])[0]
                return self._json(200, start_session(profile, repo_root=root))
            if path == "/api/stop":
                inst = (q.get("instance") or [None])[0]
                return self._json(200, stop_session(inst))
            if path == "/api/status":
                return self._json(200, {"ok": True, "sessions": list_sessions()})
            if path == "/api/dock":
                sess = get_session((q.get("instance") or [""])[0])
                op = (q.get("op") or ["attach"])[0]
                if op == "attach":
                    return self._json(
                        200,
                        {
                            "ok": True,
                            "display": sess.display.appear_external(),
                            "network": sess.network.dock_ethernet_attach(),
                            "audio": sess.audio.dock_attach(),
                            "input": sess.input.dock_desktop_profile(),
                        },
                    )
                return self._json(
                    200,
                    {
                        "ok": True,
                        "display": sess.display.disappear_external(),
                        "network": sess.network.dock_ethernet_detach(),
                        "audio": sess.audio.dock_detach(),
                    },
                )
            if path == "/api/net":
                sess = get_session((q.get("instance") or [""])[0])
                op = (q.get("op") or ["network_restore"])[0]
                return self._json(200, sess.network.apply(op))
            if path == "/api/storage":
                sess = get_session((q.get("instance") or [""])[0])
                return self._json(200, sess.storage.remove_removable())
            if path == "/api/ring":
                sess = get_session((q.get("instance") or [""])[0])
                if sess.rings.spatial is None:
                    sess.rings.start()
                op = (q.get("op") or ["click"])[0]
                if op == "low":
                    return self._json(200, sess.rings.inject(confidence=0.2))
                return self._json(200, sess.rings.inject(confidence=0.9, gesture="click"))
            return self._json(404, {"ok": False, "error": "not_found"})
        except Exception as exc:  # noqa: BLE001
            return self._json(500, {"ok": False, "error": str(exc)})

    def log_message(self, fmt: str, *args: Any) -> None:
        return


def serve(*, host: str = "127.0.0.1", port: int = 8765) -> int:
    if host not in {"127.0.0.1", "localhost", "::1"}:
        print(json.dumps({"ok": False, "error": "host_must_be_loopback"}))
        return 2
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(json.dumps({"ok": True, "url": f"http://{host}:{port}/", "note": "local only"}))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        return 0
    return 0
