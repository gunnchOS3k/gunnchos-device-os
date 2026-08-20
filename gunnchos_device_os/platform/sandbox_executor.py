"""Execution-enforced sandbox — bubblewrap / sandbox-exec only count as validation.

Plain subprocess MUST NOT count as sandbox validation. When no genuine backend
can prove the mandatory probes, LOCAL_SANDBOX_VALIDATION=BLOCKED_ENVIRONMENT.
"""
from __future__ import annotations

import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from gunnchos_device_os.sandbox_policy import Capability, SandboxPolicyEngine

CLAIM_BOUNDARY = (
    "KERNEL_SANDBOX=true only when bubblewrap namespaces prove mandatory probes. "
    "sandbox-exec counts only when the same probes pass. "
    "PLAIN_SUBPROCESS_COUNTS_AS_SANDBOX=false always."
)

HOST_SECRET_CONTENT = "WAVE004-HOST-SECRET-MUST-NOT-READ"

SECCOMP_LAUNCHER = r'''
import runpy
import sys

def _load_seccomp() -> None:
    try:
        import seccomp  # type: ignore
    except Exception:
        # Mount isolation may still deny shell binaries; same-interpreter spawn needs seccomp.
        return
    filt = seccomp.SyscallFilter(defaction=seccomp.ALLOW)
    filt.add_rule(seccomp.ERRNO(1), "execve")
    filt.add_rule(seccomp.ERRNO(1), "execveat")
    filt.load()

if __name__ == "__main__":
    target = sys.argv[1]
    _load_seccomp()
    sys.argv = [target]
    runpy.run_path(target, run_name="__main__")
'''

PROBE_FIXTURE = f'''
import json
import os
import socket
import subprocess
import sys
from pathlib import Path

HOST_SECRET_MARK = {HOST_SECRET_CONTENT!r}

result = {{
    "host_private_read": False,
    "host_private_data": None,
    "outside_write": False,
    "network_reach": False,
    "child_spawn": False,
    "privileged_capability": False,
    "cross_app_read": False,
}}

host_secret = os.environ.get("HOST_PRIVATE_SECRET", "")
try:
    data = Path(host_secret).read_text(encoding="utf-8")
    result["host_private_read"] = HOST_SECRET_MARK in data
    result["host_private_data"] = data.strip()[:80]
except Exception:
    result["host_private_read"] = False

escape = os.environ.get("OUTSIDE_WRITE_TARGET", "")
try:
    Path(escape).write_text("escaped", encoding="utf-8")
    result["outside_write"] = Path(escape).exists()
except Exception:
    result["outside_write"] = False

host = os.environ.get("CONTROL_HOST", "127.0.0.1")
port = int(os.environ.get("CONTROL_PORT", "0") or "0")
try:
    with socket.create_connection((host, port), timeout=1.0) as s:
        s.sendall(b"PING\\n")
        data = s.recv(16)
        result["network_reach"] = data.startswith(b"PONG")
except Exception:
    result["network_reach"] = False

spawned = False
for candidate in ("/bin/sh", "/usr/bin/id", "/bin/true", "/usr/bin/python3"):
    try:
        proc = subprocess.run([candidate, "--version"] if "python" in candidate else [candidate],
                              capture_output=True, timeout=2, check=False)
        spawned = True
        break
    except FileNotFoundError:
        continue
    except Exception as exc:
        if "Permission" in type(exc).__name__ or "permission" in str(exc).lower():
            continue
        # Exec blocked by seccomp typically raises OSError/PermissionError
        continue
try:
    subprocess.run([sys.executable, "-c", "print(1)"], capture_output=True, timeout=2, check=True)
    spawned = True
except Exception:
    pass
try:
    if os.system("echo pwned >/dev/null 2>&1") == 0:
        spawned = True
except Exception:
    pass
result["child_spawn"] = spawned

try:
    os.setuid(0)
    result["privileged_capability"] = True
except Exception:
    result["privileged_capability"] = False
try:
    Path("/dev/mem").open("rb").read(1)
    result["privileged_capability"] = True
except Exception:
    pass

cross = os.environ.get("CROSS_APP_SECRET", "")
try:
    data = Path(cross).read_text(encoding="utf-8")
    result["cross_app_read"] = "CROSS-APP-SECRET" in data
except Exception:
    result["cross_app_read"] = False

print(json.dumps(result))
'''

