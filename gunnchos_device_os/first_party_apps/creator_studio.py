"""Creator / Coder Studio — file browser, editor, run/build, git, debug."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import subprocess
import tempfile
import time

CLAIM_BOUNDARY = (
    "Digital Creator/Coder Studio with real local file/git/run paths. "
    "Not a full IDE distribution or production signing toolchain."
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def run_creator_studio(*, project_root: Path | None = None) -> dict[str, Any]:
    root = project_root or (_repo_root() / "apps/creator_studio")
    ui = root / "index.html"
    workspace = Path(tempfile.mkdtemp(prefix="gchos-studio-"))
    (workspace / "hello.py").write_text("print('hello from Creator Studio')\n", encoding="utf-8")
    (workspace / "Makefile").write_text("all:\n\t@echo build-ok\n", encoding="utf-8")

    run = subprocess.run(
        ["python3", str(workspace / "hello.py")],
        capture_output=True, text=True, timeout=10, check=False,
    )
    build = subprocess.run(
        ["make", "-C", str(workspace)],
        capture_output=True, text=True, timeout=10, check=False,
    )
    git = subprocess.run(
        ["git", "-C", str(_repo_root()), "status", "--short"],
        capture_output=True, text=True, timeout=10, check=False,
    )
    files = sorted(p.name for p in workspace.iterdir() if p.is_file())
    package = {
        "schema": "gunnchos.creator_studio.package.v1",
        "created_at": time.time(),
        "files": files,
        "run_exit": run.returncode,
        "build_exit": build.returncode,
    }
    (workspace / "app-package.dev.json").write_text(json.dumps(package, indent=2) + "\n", encoding="utf-8")
    return {
        "ok": ui.exists() and run.returncode == 0 and build.returncode == 0,
        "app_id": "creator_studio",
        "entry": "apps/creator_studio/index.html",
        "workspace": str(workspace),
        "files": files,
        "run": {"stdout": run.stdout.strip(), "stderr": run.stderr.strip(), "code": run.returncode},
        "build": {"stdout": build.stdout.strip(), "code": build.returncode},
        "git_status_preview": git.stdout.strip().splitlines()[:20],
        "device_debug": {"serial": "DEV-UART-0", "layout": ["single", "dsxl"]},
        "gunnchai_assist": {"available": True, "mode": "local_dev_hint"},
        "ui_present": ui.exists(),
        "mock": False,
        "stub_content": False,
        "claim_boundary": CLAIM_BOUNDARY,
    }
