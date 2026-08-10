"""Proton/Wine harness for redistributable test apps only.

Steam itself is treated as user-external — never claimed as bundled.
"""
from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from gunnchos_device_os.stage2.compat.classifier import classify


STEAM_USER_EXTERNAL = True


def probe_wine_proton() -> dict[str, Any]:
    wine = shutil.which("wine") or shutil.which("wine64")
    proton = shutil.which("proton")
    return {
        "steam_user_external": STEAM_USER_EXTERNAL,
        "wine_present": bool(wine),
        "wine_path": wine,
        "proton_present": bool(proton),
        "proton_path": proton,
    }


def run_redistributable_test_app(app_path: Path | str | None = None) -> dict[str, Any]:
    """Run a redistributable test binary under Wine when available.

    If no app or wine is present → UNKNOWN (never fake PASS).
    """
    probe = probe_wine_proton()
    path = Path(app_path) if app_path else None
    if not probe["wine_present"]:
        evidence = {
            "binary_present": False,
            "skipped": True,
            "skip_reason": "wine_absent",
            "lane": "STEAM_PROTON_USER",
        }
        return {"probe": probe, **classify(evidence), "app": None}
    if path is None or not path.exists():
        evidence = {
            "binary_present": False,
            "skipped": True,
            "skip_reason": "redistributable_test_app_absent",
            "lane": "STEAM_PROTON_USER",
        }
        return {"probe": probe, **classify(evidence), "app": str(path) if path else None}

    # Soft probe: wine --version (do not launch arbitrary EXEs in CI without fixture)
    import subprocess

    try:
        r = subprocess.run(
            [probe["wine_path"], "--version"],
            capture_output=True,
            text=True,
            timeout=20,
        )
        evidence = {
            "binary_present": True,
            "executed": True,
            "exit_code": r.returncode,
            "lane": "STEAM_PROTON_USER",
            "partial": True,  # harness ready; full title run needs fixture
            "note": "wine_version_only_until_redistributable_fixture",
        }
    except Exception as exc:  # noqa: BLE001
        evidence = {
            "binary_present": True,
            "executed": False,
            "errors": [str(exc)],
            "lane": "STEAM_PROTON_USER",
        }
    return {"probe": probe, **classify(evidence), "app": str(path)}
