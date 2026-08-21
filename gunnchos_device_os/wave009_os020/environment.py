"""READ-ONLY environment diagnosis + unprivileged bwrap smoke."""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _run(cmd: list[str], *, timeout: float = 15.0) -> dict[str, Any]:
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
        return {
            "cmd": cmd,
            "returncode": proc.returncode,
            "stdout": (proc.stdout or "")[-4000:],
            "stderr": (proc.stderr or "")[-4000:],
        }
    except Exception as exc:  # noqa: BLE001
        return {"cmd": cmd, "error": str(exc)}


def _read_text(path: str) -> str | None:
    try:
        return Path(path).read_text(encoding="utf-8").strip()
    except OSError:
        return None


def _sysctl(name: str) -> dict[str, Any]:
    out = _run(["sysctl", "-n", name])
    value = (out.get("stdout") or "").strip() if out.get("returncode") == 0 else None
    return {"name": name, "value": value or None, "raw": out}


def capture_environment_preflight() -> dict[str, Any]:
    bwrap = shutil.which("bwrap")
    seccomp: dict[str, Any]
    try:
        import seccomp  # type: ignore

        seccomp = {"available": True, "module_file": getattr(seccomp, "__file__", None)}
    except Exception as exc:  # noqa: BLE001
        seccomp = {"available": False, "error": str(exc)}

    smoke: dict[str, Any]
    if bwrap:
        smoke = _run([bwrap, "--unshare-user", "--", "/usr/bin/id"])
        if smoke.get("returncode") not in (0, None):
            # trivial true may be more portable than id when /usr missing in some setups
            smoke_true = _run([bwrap, "--unshare-user", "--", "/bin/true"])
            smoke = {"primary": smoke, "fallback_true": smoke_true}
    else:
        smoke = {"skipped": True, "reason": "bwrap_absent"}

    userns_clone = _sysctl("kernel.unprivileged_userns_clone")
    apparmor = _sysctl("kernel.apparmor_restrict_unprivileged_userns")
    max_userns = _sysctl("user.max_user_namespaces")
    if max_userns.get("value") is None:
        max_from_proc = _read_text("/proc/sys/user/max_user_namespaces")
        max_userns = {"name": "user.max_user_namespaces", "value": max_from_proc, "raw": {"proc": max_from_proc}}

    pre_repair_works = False
    pre_repair_error = None
    if bwrap:
        if isinstance(smoke, dict) and "primary" in smoke:
            primary = smoke["primary"]
            fallback = smoke.get("fallback_true") or {}
            pre_repair_works = primary.get("returncode") == 0 or fallback.get("returncode") == 0
            if not pre_repair_works:
                pre_repair_error = (primary.get("stderr") or fallback.get("stderr") or primary.get("error") or "")[-800:]
        else:
            pre_repair_works = smoke.get("returncode") == 0
            if not pre_repair_works:
                pre_repair_error = (smoke.get("stderr") or smoke.get("error") or "")[-800:]

    return {
        "schema": "gunnchos.engineering_wave009.environment_preflight.v1",
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "runner_os": platform.platform(),
        "system": platform.system(),
        "kernel": platform.release(),
        "machine": platform.machine(),
        "python_version": sys.version,
        "uid": os.getuid(),
        "gid": os.getgid(),
        "euid": os.geteuid(),
        "bwrap_path": bwrap,
        "bwrap_version": _run([bwrap, "--version"]) if bwrap else None,
        "seccomp_python": seccomp,
        "uname": _run(["uname", "-a"]),
        "os_release": _read_text("/etc/os-release"),
        "id_cmd": _run(["id"]),
        "userns_clone": userns_clone,
        "apparmor_restrict_unprivileged_userns": apparmor,
        "max_user_namespaces": max_userns,
        "aa_status": _run(["aa-status"]),
        "proc_self_status_caps": _run(
            ["bash", "-lc", "grep -E 'Seccomp|NoNewPrivs|Cap(Inh|Prm|Eff|Bnd|Amb)' /proc/self/status || true"]
        ),
        "raw_bwrap_smoke": smoke,
        "PRE_REPAIR_UNPRIVILEGED_BWRAP_WORKS": pre_repair_works,
        "PRE_REPAIR_BWRAP_ERROR": pre_repair_error,
        "SANDBOX_EXECUTED_AS_ROOT": os.geteuid() == 0,
        "BWRAP_INVOKED_WITH_SUDO": False,
    }


