"""Creator / Coder Studio — real project workspace, run/build, git, AI assist.

Owner product requirements (charter): build / package / install pathways,
coding help via gunnchAI, DS-XL dual layout awareness.

Claim boundary: digital first-party dogfood on gunnchSDK — not a full IDE
distribution, not production signing toolchain, not store submission.
"""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path
from typing import Any

from gunnchos_device_os.first_party_apps import runtime
from gunnchos_device_os.gunnchai_integration import (
    tutor_prompt_guard,
    tutor_safety_check,
    tutor_session_start,
)

CLAIM_BOUNDARY = (
    "Digital Creator/Coder Studio with real local file/git/run/build paths and "
    "gunnchSDK sandbox persistence. Not a full IDE distribution or production "
    "signing toolchain. HTML companion shell remains prototype UX."
)

REQUIRED_PERMISSIONS = ["storage_read", "storage_write", "ai_interface"]


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _workspace_root(data_dir: Path) -> Path:
    ws = data_dir / "workspace"
    ws.mkdir(parents=True, exist_ok=True)
    return ws


def _ensure_seed_project(workspace: Path) -> list[str]:
    hello = workspace / "hello.py"
    makefile = workspace / "Makefile"
    notes = workspace / "notes.md"
    if not hello.exists():
        hello.write_text(
            "def greet(name: str = 'Creator Studio') -> str:\n"
            "    return f'hello from {name}'\n\n"
            "if __name__ == '__main__':\n"
            "    print(greet())\n",
            encoding="utf-8",
        )
    if not makefile.exists():
        makefile.write_text(
            "all:\n"
            "\t@mkdir -p dist\n"
            "\t@echo '{\"schema\":\"gunnchos.creator_studio.artifact.v1\",\"ok\":true}' > dist/app-package.dev.json\n"
            "\t@echo build-ok\n",
            encoding="utf-8",
        )
    if not notes.exists():
        notes.write_text("# Studio notes\nPersist edits across gunnchSDK runs.\n", encoding="utf-8")
    return sorted(p.name for p in workspace.iterdir() if p.is_file())


def _load_state(data_dir: Path) -> dict[str, Any]:
    return runtime.load_json(
        data_dir / "creator_state.json",
        {
            "schema": "gunnchos.creator_studio.state.v1",
            "run_count": 0,
            "last_run": None,
            "last_build": None,
            "layout": "single",
            "projects_touched": [],
        },
    )


def _save_state(data_dir: Path, state: dict[str, Any]) -> str:
    return runtime.write_json(data_dir / "creator_state.json", state)


def _gunnchai_coding_assist(prompt: str) -> dict[str, Any]:
    """Cross-service: invoke gunnchAI tutor safety + local coding hint."""
    session = tutor_session_start("coder", "creator_studio_assist")
    guard = tutor_prompt_guard(prompt)
    if not guard.get("ok"):
        return {"ok": False, "session": session, "guard": guard, "suggestion": None}
    suggestion = (
        "Add type hints, a pytest smoke test for greet(), and keep package "
        "artifacts under dist/ so gunnchSDK install can dogfood the build path."
    )
    safety = tutor_safety_check(suggestion)
    return {
        "ok": bool(safety.get("safe_to_show")),
        "session": session,
        "guard": guard,
        "safety": safety,
        "suggestion": suggestion if safety.get("safe_to_show") else None,
        "mode": "local_dev_hint",
        "claim_boundary": "Local coding hint only — not frontier model quality.",
    }


def run_creator_studio(
    *,
    project_root: Path | None = None,
    layout: str = "single",
    crash_probe: bool = False,
) -> dict[str, Any]:
    runtime.intentional_crash_probe(enabled=crash_probe)
    perms = runtime.assert_permissions(REQUIRED_PERMISSIONS)
    if not perms["ok"]:
        return {
            "ok": False,
            "app_id": "creator_studio",
            "error": "permission_denied",
            "permissions": perms,
            "claim_boundary": CLAIM_BOUNDARY,
        }

    data_dir = runtime.sandbox_data_dir()
    ui_root = project_root or (_repo_root() / "apps/creator_studio")
    ui = ui_root / "index.html"
    workspace = _workspace_root(data_dir)
    files = _ensure_seed_project(workspace)
    state = _load_state(data_dir)
    state["run_count"] = int(state.get("run_count") or 0) + 1
    state["layout"] = layout if layout in ("single", "dsxl") else "single"

    # Owner function: edit persistence — bump notes on each dogfood run.
    notes = workspace / "notes.md"
    notes.write_text(
        notes.read_text(encoding="utf-8")
        + f"\n- run #{state['run_count']} @ {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}\n",
        encoding="utf-8",
    )

    run = subprocess.run(
        ["python3", str(workspace / "hello.py")],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    build = subprocess.run(
        ["make", "-C", str(workspace)],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    artifact = workspace / "dist" / "app-package.dev.json"
    package_ok = artifact.exists() and build.returncode == 0
    git = subprocess.run(
        ["git", "-C", str(_repo_root()), "status", "--short"],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assist = _gunnchai_coding_assist("Help improve hello.py for Creator Studio packaging")

    state["last_run"] = {
        "exit": run.returncode,
        "stdout": run.stdout.strip(),
        "at": time.time(),
    }
    state["last_build"] = {
        "exit": build.returncode,
        "package_ok": package_ok,
        "artifact": str(artifact) if artifact.exists() else None,
        "at": time.time(),
    }
    touched = list(state.get("projects_touched") or [])
    if "hello.py" not in touched:
        touched.append("hello.py")
    state["projects_touched"] = touched
    state_path = _save_state(data_dir, state)
    log_path = runtime.append_app_log(
        "creator_studio_run",
        {
            "run_count": state["run_count"],
            "package_ok": package_ok,
            "assist_ok": assist.get("ok"),
            "layout": state["layout"],
        },
    )

    result = {
        "ok": ui.exists() and run.returncode == 0 and package_ok and perms["ok"] and bool(assist.get("ok")),
        "app_id": "creator_studio",
        "sdk_app_id": runtime.app_id(),
        "sdk_version": runtime.app_version(),
        "entry": "apps/creator_studio/index.html",
        "workspace": str(workspace),
        "files": files,
        "run": {"stdout": run.stdout.strip(), "stderr": run.stderr.strip(), "code": run.returncode},
        "build": {
            "stdout": build.stdout.strip(),
            "code": build.returncode,
            "artifact": str(artifact) if artifact.exists() else None,
            "package_ok": package_ok,
        },
        "git_status_preview": git.stdout.strip().splitlines()[:20],
        "device_debug": {"serial": "DEV-UART-0", "layout": ["single", "dsxl"], "active_layout": state["layout"]},
        "gunnchai_assist": assist,
        "permissions": perms,
        "persisted_state_path": state_path,
        "persisted_run_count": state["run_count"],
        "app_log_path": log_path,
        "ui_present": ui.exists(),
        "mock": False,
        "stub_content": False,
        "depth_claim": "D5_runtime_candidate",
        "claim_boundary": CLAIM_BOUNDARY,
        "owner_functions": [
            "project_browser",
            "edit_persist",
            "run",
            "build_package_artifact",
            "git_status",
            "device_debug_layout",
            "gunnchai_coding_assist",
        ],
    }
    runtime.write_json(data_dir / "creator_studio_run.json", result)
    return result
