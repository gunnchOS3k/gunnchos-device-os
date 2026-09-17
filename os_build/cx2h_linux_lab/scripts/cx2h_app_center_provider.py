#!/usr/bin/env python3
"""CX2H App Center provider API — Flatpak truth only (no marker PASS)."""

from __future__ import annotations

import json
import os
import subprocess
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

APP_ID = "org.gunnchos.CX2HTestApp"
REMOTE = "cx2h-local"
FLATPAK_USER_DIR = os.environ.get("FLATPAK_USER_DIR", "/var/lib/cx2h/flatpak-user")
ENV = {**os.environ, "FLATPAK_USER_DIR": FLATPAK_USER_DIR}
LAST_ACTION: dict = {}
ARCH = os.uname().machine


def run(args, timeout=300):
    return subprocess.run(args, capture_output=True, text=True, env=ENV, timeout=timeout)


def remember(action: str, result: dict) -> dict:
    global LAST_ACTION
    LAST_ACTION = {"action": action, **result}
    try:
        with open("/tmp/cx2h-provider-last.json", "w", encoding="utf-8") as fh:
            json.dump(LAST_ACTION, fh)
    except Exception:
        pass
    return result


def catalog_entry(installed_info: dict | None) -> dict:
    installed = bool(installed_info and installed_info.get("installed"))
    version = (installed_info or {}).get("version") or "1.0.0"
    return {
        "id": APP_ID,
        "name": "CX2H Test App",
        "source": f"flatpak:{REMOTE}",
        "version": version,
        "permissions": ["wayland", "x11", "dri", "host-os"],
        "installed": installed,
        "provenance": "local_flatpak_repo:/var/lib/cx2h/flatpak-repo",
        "branch": (installed_info or {}).get("branch") or "stable",
        "provider": "flatpak",
    }


def flatpak_info() -> dict:
    # Prefer explicit versioned branches when multiple refs are present
    listed = run(
        ["flatpak", "--user", "list", "--app", "--columns=application,branch,version,origin"],
        timeout=60,
    )
    branches = []
    for line in (listed.stdout or "").splitlines():
        if APP_ID not in line:
            continue
        parts = [p for p in line.split("\t") if True]
        # application, branch, version, origin
        if len(parts) >= 2:
            branches.append(
                {
                    "branch": (parts[1] or "").strip(),
                    "version": (parts[2].strip() if len(parts) > 2 else "") or (parts[1] or "").strip(),
                    "origin": (parts[3].strip() if len(parts) > 3 else ""),
                }
            )
    if not branches:
        r = run(["flatpak", "--user", "info", APP_ID], timeout=60)
        if r.returncode != 0:
            return {"installed": False}
        version = None
        branch = None
        for line in (r.stdout or "").splitlines():
            if line.startswith("Version:"):
                version = line.split(":", 1)[1].strip()
            if line.startswith("Branch:"):
                branch = line.split(":", 1)[1].strip()
        if branch in ("1.0.0", "2.0.0"):
            version = branch
        return {"installed": True, "version": version or branch or "unknown", "branch": branch, "raw": r.stdout}

    # Prefer 2.0.0 if present else 1.0.0 else first
    preferred = None
    for want in ("2.0.0", "1.0.0", "stable"):
        for b in branches:
            if b.get("branch") == want:
                preferred = b
                break
        if preferred:
            break
    if not preferred:
        preferred = branches[0]
    branch = preferred.get("branch") or "stable"
    version = preferred.get("version") or branch
    if branch in ("1.0.0", "2.0.0"):
        version = branch
    # Resolve details for the preferred ref
    r = run(["flatpak", "--user", "info", f"{APP_ID}//{branch}"], timeout=60)
    raw = (r.stdout or "") if r.returncode == 0 else (listed.stdout or "")
    return {
        "installed": True,
        "version": version,
        "branch": branch,
        "all_branches": [b.get("branch") for b in branches],
        "raw": raw,
    }


def discover(query: str = "") -> list:
    apps = [catalog_entry(flatpak_info())]
    q = (query or "").lower()
    if not q:
        return apps
    return [a for a in apps if q in a["name"].lower() or q in a["id"].lower()]


def install(version: str = "1.0.0") -> dict:
    branch = version if version in ("1.0.0", "2.0.0", "stable") else "stable"
    run(["flatpak", "--user", "uninstall", "-y", APP_ID], timeout=120)
    run(["flatpak", "build-update-repo", "/var/lib/cx2h/flatpak-repo"], timeout=120)
    # Prefer versioned app refs; include stable alias for catalog installs
    candidates = [
        [REMOTE, f"app/{APP_ID}/{ARCH}/{branch}"],
        [REMOTE, f"{APP_ID}//{branch}"],
        [REMOTE, f"app/{APP_ID}/{ARCH}/stable"],
        [REMOTE, f"{APP_ID}//stable"],
        [REMOTE, APP_ID],
        [f"app/{APP_ID}/{ARCH}/{branch}"],
        [f"{APP_ID}//{branch}"],
        [APP_ID],
    ]
    last = None
    attempts = []
    for args in candidates:
        r = run(["flatpak", "--user", "install", "-y", "--noninteractive", *args], timeout=300)
        last = r
        attempts.append(
            {
                "args": args,
                "rc": r.returncode,
                "stderr": (r.stderr or "")[-400],
                "stdout": (r.stdout or "")[-200],
            }
        )
        info = flatpak_info()
        if info.get("installed"):
            return remember(
                "install",
                {
                    "ok": True,
                    "info": info,
                    "stdout": (r.stdout or "")[-800],
                    "stderr": (r.stderr or "")[-800],
                    "requested_version": version,
                    "install_args": args,
                    "attempts": attempts,
                },
            )
    info = flatpak_info()
    return remember(
        "install",
        {
            "ok": bool(info.get("installed")),
            "info": info,
            "stdout": ((last.stdout if last else "") or "")[-800],
            "stderr": ((last.stderr if last else "") or "")[-800],
            "requested_version": version,
            "attempts": attempts,
        },
    )


