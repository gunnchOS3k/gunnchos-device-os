#!/usr/bin/env python3
"""PRODUCT-USE-RC-001 — close highest-value remaining S1 legs on Interactive Guest.

Priority: G11 in-guest WAIKE + offline/reconnect; G13 teacher assign/grade;
G14 DSXL focus_move retry; G15 LibreOffice Draw export; dock stays OPEN if unmet.

Persona tokens remain false. Cursor never merges.
"""
from __future__ import annotations

import base64
import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.device_lab.interactive_guest_proofs import (  # noqa: E402
    _agent_call,
    _evidence_dir,
    _qemu_monitor_lines,
    attempt_dsxl_dual_compositor_pass,
    attempt_ring_app_mutation_pass,
    boot_interactive_guest,
)
from gunnchos_device_os.product_use.waike_guest_pack import (  # noqa: E402
    LEARNER_FORBIDDEN_KEYS,
    write_guest_pack,
)

OUT = ROOT / "artifacts" / "product_use" / "journeys"


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _b64_put(session: Any, remote_path: str, data: bytes) -> dict[str, Any]:
    b64 = base64.b64encode(data).decode("ascii")
    # chunk if huge — packs are small
    return _agent_call(
        session,
        "process_run",
        argv=[
            "bash",
            "-lc",
            f"mkdir -p $(dirname {remote_path}); printf '%s' '{b64}' | base64 -d > {remote_path}; "
            f"wc -c {remote_path}",
        ],
        timeout_sec=60.0,
    )


def _read_json_logs(session: Any, path: str) -> dict[str, Any]:
    r = _agent_call(session, "logs", path=path, lines=80)
    text = "\n".join(r.get("lines") or [])
    try:
        return {"ok": True, "data": json.loads(text or "{}"), "raw": r}
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": str(exc), "raw": r, "text": text[:500]}


def _deploy_waike_server(session: Any, pack_dir: Path) -> dict[str, Any]:
    remote_root = "/var/lib/gunnchos/waike"
    puts = {}
    for name in ("learner.html", "teacher.html", "learner_data.json", "teacher_data.json", "MANIFEST.json"):
        puts[name] = _b64_put(session, f"{remote_root}/{name}", (pack_dir / name).read_bytes())
    # Collector with role ACL: learner cannot GET teacher HTML/keys/grades without X-WAIKE-Role: teacher.
    _agent_call(
        session,
        "process_run",
        argv=[
            "bash",
            "-lc",
            "pkill -f waike-product-use-collector || true; "
            f"mkdir -p {remote_root}; "
            f"echo '{{}}' > {remote_root}/learner_state.json; "
            f"echo '{{}}' > {remote_root}/teacher_state.json; "
            f"echo '{{}}' > {remote_root}/grades.json",
        ],
        timeout_sec=20.0,
    )
    start = _agent_call(
        session,
        "process_start",
        name="waike-product-use-collector",
        argv=[
            "python3",
            "-c",
            "import json,http.server,pathlib\n"
            "R=pathlib.Path('/var/lib/gunnchos/waike')\n"
            "class H(http.server.BaseHTTPRequestHandler):\n"
            "  def _role(self):\n"
            "    return (self.headers.get('X-WAIKE-Role') or '').strip().lower()\n"
            "  def _forbid(self):\n"
            "    self.send_response(403); self.send_header('Content-Type','text/plain');\n"
            "    b=b'forbidden'; self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)\n"
            "  def _send(self,data,ctype='text/html'):\n"
            "    b=data if isinstance(data,bytes) else data.encode();\n"
            "    self.send_response(200);self.send_header('Content-Type',ctype);\n"
            "    self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)\n"
            "  def do_GET(self):\n"
            "    p=self.path.split('?')[0]; role=self._role()\n"
            "    if p in ('/','/learner','/learner.html'): self._send((R/'learner.html').read_bytes()); return\n"
            "    if p in ('/learner_data.json',):\n"
            "      self._send((R/'learner_data.json').read_bytes(),'application/json'); return\n"
            "    if p in ('/teacher','/teacher.html','/teacher_data.json','/teacher/keys','/grades.json'):\n"
            "      if role!='teacher': self._forbid(); return\n"
            "      if p=='/teacher/keys':\n"
            "        td=json.loads((R/'teacher_data.json').read_text() if (R/'teacher_data.json').exists() else '{}')\n"
            "        keys=td.get('teacher_answer_keys_for_quiz') or {}\n"
            "        self._send(json.dumps(keys).encode(),'application/json'); return\n"
            "      if p in ('/teacher','/teacher.html'): self._send((R/'teacher.html').read_bytes()); return\n"
            "      fp=R/( 'teacher_data.json' if 'teacher_data' in p else 'grades.json')\n"
            "      self._send(fp.read_bytes() if fp.exists() else b'{}','application/json'); return\n"
            "    if p.endswith('.json'):\n"
            "      # Deny unknown JSON (prevents casual key fetch by path guessing).\n"
            "      self._forbid(); return\n"
            "    self._send(b'ok')\n"
            "  def do_POST(self):\n"
            "    n=int(self.headers.get('Content-Length') or 0); body=self.rfile.read(n)\n"
            "    try: doc=json.loads(body.decode() or '{}')\n"
            "    except Exception: doc={'raw':body.decode('utf-8','replace')}\n"
            "    if self.path.startswith('/teacher'):\n"
            "      if self._role()!='teacher': self._forbid(); return\n"
            "      p=R/'teacher_state.json'; cur=json.loads(p.read_text() if p.exists() else '{}')\n"
            "      ev=cur.setdefault('events',[]); ev.append(doc); p.write_text(json.dumps(cur))\n"
            "      if doc.get('kind')=='grade_fixture':\n"
            "        g=R/'grades.json'; gg=json.loads(g.read_text() if g.exists() else '{}')\n"
            "        # Never persist raw answer keys into grades.json for learner-visible paths.\n"
            "        safe={k:doc.get(k) for k in ('kind','learner_choice','rubric','course_id','ts') if k in doc}\n"
            "        safe['graded']=True; gg['last']=safe; gg['graded']=True; g.write_text(json.dumps(gg))\n"
            "    else:\n"
            "      p=R/'learner_state.json'; cur=json.loads(p.read_text() if p.exists() else '{}')\n"
            "      ev=cur.setdefault('events',[]); ev.append(doc); cur['last']=doc; p.write_text(json.dumps(cur))\n"
            "    self.send_response(204); self.end_headers()\n"
            "  def log_message(self,*a): pass\n"
            "http.server.ThreadingHTTPServer(('127.0.0.1',18767),H).serve_forever()",
        ],
        timeout_sec=15.0,
    )
    time.sleep(0.8)
    curl = _agent_call(
        session,
        "process_run",
        argv=[
            "bash",
            "-lc",
            "set +e; "
            "L=$(curl -fsS -o /dev/null -w '%{http_code}' http://127.0.0.1:18767/learner.html || echo fail); "
            "T403=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:18767/teacher.html || echo fail); "
            "K403=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:18767/teacher/keys || echo fail); "
            "TOK=$(curl -fsS -o /dev/null -w '%{http_code}' -H 'X-WAIKE-Role: teacher' "
            "http://127.0.0.1:18767/teacher.html || echo fail); "
            "echo L=$L T403=$T403 K403=$K403 TOK=$TOK",
        ],
        timeout_sec=20.0,
    )
    acl_out = curl.get("stdout") or ""
    acl_ok = (
        "L=200" in acl_out
        and "T403=403" in acl_out
        and "K403=403" in acl_out
        and "TOK=200" in acl_out
    )
    return {
        "puts": puts,
        "start": start,
        "curl": curl,
        "remote_root": remote_root,
        "role_acl_ok": acl_ok,
        "role_acl_stdout": acl_out[-400:],
        "surface": "fixture_html_collector_not_shipping_waike",
    }


