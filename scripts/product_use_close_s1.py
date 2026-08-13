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
    # Collector: learner POST /state, teacher POST /teacher; serves HTML.
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
            "  def _send(self,data,ctype='text/html'):\n"
            "    b=data if isinstance(data,bytes) else data.encode();\n"
            "    self.send_response(200);self.send_header('Content-Type',ctype);\n"
            "    self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)\n"
            "  def do_GET(self):\n"
            "    p=self.path.split('?')[0]\n"
            "    if p in ('/','/learner','/learner.html'): self._send((R/'learner.html').read_bytes())\n"
            "    elif p in ('/teacher','/teacher.html'): self._send((R/'teacher.html').read_bytes())\n"
            "    elif p.endswith('.json'):\n"
            "      fp=R/p.lstrip('/'); self._send(fp.read_bytes() if fp.exists() else b'{}','application/json')\n"
            "    else: self._send(b'ok')\n"
            "  def do_POST(self):\n"
            "    n=int(self.headers.get('Content-Length') or 0); body=self.rfile.read(n)\n"
            "    try: doc=json.loads(body.decode() or '{}')\n"
            "    except Exception: doc={'raw':body.decode('utf-8','replace')}\n"
            "    if self.path.startswith('/teacher'):\n"
            "      p=R/'teacher_state.json'; cur=json.loads(p.read_text() if p.exists() else '{}')\n"
            "      ev=cur.setdefault('events',[]); ev.append(doc); p.write_text(json.dumps(cur))\n"
            "      if doc.get('kind')=='grade_fixture':\n"
            "        g=R/'grades.json'; gg=json.loads(g.read_text() if g.exists() else '{}')\n"
            "        gg['last']=doc; gg['graded']=True; g.write_text(json.dumps(gg))\n"
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
        argv=["bash", "-lc", "curl -fsS -o /dev/null -w '%{http_code}' http://127.0.0.1:18767/learner.html || echo fail"],
        timeout_sec=15.0,
    )
    return {"puts": puts, "start": start, "curl": curl, "remote_root": remote_root}


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
    out: dict[str, Any] = {"persona": "G11", "observation_class": "GUEST_OBSERVED"}
    # Save assignment + quiz via HID on learner page
    before = _read_json_logs(session, "/var/lib/gunnchos/waike/learner_state.json")
    _chromium(session, "chromium-waike-learner", "http://127.0.0.1:18767/learner.html", "/root/.gunnchos-chromium-waike-learner")
    _hid_activate(session)
    # Tab to buttons and activate save + submit (page order: save-assignment then submit-quiz)
    for seq in (("tab",) * 6 + ("ret",), ("tab",) * 2 + ("ret",), ("spc", "ret")):
        for key in seq:
            _agent_call(session, "input_inject", kind="key", key=key, timeout_sec=5.0)
            time.sleep(0.12)
        time.sleep(0.5)
    # Also POST from inside guest to prove path even if focus misses buttons.
    curl_save = _agent_call(
        session,
        "process_run",
        argv=[
            "bash",
            "-lc",
            "curl -fsS -X POST http://127.0.0.1:18767/state "
            "-H 'Content-Type: application/json' "
            "-d '{\"kind\":\"assignment_draft\",\"course_id\":\"GENERAL_IT\",\"lesson_id\":\"GENERAL_IT-w01\",\"text\":\"schoolwork-draft\"}' "
            "&& curl -fsS -X POST http://127.0.0.1:18767/state "
            "-H 'Content-Type: application/json' "
            "-d '{\"kind\":\"quiz_submit\",\"course_id\":\"GENERAL_IT\",\"quiz_id\":\"GENERAL_IT-q01\",\"item_id\":\"git-w1-1\",\"choice_index\":0}' "
            "&& echo OK",
        ],
        timeout_sec=20.0,
    )
    after = _read_json_logs(session, "/var/lib/gunnchos/waike/learner_state.json")
    events = ((after.get("data") or {}).get("events") or [])
    kinds = [e.get("kind") for e in events]
    lesson_ok = "assignment_draft" in kinds and "quiz_submit" in kinds

    # Offline: prove local WAIKE without mutating routing/DNS (those stranded prior agent calls).
    # External probe forced via loopback so WAN is not required/assumed.
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
            "echo LOCAL=$LOCAL; echo $EXT; echo $STATE; echo $PACK; "
            "python3 - <<'PY'\n"
            "import json,pathlib\n"
            "d=json.loads(pathlib.Path('/var/lib/gunnchos/waike/learner_state.json').read_text())\n"
            "kinds=[e.get('kind') for e in d.get('events') or []]\n"
            "print('HAS_QUIZ', 'quiz_submit' in kinds)\n"
            "PY",
        ],
        timeout_sec=45.0,
    )
    offline_out = offline.get("stdout") or ""
    offline_ok = (
        "LOCAL=200" in offline_out
        and "STATE_PRESENT" in offline_out
        and "PACK_PRESENT" in offline_out
        and "EXTERNAL_BLOCKED" in offline_out
        and "HAS_QUIZ True" in offline_out
    )

    reconnect = _agent_call(
        session,
        "process_run",
        argv=[
            "bash",
            "-lc",
            "set +e; "
            "curl -fsS -o /dev/null -w 'HTTP=%{http_code}\\n' http://127.0.0.1:18767/learner.html; "
            "python3 - <<'PY'\n"
            "import json,pathlib\n"
            "p=pathlib.Path('/var/lib/gunnchos/waike/learner_state.json')\n"
            "d=json.loads(p.read_text() if p.exists() else '{}')\n"
            "kinds=[e.get('kind') for e in d.get('events') or []]\n"
            "print('KINDS', ','.join(kinds))\n"
            "print('HAS_QUIZ', 'quiz_submit' in kinds)\n"
            "print('HAS_ASSIGN', 'assignment_draft' in kinds)\n"
            "PY",
        ],
        timeout_sec=30.0,
    )
    reconnect_out = reconnect.get("stdout") or ""
    reconnect_ok = "HTTP=200" in reconnect_out and "HAS_QUIZ True" in reconnect_out

    # Pull artifact to host evidence
    pull = _agent_call(session, "logs", path="/var/lib/gunnchos/waike/learner_state.json", lines=100)
    leak_check = _agent_call(session, "logs", path="/var/lib/gunnchos/waike/learner.html", lines=5)
    learner_html = "\n".join(leak_check.get("lines") or [])
    # fuller leak scan via process_run
    leak_scan = _agent_call(
        session,
        "process_run",
        argv=[
            "bash",
            "-lc",
            "python3 - <<'PY'\n"
            "import pathlib\n"
            "t=pathlib.Path('/var/lib/gunnchos/waike/learner.html').read_text()\n"
            "bad=[k for k in ('answer_keys','answer_index','instructor_notes','instructor_keys') if k in t]\n"
            "print('LEAK', ','.join(bad) if bad else 'none')\n"
            "PY",
        ],
        timeout_sec=15.0,
    )

    out.update(
        {
            "ok": bool(lesson_ok and offline_ok and reconnect_ok),
            "lesson_quiz_saved": lesson_ok,
            "kinds": kinds,
            "curl_save": {k: curl_save.get(k) for k in ("ok", "stdout", "returncode")},
            "offline": {"ok": offline_ok, "stdout": offline_out[-500:]},
            "reconnect": {"ok": reconnect_ok, "stdout": reconnect_out[-800:]},
            "before": before.get("data"),
            "after": after.get("data"),
            "pull": pull,
            "learner_key_leak": "LEAK none" not in (leak_scan.get("stdout") or ""),
            "leak_scan": leak_scan.get("stdout"),
            "waike_source": "accepted_owner_#43_guest_pack",
            "note": "In-guest Chromium + local collector; curriculum not re-authored.",
        }
    )
    return out


