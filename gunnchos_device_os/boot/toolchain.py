"""Offline build/test path and optional QEMU/container smoke assessment."""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any


def assess_toolchain(repo_root: Path | str | None = None) -> dict[str, Any]:
    root = Path(repo_root) if repo_root else Path.cwd()
    docker = shutil.which("docker")
    qemu = shutil.which("qemu-system-x86_64") or shutil.which("qemu-system-aarch64")
    compose_file = root / "os_build" / "linux_desktop" / "docker-compose.yml"
    image_dockerfile = root / "os_build" / "image_prototype" / "Dockerfile"

    container_smoke = {
        "supported_in_repo": compose_file.exists() or image_dockerfile.exists(),
        "docker_available": bool(docker),
        "compose_path": str(compose_file) if compose_file.exists() else None,
        "status": "available" if docker and compose_file.exists() else "skipped",
        "note": (
            "Optional container smoke uses existing os_build Docker paths; "
            "not invoked by default offline tests."
        ),
    }

    qemu_smoke = {
        "qemu_binary": qemu,
        "full_system_image": False,
        "status": "BLOCKED_TOOLCHAIN",
        "note": (
            "Repo documents container prototypes but does not ship a QEMU full-system "
            "boot image or automated QEMU smoke harness. Treat QEMU boot smoke as "
            "BLOCKED_TOOLCHAIN until an image + script land."
        ),
    }

    offline = {
        "pytest": True,
        "deps": ["pytest>=7.0"],
        "large_downloads_required": False,
        "command": "PYTHONPATH=.:src pytest -q tests/test_gate1_boot_probe.py tests/test_gate1_dock_continuity.py tests/test_gate1_identity.py",
    }

    return {
        "offline_software_path": True,
        "offline": offline,
        "container_smoke": container_smoke,
        "qemu_smoke": qemu_smoke,
        "blocker_tokens": ["BLOCKED_TOOLCHAIN"] if qemu_smoke["status"] == "BLOCKED_TOOLCHAIN" else [],
    }