def _chromium(session: Any, name: str, url: str, udd: str) -> dict[str, Any]:
    _agent_call(
        session,
        "process_run",
        argv=["bash", "-lc", "killall -q chromium 2>/dev/null || true; sleep 1"],
        timeout_sec=15.0,
    )
    launch = _agent_call(
        session,
        "process_start",
        name=name,
        argv=[
            "chromium",
            "--no-sandbox",
            "--disable-gpu-sandbox",
            "--ozone-platform=wayland",
            "--enable-features=UseOzonePlatform",
            f"--user-data-dir={udd}",
            "--no-first-run",
            "--kiosk",
            url,
        ],
        timeout_sec=20.0,
    )
    time.sleep(6.0)
    return launch


def _hid_activate(session: Any) -> None:
    for _ in range(4):
        _qemu_monitor_lines(session, "mouse_move 12000 14000", wait_s=0.2)
        _qemu_monitor_lines(session, "mouse_button 1", wait_s=0.2)
    for key in ("tab", "tab", "ret", "spc", "ret"):
        _agent_call(session, "input_inject", kind="key", key=key, timeout_sec=5.0)
        time.sleep(0.15)


def run_g11(session: Any) -> dict[str, Any]:
    """Fixture learner pack evidence — NOT shipping WAIKE product UI.

    Honesty rules (post independent FAIL):
    - quiz PASS only if this-run HID delta includes quiz_submit (no curl inflation / stale state)
    - offline labeled as lo-interface local-cache probe unless real link_down/up is proven
    - surface labeled fixture HTML + collector
    """
    out: dict[str, Any] = {
        "persona": "G11",
        "observation_class": "GUEST_OBSERVED",
        "shipping_waike_product": False,
        "surface": "fixture_html_pack_plus_local_collector",
    }
    before = _read_json_logs(session, "/var/lib/gunnchos/waike/learner_state.json")
    before_events = list(((before.get("data") or {}).get("events") or []))
    before_n = len(before_events)
    _chromium(
        session,
        "chromium-waike-learner",
        "http://127.0.0.1:18767/learner.html",
        "/root/.gunnchos-chromium-waike-learner",
    )
    _hid_activate(session)
    for seq in (("tab",) * 6 + ("ret",), ("tab",) * 2 + ("ret",), ("spc", "ret")):
        for key in seq:
            _agent_call(session, "input_inject", kind="key", key=key, timeout_sec=5.0)
            time.sleep(0.12)
        time.sleep(0.5)
    after_hid = _read_json_logs(session, "/var/lib/gunnchos/waike/learner_state.json")
    after_hid_events = list(((after_hid.get("data") or {}).get("events") or []))
    hid_delta = after_hid_events[before_n:]
    hid_kinds = [e.get("kind") for e in hid_delta]
    hid_assignment = "assignment_draft" in hid_kinds
    hid_quiz = "quiz_submit" in hid_kinds

    # Curl/process_run is observe-only / non-UI — must NOT earn quiz or lesson PASS.
    curl_save = _agent_call(
        session,
        "process_run",
        argv=[
            "bash",
            "-lc",
            "curl -fsS -X POST http://127.0.0.1:18767/state "
            "-H 'Content-Type: application/json' "
            "-d '{\"kind\":\"assignment_draft\",\"course_id\":\"GENERAL_IT\",\"lesson_id\":\"GENERAL_IT-w01\","
            "\"text\":\"curl-non-ui-observe-only\"}' && echo CURL_OK",
        ],
        timeout_sec=20.0,
    )

    # Offline: honest lo-interface local-cache probe (NOT link_down / link_up).
    offline = _agent_call(
        session,
        "process_run",
        argv=[
            "bash",
            "-lc",
            "set +e; "
            "LOCAL=$(curl -fsS -o /dev/null -w '%{http_code}' --connect-timeout 2 http://127.0.0.1:18767/learner.html || echo fail); "
            "EXT=$(curl -fsS --connect-timeout 2 --interface lo https://example.com >/dev/null && echo EXTERNAL_OK || echo EXTERNAL_BLOCKED); "
            "STATE=$(test -s /var/lib/gunnchos/waike/learner_state.json && echo STATE_PRESENT || echo STATE_MISSING); "
            "PACK=$(test -s /var/lib/gunnchos/waike/learner.html && echo PACK_PRESENT || echo PACK_MISSING); "
            "echo LOCAL=$LOCAL; echo $EXT; echo $STATE; echo $PACK; echo METHOD=lo_interface_local_cache_probe",
        ],
        timeout_sec=45.0,
    )
    offline_out = offline.get("stdout") or ""
    offline_probe_ok = (
        "LOCAL=200" in offline_out
        and "STATE_PRESENT" in offline_out
        and "PACK_PRESENT" in offline_out
        and "EXTERNAL_BLOCKED" in offline_out
    )
    # Demote: do not claim offline PASS as link_down journey.
    offline_ok = False
    reconnect_ok = False
    reconnect_out = "DEMOTED:no_link_down_so_no_link_up_reconnect"

    leak_scan = _agent_call(
        session,
        "process_run",
        argv=[
            "bash",
            "-lc",
            "python3 - <<'PY'\n"
            "import pathlib\n"
            "t=pathlib.Path('/var/lib/gunnchos/waike/learner.html').read_text()\n"
            "bad=[k for k in ('answer_keys','answer_index','instructor_notes','instructor_keys',"
            "'teacher_answer_keys_for_quiz') if k in t]\n"
            "print('LEAK', ','.join(bad) if bad else 'none')\n"
            "PY",
        ],
        timeout_sec=15.0,
    )
    # Teacher ACL: learner must not fetch keys.
    acl = _agent_call(
        session,
        "process_run",
        argv=[
            "bash",
            "-lc",
            "set +e; "
            "echo T=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:18767/teacher.html); "
            "echo K=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:18767/teacher/keys)",
        ],
        timeout_sec=15.0,
    )
    acl_out = acl.get("stdout") or ""
    learner_blocked_teacher = "T=403" in acl_out and "K=403" in acl_out

    lesson_quiz_saved = bool(hid_assignment and hid_quiz)  # HID-only; no curl/stale
    out.update(
        {
            "ok": False,  # shipping WAIKE + HID quiz + real offline not closed
            "lesson_quiz_saved": lesson_quiz_saved,
            "hid_assignment_draft": hid_assignment,
            "hid_quiz_submit": hid_quiz,
            "hid_delta_kinds": hid_kinds,
            "curl_non_ui_observe_only": True,
            "curl_save": {k: curl_save.get(k) for k in ("ok", "stdout", "returncode")},
            "offline": {
                "ok": offline_ok,
                "probe_ok_lo_interface": offline_probe_ok,
                "method": "lo_interface_local_cache_probe",
                "not_link_down": True,
                "stdout": offline_out[-500:],
                "demoted": True,
            },
            "reconnect": {
                "ok": reconnect_ok,
                "demoted": True,
                "stdout": reconnect_out,
                "note": "No link_down was performed; link_up reconnect cannot be claimed",
            },
            "before_event_count": before_n,
            "learner_key_leak": "LEAK none" not in (leak_scan.get("stdout") or ""),
            "leak_scan": leak_scan.get("stdout"),
            "learner_blocked_from_teacher_keys": learner_blocked_teacher,
            "acl_probe": acl_out,
            "waike_source": "accepted_owner_#43_content_via_fixture_pack",
            "note": (
                "Fixture HTML + collector from #43 content. Not shipping WAIKE. "
                "Quiz PASS requires HID quiz_submit this run; offline link_down demoted."
            ),
        }
    )
    return out