def update(version: str = "2.0.0") -> dict:
    before = flatpak_info()
    if not before.get("installed"):
        return remember("update", {"ok": False, "reason": "not_installed"})
    branch = version if version in ("1.0.0", "2.0.0", "stable") else "stable"
    # Replace all installed branches so App Center sees a single active version
    run(["flatpak", "--user", "uninstall", "-y", APP_ID], timeout=180)
    # Also clear any leftover versioned refs
    for b in ("1.0.0", "2.0.0", "stable"):
        run(["flatpak", "--user", "uninstall", "-y", f"{APP_ID}//{b}"], timeout=120)
    r = run(
        ["flatpak", "--user", "install", "-y", "--noninteractive", REMOTE, f"app/{APP_ID}/{ARCH}/{branch}"],
        timeout=300,
    )
    if r.returncode != 0:
        r = run(
            ["flatpak", "--user", "install", "-y", "--noninteractive", REMOTE, f"{APP_ID}//{branch}"],
            timeout=300,
        )
    after = flatpak_info()
    ok = bool(after.get("installed") and (after.get("branch") == branch or after.get("version") == version or branch in (after.get("raw") or "")))
    return remember(
        "update",
        {
            "ok": ok,
            "before": before,
            "after": after,
            "stdout": (r.stdout or "")[-800],
            "stderr": (r.stderr or "")[-800],
        },
    )


def rollback(version: str = "1.0.0") -> dict:
    return update(version=version)


def uninstall() -> dict:
    run(["flatpak", "--user", "uninstall", "-y", APP_ID], timeout=180)
    for b in ("1.0.0", "2.0.0", "stable"):
        run(["flatpak", "--user", "uninstall", "-y", f"{APP_ID}//{b}"], timeout=120)
    info = flatpak_info()
    return remember(
        "uninstall",
        {"ok": not info.get("installed"), "info": info},
    )


def launch() -> dict:
    info = flatpak_info()
    if not info.get("installed"):
        return remember("launch", {"ok": False, "reason": "not_installed"})
    log = "/tmp/cx2h-testapp-launch.log"
    cmd = f"nohup flatpak --user run {APP_ID} >{log} 2>&1 & echo $!"
    p = subprocess.run(["bash", "-lc", cmd], capture_output=True, text=True, env=ENV, timeout=30)
    pid = (p.stdout or "").strip().splitlines()[-1] if p.stdout else ""
    return remember("launch", {"ok": bool(pid.isdigit()), "pid": pid, "info": info, "log": log})


class Handler(BaseHTTPRequestHandler):
    def _json(self, code: int, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._json(200, {"ok": True})

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/health":
            return self._json(200, {"ok": True, "provider": "flatpak"})
        if parsed.path == "/api/apps":
            qs = urllib.parse.parse_qs(parsed.query)
            q = (qs.get("q") or [""])[0]
            return self._json(200, {"provider": "flatpak", "apps": discover(q)})
        if parsed.path == "/api/state":
            return self._json(200, flatpak_info())
        if parsed.path == "/api/last":
            return self._json(200, LAST_ACTION or {"action": None})
        return self._json(404, {"error": "not_found"})

    def do_POST(self):
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw.decode() or "{}")
        except Exception:
            data = {}
        path = urllib.parse.urlparse(self.path).path

        def respond(result: dict):
            code = 200 if result.get("ok") else 500
            return self._json(code, result)

        if path == "/api/install":
            return respond(install(data.get("version") or "1.0.0"))
        if path == "/api/update":
            return respond(update(data.get("version") or "2.0.0"))
        if path == "/api/rollback":
            return respond(rollback(data.get("version") or "1.0.0"))
        if path == "/api/uninstall":
            return respond(uninstall())
        if path == "/api/launch":
            return respond(launch())
        if path == "/api/refresh":
            return self._json(200, {"apps": discover(""), "provider": "flatpak"})
        return self._json(404, {"error": "not_found"})

    def log_message(self, fmt, *args):
        return


def main():
    host, port = "127.0.0.1", int(os.environ.get("CX2H_PROVIDER_PORT", "8766"))
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(f"CX2H_APP_CENTER_PROVIDER listening on http://{host}:{port}", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
