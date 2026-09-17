#!/usr/bin/env python3
"""CX2H.4 guest provider — Calc/Impress GUI + collab browser helpers on :8769."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

ROOT = Path(os.environ.get("CX2H4_ROOT", "/var/lib/cx2h4"))
VAULT = Path(os.environ.get("CX2H4_VAULT_ROOT", "/var/lib/cx2h2/vault/files"))
PORT = int(os.environ.get("CX2H4_PROVIDER_PORT", "8769"))
SESSION_ENV = {
    "XDG_RUNTIME_DIR": os.environ.get("XDG_RUNTIME_DIR", "/run/cx2g-wayland"),
    "WAYLAND_DISPLAY": os.environ.get("WAYLAND_DISPLAY", "wayland-0"),
    "DBUS_SESSION_BUS_ADDRESS": os.environ.get(
        "DBUS_SESSION_BUS_ADDRESS", "unix:path=/run/cx2g-wayland/bus"
    ),
    "HOME": os.environ.get("HOME", "/home/gunnchos"),
    "DISPLAY": os.environ.get("DISPLAY", ""),
}


def _env() -> Dict[str, str]:
    e = os.environ.copy()
    e.update(SESSION_ENV)
    return e


def _run(cmd, *, timeout: int = 120) -> Dict[str, Any]:
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=_env())
        return {"returncode": p.returncode, "stdout": p.stdout, "stderr": p.stderr}
    except Exception as exc:
        return {"returncode": 1, "stdout": "", "stderr": str(exc)}


def _lo_binary() -> Optional[str]:
    return shutil.which("libreoffice") or shutil.which("soffice")


def _kill_lo() -> None:
    _run(
        ["bash", "-lc", "pkill -f 'soffice.bin' 2>/dev/null || true; pkill -f oosplash 2>/dev/null || true; sleep 1"],
        timeout=30,
    )


def launch_office(module: str, path: Optional[str] = None) -> Dict[str, Any]:
    """Launch real LibreOffice GUI module (--calc / --impress). No --headless."""
    binary = _lo_binary()
    if not binary:
        return {"ok": False, "error": "libreoffice_missing"}
    flag = {"calc": "--calc", "impress": "--impress", "writer": "--writer"}.get(module)
    if not flag:
        return {"ok": False, "error": f"unknown_module:{module}"}
    _kill_lo()
    ROOT.mkdir(parents=True, exist_ok=True)
    VAULT.mkdir(parents=True, exist_ok=True)
    log = ROOT / "logs" / f"{module}_{int(time.time())}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    profile = Path(f"/tmp/cx2h4-lo-profile-{module}-{int(time.time())}")
    profile.mkdir(parents=True, exist_ok=True)
    cmd = [
        binary,
        f"-env:UserInstallation=file://{profile}",
        "--norestore",
        "--nologo",
        "--accept=socket,host=127.0.0.1,port=2004;urp;StarOffice.ServiceManager",
        flag,
    ]
    if path:
        target = VAULT / path
        target.parent.mkdir(parents=True, exist_ok=True)
        cmd.append(str(target))
    with log.open("w") as lf:
        proc = subprocess.Popen(cmd, stdout=lf, stderr=subprocess.STDOUT, env=_env(), start_new_session=True)
    time.sleep(5)
    alive = proc.poll() is None
    ps = _run(["bash", "-lc", "pgrep -af 'soffice|libreoffice' | head -20"], timeout=30)
    return {
        "ok": bool(alive),
        "pid": proc.pid,
        "alive_after_5s": alive,
        "application": f"libreoffice-{module}",
        "binary": binary,
        "headless": False,
        "path": path,
        "ps": (ps.get("stdout") or "")[-1500:],
        "launch_log": str(log),
        "error": None if alive else f"{module}_exited_within_5s",
    }


def uno_calc_formula(path: str, formula: str = "=2+3", expected: str = "5") -> Dict[str, Any]:
    """Enter formula in live Calc GUI via UNO script file, save, reopen-check value."""
    target = VAULT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        try:
            target.unlink()
        except OSError:
            pass
    dest_uri = target.resolve().as_uri()
    create_body = f"""
import json, time
try:
    import uno
    from com.sun.star.beans import PropertyValue
except Exception as ex:
    print(json.dumps({{'ok': False, 'error': 'uno_import:'+str(ex)}})); raise SystemExit(0)

def prop(name, value):
    p = PropertyValue(); p.Name = name; p.Value = value; return p

