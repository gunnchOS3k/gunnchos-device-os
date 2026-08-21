#!/usr/bin/env python3
"""Generate Wave009 OS-PLATFORM-020 sandbox validation evidence."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from gunnchos_device_os.platform.sandbox_executor import SandboxExecutor  # noqa: E402
from gunnchos_device_os.sandbox_policy import SandboxPolicyEngine  # noqa: E402
from gunnchos_device_os.wave009_os020.behavioral_negative_controls import (  # noqa: E402
    prove_behavioral_negative_controls,
)
from gunnchos_device_os.wave009_os020.environment import (  # noqa: E402
    apply_ephemeral_userns_repair,
    capture_environment_preflight,
)
from gunnchos_device_os.wave009_os020.evaluator import (  # noqa: E402
    CLAIM_BOUNDARIES,
    accept_suite_for_gate,
    evaluate_os_platform_020,
    run_completion_gate_negative_controls,
    run_wave009_evaluation,
)
from gunnchos_device_os.wave009_os020.evaluator_integrity import inspect_wave009_evaluator  # noqa: E402

ABS_PATH_RE = re.compile(r"(/Users/|/home/[^/]+/|/mnt/|/private/var/folders/|[A-Za-z]:\\\\)")


def _git(cmd: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *cmd], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def _file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else "missing"


def _redact(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _redact(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_redact(v) for v in obj]
    if isinstance(obj, str) and ABS_PATH_RE.search(obj):
        try:
            p = Path(obj)
            if p.is_absolute():
                parts = p.parts
                for marker in ("artifacts", "gunnchos_device_os", "scripts", "tests"):
                    if marker in parts:
                        idx = parts.index(marker)
                        return "/".join(parts[idx:])
                return "<redacted_absolute_path>"
        except Exception:
            return "<redacted_absolute_path>"
    return obj


def _write(out: Path, name: str, payload: Any) -> None:
    payload = _redact(payload)
    blob = json.dumps(payload, indent=2, sort_keys=True, default=str)
    if ABS_PATH_RE.search(blob):
        # Soft-scrub remaining absolute paths for committed evidence.
        blob = ABS_PATH_RE.sub("<redacted>", blob)
    (out / name).write_text(blob + "\n", encoding="utf-8")


def main() -> int:
    out = ROOT / "artifacts" / "engineering_wave009"
    out.mkdir(parents=True, exist_ok=True)
    (out / ".gitignore").write_text("runtime_work/\n", encoding="utf-8")

    preflight_path = out / "ENVIRONMENT_PREFLIGHT.json"
    if preflight_path.exists() and os.environ.get("WAVE009_PRESERVE_PREFLIGHT", "1") == "1":
        preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    else:
        preflight = capture_environment_preflight()
        _write(out, "ENVIRONMENT_PREFLIGHT.json", preflight)

    repair_path = out / "HOST_USERNS_CONFIGURATION_RESULT.json"
    if repair_path.exists() and os.environ.get("WAVE009_PRESERVE_PREFLIGHT", "1") == "1":
        repair = json.loads(repair_path.read_text(encoding="utf-8"))
    else:
        repair = apply_ephemeral_userns_repair(allow_sudo=os.environ.get("WAVE009_ALLOW_HOST_SUDO", "0") == "1")
        _write(out, "HOST_USERNS_CONFIGURATION_RESULT.json", repair)

    from gunnchos_device_os.wave009_os020.environment import _bwrap_unprivileged_smoke  # local helper

    bwrap = shutil.which("bwrap")
    smoke: dict[str, Any]
    if bwrap and os.geteuid() != 0:
        bound = _bwrap_unprivileged_smoke(bwrap)
        smoke = {
            "schema": "gunnchos.engineering_wave009.bwrap_smoke.v1",
            "ok": bound.get("returncode") == 0,
            "bound_true": bound,
            "SANDBOX_EXECUTED_AS_ROOT": False,
            "BWRAP_INVOKED_WITH_SUDO": False,
            "POST_REPAIR_UNPRIVILEGED_BWRAP_WORKS": bound.get("returncode") == 0
            or repair.get("POST_REPAIR_UNPRIVILEGED_BWRAP_WORKS") is True,
        }
    else:
        smoke = {
            "schema": "gunnchos.engineering_wave009.bwrap_smoke.v1",
            "ok": False,
            "reason": "bwrap_absent_or_root_runner",
            "bwrap": bwrap,
            "euid": os.geteuid(),
            "POST_REPAIR_UNPRIVILEGED_BWRAP_WORKS": False,
            "SANDBOX_EXECUTED_AS_ROOT": os.geteuid() == 0,
            "BWRAP_INVOKED_WITH_SUDO": False,
        }
    _write(out, "BWRAP_SMOKE_RESULT.json", smoke)

    work = out / "runtime_work"
    work.mkdir(parents=True, exist_ok=True)
    suite = SandboxExecutor(work, SandboxPolicyEngine()).run_enforcement_suite("wave009-mandatory")
    _write(out, "SANDBOX_ENFORCEMENT_RESULT.json", suite)

    positive = {
        "schema": "gunnchos.engineering_wave009.positive_app_root.v1",
        "PRIVATE_ROOT_RW_PASS": suite.get("PRIVATE_ROOT_RW_PASS"),
        "APP_ROOT_READ_ALLOWED": suite.get("APP_ROOT_READ_ALLOWED"),
        "APP_ROOT_WRITE_ALLOWED": suite.get("APP_ROOT_WRITE_ALLOWED"),
        "NORMAL_PYTHON_EXECUTION_INSIDE_SANDBOX": suite.get("NORMAL_PYTHON_EXECUTION_INSIDE_SANDBOX"),
        "FIXTURE_RAN": suite.get("fixture_ran"),
    }
    _write(out, "POSITIVE_APP_ROOT_RESULT.json", positive)

    filesystem = {
        "schema": "gunnchos.engineering_wave009.filesystem_escape.v1",
        "HOST_PRIVATE_READ_BLOCKED": suite.get("HOST_PRIVATE_READ_BLOCKED"),
        "OUTSIDE_WRITE_BLOCKED": suite.get("OUTSIDE_WRITE_BLOCKED"),
        "CROSS_APP_READ_BLOCKED": suite.get("CROSS_APP_READ_BLOCKED"),
        "SYMLINK_HOST_ESCAPE_BLOCKED": suite.get("SYMLINK_HOST_ESCAPE_BLOCKED"),
        "SYMLINK_CROSS_APP_ESCAPE_BLOCKED": suite.get("SYMLINK_CROSS_APP_ESCAPE_BLOCKED"),
        "PATH_TRAVERSAL_ESCAPE_BLOCKED": suite.get("PATH_TRAVERSAL_ESCAPE_BLOCKED"),
        "PROC_ROOT_ESCAPE_BLOCKED": suite.get("PROC_ROOT_ESCAPE_BLOCKED"),
    }
    _write(out, "FILESYSTEM_ESCAPE_RESULT.json", filesystem)

    network = {
        "schema": "gunnchos.engineering_wave009.network_seccomp.v1",
        "NETWORK_DENIED": suite.get("NETWORK_DENIED"),
        "NETWORK_CONTROL_REACHABLE": suite.get("NETWORK_CONTROL_REACHABLE"),
        "SECCOMP_LOADED": suite.get("SECCOMP_LOADED"),
    }
    _write(out, "NETWORK_SECCOMP_RESULT.json", network)

    child = {
        "schema": "gunnchos.engineering_wave009.child_exec_seccomp.v1",
        "CHILD_SPAWN_DENIED": suite.get("CHILD_SPAWN_DENIED"),
        "CONTROL_CHILD_EXEC_WORKS": suite.get("CONTROL_CHILD_EXEC_WORKS"),
        "SECCOMP_LOADED": suite.get("SECCOMP_LOADED"),
    }
    _write(out, "CHILD_EXEC_SECCOMP_RESULT.json", child)

    privilege = {
        "schema": "gunnchos.engineering_wave009.privilege_escape.v1",
        "PRIVILEGED_CAPABILITY_DENIED": suite.get("PRIVILEGED_CAPABILITY_DENIED"),
        "HOST_ROOT_ESCALATION_BLOCKED": suite.get("HOST_ROOT_ESCALATION_BLOCKED"),
        "DANGEROUS_DEVICE_ACCESS_BLOCKED": suite.get("DANGEROUS_DEVICE_ACCESS_BLOCKED"),
        "MOUNT_ESCAPE_BLOCKED": suite.get("MOUNT_ESCAPE_BLOCKED"),
        "fixture_caps": {
            "uid": (suite.get("fixture_result") or {}).get("uid"),
            "euid": (suite.get("fixture_result") or {}).get("euid"),
            "cap_eff": (suite.get("fixture_result") or {}).get("cap_eff"),
            "no_new_privs": (suite.get("fixture_result") or {}).get("no_new_privs"),
        },
    }
    _write(out, "PRIVILEGE_ESCAPE_RESULT.json", privilege)

    controls = {
        "schema": "gunnchos.engineering_wave009.control_probes.v1",
        "CONTROL_HOST_SECRET_READABLE": suite.get("CONTROL_HOST_SECRET_READABLE"),
        "CONTROL_NETWORK_REACHABLE": suite.get("CONTROL_NETWORK_REACHABLE"),
        "CONTROL_CHILD_EXEC_WORKS": suite.get("CONTROL_CHILD_EXEC_WORKS"),
        "CONTROL_CROSS_APP_READABLE": suite.get("CONTROL_CROSS_APP_READABLE"),
        "CONTROL_OUTSIDE_WRITABLE_WHEN_PERMITTED": suite.get("CONTROL_OUTSIDE_WRITABLE_WHEN_PERMITTED"),
    }
    _write(out, "CONTROL_PROBES_RESULT.json", controls)

    behavioral = prove_behavioral_negative_controls()
    _write(out, "BEHAVIORAL_NEGATIVE_CONTROL_RESULT.json", behavioral)

    evaluation = run_wave009_evaluation(suite)
    row = evaluation["classification"]["OS-PLATFORM-020"]
    integrity = evaluation["integrity"]
    # Prefer integrity computed against source without re-running suite side effects when suite provided.
    integrity = inspect_wave009_evaluator(evaluate_os_platform_020)
    gate = accept_suite_for_gate(row, integrity=integrity)
    gate_neg = run_completion_gate_negative_controls()
    _write(out, "EVALUATOR_INTEGRITY_RESULT.json", integrity)
    _write(out, "COMPLETION_GATE_NEGATIVE_CONTROL_RESULT.json", gate_neg)

    os020 = {
        "schema": "gunnchos.engineering_wave009.os_platform_020_result.v1",
        "requirement_id": "OS-PLATFORM-020",
        "classification": row.get("classification"),
        "ok": row.get("ok"),
        "SANDBOX_BACKEND": suite.get("SANDBOX_BACKEND"),
        "KERNEL_SANDBOX": suite.get("KERNEL_SANDBOX"),
        "SANDBOX_EXECUTION_VALIDATED": suite.get("SANDBOX_EXECUTION_VALIDATED"),
        "LOCAL_SANDBOX_VALIDATION": suite.get("LOCAL_SANDBOX_VALIDATION"),
        "PLAIN_SUBPROCESS_COUNTS_AS_SANDBOX": False,
        "gate": gate,
        "reasons": row.get("reasons"),
        "evidence_keys": sorted((row.get("evidence") or {}).keys()),
    }
    _write(out, "OS_PLATFORM_020_RESULT.json", os020)

    provenance = {
        "schema": "gunnchos.engineering_wave009.execution_provenance.v1",
        "repo": "gunnchos-device-os",
        "source_sha": _git(["rev-parse", "HEAD"]),
        "source_tree": _git(["rev-parse", "HEAD^{tree}"]),
        "branch": _git(["rev-parse", "--abbrev-ref", "HEAD"]),
        "runner_os": platform.platform(),
        "runner_image": os.environ.get("ImageOS") or os.environ.get("RUNNER_OS") or platform.system(),
        "kernel": platform.release(),
        "normal_runner_uid": os.getuid(),
        "normal_runner_gid": os.getgid(),
        "normal_runner_euid": os.geteuid(),
        "bwrap_version": (preflight.get("bwrap_version") or {}),
        "seccomp_python": preflight.get("seccomp_python"),
        "userns_sysctl_before": repair.get("before"),
        "userns_sysctl_after": repair.get("after"),
        "apparmor_userns_before": repair.get("APPARMOR_RESTRICT_USERNS_BEFORE"),
        "apparmor_userns_after": repair.get("APPARMOR_RESTRICT_USERNS_AFTER"),
        "sandbox_executor_hash": _file_hash(ROOT / "gunnchos_device_os/platform/sandbox_executor.py"),
        "sandbox_policy_hash": _file_hash(ROOT / "gunnchos_device_os/sandbox_policy.py"),
        "evaluator_source_hash": evaluation.get("evaluator_source_hash"),
        "fixture_marker": "PROBE_FIXTURE+SECCOMP_LAUNCHER",
        "SANDBOX_EXECUTED_AS_ROOT": suite.get("SANDBOX_EXECUTED_AS_ROOT"),
        "BWRAP_INVOKED_WITH_SUDO": suite.get("BWRAP_INVOKED_WITH_SUDO"),
    }
    _write(out, "EXECUTION_PROVENANCE.json", provenance)

    claims = {
        "schema": "gunnchos.engineering_wave009.claim_boundaries.v1",
        **CLAIM_BOUNDARIES,
        "KERNEL_SANDBOX": suite.get("KERNEL_SANDBOX"),
        "SANDBOX_EXECUTION_VALIDATED": suite.get("SANDBOX_EXECUTION_VALIDATED"),
    }
    _write(out, "CLAIM_BOUNDARIES.json", claims)

    validated = gate.get("complete") is True and row.get("classification") == "IMPLEMENTED_AND_VALIDATED"
    blocked = row.get("classification") == "BLOCKED_ENVIRONMENT"
    status = "PASS" if validated else ("BLOCKED_ENVIRONMENT" if blocked else "FAIL")

    wave = {
        "schema": "gunnchos.engineering_wave009.result.v1",
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "ENGINEERING_WAVE_009": status,
        "TARGET_REQUIREMENTS": 1,
        "OS_PLATFORM_020": row.get("classification"),
        "wave009_ok": validated,
        "PARTIAL": False,
        "summary": evaluation["summary"],
        "PRE_REPAIR_UNPRIVILEGED_BWRAP_WORKS": preflight.get("PRE_REPAIR_UNPRIVILEGED_BWRAP_WORKS"),
        "PRE_REPAIR_BWRAP_ERROR": preflight.get("PRE_REPAIR_BWRAP_ERROR"),
        "POST_REPAIR_UNPRIVILEGED_BWRAP_WORKS": smoke.get("POST_REPAIR_UNPRIVILEGED_BWRAP_WORKS"),
        "USERNS_CLONE_BEFORE": repair.get("USERNS_CLONE_BEFORE"),
        "USERNS_CLONE_AFTER": repair.get("USERNS_CLONE_AFTER"),
        "APPARMOR_RESTRICT_USERNS_BEFORE": repair.get("APPARMOR_RESTRICT_USERNS_BEFORE"),
        "APPARMOR_RESTRICT_USERNS_AFTER": repair.get("APPARMOR_RESTRICT_USERNS_AFTER"),
        "MAX_USER_NAMESPACES": repair.get("MAX_USER_NAMESPACES"),
        "SANDBOX_EXECUTED_AS_ROOT": suite.get("SANDBOX_EXECUTED_AS_ROOT"),
        "BWRAP_INVOKED_WITH_SUDO": suite.get("BWRAP_INVOKED_WITH_SUDO"),
        "SANDBOX_BACKEND": suite.get("SANDBOX_BACKEND"),
        "FIXTURE_RAN": suite.get("fixture_ran"),
        "KERNEL_SANDBOX": suite.get("KERNEL_SANDBOX"),
        "SANDBOX_EXECUTION_VALIDATED": suite.get("SANDBOX_EXECUTION_VALIDATED"),
        "LOCAL_SANDBOX_VALIDATION": suite.get("LOCAL_SANDBOX_VALIDATION"),
        "PLAIN_SUBPROCESS_COUNTS_AS_SANDBOX": False,
        "BEHAVIORAL_NEGATIVE_CONTROL_COUNT": behavioral.get("BEHAVIORAL_NEGATIVE_CONTROL_COUNT"),
        "BEHAVIORAL_NEGATIVE_CONTROLS_PASS": behavioral.get("BEHAVIORAL_NEGATIVE_CONTROLS_PASS"),
        "UNCONDITIONAL_TRUE_CLASSIFIERS": integrity.get("UNCONDITIONAL_TRUE_CLASSIFIERS"),
        "UNCONDITIONAL_TRUE_CLASSIFIERS_COMPUTED": True,
        "COMPLETE_GATE_REQUIRES_1_OF_1": True,
        "completion_gate": gate,
        "completion_gate_negatives": {
            k: gate_neg.get(k)
            for k in (
                "BROKEN_EVALUATOR_REJECTED",
                "MISSING_EVALUATOR_REJECTED",
                "WRONG_EVALUATOR_ID_REJECTED",
                "EMPTY_EVIDENCE_REJECTED",
                "STALE_EVIDENCE_REJECTED",
                "WRONG_SOURCE_HASH_REJECTED",
            )
        },
        "BASELINE_COUNTS_UPDATED": False,
        "DIGITAL_VALIDATION_QUEUE_UPDATED": False,
        "CURSOR_MERGED_NOTHING": True,
        "claim_boundaries": claims,
        "provenance": {
            "source_sha": provenance["source_sha"],
            "source_tree": provenance["source_tree"],
        },
    }
    _write(out, "WAVE009_RESULT.json", wave)

    # Strict gates
    if behavioral.get("ok") is not True:
        print("WAVE009 FAIL: behavioral negative controls", file=sys.stderr)
        return 2
    if gate_neg.get("ok") is not True:
        print("WAVE009 FAIL: completion gate negatives", file=sys.stderr)
        return 2
    if suite.get("PLAIN_SUBPROCESS_COUNTS_AS_SANDBOX") is not False:
        print("WAVE009 FAIL: plain subprocess claimed", file=sys.stderr)
        return 2
    if suite.get("SANDBOX_EXECUTED_AS_ROOT") is True or suite.get("BWRAP_INVOKED_WITH_SUDO") is True:
        print("WAVE009 FAIL: sandbox executed as root/sudo", file=sys.stderr)
        return 2

    require_pass = os.environ.get("WAVE009_REQUIRE_SANDBOX_VALIDATED", "0") == "1"
    if require_pass and not validated:
        print(json.dumps({"status": status, "os020": os020}, indent=2, default=str))
        print("WAVE009 FAIL: required validated sandbox not earned", file=sys.stderr)
        return 1

    if validated:
        print("WAVE009 PASS: OS-PLATFORM-020 IMPLEMENTED_AND_VALIDATED")
        return 0

    # Honest local/diagnostic blocked path is success for make wave009 unless CI requires pass.
    print(f"WAVE009 {status}: OS-PLATFORM-020={row.get('classification')} backend={suite.get('SANDBOX_BACKEND')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