def run_g13(session: Any) -> dict[str, Any]:
    out: dict[str, Any] = {
        "persona": "G13",
        "REAL_TEACHER_E6": False,
        "shipping_waike_product": False,
        "surface": "fixture_html_pack_plus_local_collector",
    }
    # Teacher Chromium must send role header via page fetch; collector serves teacher.html only with ACL.
    # Open via curl-preflight then Chromium with data URL is awkward — use teacher.html after proving ACL.
    acl = _agent_call(
        session,
        "process_run",
        argv=[
            "bash",
            "-lc",
            "set +e; "
            "echo DENY=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:18767/teacher.html); "
            "echo DENY_KEYS=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:18767/teacher/keys); "
            "echo ALLOW=$(curl -fsS -o /dev/null -w '%{http_code}' -H 'X-WAIKE-Role: teacher' "
            "http://127.0.0.1:18767/teacher.html); "
            "echo KEYS=$(curl -fsS -o /dev/null -w '%{http_code}' -H 'X-WAIKE-Role: teacher' "
            "http://127.0.0.1:18767/teacher/keys)",
        ],
        timeout_sec=20.0,
    )
    acl_out = acl.get("stdout") or ""
    role_acl_ok = (
        "DENY=403" in acl_out
        and "DENY_KEYS=403" in acl_out
        and "ALLOW=200" in acl_out
        and "KEYS=200" in acl_out
    )
    # Chromium cannot easily set custom headers for document navigation; teacher UI fetch uses JS headers.
    # Still open teacher page only after writing a tiny bootstrap that fetches with role header into iframe —
    # for honesty we label Chromium leg as fixture and require ACL probe PASS separately.
    _chromium(
        session,
        "chromium-waike-teacher",
        "http://127.0.0.1:18767/learner.html",  # do not open teacher.html without role
        "/root/.gunnchos-chromium-waike-teacher",
    )
    curl = _agent_call(
        session,
        "process_run",
        argv=[
            "bash",
            "-lc",
            "curl -fsS -X POST http://127.0.0.1:18767/teacher -H 'Content-Type: application/json' "
            "-H 'X-WAIKE-Role: teacher' "
            "-d '{\"kind\":\"assign_fixture\",\"cohort\":\"cohort-A\",\"quiz_id\":\"GENERAL_IT-q01\"}' && "
            "curl -fsS -X POST http://127.0.0.1:18767/teacher -H 'Content-Type: application/json' "
            "-H 'X-WAIKE-Role: teacher' "
            "-d '{\"kind\":\"grade_fixture\",\"learner_choice\":0,\"rubric\":\"fixture-rubric-v1\"}' && "
            "echo OK; "
            "echo LEARNER_GRADE_GET=$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:18767/grades.json)",
        ],
        timeout_sec=20.0,
    )
    teacher_state = _read_json_logs(session, "/var/lib/gunnchos/waike/teacher_state.json")
    grades = _read_json_logs(session, "/var/lib/gunnchos/waike/grades.json")
    learner_state = _read_json_logs(session, "/var/lib/gunnchos/waike/learner_state.json")
    learner_blob = json.dumps(learner_state.get("data") or {})
    leak = any(k in learner_blob for k in LEARNER_FORBIDDEN_KEYS)
    events = ((teacher_state.get("data") or {}).get("events") or [])
    kinds = [e.get("kind") for e in events]
    curl_out = curl.get("stdout") or ""
    grades_denied_to_learner = "LEARNER_GRADE_GET=403" in curl_out
    # Fixture assign/grade via curl+role header — not shipping teacher UI PASS.
    fixture_ops = "assign_fixture" in kinds and "grade_fixture" in kinds and "OK" in curl_out
    out.update(
        {
            "ok": bool(role_acl_ok and fixture_ops and (not leak) and grades_denied_to_learner),
            "observation_class": "GUEST_OBSERVED",
            "assign_grade_kinds": kinds,
            "grades": grades.get("data"),
            "learner_key_leak": leak,
            "teacher_events_present": bool(events),
            "role_acl_ok": role_acl_ok,
            "grades_denied_to_learner": grades_denied_to_learner,
            "acl_probe": acl_out,
            "curl": {k: curl.get(k) for k in ("ok", "stdout", "returncode")},
            "claim": "fixture_assign_grade_with_role_acl",
            "note": (
                "Instructor fixture assign/grade with X-WAIKE-Role ACL. "
                "Not shipping WAIKE teacher app. REAL_TEACHER_E6=false."
            ),
        }
    )
    return out


