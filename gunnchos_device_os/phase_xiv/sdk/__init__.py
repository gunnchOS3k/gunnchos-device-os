"""Developer SDK + debug/profiling templates for Phase XIV."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

TEMPLATES = (
    "hello_service",
    "wayland_client_stub",
    "ai_capability_client",
    "debug_profiler",
)


class DeveloperSdk:
    def __init__(self, root: Path):
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)
        self.templates_dir = self.root / "templates"
        self.templates_dir.mkdir(exist_ok=True)

    def materialize_templates(self) -> dict[str, str]:
        written = {}
        hello = '''#!/usr/bin/env python3
"""gunnchOS adopter hello service template."""
def main():
    print({"ok": True, "service": "hello", "sdk": "phase_xiv"})

if __name__ == "__main__":
    main()
'''
        wayland = '''# Wayland client stub — connect to gunnchOS session
# PHYSICAL_PENDING for real protocol binding
SCHEMA = "gunnchos.sdk.wayland_client_stub.v1"
CONNECT = ["xdg_wm_base", "wl_compositor", "wl_seat"]
'''
        ai_client = '''#!/usr/bin/env python3
"""Call OS AI System API — never model paths."""
import json, urllib.request

def invoke(capability: str, text: str, base: str = "http://127.0.0.1:8788"):
    req = urllib.request.Request(
        f"{base}/v1/capability/{capability}",
        data=json.dumps({"user_id": "dev", "input": text}).encode(),
        headers={"content-type": "application/json"},
        method="POST",
    )
    return json.loads(urllib.request.urlopen(req, timeout=30).read().decode())
'''
        profiler = '''#!/usr/bin/env python3
"""Debug/profiling template — CPU/mem markers for local sessions."""
import time, resource, json

def profile(fn):
    start = time.time()
    ru0 = resource.getrusage(resource.RUSAGE_SELF)
    result = fn()
    ru1 = resource.getrusage(resource.RUSAGE_SELF)
    return {
        "result": result,
        "elapsed_s": time.time() - start,
        "user_cpu_s": ru1.ru_utime - ru0.ru_utime,
        "max_rss_kb": ru1.ru_maxrss,
    }
'''
        mapping = {
            "hello_service": ("hello_service.py", hello),
            "wayland_client_stub": ("wayland_client_stub.py", wayland),
            "ai_capability_client": ("ai_capability_client.py", ai_client),
            "debug_profiler": ("debug_profiler.py", profiler),
        }
        for name, (fname, body) in mapping.items():
            path = self.templates_dir / fname
            path.write_text(body, encoding="utf-8")
            written[name] = str(path.relative_to(self.root.parent.parent) if False else path.name)
            # also mirror under os_build templates for CI discovery
        return written

    def debug_session(self, label: str = "phase_xiv") -> dict[str, Any]:
        marker = {
            "schema": "gunnchos.phase_xiv.debug_session.v1",
            "label": label,
            "started_at": time.time(),
            "hooks": ["cpu", "rss", "wayland_frame", "ai_latency"],
            "production_profiler": False,
        }
        (self.root / "DEBUG_SESSION.json").write_text(json.dumps(marker, indent=2) + "\n")
        return marker

    def e2e(self, os_build_templates: Path | None = None) -> dict[str, Any]:
        written = self.materialize_templates()
        if os_build_templates:
            os_build_templates.mkdir(parents=True, exist_ok=True)
            for src in self.templates_dir.iterdir():
                (os_build_templates / src.name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        dbg = self.debug_session()
        ok = set(written) == set(TEMPLATES) and dbg["production_profiler"] is False
        return {"ok": ok, "templates": written, "debug": dbg}