def apply_ephemeral_userns_repair(*, allow_sudo: bool = True) -> dict[str, Any]:
    """Host-only repair. Never wraps bwrap/fixture with sudo."""
    before = {
        "userns_clone": _sysctl("kernel.unprivileged_userns_clone"),
        "apparmor_restrict_unprivileged_userns": _sysctl("kernel.apparmor_restrict_unprivileged_userns"),
        "max_user_namespaces": _sysctl("user.max_user_namespaces"),
    }
    actions: list[dict[str, Any]] = []
    if not allow_sudo or os.geteuid() == 0:
        # Still record; CI uses sudo as normal runner via passwordless sudo.
        pass

    def _maybe_sysctl(key: str, desired: str) -> None:
        current = _sysctl(key).get("value")
        if current is None:
            actions.append({"action": "skip_missing_sysctl", "key": key})
            return
        if current == desired:
            actions.append({"action": "already_set", "key": key, "value": current})
            return
        if not allow_sudo:
            actions.append({"action": "would_set_without_sudo_denied", "key": key, "from": current, "to": desired})
            return
        result = _run(["sudo", "sysctl", "-w", f"{key}={desired}"])
        actions.append({"action": "sysctl_set", "key": key, "from": current, "to": desired, "result": result})

    # Smallest admissible Ubuntu 24.04 repair path.
    _maybe_sysctl("kernel.apparmor_restrict_unprivileged_userns", "0")
    _maybe_sysctl("kernel.unprivileged_userns_clone", "1")

    after = {
        "userns_clone": _sysctl("kernel.unprivileged_userns_clone"),
        "apparmor_restrict_unprivileged_userns": _sysctl("kernel.apparmor_restrict_unprivileged_userns"),
        "max_user_namespaces": _sysctl("user.max_user_namespaces"),
    }

    bwrap = shutil.which("bwrap")
    post_smoke: dict[str, Any]
    post_works = False
    if bwrap and os.geteuid() != 0:
        post_smoke = _run([bwrap, "--unshare-user", "--", "/usr/bin/id"])
        if post_smoke.get("returncode") != 0:
            alt = _run([bwrap, "--unshare-user", "--", "/bin/true"])
            post_smoke = {"primary": post_smoke, "fallback_true": alt}
            post_works = alt.get("returncode") == 0
        else:
            post_works = True
    elif not bwrap:
        post_smoke = {"skipped": True, "reason": "bwrap_absent"}
    else:
        post_smoke = {"skipped": True, "reason": "runner_is_root_forbidden_for_sandbox_validation"}
        post_works = False

    return {
        "schema": "gunnchos.engineering_wave009.host_userns_configuration.v1",
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "before": before,
        "after": after,
        "actions": actions,
        "POST_REPAIR_UNPRIVILEGED_BWRAP_WORKS": post_works,
        "post_repair_bwrap_smoke": post_smoke,
        "SANDBOX_EXECUTED_AS_ROOT": os.geteuid() == 0,
        "BWRAP_INVOKED_WITH_SUDO": False,
        "USERNS_CLONE_BEFORE": (before["userns_clone"] or {}).get("value"),
        "USERNS_CLONE_AFTER": (after["userns_clone"] or {}).get("value"),
        "APPARMOR_RESTRICT_USERNS_BEFORE": (before["apparmor_restrict_unprivileged_userns"] or {}).get("value"),
        "APPARMOR_RESTRICT_USERNS_AFTER": (after["apparmor_restrict_unprivileged_userns"] or {}).get("value"),
        "MAX_USER_NAMESPACES": (after["max_user_namespaces"] or {}).get("value"),
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