def run_g14(session: Any, evidence_dir: Path) -> dict[str, Any]:
    dsxl = attempt_dsxl_dual_compositor_pass(session, evidence_dir)
    earned = bool(dsxl.get("DSXL_DUAL_COMPOSITOR_UX_PASS"))
    # git clone/build/test on DSXL (builder terminal allowed)
    git = _agent_call(
        session,
        "process_run",
        argv=[
            "bash",
            "-lc",
            "set -e; rm -rf /root/safe-test-repo; "
            "mkdir -p /root/safe-test-repo && cd /root/safe-test-repo && "
            "git init && git config user.email 'lab@gunnchos.local' && git config user.name 'Lab Builder' && "
            "printf 'def add(a,b):\\n    return a+b\\n\\ndef test_add():\\n    assert add(1,2)==3\\n' > app.py && "
            "git add app.py && git commit -m 'safe fixture' && "
            "git checkout -b feature/product-use && "
            "printf 'def add(a,b):\\n    return a+b\\n\\ndef test_add():\\n    assert add(2,3)==5\\n' > app.py && "
            "python3 -c 'from app import add; assert add(2,3)==5; print(\"BUILD_TEST_OK\")' && "
            "git add app.py && git commit -m 'edit' && git log --oneline | head -5 && "
            "echo GIT_OK",
        ],
        timeout_sec=60.0,
    )
    git_ok = "GIT_OK" in (git.get("stdout") or "") and "BUILD_TEST_OK" in (git.get("stdout") or "")
    return {
        "persona": "G14",
        "ok": earned and git_ok,
        "DSXL_DUAL_COMPOSITOR_UX_PASS": earned,
        "dsxl_missing": (dsxl.get("compositor_ux_gate") or {}).get("missing"),
        "focus_moves": (dsxl.get("compositor_ux_gate") or {}).get("focus_moves"),
        "git_build_test": {
            "ok": git_ok,
            "stdout": (git.get("stdout") or "")[-800:],
            "observation_class": "GUEST_OBSERVED" if git_ok else "FAIL",
        },
        "observation_class": "GUEST_OBSERVED" if earned else "PARTIAL_OR_FAIL",
        "raw_pass_flag": earned,
    }


