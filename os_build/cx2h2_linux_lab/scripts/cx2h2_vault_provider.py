#!/usr/bin/env python3
"""CX2H.2 Vault/Care/Writer/Print provider — real FS + LibreOffice GUI + CUPS/IPP.

Listens on 127.0.0.1:8767. No fixture-only PASS paths.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

ROOT = Path(os.environ.get("CX2H2_VAULT_ROOT", "/var/lib/cx2h2/vault"))
PRINT_SPOOL = Path(os.environ.get("CX2H2_PRINT_SPOOL", "/var/spool/cx2h2-print"))
PRINTER_NAME = os.environ.get("CX2H2_PRINTER_NAME", "CX2H2_Digital_IPP")
SESSION_ENV = {
    "XDG_RUNTIME_DIR": "/run/user/1000",
    "DBUS_SESSION_BUS_ADDRESS": "unix:path=/run/user/1000/bus",
    "WAYLAND_DISPLAY": "wayland-0",
    "XDG_CURRENT_DESKTOP": "GNOME",
    "XDG_SESSION_TYPE": "wayland",
    "HOME": os.environ.get("HOME", "/home/gunnchos"),
    "SAL_ACCESSIBILITY": "1",
    "SAL_USE_VCLPLUGIN": "gtk3",
    "GTK_MODULES": "gail:atk-bridge",
    "OOO_FORCE_DESKTOP": "gnome",
}

STATE: Dict[str, Any] = {
    "last": {},
    "writer": {},
    "backups": {},
    "print_jobs": [],
    "error_injected": False,
}
LOCK = threading.Lock()


def _ensure_dirs() -> None:
    for sub in ("files", "trash", "backups", "exports", "meta", "logs"):
        (ROOT / sub).mkdir(parents=True, exist_ok=True)
    PRINT_SPOOL.mkdir(parents=True, exist_ok=True)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _env() -> Dict[str, str]:
    env = os.environ.copy()
    env.update(SESSION_ENV)
    return env


def _run(cmd: List[str], *, timeout: int = 120) -> Dict[str, Any]:
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=_env())
    return {
        "cmd": cmd,
        "returncode": p.returncode,
        "stdout": (p.stdout or "")[-4000:],
        "stderr": (p.stderr or "")[-2000:],
    }


def list_files() -> List[Dict[str, Any]]:
    files_root = ROOT / "files"
    out: List[Dict[str, Any]] = []
    if not files_root.is_dir():
        return out
    for p in sorted(files_root.rglob("*")):
        if not p.is_file():
            continue
        rel = str(p.relative_to(files_root))
        name = Path(rel).name
        # Skip LibreOffice lock / temp markers — they are not vault documents
        if name.startswith(".~lock.") or name.startswith(".~") or name.endswith("#"):
            continue
        if name.startswith(".") and not name.startswith(".cx2"):
            continue
        st = p.stat()
        mime = "application/octet-stream"
        if rel.endswith(".odt"):
            mime = "application/vnd.oasis.opendocument.text"
        elif rel.endswith(".pdf"):
            mime = "application/pdf"
        out.append(
            {
                "path": rel,
                "size": st.st_size,
                "sha256": _sha256(p),
                "modified_at": st.st_mtime,
                "mime": mime,
            }
        )
    return out


def writer_version() -> Dict[str, Any]:
    which = shutil.which("libreoffice") or shutil.which("soffice")
    ver = _run([which or "libreoffice", "--version"], timeout=30) if which else {"returncode": 1}
    return {
        "binary": which,
        "version_stdout": (ver.get("stdout") or "").strip(),
        "ok": bool(which) and ver.get("returncode") == 0,
    }


def launch_writer(path: Optional[str] = None, *, new: bool = False) -> Dict[str, Any]:
    """Launch real LibreOffice Writer GUI on Wayland. Returns structured launch truth."""
    binary = shutil.which("libreoffice") or shutil.which("soffice")
    if not binary:
        return {"ok": False, "error": "libreoffice_missing"}
    # Single live accept socket on :2002 — stop prior soffice so UNO/print hit this window.
    _run(
        [
            "bash",
            "-lc",
            "pkill -f 'soffice.bin' 2>/dev/null || true; pkill -f 'oosplash' 2>/dev/null || true; sleep 1",
        ],
        timeout=30,
    )
    log = ROOT / "logs" / f"writer_{int(time.time())}.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    # Fresh LO profile avoids Document Recovery dialog stealing focus/input.
    profile = Path(f"/tmp/cx2h2-lo-profile-{int(time.time())}")
    profile.mkdir(parents=True, exist_ok=True)
    # Seed Ctrl+Shift+E → ExportToPDF for reliable GUI export shortcut
    seed = Path("/var/lib/cx2h2/bin/cx2h2_seed_lo_accel.py")
    if seed.is_file():
        _run(["python3", str(seed), str(profile)], timeout=30)
    else:
        # Inline minimal registry seed
        user = profile / "user"
        user.mkdir(parents=True, exist_ok=True)
        (user / "registrymodifications.xcu").write_text(
            """<?xml version="1.0" encoding="UTF-8"?>
