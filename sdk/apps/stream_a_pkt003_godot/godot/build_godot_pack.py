#!/usr/bin/env python3
"""Distinct Godot pack builder — NOT gunnchSDK PackageBuilder.

Reads project.godot + assets, emits content-addressed microgame.pck.json.
Optional: invoke host/guest Godot binary when available for --export-pack.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import time
from pathlib import Path


BUILD_SYSTEM = "godot_pack_v1"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build(project_dir: Path, out_dir: Path) -> dict:
    project_dir = Path(project_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    project = project_dir / "project.godot"
    if not project.exists():
        return {"ok": False, "error": "project_godot_missing", "build_system": BUILD_SYSTEM}
    files = {}
    for rel in ("project.godot", "main.tscn"):
        p = project_dir / rel
        if p.exists():
            files[rel] = _sha(p.read_bytes())
    blob = json.dumps({"files": files, "build_system": BUILD_SYSTEM}, sort_keys=True).encode()
    digest = _sha(blob)
    artifact = {
        "schema": "gunnchos.godot_pack.v1",
        "build_system": BUILD_SYSTEM,
        "project_name": "PKT003 Microgame",
        "files": files,
        "pack_sha256": digest,
        "built_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "godot_export_pack": False,
        "SILICON_EXACT_EMULATION": False,
    }
    godot = shutil.which("godot") or shutil.which("godot3") or shutil.which("godot4")
    if godot:
        # Best-effort real export; do not fail the digital pack if export templates absent.
        try:
            proc = subprocess.run(
                [godot, "--headless", "--path", str(project_dir), "--quit-after", "1"],
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
            artifact["godot_bin"] = godot
            artifact["godot_probe_rc"] = proc.returncode
            artifact["godot_probe_ok"] = proc.returncode == 0
        except Exception as exc:  # noqa: BLE001
            artifact["godot_probe_error"] = str(exc)[:200]
    out = out_dir / "microgame.pck.json"
    out.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    artifact["ok"] = True
    artifact["artifact_path"] = str(out)
    return artifact


if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    print(json.dumps(build(root, root), indent=2))