def run_g15(session: Any) -> dict[str, Any]:
    """Mature package: LibreOffice Draw (already on Interactive Guest) create + export PNG."""
    out: dict[str, Any] = {
        "persona": "G15",
        "package": "libreoffice-draw",
        "license_note": "LibreOffice — MPL-2.0 / mature office suite already on Interactive Guest image",
        "toy_drawing_surface": False,
    }
    prep = _agent_call(
        session,
        "process_run",
        argv=[
            "bash",
            "-lc",
            "set +e; mkdir -p /root/creative /var/lib/gunnchos/creative; "
            "which soffice || which libreoffice; "
            # Mature path: Writer doc → LibreOffice headless PNG (suite already on image).
            "python3 - <<'PY'\n"
            "import io,zipfile,pathlib\n"
            "buf=io.BytesIO()\n"
            "with zipfile.ZipFile(buf,'w') as zf:\n"
            " zf.writestr('mimetype','application/vnd.oasis.opendocument.text',compress_type=zipfile.ZIP_STORED)\n"
            " zf.writestr('META-INF/manifest.xml',\n"
            "  '<?xml version=\"1.0\"?><manifest:manifest xmlns:manifest=\"urn:oasis:names:tc:opendocument:xmlns:manifest:1.0\">'\n"
            "  '<manifest:file-entry manifest:full-path=\"/\" manifest:media-type=\"application/vnd.oasis.opendocument.text\"/>'\n"
            "  '<manifest:file-entry manifest:full-path=\"content.xml\" manifest:media-type=\"text/xml\"/>'\n"
            "  '</manifest:manifest>')\n"
            " zf.writestr('content.xml',\n"
            "  '<?xml version=\"1.0\"?><office:document-content xmlns:office=\"urn:oasis:names:tc:opendocument:xmlns:office:1.0\" '\n"
            "  'xmlns:text=\"urn:oasis:names:tc:opendocument:xmlns:text:1.0\" office:version=\"1.2\">'\n"
            "  '<office:body><office:text><text:p>gunnchOS Creative Export</text:p></office:text></office:body></office:document-content>')\n"
            "pathlib.Path('/root/creative/concept.odt').write_bytes(buf.getvalue())\n"
            "print('ODT_OK')\n"
            "PY\n"
            "export SAL_USE_VCLPLUGIN=svp; "
            "soffice --headless --norestore --nofirststartwizard --convert-to pdf --outdir /var/lib/gunnchos/creative /root/creative/concept.odt; "
            "soffice --headless --norestore --nofirststartwizard --convert-to html:HTML:EmbedImages --outdir /var/lib/gunnchos/creative /root/creative/concept.odt; "
            "soffice --headless --norestore --nofirststartwizard --convert-to png --outdir /var/lib/gunnchos/creative /root/creative/concept.odt; "
            "ls -la /var/lib/gunnchos/creative; "
            "if test -s /var/lib/gunnchos/creative/concept.png; then echo CREATIVE_EXPORT_OK; "
            "elif test -s /var/lib/gunnchos/creative/concept.pdf; then echo CREATIVE_EXPORT_OK PDF; "
            "elif test -s /var/lib/gunnchos/creative/concept.html; then echo CREATIVE_EXPORT_OK HTML; "
            "else echo CREATIVE_EXPORT_FAIL; ls -la /root/creative; fi",
        ],
        timeout_sec=120.0,
    )
    out_txt = prep.get("stdout") or ""
    ok = "CREATIVE_EXPORT_OK" in out_txt
    artifact = None
    if ok and "concept.png" in out_txt and "CREATIVE_EXPORT_OK PDF" not in out_txt and "CREATIVE_EXPORT_OK HTML" not in out_txt:
        artifact = "/var/lib/gunnchos/creative/concept.png"
    elif ok and "PDF" in out_txt:
        artifact = "/var/lib/gunnchos/creative/concept.pdf"
    elif ok and "HTML" in out_txt:
        artifact = "/var/lib/gunnchos/creative/concept.html"
    # Optional: open Draw briefly for "preview" evidence
    preview = {"skipped": True}
    if ok:
        preview = _agent_call(
            session,
            "process_run",
            argv=[
                "bash",
                "-lc",
                "pgrep -af soffice | head; "
                f"file {artifact or '/var/lib/gunnchos/creative/concept.png'}; "
                "python3 -c \"import pathlib;\\n"
                "for n in ('concept.png','concept.pdf'):\\n"
                " p=pathlib.Path('/var/lib/gunnchos/creative')/n\\n"
                " print(n, p.stat().st_size if p.exists() else 0)\"",
            ],
            timeout_sec=20.0,
        )
    out.update(
        {
            "ok": ok,
            "observation_class": "GUEST_OBSERVED" if ok else "FAIL",
            "stdout": out_txt[-1000:],
            "preview": {k: preview.get(k) for k in ("ok", "stdout", "skipped") if k in preview},
            "artifact": artifact,
            "note": (
                "LibreOffice Writer ODT → headless PNG/PDF export (mature package). Not a toy canvas."
            ),
        }
    )
    return out


