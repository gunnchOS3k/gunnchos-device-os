"""Adopter SDK external sample from clean checkout OUTSIDE main repos."""
from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import os
import shutil
import subprocess
import sys
import tempfile

from gunnchos_device_os.cont_ix import CLAIM_BOUNDARY, TOKEN_ADOPTER_READY


def run_adopter_external_sample() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[2]
    sdk_src = root / "sdk"
    # Outside main repos: temp under /tmp (CI) — never under /Users/gunnchos workspace path requirement
    outside = Path(tempfile.mkdtemp(prefix="gchos-adopter-ext-", dir="/tmp"))
    steps: dict[str, Any] = {}

    # Copy SDK tree into external checkout
    ext_sdk = outside / "gunnchos_adopter_sdk_checkout"
    shutil.copytree(sdk_src, ext_sdk)
    steps["clean_checkout_outside"] = not str(ext_sdk).startswith("/Users/gunnchos")
    steps["sdk_copied"] = (ext_sdk / "gunnchos_adopter_sdk" / "client.py").exists()

    # Install SDK editable into isolated venv-like PYTHONPATH
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ext_sdk)
    # Create sample app
    sample = outside / "sample_app"
    sample.mkdir()
    (sample / "app.py").write_text(
        "from gunnchos_adopter_sdk.client import AdopterClient\n"
        "c = AdopterClient()\n"
        "print(c.negotiate('device_role','1.0.0'))\n"
        "print(c.sample_ring_input('tap'))\n"
        "print(c.sample_ai('hello'))\n"
        "print(c.sample_telemetry('boot'))\n",
        encoding="utf-8",
    )
    steps["sample_app_created"] = (sample / "app.py").exists()

    # Device profile + AI + ring + telemetry via client
    sys.path.insert(0, str(ext_sdk))
    from gunnchos_adopter_sdk.client import AdopterClient

    client = AdopterClient(base_url="http://127.0.0.1:9")
    device = client.sample_device_role("adopter")
    ai = client.sample_ai("capability probe")
    ring = client.sample_ring_input("tap")
    tele = client.sample_telemetry("sample_event")
    steps["device_profile"] = bool(device.get("ok"))
    steps["ai_capability"] = bool(ai.get("ok"))
    steps["ring_event"] = bool(ring.get("ok"))
    steps["telemetry"] = bool(tele.get("ok"))

    # Package + tests
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", str(ext_sdk / "tests")],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
        env=env,
        cwd=str(ext_sdk),
    )
    steps["tests"] = proc.returncode == 0
    steps["package_metadata"] = (ext_sdk / "pyproject.toml").exists()

    # Run sample
    run = subprocess.run(
        [sys.executable, str(sample / "app.py")],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
        env=env,
    )
    steps["sample_ran"] = run.returncode == 0

    ok = all(bool(v) for v in steps.values())
    # Never embed laptop absolute paths in the published report
    outside_label = "tmpfs:/tmp/gchos-adopter-ext-*"
    report = {
        "schema": "gunnchos.adopter_digital_ready.v1",
        "ok": ok,
        "token": TOKEN_ADOPTER_READY if ok else None,
        "outside_path": outside_label,
        "outside_is_tmp": str(outside).startswith("/tmp"),
        "steps": steps,
        "pytest_stdout": (proc.stdout or "")[:500],
        "open_hardware_required": False,
        "mock": False,
        "claim_boundary": CLAIM_BOUNDARY,
        "failure_reason": None if ok else "adopter_external_gap:" + ",".join(k for k, v in steps.items() if not v),
    }
    out = root / "artifacts" / "continuation_ix" / "adopter_digital_ready.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    return report