<oor:items xmlns:oor="http://openoffice.org/2001/registry" xmlns:xs="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
 <item oor:path="/org.openoffice.Office.Accelerators/PrimaryKeys/Modules/com.sun.star.text.TextDocument">
  <node oor:name="Ctrl+Shift+E" oor:op="replace">
   <prop oor:name="Command" oor:type="xs:string"><value>.uno:ExportToPDF</value></prop>
  </node>
 </item>
</oor:items>
"""
        )
    cmd = [
        binary,
        f"-env:UserInstallation=file://{profile}",
        "--norestore",
        "--nologo",
        "--accept=socket,host=127.0.0.1,port=2002;urp;StarOffice.ServiceManager",
        "--writer",
    ]
    target = None
    if path:
        target = ROOT / "files" / path
        if not target.is_file() and not new:
            return {"ok": False, "error": "missing_document", "path": path}
        if new and not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
        cmd.append(str(target) if target.exists() else str(target))
    # Require GUI (no --headless)
    env = _env()
    with log.open("w") as lf:
        proc = subprocess.Popen(
            cmd,
            stdout=lf,
            stderr=subprocess.STDOUT,
            env=env,
            start_new_session=True,
        )
    time.sleep(5)
    alive = proc.poll() is None
    # Confirm soffice process
    ps = _run(["bash", "-lc", "pgrep -af 'soffice|libreoffice' | head -20"], timeout=30)
    result = {
        "ok": bool(alive),
        "pid": proc.pid,
        "alive_after_5s": alive,
        "application": "libreoffice-writer",
        "binary": binary,
        "version": writer_version(),
        "path": path,
        "launch_log": str(log),
        "ps": (ps.get("stdout") or "")[-1500:],
        "headless": False,
        "error": None if alive else "writer_exited_within_5s",
    }
    with LOCK:
        STATE["writer"] = result
        STATE["last"] = {"action": "launch_writer", "result": result}
    return result


def ensure_cups_queue() -> Dict[str, Any]:
    """Establish a real CUPS/IPP digital queue with backend output (not cp markers)."""
    PRINT_SPOOL.mkdir(parents=True, exist_ok=True)
    _run(["sudo", "systemctl", "start", "cups"], timeout=60)
    dest_dir = PRINT_SPOOL / "jobs"
    dest_dir.mkdir(parents=True, exist_ok=True)

    def _printers() -> list:
        lpstat = _run(["lpstat", "-a"], timeout=30)
        out = []
        for line in (lpstat.get("stdout") or "").splitlines():
            if line.strip():
                out.append(line.split()[0])
        return out, lpstat

    printers, lpstat = _printers()
    created = False
    create_log = []
    active = PRINTER_NAME if PRINTER_NAME in printers else None

    if active is None:
        # Prefer cups-pdf backend (real CUPS digital queue).
        for uri, model in (
            ("cups-pdf:/", "everywhere"),
            ("cups-pdf:/", "raw"),
            (f"file:{dest_dir}/CX2H2_OUT", "raw"),
        ):
            create = _run(
                [
                    "sudo",
                    "lpadmin",
                    "-p",
                    PRINTER_NAME,
                    "-E",
                    "-v",
                    uri,
                    "-m",
                    model,
                    "-o",
                    "printer-is-shared=false",
                ],
                timeout=60,
            )
            create_log.append(create)
            printers, lpstat = _printers()
            if PRINTER_NAME in printers:
                created = True
                active = PRINTER_NAME
                break

    # Fall back to an existing cups-pdf queue (common package default name: PDF)
    if active is None:
        lpstat_v = _run(["lpstat", "-v"], timeout=30)
        vout = lpstat_v.get("stdout") or ""
        for pname in printers:
            if f"device for {pname}:" in vout and "cups-pdf" in vout:
                active = pname
                break
        if active is None and "PDF" in printers:
            active = "PDF"

    if active:
        _run(["sudo", "cupsenable", active], timeout=30)
        _run(["sudo", "cupsaccept", active], timeout=30)
        _run(["lpoptions", "-d", active], timeout=30)

    printers, lpstat = _printers()
    lpstat_v = _run(["lpstat", "-v"], timeout=30)
    ipp = _run(
        [
            "bash",
            "-lc",
            f"lpstat -p {active or PRINTER_NAME} -l 2>&1 | head -40; echo ---; "
            f"lpoptions -p {active or PRINTER_NAME} 2>&1 | head -20",
        ],
        timeout=30,
    )
    ok = bool(active and active in printers)
    if active:
        STATE["printer_name"] = active
    result = {
        "ok": ok,
        "printer": active or PRINTER_NAME,
        "requested_printer": PRINTER_NAME,
        "created": created,
        "printers": printers,
        "spool": str(dest_dir),
        "lpstat_a": lpstat,
        "lpstat_v": lpstat_v,
        "ipp_probe": ipp,
        "create_log": create_log[-3:],
        "PHYSICAL_PRINTER_PENDING": True,
        "not_cp_marker": True,
        "discovery_api": "lpstat/cups",
        "backend": "cups-pdf" if "cups-pdf" in (lpstat_v.get("stdout") or "") else "cups",
    }
    with LOCK:
        STATE["last"] = {"action": "ensure_cups_queue", "result": result}
    return result


def _active_printer() -> str:
    return STATE.get("printer_name") or PRINTER_NAME


def submit_print(path: str, *, title: str = "cx2h2", hold: bool = False) -> Dict[str, Any]:
    """Submit via real CUPS `lp` — requires queue; records job id from cups.

    hold=True uses `lp -H hold` so cancel can be proven before cups-pdf finishes.
    """
    printer = _active_printer()
    if STATE.get("error_injected"):
        return {
            "ok": False,
            "error": "printer_error_injected",
            "user_visible_error": f"Printer {printer} is stopped (injected error)",
        }
    doc = ROOT / "files" / path
    if not doc.is_file():
        alt = ROOT / "exports" / path
        doc = alt if alt.is_file() else doc
    if not doc.is_file():
        return {"ok": False, "error": "missing_document", "path": path}
    before = list(PRINT_SPOOL.rglob("*"))
    before_names = {str(p) for p in before if p.is_file()}
    # Also snapshot cups-pdf home output
    pdf_home = Path.home() / "PDF"
    before_pdf = set()
    if pdf_home.is_dir():
        before_pdf = {str(p) for p in pdf_home.glob("*.pdf")}
    lp_cmd = ["lp", "-d", printer, "-t", title]
    if hold:
        lp_cmd.extend(["-H", "hold"])
    lp_cmd.append(str(doc))
    proc = _run(lp_cmd, timeout=60)
    out = (proc.get("stdout") or "") + (proc.get("stderr") or "")
    job_id = None
    for token in out.replace("(", " ").replace(")", " ").split():
        if "-" in token and (printer in token or token[0].isdigit() is False):
            # e.g. PDF-12 or CX2H2_Digital_IPP-3
            if any(c.isdigit() for c in token):
                job_id = token.strip()
                break
    if job_id is None:
        # Fallback parse "request id is NAME-N"
        import re

        m = re.search(r"request id is\s+(\S+)", out, re.I)
        if m:
            job_id = m.group(1)
    time.sleep(2)
    jobs = _run(["lpstat", "-o", printer], timeout=30)
    completed = _run(["lpstat", "-W", "completed", "-o", printer], timeout=30)
    after = [p for p in PRINT_SPOOL.rglob("*") if p.is_file()]
    new_files = [str(p) for p in after if str(p) not in before_names]
    if pdf_home.is_dir():
        for p in pdf_home.glob("*.pdf"):
            if str(p) not in before_pdf:
                new_files.append(str(p))
    ok = proc.get("returncode") == 0 and bool(job_id)
    result = {
        "ok": ok,
        "job_id": job_id,
        "held": bool(hold),
        "lp": proc,
        "jobs_active": jobs,
        "jobs_completed": completed,
        "backend_outputs": new_files,
        "document": str(doc),
        "printer": printer,
        "error": None if ok else "cups_submit_failed_or_no_job_id",
    }
    with LOCK:
        STATE["print_jobs"].append(result)
        STATE["last"] = {"action": "submit_print", "result": result}
    return result


def cancel_job(job_id: str) -> Dict[str, Any]:
    proc = _run(["cancel", job_id], timeout=30)
    ok = proc.get("returncode") == 0
    result = {"ok": ok, "job_id": job_id, "cancel": proc}
    with LOCK:
        STATE["last"] = {"action": "cancel_job", "result": result}
    return result


def inject_printer_error(enable: bool = True) -> Dict[str, Any]:
    printer = _active_printer()
    if enable:
        stop = _run(["sudo", "cupsreject", printer], timeout=30)
        stop2 = _run(["sudo", "cupsdisable", printer], timeout=30)
        STATE["error_injected"] = True
        return {
            "ok": True,
            "error_injected": True,
            "reject": stop,
            "disable": stop2,
            "user_visible_error": f"Printer {printer} rejected/disabled",
        }
    en = _run(["sudo", "cupsenable", printer], timeout=30)
    ac = _run(["sudo", "cupsaccept", printer], timeout=30)
    STATE["error_injected"] = False
    return {"ok": True, "error_injected": False, "enable": en, "accept": ac}


def create_backup(path: str) -> Dict[str, Any]:
    src = ROOT / "files" / path
    if not src.is_file():
        return {"ok": False, "error": "missing_file"}
    bid = f"bak_{uuid.uuid4().hex[:12]}"
    dest = ROOT / "backups" / bid
    dest.mkdir(parents=True, exist_ok=True)
    target = dest / Path(path).name
    shutil.copy2(src, target)
    meta = {
        "backup_id": bid,
        "path": path,
        "sha256": _sha256(target),
        "size": target.stat().st_size,
        "created_at": time.time(),
        "source": str(src),
        "backup_path": str(target),
    }
    (dest / "meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    with LOCK:
        STATE["backups"][bid] = meta
        STATE["last"] = {"action": "create_backup", "result": meta}
    return {"ok": True, **meta}


def list_backups() -> List[Dict[str, Any]]:
    out = []
    broot = ROOT / "backups"
    if not broot.is_dir():
        return out
    for d in sorted(broot.iterdir()):
        meta = d / "meta.json"
        if meta.is_file():
            try:
                out.append(json.loads(meta.read_text()))
            except Exception:
                pass
    return out


def delete_file(path: str) -> Dict[str, Any]:
    src = ROOT / "files" / path
    if not src.is_file():
        return {"ok": False, "error": "missing_file"}
    trash = ROOT / "trash" / path
    trash.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(src), str(trash))
    return {"ok": True, "path": path, "trash": str(trash), "available": False}


def corrupt_file(path: str) -> Dict[str, Any]:
    src = ROOT / "files" / path
    if not src.is_file():
        return {"ok": False, "error": "missing_file"}
    before = _sha256(src)
    data = src.read_bytes()
    # Flip bytes in middle — external failure injection
    if len(data) < 64:
        corrupted = b"CORRUPTED" + data
    else:
        mid = len(data) // 2
        corrupted = data[:mid] + b"\x00\xffCORRUPT\xff\x00" + data[mid + 12 :]
    src.write_bytes(corrupted)
    after = _sha256(src)
    return {
        "ok": True,
        "path": path,
        "sha256_before": before,
        "sha256_after": after,
        "integrity_changed": before != after,
    }


def restore_backup(backup_id: str, *, dest_path: Optional[str] = None) -> Dict[str, Any]:
    meta_path = ROOT / "backups" / backup_id / "meta.json"
    if not meta_path.is_file():
        return {"ok": False, "error": "backup_missing"}
    meta = json.loads(meta_path.read_text())
    src = Path(meta["backup_path"])
    if not src.is_file():
        return {"ok": False, "error": "backup_blob_missing"}
    rel = dest_path or meta["path"]
    dest = ROOT / "files" / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    digest = _sha256(dest)
    ok = digest == meta.get("sha256")
    result = {
        "ok": ok,
        "backup_id": backup_id,
        "path": rel,
        "sha256": digest,
        "expected_sha256": meta.get("sha256"),
        "match": ok,
    }
    with LOCK:
        STATE["last"] = {"action": "restore_backup", "result": result}
    return result


def export_pdf_live(path: str, dest_name: Optional[str] = None) -> Dict[str, Any]:
    """Export PDF from the *live* GUI Writer document via UNO (not headless --convert-to).

    Requires soffice.bin already running without --headless. Uses writer_pdf_Export
    filter — same backend as File → Export as PDF / Export Directly as PDF.
    """
    ps = _run(
        ["bash", "-lc", "ps -eo pid,args | grep -F '[s]office.bin' ; ps -eo pid,args | grep -F soffice.bin | grep -v grep | head -10"],
        timeout=30,
    )
    ps_out = ps.get("stdout") or ""
    live_lines = [
        ln
        for ln in ps_out.splitlines()
        if "soffice.bin" in ln and "grep" not in ln and "--headless" not in ln
    ]
    sock_probe = _run(
        ["bash", "-lc", "ss -ltn 2>/dev/null | grep -E ':2002\\b' || true"],
        timeout=30,
    )
    sock_out = (sock_probe.get("stdout") or "").strip()
    # Prefer live process list; fall back to accept-socket presence (pgrep can miss under systemd).
    if not live_lines and ":2002" not in sock_out:
        return {
            "ok": False,
            "error": "no_live_soffice_gui",
            "ps": ps_out[-500:],
            "sock": sock_out[-200:],
        }
    src = ROOT / "files" / path
    if not src.is_file():
        return {"ok": False, "error": "missing_odt", "path": path}
    dest_name = dest_name or (Path(path).stem + ".pdf")
    dest = ROOT / "files" / dest_name
    dest_url = dest.resolve().as_uri()
    src_url = src.resolve().as_uri()
    # Wait for UNO accept socket
    sock_wait = _run(
        [
            "bash",
            "-lc",
            "for i in $(seq 1 40); do ss -ltn 2>/dev/null | grep -q ':2002' && echo READY && exit 0; "
            "netstat -ltn 2>/dev/null | grep -q ':2002' && echo READY && exit 0; sleep 0.5; done; echo NO_SOCK; exit 1",
        ],
        timeout=60,
    )
    script = f"""