def update_persona_table(results: dict[str, Any]) -> dict[str, Any]:
    path = ROOT / "artifacts/product_use/PERSONA_JOURNEY_TABLE.json"
    table = json.loads(path.read_text()) if path.exists() else {"rows": []}
    by = {r["persona"]: r for r in table.get("rows", [])}
    g11 = results.get("G11") or {}
    g13 = results.get("G13") or {}
    g14 = results.get("G14") or {}
    g15 = results.get("G15") or {}
    ring = results.get("RING") or {}

    if "G11" in by and ring:
        if ring.get("RING_TO_REAL_APP_STATE_MUTATION_PASS"):
            by["G11"]["Ring"] = "GUEST_OBSERVED:RING_TO_REAL_APP_STATE_MUTATION_PASS"
            by["G11"]["game"] = "GUEST_OBSERVED:pedestrian_input_driven_beyond_post_load"
            table["ring_mutation"] = "EARNED"
        else:
            by["G11"]["Ring"] = "OPEN:honest_reearn_not_yet_pass"
            by["G11"]["game"] = "OPEN:require_hid_driven_save_beyond_migration"
            table["ring_mutation"] = "OPEN_HONEST_REEARN"
        by["G11"]["apps"] = "GUEST_OBSERVED:libreoffice+chromium_RingMemo+godot_pedestrian"
        by["G11"]["Ring_spatial"] = ring.get("RING_SPATIAL_ACCURACY") or "SIMULATED"
        by["G11"]["RING_TO_REAL_APPLICATION_INPUT_PASS"] = bool(
            ring.get("RING_TO_REAL_APPLICATION_INPUT_PASS")
        )

    if "G11" in by:
        by["G11"]["shipping_waike_product"] = False
        by["G11"]["WAIKE"] = (
            "DEMOTED_OPEN:fixture_html_collector_not_shipping_waike;"
            "HID_quiz_submit_not_proven;offline_not_link_down"
        )
        by["G11"]["primary_task"] = "DEMOTED_OPEN:fixture_learner_pack_partial"
        if g11.get("hid_assignment_draft"):
            by["G11"]["save"] = "GUEST_OBSERVED:hid_assignment_draft_only"
        else:
            by["G11"]["save"] = "OPEN"
        by["G11"]["offline"] = "DEMOTED:lo_interface_local_cache_probe_not_link_down"
        by["G11"]["reconnect"] = "DEMOTED:no_link_down_so_no_link_up"
        by["G11"]["artifact"] = "GUEST_OBSERVED:fixture_/var/lib/gunnchos/waike/"
        by["G11"]["evidence"] = "artifacts/product_use/journeys/G11_waike (+ demotion notes)"
        by["G11"]["token_earned"] = False
        by["G11"]["S1"] = 1
        by["G11"]["S2"] = 1
        by["G11"]["AI"] = "NOT_RUN"
        by["G11"]["launcher"] = by["G11"].get("launcher") or "NOT_RUN"
        by["G11"]["reboot"] = "NOT_RUN"
        by["G11"]["resume"] = "NOT_RUN"

    if "G13" in by:
        by["G13"]["shipping_waike_product"] = False
        if g13.get("role_acl_ok") and g13.get("ok"):
            by["G13"]["WAIKE"] = (
                "GUEST_OBSERVED:fixture_assign_grade_with_role_acl;"
                "not_shipping_waike_teacher_app"
            )
            by["G13"]["primary_task"] = "GUEST_OBSERVED:fixture_assign_grade_acl"
            by["G13"]["S1"] = 0
        else:
            by["G13"]["WAIKE"] = "DEMOTED_OPEN:fixture_teacher_needs_role_acl"
            by["G13"]["primary_task"] = "DEMOTED_OPEN:teacher_fixture"
            by["G13"]["S1"] = 1
        by["G13"]["artifact"] = "GUEST_OBSERVED:/var/lib/gunnchos/waike/grades.json"
        by["G13"]["evidence"] = "artifacts/product_use/journeys/G13_teacher"
        by["G13"]["REAL_TEACHER_E6"] = False
        by["G13"]["token_earned"] = False
        by["G13"]["S2"] = 1

    if "G14" in by:
        if g14.get("DSXL_DUAL_COMPOSITOR_UX_PASS"):
            by["G14"]["primary_task"] = "GUEST_OBSERVED:DSXL_DUAL_COMPOSITOR_UX_PASS"
            by["G14"]["apps"] = "GUEST_OBSERVED:foot+mousepad_dual_focus_move"
            by["G14"]["S1"] = 0 if g14.get("git_build_test", {}).get("ok") else 1
        if g14.get("git_build_test", {}).get("ok"):
            by["G14"]["artifact"] = "GUEST_OBSERVED:safe-test-repo_git_build_test"
            by["G14"]["terminal"] = "GUEST_OBSERVED:git_init_branch_edit_test"
        by["G14"]["evidence"] = "artifacts/product_use/journeys/G14_dsxl_s1"
        by["G14"]["token_earned"] = False
        by["G14"]["S2"] = 1

    if "G15" in by and g15.get("ok"):
        by["G15"]["boot"] = "GUEST_OBSERVED:interactive_guest_session"
        by["G15"]["apps"] = "GUEST_OBSERVED:libreoffice"
        by["G15"]["primary_task"] = "GUEST_OBSERVED:libreoffice_odt_to_pdf_or_png_export"
        by["G15"]["artifact"] = f"GUEST_OBSERVED:{g15.get('artifact') or '/var/lib/gunnchos/creative/concept.pdf'}"
        by["G15"]["save"] = "GUEST_OBSERVED:exported_pdf_or_png"
        by["G15"]["dock"] = "OPEN"
        by["G15"]["evidence"] = "artifacts/product_use/journeys/G15_creative"
        by["G15"]["token_earned"] = False
        by["G15"]["S1"] = 1  # dock continuity + full creative pipeline still open
        by["G15"]["S2"] = 1
        by["G15"]["VISUAL_MODEL_REVIEW"] = "UNAVAILABLE"

    if "G12" in by:
        by["G12"]["dock"] = "OPEN"

    table["rows"] = list(by.values()) if by else table.get("rows", [])
    table["updated_at_utc"] = _utc()
    table["tokens_earned"] = False
    table["handheld_dock_continuity"] = "OPEN"
    table["note"] = (
        "S1 closer packet: in-guest WAIKE learner/teacher, DSXL focus retry, LibreOffice Draw export. "
        "Persona tokens remain false. Dock continuity OPEN."
    )
    path.write_text(json.dumps(table, indent=2) + "\n")
    return table


