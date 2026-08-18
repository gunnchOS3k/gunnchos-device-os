#!/usr/bin/env python3
"""Checksum digital container/VM *sources* — not a shipping OS image."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FILES = [
    "os_build/linux_desktop/Dockerfile",
    "os_build/linux_desktop/docker-compose.yml",
    "os_build/linux_desktop/entrypoint.sh",
    "os_build/linux_desktop/nginx.conf",
    ".devcontainer/devcontainer.json",
    "os_build/reproducible_system_image/artifacts/CHECKSUMS.json",
    "os_build/reproducible_system_image/notes/VM_EMULATION.md",
]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def main() -> int:
    rows = []
    for rel in FILES:
        path = ROOT / rel
        if not path.exists():
            rows.append({"path": rel, "present": False})
            continue
        rows.append(
            {
                "path": rel,
                "present": True,
                "sha256": sha256_file(path),
                "bytes": path.stat().st_size,
            }
        )
    payload = {
        "schema": "gunnchos.digital_container_vm_checksums.v1",
        "shipping_os": False,
        "physical_boot": False,
        "note": (
            "Hashes of prototype container/devcontainer/digital-bundle sources. "
            "Docker :8080 serves launcher_mock. QEMU bootable-reference is DEV/VM "
            "evidence only (make bootable-reference)."
        ),
        "files": rows,
    }
    out = ROOT / "artifacts" / "supervisor_ready"
    out.mkdir(parents=True, exist_ok=True)
    dest = out / "DIGITAL_CONTAINER_VM_CHECKSUMS.json"
    dest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote={dest}")
    missing = [r["path"] for r in rows if not r.get("present")]
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