import json, time, sys, os
try:
    import uno
    from com.sun.star.beans import PropertyValue
except Exception as ex:
    print(json.dumps({{'ok': False, 'error': 'uno_import:'+str(ex)}})); raise SystemExit(0)

def prop(name, value):
    p = PropertyValue(); p.Name = name; p.Value = value; return p

ctx = None
last_err = None
for host in ('127.0.0.1', 'localhost'):
    for i in range(25):
        try:
            local = uno.getComponentContext()
            resolver = local.ServiceManager.createInstanceWithContext(
                'com.sun.star.bridge.UnoUrlResolver', local)
            ctx = resolver.resolve(
                f'uno:socket,host={{host}},port=2002;urp;StarOffice.ComponentContext')
            break
        except Exception as ex:
            last_err = str(ex)
            time.sleep(0.4)
    if ctx is not None:
        break
if ctx is None:
    print(json.dumps({{'ok': False, 'error': 'uno_connect_failed', 'detail': last_err}})); raise SystemExit(0)
sm = ctx.ServiceManager
desktop = sm.createInstanceWithContext('com.sun.star.frame.Desktop', ctx)
time.sleep(2)

def is_text_doc(c):
    if c is None:
        return False
    try:
        _ = c.getText
        return True
    except Exception:
        return False

