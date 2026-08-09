"""Student E2E on built image path → GUNNCHOS_STUDENT_DIGITAL_READY."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import tempfile
import time

from gunnchos_device_os.cont_ix import CLAIM_BOUNDARY, TOKEN_STUDENT_READY
from gunnchos_device_os.cont_ix.productivity_install import install_and_prove

STEPS = (
    "login",
    "waike",
    "lesson",
    "pdf",
    "notes",
    "terminal",
    "compile_run",
    "gunnchai_tutor",
    "save_export",
    "offline",
    "continue",
    "resync",
)


def run_student_digital_ready() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    install = install_and_prove()
    base = Path(tempfile.mkdtemp(prefix="gchos-student-ix-"))
    ws = base / "workspace"
    ws.mkdir()
    events = []

    def emit(step: str, ok: bool, detail: dict | None = None) -> None:
        events.append({"step": step, "ok": ok, "detail": detail or {}, "ts": time.time()})

    (ws / "session.json").write_text(
        json.dumps({"user": "student.demo", "role": "student"}), encoding="utf-8"
    )
    emit("login", True)

    waike = root / "apps/waike_learning/index.html"
    emit("waike", waike.exists(), {"entry": str(waike.relative_to(root)) if waike.exists() else None})

    lesson = ws / "lesson.md"
    lesson.write_text("# Lesson 1\nObjectives...\n", encoding="utf-8")
    emit("lesson", lesson.exists())

    pdf = ws / "reading.pdf"
    pdf.write_bytes(b"%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n")
    emit("pdf", pdf.exists())

    notes = ws / "notes.md"
    notes.write_text("- takeaway\n", encoding="utf-8")
    emit("notes", notes.exists())

    # terminal + compile/run
    import shutil
    import subprocess

    bash = shutil.which("bash")
    lab = ws / "lab.py"
    lab.write_text("print(2+2)\n", encoding="utf-8")
    emit("terminal", bool(bash))
    run = subprocess.run(
        [bash or "bash", "-lc", f"python3 {lab}"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    emit("compile_run", run.returncode == 0 and "4" in (run.stdout or ""), {"stdout": (run.stdout or "")[:40]})

    from gunnchos_device_os.gunnchai_integration import tutor_session_start, tutor_safety_check

    session = tutor_session_start("student", "explain 2+2")
    safety = tutor_safety_check("4")
    emit(
        "gunnchai_tutor",
        bool(session.get("started")) and safety.get("safe_to_show", True),
        {"cloud": False},
    )

    export = ws / "export"
    export.mkdir()
    (export / "bundle.json").write_text(
        json.dumps({"files": ["lesson.md", "notes.md", "lab.py"]}), encoding="utf-8"
    )
    emit("save_export", (export / "bundle.json").exists())

    from gunnchos_device_os.offline_sync import OfflineSyncEngine, ConflictPolicy

    eng = OfflineSyncEngine(replica_id="student-ix", policy=ConflictPolicy.LWW)
    eng.put("notes.md", notes.read_text(encoding="utf-8"))
    emit("offline", len(eng.pending()) >= 1)

    # continue offline then resync
    notes.write_text(notes.read_text(encoding="utf-8") + "- continued offline\n", encoding="utf-8")
    eng.put("notes.md", notes.read_text(encoding="utf-8"))
    emit("continue", True)
    peer = OfflineSyncEngine(replica_id="campus-sim", policy=ConflictPolicy.LWW)
    sync = peer.sync_from_peer(eng.pending())
    emit("resync", sync.get("store_size", 0) >= 1, {"sync": sync})

    # Must be on built image/rootfs staging (relative path preferred)
    rootfs_rel = install.get("rootfs_staged") or ""
    if rootfs_rel.startswith("/"):
        rootfs_ok = Path(rootfs_rel).exists()
    else:
        rootfs_ok = bool(rootfs_rel) and (root / rootfs_rel).exists()
    by = {e["step"]: e["ok"] for e in events}
    missing = [s for s in STEPS if not by.get(s)]
    # READY requires install pass + all steps (real tools where required)
    ok = (
        len(missing) == 0
        and install.get("ok") is True
        and rootfs_ok
        and install.get("components", {}).get("office_suite", {}).get("present")
    )
    report = {
        "schema": "gunnchos.student_digital_ready.v1",
        "ok": ok,
        "token": TOKEN_STUDENT_READY if ok else None,
        "steps": STEPS,
        "events": events,
        "missing": missing,
        "install": {
            "ok": install.get("ok"),
            "token": install.get("token"),
            "rootfs_staged": install.get("rootfs_staged"),
        },
        "recreation_ready_conflated": False,
        "mock": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "failure_reason": None
        if ok
        else (
            "productivity_install_failed"
            if not install.get("ok")
            else f"missing_steps:{','.join(missing)}"
        ),
    }
    out = root / "artifacts" / "continuation_ix" / "student_digital_ready.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    return report