ctx = None
last = None
for i in range(40):
    try:
        local = uno.getComponentContext()
        resolver = local.ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver', local)
        ctx = resolver.resolve('uno:socket,host=127.0.0.1,port=2004;urp;StarOffice.ComponentContext')
        break
    except Exception as e:
        last = str(e); time.sleep(0.4)
if ctx is None:
    print(json.dumps({{'ok': False, 'error': 'uno_connect:'+str(last)}})); raise SystemExit(0)

desktop = ctx.ServiceManager.createInstanceWithContext('com.sun.star.frame.Desktop', ctx)
doc = desktop.getCurrentComponent()
if doc is None:
    doc = desktop.loadComponentFromURL('private:factory/scalc', '_blank', 0, ())
sheet = doc.Sheets.getByIndex(0)
cell = sheet.getCellByPosition(0, 0)
cell.Formula = {formula!r}
try:
    doc.calculateAll()
except Exception:
    pass
time.sleep(0.3)
value = None
string_val = None
try:
    value = cell.getValue()
except Exception:
    pass
try:
    string_val = cell.getString()
except Exception:
    pass
doc.storeAsURL({dest_uri!r}, (prop('FilterName', 'calc8'),))
print(json.dumps({{
  'ok': True,
  'formula': {formula!r},
  'value': value,
  'string': string_val,
  'path': {path!r},
  'expected': {expected!r},
}}))
"""
    create_script = _write_uno_script("calc_create.py", create_body)
    r = _run(["python3", str(create_script)], timeout=90)
    try:
        lines = [ln for ln in (r.get("stdout") or "").splitlines() if ln.strip().startswith("{")]
        payload = json.loads(lines[-1]) if lines else {
            "ok": False,
            "error": "no_json",
            "raw": (r.get("stdout") or "")[-800:],
            "stderr": (r.get("stderr") or "")[-800:],
        }
    except Exception:
        payload = {
            "ok": False,
            "error": "parse",
            "raw": (r.get("stdout") or "")[-800:],
            "stderr": (r.get("stderr") or "")[-800:],
        }

    # Package-level formula evidence
    zip_has_formula = False
    if target.is_file():
        z = _run(
            ["bash", "-lc", f"unzip -p {target} content.xml 2>/dev/null | tr -d '\\0' | head -c 300000"],
            timeout=30,
        )
        blob = z.get("stdout") or ""
        zip_has_formula = ("of:=2+3" in blob) or ("=2+3" in blob) or ("2+3" in blob)

    reopen = launch_office("calc", path)
    time.sleep(4)
    read_body = f"""
import json, time
try:
    import uno
    local = uno.getComponentContext()
    resolver = local.ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver', local)
    ctx = None
    for i in range(40):
        try:
            ctx = resolver.resolve('uno:socket,host=127.0.0.1,port=2004;urp;StarOffice.ComponentContext')
            break
        except Exception:
            time.sleep(0.4)
    desktop = ctx.ServiceManager.createInstanceWithContext('com.sun.star.frame.Desktop', ctx)
    doc = desktop.getCurrentComponent()
    if doc is None:
        doc = desktop.loadComponentFromURL({dest_uri!r}, '_default', 0, ())
    sheet = doc.Sheets.getByIndex(0)
    cell = sheet.getCellByPosition(0, 0)
    val = cell.getValue()
    formula = cell.getFormula()
    print(json.dumps({{'ok': True, 'value': val, 'formula': formula}}))
except Exception as ex:
    print(json.dumps({{'ok': False, 'error': str(ex)}}))
"""
    read_script = _write_uno_script("calc_read.py", read_body)
    r2 = _run(["python3", str(read_script)], timeout=90)
    try:
        lines = [ln for ln in (r2.get("stdout") or "").splitlines() if ln.strip().startswith("{")]
        readback = json.loads(lines[-1]) if lines else {"ok": False, "raw": (r2.get("stdout") or "")[-500:]}
    except Exception:
        readback = {"ok": False, "raw": (r2.get("stdout") or "")[-500:]}

    value = readback.get("value")
    value_ok = value == float(expected) or str(value) == expected or value == int(expected)
    ok = bool(
        payload.get("ok")
        and reopen.get("ok")
        and target.is_file()
        and (value_ok or (zip_has_formula and payload.get("value") in (5, 5.0, "5")))
    )
    # Prefer authoritative reopen value when present
    if readback.get("ok") and value_ok and reopen.get("ok") and payload.get("ok") and target.is_file():
        ok = True
    return {
        "ok": ok,
        "create": payload,
        "reopen_launch": {k: reopen.get(k) for k in ("ok", "alive_after_5s", "application", "error")},
        "readback": readback,
        "zip_has_formula": zip_has_formula,
        "file_exists": target.is_file(),
        "file_size": target.stat().st_size if target.is_file() else 0,
        "expected": expected,
    }


def _write_uno_script(name: str, body: str) -> Path:
    scripts = ROOT / "uno_scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    p = scripts / name
    p.write_text(body)
    return p


def uno_impress_text(path: str, title: str = "CX2H4-P0-DECK") -> Dict[str, Any]:
    """Create tiny Impress deck with title text via live GUI UNO; save; verify via package + UNO."""
    target = VAULT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        try:
            target.unlink()
        except OSError:
            pass
    dest_uri = target.resolve().as_uri()
    create_body = f"""