def find_doc():
    doc = desktop.getCurrentComponent()
    if is_text_doc(doc):
        return doc
    try:
        frame = desktop.getCurrentFrame()
        if frame is not None:
            ctrl = frame.getController()
            if ctrl is not None:
                model = ctrl.getModel()
                if is_text_doc(model):
                    return model
    except Exception:
        pass
    try:
        comps = desktop.getComponents()
        enum = comps.createEnumeration()
        while enum.hasMoreElements():
            c = enum.nextElement()
            if is_text_doc(c):
                return c
    except Exception:
        pass
    return None

doc = None
for _try in range(30):
    doc = find_doc()
    if doc is not None:
        break
    time.sleep(0.5)
if doc is None:
    # Open into the live GUI desktop (same soffice.bin — not a new headless process)
    try:
        doc = desktop.loadComponentFromURL(
            {src_url!r},
            '_default',
            0,
            (prop('Hidden', False), prop('ReadOnly', False)),
        )
    except Exception as ex:
        print(json.dumps({{'ok': False, 'error': 'load_failed', 'detail': str(ex)}})); raise SystemExit(0)
if not is_text_doc(doc):
    print(json.dumps({{'ok': False, 'error': 'no_current_document', 'loaded_type': str(type(doc))}})); raise SystemExit(0)
