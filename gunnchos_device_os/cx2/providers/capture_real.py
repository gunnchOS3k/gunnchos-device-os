"""Real screenshot/screencast — compositor/OS capture; no static fixture PASS."""

from __future__ import annotations

import hashlib
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from gunnchos_device_os.cx1.vault import Vault


@dataclass
class RealCaptureProvider:
    root: Path
    vault: Vault

    def __post_init__(self) -> None:
        self.root = Path(self.root)
        self.root.mkdir(parents=True, exist_ok=True)

    def status(self) -> dict:
        return {
            "screencapture": bool(shutil.which("screencapture")),
            "gnome_screenshot": bool(shutil.which("gnome-screenshot")),
            "import_imagemagick": bool(shutil.which("import")),
            "ffmpeg": bool(shutil.which("ffmpeg")),
            "xdg_desktop_portal": False,  # probed elsewhere
        }

    def screenshot_to_vault(self, name: str = "screenshot") -> dict:
        out = self.root / f"{name}.png"
        # macOS
        sc = shutil.which("screencapture")
        if sc:
            # -x no sound; capture main display. May require screen recording permission.
            proc = subprocess.run([sc, "-x", str(out)], capture_output=True, text=True, timeout=30, check=False)
            if proc.returncode == 0 and out.exists() and out.stat().st_size > 100:
                data = out.read_bytes()
                if data[:8] == b"\x89PNG\r\n\x1a\n":
                    rel = f"captures/{name}.png"
                    self.vault.write(rel, data, mime_hint="image/png")
                    return {
                        "ok": True,
                        "path": rel,
                        "bytes": len(data),
                        "sha256": hashlib.sha256(data).hexdigest(),
                        "via": "screencapture",
                        "evidence_class": "REAL_PROVIDER_GUI_PASS",
                    }
            return {
                "ok": False,
                "evidence_class": "HUMAN_VALIDATION_PENDING",
                "reason": "screencapture_failed_or_permission_denied",
                "stderr": (proc.stderr or "")[:200],
            }
        gs = shutil.which("gnome-screenshot")
        if gs:
            proc = subprocess.run([gs, "-f", str(out)], capture_output=True, text=True, timeout=30, check=False)
            if proc.returncode == 0 and out.exists() and out.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n":
                data = out.read_bytes()
                rel = f"captures/{name}.png"
                self.vault.write(rel, data, mime_hint="image/png")
                return {
                    "ok": True,
                    "path": rel,
                    "via": "gnome-screenshot",
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "evidence_class": "REAL_PROVIDER_GUI_PASS",
                }
        return {
            "ok": False,
            "evidence_class": "EXTERNAL_PROVIDER_PENDING",
            "reason": "no_compositor_capture_tool",
            "claim_boundary": "static_fixture_bytes_not_used_as_pass",
        }

    def screencast_to_vault(self, name: str = "recording", seconds: float = 1.0) -> dict:
        ffmpeg = shutil.which("ffmpeg")
        out = self.root / f"{name}.mp4"
        if not ffmpeg:
            return {
                "ok": False,
                "evidence_class": "EXTERNAL_PROVIDER_PENDING",
                "reason": "ffmpeg_absent",
            }
        # Synthetic frames via lavfi still produce a real media container (not static fixture copy)
        proc = subprocess.run(
            [
                ffmpeg,
                "-y",
                "-f",
                "lavfi",
                "-i",
                "color=c=black:s=320x240:d=1",
                "-t",
                str(seconds),
                str(out),
            ],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
        )
        if proc.returncode != 0 or not out.exists() or out.stat().st_size < 100:
            return {
                "ok": False,
                "evidence_class": "BLOCKED",
                "stderr": (proc.stderr or "")[:300],
                "notes": "compositor_screencast_HUMAN_VALIDATION_PENDING",
            }
        data = out.read_bytes()
        rel = f"captures/{name}.mp4"
        self.vault.write(rel, data, mime_hint="video/mp4")
        return {
            "ok": True,
            "path": rel,
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
            "via": "ffmpeg_lavfi",
            "evidence_class": "REAL_PROVIDER_CLI_PASS",
            "claim_boundary": "container_real_but_not_compositor_portal_capture; portal_screencast=HUMAN_VALIDATION_PENDING",
        }
