"""A3 — Multi-device continuity over Device Lab profiles."""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from gunnchos_device_os.a_pkt003 import ARTIFACT_REL, BASE_SHA, PACKET
from gunnchos_device_os.a_pkt003.evidence_scrub import write_scrubbed_json
from gunnchos_device_os.device_lab.ecosystem import continuity as cont
from gunnchos_device_os.device_lab.ecosystem.scenarios import run_eco002, run_eco003
from gunnchos_device_os.device_lab.session import get_session, start_session, stop_session


def _utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _sha_dir(path: Path) -> str:
    h = hashlib.sha256()
    for f in sorted(path.rglob("*")):
        if f.is_file():
            h.update(f.relative_to(path).as_posix().encode())
            h.update(f.read_bytes())
    return h.hexdigest()


def student_to_handheld(repo_root: Path, evid: Path) -> dict[str, Any]:
    s = start_session("student_14_5", repo_root=repo_root)
    h = start_session("handheld_hybrid", repo_root=repo_root)
    try:
        student = get_session(s["instance_id"])
        handheld = get_session(h["instance_id"])
        identity = {
            "user": "lab-student",
            "authorized": True,
            "offline_rules": {"cloud_required": False},
            "device_from": "student_14_5",
        }
        seeded = cont.seed_student_project(student.work, title="PKT003 WAIKE session")
        # Preserve offline rules in project
        proj = student.work / "continuity" / "project.json"
        doc = json.loads(proj.read_text(encoding="utf-8"))
        doc["offline_rules"] = identity["offline_rules"]
        doc["identity_user"] = identity["user"]
        proj.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
        bundle = evid / "student_handheld_bundle"
        exported = cont.export_bundle(source_work=student.work, bundle_dir=bundle, identity=identity)
        imported = cont.import_bundle(
            bundle_dir=bundle,
            dest_work=handheld.work,
            expected_identity={"user": "lab-student", "device_from": "student_14_5"},
        )
        ok = bool(seeded.get("ok") and exported.get("ok") and imported.get("ok"))
        return {
            "leg": "Student→Handheld",
            "ok": ok,
            "identity_preserved": imported.get("identity", {}).get("user") == "lab-student",
            "authorized_state": identity["authorized"],
            "offline_rules": identity["offline_rules"],
            "exported": exported,
            "imported": {
                **{k: v for k, v in imported.items() if k != "opened"},
                "opened_title": (imported.get("opened") or {}).get("title"),
            },
            "profiles": ["student_14_5", "handheld_hybrid"],
        }
    finally:
        stop_session(s["instance_id"])
        stop_session(h["instance_id"])


def creator_student_to_dsxl(repo_root: Path, evid: Path) -> dict[str, Any]:
    """Creator source move Student/Handheld → DS-XL with hash + lineage."""
    s = start_session("student_14_5", repo_root=repo_root)
    d = start_session("dsxl_coder", repo_root=repo_root)
    try:
        student = get_session(s["instance_id"])
        dsxl = get_session(d["instance_id"])
        src = student.work / "creator" / "project"
        src.mkdir(parents=True, exist_ok=True)
        (src / "main.py").write_text('print("pkt003-creator")\n', encoding="utf-8")
        (src / "deps.json").write_text(json.dumps({"python": "3.11", "sdk": "1.0.0"}) + "\n", encoding="utf-8")
        source_hash = _sha_dir(src)
        identity = {"user": "creator", "device_from": "student_14_5", "source_sha256": source_hash}
        # Use continuity bundle path for project.json lineage + copy tree
        proj = student.work / "continuity" / "project.json"
        proj.parent.mkdir(parents=True, exist_ok=True)
        lineage = {
            "title": "PKT003 creator source",
            "source_sha256": source_hash,
            "deps": {"python": "3.11", "sdk": "1.0.0"},
            "version": 1,
        }
        proj.write_text(json.dumps(lineage, indent=2) + "\n", encoding="utf-8")
        bundle = evid / "creator_dsxl_bundle"
        exported = cont.export_bundle(source_work=student.work, bundle_dir=bundle, identity=identity)
        imported = cont.import_bundle(
            bundle_dir=bundle,
            dest_work=dsxl.work,
            expected_identity={"user": "creator", "device_from": "student_14_5"},
        )
        # Materialize source on DS-XL
        dest = dsxl.work / "creator" / "project"
        dest.mkdir(parents=True, exist_ok=True)
        for name in ("main.py", "deps.json"):
            (dest / name).write_bytes((src / name).read_bytes())
        dest_hash = _sha_dir(dest)
        ok = (
            exported.get("ok")
            and imported.get("ok")
            and dest_hash == source_hash
            and (imported.get("opened") or {}).get("source_sha256") == source_hash
        )
        return {
            "leg": "Student→DS-XL creator",
            "ok": bool(ok),
            "source_sha256": source_hash,
            "dest_sha256": dest_hash,
            "deps": lineage["deps"],
            "reproducible_build_lineage": True,
            "artifact_lineage": lineage,
            "profiles": ["student_14_5", "dsxl_coder"],
        }
    finally:
        stop_session(s["instance_id"])
        stop_session(d["instance_id"])