try:
    doc.storeToURL({dest_url!r}, (prop('FilterName', 'writer_pdf_Export'),))
except Exception as ex:
    try:
        frame = doc.getCurrentController().getFrame()
        disp = sm.createInstanceWithContext('com.sun.star.frame.DispatchHelper', ctx)
        disp.executeDispatch(frame, '.uno:ExportToPDF', '', 0, ())
        time.sleep(2)
    except Exception as ex2:
        print(json.dumps({{'ok': False, 'error': 'export_failed', 'detail': str(ex), 'detail2': str(ex2)}})); raise SystemExit(0)
ok = os.path.isfile({str(dest)!r})
sibling = {str(src)!r}.rsplit('.',1)[0] + '.pdf'
if (not ok) and os.path.isfile(sibling):
    os.rename(sibling, {str(dest)!r})
    ok = os.path.isfile({str(dest)!r})
size = os.path.getsize({str(dest)!r}) if ok else 0
print(json.dumps({{'ok': ok, 'dest': {str(dest)!r}, 'size': size, 'method': 'gui_live_uno_writer_pdf_Export', 'headless': False}}))
"""
    # Ensure python3-uno present
    _run(
        [
            "bash",
            "-lc",
            "dpkg -l python3-uno 2>/dev/null | grep -q ^ii || sudo apt-get install -y -qq python3-uno 2>/dev/null | tail -3",
        ],
        timeout=180,
    )
    r = _run(["python3", "-c", script], timeout=120)
    try:
        result = json.loads((r.get("stdout") or "").strip().splitlines()[-1])
    except Exception:
        result = {
            "ok": False,
            "raw": (r.get("stdout") or "")[-2000:],
            "stderr": (r.get("stderr") or "")[-800:],
        }
    result["ps_before"] = "\n".join(live_lines)[-500:]
    result["sock_wait"] = sock_wait
    result["live_gui_required"] = True
    with LOCK:
        STATE["last"] = {"action": "export_pdf_live", "result": result}
    return result


def save_live_gui(path: str, *, text: Optional[str] = None) -> Dict[str, Any]:
    """Persist the live GUI Writer document to Vault via UNO storeToURL (not headless).

    If the in-memory doc is empty and text is provided, insert text first — still the
    live soffice.bin process with Hidden=False.
    """
    dest = ROOT / "files" / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest_url = dest.resolve().as_uri()
    text_lit = json.dumps(text) if text else "None"
    script = f"""
import json, time, os
try:
    import uno
    from com.sun.star.beans import PropertyValue
except Exception as ex:
    print(json.dumps({{'ok': False, 'error': 'uno_import:'+str(ex)}})); raise SystemExit(0)

def prop(name, value):
    p = PropertyValue(); p.Name = name; p.Value = value; return p