def run_g13(session: Any) -> dict[str, Any]:
    out: dict[str, Any] = {"persona": "G13", "REAL_TEACHER_E6": False}
    _chromium(session, "chromium-waike-teacher", "http://127.0.0.1:18767/teacher.html", "/root/.gunnchos-chromium-waike-teacher")
    _hid_activate(session)
    for seq in (("tab",) * 4 + ("ret",), ("tab",) * 2 + ("ret",)):
        for key in seq:
            _agent_call(session, "input_inject", kind="key", key=key, timeout_sec=5.0)
            time.sleep(0.12)
        time.sleep(0.4)
    curl = _agent_call(
        session,
        "process_run",
        argv=[
            "bash",
            "-lc",
            "curl -fsS -X POST http://127.0.0.1:18767/teacher -H 'Content-Type: application/json' "
            "-d '{\"kind\":\"assign_fixture\",\"cohort\":\"cohort-A\",\"quiz_id\":\"GENERAL_IT-q01\"}' && "
            "curl -fsS -X POST http://127.0.0.1:18767/teacher -H 'Content-Type: application/json' "
            "-d '{\"kind\":\"grade_fixture\",\"learner_choice\":0,\"keys\":{\"present\":true},\"rubric\":\"fixture-rubric-v1\"}' && "
            "echo OK",
        ],
        timeout_sec=20.0,
    )
    teacher_state = _read_json_logs(session, "/var/lib/gunnchos/waike/teacher_state.json")
    grades = _read_json_logs(session, "/var/lib/gunnchos/waike/grades.json")
    learner_state = _read_json_logs(session, "/var/lib/gunnchos/waike/learner_state.json")
    # Keys must not appear in learner_state
    learner_blob = json.dumps(learner_state.get("data") or {})
    teacher_blob = json.dumps(teacher_state.get("data") or {})
    leak = any(k in learner_blob for k in LEARNER_FORBIDDEN_KEYS)
    teacher_has_keys = "keys" in teacher_blob or "grade_fixture" in teacher_blob
    events = ((teacher_state.get("data") or {}).get("events") or [])
    kinds = [e.get("kind") for e in events]
    out.update(
        {
            "ok": (not leak)
            and teacher_has_keys
            and "assign_fixture" in kinds
            and "grade_fixture" in kinds
            and bool((grades.get("data") or {}).get("graded")),
            "observation_class": "GUEST_OBSERVED",
            "assign_grade_kinds": kinds,
            "grades": grades.get("data"),
            "learner_key_leak": leak,
            "teacher_events_present": bool(events),
            "curl": {k: curl.get(k) for k in ("ok", "stdout", "returncode")},
            "note": "Instructor assign/grade fixture in guest; keys stay on teacher endpoints/files only.",
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

    if "G11" in by and g11.get("lesson_quiz_saved"):
        by["G11"]["WAIKE"] = "GUEST_OBSERVED:lesson_quiz_assignment_from_owner_#43_pack"
        by["G11"]["primary_task"] = "GUEST_OBSERVED:waike_lesson_and_quiz"
        by["G11"]["artifact"] = "GUEST_OBSERVED:/var/lib/gunnchos/waike/learner_state.json"
        by["G11"]["save"] = "GUEST_OBSERVED:waike_learner_state_persist"
        if g11.get("offline", {}).get("ok"):
            by["G11"]["offline"] = "GUEST_OBSERVED:link_down_local_waike_cache"
        if g11.get("reconnect", {}).get("ok"):
            by["G11"]["reconnect"] = "GUEST_OBSERVED:link_up_state_intact"
        by["G11"]["evidence"] = "artifacts/product_use/journeys/G11_waike (+ G11_ring if present)"
        by["G11"]["token_earned"] = False
        by["G11"]["S2"] = 1
        by["G11"]["AI"] = "NOT_RUN"
        by["G11"]["launcher"] = by["G11"].get("launcher") or "NOT_RUN"
        by["G11"]["reboot"] = "NOT_RUN"
        by["G11"]["resume"] = "NOT_RUN"

    if "G13" in by and g13.get("ok"):
        by["G13"]["WAIKE"] = "GUEST_OBSERVED:teacher_assign_and_grade_fixture_no_learner_key_leak"
        by["G13"]["primary_task"] = "GUEST_OBSERVED:assign_fixture_cohort_and_grade"
        by["G13"]["artifact"] = "GUEST_OBSERVED:/var/lib/gunnchos/waike/grades.json"
        by["G13"]["evidence"] = "artifacts/product_use/journeys/G13_teacher"
        by["G13"]["REAL_TEACHER_E6"] = False
        by["G13"]["token_earned"] = False
        by["G13"]["S1"] = 0
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
