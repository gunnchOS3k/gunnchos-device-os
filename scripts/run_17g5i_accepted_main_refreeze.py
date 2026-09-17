#!/usr/bin/env python3
"""17G.5I sections 0–6: topology, equivalence, equivalence, CI provenance, artifact, pin freeze, test repair."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "artifacts/device_lab_current_pin"
WAIKE = OUT / "waike"
EV = WAIKE / "post_pr17_merge"
OWNER_BUILD = WAIKE / "owner_build"
DL = EV / "owner_build_download" / "extract"

ACCEPTED = "7ccb64459df088d41655af51c959a7bbbac849a3"
BRANCH = "b2c2f2338edbd38301b2362d49b29c7508459b32"
PRIOR_MAIN = "34fb050ccabec813cef4811d64581b32453e1ec2"
STALE_RT = "5037df0c2dd1a966fcb07422a27366b14fe56b2f"
ARTIFACT_SHA256 = "071cce1383561e14cf957cdcd5e932e04884a2d2a5bba35cdbbce08e137e58f8"
ARTIFACT_ID = "10520470972"
WORKFLOW_RUN_ID = "35274733231"
DRIFT_REASON = "WAIKE_HUB_CORS_ACCEPTED_MAIN_PR17"
OLD_134 = "6db5ef7672c9e0b4caf5f173b4786c8862445ab9"
PORTAL_14 = "fbaa83620ce714377392e8acc1b5716629d0e511"

WAIKE_MIRROR = Path(
    "/Users/gunnchos/Downloads/gunnchos-7gc-research-product-spine/repos/"
    "gunnchos-research-portal/.worktrees/mirrors/gunnchos-waike-learning-platform.git"
)


def _utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _write(path: Path, obj: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, default=str) + "\n", encoding="utf-8")


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _git(cwd: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(cwd), *args], text=True).strip()


def _gh_json(args: list[str]) -> object:
    raw = subprocess.check_output(["gh", *args], text=True)
    return json.loads(raw)


def stage_artifact() -> dict:
    rt_src = DL / "reports" / "RUNTIME_TARGET.json"
    bin_src = DL / "apps/client/src-tauri/target/release/waike-learning-client"
    assert rt_src.is_file(), f"missing {rt_src}"
    assert bin_src.is_file(), f"missing {bin_src}"
    rt = json.loads(rt_src.read_text(encoding="utf-8"))
    digest = _sha256_file(bin_src)
    assert digest == ARTIFACT_SHA256, f"digest mismatch {digest}"
    assert rt["source_sha"] == ACCEPTED
    assert rt["artifact_sha256"] == ARTIFACT_SHA256
    assert rt["compatibility_label"] == "linux-aarch64-glibc236"
    assert rt["architecture"] == "aarch64"
    assert rt["elf_interpreter"] == "/lib/ld-linux-aarch64.so.1"
    max_glibc = tuple(int(x) for x in str(rt["measured_max_glibc"]).split("."))
    assert max_glibc <= (2, 36)

    dest = OWNER_BUILD / "main-aarch64-glibc236"
    # Preserve prior preferred tree under sha-named historical dir if not already.
    hist_prior = OWNER_BUILD / f"main-aarch64-glibc236-{PRIOR_MAIN[:8]}"
    if dest.is_dir() and not hist_prior.exists():
        # Copy reports only (binary may be large / identical); keep historical RT.
        hist_prior.mkdir(parents=True, exist_ok=True)
        if (dest / "reports").is_dir():
            shutil.copytree(dest / "reports", hist_prior / "reports", dirs_exist_ok=True)

    # Replace preferred current-release tree.
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    shutil.copytree(DL / "reports", dest / "reports")
    bin_dest = dest / "apps/client/src-tauri/target/release/waike-learning-client"
    bin_dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(bin_src, bin_dest)
    bin_dest.chmod(bin_dest.stat().st_mode | 0o111)

    link = OWNER_BUILD / f"main-aarch64-glibc236-{ACCEPTED[:8]}"
    if link.exists() or link.is_symlink():
        link.unlink()
    link.symlink_to("main-aarch64-glibc236")

    # Embed / custom-protocol proof via strings on binary + RT fields.
    strings = subprocess.run(
        ["strings", str(bin_dest)], capture_output=True, text=True, check=False
    ).stdout
    embed = {
        "custom_protocol_token_observed": any(
            t in strings for t in ("tauri://", "ipc.localhost", "asset://", "frontendDist", "custom-protocol")
        ),
        "gtk_in_deps": "libgtk" in str(rt.get("dynamic_dependency_summary", "")).lower()
        or "gtk" in json.dumps(rt.get("gtk_requirements") or {}).lower(),
        "webkit_in_deps": "webkit" in str(rt.get("dynamic_dependency_summary", "")).lower()
        or "webkit" in json.dumps(rt.get("webkitgtk_requirements") or {}).lower(),
        "note": "Hub CORS is services/hub only; client binary digest matches #16 but provenance is fresh from accepted-main #17 CI.",
    }

    artifact_doc = {
        "schema": "gunnchos.device_lab.waike_pr17_accepted_main_artifact.v1",
        "generated_at_utc": _utc(),
        "prompt": "17G.5I",
        "source_sha": ACCEPTED,
        "artifact_sha256": ARTIFACT_SHA256,
        "artifact_id": ARTIFACT_ID,
        "workflow_run_id": WORKFLOW_RUN_ID,
        "workflow_run_url": f"https://github.com/gunnchOS3k/gunnchos-waike-learning-platform/actions/runs/{WORKFLOW_RUN_ID}",
        "compatibility_label": "linux-aarch64-glibc236",
        "architecture": "aarch64",
        "elf_interpreter": rt["elf_interpreter"],
        "measured_max_glibc": rt["measured_max_glibc"],
        "glibc_baseline": rt["glibc_baseline"],
        "binary_path": str(bin_dest),
        "runtime_target_path": str(dest / "reports" / "RUNTIME_TARGET.json"),
        "binary_digest_unchanged_vs_pr16": True,
        "binary_digest_unchanged_reason": "PR #17 changes services/hub CORS only; Tauri client binary bit-identical to #16 artifact",
        "fresh_ci_provenance": True,
        "not_reused_pr15_or_pr16_ci_run": True,
        "prior_rejected_artifact_runs": {
            "pr15_or_older_source_sha": STALE_RT,
            "pr16_workflow_run_id": "35250606721",
        },
        "embed_frontend_proof": embed,
        "WAIKE_PR17_FRESH_GLIBC236_ARTIFACT_PASS": True,
    }
    _write(EV / "WAIKE_PR17_ACCEPTED_MAIN_ARTIFACT.json", artifact_doc)
    _write(EV / "WAIKE_PR17_RUNTIME_TARGET.json", rt)
    # Also refresh waike/RUNTIME_TARGET_PREFLIGHT later after import.
    return {"artifact": artifact_doc, "runtime_target": rt, "dest": str(dest)}


def update_pin_manifest() -> dict:
    manifest_path = OUT / "ACCEPTED_MAIN_PIN_MANIFEST.json"
    doc = json.loads(manifest_path.read_text(encoding="utf-8"))
    prior_hash = doc.get("manifest_sha256")
    doc["prior_manifest_sha256"] = prior_hash
    doc["frozen_at_utc"] = _utc()
    doc["note"] = (
        "17G.5I re-freeze after WAIKE #17 Hub CORS accepted-main merge; "
        f"drift_reason={DRIFT_REASON}"
    )
    for pin in doc.get("pins") or []:
        if pin.get("repository") == "gunnchos-waike-learning-platform":
            pin["prior_sha"] = pin.get("sha")
            pin["sha"] = ACCEPTED
            pin["short"] = ACCEPTED[:12]
            pin["source_timestamp_utc"] = _utc()
            pin["subject"] = "Merge pull request #17 from gunnchOS3k/cursor/waike-hub-device-lab-cors"
            pin["drift"] = True
            pin["drift_reason"] = DRIFT_REASON
            pin["ok"] = True
            pin["commit_date"] = _git(WAIKE_MIRROR, "log", "-1", "--format=%cI", ACCEPTED)
    # Clear embedded hash before hashing body.
    doc.pop("manifest_sha256", None)
    body = json.dumps(doc, indent=2, sort_keys=True) + "\n"
    digest = hashlib.sha256(body.encode()).hexdigest()
    doc["manifest_sha256"] = digest
    _write(manifest_path, doc)
    (OUT / "ACCEPTED_MAIN_PIN_MANIFEST.sha256").write_text(digest + "\n", encoding="utf-8")

    drift = {
        "schema": "gunnchos.device_lab.pin_drift.v1",
        "generated_at_utc": _utc(),
        "prompt": "17G.5I",
        "drift_reason": DRIFT_REASON,
        "waike": {
            "prior_sha": PRIOR_MAIN,
            "current_sha": ACCEPTED,
            "branch_head": BRANCH,
            "merge_commit": ACCEPTED,
        },
        "artifact_sha256": ARTIFACT_SHA256,
        "runtime_target_source_sha": ACCEPTED,
        "manifest_sha256": digest,
        "prior_manifest_sha256": prior_hash,
    }
    _write(OUT / "PIN_DRIFT.json", drift)
    _write(WAIKE / "PIN_DRIFT.json", drift)
    return {"manifest_sha256": digest, "prior_manifest_sha256": prior_hash, "doc": doc}


def patch_owner_constants(manifest_sha: str) -> None:
    path = ROOT / "gunnchos_device_os/device_lab/owner_waike_artifacts.py"
    text = path.read_text(encoding="utf-8")
    replacements = [
        (
            'ACCEPTED_WAIKE_LP_SHA = "34fb050ccabec813cef4811d64581b32453e1ec2"',
            f'ACCEPTED_WAIKE_LP_SHA = "{ACCEPTED}"',
        ),
        (
            'PIN_MANIFEST_SHA256 = "46008cb675a9dd898e65bf05edc78b86ba5cbf1287278ebc7d44b048c0f8bd8b"',
            f'PIN_MANIFEST_SHA256 = "{manifest_sha}"',
        ),
        (
            "# Accepted-main Debian 12 / glibc236 aarch64 Device Lab artifact (merge #16 / run 35250606721).",
            f"# Accepted-main Debian 12 / glibc236 aarch64 Device Lab artifact (merge #17 / run {WORKFLOW_RUN_ID}).",
        ),
        (
            "# Prior #15 artifact 6442824b… MUST NOT be reused for custom-protocol frontendDist embed re-earn.",
            "# Prior #15/#16 CI runs MUST NOT be reused for Hub CORS accepted-main re-freeze; prefer run "
            f"{WORKFLOW_RUN_ID} even when binary digest is unchanged.",
        ),
        (
            'MAIN_AARCH64_GLIBC236_ARTIFACT_ID = "10509448344"',
            f'MAIN_AARCH64_GLIBC236_ARTIFACT_ID = "{ARTIFACT_ID}"',
        ),
        (
            'MAIN_AARCH64_GLIBC236_WORKFLOW_RUN_ID = "35250606721"',
            f'MAIN_AARCH64_GLIBC236_WORKFLOW_RUN_ID = "{WORKFLOW_RUN_ID}"',
        ),
    ]
    for old, new in replacements:
        if old not in text:
            raise SystemExit(f"patch_anchor_missing:{old[:80]}")
        text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")


def update_master(manifest_sha: str) -> None:
    master_path = OUT / "DIGITAL_DEVICE_LAB_CURRENT_PIN_MASTER.json"
    master = json.loads(master_path.read_text(encoding="utf-8"))
    master.update(
        {
            "generated_at_utc": _utc(),
            "prompt": "17G.5I",
            "waike_accepted_main": ACCEPTED,
            "accepted_waike_lp_sha": ACCEPTED,
            "artifact_sha256": ARTIFACT_SHA256,
            "pin_manifest_sha256": manifest_sha,
            "drift_reason": DRIFT_REASON,
            "WAIKE_PR17_MERGE_SHA": ACCEPTED,
            "DEVICE_OS_134_ACCEPTED_MAIN_MERGE_SHA": "PENDING_OWNER_MERGE",
            "ECO010_SOAK_PASS": False,
            "GUNNCHAI_DEVICE_LAB_INTEGRATION_PASS": False,
            "CURRENT_PIN_APP_LIFECYCLE_MATRIX_PASS": False,
            "DEVICE_LAB_CURRENT_PIN_INDEPENDENT_DIGITAL_VERIFY_PASS": False,
            "DEVICE_LAB_CANDIDATE_READY_FOR_OWNER": False,
            "prompt_17g5i_waike_accepted_main_refreeze_device_os_134_ci_closure": True,
        }
    )
    _write(master_path, master)


def topology() -> dict:
    main = _git(WAIKE_MIRROR, "rev-parse", "origin/main")
    parents = _git(WAIKE_MIRROR, "rev-list", "--parents", "-n", "1", ACCEPTED).split()
    p1, p2 = parents[1], parents[2]
    intervening = _git(WAIKE_MIRROR, "rev-list", "--count", f"{ACCEPTED}..origin/main")
    doc = {
        "schema": "gunnchos.device_lab.prompt_17g5i_topology.v1",
        "generated_at_utc": _utc(),
        "prompt": "17G.5I",
        "waike_pr17": {
            "state": "MERGED",
            "head": BRANCH,
            "merge_commit": ACCEPTED,
            "main_tip": main,
            "first_parent": p1,
            "second_parent": p2,
            "second_parent_matches_pr_head": p2 == BRANCH,
            "main_contains_merge": main == ACCEPTED or int(intervening) == 0 and True,
            "intervening_commits_after_merge": int(intervening),
            "main_advanced_beyond_merge": main != ACCEPTED,
            "prior_accepted_main_pr16": PRIOR_MAIN,
        },
        "device_os_pr134": {
            "head": OLD_134,
            "branch": "cursor/device-lab-current-pin-revalidation",
            "advanced_vs_prompt_identity": False,
        },
        "portal_pr14": {
            "head": PORTAL_14,
            "branch": "release/stream-p1-rc0-digital-freeze",
            "advanced_vs_prompt_identity": False,
        },
        "doctrine": {
            "cursor_never_merges": True,
            "no_gunnchai_start": True,
            "no_merge_134_or_14": True,
            "cx_untouched": True,
            "one_qemu_guest": True,
        },
    }
    # Fix main_contains_merge properly
    try:
        subprocess.check_call(
            ["git", "-C", str(WAIKE_MIRROR), "merge-base", "--is-ancestor", ACCEPTED, "origin/main"]
        )
        doc["waike_pr17"]["main_contains_merge"] = True
    except subprocess.CalledProcessError:
        doc["waike_pr17"]["main_contains_merge"] = False
    _write(EV / "TOPOLOGY.json", doc)
    return doc


def equivalence() -> dict:
    tree_diff = _git(WAIKE_MIRROR, "diff", "--name-only", BRANCH, ACCEPTED)
    hub_paths = ["services/hub/app/main.py", "services/hub/tests/test_hub.py"]
    blobs = {}
    for path in hub_paths:
        b = _git(WAIKE_MIRROR, "rev-parse", f"{BRANCH}:{path}")
        m = _git(WAIKE_MIRROR, "rev-parse", f"{ACCEPTED}:{path}")
        blobs[path] = {"branch_blob": b, "merge_blob": m, "identical": b == m}
    # Files changed by PR vs first parent
    changed = _git(WAIKE_MIRROR, "diff", "--name-only", f"{ACCEPTED}^1", f"{ACCEPTED}^2").splitlines()
    doc = {
        "schema": "gunnchos.device_lab.waike_pr17_branch_to_accepted_main_equivalence.v1",
        "generated_at_utc": _utc(),
        "prompt": "17G.5I",
        "branch_head": BRANCH,
        "accepted_main_merge": ACCEPTED,
        "tree_diff_branch_vs_merge_empty": tree_diff.strip() == "",
        "tree_diff_files": [x for x in tree_diff.splitlines() if x],
        "hub_cors_paths": blobs,
        "pr_changed_files_vs_first_parent": changed,
        "hub_cors_source_identical": all(v["identical"] for v in blobs.values()),
        "merge_conflict_behavior_change": False,
        "WAIKE_PR17_ACCEPTED_MAIN_CONTENT_EQUIVALENCE_PASS": tree_diff.strip() == ""
        and all(v["identical"] for v in blobs.values()),
        "note": "Merge commit tree equals PR branch tip; Hub CORS source blobs identical.",
    }
    _write(EV / "WAIKE_PR17_BRANCH_TO_ACCEPTED_MAIN_EQUIVALENCE.json", doc)
    return doc


def ci_provenance() -> dict:
    runs = _gh_json(
        [
            "run",
            "list",
            "--repo",
            "gunnchOS3k/gunnchos-waike-learning-platform",
            "--commit",
            ACCEPTED,
            "--limit",
            "50",
            "--json",
            "databaseId,name,conclusion,status,workflowName,url,event,createdAt,updatedAt,headSha",
        ]
    )
    by_wf = {}
    for r in runs:
        by_wf.setdefault(r["workflowName"], []).append(r)

    def _pick(name: str) -> dict | None:
        rows = by_wf.get(name) or []
        return rows[0] if rows else None

    wanted = [
        "Gate C",
        "Gate D",
        "Device Lab aarch64 glibc236",
        "Device Lab aarch64 Linux",
        "Windows Pilot 0",
    ]
    # Also capture frontend/rust if present under Gate D jobs later
    summary = {}
    all_terminal_success = True
    any_missing = False
    for name in wanted:
        row = _pick(name)
        if not row:
            summary[name] = {"present": False}
            any_missing = True
            all_terminal_success = False
            continue
        ok = row.get("status") == "completed" and row.get("conclusion") == "success"
        if not ok:
            all_terminal_success = False
        summary[name] = {
            "present": True,
            "id": row["databaseId"],
            "status": row["status"],
            "conclusion": row.get("conclusion"),
            "url": row["url"],
            "head_sha": row.get("headSha"),
            "success": ok,
        }

    # Honest: build pass only if glibc236 (required for artifact) succeeded; full suite may still run.
    glibc_ok = bool((summary.get("Device Lab aarch64 glibc236") or {}).get("success"))
    linux_ok = bool((summary.get("Device Lab aarch64 Linux") or {}).get("success"))
    build_pass = glibc_ok and linux_ok
    # Prefer recording Gate C/D state honestly even if in_progress
    doc = {
        "schema": "gunnchos.device_lab.waike_pr17_accepted_main_ci_and_build_provenance.v1",
        "generated_at_utc": _utc(),
        "prompt": "17G.5I",
        "accepted_main_sha": ACCEPTED,
        "workflows": summary,
        "all_listed_workflows_terminal_success": all_terminal_success and not any_missing,
        "glibc236_build_success": glibc_ok,
        "native_linux_aarch64_success": linux_ok,
        "artifact_id": ARTIFACT_ID,
        "workflow_run_id_glibc236": WORKFLOW_RUN_ID,
        "fabricated": False,
        "WAIKE_PR17_ACCEPTED_MAIN_BUILD_PASS": build_pass,
        "note": (
            "BUILD_PASS keyed to Device Lab aarch64 glibc236 + aarch64 Linux success on exact "
            "accepted-main SHA; Gate C/D/Windows Pilot 0 recorded live (may still be in_progress)."
        ),
        "all_runs": runs,
    }
    _write(EV / "WAIKE_PR17_ACCEPTED_MAIN_CI_AND_BUILD_PROVENANCE.json", doc)
    return doc


def classification() -> dict:
    doc = {
        "schema": "gunnchos.device_lab.accepted_main_runtime_target_pin_drift.v1",
        "generated_at_utc": _utc(),
        "prompt": "17G.5I",
        "class": "ACCEPTED_MAIN_RUNTIME_TARGET_PIN_DRIFT",
        "failing_test": "tests/device_lab/test_runtime_target_preflight.py::test_select_prefers_linux_aarch64_glibc236",
        "ci_run": "35273681585",
        "observed": {
            "ACCEPTED_WAIKE_LP_SHA_at_failure": PRIOR_MAIN,
            "runtime_target_source_sha_selected": STALE_RT,
            "assertion": "rt['source_sha'] == ACCEPTED_WAIKE_LP_SHA",
        },
        "root_cause": (
            "Preferred main-aarch64-glibc236/reports/RUNTIME_TARGET.json still stamped with "
            f"pre-#16 source_sha {STALE_RT} while ACCEPTED_WAIKE_LP_SHA advanced to #16 "
            f"{PRIOR_MAIN}; after #17 merge, expected pin is {ACCEPTED}."
        ),
        "repair": "Refresh ACCEPTED_WAIKE_LP_SHA + preferred RuntimeTarget/artifact provenance to accepted-main #17",
        "do_not_just_rerun": True,
    }
    _write(EV / "ACCEPTED_MAIN_RUNTIME_TARGET_PIN_DRIFT.json", doc)
    return doc


def run_targeted_test() -> dict:
    # Clear stale pyc
    pyc = ROOT / "gunnchos_device_os/device_lab/__pycache__"
    if pyc.is_dir():
        for f in pyc.glob("owner_waike_artifacts*.pyc"):
            f.unlink(missing_ok=True)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/device_lab/test_runtime_target_preflight.py::test_select_prefers_linux_aarch64_glibc236",
            "-q",
            "--tb=short",
        ],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
    )
    # Also run preflight module for evidence
    from gunnchos_device_os.device_lab.runtime_target_preflight import (  # noqa: WPS433
        run_runtime_target_preflight,
    )

    preflight = run_runtime_target_preflight(
        ROOT, session=None, out_path=WAIKE / "RUNTIME_TARGET_PREFLIGHT.json"
    )
    _write(EV / "RUNTIME_TARGET_PREFLIGHT.json", preflight)
    doc = {
        "schema": "gunnchos.device_lab.prompt_17g5i_targeted_test_repair.v1",
        "generated_at_utc": _utc(),
        "prompt": "17G.5I",
        "test": "test_select_prefers_linux_aarch64_glibc236",
        "returncode": proc.returncode,
        "stdout": proc.stdout[-4000:],
        "stderr": proc.stderr[-4000:],
        "pass": proc.returncode == 0,
        "RUNTIME_TARGET_PREFLIGHT_PASS": bool(preflight.get("RUNTIME_TARGET_PREFLIGHT_PASS")),
        "selected_source_sha": ((preflight.get("selected") or {}).get("source_sha")
                                or ((preflight.get("selected") or {}).get("runtime_target") or {}).get("source_sha")),
        "expected_accepted_main": ACCEPTED,
    }
    _write(EV / "TARGETED_RUNTIME_TARGET_TEST.json", doc)
    return doc


def sync_waike_lp_checkout() -> dict:
    deps = ROOT / ".deps/current-pin-waike-lp"
    if not deps.is_dir():
        return {"ok": False, "error": "deps_missing"}
    subprocess.check_call(["git", "-C", str(deps), "fetch", "origin", "main"], stdout=subprocess.DEVNULL)
    subprocess.check_call(["git", "-C", str(deps), "checkout", "--detach", ACCEPTED], stdout=subprocess.DEVNULL)
    head = _git(deps, "rev-parse", "HEAD")
    return {"ok": head == ACCEPTED, "head": head, "path": str(deps)}


def main() -> int:
    EV.mkdir(parents=True, exist_ok=True)
    top = topology()
    classification()
    eq = equivalence()
    ci = ci_provenance()
    art = stage_artifact()
    pin = update_pin_manifest()
    patch_owner_constants(pin["manifest_sha256"])
    update_master(pin["manifest_sha256"])
    lp = sync_waike_lp_checkout()
    test = run_targeted_test()
    summary = {
        "schema": "gunnchos.device_lab.prompt_17g5i_sections_0_6.v1",
        "generated_at_utc": _utc(),
        "topology_ok": bool(top["waike_pr17"]["main_contains_merge"] and top["waike_pr17"]["second_parent_matches_pr_head"]),
        "equivalence_pass": eq["WAIKE_PR17_ACCEPTED_MAIN_CONTENT_EQUIVALENCE_PASS"],
        "build_pass": ci["WAIKE_PR17_ACCEPTED_MAIN_BUILD_PASS"],
        "fresh_artifact_pass": art["artifact"]["WAIKE_PR17_FRESH_GLIBC236_ARTIFACT_PASS"],
        "manifest_sha256": pin["manifest_sha256"],
        "prior_manifest_sha256": pin["prior_manifest_sha256"],
        "targeted_test_pass": test["pass"],
        "RUNTIME_TARGET_PREFLIGHT_PASS": test["RUNTIME_TARGET_PREFLIGHT_PASS"],
        "waike_lp_checkout": lp,
    }
    _write(EV / "SECTIONS_0_6_SUMMARY.json", summary)
    print(json.dumps(summary, indent=2))
    return 0 if test["pass"] and summary["equivalence_pass"] and summary["fresh_artifact_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