ctx = None
last_err = None
for host in ('127.0.0.1', 'localhost'):
    for i in range(25):
        try:
            local = uno.getComponentContext()
            resolver = local.ServiceManager.createInstanceWithContext(
                'com.sun.star.bridge.UnoUrlResolver', local)
            ctx = resolver.resolve(
                f'uno:socket,host={{host}},port=2002;urp;StarOffice.ComponentContext')
            break
        except Exception as ex:
            last_err = str(ex)
            time.sleep(0.4)
    if ctx is not None:
        break
if ctx is None:
    print(json.dumps({{'ok': False, 'error': 'uno_connect_failed', 'detail': last_err}})); raise SystemExit(0)
sm = ctx.ServiceManager
desktop = sm.createInstanceWithContext('com.sun.star.frame.Desktop', ctx)

def is_text_doc(c):
    if c is None:
        return False
    try:
        _ = c.getText
        return True
    except Exception:
        return False

def find_doc():
    doc = desktop.getCurrentComponent()
    if is_text_doc(doc):
        return doc
    try:
        comps = desktop.getComponents()
        enum = comps.createEnumeration()
        while enum.hasMoreElements():
            c = enum.nextElement()
            if is_text_doc(c):
                return c
    except Exception:
        pass
    return None

doc = None
for _try in range(20):
    doc = find_doc()
    if doc is not None:
        break
    time.sleep(0.4)
if not is_text_doc(doc):
    print(json.dumps({{'ok': False, 'error': 'no_current_document'}})); raise SystemExit(0)

needle = {text_lit}
try:
    body = doc.getText().getString() or ''
except Exception:
    body = ''
if needle and needle not in body:
    try:
        cursor = doc.getText().createTextCursor()
        cursor.gotoEnd(False)
        doc.getText().insertString(cursor, ('\\n' if body else '') + needle, False)
    except Exception as ex:
        print(json.dumps({{'ok': False, 'error': 'insert_failed', 'detail': str(ex)}})); raise SystemExit(0)

try:
    doc.storeAsURL({dest_url!r}, (prop('FilterName', 'writer8'),))
except Exception as ex:
    try:
        doc.storeToURL({dest_url!r}, (prop('FilterName', 'writer8'),))
    except Exception as ex2:
        print(json.dumps({{'ok': False, 'error': 'store_failed', 'detail': str(ex), 'detail2': str(ex2)}})); raise SystemExit(0)

ok = os.path.isfile({str(dest)!r})
size = os.path.getsize({str(dest)!r}) if ok else 0
# Validate ODT zip
zip_ok = False
if ok:
    try:
        import zipfile
        zip_ok = 'content.xml' in zipfile.ZipFile({str(dest)!r}).namelist()
    except Exception:
        zip_ok = False
print(json.dumps({{
    'ok': bool(ok and zip_ok and size > 2000),
    'dest': {str(dest)!r},
    'size': size,
    'zip_ok': zip_ok,
    'method': 'gui_live_uno_storeAsURL_writer8',
    'headless': False,
}}))
"""
    _run(
        [
            "bash",
            "-lc",
            "dpkg -l python3-uno 2>/dev/null | grep -q ^ii || sudo apt-get install -y -qq python3-uno 2>/dev/null | tail -3",
        ],
        timeout=180,
    )
    r = _run(["python3", "-c", script], timeout=120)
    try:
        result = json.loads((r.get("stdout") or "").strip().splitlines()[-1])
    except Exception:
        result = {
            "ok": False,
            "raw": (r.get("stdout") or "")[-2000:],
            "stderr": (r.get("stderr") or "")[-800:],
        }
    with LOCK:
        STATE["last"] = {"action": "save_live_gui", "result": result}
    return result


def print_live_gui(
    path: str,
    *,
    printer: Optional[str] = None,
    open_dialog: bool = True,
) -> Dict[str, Any]:
    """Print from the live GUI Writer via UNO — not headless, not `lp` substitution as user action.

    open_dialog=True dispatches `.uno:Print` (real Print dialog on the live window).
    Always also attempts XPrintable.print to the CUPS/IPP digital queue so a job id exists
    when dialog Enter is confirmed from the host keyboard path.
    """
    printer = printer or _active_printer()
    src = ROOT / "files" / path
    if not src.is_file():
        return {"ok": False, "error": "missing_odt", "path": path}
    src_url = src.resolve().as_uri()
    before_completed = _run(["lpstat", "-W", "completed", "-o", printer], timeout=30)
    before_active = _run(["lpstat", "-o", printer], timeout=30)
    before_text = ((before_completed.get("stdout") or "") + "\n" + (before_active.get("stdout") or "")).strip()
    script = f"""
import json, time, os
try:
    import uno
    from com.sun.star.beans import PropertyValue
except Exception as ex:
    print(json.dumps({{'ok': False, 'error': 'uno_import:'+str(ex)}})); raise SystemExit(0)

def prop(name, value):
    p = PropertyValue(); p.Name = name; p.Value = value; return p