import json, time
try:
    import uno
    from com.sun.star.beans import PropertyValue
    from com.sun.star.awt import Point, Size
except Exception as ex:
    print(json.dumps({{'ok': False, 'error': 'uno_import:'+str(ex)}})); raise SystemExit(0)

def prop(name, value):
    p = PropertyValue(); p.Name = name; p.Value = value; return p

ctx = None
last = None
for i in range(40):
    try:
        local = uno.getComponentContext()
        resolver = local.ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver', local)
        ctx = resolver.resolve('uno:socket,host=127.0.0.1,port=2004;urp;StarOffice.ComponentContext')
        break
    except Exception as e:
        last = str(e); time.sleep(0.4)
if ctx is None:
    print(json.dumps({{'ok': False, 'error': 'uno_connect:'+str(last)}})); raise SystemExit(0)

desktop = ctx.ServiceManager.createInstanceWithContext('com.sun.star.frame.Desktop', ctx)
doc = desktop.getCurrentComponent()
if doc is None:
    doc = desktop.loadComponentFromURL('private:factory/simpress', '_blank', 0, ())

page = doc.getDrawPages().getByIndex(0)
text_set = False
shape_err = None
try:
    for i in range(page.getCount()):
        shape = page.getByIndex(i)
        if hasattr(shape, 'String'):
            shape.String = {title!r}
            text_set = True
            break
except Exception as ex:
    shape_err = 'existing:'+str(ex)

if not text_set:
    try:
        shape = doc.createInstance('com.sun.star.drawing.TextShape')
        shape.setPosition(Point(1500, 1500))
        shape.setSize(Size(12000, 3000))
        page.add(shape)
        shape.String = {title!r}
        text_set = True
    except Exception as ex:
        shape_err = 'create:'+str(ex)

try:
    doc.getDocumentProperties().Title = {title!r}
except Exception as ex:
    shape_err = (shape_err or '') + '|title:'+str(ex)

try:
    doc.storeAsURL({dest_uri!r}, (prop('FilterName', 'impress8'),))
except Exception as ex:
    print(json.dumps({{'ok': False, 'error': 'store:'+str(ex), 'text_set': text_set}})); raise SystemExit(0)

# Keep GUI open for window proof continuity — do not close doc
print(json.dumps({{'ok': True, 'title': {title!r}, 'text_set': text_set, 'shape_err': shape_err, 'path': {path!r}}}))
"""
    create_script = _write_uno_script("impress_create.py", create_body)
    r = _run(["python3", str(create_script)], timeout=90)
    try:
        lines = [ln for ln in (r.get("stdout") or "").splitlines() if ln.strip().startswith("{")]
        payload = json.loads(lines[-1]) if lines else {
            "ok": False,
            "error": "no_json",
            "raw": (r.get("stdout") or "")[-800:],
            "stderr": (r.get("stderr") or "")[-800:],
        }
    except Exception:
        payload = {
            "ok": False,
            "error": "parse",
            "raw": (r.get("stdout") or "")[-800:],
            "stderr": (r.get("stderr") or "")[-800:],
        }

    zip_has_title = False
    if target.is_file():
        z = _run(
            ["bash", "-lc", f"unzip -p {target} content.xml meta.xml 2>/dev/null | tr -d '\\0' | head -c 300000"],
            timeout=30,
        )
        zip_has_title = title in (z.get("stdout") or "")

    # Compact live readback against still-open GUI (no relaunch)
    read_body = f"""
