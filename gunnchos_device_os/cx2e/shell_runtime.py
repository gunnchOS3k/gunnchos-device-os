"""ShellRuntimeTarget v1 — production gunnch_shell launch contract."""

from __future__ import annotations

import hashlib
import json
import subprocess
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass
class ShellRuntimeTarget:
    """Immutable production shell launch target (not Vite dev server)."""

    schema: str = "gunnchos.cx2e.shell_runtime_target.v1"
    source_sha: str = ""
    build_hash: str = ""
    arch: str = "aarch64"
    guest_os: str = "debian-12-bookworm"
    renderer: str = "chromium-app-mode"
    launch_cmd: str = ""
    content_origin: str = "file:///opt/cx2e/gunnch_shell/index.html"
    compositor: str = "weston"
    display_socket: str = "/run/cx2e-wayland/wayland-0"
    dbus_session: str = "unix:path=/run/cx2e-wayland/bus"
    a11y_bus: str = "at-spi-bus"
    device_profile: str = "ci_qemu_linux_graphical"
    production_assets_dir: str = "/opt/cx2e/gunnch_shell"
    notes: str = (
        "Vite dev server is NOT production. Chromium --app=file://... is an "
        "allowed ShellRuntimeTarget provider for local signed/built assets only."
    )
    extras: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return d


def sha256_dir_files(root: Path) -> str:
    h = hashlib.sha256()
    if not root.is_dir():
        return ""
    for path in sorted(root.rglob("*")):
        if path.is_file():
            h.update(str(path.relative_to(root)).encode())
            h.update(path.read_bytes())
    return h.hexdigest()


def build_production_shell(repo: Path, out_dir: Path) -> Dict[str, Any]:
    """Build immutable production assets from apps/gunnch_shell."""
    shell = repo / "apps" / "gunnch_shell"
    result: Dict[str, Any] = {
        "ok": False,
        "shell_dir": str(shell),
        "out_dir": str(out_dir),
        "blocker": None,
    }
    if not (shell / "package.json").is_file():
        result["blocker"] = "CX2E_GUNNCH_SHELL_MISSING"
        return result
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        head = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=repo, text=True
        ).strip()
    except Exception:
        head = "unknown"
    npm = subprocess.run(
        ["npm", "ci"],
        cwd=shell,
        capture_output=True,
        text=True,
        timeout=600,
    )
    if npm.returncode != 0:
        # fallback to npm install if lock-only ci fails in sparse trees
        npm = subprocess.run(
            ["npm", "install"],
            cwd=shell,
            capture_output=True,
            text=True,
            timeout=600,
        )
    build = subprocess.run(
        ["npm", "run", "build"],
        cwd=shell,
        capture_output=True,
        text=True,
        timeout=300,
    )
    dist = shell / "dist"
    if build.returncode != 0 or not (dist / "index.html").is_file():
        result["blocker"] = f"CX2E_SHELL_BUILD_FAILED: {build.stderr[-800:]}"
        result["build_stdout"] = build.stdout[-800:]
        return result
    # Copy dist into lab staging
    import shutil

    staged = out_dir / "gunnch_shell"
    if staged.exists():
        shutil.rmtree(staged)
    shutil.copytree(dist, staged)
    build_hash = sha256_dir_files(staged)
    target = ShellRuntimeTarget(
        source_sha=head,
        build_hash=build_hash,
        launch_cmd=(
            "chromium --no-sandbox --disable-gpu-sandbox "
            f"--user-data-dir=/var/lib/cx2e/chromium-shell "
            f"--app=file://{staged.as_posix()}/index.html"
        ).replace(str(staged), "/opt/cx2e/gunnch_shell"),
        content_origin="file:///opt/cx2e/gunnch_shell/index.html",
        production_assets_dir="/opt/cx2e/gunnch_shell",
        extras={
            "built_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "host_staged_dir": str(staged),
            "npm_ci_rc": npm.returncode,
            "build_rc": build.returncode,
        },
    )
    (out_dir / "SHELL_RUNTIME_TARGET.json").write_text(
        json.dumps(target.to_dict(), indent=2) + "\n"
    )
    result["ok"] = True
    result["target"] = target.to_dict()
    result["build_hash"] = build_hash
    result["source_sha"] = head
    return result