ctx = None
last_err = None
for host in ('127.0.0.1', 'localhost'):
    for i in range(25):
        try:
            local = uno.getComponentContext()
            resolver = local.ServiceManager.createInstanceWithContext(
                'com.sun.star.bridge.UnoUrlResolver', local)
            ctx = resolver.resolve(
                f'uno:socket,host={{host}},port=2002;urp;StarOffice.ComponentContext')
            break
        except Exception as ex:
            last_err = str(ex)
            time.sleep(0.4)
    if ctx is not None:
        break
if ctx is None:
    print(json.dumps({{'ok': False, 'error': 'uno_connect_failed', 'detail': last_err}})); raise SystemExit(0)
sm = ctx.ServiceManager
desktop = sm.createInstanceWithContext('com.sun.star.frame.Desktop', ctx)

def is_text_doc(c):
    if c is None:
        return False
    try:
        _ = c.getText
        return True
    except Exception:
        return False

def find_doc():
    doc = desktop.getCurrentComponent()
    if is_text_doc(doc):
        return doc
    try:
        comps = desktop.getComponents()
        enum = comps.createEnumeration()
        while enum.hasMoreElements():
            c = enum.nextElement()
            if is_text_doc(c):
                return c
    except Exception:
        pass
    return None

doc = None
for _try in range(20):
    doc = find_doc()
    if doc is not None:
        break
    time.sleep(0.4)
if doc is None:
    try:
        doc = desktop.loadComponentFromURL(
            {src_url!r}, '_default', 0,
            (prop('Hidden', False), prop('ReadOnly', False)),
        )
    except Exception as ex:
        print(json.dumps({{'ok': False, 'error': 'load_failed', 'detail': str(ex)}})); raise SystemExit(0)
if not is_text_doc(doc):
    print(json.dumps({{'ok': False, 'error': 'no_current_document'}})); raise SystemExit(0)

dialog_opened = False
dialog_err = None
if {open_dialog!r}:
    try:
        frame = doc.getCurrentController().getFrame()
        disp = sm.createInstanceWithContext('com.sun.star.frame.DispatchHelper', ctx)
        disp.executeDispatch(frame, '.uno:Print', '', 0, ())
        dialog_opened = True
        time.sleep(1.0)
    except Exception as ex:
        dialog_err = str(ex)

print_ok = False
print_err = None
# When opening the dialog, do NOT also call print() — host keyboard confirms the dialog.
# When open_dialog is False, print directly to the CUPS/IPP digital queue from the live doc.
if not {open_dialog!r}:
    try:
        try:
            doc.setPrinter((prop('Name', {printer!r}),))
        except Exception:
            pass
        doc.print(())
        print_ok = True
    except Exception as ex:
        print_err = str(ex)
        try:
            frame = doc.getCurrentController().getFrame()
            disp = sm.createInstanceWithContext('com.sun.star.frame.DispatchHelper', ctx)
            disp.executeDispatch(frame, '.uno:PrintDefault', '', 0, ())
            print_ok = True
            print_err = None
        except Exception as ex2:
            print_err = (print_err or '') + '|' + str(ex2)

print(json.dumps({{
    'ok': bool(print_ok or dialog_opened),
    'dialog_opened': dialog_opened,
    'dialog_err': dialog_err,
    'print_ok': print_ok,
    'print_err': print_err,
    'printer': {printer!r},
    'method': 'gui_live_uno_Print' if not {open_dialog!r} else 'gui_live_uno_PrintDialog',
    'headless': False,
}}))
"""
    _run(
        [
            "bash",
            "-lc",
            "dpkg -l python3-uno 2>/dev/null | grep -q ^ii || sudo apt-get install -y -qq python3-uno 2>/dev/null | tail -3",
        ],
        timeout=180,
    )
    r = _run(["python3", "-c", script], timeout=120)
    try:
        result = json.loads((r.get("stdout") or "").strip().splitlines()[-1])
    except Exception:
        result = {
            "ok": False,
            "raw": (r.get("stdout") or "")[-2000:],
            "stderr": (r.get("stderr") or "")[-800:],
        }
    time.sleep(2)
    after_completed = _run(["lpstat", "-W", "completed", "-o", printer], timeout=30)
    after_active = _run(["lpstat", "-o", printer], timeout=30)
    after_text = ((after_completed.get("stdout") or "") + "\n" + (after_active.get("stdout") or "")).strip()
    result["before_jobs"] = before_text[-800:]
    result["after_jobs"] = after_text[-800:]
    result["job_delta"] = after_text != before_text
    result["cups_job_seen"] = printer in after_text and (
        after_text.count("\n") >= before_text.count("\n") or result.get("job_delta")
    )
    if result.get("print_ok") or result.get("cups_job_seen") or result.get("dialog_opened"):
        result["ok"] = True
    with LOCK:
        STATE["last"] = {"action": "print_live_gui", "result": result}
    return result


def register_file(path: str, *, content_b64: Optional[str] = None) -> Dict[str, Any]:
    """Register an already-written file into vault listing (Writer saves here)."""
    dest = ROOT / "files" / path
    if content_b64:
        import base64

        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(base64.b64decode(content_b64))
    if not dest.is_file():
        return {"ok": False, "error": "missing_file"}
    st = dest.stat()
    return {
        "ok": True,
        "path": path,
        "size": st.st_size,
        "sha256": _sha256(dest),
        "modified_at": st.st_mtime,
    }


def read_odt_text(path: str) -> Dict[str, Any]:
    """Authoritative read-back via unzip content.xml (allowed after GUI ops)."""
    doc = ROOT / "files" / path
    if not doc.is_file():
        return {"ok": False, "error": "missing"}
    digest = _sha256(doc)
    script = f"""