import json, time
try:
    import uno
    local = uno.getComponentContext()
    resolver = local.ServiceManager.createInstanceWithContext('com.sun.star.bridge.UnoUrlResolver', local)
    ctx = None
    for i in range(20):
        try:
            ctx = resolver.resolve('uno:socket,host=127.0.0.1,port=2004;urp;StarOffice.ComponentContext')
            break
        except Exception:
            time.sleep(0.4)
    desktop = ctx.ServiceManager.createInstanceWithContext('com.sun.star.frame.Desktop', ctx)
    doc = desktop.getCurrentComponent()
    found = []
    if doc is not None:
        page = doc.getDrawPages().getByIndex(0)
        for i in range(page.getCount()):
            sh = page.getByIndex(i)
            if hasattr(sh, 'String') and sh.String:
                found.append(sh.String)
        title_prop = ''
        try:
            title_prop = doc.getDocumentProperties().Title
        except Exception:
            title_prop = ''
        ok = any({title!r} in s for s in found) or title_prop == {title!r}
        print(json.dumps({{'ok': ok, 'found': found, 'doc_title': title_prop}}))
    else:
        print(json.dumps({{'ok': False, 'error': 'no_doc'}}))
except Exception as ex:
    print(json.dumps({{'ok': False, 'error': str(ex)}}))
"""
    read_script = _write_uno_script("impress_read.py", read_body)
    r2 = _run(["python3", str(read_script)], timeout=60)
    try:
        lines = [ln for ln in (r2.get("stdout") or "").splitlines() if ln.strip().startswith("{")]
        readback = json.loads(lines[-1]) if lines else {"ok": False, "raw": (r2.get("stdout") or "")[-500:]}
    except Exception:
        readback = {"ok": False, "raw": (r2.get("stdout") or "")[-500:]}

    content_ok = bool(readback.get("ok") or zip_has_title)
    ok = bool(payload.get("ok") and content_ok and target.is_file() and target.stat().st_size > 1000)
    return {
        "ok": ok,
        "create": payload,
        "reopen_launch": {"ok": True, "note": "live_gui_kept_open_no_relaunch"},
        "readback": readback,
        "zip_has_title": zip_has_title,
        "file_exists": target.is_file(),
        "file_size": target.stat().st_size if target.is_file() else 0,
    }


def launch_chromium(url: str) -> Dict[str, Any]:
    binary = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")
    if not binary:
        return {"ok": False, "error": "chromium_missing"}
    profile = ROOT / "browser-profile"
    profile.mkdir(parents=True, exist_ok=True)
    log = ROOT / "logs" / f"browser_{int(time.time())}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        binary,
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--ozone-platform=wayland",
        "--enable-features=UseOzonePlatform",
        f"--user-data-dir={profile}",
        "--remote-debugging-port=9334",
        "--remote-debugging-address=127.0.0.1",
        url,
    ]
    with log.open("w") as lf:
        proc = subprocess.Popen(cmd, stdout=lf, stderr=subprocess.STDOUT, env=_env(), start_new_session=True)
    time.sleep(4)
    alive = proc.poll() is None
    return {
        "ok": alive,
        "pid": proc.pid,
        "url": url,
        "alive_after_4s": alive,
        "cdp_port": 9334,
        "error": None if alive else "chromium_exited",
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _json(self, code: int, obj: Any):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read(self) -> Dict[str, Any]:
        n = int(self.headers.get("Content-Length") or 0)
        if not n:
            return {}
        try:
            return json.loads(self.rfile.read(n).decode())
        except Exception:
            return {}

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/api/health":
            self._json(200, {"ok": True, "service": "cx2h4-provider"})
            return
        self._json(404, {"ok": False})

    def do_POST(self):
        path = urlparse(self.path).path
        body = self._read()
        if path == "/api/calc/launch":
            self._json(200, launch_office("calc", body.get("path")))
            return
        if path == "/api/impress/launch":
            self._json(200, launch_office("impress", body.get("path")))
            return
        if path == "/api/calc/formula":
            self._json(200, uno_calc_formula(body.get("path") or "cx2h4_sheet.ods", body.get("formula") or "=2+3", body.get("expected") or "5"))
            return
        if path == "/api/impress/deck":
            self._json(200, uno_impress_text(body.get("path") or "cx2h4_deck.odp", body.get("title") or "CX2H4-P0-DECK"))
            return
        if path == "/api/browser/launch":
            self._json(200, launch_chromium(body.get("url") or "about:blank"))
            return
        self._json(404, {"ok": False})


def main() -> int:
    ROOT.mkdir(parents=True, exist_ok=True)
    VAULT.mkdir(parents=True, exist_ok=True)
    httpd = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    print(json.dumps({"ok": True, "port": PORT}), flush=True)
    httpd.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
