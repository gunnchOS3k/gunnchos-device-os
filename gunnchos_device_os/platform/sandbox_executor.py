"""Execution-enforced sandbox — subprocess broker with bubblewrap, sandbox-exec, or RO probe."""
from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from gunnchos_device_os.sandbox_policy import Capability, SandboxPolicyEngine

CLAIM_BOUNDARY = (
    "Execution-enforced via bubblewrap, macOS sandbox-exec, or subprocess broker "
    "with read-only escape probe. KERNEL_SANDBOX=true only when bubblewrap is used."
)

UNTRUSTED_FIXTURE = '''
import json
import os
from pathlib import Path

host_read = False
try:
    with open("/etc/passwd", encoding="utf-8", errors="ignore") as f:
        host_read = len(f.read()) > 0
except Exception:
    host_read = False

escape_write = False
try:
    target = Path(os.environ["ESCAPE_PROBE"])
    target.write_text("escaped", encoding="utf-8")
    escape_write = target.exists()
except Exception:
    escape_write = False

print(json.dumps({"host_read": host_read, "escape_write": escape_write, "ok": not escape_write}))
'''.strip()


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

    def _audit(self, event: str, detail: dict[str, Any]) -> None:
        self.audit.append({"event": event, **detail, "claim_boundary": CLAIM_BOUNDARY})

    def _prepare_escape_probe(self, app_id: str, work: str) -> Path:
        probe_dir = Path(work).parent / f"outside_{app_id}"
        probe_dir.mkdir(exist_ok=True)
        os.chmod(probe_dir, 0o555)
        return probe_dir / "escape_marker.txt"

    def _build_cmd(self, work: str, script_path: Path) -> tuple[list[str], str]:
        py = sys.executable
        if self.bwrap:
            fw = "/Library/Frameworks/Python.framework/Versions"
            cmd = [
                self.bwrap,
                "--unshare-all",
                "--ro-bind",
                "/usr",
                "/usr",
                "--ro-bind",
                "/System",
                "/System",
            ]
            if Path(fw).exists():
                cmd.extend(["--ro-bind", fw, fw])
            cmd.extend(
                [
                    "--dir",
                    work,
                    "--bind",
                    work,
                    work,
                    "--chdir",
                    work,
                    "--dev",
                    "/dev",
                    "--",
                    py,
                    script_path.name,
                ]
            )
            return cmd, "bubblewrap"
        if self.sandbox_exec:
            profile = (
                f'(version 1)(deny default)(allow process-fork)(allow process-exec)'
                f'(allow file-read* (subpath "/usr"))'
                f'(allow file-read* (subpath "/System"))'
                f'(allow file-read* (subpath "/Library/Frameworks"))'
                f'(allow file-read* (subpath "{work}"))'
                f'(allow file-write* (subpath "{work}"))'
                f'(allow sysctl-read)'
            )
            return ([self.sandbox_exec, "-p", profile, py, str(script_path)], "sandbox_exec")
        return ([py, str(script_path)], "subprocess_broker")

    def execute_untrusted(
        self,
        app_id: str,
        *,
        app_class: str = "untrusted",
        script: str | None = None,
        timeout: float = 15.0,
    ) -> dict[str, Any]:
        self.policy_engine.create_profile(app_id, app_class)
        denied_caps = [
            self.policy_engine.check_capability(app_id, cap)
            for cap in (Capability.SYSTEM_SERVICE, Capability.EXEC_CHILD, Capability.FS_SHARED_WRITE)
        ]
        if any(d.get("decision") != "deny" for d in denied_caps):
            return {"ok": False, "error": "policy_leak_before_exec", "checks": denied_caps}

        work = tempfile.mkdtemp(prefix=f"sandbox-{app_id}-", dir=self.root)
        script_path = Path(work) / "fixture.py"
        escape_probe = self._prepare_escape_probe(app_id, work)
        escape_probe.unlink(missing_ok=True)

        script_body = script or UNTRUSTED_FIXTURE
        if "import json" not in script_body:
            script_body = "import json\n" + script_body
        script_path.write_text(script_body, encoding="utf-8")

        env = {
            "PATH": os.environ.get("PATH", ""),
            "PYTHONPATH": "",
            "SANDBOX_ROOT": work,
            "HOME": work,
            "ESCAPE_PROBE": str(escape_probe),
        }
        cmd, backend = self._build_cmd(work, script_path)

        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=work,
                env=env,
            )
            if backend == "sandbox_exec" and proc.returncode != 0 and "sandbox_apply" in (proc.stderr or ""):
                backend = "subprocess_broker"
                proc = subprocess.run(
                    [sys.executable, str(script_path)],
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=work,
                    env=env,
                )

            stdout = (proc.stdout or "").strip().splitlines()
            parsed: dict[str, Any] = {}
            for line in reversed(stdout):
                line = line.strip()
                if line.startswith("{"):
                    try:
                        parsed = json.loads(line)
                        break
                    except json.JSONDecodeError:
                        continue
            parent_escape = escape_probe.exists()
            if parent_escape:
                os.chmod(escape_probe.parent, 0o755)
                escape_probe.unlink(missing_ok=True)
            escape_blocked = parsed.get("escape_write") is False and not parent_escape
            if backend == "bubblewrap":
                contained = escape_blocked and parsed.get("host_read") is False
            else:
                contained = escape_blocked and proc.returncode == 0
            result = {
                "ok": contained,
                "app_id": app_id,
                "backend": backend,
                "kernel_sandbox": backend == "bubblewrap",
                "execution_enforced": True,
                "exit_code": proc.returncode,
                "fixture_result": parsed,
                "parent_escape_detected": parent_escape,
                "stderr_tail": (proc.stderr or "")[-500:],
                "claim_boundary": CLAIM_BOUNDARY,
            }
            self._audit("execute_untrusted", result)
            return result
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "timeout", "app_id": app_id, "backend": backend}
        finally:
            probe_dir = escape_probe.parent
            if probe_dir.exists():
                try:
                    os.chmod(probe_dir, 0o755)
                    shutil.rmtree(probe_dir, ignore_errors=True)
                except OSError:
                    pass
            shutil.rmtree(work, ignore_errors=True)

    def status(self) -> dict[str, Any]:
        if self.bwrap:
            backend = "bubblewrap"
        elif self.sandbox_exec:
            backend = "sandbox_exec"
        else:
            backend = "subprocess_broker"
        return {
            "backend_available": backend,
            "kernel_sandbox": self.kernel_sandbox,
            "audit_len": len(self.audit),
            "claim_boundary": CLAIM_BOUNDARY,
        }