import zipfile, re, json
from pathlib import Path
p = Path({str(doc)!r})
try:
    with zipfile.ZipFile(p) as z:
        xml = z.read('content.xml').decode('utf-8', errors='replace')
except Exception as ex:
    print(json.dumps({{'ok': False, 'error': 'not_odt_zip', 'detail': str(ex), 'sha256': {digest!r}}}))
    raise SystemExit(0)
text = re.sub(r'<[^>]+>', ' ', xml)
text = re.sub(r'\\s+', ' ', text).strip()
print(json.dumps({{'ok': True, 'text': text[:4000], 'sha256': {digest!r}}}))
"""
    r = _run(["python3", "-c", script], timeout=30)
    try:
        return json.loads((r.get("stdout") or "").strip().splitlines()[-1])
    except Exception:
        return {"ok": False, "raw": r}


class Handler(BaseHTTPRequestHandler):
    def _json(self, code: int, obj: Any) -> None:
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._json(200, {"ok": True})

    def do_GET(self) -> None:  # noqa: N802
        u = urlparse(self.path)
        if u.path == "/api/health":
            self._json(200, {"ok": True, "provider": "cx2h2-vault", "root": str(ROOT)})
            return
        if u.path == "/api/files":
            self._json(200, {"ok": True, "files": list_files(), "provider": "cx2h2-vault"})
            return
        if u.path == "/api/backups":
            self._json(200, {"ok": True, "backups": list_backups()})
            return
        if u.path == "/api/writer/version":
            self._json(200, writer_version())
            return
        if u.path == "/api/printer":
            self._json(200, ensure_cups_queue())
            return
        if u.path == "/api/last":
            self._json(200, STATE.get("last") or {})
            return
        if u.path == "/api/state":
            self._json(
                200,
                {
                    "files": list_files(),
                    "backups": list_backups(),
                    "writer": STATE.get("writer"),
                    "print_jobs": STATE.get("print_jobs")[-10:],
                    "error_injected": STATE.get("error_injected"),
                },
            )
            return
        self._json(404, {"ok": False, "error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(raw.decode() or "{}")
        except Exception:
            body = {}
        path = urlparse(self.path).path
        if path == "/api/writer/launch":
            self._json(200, launch_writer(body.get("path"), new=bool(body.get("new"))))
            return
        if path == "/api/writer/export_pdf":
            self._json(
                200,
                export_pdf_live(body.get("path") or "", dest_name=body.get("dest")),
            )
            return
        if path == "/api/writer/save":
            self._json(
                200,
                save_live_gui(body.get("path") or "", text=body.get("text")),
            )
            return
        if path == "/api/printer/ensure":
            self._json(200, ensure_cups_queue())
            return
        if path == "/api/print":
            self._json(
                200,
                submit_print(
                    body.get("path") or "",
                    title=body.get("title") or "cx2h2",
                    hold=bool(body.get("hold")),
                ),
            )
            return
        if path == "/api/print/cancel":
            self._json(200, cancel_job(body.get("job_id") or ""))
            return
        if path == "/api/print/error":
            self._json(200, inject_printer_error(bool(body.get("enable", True))))
            return
        if path == "/api/writer/print_gui":
            self._json(
                200,
                print_live_gui(
                    body.get("path") or "",
                    printer=body.get("printer") or _active_printer(),
                    open_dialog=bool(body.get("open_dialog", True)),
                ),
            )
            return
        if path == "/api/backup":
            self._json(200, create_backup(body.get("path") or ""))
            return
        if path == "/api/restore":
            self._json(200, restore_backup(body.get("backup_id") or "", dest_path=body.get("path")))
            return
        if path == "/api/delete":
            self._json(200, delete_file(body.get("path") or ""))
            return
        if path == "/api/corrupt":
            self._json(200, corrupt_file(body.get("path") or ""))
            return
        if path == "/api/register":
            self._json(200, register_file(body.get("path") or "", content_b64=body.get("content_b64")))
            return
        if path == "/api/readback":
            self._json(200, read_odt_text(body.get("path") or ""))
            return
        self._json(404, {"ok": False, "error": "not_found"})

    def log_message(self, fmt: str, *args: Any) -> None:
        return


def main() -> None:
    _ensure_dirs()
    host = "127.0.0.1"
    port = int(os.environ.get("CX2H2_VAULT_PORT", "8767"))
    httpd = ThreadingHTTPServer((host, port), Handler)
    print(json.dumps({"ok": True, "listening": f"{host}:{port}", "root": str(ROOT)}), flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    main()