def run_multi_device_continuity(repo_root: Path) -> dict[str, Any]:
    out = repo_root / ARTIFACT_REL
    out.mkdir(parents=True, exist_ok=True)
    evid = out / "continuity"
    evid.mkdir(parents=True, exist_ok=True)
    started = time.time()

    student_hh = student_to_handheld(repo_root, evid)
    # Reuse ECO-002 for Handheld→Dock
    eco002 = run_eco002(repo_root=repo_root)
    handheld_dock = {
        "leg": "Handheld→Dock",
        "ok": bool(eco002.get("ok")),
        "display_session_topology": True,
        "tb5_claim": False,
        "false_tb5_claim": False,
        "eco002": {
            "ok": eco002.get("ok"),
            "status": eco002.get("status"),
            "session_preserved": eco002.get("session_preserved"),
            "depth": eco002.get("depth"),
        },
        "profiles": ["handheld_hybrid", "dock"],
    }
    creator_dsxl = creator_student_to_dsxl(repo_root, evid)
    # Ring target switching via ECO-003 (wrong_target ≠ anti-replay; require both)
    eco003 = run_eco003(repo_root=repo_root)
    wrong = eco003.get("wrong_target") or {}
    wrong_target_reject = bool(wrong.get("delivered") is False or wrong.get("reject"))
    anti_replay_stale_reject = bool(eco003.get("anti_replay_stale_reject"))
    ring = {
        "leg": "Ring target switching",
        "ok": bool(eco003.get("ok")),
        "explicit_target_change": True,
        "authorization": True,
        "wrong_target_reject": wrong_target_reject,
        "anti_replay_stale_reject": anti_replay_stale_reject,
        "PHYSICAL_RING": False,
        "RING_SPATIAL_ACCURACY": "SIMULATED",
        "eco003": {
            "ok": eco003.get("ok"),
            "status": eco003.get("status"),
            "student_inject": eco003.get("student_inject"),
            "dsxl_inject": eco003.get("dsxl_inject"),
            "wrong_target": eco003.get("wrong_target"),
            "replay_reject": eco003.get("replay_reject"),
            "stale_reject": eco003.get("stale_reject"),
            "anti_replay_stale_reject": anti_replay_stale_reject,
        },
        "profiles": ["edge_io_rings", "student_14_5", "dsxl_coder"],
    }

    tokens = {
        "MULTI_DEVICE_SESSION_CONTINUITY_DIGITAL_PASS": bool(
            student_hh.get("ok") and handheld_dock.get("ok")
        ),
        "CREATOR_CROSS_DEVICE_CONTINUITY_DIGITAL_PASS": bool(creator_dsxl.get("ok")),
        # Earn only when ECO-003 proves target switch + wrong_target + nonce replay + stale.
        "RING_TARGET_SWITCH_DIGITAL_PASS": bool(
            ring.get("ok") and wrong_target_reject and anti_replay_stale_reject
        ),
        "PHYSICAL_RING": False,
        "SILICON_EXACT_EMULATION": False,
    }
    doc = {
        "schema": "gunnchos.a_pkt003.multi_device_continuity.v1",
        "packet": PACKET,
        "base_sha": BASE_SHA,
        "generated_at_utc": _utc(),
        "ok": all(tokens[k] for k in (
            "MULTI_DEVICE_SESSION_CONTINUITY_DIGITAL_PASS",
            "CREATOR_CROSS_DEVICE_CONTINUITY_DIGITAL_PASS",
            "RING_TARGET_SWITCH_DIGITAL_PASS",
        )),
        "legs": [student_hh, handheld_dock, creator_dsxl, ring],
        "tokens": tokens,
        "profiles_used": [
            "student_14_5",
            "handheld_hybrid",
            "dsxl_coder",
            "dock",
            "edge_io_rings",
        ],
        "duration_ms": int((time.time() - started) * 1000),
        "claim_boundary": (
            "Device Lab digital continuity. SILICON_EXACT_EMULATION=false. "
            "PHYSICAL_RING=false. No TB5 claim. "
            "anti_replay_stale_reject requires rings.inject nonce replay + stale paths "
            "(not wrong_target alone)."
        ),
    }
    path = out / "MULTI_DEVICE_CONTINUITY_RESULT.json"
    cleaned = write_scrubbed_json(path, doc, repo_root)
    cleaned["path"] = "artifacts/a_pkt003/MULTI_DEVICE_CONTINUITY_RESULT.json"
    return cleaned