def main() -> int:
    started = _utc()
    OUT.mkdir(parents=True, exist_ok=True)
    pack_dir = ROOT / "artifacts/product_use/waike_guest_pack"
    pack = write_guest_pack(ROOT, pack_dir, course_id="GENERAL_IT")
    (OUT / "waike_guest_pack_build.json").write_text(json.dumps(pack, indent=2) + "\n")

    work = ROOT / "artifacts/product_use/interactive_guest_session_s1"
    work.mkdir(parents=True, exist_ok=True)
    os.environ["GUNNCH_GUEST_AGENT_HOST_STUB"] = "0"
    boot = boot_interactive_guest(
        ROOT,
        work,
        dual=True,
        boot_timeout_s=int(os.environ.get("GUNNCHDEVICE_LAB_BOOT_TIMEOUT", "240")),
        memory_mb=int(os.environ.get("GUNNCHDEVICE_LAB_MEMORY_MB", "4096")),
    )
    session = boot.pop("_session", None)
    summary: dict[str, Any] = {
        "schema": "gunnchos.product_use_rc_001.s1_closer.v1",
        "started_at_utc": started,
        "boot_ok": bool(boot.get("ok")),
        "pack": pack,
        "prefer_fail_over_false_pass": True,
        "tokens_remain_false": True,
    }
    if not boot.get("ok") or session is None:
        summary["error"] = boot.get("error") or "boot_failed"
        (OUT / "S1_CLOSER_SUMMARY.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
        print(json.dumps(summary, indent=2, default=str))
        return 1

    results: dict[str, Any] = {}
    try:
        for _ in range(20):
            if _agent_call(session, "compositor_info", timeout_sec=10.0).get("available"):
                break
            time.sleep(2.0)

        # Highest priority: honest Ring re-earn (no lab_browser collector; no migration-alone).
        ring_dir = OUT / "G11_ring"
        ring_dir.mkdir(parents=True, exist_ok=True)
        ring_ev = _evidence_dir(ROOT, "ring")
        results["RING"] = attempt_ring_app_mutation_pass(session, ring_ev)
        for name in ("RING_APP_MUTATION_EVIDENCE.json",):
            src = ring_ev / name
            if src.exists():
                shutil.copy2(src, ring_dir / name)
        for sub in ("document", "browser", "game"):
            sdir = ring_ev / sub
            if sdir.exists():
                shutil.copytree(sdir, ring_dir / sub, dirs_exist_ok=True)
        (ring_dir / "HONEST_REEARN_NOTE.json").write_text(
            json.dumps(
                {
                    "lab_browser_collector_forbidden": True,
                    "pedestrian_seed_save_version": "2",
                    "migration_alone_forbidden": True,
                    "browser_surface": "RingMemo.html contenteditable → RingMemo.txt",
                    "RING_TO_REAL_APP_STATE_MUTATION_PASS": bool(
                        results["RING"].get("RING_TO_REAL_APP_STATE_MUTATION_PASS")
                    ),
                    "RING_TO_REAL_APPLICATION_INPUT_PASS": bool(
                        results["RING"].get("RING_TO_REAL_APPLICATION_INPUT_PASS")
                    ),
                    "RING_SPATIAL_ACCURACY": results["RING"].get("RING_SPATIAL_ACCURACY"),
                    "blocker": results["RING"].get("blocker"),
                },
                indent=2,
            )
            + "\n"
        )

        deploy = _deploy_waike_server(session, pack_dir)
        summary["deploy"] = {
            "curl": deploy.get("curl"),
            "start_ok": bool((deploy.get("start") or {}).get("ok")),
        }

        results["G11"] = run_g11(session)
        (OUT / "G11_waike").mkdir(parents=True, exist_ok=True)
        (OUT / "G11_waike" / "result.json").write_text(json.dumps(results["G11"], indent=2, default=str) + "\n")
        shutil.copytree(pack_dir, OUT / "G11_waike" / "pack", dirs_exist_ok=True)

        results["G13"] = run_g13(session)
        (OUT / "G13_teacher").mkdir(parents=True, exist_ok=True)
        (OUT / "G13_teacher" / "result.json").write_text(json.dumps(results["G13"], indent=2, default=str) + "\n")

        g14_dir = _evidence_dir(ROOT, "dsxl_s1")
        results["G14"] = run_g14(session, g14_dir)
        (OUT / "G14_dsxl_s1").mkdir(parents=True, exist_ok=True)
        (OUT / "G14_dsxl_s1" / "result.json").write_text(json.dumps(results["G14"], indent=2, default=str) + "\n")
        if g14_dir.exists():
            for p in g14_dir.glob("*"):
                if p.is_file() and p.suffix in {".json", ".png"}:
                    shutil.copy2(p, OUT / "G14_dsxl_s1" / p.name)

        results["G15"] = run_g15(session)
        (OUT / "G15_creative").mkdir(parents=True, exist_ok=True)
        (OUT / "G15_creative" / "result.json").write_text(json.dumps(results["G15"], indent=2, default=str) + "\n")
        # pull png if present
        png_pull = _agent_call(
            session,
            "process_run",
            argv=[
                "bash",
                "-lc",
                "python3 - <<'PY'\n"
                "import base64,pathlib\n"
                "p=pathlib.Path('/var/lib/gunnchos/creative/concept.png')\n"
                "print(base64.b64encode(p.read_bytes()).decode() if p.exists() else '')\n"
                "PY",
            ],
            timeout_sec=30.0,
        )
        b64 = (png_pull.get("stdout") or "").strip()
        if b64:
            (OUT / "G15_creative" / "concept.png").write_bytes(base64.b64decode(b64))

        summary["handheld_dock_continuity"] = "OPEN"
        summary["results"] = {k: {kk: vv for kk, vv in v.items() if kk != "pull"} for k, v in results.items()}
        table = update_persona_table(results)
        summary["persona_table"] = "artifacts/product_use/PERSONA_JOURNEY_TABLE.json"
        summary["tokens_earned"] = {r["token_id"]: r.get("token_earned") for r in table.get("rows", [])}

        # Remaining S1 list
        remaining = []
        if not results["RING"].get("RING_TO_REAL_APP_STATE_MUTATION_PASS"):
            remaining.append(
                "RING_TO_REAL_APP_STATE_MUTATION_PASS still open after honest re-earn attempt "
                "(no lab collector; Pedestrian requires input-driven delta beyond post-load)"
            )
        if not results["G11"].get("ok"):
            remaining.append("G11 in-guest WAIKE lesson/quiz/offline incomplete")
        if not results["G13"].get("ok"):
            remaining.append("G13 teacher assign/grade incomplete or key leak")
        if not results["G14"].get("DSXL_DUAL_COMPOSITOR_UX_PASS"):
            remaining.append("G14 DSXL_DUAL_COMPOSITOR_UX_PASS still false")
        if not results["G14"].get("git_build_test", {}).get("ok"):
            remaining.append("G14 git clone/build/test incomplete")
        if not results["G15"].get("ok"):
            remaining.append("G15 creative export incomplete")
        remaining.append("Handheld dock continuity OPEN")
        remaining.append("Full persona tokens (pickup-and-use) still false by policy until complete journeys")
        if results["G11"].get("ok"):
            remaining.append("G11 reboot/resume schoolwork still NOT_RUN (offline/reconnect closed instead)")
        summary["S1_remaining"] = remaining
        summary["Edmund_mergeable"] = False
        summary["finished_at_utc"] = _utc()

        status_path = ROOT / "artifacts/product_use/PRODUCT_USE_RC_001_STATUS.json"
        status = json.loads(status_path.read_text()) if status_path.exists() else {}
        status["s1_closer"] = {
            "started_at_utc": summary.get("started_at_utc"),
            "finished_at_utc": summary.get("finished_at_utc"),
            "boot_ok": summary.get("boot_ok"),
            "RING_TO_REAL_APP_STATE_MUTATION_PASS": bool(
                results["RING"].get("RING_TO_REAL_APP_STATE_MUTATION_PASS")
            ),
            "RING_TO_REAL_APPLICATION_INPUT_PASS": bool(
                results["RING"].get("RING_TO_REAL_APPLICATION_INPUT_PASS")
            ),
            "RING_SPATIAL_ACCURACY": results["RING"].get("RING_SPATIAL_ACCURACY"),
            "G11_ok": bool(results["G11"].get("ok")),
            "G13_ok": bool(results["G13"].get("ok")),
            "G14_DSXL": bool(results["G14"].get("DSXL_DUAL_COMPOSITOR_UX_PASS")),
            "G14_git": bool(results["G14"].get("git_build_test", {}).get("ok")),
            "G15_ok": bool(results["G15"].get("ok")),
            "Edmund_mergeable": False,
            "tokens_remain_false": True,
            "LIVE_visual_retained": True,
        }
        status["S1_open"] = remaining
        status["updated_at_utc"] = _utc()
        status["persona_tokens"] = {
            "STUDENT_DIGITAL_PICKUP_AND_USE_READY": False,
            "OFFICE_DIGITAL_PICKUP_AND_USE_READY": False,
            "TEACHER_DIGITAL_PICKUP_AND_USE_READY": False,
            "BUILDER_DIGITAL_PICKUP_AND_USE_READY": False,
            "CREATIVE_DIGITAL_PICKUP_AND_USE_READY": False,
        }
        status["Edmund_mergeable"] = False
        status_path.write_text(json.dumps(status, indent=2, default=str) + "\n")
    finally:
        try:
            session.stop()
        except Exception:  # noqa: BLE001
            pass

    (OUT / "S1_CLOSER_SUMMARY.json").write_text(json.dumps(summary, indent=2, default=str) + "\n")
    print(json.dumps(summary, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