@dataclass
class SandboxExecutor:
    root: Path
    policy_engine: SandboxPolicyEngine
    audit: list[dict[str, Any]] = field(default_factory=list)
    bwrap: str | None = field(default=None, init=False)
    sandbox_exec: str | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.bwrap = shutil.which("bwrap")
        self.sandbox_exec = shutil.which("sandbox-exec") if platform.system() == "Darwin" else None

    @property
    def kernel_sandbox(self) -> bool:
        return bool(self.bwrap)

    @property
    def genuine_backend_available(self) -> bool:
        return bool(self.bwrap or self.sandbox_exec)

    def _audit(self, event: str, detail: dict[str, Any]) -> None:
        self.audit.append({"event": event, **detail, "claim_boundary": CLAIM_BOUNDARY})

    def _start_control_server(self) -> tuple[socket.socket, int]:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        sock.listen(5)

        def _serve() -> None:
            while True:
                try:
                    conn, _ = sock.accept()
                except OSError:
                    break
                with conn:
                    try:
                        conn.recv(64)
                        conn.sendall(b"PONG\n")
                    except OSError:
                        pass

        threading.Thread(target=_serve, daemon=True).start()
        return sock, port
    def _control_reachable_unsandboxed(self, port: int) -> bool:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1.0) as s:
                s.sendall(b"PING\n")
                return s.recv(16).startswith(b"PONG")
        except OSError:
            return False

    def _build_bwrap_cmd(self, work: str, launcher: Path, script_path: Path, py: str) -> list[str]:
        assert self.bwrap
        real_py = str(Path(py).resolve())
        prefix = str(Path(sys.prefix).resolve())
        cmd = [
            self.bwrap,
            "--unshare-all",
            "--die-with-parent",
            "--proc",
            "/proc",
            "--dev",
            "/dev",
            # Do not tmpfs-mask /tmp: pytest/CI place sandbox roots under /tmp and
            # masking it before bind can break the writable app root.
            "--ro-bind",
            "/usr",
            "/usr",
        ]
        for p in ("/lib", "/lib64", "/lib32", "/bin", "/sbin"):
            if Path(p).exists():
                cmd.extend(["--ro-bind", p, p])
        if Path(prefix).exists():
            cmd.extend(["--ro-bind", prefix, prefix])
        cmd.extend(["--ro-bind", real_py, real_py])
        # System site-packages (apt python3-seccomp) when using --system-site-packages venvs.
        for site in (
            "/usr/lib/python3/dist-packages",
            f"/usr/lib/python{sys.version_info.major}.{sys.version_info.minor}/dist-packages",
        ):
            if Path(site).exists():
                cmd.extend(["--ro-bind", site, site])
        for bind in ("/etc/ld.so.cache", "/etc/alternatives", "/etc/ssl", "/etc/passwd"):
            if Path(bind).exists():
                cmd.extend(["--ro-bind", bind, bind])
        cmd.extend(
            [
                "--bind",
                work,
                work,
                "--chdir",
                work,
                "--clearenv",
                "--setenv",
                "PATH",
                "/usr/bin:/bin",
                "--setenv",
                "HOME",
                work,
                "--setenv",
                "PYTHONPATH",
                "/usr/lib/python3/dist-packages",
                "--setenv",
                "LANG",
                "C",
                "--",
                real_py,
                str(launcher),
                str(script_path),
            ]
        )
        return cmd
    def _build_sandbox_exec_cmd(self, work: str, script_path: Path, py: str) -> list[str] | None:
        if not self.sandbox_exec:
            return None
        profile = (
            '(version 1)'
            '(deny default)'
            '(allow process-fork)'
            '(allow process-exec)'
            '(allow sysctl-read)'
            '(allow file-read* (subpath "/usr"))'
            '(allow file-read* (subpath "/System"))'
            '(allow file-read* (subpath "/Library"))'
            '(allow file-read* (subpath "/bin"))'
            '(allow file-read* (subpath "/private/var/db"))'
            f'(allow file-read* (subpath "{work}"))'
            f'(allow file-write* (subpath "{work}"))'
            f'(allow file-read* (literal "{py}"))'
            f'(allow file-read* (subpath "{str(Path(py).resolve().parent)}"))'
        )
        return [self.sandbox_exec, "-p", profile, py, str(script_path)]

    def _run_probe(
        self,
        *,
        backend: str,
        cmd: list[str],
        work: Path,
        env: dict[str, str],
        timeout: float,
    ) -> dict[str, Any]:
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(work),
                env=env,
            )
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "timeout", "backend": backend}
        parsed: dict[str, Any] = {}
        for line in reversed((proc.stdout or "").strip().splitlines()):
            line = line.strip()
            if line.startswith("{"):
                try:
                    parsed = json.loads(line)
                    break
                except json.JSONDecodeError:
                    continue
        return {
            "exit_code": proc.returncode,
            "fixture_result": parsed,
            "stderr_tail": (proc.stderr or "")[-800:],
            "stdout_tail": (proc.stdout or "")[-800:],
            "backend": backend,
        }

    def run_enforcement_suite(self, app_id: str = "sandbox-suite", *, timeout: float = 20.0) -> dict[str, Any]:
        """Mandatory probes. Plain subprocess never validates."""
        self.policy_engine.create_profile(app_id, "untrusted")
        for cap in (Capability.SYSTEM_SERVICE, Capability.EXEC_CHILD, Capability.FS_SHARED_WRITE):
            decision = self.policy_engine.check_capability(app_id, cap)
            if decision.get("decision") != "deny":
                return {
                    "ok": False,
                    "SANDBOX_EXECUTION_VALIDATED": False,
                    "error": "policy_leak_before_exec",
                    "PLAIN_SUBPROCESS_COUNTS_AS_SANDBOX": False,
                }

        work_root = Path(tempfile.mkdtemp(prefix=f"sandbox-{app_id}-", dir=self.root))
        app_root = work_root / "app"
        host_private = work_root / "host_private"
        outside = work_root / "outside"
        cross_app = work_root / "app_a_private"
        app_root.mkdir()
        host_private.mkdir()
        outside.mkdir()
        cross_app.mkdir()
        secret_path = host_private / "secret.txt"
        secret_path.write_text(HOST_SECRET_CONTENT + "\n", encoding="utf-8")
        cross_secret = cross_app / "secret.txt"
        cross_secret.write_text("CROSS-APP-SECRET-MUST-NOT-READ\n", encoding="utf-8")
        escape_target = outside / "escape_marker.txt"
        os.chmod(outside, 0o555)

        script_path = app_root / "probe.py"
        script_path.write_text(PROBE_FIXTURE, encoding="utf-8")
        launcher_path = app_root / "seccomp_launcher.py"
        launcher_path.write_text(SECCOMP_LAUNCHER, encoding="utf-8")

        control_sock, port = self._start_control_server()
        network_control_reachable = self._control_reachable_unsandboxed(port)

        py = sys.executable
        base_env = {
            "PATH": "/usr/bin:/bin",
            "HOME": str(app_root),
            "PYTHONPATH": "",
            "HOST_PRIVATE_SECRET": str(secret_path),
            "OUTSIDE_WRITE_TARGET": str(escape_target),
            "CROSS_APP_SECRET": str(cross_secret),
            "CONTROL_HOST": "127.0.0.1",
            "CONTROL_PORT": str(port),
            "LANG": "C",
        }

        backend = "none"
        run: dict[str, Any] = {}
        local_status = "BLOCKED_ENVIRONMENT"

        try:
            if self.bwrap:
                backend = "bubblewrap"
                env = dict(base_env)
                cmd = self._build_bwrap_cmd(str(app_root), launcher_path, script_path, py)
                idx = cmd.index("--")
                for k, v in env.items():
                    cmd.insert(idx, v)
                    cmd.insert(idx, k)
                    cmd.insert(idx, "--setenv")
                    idx = cmd.index("--")
                run = self._run_probe(backend=backend, cmd=cmd, work=app_root, env=env, timeout=timeout)
            elif self.sandbox_exec:
                backend = "sandbox_exec"
                cmd = self._build_sandbox_exec_cmd(str(app_root), script_path, py)
                if cmd is None:
                    run = {"error": "sandbox_exec_unavailable"}
                else:
                    run = self._run_probe(
                        backend=backend, cmd=cmd, work=app_root, env=base_env, timeout=timeout
                    )
                    # If sandbox-exec cannot apply, do NOT fall back to plain subprocess as pass.
                    if "sandbox_apply" in (run.get("stderr_tail") or "") or (
                        run.get("exit_code") not in (0, None) and not run.get("fixture_result")
                    ):
                        local_status = "BLOCKED_ENVIRONMENT"
                        backend = "sandbox_exec_unavailable"
            else:
                backend = "subprocess_broker"
                # Diagnostic-only plain subprocess — NEVER validates.
                run = self._run_probe(
                    backend=backend,
                    cmd=[py, str(script_path)],
                    work=app_root,
                    env=base_env,
                    timeout=timeout,
                )
                local_status = "BLOCKED_ENVIRONMENT"
        finally:
            try:
                control_sock.close()
            except OSError:
                pass

        parent_escape = escape_target.exists()
        if parent_escape:
            try:
                os.chmod(outside, 0o755)
                escape_target.unlink(missing_ok=True)
            except OSError:
                pass

        fixture = run.get("fixture_result") or {}
        host_private_read = bool(fixture.get("host_private_read"))
        outside_write = bool(fixture.get("outside_write")) or parent_escape
        network_reach = bool(fixture.get("network_reach"))
        child_spawn = bool(fixture.get("child_spawn"))
        privileged = bool(fixture.get("privileged_capability"))
        cross_app_read = bool(fixture.get("cross_app_read"))

        host_blocked = not host_private_read
        outside_blocked = not outside_write
        network_denied = not network_reach
        child_denied = not child_spawn
        priv_denied = not privileged
        cross_blocked = not cross_app_read

        # Vacuous "blocked" flags when the fixture never ran must not count as probes_pass.
        fixture_ran = bool(fixture) and "host_private_read" in fixture
        probes_pass = fixture_ran and all(
            [host_blocked, outside_blocked, network_denied, child_denied, priv_denied, cross_blocked]
        )
        genuine = backend in {"bubblewrap", "sandbox_exec"}
        # Regression: host read success + outside write fail MUST fail validation
        regression_fail = host_private_read and outside_blocked

        if backend == "subprocess_broker" or not genuine:
            validated = False
            local_status = "BLOCKED_ENVIRONMENT"
            classification_hint = "BLOCKED_ENVIRONMENT"
        elif regression_fail or not probes_pass or not network_control_reachable:
            validated = False
            local_status = "PROBE_FAILURE"
            classification_hint = "IMPLEMENTATION_OPEN"
        else:
            validated = True
            local_status = "VALIDATED"
            classification_hint = "IMPLEMENTED_AND_VALIDATED"

        kernel = backend == "bubblewrap" and validated

        result = {
            "ok": validated,
            "app_id": app_id,
            "SANDBOX_BACKEND": backend,
            "KERNEL_SANDBOX": kernel,
            "PLAIN_SUBPROCESS_COUNTS_AS_SANDBOX": False,
            "HOST_PRIVATE_READ_BLOCKED": host_blocked,
            "OUTSIDE_WRITE_BLOCKED": outside_blocked,
            "NETWORK_DENIED": network_denied,
            "NETWORK_CONTROL_REACHABLE": network_control_reachable,
            "CHILD_SPAWN_DENIED": child_denied,
            "CROSS_APP_READ_BLOCKED": cross_blocked,
            "PRIVILEGED_CAPABILITY_DENIED": priv_denied,
            "SANDBOX_EXECUTION_VALIDATED": validated,
            "LOCAL_SANDBOX_VALIDATION": local_status,
            "classification_hint": classification_hint,
            "execution_enforced": genuine and validated,
            "fixture_result": fixture,
            "parent_escape_detected": parent_escape,
            "stderr_tail": run.get("stderr_tail", ""),
            "stdout_tail": run.get("stdout_tail", ""),
            "exit_code": run.get("exit_code"),
            "fixture_ran": fixture_ran,
            "claim_boundary": CLAIM_BOUNDARY,
            "backend": backend,
            "kernel_sandbox": kernel,
        }
        self._audit("run_enforcement_suite", result)
        try:
            os.chmod(outside, 0o755)
            shutil.rmtree(work_root, ignore_errors=True)
        except OSError:
            pass
        return result

    def execute_untrusted(
        self,
        app_id: str,
        *,
        app_class: str = "untrusted",
        script: str | None = None,
        timeout: float = 15.0,
    ) -> dict[str, Any]:
        """Back-compat entrypoint — delegates to enforcement suite (script ignored for validation)."""
        _ = (app_class, script)
        return self.run_enforcement_suite(app_id=app_id, timeout=timeout)

    def status(self) -> dict[str, Any]:
        if self.bwrap:
            backend = "bubblewrap"
        elif self.sandbox_exec:
            backend = "sandbox_exec"
        else:
            backend = "subprocess_broker"
        return {
            "backend_available": backend,
            "genuine_backend_available": self.genuine_backend_available,
            "kernel_sandbox": self.kernel_sandbox,
            "PLAIN_SUBPROCESS_COUNTS_AS_SANDBOX": False,
            "audit_len": len(self.audit),
            "claim_boundary": CLAIM_BOUNDARY,
        }
