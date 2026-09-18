"""ShellRuntimeTarget v1 for CX2F — loopback HTTP asset delivery."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict


@dataclass
class ShellRuntimeTarget:
    schema: str = "gunnchos.cx2f.shell_runtime_target.v1"
    source_sha: str = ""
    build_hash: str = ""
    arch: str = "aarch64"
    guest_os: str = "debian-12-bookworm"
    renderer: str = "chromium-app-mode-wayland"
    asset_server_implementation: str = "python3 -m http.server (loopback-only; replaceable)"
    content_origin: str = "http://127.0.0.1:8765/"
    production_assets_dir: str = ""
    launch_cmd: str = ""
    compositor: str = "weston"
    display_socket: str = "/run/cx2f-wayland/wayland-0"
    dbus_session: str = "unix:path=/run/cx2f-wayland/bus"
    ozone_platform: str = "wayland"
    chromium_profile: str = "/var/lib/cx2f/chromium-shell"
    remote_debugging: str = "127.0.0.1:9222"
    rendering_proof_method: str = "qemu_hmp_screendump_ppm + framebuffer_diff + atspi/dom"
    notes: str = (
        "Immutable production build served via loopback static HTTP. "
        "Vite dev server is NOT production. file:// absolute /assets/ is invalid."
    )
    extras: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


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
    shell = repo / "apps" / "gunnch_shell"
    result: Dict[str, Any] = {"ok": False, "shell_dir": str(shell), "blocker": None}
    if not (shell / "package.json").is_file():
        result["blocker"] = "CX2F_GUNNCH_SHELL_MISSING"
        return result
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    except Exception:
        head = "unknown"
    npm = subprocess.run(["npm", "ci"], cwd=shell, capture_output=True, text=True, timeout=600)
    if npm.returncode != 0:
        npm = subprocess.run(["npm", "install"], cwd=shell, capture_output=True, text=True, timeout=600)
    build = subprocess.run(["npm", "run", "build"], cwd=shell, capture_output=True, text=True, timeout=300)
    dist = shell / "dist"
    if build.returncode != 0 or not (dist / "index.html").is_file():
        result["blocker"] = f"CX2F_SHELL_BUILD_FAILED: {(build.stderr or '')[-800:]}"
        return result
    index = (dist / "index.html").read_text()
    absolute_assets = 'src="/assets/' in index or 'href="/assets/' in index
    build_hash = sha256_dir_files(dist)
    staged = out_dir / "gunnch_shell" / build_hash
    if staged.exists():
        shutil.rmtree(staged)
    staged.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(dist, staged)
    guest_dir = f"/opt/gunnchos/gunnch_shell/{build_hash}"
    origin = "http://127.0.0.1:8765/"
    target = ShellRuntimeTarget(
        source_sha=head,
        build_hash=build_hash,
        content_origin=origin,
        production_assets_dir=guest_dir,
        launch_cmd=(
            "chromium --ozone-platform=wayland --enable-features=UseOzonePlatform "
            "--user-data-dir=/var/lib/cx2f/chromium-shell "
            "--remote-debugging-address=127.0.0.1 --remote-debugging-port=9222 "
            "--no-first-run --disable-extensions "
            f"--app={origin}"
        ),
        extras={
            "built_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "host_staged_dir": str(staged),
            "absolute_assets_detected": absolute_assets,
            "asset_delivery": "loopback_http_static",
            "npm_ci_rc": npm.returncode,
            "build_rc": build.returncode,
            "sandbox_note": "May add --no-sandbox only if guest constraint requires; prefer sandbox on",
        },
    )
    (out_dir / "SHELL_RUNTIME_TARGET.json").write_text(json.dumps(target.to_dict(), indent=2) + "\n")
    result["ok"] = True
    result["target"] = target.to_dict()
    result["build_hash"] = build_hash
    result["absolute_assets"] = absolute_assets
    result["staged"] = str(staged)
    return result
